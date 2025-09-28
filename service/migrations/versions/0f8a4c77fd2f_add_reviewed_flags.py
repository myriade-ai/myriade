"""add reviewed flags to catalog entities

Revision ID: 0f8a4c77fd2f
Revises: c3dae8db7eae
Create Date: 2025-03-06 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0f8a4c77fd2f"
down_revision: Union[str, None] = "c3dae8db7eae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "asset",
        sa.Column("reviewed", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "term",
        sa.Column("reviewed", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("term", "reviewed")
    op.drop_column("asset", "reviewed")
