"""add tables_metadata

Revision ID: a167337af939
Revises: bb9fe32018b6
Create Date: 2023-09-08 19:00:54.438146

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a167337af939"
down_revision: Union[str, None] = "bb9fe32018b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

tables_metadata = [
    {
        "name": "clients",
        "schema": "main",
        "columns": [
            {
                "name": "id",
                "type": "NUMERIC",
                "Noneable": True,
                "description": None,
            },
            {
                "name": "name",
                "type": "VARCHAR(255)",
                "Noneable": False,
                "description": None,
            },
            {
                "name": "email",
                "type": "VARCHAR(255)",
                "Noneable": False,
                "description": None,
            },
            {
                "name": "phone",
                "type": "VARCHAR(255)",
                "Noneable": False,
                "description": None,
            },
            {
                "name": "address",
                "type": "VARCHAR(255)",
                "Noneable": False,
                "description": None,
            },
        ],
        "is_view": False,
        "description": None,
    },
    {
        "name": "orders",
        "schema": "main",
        "columns": [
            {
                "name": "id",
                "type": "NUMERIC",
                "Noneable": True,
                "description": None,
            },
            {
                "name": "client_id",
                "type": "INTEGER",
                "Noneable": False,
                "description": None,
            },
            {
                "name": "product_id",
                "type": "INTEGER",
                "Noneable": False,
                "description": None,
            },
            {
                "name": "quantity",
                "type": "INTEGER",
                "Noneable": False,
                "description": None,
            },
        ],
        "is_view": False,
        "description": None,
    },
    {
        "name": "products",
        "schema": "main",
        "columns": [
            {
                "name": "id",
                "type": "NUMERIC",
                "Noneable": True,
                "description": None,
            },
            {
                "name": "name",
                "type": "VARCHAR(255)",
                "Noneable": False,
                "description": None,
            },
            {
                "name": "price",
                "type": "DECIMAL(10, 2)",
                "Noneable": False,
                "description": None,
            },
        ],
        "is_view": False,
        "description": None,
    },
    {
        "name": "clients",
        "schema": "main",
        "columns": [
            {
                "name": "id",
                "type": "NUMERIC",
                "Noneable": True,
                "description": None,
            },
            {
                "name": "name",
                "type": "VARCHAR(255)",
                "Noneable": False,
                "description": None,
            },
            {
                "name": "email",
                "type": "VARCHAR(255)",
                "Noneable": False,
                "description": None,
            },
            {
                "name": "phone",
                "type": "VARCHAR(255)",
                "Noneable": False,
                "description": None,
            },
            {
                "name": "address",
                "type": "VARCHAR(255)",
                "Noneable": False,
                "description": None,
            },
        ],
        "is_view": False,
        "description": None,
    },
    {
        "name": "orders",
        "schema": "main",
        "columns": [
            {
                "name": "id",
                "type": "NUMERIC",
                "Noneable": True,
                "description": None,
            },
            {
                "name": "client_id",
                "type": "INTEGER",
                "Noneable": False,
                "description": None,
            },
            {
                "name": "product_id",
                "type": "INTEGER",
                "Noneable": False,
                "description": None,
            },
            {
                "name": "quantity",
                "type": "INTEGER",
                "Noneable": False,
                "description": None,
            },
        ],
        "is_view": False,
        "description": None,
    },
    {
        "name": "products",
        "schema": "main",
        "columns": [
            {
                "name": "id",
                "type": "NUMERIC",
                "Noneable": True,
                "description": None,
            },
            {
                "name": "name",
                "type": "VARCHAR(255)",
                "Noneable": False,
                "description": None,
            },
            {
                "name": "price",
                "type": "DECIMAL(10, 2)",
                "Noneable": False,
                "description": None,
            },
        ],
        "is_view": False,
        "description": None,
    },
]


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "database",
        sa.Column(
            "tables_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )
    # Add tables_metadata to sample database
    database_table = sa.Table(
        "database",
        sa.MetaData(),
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String),
        sa.Column("tables_metadata", sa.JSON),
    )

    op.execute(
        database_table.update()
        .where(database_table.c.name == "sample")
        .values(tables_metadata=tables_metadata)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("database", "tables_metadata")
    # ### end Alembic commands ###
