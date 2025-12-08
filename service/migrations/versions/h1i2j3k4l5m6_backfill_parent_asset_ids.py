"""backfill_parent_asset_ids

Backfill parent_schema_asset_id for table_facet and
parent_database_asset_id for schema_facet where they are NULL.

Revision ID: h1i2j3k4l5m6
Revises: g1h2i3j4k5l6
Create Date: 2025-12-08

"""

from typing import Sequence, Union

from alembic import op

revision: str = "h1i2j3k4l5m6"
down_revision: Union[str, None] = "g1h2i3j4k5l6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    dialect = op.get_bind().dialect.name

    if dialect == "postgresql":
        # Backfill schema_facet.parent_database_asset_id
        # Match schemas to databases using database_name within the same database_id
        op.execute("""
            UPDATE schema_facet sf
            SET parent_database_asset_id = df.asset_id
            FROM database_facet df
            WHERE sf.parent_database_asset_id IS NULL
              AND sf.database_id = df.database_id
              AND sf.database_name = df.database_name
        """)

        # Backfill table_facet.parent_schema_asset_id
        # Match tables to schemas using database_name and schema within the same database_id
        op.execute("""
            UPDATE table_facet tf
            SET parent_schema_asset_id = sf.asset_id
            FROM schema_facet sf
            WHERE tf.parent_schema_asset_id IS NULL
              AND tf.database_id = sf.database_id
              AND tf.database_name = sf.database_name
              AND tf.schema = sf.schema_name
        """)

    elif dialect == "sqlite":
        # SQLite doesn't support UPDATE ... FROM, use subqueries instead

        # Backfill schema_facet.parent_database_asset_id
        op.execute("""
            UPDATE schema_facet
            SET parent_database_asset_id = (
                SELECT df.asset_id
                FROM database_facet df
                WHERE df.database_id = schema_facet.database_id
                  AND df.database_name = schema_facet.database_name
            )
            WHERE parent_database_asset_id IS NULL
              AND EXISTS (
                SELECT 1 FROM database_facet df
                WHERE df.database_id = schema_facet.database_id
                  AND df.database_name = schema_facet.database_name
              )
        """)

        # Backfill table_facet.parent_schema_asset_id
        op.execute("""
            UPDATE table_facet
            SET parent_schema_asset_id = (
                SELECT sf.asset_id
                FROM schema_facet sf
                WHERE sf.database_id = table_facet.database_id
                  AND sf.database_name = table_facet.database_name
                  AND sf.schema_name = table_facet.schema
            )
            WHERE parent_schema_asset_id IS NULL
              AND EXISTS (
                SELECT 1 FROM schema_facet sf
                WHERE sf.database_id = table_facet.database_id
                  AND sf.database_name = table_facet.database_name
                  AND sf.schema_name = table_facet.schema
              )
        """)


def downgrade() -> None:
    # This migration only fills in NULL values, so downgrade is a no-op
    # We don't want to set values back to NULL as that would lose data
    pass
