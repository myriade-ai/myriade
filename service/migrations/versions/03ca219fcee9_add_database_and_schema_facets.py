"""add_database_and_schema_facets

Revision ID: 03ca219fcee9
Revises: c71588b086e4
Create Date: 2025-11-04 14:54:37.047433

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "03ca219fcee9"
down_revision: Union[str, None] = "c71588b086e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create database_facet table
    op.create_table(
        "database_facet",
        sa.Column("asset_id", sa.UUID(), nullable=False),
        sa.Column("database_id", sa.UUID(), nullable=False),
        sa.Column("database_name", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["asset.id"],
        ),
        sa.ForeignKeyConstraint(
            ["database_id"],
            ["database.id"],
        ),
        sa.PrimaryKeyConstraint("asset_id"),
        sa.UniqueConstraint("database_id", "database_name"),
    )

    # Create schema_facet table
    op.create_table(
        "schema_facet",
        sa.Column("asset_id", sa.UUID(), nullable=False),
        sa.Column("database_id", sa.UUID(), nullable=False),
        sa.Column("database_name", sa.String(), nullable=False),
        sa.Column("schema_name", sa.String(), nullable=False),
        sa.Column("parent_database_asset_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["asset.id"],
        ),
        sa.ForeignKeyConstraint(
            ["database_id"],
            ["database.id"],
        ),
        sa.ForeignKeyConstraint(
            ["parent_database_asset_id"],
            ["asset.id"],
        ),
        sa.PrimaryKeyConstraint("asset_id"),
        sa.UniqueConstraint("database_id", "database_name", "schema_name"),
    )

    # Add parent_schema_asset_id column to table_facet
    op.add_column(
        "table_facet", sa.Column("parent_schema_asset_id", sa.UUID(), nullable=True)
    )
    op.create_foreign_key(
        "fk_table_facet_parent_schema_asset",
        "table_facet",
        "asset",
        ["parent_schema_asset_id"],
        ["id"],
    )


def downgrade() -> None:
    # Remove parent_schema_asset_id from table_facet
    op.drop_constraint(
        "fk_table_facet_parent_schema_asset", "table_facet", type_="foreignkey"
    )
    op.drop_column("table_facet", "parent_schema_asset_id")

    # Drop schema_facet table
    op.drop_table("schema_facet")

    # Drop database_facet table
    op.drop_table("database_facet")
