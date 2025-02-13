"""create admin user

Revision ID: 4b610242919c
Revises: f5da7bf41365
Create Date: 2023-08-13 13:31:45.233738

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import column, insert, table

from back.models import User

# revision identifiers, used by Alembic.
revision: str = "4b610242919c"
down_revision: Union[str, None] = "f5da7bf41365"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create admin user
    op.execute(insert(User).values(email="admin@localhost", id="admin"))


def downgrade() -> None:
    # Delete admin user
    op.execute(table("user").delete().where(column("email") == "admin@localhost"))
