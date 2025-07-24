"""add_credits_to_user

Revision ID: e0c32661a349
Revises: 050bddebb99e
Create Date: 2025-07-24 18:26:02.218028

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e0c32661a349"
down_revision: Union[str, None] = "050bddebb99e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add credits column to user table
    op.add_column(
        "user", sa.Column("credits", sa.Integer(), nullable=False, server_default="5")
    )


def downgrade() -> None:
    # Remove credits column from user table
    op.drop_column("user", "credits")
