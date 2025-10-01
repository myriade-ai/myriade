"""make timestamps timezone aware

Revision ID: f5b7d2b3ab12
Revises: c8852c2a5ee9
Create Date: 2025-09-20 00:00:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from config import DATABASE_URL

revision: str = "f5b7d2b3ab12"
down_revision: Union[str, None] = "9addce233509"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMESTAMP_TABLES: dict[str, tuple[str, ...]] = {
    "organisation": ("createdAt", "updatedAt"),
    "database": ("createdAt", "updatedAt"),
    "user": ("createdAt", "updatedAt"),
    "user_organisation": ("createdAt", "updatedAt"),
    "conversation": ("createdAt", "updatedAt"),
    "conversation_message": ("createdAt", "updatedAt"),
    "query": ("createdAt", "updatedAt"),
    "chart": ("createdAt", "updatedAt"),
    "project": ("createdAt", "updatedAt"),
    "project_tables": ("createdAt", "updatedAt"),
    "note": ("createdAt", "updatedAt"),
    "user_favorite": ("createdAt", "updatedAt"),
    "asset": ("createdAt", "updatedAt"),
    "term": ("createdAt", "updatedAt"),
    "issues": ("createdAt", "updatedAt"),
    "business_entity": ("createdAt", "updatedAt"),
    "metadata": ("createdAt", "updatedAt"),
}

POSTGRES_SERVER_DEFAULT = sa.text("CURRENT_TIMESTAMP")
SQLITE_SERVER_DEFAULT = sa.text("STRFTIME('%Y-%m-%dT%H:%M:%fZ', 'now')")
LEGACY_SERVER_DEFAULT = sa.text("CURRENT_TIMESTAMP")


def _upgrade_postgres() -> None:
    for table, columns in TIMESTAMP_TABLES.items():
        for column in columns:
            kwargs: dict[str, object] = {
                "existing_type": sa.DateTime(),
                "type_": sa.DateTime(timezone=True),
                "existing_nullable": False,
                "server_default": POSTGRES_SERVER_DEFAULT,
                "postgresql_using": f"\"{column}\" AT TIME ZONE 'UTC'",
            }
            if column == "updatedAt":
                kwargs["server_onupdate"] = POSTGRES_SERVER_DEFAULT
            op.alter_column(table, column, **kwargs)


def _upgrade_sqlite() -> None:
    for table, columns in TIMESTAMP_TABLES.items():
        with op.batch_alter_table(table, recreate="always") as batch_op:
            for column in columns:
                kwargs: dict[str, object] = {
                    "existing_type": sa.DateTime(),
                    "existing_nullable": False,
                    "server_default": SQLITE_SERVER_DEFAULT,
                }
                if column == "updatedAt":
                    kwargs["server_onupdate"] = SQLITE_SERVER_DEFAULT
                batch_op.alter_column(column, **kwargs)
    for table, columns in TIMESTAMP_TABLES.items():
        for column in columns:
            op.execute(
                sa.text(
                    f'UPDATE "{table}" '
                    f'SET "{column}" = strftime(\'%Y-%m-%dT%H:%M:%fZ\', "{column}") '
                    f'WHERE "{column}" IS NOT NULL AND instr("{column}", \'T\') = 0'
                )
            )


def upgrade() -> None:
    if DATABASE_URL.startswith("postgres"):
        _upgrade_postgres()
    else:
        _upgrade_sqlite()


def _downgrade_postgres() -> None:
    for table, columns in TIMESTAMP_TABLES.items():
        for column in columns:
            kwargs: dict[str, object] = {
                "existing_type": sa.DateTime(timezone=True),
                "type_": sa.DateTime(),
                "existing_nullable": False,
                "server_default": LEGACY_SERVER_DEFAULT,
                "postgresql_using": f"\"{column}\" AT TIME ZONE 'UTC'",
            }
            if column == "updatedAt":
                kwargs["server_onupdate"] = None
            op.alter_column(table, column, **kwargs)


def _downgrade_sqlite() -> None:
    for table, columns in TIMESTAMP_TABLES.items():
        with op.batch_alter_table(table, recreate="always") as batch_op:
            for column in columns:
                kwargs: dict[str, object] = {
                    "existing_type": sa.DateTime(),
                    "existing_nullable": False,
                    "server_default": LEGACY_SERVER_DEFAULT,
                }
                if column == "updatedAt":
                    kwargs["server_onupdate"] = None
                batch_op.alter_column(column, **kwargs)
    for table, columns in TIMESTAMP_TABLES.items():
        for column in columns:
            op.execute(
                sa.text(
                    f'UPDATE "{table}" '
                    f'SET "{column}" = strftime(\'%Y-%m-%d %H:%M:%S\', "{column}") '
                    f'WHERE "{column}" IS NOT NULL AND instr("{column}", \'T\') > 0'
                )
            )


def downgrade() -> None:
    if DATABASE_URL.startswith("postgres"):
        _downgrade_postgres()
    else:
        _downgrade_sqlite()
