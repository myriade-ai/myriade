"""merge_syncing_support_and_view_support

Revision ID: 925f5be3d756
Revises: d3f4e5a6b7c8, 6bb81bb6b719
Create Date: 2025-10-27 10:32:29.085072

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "925f5be3d756"
down_revision: Union[str, None] = ("d3f4e5a6b7c8", "6bb81bb6b719")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
