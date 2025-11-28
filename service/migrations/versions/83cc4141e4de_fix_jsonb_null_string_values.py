"""fix jsonb null string values

Revision ID: 83cc4141e4de
Revises: 17c439eb88d7
Create Date: 2025-11-28 11:00:19.499403

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "83cc4141e4de"
down_revision: Union[str, None] = "17c439eb88d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fix ai_suggested_tags in asset table
    # Convert 'null' string to NULL for JSONB columns
    op.execute(
        """
        UPDATE asset
        SET ai_suggested_tags = NULL
        WHERE ai_suggested_tags::text = 'null'
        """
    )


def downgrade() -> None:
    # No downgrade needed - this is a data cleanup migration
    # The fix is permanent and beneficial
    pass
