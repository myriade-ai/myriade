"""add dbt sync fields to database

Revision ID: a1b2c3d4e5f8
Revises: 3f2b8c41d4aa
Create Date: 2025-01-10 00:00:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f8"
down_revision: Union[str, None] = "3f2b8c41d4aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add DBT sync tracking fields to database table
    op.add_column(
        "database",
        sa.Column("last_dbt_commit_hash", sa.String(), nullable=True),
    )
    op.add_column(
        "database",
        sa.Column(
            "dbt_last_synced_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "database",
        sa.Column(
            "dbt_sync_status",
            sa.String(),
            nullable=False,
            server_default="idle",
        ),
    )
    op.add_column(
        "database",
        sa.Column(
            "dbt_generation_started_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "database",
        sa.Column("dbt_generation_error", sa.String(), nullable=True),
    )


def downgrade() -> None:
    # Remove DBT sync tracking fields from database table
    op.drop_column("database", "dbt_generation_error")
    op.drop_column("database", "dbt_generation_started_at")
    op.drop_column("database", "dbt_sync_status")
    op.drop_column("database", "dbt_last_synced_at")
    op.drop_column("database", "last_dbt_commit_hash")
