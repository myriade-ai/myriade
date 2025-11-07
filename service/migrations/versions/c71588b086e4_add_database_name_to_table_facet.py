"""add_database_name_to_table_facet

Revision ID: c71588b086e4
Revises: d019f75039d5
Create Date: 2025-11-04 12:48:52.659693

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c71588b086e4"
down_revision: Union[str, None] = "d019f75039d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add database_name column (nullable initially)
    op.add_column("table_facet", sa.Column("database_name", sa.String(), nullable=True))

    # Backfill database_name from database.details JSONB field
    # For each engine, extract the appropriate field:
    # - PostgreSQL/MySQL/MotherDuck: details->>'database'
    # - Snowflake: details->>'database'
    # - BigQuery: details->>'project_id'
    # - SQLite: details->>'filename'
    # - Oracle: details->>'service_name' or details->>'sid'

    connection = op.get_bind()

    # Update with database name from the database table's details field
    if connection.dialect.name == "postgresql":
        # PostgreSQL with JSONB
        connection.execute(
            sa.text("""
            UPDATE table_facet tf
            SET database_name = COALESCE(
                CASE
                    WHEN d.engine IN ('postgres', 'mysql', 'motherduck', 'snowflake')
                    THEN d.details->>'database'
                    WHEN d.engine = 'bigquery'
                    THEN d.details->>'project_id'
                    WHEN d.engine = 'sqlite'
                    THEN d.details->>'filename'
                    WHEN d.engine = 'oracle'
                    THEN COALESCE(d.details->>'service_name', d.details->>'sid')
                    ELSE d.details->>'database'
                END,
                'unknown'
            )
            FROM database d
            WHERE tf.database_id = d.id
        """)
        )
    else:
        # SQLite with JSON
        connection.execute(
            sa.text("""
            UPDATE table_facet
            SET database_name = COALESCE(
                CASE
                    WHEN (SELECT engine FROM database d WHERE table_facet.database_id = d.id) IN ('postgres', 'mysql', 'motherduck', 'snowflake')
                    THEN (SELECT json_extract(details, '$.database') FROM database d WHERE table_facet.database_id = d.id)
                    WHEN (SELECT engine FROM database d WHERE table_facet.database_id = d.id) = 'bigquery'
                    THEN (SELECT json_extract(details, '$.project_id') FROM database d WHERE table_facet.database_id = d.id)
                    WHEN (SELECT engine FROM database d WHERE table_facet.database_id = d.id) = 'sqlite'
                    THEN (SELECT json_extract(details, '$.filename') FROM database d WHERE table_facet.database_id = d.id)
                    WHEN (SELECT engine FROM database d WHERE table_facet.database_id = d.id) = 'oracle'
                    THEN COALESCE(
                        (SELECT json_extract(details, '$.service_name') FROM database d WHERE table_facet.database_id = d.id),
                        (SELECT json_extract(details, '$.sid') FROM database d WHERE table_facet.database_id = d.id)
                    )
                    ELSE (SELECT json_extract(details, '$.database') FROM database d WHERE table_facet.database_id = d.id)
                END,
                'unknown'
            )
        """)
        )

    # Drop old unique constraint and add new one
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table("table_facet", schema=None) as batch_op:
        batch_op.drop_constraint("uq_table_facet_database_schema_table", type_="unique")
        batch_op.create_unique_constraint(
            "uq_table_facet_database_name_schema_table",
            ["database_id", "database_name", "schema", "table_name"],
        )


def downgrade() -> None:
    # Drop new unique constraint, restore old one, and drop database_name column
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table("table_facet", schema=None) as batch_op:
        batch_op.drop_constraint(
            "uq_table_facet_database_name_schema_table", type_="unique"
        )
        batch_op.create_unique_constraint(
            "uq_table_facet_database_schema_table",
            ["database_id", "schema", "table_name"],
        )
        batch_op.drop_column("database_name")
