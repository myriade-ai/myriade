"""Add asset_activity table for activity feed

Revision ID: 9ea914b67343
Revises: 7d144dc7ef11
Create Date: 2025-11-25 17:17:38.762021

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

import db

# revision identifiers, used by Alembic.
revision: str = "9ea914b67343"
down_revision: Union[str, None] = "7d144dc7ef11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "asset_activity",
        sa.Column("id", db.UUID(), nullable=False),
        sa.Column("asset_id", db.UUID(), nullable=False),
        sa.Column("actor_id", sa.String(), nullable=False),
        sa.Column("activity_type", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("changes", db.JSONB(), nullable=True),
        sa.Column("conversation_id", db.UUID(), nullable=True),
        sa.Column("created_at", db.UtcDateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["asset.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversation.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Index for efficient queries by asset
    op.create_index("ix_asset_activity_asset_id", "asset_activity", ["asset_id"])


def downgrade() -> None:
    op.drop_index("ix_asset_activity_asset_id", table_name="asset_activity")
    op.drop_table("asset_activity")
