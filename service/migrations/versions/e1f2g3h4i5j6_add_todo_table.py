"""add_todo_table

Revision ID: e1f2g3h4i5j6
Revises: d3f4e5a6b7c8
Create Date: 2025-11-11 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from db import UUID

# revision identifiers, used by Alembic.
revision: str = "e1f2g3h4i5j6"
down_revision: Union[str, None] = "0642395ff862"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create todo table
    op.create_table(
        "todo",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("conversation_id", UUID(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "in_progress",
                "completed",
                "cancelled",
                name="todo_status_enum",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("order", sa.Integer(), nullable=False, default=0, server_default="0"),
        sa.Column(
            "createdAt",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updatedAt",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversation.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for efficient querying
    op.create_index("ix_todo_conversation_id", "todo", ["conversation_id"])
    op.create_index("ix_todo_status", "todo", ["status"])


def downgrade() -> None:
    op.drop_index("ix_todo_status", "todo")
    op.drop_index("ix_todo_conversation_id", "todo")
    op.drop_table("todo")
