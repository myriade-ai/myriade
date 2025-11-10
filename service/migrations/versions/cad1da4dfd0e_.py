"""empty message

Revision ID: cad1da4dfd0e
Revises: 0642395ff862, e1f2c3d4e5f6
Create Date: 2025-11-10 11:23:14.578004

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cad1da4dfd0e'
down_revision: Union[str, None] = ('0642395ff862', 'e1f2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
