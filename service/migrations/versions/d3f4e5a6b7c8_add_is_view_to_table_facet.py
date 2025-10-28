"""add table_type to table_facet

Revision ID: d3f4e5a6b7c8
Revises: c9d4e5f6a7b8
Create Date: 2025-10-24 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d3f4e5a6b7c8"
down_revision: Union[str, None] = "c9d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add table_type string column to table_facet table (check if exists first)
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col["name"] for col in inspector.get_columns("table_facet")]

    if "table_type" not in columns:
        op.add_column(
            "table_facet",
            sa.Column("table_type", sa.String(), nullable=True, default="TABLE"),
        )
        # Set default value for existing rows
        op.execute(
            "UPDATE table_facet SET table_type = 'TABLE' WHERE table_type IS NULL"
        )


def downgrade() -> None:
    # Remove table_type column from table_facet table
    op.drop_column("table_facet", "table_type")
