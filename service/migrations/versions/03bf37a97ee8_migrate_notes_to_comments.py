"""migrate notes to comments

Revision ID: 03bf37a97ee8
Revises: f1a8b2c3d4e5
Create Date: 2025-11-26 15:34:48.167719

"""

from datetime import datetime
from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "03bf37a97ee8"
down_revision: Union[str, None] = "f1a8b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate existing asset notes to AssetActivity comments."""
    # Get connection
    conn = op.get_bind()

    # Query assets with non-null notes
    assets_with_notes = conn.execute(
        sa.text(
            'SELECT id, note, "asset"."updatedAt" FROM asset WHERE note IS NOT NULL AND note != \'\''
        )
    ).fetchall()

    # Create AssetActivity comment for each note
    for asset_id, note, updatedAt in assets_with_notes:
        # Create activity entry
        activity_id = str(uuid4())
        created_at = updatedAt or datetime.utcnow()

        conn.execute(
            sa.text(
                """
                INSERT INTO asset_activity (id, asset_id, actor_id, activity_type, content, created_at)
                VALUES (:id, :asset_id, :actor_id, :activity_type, :content, :created_at)
                """
            ),
            {
                "id": activity_id,
                "asset_id": asset_id,
                "actor_id": "system",
                "activity_type": "comment",
                "content": note,
                "created_at": created_at,
            },
        )

        # Clear the note field
        conn.execute(
            sa.text("UPDATE asset SET note = NULL WHERE id = :asset_id"),
            {"asset_id": asset_id},
        )


def downgrade() -> None:
    """No-op: Cannot restore notes from comments reliably."""
    # We cannot reliably restore notes from comments since:
    # 1. We don't know which comments were originally notes
    # 2. Notes may have been edited/deleted
    # Users should restore from backup if downgrade is needed
    pass
