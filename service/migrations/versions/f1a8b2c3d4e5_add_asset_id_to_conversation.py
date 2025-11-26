"""add_asset_id_to_conversation

Revision ID: f1a8b2c3d4e5
Revises: e3487c9647e2
Create Date: 2025-01-26 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# Import custom UUID type that handles both PostgreSQL and SQLite
from db import UUID

# revision identifiers, used by Alembic.
revision: str = "f1a8b2c3d4e5"
down_revision: Union[str, None] = "e3487c9647e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add asset_id column to conversation table
    with op.batch_alter_table("conversation", schema=None) as batch_op:
        batch_op.add_column(sa.Column("asset_id", UUID(), nullable=True))
        batch_op.create_foreign_key(
            "fk_conversation_asset_id",
            "asset",
            ["asset_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_conversation_asset_id", ["asset_id"], unique=False)


def downgrade() -> None:
    # Remove asset_id column and related constraints
    with op.batch_alter_table("conversation", schema=None) as batch_op:
        batch_op.drop_index("ix_conversation_asset_id")
        batch_op.drop_constraint("fk_conversation_asset_id", type_="foreignkey")
        batch_op.drop_column("asset_id")
