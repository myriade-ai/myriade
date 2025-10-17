"""add vector search support

Revision ID: d4e5f6g7h8i9
Revises: b13535e176c6
Create Date: 2025-10-17 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from config import DATABASE_URL

# revision identifiers, used by Alembic.
revision: str = "d4e5f6g7h8i9"
down_revision: Union[str, None] = "b13535e176c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add vector search support for PostgreSQL"""
    if DATABASE_URL.startswith("postgres"):
        # Enable pgvector extension
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        
        # Add embedding column to asset table
        # Using vector(384) for all-MiniLM-L6-v2 embeddings
        op.execute(
            "ALTER TABLE asset ADD COLUMN embedding vector(384)"
        )


def downgrade() -> None:
    """Remove vector search support"""
    if DATABASE_URL.startswith("postgres"):
        # Drop embedding column
        op.drop_column("asset", "embedding")
        
        # Note: We don't drop the extension as other tables might use it
        # If you want to drop it: op.execute("DROP EXTENSION IF EXISTS vector")
