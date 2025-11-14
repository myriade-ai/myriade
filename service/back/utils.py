import logging
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from flask import g
from sqlalchemy.orm import Session

from back.data_warehouse import AbstractDatabase
from models import Database
from models.catalog import Asset, ColumnFacet, DatabaseFacet, SchemaFacet, TableFacet

logger = logging.getLogger(__name__)


def _build_asset_urn(
    asset_type: Literal["DATABASE", "SCHEMA", "TABLE", "COLUMN"],
    connection_id: UUID,
    database_name: Optional[str],
    schema_name: Optional[str] = None,
    table_name: Optional[str] = None,
    column_name: Optional[str] = None,
) -> str:
    """
    Build a consistent URN for catalog assets.

    URN format follows a hierarchical structure prefixed with connection ID:
    - Database: urn:connection:{connection_id}:db:{database_name}
    - Schema: urn:connection:{connection_id}:db:{database_name}:{schema_name}
    - Table: urn:connection:{connection_id}:db:{database_name}:{schema_name}:{table_name}
    - Column: urn:connection:{connection_id}:db:{database_name}:{schema_name}:{table_name}:{column_name}

    Args:
        asset_type: Type of asset ("DATABASE", "SCHEMA", "TABLE", "COLUMN")
        connection_id: UUID of the database connection (ensures global uniqueness)
        database_name: Name of the database from the provider (required for all types)
        schema_name: Schema name (required for SCHEMA, TABLE, COLUMN)
        table_name: Table name (required for TABLE, COLUMN)
        column_name: Column name (required for COLUMN)

    Returns:
        URN string for the asset

    Raises:
        ValueError: If required parameters are None for the given asset type
    """

    if database_name is None:
        raise ValueError("database_name is required for all asset types")

    parts = ["urn:connection", str(connection_id), "db", database_name]

    if asset_type in ("SCHEMA", "TABLE", "COLUMN"):
        if schema_name is None:
            raise ValueError(f"schema_name is required for {asset_type} assets")
        parts.append(schema_name)

    if asset_type in ("TABLE", "COLUMN"):
        if table_name is None:
            raise ValueError(f"table_name is required for {asset_type} assets")
        parts.append(table_name)

    if asset_type == "COLUMN":
        if column_name is None:
            raise ValueError("column_name is required for COLUMN assets")
        parts.append(column_name)

    return ":".join(parts)


def create_database(
    name: str,
    description: str,
    engine: str,
    details: dict,
    public: bool,
    write_mode: str = "confirmation",
    owner_id: str | None = None,
    organisation_id: str | None = None,
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
    )
    # After database creation, we'll sync initial metadata to catalog
    # This happens in the API layer after the database is persisted
    return database


