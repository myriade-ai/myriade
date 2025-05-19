"""add user favorites

Revision ID: add_user_favorites
Revises: 1f6fd3b9e901
Create Date: 2025-05-19 15:15:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID


revision: str = 'add_user_favorites'
down_revision: Union[str, None] = '1f6fd3b9e901'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_favorite',
        sa.Column(
            'id', 
            UUID(), 
            server_default=sa.text('gen_random_uuid_v7()'), 
            nullable=False
        ),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('query_id', UUID(), nullable=True),
        sa.Column('chart_id', UUID(), nullable=True),
        sa.Column(
            'createdAt', 
            sa.DateTime(), 
            server_default=sa.func.now(), 
            nullable=False
        ),
        sa.Column(
            'updatedAt', 
            sa.DateTime(), 
            server_default=sa.func.now(), 
            onupdate=sa.func.now(), 
            nullable=False
        ),
        sa.CheckConstraint(
            '(query_id IS NOT NULL AND chart_id IS NULL) OR '
            '(query_id IS NULL AND chart_id IS NOT NULL)',
            name='check_favorite_type'
        ),
        sa.ForeignKeyConstraint(['chart_id'], ['chart.id'], ),
        sa.ForeignKeyConstraint(['query_id'], ['query.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('user_favorite')
