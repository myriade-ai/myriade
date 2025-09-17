"""remove tables_metadata column

Revision ID: 77eb4f67da14
Revises: 86127ef44269
Create Date: 2025-09-17 09:51:19.555082

"""

from typing import Sequence, Union
from db import JSONB

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "77eb4f67da14"
down_revision: Union[str, None] = "86127ef44269"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the tables_metadata column from the database table
    op.drop_column("database", "tables_metadata")


def downgrade() -> None:
    # Add back the tables_metadata column if needed to rollback
    op.add_column("database", sa.Column("tables_metadata", JSONB(), nullable=True))
