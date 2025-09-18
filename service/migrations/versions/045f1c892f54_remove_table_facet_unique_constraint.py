"""remove table_facet unique constraint

Revision ID: 045f1c892f54
Revises: 047e24c2957e
Create Date: 2025-09-18 09:55:15.652748

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "045f1c892f54"
down_revision: Union[str, None] = "047e24c2957e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite doesn't support dropping constraints, so we need to recreate the table
    # Create new table without the unique constraint
    op.create_table(
        "table_facet_new",
        sa.Column("asset_id", sa.String(36), nullable=False),
        sa.Column("schema", sa.String(), nullable=True),
        sa.Column("table_name", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["asset.id"]),
        sa.PrimaryKeyConstraint("asset_id"),
    )

    op.execute("INSERT INTO table_facet_new SELECT * FROM table_facet")

    op.drop_table("table_facet")

    op.rename_table("table_facet_new", "table_facet")


def downgrade() -> None:
    op.create_table(
        "table_facet_new",
        sa.Column("asset_id", sa.String(36), nullable=False),
        sa.Column("schema", sa.String(), nullable=True),
        sa.Column("table_name", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["asset.id"]),
        sa.PrimaryKeyConstraint("asset_id"),
        sa.UniqueConstraint("schema", "table_name"),
    )

    op.execute("INSERT INTO table_facet_new SELECT * FROM table_facet")

    op.drop_table("table_facet")

    op.rename_table("table_facet_new", "table_facet")
