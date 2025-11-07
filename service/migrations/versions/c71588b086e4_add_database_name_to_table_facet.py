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

    # Drop old unique constraint
    op.drop_constraint(
        "uq_table_facet_database_schema_table", "table_facet", type_="unique"
    )

    # Add new unique constraint including database_name
    op.create_unique_constraint(
        "uq_table_facet_database_name_schema_table",
        "table_facet",
        ["database_id", "database_name", "schema", "table_name"],
    )


def downgrade() -> None:
    # Drop new unique constraint
    op.drop_constraint(
        "uq_table_facet_database_name_schema_table", "table_facet", type_="unique"
    )

    # Restore old unique constraint
    op.create_unique_constraint(
        "uq_table_facet_database_schema_table",
        "table_facet",
        ["database_id", "schema", "table_name"],
    )

    # Drop database_name column
    op.drop_column("table_facet", "database_name")
