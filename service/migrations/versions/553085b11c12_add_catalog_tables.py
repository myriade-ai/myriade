"""Add catalog tables

Revision ID: 553085b11c12
Revises: c8852c2a5ee9
Create Date: 2025-09-16 10:13:45.814021

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from db import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = "553085b11c12"
down_revision: Union[str, None] = "c8852c2a5ee9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create catalog_asset table
    op.create_table(
        "catalog_asset",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("asset_type", sa.String(), nullable=False),
        sa.Column("database_id", UUID(), nullable=False),
        sa.Column("tags", JSONB(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("schema_name", sa.String(), nullable=True),
        sa.Column("table_name", sa.String(), nullable=True),
        sa.Column("column_name", sa.String(), nullable=True),
        sa.Column("data_type", sa.String(), nullable=True),
        sa.Column("query_id", UUID(), nullable=True),
        sa.Column("chart_id", UUID(), nullable=True),
        sa.Column(
            "createdAt",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updatedAt",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["chart_id"], ["chart.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"]),
        sa.ForeignKeyConstraint(["database_id"], ["database.id"]),
        sa.ForeignKeyConstraint(["query_id"], ["query.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create business_glossary_term table
    op.create_table(
        "business_glossary_term",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("definition", sa.Text(), nullable=False),
        sa.Column("database_id", UUID(), nullable=False),
        sa.Column("business_domain", sa.String(), nullable=True),
        sa.Column("synonyms", JSONB(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column(
            "createdAt",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updatedAt",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"]),
        sa.ForeignKeyConstraint(["database_id"], ["database.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("business_glossary_term")
    op.drop_table("catalog_asset")
