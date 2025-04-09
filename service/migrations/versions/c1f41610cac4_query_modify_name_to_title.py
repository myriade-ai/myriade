"""Query: modify name to title

Revision ID: c1f41610cac4
Revises: be42ad21b0c9
Create Date: 2025-04-09 19:08:19.188231

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1f41610cac4"
down_revision: Union[str, None] = "be42ad21b0c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("query", "query", new_column_name="title")


def downgrade() -> None:
    op.alter_column("query", "title", new_column_name="query")
