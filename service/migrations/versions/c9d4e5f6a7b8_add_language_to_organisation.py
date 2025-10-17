"""add_language_to_organisation

Revision ID: c9d4e5f6a7b8
Revises: b13535e176c6
Create Date: 2025-10-17 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c9d4e5f6a7b8"
down_revision: Union[str, None] = "b13535e176c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add language column to organisation table
    op.add_column("organisation", sa.Column("language", sa.String(), nullable=True))


def downgrade() -> None:
    # Remove language column from organisation table
    op.drop_column("organisation", "language")
