"""add_columns_to_query

Revision ID: d019f75039d5
Revises: 17079fd7073b
Create Date: 2025-10-29 15:10:31.736277

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from db import JSONB

# revision identifiers, used by Alembic.
revision: str = "d019f75039d5"
down_revision: Union[str, None] = "17079fd7073b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("query", sa.Column("columns", JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("query", "columns")
