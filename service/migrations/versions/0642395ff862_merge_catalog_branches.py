"""merge_catalog_branches

Revision ID: 0642395ff862
Revises: c71588b086e4, 7c8150e1bdbe
Create Date: 2025-11-09 19:20:17.238397

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "0642395ff862"
down_revision: Union[str, None] = ("c71588b086e4", "7c8150e1bdbe")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
