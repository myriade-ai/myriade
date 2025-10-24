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
    dbt_repo_path: str | None = None,
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
        dbt_repo_path=dbt_repo_path,
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


def get_tables_metadata_from_catalog(
    database_id: UUID, session=None
) -> List[Dict[str, Any]]:
    """Get tables metadata from catalog in the same format as the old
    tables_metadata field

    Args:
        database_id: UUID of the database
        session: Optional SQLAlchemy session. If not provided, uses g.session
    """
    # Use provided session or fall back to g.session
    db_session = session if session is not None else g.session

    try:
        # Get all table and column assets for this database
        tables_data = (
            db_session.query(Asset, TableFacet)
            .join(TableFacet, Asset.id == TableFacet.asset_id)
            .filter(Asset.database_id == database_id, Asset.type == "TABLE")
            .all()
        )

        columns_data = (
            db_session.query(Asset, ColumnFacet, TableFacet)
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
                "table_type": table_facet.table_type,
                "columns": [],
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
        # If catalog is not available or fails, rollback and return empty list
        db_session.rollback()
        return []


def sync_database_metadata_to_assets(
    database_id: UUID,
    tables_metadata: List[Dict[str, Any]],
    session=None,
):
    """
    Sync catalog with database metadata (tables/columns)
    This method creates catalog assets from the database's tables_metadata
    using facet-based models. It also removes assets that no longer exist
    in the database.

    Args:
        database_id: UUID of the database
        tables_metadata: List of table metadata dictionaries
        session: Optional SQLAlchemy session. If not provided, uses g.session
    """
    if not tables_metadata:
        raise ValueError("No database metadata available to sync")

    # Use provided session or fall back to g.session
    db_session = session if session is not None else g.session

    synced_count = 0

    # Track all valid URNs from current metadata (both tables and columns)
    valid_urns = set()

    for table_meta in tables_metadata:
        schema_name = table_meta.get("schema")
        table_name = table_meta.get("name")

        # Generate URN for table
        table_urn = f"urn:table:{database_id}:{schema_name}:{table_name}"
        valid_urns.add(table_urn)

        # Check if table asset already exists
        table_asset = (
            db_session.query(Asset)
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
            db_session.add(table_asset)
            db_session.flush()  # Get the ID

            # Create table facet
            table_facet = TableFacet(
                asset_id=table_asset.id,
                database_id=database_id,
                schema=schema_name,
                table_name=table_name,
                table_type=table_meta.get("table_type"),
            )
            db_session.add(table_facet)
            synced_count += 1
        else:
            # Update existing table facet's table_type field if it changed
            table_facet = (
                db_session.query(TableFacet)
                .filter(TableFacet.asset_id == table_asset.id)
                .first()
            )
            if table_facet:
                table_facet.table_type = table_meta.get("table_type").upper()

        # Create/update column assets
        for i, column in enumerate(table_meta.get("columns", [])):
            column_name = column.get("name")

            # Generate URN for column
            column_urn = (
                f"urn:column:{database_id}:{schema_name}:{table_name}:{column_name}"
            )
            valid_urns.add(column_urn)

            column_asset = (
                db_session.query(Asset)
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
                db_session.add(column_asset)
                db_session.flush()  # Get the ID

                # Create column facet
                column_facet = ColumnFacet(
                    asset_id=column_asset.id,
                    parent_table_asset_id=table_asset.id,
                    column_name=column_name,
                    ordinal=i,
                    data_type=column.get("type"),
                    privacy=column.get("privacy"),
                )
                db_session.add(column_facet)
                synced_count += 1

    # Delete assets that no longer exist in the database
    orphaned_assets = (
        db_session.query(Asset)
        .filter(
            Asset.database_id == database_id,
            ~Asset.urn.in_(valid_urns) if valid_urns else True,
        )
        .all()
    )

    for asset in orphaned_assets:
        if asset.type == "COLUMN":
            db_session.query(ColumnFacet).filter(
                ColumnFacet.asset_id == asset.id
            ).delete()
        elif asset.type == "TABLE":
            db_session.query(TableFacet).filter(
                TableFacet.asset_id == asset.id
            ).delete()
        db_session.delete(asset)

    return {
        "synced_count": synced_count,
    }


def update_catalog_privacy(
    database_id: UUID, tables_metadata: List[Dict[str, Any]], session=None
):
    """
    Update privacy settings in catalog for existing assets
    This method updates column facets with new privacy information

    Args:
        database_id: UUID of the database
        tables_metadata: List of table metadata dictionaries
        session: Optional SQLAlchemy session. If not provided, uses g.session
    """
    if not tables_metadata:
        return

    db_session = session if session is not None else g.session

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
                db_session.query(Asset)
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
                    db_session.query(ColumnFacet)
                    .filter(ColumnFacet.asset_id == column_asset.id)
                    .first()
                )

                if column_facet:
                    column_facet.privacy = privacy_settings
