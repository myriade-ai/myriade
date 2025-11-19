"""empty message

Revision ID: 8411ff117e84
Revises: 1e36f0e1a315, dabb5b1e2cad
Create Date: 2025-11-17 16:24:14.988201

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "8411ff117e84"
down_revision: Union[str, None] = ("1e36f0e1a315", "dabb5b1e2cad")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
