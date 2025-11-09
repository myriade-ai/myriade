"""add_deleted_to_document

Revision ID: 7c8150e1bdbe
Revises: aeb0f9247d7b
Create Date: 2025-11-07 18:09:52.937002

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7c8150e1bdbe"
down_revision: Union[str, None] = "aeb0f9247d7b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add deleted column to document table
    op.add_column(
        "document",
        sa.Column("deleted", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    # Remove deleted column from document table
    op.drop_column("document", "deleted")
