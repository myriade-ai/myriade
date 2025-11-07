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
    bind = op.get_bind()
    
    # Add database_name column (nullable initially)
    op.add_column("table_facet", sa.Column("database_name", sa.String(), nullable=True))

    # Backfill database_name from database.details JSONB field
    # For each engine, extract the appropriate field:
    # - PostgreSQL/MySQL/MotherDuck: details->>'database'
    # - Snowflake: details->>'database'
    # - BigQuery: details->>'project_id'
    # - SQLite: details->>'filename'
    # - Oracle: details->>'service_name' or details->>'sid'

    connection = bind

    # Update with database name from the database table's details field
    if bind.dialect.name == "sqlite":
        # SQLite uses json_extract instead of JSONB operators
        connection.execute(
            sa.text("""
            UPDATE table_facet
            SET database_name = COALESCE(
                CASE
                    WHEN (SELECT engine FROM database WHERE id = table_facet.database_id) IN ('postgres', 'mysql', 'motherduck', 'snowflake')
                    THEN (SELECT json_extract(details, '$.database') FROM database WHERE id = table_facet.database_id)
                    WHEN (SELECT engine FROM database WHERE id = table_facet.database_id) = 'bigquery'
                    THEN (SELECT json_extract(details, '$.project_id') FROM database WHERE id = table_facet.database_id)
                    WHEN (SELECT engine FROM database WHERE id = table_facet.database_id) = 'sqlite'
                    THEN (SELECT json_extract(details, '$.filename') FROM database WHERE id = table_facet.database_id)
                    WHEN (SELECT engine FROM database WHERE id = table_facet.database_id) = 'oracle'
                    THEN COALESCE(
                        (SELECT json_extract(details, '$.service_name') FROM database WHERE id = table_facet.database_id),
                        (SELECT json_extract(details, '$.sid') FROM database WHERE id = table_facet.database_id)
                    )
                    ELSE (SELECT json_extract(details, '$.database') FROM database WHERE id = table_facet.database_id)
                END,
                'unknown'
            )
        """)
        )
    else:
        # PostgreSQL uses JSONB operators
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

    # Drop old unique constraint and add new one
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("table_facet") as batch_op:
            batch_op.drop_constraint(
                "uq_table_facet_database_schema_table", type_="unique"
            )
            batch_op.create_unique_constraint(
                "uq_table_facet_database_name_schema_table",
                ["database_id", "database_name", "schema", "table_name"],
            )
    else:
        op.drop_constraint(
            "uq_table_facet_database_schema_table", "table_facet", type_="unique"
        )
        op.create_unique_constraint(
            "uq_table_facet_database_name_schema_table",
            "table_facet",
            ["database_id", "database_name", "schema", "table_name"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("table_facet") as batch_op:
            # Drop new unique constraint
            batch_op.drop_constraint(
                "uq_table_facet_database_name_schema_table", type_="unique"
            )
            # Restore old unique constraint
            batch_op.create_unique_constraint(
                "uq_table_facet_database_schema_table",
                ["database_id", "schema", "table_name"],
            )
            # Drop database_name column
            batch_op.drop_column("database_name")
    else:
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