def merge_tables_metadata(
    existing: Optional[List[Dict[str, Any]]], new: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Return `new` tables list enriched with metadata from `existing`.

    Preserves user-added metadata:
    - If a table/column already has a description in `existing`, keep it
    - If a table/column already has a privacy map in `existing`, keep it
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

        # Preserve user-added table description if it exists
        table_description = t.get("description")
        if previous and previous.get("description"):
            table_description = previous.get("description")

        # Build columns preserving privacy and description if available
        merged_columns: List[Dict[str, Any]] = []
        for col in t["columns"]:
            # find same column in previous
            prev_col_priv = {}
            prev_col_desc = None
            if previous:
                for pc in previous.get("columns", []):
                    if pc["name"] == col["name"]:
                        prev_col_priv = pc.get("privacy", {})
                        prev_col_desc = pc.get("description")
                        break

            # Preserve user-added column description if it exists
            col_description = col.get("description")
            if prev_col_desc:
                col_description = prev_col_desc

            merged_columns.append(
                {
                    **col,
                    "description": col_description,
                    "privacy": prev_col_priv.copy(),
                }
            )
        merged.append(
            {**t, "description": table_description, "columns": merged_columns}
        )

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
                "database_name": table_facet.database_name,
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
    progress_callback=None,
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
        progress_callback: Optional callback function(current, total, message)
                          called after each table is processed
    """
    if not tables_metadata:
        raise ValueError("No database metadata available to sync")

    # Use provided session or fall back to g.session
    db_session = session if session is not None else g.session

    created_count = 0
    updated_count = 0

    # Track all valid URNs from current metadata (databases, schemas, tables, columns)
    valid_urns = set()

    # Optimization: Pre-load all existing assets in a single query
    # Load full Asset objects to avoid re-querying
    existing_assets = (
        db_session.query(Asset).filter(Asset.database_id == database_id).all()
    )
    existing_assets_by_urn = {asset.urn: asset for asset in existing_assets}

    # Step 1: Extract unique databases from metadata
    unique_databases = {}
    for table_meta in tables_metadata:
        database_name = table_meta.get("database")
        if database_name and database_name not in unique_databases:
            unique_databases[database_name] = database_name

    # Step 2: Create/update database assets
    database_assets = {}
    for database_name in unique_databases:
        database_urn = _build_asset_urn("DATABASE", database_id, database_name)
        valid_urns.add(database_urn)

        database_asset = existing_assets_by_urn.get(database_urn)
        if not database_asset:
            # Create new database asset
            database_asset = Asset(
                name=database_name,
                urn=database_urn,
                type="DATABASE",
                database_id=database_id,
            )
            db_session.add(database_asset)
            db_session.flush()  # Get the ID

            # Create database facet
            database_facet = DatabaseFacet(
                asset_id=database_asset.id,
                database_id=database_id,
                database_name=database_name,
            )
            db_session.add(database_facet)
            created_count += 1

        database_assets[database_name] = database_asset

    # Step 3: Extract unique schemas from metadata
    unique_schemas = {}
    for table_meta in tables_metadata:
        database_name = table_meta.get("database")
        schema_name = table_meta.get("schema")
        if database_name and schema_name:
            key = (database_name, schema_name)
            if key not in unique_schemas:
                unique_schemas[key] = (database_name, schema_name)

    # Step 4: Create/update schema assets
    schema_assets = {}
    for database_name, schema_name in unique_schemas.values():
        # Get the database asset ID to use in schema URN
        parent_database_asset = database_assets.get(database_name)
        if not parent_database_asset:
            raise ValueError(
                f"Parent database asset not found for schema: {database_name}.{schema_name}. "
                f"Database assets must be created before schemas."
            )

        schema_urn = _build_asset_urn(
            "SCHEMA",
            database_id,
            database_name,
            schema_name,
        )
        valid_urns.add(schema_urn)

        schema_asset = existing_assets_by_urn.get(schema_urn)
        if not schema_asset:
            # Create new schema asset
            schema_asset = Asset(
                name=schema_name,
                urn=schema_urn,
                type="SCHEMA",
                database_id=database_id,
            )
            db_session.add(schema_asset)
            db_session.flush()  # Get the ID

            # Create schema facet
            schema_facet = SchemaFacet(
                asset_id=schema_asset.id,
                database_id=database_id,
                database_name=database_name,
                schema_name=schema_name,
                parent_database_asset_id=parent_database_asset.id,
            )
            db_session.add(schema_facet)
            created_count += 1

        schema_assets[(database_name, schema_name)] = schema_asset

    # Commit database and schema assets
    db_session.commit()
    logger.info(
        f"Created/updated {len(database_assets)} databases and "
        f"{len(schema_assets)} schemas"
    )

    # Batch commit settings
    COMMIT_BATCH_SIZE = 100  # Commit every 100 tables
    tables_processed = 0

    # Step 5: Create/update table and column assets
    for table_meta in tables_metadata:
        database_name = table_meta.get("database")
        schema_name = table_meta.get("schema")
        table_name = table_meta.get("name")

        # Get the database asset ID to use in table URN
        parent_database_asset = database_assets.get(database_name)
        if not parent_database_asset:
            raise ValueError(
                f"Parent database asset not found for table: {database_name}.{schema_name}.{table_name}. "
                f"Database assets must be created before tables."
            )

        # Generate URN for table
        table_urn = _build_asset_urn(
            "TABLE",
            database_id,
            database_name,
            schema_name,
            table_name,
        )
        valid_urns.add(table_urn)

        # Check if table asset already exists (using pre-loaded dict)
        table_asset = existing_assets_by_urn.get(table_urn)

        # Get parent schema asset
        parent_schema_asset = schema_assets.get((database_name, schema_name))

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
                database_name=database_name,
                schema=schema_name,
                table_name=table_name,
                table_type=table_meta.get("table_type"),
                parent_schema_asset_id=parent_schema_asset.id
                if parent_schema_asset
                else None,
            )
            db_session.add(table_facet)
            created_count += 1
        else:
            # Update existing table facet's table_type field if it changed
            table_facet = (
                db_session.query(TableFacet)
                .filter(TableFacet.asset_id == table_asset.id)
                .first()
            )
            if table_facet:
                old_table_type = table_facet.table_type
                new_table_type = table_meta.get("table_type")
                if old_table_type != new_table_type:
                    table_facet.table_type = (
                        new_table_type.upper() if new_table_type else None
                    )
                    updated_count += 1

        # Create/update column assets
        for i, column in enumerate(table_meta.get("columns", [])):
            column_name = column.get("name")

            # Generate URN for column
            column_urn = _build_asset_urn(
                "COLUMN",
                database_id,
                database_name,
                schema_name,
                table_name,
                column_name,
            )
            valid_urns.add(column_urn)

            # Check if column asset already exists (using pre-loaded dict)
            column_asset = existing_assets_by_urn.get(column_urn)

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
                created_count += 1
            else:
                # Update column facet if data type changed
                column_facet = (
                    db_session.query(ColumnFacet)
                    .filter(ColumnFacet.asset_id == column_asset.id)
                    .first()
                )
                if column_facet:
                    old_data_type = column_facet.data_type
                    new_data_type = column.get("type")
                    if old_data_type != new_data_type:
                        column_facet.data_type = new_data_type
                        updated_count += 1

        # Batch commit: commit every COMMIT_BATCH_SIZE tables
        tables_processed += 1

        # Call progress callback if provided
        if progress_callback:
            progress_callback(
                tables_processed,
                len(tables_metadata),
                f"Syncing {schema_name}.{table_name}",
            )

        if tables_processed % COMMIT_BATCH_SIZE == 0:
            db_session.commit()
            logger.info(
                f"Committed batch of {COMMIT_BATCH_SIZE} tables "
                f"({tables_processed}/{len(tables_metadata)} total)"
            )

    # Final commit for remaining tables
    if tables_processed % COMMIT_BATCH_SIZE != 0:
        db_session.commit()
        logger.info(f"Committed final batch ({tables_processed} tables total)")

    # Delete assets that no longer exist in the database
    orphaned_assets = (
        db_session.query(Asset)
        .filter(
            Asset.database_id == database_id,
            ~Asset.urn.in_(valid_urns) if valid_urns else True,
        )
        .all()
    )

    # Sort orphaned assets by type to delete children before parents
    # This ensures we don't violate foreign key constraints
    # Order: COLUMN -> TABLE -> SCHEMA -> DATABASE
    asset_type_order = {"COLUMN": 0, "TABLE": 1, "SCHEMA": 2, "DATABASE": 3}
    orphaned_assets.sort(key=lambda a: asset_type_order.get(a.type, 999))

    for asset in orphaned_assets:
        if asset.type == "COLUMN":
            db_session.query(ColumnFacet).filter(
                ColumnFacet.asset_id == asset.id
            ).delete()
        elif asset.type == "TABLE":
            db_session.query(TableFacet).filter(
                TableFacet.asset_id == asset.id
            ).delete()
        elif asset.type == "SCHEMA":
            db_session.query(SchemaFacet).filter(
                SchemaFacet.asset_id == asset.id
            ).delete()
        elif asset.type == "DATABASE":
            db_session.query(DatabaseFacet).filter(
                DatabaseFacet.asset_id == asset.id
            ).delete()
        db_session.delete(asset)

    if orphaned_assets:
        db_session.commit()
        logger.info(f"Deleted {len(orphaned_assets)} orphaned assets")

    return {
        "created_count": created_count,
        "updated_count": updated_count,
        "synced_count": created_count,  # Backward compatibility
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

    # Build a map of database names to their asset IDs
    database_assets = (
        db_session.query(Asset)
        .filter(
            Asset.database_id == database_id,
            Asset.type == "DATABASE",
        )
        .all()
    )
    database_name_to_asset_id = {asset.name: asset.id for asset in database_assets}

    for table_meta in tables_metadata:
        database_name = table_meta.get("database")
        schema_name = table_meta.get("schema")
        table_name = table_meta.get("name")

        # Get the database asset ID
        database_asset_id = database_name_to_asset_id.get(database_name)
        if not database_asset_id:
            raise ValueError(
                f"Database asset not found for {database_name}. "
                f"Cannot update privacy for {database_name}.{schema_name}.{table_name}"
            )

        # Update column privacy settings
        for column in table_meta.get("columns", []):
            column_name = column.get("name")
            privacy_settings = column.get("privacy", {})

            # Generate URN for column
            column_urn = _build_asset_urn(
                "COLUMN",
                database_id,
                database_name,
                schema_name,
                table_name,
                column_name,
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


def get_provider_metadata_for_asset(
    asset: Asset, data_warehouse: AbstractDatabase, session: Session
) -> Optional[Dict[str, Any]]:
    """
    Extract metadata from the data provider for the given asset.
    Delegates to database-specific methods for actual metadata retrieval.

    Args:
        asset: The asset to get provider metadata for
        data_warehouse: The data warehouse instance to query metadata from
        session: SQLAlchemy session for database queries

    Returns:
        Dictionary with description (comment) and tags if found, None otherwise
    """
    try:
        # For table assets
        if asset.type == "TABLE" and asset.table_facet:
            schema = asset.table_facet.schema
            table_name = asset.table_facet.table_name

            if not schema or not table_name:
                return None

            # Delegate to data warehouse method
            result = data_warehouse.get_table_metadata(schema, table_name)
            return result if result else None

        # For column assets
        elif asset.type == "COLUMN" and asset.column_facet:
            parent_asset = (
                session.query(Asset)
                .filter(Asset.id == asset.column_facet.parent_table_asset_id)
                .first()
            )

            if parent_asset and parent_asset.table_facet:
                schema = parent_asset.table_facet.schema
                table_name = parent_asset.table_facet.table_name
                column_name = asset.column_facet.column_name

                if not schema or not table_name or not column_name:
                    return None

                # Delegate to data warehouse method
                result = data_warehouse.get_column_metadata(
                    schema, table_name, column_name
                )
                return result if result else None

        return None

    except Exception as e:
        logger.error(f"Error fetching provider metadata: {e}")
        return None


def get_dialect_name(session: Session) -> str:
    """Get the dialect name of the database connected to the given session.

    Args:
        session: SQLAlchemy session

    Returns:
        Dialect name as a string (e.g., 'postgresql', 'mysql', etc.)
    """
    return session.get_bind().dialect.name
