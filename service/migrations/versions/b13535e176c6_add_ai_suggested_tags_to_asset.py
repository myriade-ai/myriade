"""add_ai_suggested_tags_to_asset

Revision ID: b13535e176c6
Revises: b9c8d7e6f5a4
Create Date: 2025-10-16 12:01:36.675141

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from db import JSONB

# revision identifiers, used by Alembic.
revision: str = "b13535e176c6"
down_revision: Union[str, None] = "b9c8d7e6f5a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add ai_suggested_tags column to asset table
    # JSONB type automatically handles PostgreSQL (native JSONB) and SQLite (JSON)
    op.add_column("asset", sa.Column("ai_suggested_tags", JSONB(), nullable=True))


def downgrade() -> None:
    # Remove ai_suggested_tags column from asset table
    op.drop_column("asset", "ai_suggested_tags")
