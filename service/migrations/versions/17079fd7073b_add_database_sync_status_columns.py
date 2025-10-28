"""add_database_sync_status_columns

Revision ID: 17079fd7073b
Revises: d3f4e5a6b7c8
Create Date: 2025-10-24 14:13:01.805703

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "17079fd7073b"
down_revision: Union[str, None] = "d3f4e5a6b7c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check existing columns
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col["name"] for col in inspector.get_columns("database")]

    # Create sync_status_enum type
    sync_status_enum = sa.Enum(
        "idle", "syncing", "completed", "failed", name="sync_status_enum"
    )
    sync_status_enum.create(op.get_bind(), checkfirst=True)

    # Add sync status columns to database table (only if they don't exist)
    if "sync_status" not in columns:
        op.add_column(
            "database",
            sa.Column(
                "sync_status", sync_status_enum, nullable=True, server_default="idle"
            ),
        )
    if "sync_progress" not in columns:
        op.add_column(
            "database",
            sa.Column("sync_progress", sa.Integer(), nullable=True, server_default="0"),
        )
    if "sync_started_at" not in columns:
        op.add_column(
            "database",
            sa.Column("sync_started_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "sync_completed_at" not in columns:
        op.add_column(
            "database",
            sa.Column("sync_completed_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "sync_error" not in columns:
        op.add_column("database", sa.Column("sync_error", sa.String(), nullable=True))


def downgrade() -> None:
    # Remove columns
    op.drop_column("database", "sync_error")
    op.drop_column("database", "sync_completed_at")
    op.drop_column("database", "sync_started_at")
    op.drop_column("database", "sync_progress")
    op.drop_column("database", "sync_status")

    # Drop enum type
    sync_status_enum = sa.Enum(
        "idle", "syncing", "completed", "failed", name="sync_status_enum"
    )
    sync_status_enum.drop(op.get_bind(), checkfirst=True)
