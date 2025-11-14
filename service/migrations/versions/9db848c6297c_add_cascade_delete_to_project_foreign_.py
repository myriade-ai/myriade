"""add cascade delete to project foreign keys

Revision ID: 9db848c6297c
Revises: 0626815234ba
Create Date: 2025-11-14 12:11:25.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9db848c6297c"
down_revision: Union[str, None] = "0626815234ba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Foreign key constraint names
CHART_QUERY_FK = "chart_queryId_fkey"
PROJECT_TABLES_PROJECT_FK = "project_tables_projectId_fkey"
NOTE_PROJECT_FK = "note_projectId_fkey"
CONVERSATION_PROJECT_FK = "conversation_projectId_fkey"
SCHEMA_FACET_PARENT_DB_FK = "schema_facet_parent_database_asset_id_fkey"
TABLE_FACET_PARENT_SCHEMA_FK = "table_facet_parent_schema_asset_id_fkey"
COLUMN_FACET_PARENT_TABLE_FK = "column_facet_parent_table_asset_id_fkey"


def upgrade() -> None:
    # Chart.queryId -> Query.id (CASCADE)
    with op.batch_alter_table("chart", schema=None) as batch_op:
        batch_op.drop_constraint(CHART_QUERY_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            CHART_QUERY_FK,
            "query",
            ["queryId"],
            ["id"],
            ondelete="CASCADE",
        )

    # ProjectTables.projectId -> Project.id (CASCADE)
    with op.batch_alter_table("project_tables", schema=None) as batch_op:
        batch_op.drop_constraint(PROJECT_TABLES_PROJECT_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            PROJECT_TABLES_PROJECT_FK,
            "project",
            ["projectId"],
            ["id"],
            ondelete="CASCADE",
        )

    # Note.projectId -> Project.id (CASCADE)
    with op.batch_alter_table("note", schema=None) as batch_op:
        batch_op.drop_constraint(NOTE_PROJECT_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            NOTE_PROJECT_FK,
            "project",
            ["projectId"],
            ["id"],
            ondelete="CASCADE",
        )

    # Conversation.projectId -> Project.id (SET NULL)
    with op.batch_alter_table("conversation", schema=None) as batch_op:
        batch_op.drop_constraint(CONVERSATION_PROJECT_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            CONVERSATION_PROJECT_FK,
            "project",
            ["projectId"],
            ["id"],
            ondelete="SET NULL",
        )

    # Asset self-references in facets (CASCADE)
    # SchemaFacet.parent_database_asset_id -> Asset.id
    with op.batch_alter_table("schema_facet", schema=None) as batch_op:
        batch_op.drop_constraint(SCHEMA_FACET_PARENT_DB_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            SCHEMA_FACET_PARENT_DB_FK,
            "asset",
            ["parent_database_asset_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # TableFacet.parent_schema_asset_id -> Asset.id
    with op.batch_alter_table("table_facet", schema=None) as batch_op:
        batch_op.drop_constraint(TABLE_FACET_PARENT_SCHEMA_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            TABLE_FACET_PARENT_SCHEMA_FK,
            "asset",
            ["parent_schema_asset_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # ColumnFacet.parent_table_asset_id -> Asset.id
    with op.batch_alter_table("column_facet", schema=None) as batch_op:
        batch_op.drop_constraint(COLUMN_FACET_PARENT_TABLE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            COLUMN_FACET_PARENT_TABLE_FK,
            "asset",
            ["parent_table_asset_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    # Reverse order for downgrade

    # Remove CASCADE from asset self-references
    with op.batch_alter_table("column_facet", schema=None) as batch_op:
        batch_op.drop_constraint(COLUMN_FACET_PARENT_TABLE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            COLUMN_FACET_PARENT_TABLE_FK,
            "asset",
            ["parent_table_asset_id"],
            ["id"],
        )

    with op.batch_alter_table("table_facet", schema=None) as batch_op:
        batch_op.drop_constraint(TABLE_FACET_PARENT_SCHEMA_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            TABLE_FACET_PARENT_SCHEMA_FK,
            "asset",
            ["parent_schema_asset_id"],
            ["id"],
        )

    with op.batch_alter_table("schema_facet", schema=None) as batch_op:
        batch_op.drop_constraint(SCHEMA_FACET_PARENT_DB_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            SCHEMA_FACET_PARENT_DB_FK,
            "asset",
            ["parent_database_asset_id"],
            ["id"],
        )

    with op.batch_alter_table("conversation", schema=None) as batch_op:
        batch_op.drop_constraint(CONVERSATION_PROJECT_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            CONVERSATION_PROJECT_FK,
            "project",
            ["projectId"],
            ["id"],
        )

    with op.batch_alter_table("note", schema=None) as batch_op:
        batch_op.drop_constraint(NOTE_PROJECT_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            NOTE_PROJECT_FK,
            "project",
            ["projectId"],
            ["id"],
        )

    with op.batch_alter_table("project_tables", schema=None) as batch_op:
        batch_op.drop_constraint(PROJECT_TABLES_PROJECT_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            PROJECT_TABLES_PROJECT_FK,
            "project",
            ["projectId"],
            ["id"],
        )

    with op.batch_alter_table("chart", schema=None) as batch_op:
        batch_op.drop_constraint(CHART_QUERY_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            CHART_QUERY_FK,
            "query",
            ["queryId"],
            ["id"],
        )
