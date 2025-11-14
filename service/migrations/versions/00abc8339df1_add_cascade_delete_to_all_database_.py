"""add cascade delete to all database foreign keys

Revision ID: 00abc8339df1
Revises: dabb5b1e2cad
Create Date: 2025-11-14 12:30:00.000000

This migration adds CASCADE or SET NULL to all foreign key constraints
that reference database.id, query.id, project.id, asset.id, and conversation.id.

This ensures that when a database is deleted, all related records are
automatically cleaned up by the database itself, avoiding foreign key violations.

This migration consolidates all CASCADE constraints from the previous PR.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "00abc8339df1"
down_revision: Union[str, None] = "dabb5b1e2cad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def is_sqlite():
    """Check if we're running on SQLite."""
    bind = op.get_bind()
    return bind.dialect.name == "sqlite"


def modify_foreign_key(
    table_name, constraint_name, referent_table, local_cols, remote_cols, ondelete=None
):
    """
    Helper to modify a foreign key constraint in a cross-database compatible way.
    For SQLite: recreates the table with new constraints
    For PostgreSQL: drops and recreates the constraint
    """
    sqlite = is_sqlite()
    with op.batch_alter_table(
        table_name, schema=None, recreate="always" if sqlite else "auto"
    ) as batch_op:
        if not sqlite:
            # PostgreSQL: explicitly drop the old constraint
            batch_op.drop_constraint(constraint_name, type_="foreignkey")
        # Create the new constraint with ondelete
        batch_op.create_foreign_key(
            constraint_name,
            referent_table,
            local_cols,
            remote_cols,
            ondelete=ondelete,
        )


def upgrade() -> None:
    # =====================================================================
    # Part 1: Foreign keys referencing database.id (CASCADE or SET NULL)
    # =====================================================================

    modify_foreign_key(
        "query", "query_databaseId_fkey", "database", ["databaseId"], ["id"], "CASCADE"
    )
    modify_foreign_key(
        "project",
        "project_databaseId_fkey",
        "database",
        ["databaseId"],
        ["id"],
        "CASCADE",
    )
    modify_foreign_key(
        "github_integration",
        "github_integration_databaseId_fkey",
        "database",
        ["databaseId"],
        ["id"],
        "CASCADE",
    )
    modify_foreign_key(
        "github_oauth_state",
        "github_oauth_state_databaseId_fkey",
        "database",
        ["databaseId"],
        ["id"],
        "CASCADE",
    )
    modify_foreign_key(
        "document",
        "document_database_id_fkey",
        "database",
        ["database_id"],
        ["id"],
        "CASCADE",
    )
    modify_foreign_key(
        "asset",
        "asset_database_id_fkey",
        "database",
        ["database_id"],
        ["id"],
        "CASCADE",
    )
    modify_foreign_key(
        "term", "term_database_id_fkey", "database", ["database_id"], ["id"], "CASCADE"
    )
    modify_foreign_key(
        "asset_tag",
        "asset_tag_database_id_fkey",
        "database",
        ["database_id"],
        ["id"],
        "CASCADE",
    )
    modify_foreign_key(
        "issues",
        "issues_database_id_fkey",
        "database",
        ["database_id"],
        ["id"],
        "SET NULL",
    )
    modify_foreign_key(
        "business_entity",
        "business_entity_database_id_fkey",
        "database",
        ["database_id"],
        ["id"],
        "CASCADE",
    )
    modify_foreign_key(
        "database_facet",
        "database_facet_database_id_fkey",
        "database",
        ["database_id"],
        ["id"],
        "CASCADE",
    )
    modify_foreign_key(
        "schema_facet",
        "schema_facet_database_id_fkey",
        "database",
        ["database_id"],
        ["id"],
        "CASCADE",
    )
    modify_foreign_key(
        "table_facet",
        "table_facet_database_id_fkey",
        "database",
        ["database_id"],
        ["id"],
        "CASCADE",
    )
    modify_foreign_key(
        "conversation",
        "conversation_databaseId_fkey",
        "database",
        ["databaseId"],
        ["id"],
        "CASCADE",
    )
    modify_foreign_key(
        "dbt", "dbt_database_id_fkey", "database", ["database_id"], ["id"], "CASCADE"
    )

    # =====================================================================
    # Part 2: Foreign keys referencing query.id and project.id
    # =====================================================================

    modify_foreign_key(
        "chart", "chart_queryId_fkey", "query", ["queryId"], ["id"], "CASCADE"
    )
    modify_foreign_key(
        "project_tables",
        "project_tables_projectId_fkey",
        "project",
        ["projectId"],
        ["id"],
        "CASCADE",
    )
    modify_foreign_key(
        "note", "note_projectId_fkey", "project", ["projectId"], ["id"], "CASCADE"
    )
    modify_foreign_key(
        "conversation",
        "conversation_projectId_fkey",
        "project",
        ["projectId"],
        ["id"],
        "SET NULL",
    )

    # =====================================================================
    # Part 3: Asset self-references (hierarchy in catalog)
    # =====================================================================

    modify_foreign_key(
        "column_facet",
        "column_facet_parent_table_asset_id_fkey",
        "asset",
        ["parent_table_asset_id"],
        ["id"],
        "CASCADE",
    )
    modify_foreign_key(
        "table_facet",
        "fk_table_facet_parent_schema_asset",
        "asset",
        ["parent_schema_asset_id"],
        ["id"],
        "CASCADE",
    )
    modify_foreign_key(
        "schema_facet",
        "schema_facet_parent_database_asset_id_fkey",
        "asset",
        ["parent_database_asset_id"],
        ["id"],
        "CASCADE",
    )

    # =====================================================================
    # Part 4: Foreign keys referencing conversation.id and conversation_message.id
    # =====================================================================

    modify_foreign_key(
        "conversation_message",
        "conversation_message_conversationId_fkey",
        "conversation",
        ["conversationId"],
        ["id"],
        "CASCADE",
    )
    modify_foreign_key(
        "issues",
        "issues_message_id_fkey",
        "conversation_message",
        ["message_id"],
        ["id"],
        "SET NULL",
    )
    modify_foreign_key(
        "business_entity",
        "business_entity_review_conversation_id_fkey",
        "conversation",
        ["review_conversation_id"],
        ["id"],
        "SET NULL",
    )
    modify_foreign_key(
        "issues",
        "issues_business_entity_id_fkey",
        "business_entity",
        ["business_entity_id"],
        ["id"],
        "SET NULL",
    )


