"""empty message

Revision ID: 06756ce6db5b
Revises: 53de7f643cb2, b1c2d3e4f5g6
Create Date: 2025-11-06 15:46:01.867788

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "06756ce6db5b"
down_revision: Union[str, None] = ("53de7f643cb2", "b1c2d3e4f5g6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
