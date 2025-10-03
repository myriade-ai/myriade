"""add asset_tag table and associations

Revision ID: a1b2c3d4e5f6
Revises: f5b7d2b3ab12
Create Date: 2025-10-02 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from db import UUID

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f5b7d2b3ab12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "asset_tag",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("database_id", UUID(), nullable=False),
        sa.Column(
            "createdAt",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updatedAt",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["database_id"],
            ["database.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("database_id", "name", name="uq_asset_tag_database_name"),
    )

    op.create_table(
        "asset_tag_association",
        sa.Column("asset_id", UUID(), nullable=False),
        sa.Column("tag_id", UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["asset.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["asset_tag.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("asset_id", "tag_id"),
    )

    # Create indexes for better query performance
    op.create_index(
        "ix_asset_tag_database_id", "asset_tag", ["database_id"], unique=False
    )
    op.create_index(
        "ix_asset_tag_association_asset_id",
        "asset_tag_association",
        ["asset_id"],
        unique=False,
    )
    op.create_index(
        "ix_asset_tag_association_tag_id",
        "asset_tag_association",
        ["tag_id"],
        unique=False,
    )

    # Drop the old tags JSONB column from asset table
    op.drop_column("asset", "tags")


def downgrade() -> None:
    op.add_column("asset", sa.Column("tags", sa.JSON(), nullable=True))

    op.drop_index("ix_asset_tag_association_tag_id", table_name="asset_tag_association")
    op.drop_index(
        "ix_asset_tag_association_asset_id", table_name="asset_tag_association"
    )
    op.drop_index("ix_asset_tag_database_id", table_name="asset_tag")

    op.drop_table("asset_tag_association")

    # Drop asset_tag table
    op.drop_table("asset_tag")