def downgrade() -> None:
    # Reverse all CASCADE constraints back to default (NO ACTION)
    # In reverse order of upgrade

    # Part 4: Conversation and ConversationMessage references
    modify_foreign_key(
        "issues",
        "issues_business_entity_id_fkey",
        "business_entity",
        ["business_entity_id"],
        ["id"],
    )
    modify_foreign_key(
        "business_entity",
        "business_entity_review_conversation_id_fkey",
        "conversation",
        ["review_conversation_id"],
        ["id"],
    )
    modify_foreign_key(
        "issues",
        "issues_message_id_fkey",
        "conversation_message",
        ["message_id"],
        ["id"],
    )
    modify_foreign_key(
        "conversation_message",
        "conversation_message_conversationId_fkey",
        "conversation",
        ["conversationId"],
        ["id"],
    )

    # Part 3: Asset self-references
    modify_foreign_key(
        "schema_facet",
        "schema_facet_parent_database_asset_id_fkey",
        "asset",
        ["parent_database_asset_id"],
        ["id"],
    )
    modify_foreign_key(
        "table_facet",
        "fk_table_facet_parent_schema_asset",
        "asset",
        ["parent_schema_asset_id"],
        ["id"],
    )
    modify_foreign_key(
        "column_facet",
        "column_facet_parent_table_asset_id_fkey",
        "asset",
        ["parent_table_asset_id"],
        ["id"],
    )

    # Part 2: Query and Project references
    modify_foreign_key(
        "conversation",
        "conversation_projectId_fkey",
        "project",
        ["projectId"],
        ["id"],
    )
    modify_foreign_key("note", "note_projectId_fkey", "project", ["projectId"], ["id"])
    modify_foreign_key(
        "project_tables",
        "project_tables_projectId_fkey",
        "project",
        ["projectId"],
        ["id"],
    )
    modify_foreign_key("chart", "chart_queryId_fkey", "query", ["queryId"], ["id"])

    # Part 1: Database references
    modify_foreign_key(
        "dbt", "dbt_database_id_fkey", "database", ["database_id"], ["id"]
    )
    modify_foreign_key(
        "conversation",
        "conversation_databaseId_fkey",
        "database",
        ["databaseId"],
        ["id"],
    )
    modify_foreign_key(
        "table_facet",
        "table_facet_database_id_fkey",
        "database",
        ["database_id"],
        ["id"],
    )
    modify_foreign_key(
        "schema_facet",
        "schema_facet_database_id_fkey",
        "database",
        ["database_id"],
        ["id"],
    )
    modify_foreign_key(
        "database_facet",
        "database_facet_database_id_fkey",
        "database",
        ["database_id"],
        ["id"],
    )
    modify_foreign_key(
        "business_entity",
        "business_entity_database_id_fkey",
        "database",
        ["database_id"],
        ["id"],
    )
    modify_foreign_key(
        "issues", "issues_database_id_fkey", "database", ["database_id"], ["id"]
    )
    modify_foreign_key(
        "asset_tag", "asset_tag_database_id_fkey", "database", ["database_id"], ["id"]
    )
    modify_foreign_key(
        "term", "term_database_id_fkey", "database", ["database_id"], ["id"]
    )
    modify_foreign_key(
        "asset", "asset_database_id_fkey", "database", ["database_id"], ["id"]
    )
    modify_foreign_key(
        "document", "document_database_id_fkey", "database", ["database_id"], ["id"]
    )
    modify_foreign_key(
        "github_oauth_state",
        "github_oauth_state_databaseId_fkey",
        "database",
        ["databaseId"],
        ["id"],
    )
    modify_foreign_key(
        "github_integration",
        "github_integration_databaseId_fkey",
        "database",
        ["databaseId"],
        ["id"],
    )
    modify_foreign_key(
        "project", "project_databaseId_fkey", "database", ["databaseId"], ["id"]
    )
    modify_foreign_key(
        "query", "query_databaseId_fkey", "database", ["databaseId"], ["id"]
    )
