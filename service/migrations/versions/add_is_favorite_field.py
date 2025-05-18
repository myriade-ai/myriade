"""add is_favorite field to query and chart

Revision ID: add_is_favorite_field
Revises: 
Create Date: 2025-05-18 21:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'add_is_favorite_field'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('query', sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('chart', sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('chart', 'is_favorite')
    op.drop_column('query', 'is_favorite')
