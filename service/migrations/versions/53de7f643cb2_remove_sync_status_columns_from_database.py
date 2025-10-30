"""remove_sync_status_columns_from_database

Revision ID: 53de7f643cb2
Revises: d019f75039d5
Create Date: 2025-10-30 14:56:00.490376

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "53de7f643cb2"
down_revision: Union[str, None] = "d019f75039d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove sync-related columns from database table
    # These are now managed in-memory only
    with op.batch_alter_table("database", schema=None) as batch_op:
        batch_op.drop_column("sync_error")
        batch_op.drop_column("sync_completed_at")
        batch_op.drop_column("sync_started_at")
        batch_op.drop_column("sync_progress")
        batch_op.drop_column("sync_status")


def downgrade() -> None:
    # Re-add sync-related columns if downgrade is needed
    with op.batch_alter_table("database", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "sync_status",
                sa.Enum(
                    "idle", "syncing", "completed", "failed", name="sync_status_enum"
                ),
                server_default="idle",
                nullable=True,
            )
        )
        batch_op.add_column(sa.Column("sync_progress", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("sync_started_at", sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column("sync_completed_at", sa.DateTime(), nullable=True)
        )
        batch_op.add_column(sa.Column("sync_error", sa.String(), nullable=True))
