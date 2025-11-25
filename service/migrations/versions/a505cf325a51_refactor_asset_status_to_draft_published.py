"""refactor_asset_status_to_draft_published

Revision ID: a505cf325a51
Revises: 25945c932d42
Create Date: 2025-11-24 16:31:19.688653

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a505cf325a51"
down_revision: Union[str, None] = "25945c932d42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Rename ai_flag_reason to note
    op.alter_column("asset", "ai_flag_reason", new_column_name="note")

    # Step 2: Add published_by and published_at columns
    op.add_column("asset", sa.Column("published_by", sa.String(), nullable=True))
    op.add_column("asset", sa.Column("published_at", sa.DateTime(), nullable=True))

    # Step 3: Map existing statuses to new status values
    # validated, human_authored → published (published_by = "user")
    op.execute(
        """
        UPDATE asset
        SET status = 'published',
            published_by = 'user',
            published_at = COALESCE("updatedAt", "createdAt", CURRENT_TIMESTAMP)
        WHERE status IN ('validated', 'human_authored')
        """
    )

    # published_by_ai → published (published_by = "myriade-agent")
    op.execute(
        """
        UPDATE asset
        SET status = 'published',
            published_by = 'myriade-agent',
            published_at = COALESCE("updatedAt", "createdAt", CURRENT_TIMESTAMP)
        WHERE status = 'published_by_ai'
        """
    )

    # needs_review, requires_validation → draft
    op.execute(
        """
        UPDATE asset
        SET status = 'draft'
        WHERE status IN ('needs_review', 'requires_validation')
        """
    )


def downgrade() -> None:
    # Reverse status mapping (best effort - some information will be lost)
    # published with published_by="user" → human_authored
    op.execute(
        """
        UPDATE asset
        SET status = 'human_authored'
        WHERE status = 'published' AND published_by = 'user'
        """
    )

    # published with published_by="myriade-agent" → published_by_ai
    op.execute(
        """
        UPDATE asset
        SET status = 'published_by_ai'
        WHERE status = 'published' AND published_by = 'myriade-agent'
        """
    )

    # draft → needs_review (arbitrary choice, information is lost)
    op.execute(
        """
        UPDATE asset
        SET status = 'needs_review'
        WHERE status = 'draft'
        """
    )

    # Drop published_by and published_at columns
    op.drop_column("asset", "published_at")
    op.drop_column("asset", "published_by")

    # Rename note back to ai_flag_reason
    op.alter_column("asset", "note", new_column_name="ai_flag_reason")
