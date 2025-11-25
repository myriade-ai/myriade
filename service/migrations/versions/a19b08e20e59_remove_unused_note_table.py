"""remove unused note table

Revision ID: a19b08e20e59
Revises: 25945c932d42
Create Date: 2025-11-25 09:24:31.153135

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a19b08e20e59"
down_revision: Union[str, None] = "25945c932d42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the note table if it exists (it was never used in production)
    # Use batch mode for SQLite compatibility
    op.drop_table("note")


def downgrade() -> None:
    # Recreate the note table if needed

    op.create_table(
        "note",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("content", sa.String(), nullable=True),
        sa.Column("projectId", sa.UUID(), nullable=True),
        sa.Column(
            "createdAt",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updatedAt",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["projectId"],
            ["project.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
