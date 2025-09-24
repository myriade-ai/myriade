"""add validated flag to catalog models

Revision ID: d8d74b96c4b2
Revises: c3dae8db7eae
Create Date: 2025-10-08 00:00:00.000000

"""

from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d8d74b96c4b2"
down_revision: Union[str, None] = "c3dae8db7eae"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    default_expr = sa.text("0") if bind.dialect.name == "sqlite" else sa.text("false")

    op.add_column(
        "asset",
        sa.Column(
            "validated",
            sa.Boolean(),
            nullable=False,
            server_default=default_expr,
        ),
    )
    op.add_column(
        "term",
        sa.Column(
            "validated",
            sa.Boolean(),
            nullable=False,
            server_default=default_expr,
        ),
    )


def downgrade() -> None:
    op.drop_column("term", "validated")
    op.drop_column("asset", "validated")

