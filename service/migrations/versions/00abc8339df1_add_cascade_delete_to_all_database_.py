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


def upgrade() -> None:
    # =====================================================================
    # Part 1: Foreign keys referencing database.id
    # =====================================================================

    # Query.databaseId -> Database.id (CASCADE)
    op.drop_constraint("query_databaseId_fkey", "query", type_="foreignkey")
    op.create_foreign_key(
        "query_databaseId_fkey",
        "query",
        "database",
        ["databaseId"],
        ["id"],
        ondelete="CASCADE",
    )

    # Project.databaseId -> Database.id (CASCADE)
    op.drop_constraint("project_databaseId_fkey", "project", type_="foreignkey")
    op.create_foreign_key(
        "project_databaseId_fkey",
        "project",
        "database",
        ["databaseId"],
        ["id"],
        ondelete="CASCADE",
    )

    # GithubIntegration.databaseId -> Database.id (CASCADE)
    op.drop_constraint(
        "github_integration_databaseId_fkey", "github_integration", type_="foreignkey"
    )
    op.create_foreign_key(
        "github_integration_databaseId_fkey",
        "github_integration",
        "database",
        ["databaseId"],
        ["id"],
        ondelete="CASCADE",
    )

    # GithubOAuthState.databaseId -> Database.id (CASCADE)
    op.drop_constraint(
        "github_oauth_state_databaseId_fkey", "github_oauth_state", type_="foreignkey"
    )
    op.create_foreign_key(
        "github_oauth_state_databaseId_fkey",
        "github_oauth_state",
        "database",
        ["databaseId"],
        ["id"],
        ondelete="CASCADE",
    )

    # Document.database_id -> Database.id (CASCADE)
    op.drop_constraint("document_database_id_fkey", "document", type_="foreignkey")
    op.create_foreign_key(
        "document_database_id_fkey",
        "document",
        "database",
        ["database_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Asset.database_id -> Database.id (CASCADE)
    op.drop_constraint("asset_database_id_fkey", "asset", type_="foreignkey")
    op.create_foreign_key(
        "asset_database_id_fkey",
        "asset",
        "database",
        ["database_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Term.database_id -> Database.id (CASCADE)
    op.drop_constraint("term_database_id_fkey", "term", type_="foreignkey")
    op.create_foreign_key(
        "term_database_id_fkey",
        "term",
        "database",
        ["database_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # AssetTag.database_id -> Database.id (CASCADE)
    op.drop_constraint("asset_tag_database_id_fkey", "asset_tag", type_="foreignkey")
    op.create_foreign_key(
        "asset_tag_database_id_fkey",
        "asset_tag",
        "database",
        ["database_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Issue.database_id -> Database.id (SET NULL - nullable field)
    op.drop_constraint("issues_database_id_fkey", "issues", type_="foreignkey")
    op.create_foreign_key(
        "issues_database_id_fkey",
        "issues",
        "database",
        ["database_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # BusinessEntity.database_id -> Database.id (CASCADE)
    op.drop_constraint(
        "business_entity_database_id_fkey", "business_entity", type_="foreignkey"
    )
    op.create_foreign_key(
        "business_entity_database_id_fkey",
        "business_entity",
        "database",
        ["database_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # DatabaseFacet.database_id -> Database.id (CASCADE)
    op.drop_constraint(
        "database_facet_database_id_fkey", "database_facet", type_="foreignkey"
    )
    op.create_foreign_key(
        "database_facet_database_id_fkey",
        "database_facet",
        "database",
        ["database_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # SchemaFacet.database_id -> Database.id (CASCADE)
    op.drop_constraint(
        "schema_facet_database_id_fkey", "schema_facet", type_="foreignkey"
    )
    op.create_foreign_key(
        "schema_facet_database_id_fkey",
        "schema_facet",
        "database",
        ["database_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # TableFacet.database_id -> Database.id (CASCADE)
    op.drop_constraint(
        "table_facet_database_id_fkey", "table_facet", type_="foreignkey"
    )
    op.create_foreign_key(
        "table_facet_database_id_fkey",
        "table_facet",
        "database",
        ["database_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Conversation.databaseId -> Database.id (CASCADE)
    op.drop_constraint(
        "conversation_databaseId_fkey", "conversation", type_="foreignkey"
    )
    op.create_foreign_key(
        "conversation_databaseId_fkey",
        "conversation",
        "database",
        ["databaseId"],
        ["id"],
        ondelete="CASCADE",
    )

    # DBT.database_id -> Database.id (CASCADE)
    op.drop_constraint("dbt_database_id_fkey", "dbt", type_="foreignkey")
    op.create_foreign_key(
        "dbt_database_id_fkey",
        "dbt",
        "database",
        ["database_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # =====================================================================
    # Part 2: Foreign keys referencing query.id and project.id
    # =====================================================================

    # Chart.queryId -> Query.id (CASCADE)
    op.drop_constraint("chart_queryId_fkey", "chart", type_="foreignkey")
    op.create_foreign_key(
        "chart_queryId_fkey",
        "chart",
        "query",
        ["queryId"],
        ["id"],
        ondelete="CASCADE",
    )

    # ProjectTables.projectId -> Project.id (CASCADE)
    op.drop_constraint(
        "project_tables_projectId_fkey", "project_tables", type_="foreignkey"
    )
    op.create_foreign_key(
        "project_tables_projectId_fkey",
        "project_tables",
        "project",
        ["projectId"],
        ["id"],
        ondelete="CASCADE",
    )

    # Note.projectId -> Project.id (CASCADE)
    op.drop_constraint("note_projectId_fkey", "note", type_="foreignkey")
    op.create_foreign_key(
        "note_projectId_fkey",
        "note",
        "project",
        ["projectId"],
        ["id"],
        ondelete="CASCADE",
    )

    # Conversation.projectId -> Project.id (SET NULL - nullable field)
    op.drop_constraint(
        "conversation_projectId_fkey", "conversation", type_="foreignkey"
    )
    op.create_foreign_key(
        "conversation_projectId_fkey",
        "conversation",
        "project",
        ["projectId"],
        ["id"],
        ondelete="SET NULL",
    )

    # =====================================================================
    # Part 3: Asset self-references (hierarchy in catalog)
    # =====================================================================

    # ColumnFacet.parent_table_asset_id -> Asset.id (CASCADE)
    op.drop_constraint(
        "column_facet_parent_table_asset_id_fkey", "column_facet", type_="foreignkey"
    )
    op.create_foreign_key(
        "column_facet_parent_table_asset_id_fkey",
        "column_facet",
        "asset",
        ["parent_table_asset_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # TableFacet.parent_schema_asset_id -> Asset.id (CASCADE)
    # Note: This constraint has a different name in the database
    op.drop_constraint(
        "fk_table_facet_parent_schema_asset", "table_facet", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_table_facet_parent_schema_asset",
        "table_facet",
        "asset",
        ["parent_schema_asset_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # SchemaFacet.parent_database_asset_id -> Asset.id (CASCADE)
    op.drop_constraint(
        "schema_facet_parent_database_asset_id_fkey", "schema_facet", type_="foreignkey"
    )
    op.create_foreign_key(
        "schema_facet_parent_database_asset_id_fkey",
        "schema_facet",
        "asset",
        ["parent_database_asset_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # =====================================================================
    # Part 4: Foreign keys referencing conversation.id and conversation_message.id
    # =====================================================================

    # ConversationMessage.conversationId -> Conversation.id (CASCADE)
    op.drop_constraint(
        "conversation_message_conversationId_fkey",
        "conversation_message",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "conversation_message_conversationId_fkey",
        "conversation_message",
        "conversation",
        ["conversationId"],
        ["id"],
        ondelete="CASCADE",
    )

    # Issue.message_id -> ConversationMessage.id (SET NULL - nullable field)
    op.drop_constraint("issues_message_id_fkey", "issues", type_="foreignkey")
    op.create_foreign_key(
        "issues_message_id_fkey",
        "issues",
        "conversation_message",
        ["message_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # BusinessEntity.review_conversation_id -> Conversation.id (SET NULL - nullable field)
    op.drop_constraint(
        "business_entity_review_conversation_id_fkey",
        "business_entity",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "business_entity_review_conversation_id_fkey",
        "business_entity",
        "conversation",
        ["review_conversation_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Issue.business_entity_id -> BusinessEntity.id (SET NULL - nullable field)
    op.drop_constraint("issues_business_entity_id_fkey", "issues", type_="foreignkey")
    op.create_foreign_key(
        "issues_business_entity_id_fkey",
        "issues",
        "business_entity",
        ["business_entity_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Reverse all CASCADE constraints back to default (NO ACTION)
    # In reverse order of upgrade

    # Part 4: Conversation and ConversationMessage references
    op.drop_constraint("issues_business_entity_id_fkey", "issues", type_="foreignkey")
    op.create_foreign_key(
        "issues_business_entity_id_fkey",
        "issues",
        "business_entity",
        ["business_entity_id"],
        ["id"],
    )

    op.drop_constraint(
        "business_entity_review_conversation_id_fkey",
        "business_entity",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "business_entity_review_conversation_id_fkey",
        "business_entity",
        "conversation",
        ["review_conversation_id"],
        ["id"],
    )

    op.drop_constraint("issues_message_id_fkey", "issues", type_="foreignkey")
    op.create_foreign_key(
        "issues_message_id_fkey",
        "issues",
        "conversation_message",
        ["message_id"],
        ["id"],
    )

    op.drop_constraint(
        "conversation_message_conversationId_fkey",
        "conversation_message",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "conversation_message_conversationId_fkey",
        "conversation_message",
        "conversation",
        ["conversationId"],
        ["id"],
    )

    # Part 3: Asset self-references
    op.drop_constraint(
        "schema_facet_parent_database_asset_id_fkey", "schema_facet", type_="foreignkey"
    )
    op.create_foreign_key(
        "schema_facet_parent_database_asset_id_fkey",
        "schema_facet",
        "asset",
        ["parent_database_asset_id"],
        ["id"],
    )

    op.drop_constraint(
        "fk_table_facet_parent_schema_asset", "table_facet", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_table_facet_parent_schema_asset",
        "table_facet",
        "asset",
        ["parent_schema_asset_id"],
        ["id"],
    )

    op.drop_constraint(
        "column_facet_parent_table_asset_id_fkey", "column_facet", type_="foreignkey"
    )
    op.create_foreign_key(
        "column_facet_parent_table_asset_id_fkey",
        "column_facet",
        "asset",
        ["parent_table_asset_id"],
        ["id"],
    )

    # Part 2: Query and Project references
    op.drop_constraint(
        "conversation_projectId_fkey", "conversation", type_="foreignkey"
    )
    op.create_foreign_key(
        "conversation_projectId_fkey",
        "conversation",
        "project",
        ["projectId"],
        ["id"],
    )

    op.drop_constraint("note_projectId_fkey", "note", type_="foreignkey")
    op.create_foreign_key(
        "note_projectId_fkey",
        "note",
        "project",
        ["projectId"],
        ["id"],
    )

    op.drop_constraint(
        "project_tables_projectId_fkey", "project_tables", type_="foreignkey"
    )
    op.create_foreign_key(
        "project_tables_projectId_fkey",
        "project_tables",
        "project",
        ["projectId"],
        ["id"],
    )

    op.drop_constraint("chart_queryId_fkey", "chart", type_="foreignkey")
    op.create_foreign_key(
        "chart_queryId_fkey",
        "chart",
        "query",
        ["queryId"],
        ["id"],
    )

    # Part 1: Database references
    op.drop_constraint(
        "table_facet_database_id_fkey", "table_facet", type_="foreignkey"
    )
    op.create_foreign_key(
        "table_facet_database_id_fkey",
        "table_facet",
        "database",
        ["database_id"],
        ["id"],
    )

    op.drop_constraint(
        "schema_facet_database_id_fkey", "schema_facet", type_="foreignkey"
    )
    op.create_foreign_key(
        "schema_facet_database_id_fkey",
        "schema_facet",
        "database",
        ["database_id"],
        ["id"],
    )

    op.drop_constraint(
        "database_facet_database_id_fkey", "database_facet", type_="foreignkey"
    )
    op.create_foreign_key(
        "database_facet_database_id_fkey",
        "database_facet",
        "database",
        ["database_id"],
        ["id"],
    )

    op.drop_constraint(
        "business_entity_database_id_fkey", "business_entity", type_="foreignkey"
    )
    op.create_foreign_key(
        "business_entity_database_id_fkey",
        "business_entity",
        "database",
        ["database_id"],
        ["id"],
    )

    op.drop_constraint("issues_database_id_fkey", "issues", type_="foreignkey")
    op.create_foreign_key(
        "issues_database_id_fkey",
        "issues",
        "database",
        ["database_id"],
        ["id"],
    )

    op.drop_constraint("asset_tag_database_id_fkey", "asset_tag", type_="foreignkey")
    op.create_foreign_key(
        "asset_tag_database_id_fkey",
        "asset_tag",
        "database",
        ["database_id"],
        ["id"],
    )

    op.drop_constraint("term_database_id_fkey", "term", type_="foreignkey")
    op.create_foreign_key(
        "term_database_id_fkey",
        "term",
        "database",
        ["database_id"],
        ["id"],
    )

    op.drop_constraint("asset_database_id_fkey", "asset", type_="foreignkey")
    op.create_foreign_key(
        "asset_database_id_fkey",
        "asset",
        "database",
        ["database_id"],
        ["id"],
    )

    op.drop_constraint("document_database_id_fkey", "document", type_="foreignkey")
    op.create_foreign_key(
        "document_database_id_fkey",
        "document",
        "database",
        ["database_id"],
        ["id"],
    )

    op.drop_constraint(
        "github_oauth_state_databaseId_fkey", "github_oauth_state", type_="foreignkey"
    )
    op.create_foreign_key(
        "github_oauth_state_databaseId_fkey",
        "github_oauth_state",
        "database",
        ["databaseId"],
        ["id"],
    )

    op.drop_constraint(
        "github_integration_databaseId_fkey", "github_integration", type_="foreignkey"
    )
    op.create_foreign_key(
        "github_integration_databaseId_fkey",
        "github_integration",
        "database",
        ["databaseId"],
        ["id"],
    )

    op.drop_constraint("project_databaseId_fkey", "project", type_="foreignkey")
    op.create_foreign_key(
        "project_databaseId_fkey",
        "project",
        "database",
        ["databaseId"],
        ["id"],
    )

    op.drop_constraint("query_databaseId_fkey", "query", type_="foreignkey")
    op.create_foreign_key(
        "query_databaseId_fkey",
        "query",
        "database",
        ["databaseId"],
        ["id"],
    )

    op.drop_constraint("dbt_database_id_fkey", "dbt", type_="foreignkey")
    op.create_foreign_key(
        "dbt_database_id_fkey",
        "dbt",
        "database",
        ["database_id"],
        ["id"],
    )

    op.drop_constraint(
        "conversation_databaseId_fkey", "conversation", type_="foreignkey"
    )
    op.create_foreign_key(
        "conversation_databaseId_fkey",
        "conversation",
        "database",
        ["databaseId"],
        ["id"],
    )
