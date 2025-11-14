"""migrate asset urns to simplified hierarchical format

Revision ID: dabb5b1e2cad
Revises: f2a3b4c5d6e7
Create Date: 2025-11-13 14:21:07.000000

This migration updates the URN format for all assets to use a simplified,
human-readable hierarchical format based on database/schema/table/column names,
prefixed with the connection ID to ensure global uniqueness.

Old format (varies by implementation):
- Database: urn:database:{connection_id}:{database_name}
- Schema: urn:schema:{connection_id}:{database_name}:{schema_name} (or with database_asset_id)
- Table: urn:table:{connection_id}:{database_name}:{schema_name}:{table_name} (or with database_asset_id)
- Column: urn:column:{connection_id}:{database_name}:{schema_name}:{table_name}:{column_name} (or with database_asset_id)

New format:
- Database: urn:connection:{connection_id}:db:{database_name}
- Schema: urn:connection:{connection_id}:db:{database_name}:{schema_name}
- Table: urn:connection:{connection_id}:db:{database_name}:{schema_name}:{table_name}
- Column: urn:connection:{connection_id}:db:{database_name}:{schema_name}:{table_name}:{column_name}

This migration preserves all user-added descriptions, tags, and AI suggestions.
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "dabb5b1e2cad"
down_revision: Union[str, None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _build_new_urn(
    connection_id: str,
    database_name: str,
    schema_name: str | None = None,
    table_name: str | None = None,
    column_name: str | None = None,
) -> str:
    """
    Build new simplified URN format using hierarchical naming.

    Format: urn:connection:{connection_id}:db:{database_name}[:schema_name][:table_name][:column_name]
    """
    parts = ["urn:connection", connection_id, "db", database_name]

    if schema_name:
        parts.append(schema_name)

    if table_name:
        parts.append(table_name)

    if column_name:
        parts.append(column_name)

    return ":".join(parts)


def upgrade() -> None:
    """Migrate URNs from old format to new simplified format."""

    conn = op.get_bind()

    # Migrate Database assets
    database_assets = conn.execute(
        text("""
            SELECT a.id, a.urn, a.database_id, df.database_name
            FROM asset a
            JOIN database_facet df ON a.id = df.asset_id
            WHERE a.type = 'DATABASE'
        """)
    ).fetchall()

    print(f"Migrating {len(database_assets)} database assets...")
    for row in database_assets:
        asset_id, old_urn, database_id, database_name = row

        # Build new URN: urn:connection:{connection_id}:db:{database_name}
        new_urn = _build_new_urn(str(database_id), database_name)

        # Update the asset URN
        conn.execute(
            text("UPDATE asset SET urn = :new_urn WHERE id = :asset_id"),
            {"new_urn": new_urn, "asset_id": str(asset_id)},
        )

        print(f"  Database: {old_urn} -> {new_urn}")

    # Migrate Schema assets
    schema_assets = conn.execute(
        text("""
            SELECT a.id, a.urn, a.database_id, sf.database_name, sf.schema_name
            FROM asset a
            JOIN schema_facet sf ON a.id = sf.asset_id
            WHERE a.type = 'SCHEMA'
        """)
    ).fetchall()

    print(f"Migrating {len(schema_assets)} schema assets...")
    for row in schema_assets:
        asset_id, old_urn, database_id, database_name, schema_name = row

        # Build new URN: urn:connection:{connection_id}:db:{database_name}:{schema_name}
        new_urn = _build_new_urn(str(database_id), database_name, schema_name)

        # Update the asset URN
        conn.execute(
            text("UPDATE asset SET urn = :new_urn WHERE id = :asset_id"),
            {"new_urn": new_urn, "asset_id": str(asset_id)},
        )

        print(f"  Schema: {old_urn} -> {new_urn}")

    # Migrate Table assets
    table_assets = conn.execute(
        text("""
            SELECT a.id, a.urn, a.database_id, tf.database_name, tf.schema, tf.table_name
            FROM asset a
            JOIN table_facet tf ON a.id = tf.asset_id
            WHERE a.type = 'TABLE'
        """)
    ).fetchall()

    print(f"Migrating {len(table_assets)} table assets...")
    for row in table_assets:
        asset_id, old_urn, database_id, database_name, schema_name, table_name = row

        # Build new URN: urn:connection:{connection_id}:db:{database_name}:{schema_name}:{table_name}
        new_urn = _build_new_urn(
            str(database_id), database_name, schema_name, table_name
        )

        # Update the asset URN
        conn.execute(
            text("UPDATE asset SET urn = :new_urn WHERE id = :asset_id"),
            {"new_urn": new_urn, "asset_id": str(asset_id)},
        )

    print(f"  Migrated {len(table_assets)} tables")

    # Migrate Column assets
    column_assets = conn.execute(
        text("""
            SELECT a.id, a.urn, a.database_id, cf.column_name, 
                   tf.database_name, tf.schema, tf.table_name
            FROM asset a
            JOIN column_facet cf ON a.id = cf.asset_id
            JOIN table_facet tf ON cf.parent_table_asset_id = tf.asset_id
            WHERE a.type = 'COLUMN'
        """)
    ).fetchall()

    print(f"Migrating {len(column_assets)} column assets...")
    for row in column_assets:
        (
            asset_id,
            old_urn,
            database_id,
            column_name,
            database_name,
            schema_name,
            table_name,
        ) = row

        # Build new URN: urn:connection:{connection_id}:db:{database_name}:{schema_name}:{table_name}:{column_name}
        new_urn = _build_new_urn(
            str(database_id),
            database_name,
            schema_name,
            table_name,
            column_name,
        )

        # Update the asset URN
        conn.execute(
            text("UPDATE asset SET urn = :new_urn WHERE id = :asset_id"),
            {"new_urn": new_urn, "asset_id": str(asset_id)},
        )

    print(f"  Migrated {len(column_assets)} columns")
    print("URN migration completed successfully!")


def downgrade() -> None:
    """Downgrade is not supported as it would require storing old URN format."""
