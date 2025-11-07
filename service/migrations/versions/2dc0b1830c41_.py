"""empty message

Revision ID: 2dc0b1830c41
Revises: 06756ce6db5b, af6ff2d17d32
Create Date: 2025-11-07 15:19:19.993427

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "2dc0b1830c41"
down_revision: Union[str, None] = ("06756ce6db5b", "af6ff2d17d32")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
