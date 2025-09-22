"""merge privacy field and database id migrations

Revision ID: c3dae8db7eae
Revises: 047e24c2957e, 20e2f4ee32f4
Create Date: 2025-09-22 11:28:21.912541

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "c3dae8db7eae"
down_revision: Union[str, None] = ("047e24c2957e", "20e2f4ee32f4")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
