"""add_archived_to_document

Revision ID: aeb0f9247d7b
Revises: 419430f6aea3
Create Date: 2025-11-07 18:05:07.310586

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "aeb0f9247d7b"
down_revision: Union[str, None] = "419430f6aea3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add archived column to document table
    op.add_column(
        "document",
        sa.Column("archived", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    # Remove archived column from document table
    op.drop_column("document", "archived")
