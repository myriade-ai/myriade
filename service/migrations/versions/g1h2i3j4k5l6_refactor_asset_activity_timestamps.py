"""Refactor asset_activity to use DefaultBase timestamps

Revision ID: g1h2i3j4k5l6
Revises: 83cc4141e4de
Create Date: 2025-12-08 12:00:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from config import DATABASE_URL

revision: str = "g1h2i3j4k5l6"
down_revision: Union[str, None] = "83cc4141e4de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

POSTGRES_SERVER_DEFAULT = sa.text("CURRENT_TIMESTAMP")
SQLITE_SERVER_DEFAULT = sa.text("STRFTIME('%Y-%m-%dT%H:%M:%fZ', 'now')")


def _upgrade_postgres() -> None:
    # Rename created_at to createdAt
    op.alter_column(
        "asset_activity",
        "created_at",
        new_column_name="createdAt",
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
    )

    # Add updatedAt column
    op.add_column(
        "asset_activity",
        sa.Column(
            "updatedAt",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=POSTGRES_SERVER_DEFAULT,
        ),
    )

    # Set updatedAt to match createdAt for existing rows
    op.execute(sa.text('UPDATE "asset_activity" SET "updatedAt" = "createdAt"'))


def _upgrade_sqlite() -> None:
    # SQLite requires batch mode for column renames
    with op.batch_alter_table("asset_activity", recreate="always") as batch_op:
        batch_op.alter_column(
            "created_at",
            new_column_name="createdAt",
            existing_type=sa.DateTime(),
            existing_nullable=False,
        )
        batch_op.add_column(
            sa.Column(
                "updatedAt",
                sa.DateTime(),
                nullable=False,
                server_default=SQLITE_SERVER_DEFAULT,
            ),
        )

    # Set updatedAt to match createdAt for existing rows
    op.execute(sa.text('UPDATE "asset_activity" SET "updatedAt" = "createdAt"'))


def upgrade() -> None:
    if DATABASE_URL.startswith("postgres"):
        _upgrade_postgres()
    else:
        _upgrade_sqlite()


def _downgrade_postgres() -> None:
    # Drop updatedAt column
    op.drop_column("asset_activity", "updatedAt")

    # Rename createdAt back to created_at
    op.alter_column(
        "asset_activity",
        "createdAt",
        new_column_name="created_at",
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
    )


def _downgrade_sqlite() -> None:
    with op.batch_alter_table("asset_activity", recreate="always") as batch_op:
        batch_op.drop_column("updatedAt")
        batch_op.alter_column(
            "createdAt",
            new_column_name="created_at",
            existing_type=sa.DateTime(),
            existing_nullable=False,
        )


def downgrade() -> None:
    if DATABASE_URL.startswith("postgres"):
        _downgrade_postgres()
    else:
        _downgrade_sqlite()
