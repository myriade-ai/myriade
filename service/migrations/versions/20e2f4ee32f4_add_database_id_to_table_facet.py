"""add database id to table facet

Revision ID: 20e2f4ee32f4
Revises: 86127ef44269
Create Date: 2024-06-02 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from db import UUID

# revision identifiers, used by Alembic.
revision: str = "20e2f4ee32f4"
down_revision: Union[str, None] = "86127ef44269"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add database_id column to table_facet
    op.add_column("table_facet", sa.Column("database_id", UUID(), nullable=True))

    table_facet_table = sa.table(
        "table_facet",
        sa.column("asset_id", UUID()),
        sa.column("database_id", UUID()),
    )
    asset_table = sa.table(
        "asset",
        sa.column("id", UUID()),
        sa.column("database_id", UUID()),
    )

    connection = op.get_bind()
    results = connection.execute(
        sa.select(
            table_facet_table.c.asset_id,
            asset_table.c.database_id,
        ).select_from(
            table_facet_table.join(
                asset_table, table_facet_table.c.asset_id == asset_table.c.id
            )
        )
    ).fetchall()

    for asset_id, database_id in results:
        connection.execute(
            table_facet_table.update()
            .where(table_facet_table.c.asset_id == asset_id)
            .values(database_id=database_id)
        )

    op.alter_column("table_facet", "database_id", nullable=False)

    op.create_foreign_key(
        "table_facet_database_id_fkey",
        "table_facet",
        "database",
        ["database_id"],
        ["id"],
    )

    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.drop_constraint(
            "table_facet_schema_table_name_key",
            "table_facet",
            type_="unique",
        )

    op.create_unique_constraint(
        "uq_table_facet_database_schema_table",
        "table_facet",
        ["database_id", "schema", "table_name"],
    )


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_constraint(
        "uq_table_facet_database_schema_table",
        "table_facet",
        type_="unique",
    )

    if bind.dialect.name != "sqlite":
        op.create_unique_constraint(
            "table_facet_schema_table_name_key",
            "table_facet",
            ["schema", "table_name"],
        )

    op.drop_constraint("table_facet_database_id_fkey", "table_facet", type_="foreignkey")
    op.drop_column("table_facet", "database_id")
