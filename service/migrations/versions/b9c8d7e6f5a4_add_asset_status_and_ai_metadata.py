"""add asset status and AI metadata

Revision ID: b9c8d7e6f5a4
Revises: a1b2c3d4e5f6
Create Date: 2025-10-13 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b9c8d7e6f5a4"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add status column as string for both PostgreSQL and SQLite
    op.add_column(
        "asset",
        sa.Column(
            "status",
            sa.String(),
            nullable=True,
        ),
    )

    # Add AI metadata columns (work for both PostgreSQL and SQLite)
    op.add_column("asset", sa.Column("ai_suggestion", sa.Text(), nullable=True))
    op.add_column("asset", sa.Column("ai_flag_reason", sa.Text(), nullable=True))

    # Drop the deprecated reviewed column from asset and term tables
    op.drop_column("asset", "reviewed")
    op.drop_column("term", "reviewed")


def downgrade() -> None:
    # Restore the reviewed columns
    op.add_column(
        "term",
        sa.Column("reviewed", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.add_column(
        "asset",
        sa.Column("reviewed", sa.Boolean(), nullable=False, server_default="0"),
    )

    # Migrate status back to reviewed
    op.execute(
        """
        UPDATE asset
        SET reviewed = CASE
            WHEN status = 'validated' THEN 1
            ELSE 0
        END
        """
    )

    # Drop the new columns
    op.drop_column("asset", "ai_flag_reason")
    op.drop_column("asset", "ai_suggestion")
    op.drop_column("asset", "status")
