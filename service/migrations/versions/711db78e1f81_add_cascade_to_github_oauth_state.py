"""add cascade to github_oauth_state

Revision ID: 711db78e1f81
Revises: 986d35afd76a
Create Date: 2025-11-14 12:25:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "711db78e1f81"
down_revision: Union[str, None] = "986d35afd76a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

GITHUB_OAUTH_STATE_DATABASE_FK = "github_oauth_state_databaseId_fkey"


def upgrade() -> None:
    # GithubOAuthState.databaseId -> Database.id (CASCADE)
    op.drop_constraint(
        GITHUB_OAUTH_STATE_DATABASE_FK, "github_oauth_state", type_="foreignkey"
    )
    op.create_foreign_key(
        GITHUB_OAUTH_STATE_DATABASE_FK,
        "github_oauth_state",
        "database",
        ["databaseId"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # Remove CASCADE
    op.drop_constraint(
        GITHUB_OAUTH_STATE_DATABASE_FK, "github_oauth_state", type_="foreignkey"
    )
    op.create_foreign_key(
        GITHUB_OAUTH_STATE_DATABASE_FK,
        "github_oauth_state",
        "database",
        ["databaseId"],
        ["id"],
    )
