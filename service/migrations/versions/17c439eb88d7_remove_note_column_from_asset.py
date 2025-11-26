"""remove note column from asset

Revision ID: 17c439eb88d7
Revises: 03bf37a97ee8
Create Date: 2025-11-26 15:35:26.044802

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '17c439eb88d7'
down_revision: Union[str, None] = '03bf37a97ee8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove note column from asset table."""
    op.drop_column('asset', 'note')


def downgrade() -> None:
    """Recreate note column in asset table."""
    op.add_column('asset', sa.Column('note', sa.Text(), nullable=True))
