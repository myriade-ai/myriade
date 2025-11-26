"""add_status_to_asset_activity

Revision ID: e3487c9647e2
Revises: 9ea914b67343
Create Date: 2025-11-25 23:43:22.970468

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e3487c9647e2"
down_revision: Union[str, None] = "9ea914b67343"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add status column to asset_activity for tracking agent task status
    op.add_column("asset_activity", sa.Column("status", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("asset_activity", "status")
