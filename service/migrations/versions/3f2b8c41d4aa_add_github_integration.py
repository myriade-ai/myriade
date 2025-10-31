"""add github integration tables and fields

Revision ID: 3f2b8c41d4aa
Revises: d019f75039d5
Create Date: 2025-10-30 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from db import UUID

# revision identifiers, used by Alembic.
revision: str = "3f2b8c41d4aa"
down_revision: Union[str, None] = "d019f75039d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "github_integration",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("databaseId", UUID(), nullable=False),
        sa.Column("access_token", sa.String(), nullable=True),
        sa.Column("refresh_token", sa.String(), nullable=True),
        sa.Column("token_type", sa.String(), nullable=True),
        sa.Column("scope", sa.String(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("repo_owner", sa.String(), nullable=True),
        sa.Column("repo_name", sa.String(), nullable=True),
        sa.Column("default_branch", sa.String(), nullable=True),
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
        sa.ForeignKeyConstraint(["databaseId"], ["database.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("databaseId", name="uq_github_integration_database"),
    )

    op.create_table(
        "github_oauth_state",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("databaseId", UUID(), nullable=False),
        sa.Column("userId", sa.String(), nullable=False),
        sa.Column("state", sa.String(length=255), nullable=False),
        sa.Column("code_verifier", sa.String(length=255), nullable=True),
        sa.Column("redirect_uri", sa.String(), nullable=True),
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
        sa.ForeignKeyConstraint(["databaseId"], ["database.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("state", name="uq_github_oauth_state_state"),
    )

    op.add_column(
        "conversation",
        sa.Column("github_branch", sa.String(), nullable=True),
    )
    op.add_column(
        "conversation",
        sa.Column("github_base_branch", sa.String(), nullable=True),
    )
    op.add_column(
        "conversation",
        sa.Column("github_repo_full_name", sa.String(), nullable=True),
    )
    op.add_column(
        "conversation",
        sa.Column("github_pr_url", sa.String(), nullable=True),
    )
    op.add_column(
        "conversation",
        sa.Column("github_pr_number", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("conversation", "github_pr_number")
    op.drop_column("conversation", "github_pr_url")
    op.drop_column("conversation", "github_repo_full_name")
    op.drop_column("conversation", "github_base_branch")
    op.drop_column("conversation", "github_branch")

    op.drop_table("github_oauth_state")
    op.drop_table("github_integration")
