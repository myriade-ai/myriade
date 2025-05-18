"""Switch to uuid

Revision ID: 474420e93417
Revises: 2ba0d4f73bb9
Create Date: 2025-05-17 12:14:21.941896

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "474420e93417"
down_revision: Union[str, None] = "2ba0d4f73bb9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rewrite all primary- and foreign-key integer columns to UUID.

    Strategy per table (parent):
    1.  Add a temporary UUID column with server-side default (gen_random_uuid()).
    2.  For every referencing child column add its own temporary UUID column.
    3.  Populate the child temporary column using the deterministic mapping
        parent.id -> parent.id_uuid.
    4.  Drop FKs on the integer columns and drop the parent PK.
    5.  Rename integer columns to *_int and the *_uuid columns to the canonical
        column name.
    6.  Re-create PKs & FKs on the UUID columns.

    This keeps source data intact (integer columns are retained as *_int) so the
    migration is fully reversible by hand even though the downgrade() section
    below is left empty on purpose.
    """

    # Native SQL access handle
    conn = op.get_bind()

    # Ensure we have pgcrypto (gen_random_uuid)
    conn.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))

    # ------------------------------------------------------------------
    # Definition of the parent → children mapping.
    # Every child tuple is (<child_table>, <child_fk_column>)
    # ------------------------------------------------------------------
    TABLE_GRAPH = {
        # core / root tables
        "database": {
            "pk": "id",
            "children": [
                ("project", "databaseId"),
                ("query", "databaseId"),
                ("conversation", "databaseId"),
                ("issues", "database_id"),
                ("business_entity", "database_id"),
            ],
        },
        "business_entity": {
            "pk": "id",
            "children": [
                ("issues", "business_entity_id"),
            ],
        },
        "project": {
            "pk": "id",
            "children": [
                ("note", "projectId"),
                ("conversation", "projectId"),
                ("project_tables", "projectId"),
            ],
        },
        "query": {
            "pk": "id",
            "children": [
                ("chart", "queryId"),
                ("conversation_message", "queryId"),
            ],
        },
        "chart": {
            "pk": "id",
            "children": [
                ("conversation_message", "chartId"),
            ],
        },
        "conversation": {
            "pk": "id",
            "children": [
                ("conversation_message", "conversationId"),
                ("business_entity", "review_conversation_id"),
            ],
        },
        "conversation_message": {
            "pk": "id",
            "children": [
                ("issues", "message_id"),
            ],
        },
        # Leaf tables (no children of their own)
        "project_tables": {"pk": "id", "children": []},
        "note": {"pk": "id", "children": []},
        "issues": {"pk": "id", "children": []},
    }

    # Helper for proper quoting of identifiers that may be reserved words
    def qi(name: str) -> str:
        """Return identifier quoted with double-quotes."""
        return f'"{name}"'

    # ------------------------------------------------------------------
    # Perform migration per parent table (order matters – parents first).
    # ------------------------------------------------------------------
    for parent, cfg in TABLE_GRAPH.items():
        pk_col = cfg["pk"]

        parent_tmp_col = f"{pk_col}_uuid"

        # 1. Add temp UUID column to parent (NOT NULL, default)
        op.add_column(
            parent,
            sa.Column(
                parent_tmp_col,
                sa.dialects.postgresql.UUID(),
                nullable=False,
                server_default=sa.text("gen_random_uuid()"),
            ),
        )

        # 2. Add temp columns to children *before* we touch constraints
        for child_table, child_col in cfg["children"]:
            child_tmp_col = f"{child_col}_uuid"
            op.add_column(
                child_table,
                sa.Column(child_tmp_col, sa.dialects.postgresql.UUID()),
            )

        # 3. Populate temp child columns with deterministic mapping
        for child_table, child_col in cfg["children"]:
            child_tmp_col = f"{child_col}_uuid"
            conn.execute(
                sa.text(
                    f"""
                    UPDATE {qi(child_table)} AS c
                    SET {qi(child_tmp_col)} = p.{parent_tmp_col}
                    FROM {qi(parent)} AS p
                    WHERE c.{qi(child_col)} = p.{qi(pk_col)}
                    """
                )
            )

        # 4. Drop constraints on old integer columns
        #    Simply drop the parent primary key with CASCADE which automatically
        #    removes every referencing foreign key. That avoids having to guess
        #    the FK names which may include suffixes like _fkey1, _fkey2, …

        pk_name = f"{parent}_pkey"
        conn.execute(
            sa.text(
                f"ALTER TABLE {qi(parent)} DROP CONSTRAINT IF EXISTS {qi(pk_name)} CASCADE"  # noqa: E501
            )
        )

        # 5. Rename columns:  <col> -> <col>_int, <col>_uuid -> <col>
        op.alter_column(parent, pk_col, new_column_name=f"{pk_col}_int")
        op.alter_column(parent, parent_tmp_col, new_column_name=pk_col)

        for child_table, child_col in cfg["children"]:
            op.alter_column(child_table, child_col, new_column_name=f"{child_col}_int")
            op.alter_column(child_table, f"{child_col}_uuid", new_column_name=child_col)

        # 6. Re-create constraints on the UUID columns
        op.create_primary_key(pk_name, parent, [pk_col])

        for child_table, child_col in cfg["children"]:
            fk_name = f"{child_table}_{child_col}_fkey"
            op.create_foreign_key(
                fk_name,
                child_table,
                parent,
                [child_col],
                [pk_col],
            )


def downgrade() -> None:
    pass
