from typing import Any, Dict, List, Optional
from uuid import UUID

from flask import g

from models import Database
from models.catalog import Asset, ColumnFacet, TableFacet


def create_database(
    name: str,
    description: str,
    engine: str,
    details: dict,
    public: bool,
    write_mode: str = "confirmation",
    owner_id: str | None = None,
    organisation_id: str | None = None,
    dbt_catalog: dict | None = None,
    dbt_manifest: dict | None = None,
):
    # Create a new database
    database = Database(
        name=name,
        description=description,
        engine=engine,
        details=details,
        organisationId=organisation_id,
        ownerId=owner_id,
        public=public,
        write_mode=write_mode,
        dbt_catalog=dbt_catalog,
        dbt_manifest=dbt_manifest,
    )
    # After database creation, we'll sync initial metadata to catalog
    # This happens in the API layer after the database is persisted
    return database


def merge_tables_metadata(
    existing: Optional[List[Dict[str, Any]]], new: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Return `new` tables list enriched with privacy maps from `existing`.

    If a table/column already has a privacy map in `existing`, keep it.
    Tables not present in the data_warehouse anymore are discarded.
    """

    existing_lookup = {}
    if existing:
        for t in existing:
            existing_lookup[(t.get("schema"), t["name"])] = t

    merged: List[Dict[str, Any]] = []
    for t in new:
        key = (t.get("schema"), t["name"])
        previous = existing_lookup.get(key)
        # Build columns preserving privacy if available
        merged_columns: List[Dict[str, Any]] = []
        for col in t["columns"]:
            # find same column in previous
            prev_col_priv = {}
            if previous:
                for pc in previous.get("columns", []):
                    if pc["name"] == col["name"]:
                        prev_col_priv = pc.get("privacy", {})
                        break
            merged_columns.append(
                {
                    **col,
                    "privacy": prev_col_priv.copy(),
                }
            )
        merged.append({**t, "columns": merged_columns})

    return merged


def get_tables_metadata_from_catalog(database_id: UUID) -> List[Dict[str, Any]]:
    """Get tables metadata from catalog in the same format as the old
    tables_metadata field"""
    try:
        # Get all table and column assets for this database
        tables_data = (
            g.session.query(Asset, TableFacet)
            .join(TableFacet, Asset.id == TableFacet.asset_id)
            .filter(Asset.database_id == database_id, Asset.type == "TABLE")
            .all()
        )

        columns_data = (
            g.session.query(Asset, ColumnFacet, TableFacet)
            .join(ColumnFacet, Asset.id == ColumnFacet.asset_id)
            .join(TableFacet, ColumnFacet.parent_table_asset_id == TableFacet.asset_id)
            .filter(Asset.database_id == database_id, Asset.type == "COLUMN")
            .order_by(ColumnFacet.ordinal)
            .all()
        )

        # Group columns by table
        tables_map = {}
        for asset, table_facet in tables_data:
            table_key = (table_facet.schema, table_facet.table_name)
            tables_map[table_key] = {
                "name": table_facet.table_name,
                "schema": table_facet.schema,
                "description": asset.description,
                "columns": [],
                "is_view": False,  # Default, could be enhanced later
            }

        # Add columns to their tables
        for asset, column_facet, table_facet in columns_data:
            table_key = (table_facet.schema, table_facet.table_name)
            if table_key in tables_map:
                column_info = {
                    "name": column_facet.column_name,
                    "type": column_facet.data_type,
                    "description": asset.description,
                    "privacy": column_facet.privacy or {},
                }
                tables_map[table_key]["columns"].append(column_info)

        return list(tables_map.values())

    except Exception:
        # If catalog is not available or fails, return empty list
        return []


def sync_database_metadata_to_assets(
    database_id: UUID,
    tables_metadata: List[Dict[str, Any]],
):
    """
    Sync catalog with database metadata (tables/columns)
    This method creates catalog assets from the database's tables_metadata
    using facet-based models
    """
    if not tables_metadata:
        return "No database metadata available to sync"

    synced_count = 0

    for table_meta in tables_metadata:
        schema_name = table_meta.get("schema")
        table_name = table_meta.get("name")

        # Generate URN for table
        table_urn = f"urn:table:{database_id}:{schema_name}:{table_name}"

        # Check if table asset already exists
        table_asset = (
            g.session.query(Asset)
            .filter(
                Asset.database_id == database_id,
                Asset.urn == table_urn,
            )
            .first()
        )

        if not table_asset:
            # Create new table asset
            table_asset = Asset(
                name=table_name,
                urn=table_urn,
                type="TABLE",
                description=table_meta.get("description"),
                database_id=database_id,
            )
            g.session.add(table_asset)
            g.session.flush()  # Get the ID

            # Create table facet
            table_facet = TableFacet(
                asset_id=table_asset.id,
                database_id=database_id,
                schema=schema_name,
                table_name=table_name,
            )
            g.session.add(table_facet)
            synced_count += 1

        # Create/update column assets
        for i, column in enumerate(table_meta.get("columns", [])):
            column_name = column.get("name")

            # Generate URN for column
            column_urn = (
                f"urn:column:{database_id}:{schema_name}:{table_name}:{column_name}"
            )

            column_asset = (
                g.session.query(Asset)
                .filter(
                    Asset.database_id == database_id,
                    Asset.urn == column_urn,
                )
                .first()
            )

            if not column_asset:
                # Create new column asset
                column_asset = Asset(
                    name=column_name,
                    urn=column_urn,
                    type="COLUMN",
                    description=column.get("description"),
                    database_id=database_id,
                )
                g.session.add(column_asset)
                g.session.flush()  # Get the ID

                # Create column facet
                column_facet = ColumnFacet(
                    asset_id=column_asset.id,
                    parent_table_asset_id=table_asset.id,
                    column_name=column_name,
                    ordinal=i,
                    data_type=column.get("type"),
                    privacy=column.get("privacy"),
                )
                g.session.add(column_facet)
                synced_count += 1

    return {
        "synced_count": synced_count,
    }


def update_catalog_privacy(database_id: UUID, tables_metadata: List[Dict[str, Any]]):
    """
    Update privacy settings in catalog for existing assets
    This method updates column facets with new privacy information
    """
    if not tables_metadata:
        return

    for table_meta in tables_metadata:
        schema_name = table_meta.get("schema")
        table_name = table_meta.get("name")

        # Update column privacy settings
        for column in table_meta.get("columns", []):
            column_name = column.get("name")
            privacy_settings = column.get("privacy", {})

            # Generate URN for column
            column_urn = (
                f"urn:column:{database_id}:{schema_name}:{table_name}:{column_name}"
            )

            # Find existing column asset
            column_asset = (
                g.session.query(Asset)
                .filter(
                    Asset.database_id == database_id,
                    Asset.urn == column_urn,
                    Asset.type == "COLUMN",
                )
                .first()
            )

            if column_asset:
                # Update column facet privacy settings
                column_facet = (
                    g.session.query(ColumnFacet)
                    .filter(ColumnFacet.asset_id == column_asset.id)
                    .first()
                )

                if column_facet:
                    column_facet.privacy = privacy_settings
