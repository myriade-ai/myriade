"""add privacy field to column_facet

Revision ID: 047e24c2957e
Revises: 77eb4f67da14
Create Date: 2025-09-17 09:52:49.899980

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '047e24c2957e'
down_revision: Union[str, None] = '77eb4f67da14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add privacy JSONB column to column_facet table
    from db import JSONB
    op.add_column('column_facet', sa.Column('privacy', JSONB(), nullable=True))


def downgrade() -> None:
    # Remove privacy column from column_facet table
    op.drop_column('column_facet', 'privacy')
