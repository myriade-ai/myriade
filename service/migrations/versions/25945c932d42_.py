"""empty message

Revision ID: 25945c932d42
Revises: 00abc8339df1, 8411ff117e84
Create Date: 2025-11-19 16:38:00.135743

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "25945c932d42"
down_revision: Union[str, None] = ("00abc8339df1", "8411ff117e84")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
