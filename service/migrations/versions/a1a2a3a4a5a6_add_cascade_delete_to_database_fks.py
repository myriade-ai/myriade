"""add cascade delete to database foreign keys

Revision ID: a1a2a3a4a5a6
Revises: 2dc0b1830c41
Create Date: 2025-11-12 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from db import UUID

# revision identifiers, used by Alembic.
revision: str = "a1a2a3a4a5a6"
down_revision: Union[str, None] = "2dc0b1830c41"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Core tables
    # Update conversation.databaseId foreign key to CASCADE on delete
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

    # Update query.databaseId foreign key to CASCADE on delete
    op.drop_constraint("query_databaseId_fkey", "query", type_="foreignkey")
    op.create_foreign_key(
        "query_databaseId_fkey",
        "query",
        "database",
        ["databaseId"],
        ["id"],
        ondelete="CASCADE",
    )

    # Update project.databaseId foreign key to CASCADE on delete
    op.drop_constraint("project_databaseId_fkey", "project", type_="foreignkey")
    op.create_foreign_key(
        "project_databaseId_fkey",
        "project",
        "database",
        ["databaseId"],
        ["id"],
        ondelete="CASCADE",
    )

    # Update document.database_id foreign key to CASCADE on delete
    op.drop_constraint("document_database_id_fkey", "document", type_="foreignkey")
    op.create_foreign_key(
        "document_database_id_fkey",
        "document",
        "database",
        ["database_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Update dbt.database_id foreign key to CASCADE on delete
    op.drop_constraint("dbt_database_id_fkey", "dbt", type_="foreignkey")
    op.create_foreign_key(
        "dbt_database_id_fkey",
        "dbt",
        "database",
        ["database_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Catalog tables
    # Update asset.database_id foreign key to CASCADE on delete
    op.drop_constraint("asset_database_id_fkey", "asset", type_="foreignkey")
    op.create_foreign_key(
        "asset_database_id_fkey",
        "asset",
        "database",
        ["database_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Update database_facet.database_id foreign key to CASCADE on delete
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

    # Update schema_facet.database_id foreign key to CASCADE on delete
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

    # Update table_facet.database_id foreign key to CASCADE on delete
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

    # Update column_facet.database_id foreign key to CASCADE on delete
    op.drop_constraint(
        "column_facet_database_id_fkey", "column_facet", type_="foreignkey"
    )
    op.create_foreign_key(
        "column_facet_database_id_fkey",
        "column_facet",
        "database",
        ["database_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Update asset_tag.database_id foreign key to CASCADE on delete
    op.drop_constraint("asset_tag_database_id_fkey", "asset_tag", type_="foreignkey")
    op.create_foreign_key(
        "asset_tag_database_id_fkey",
        "asset_tag",
        "database",
        ["database_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Update term.database_id foreign key to CASCADE on delete
    op.drop_constraint("term_database_id_fkey", "term", type_="foreignkey")
    op.create_foreign_key(
        "term_database_id_fkey",
        "term",
        "database",
        ["database_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Quality tables
    # Update issue.database_id foreign key to CASCADE on delete (nullable but still needs CASCADE)
    op.drop_constraint("issues_database_id_fkey", "issues", type_="foreignkey")
    op.create_foreign_key(
        "issues_database_id_fkey",
        "issues",
        "database",
        ["database_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Update business_entity.database_id foreign key to CASCADE on delete
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


def downgrade() -> None:
    # Core tables - revert to no cascade
    # Revert conversation.databaseId foreign key
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

    # Revert query.databaseId foreign key
    op.drop_constraint("query_databaseId_fkey", "query", type_="foreignkey")
    op.create_foreign_key(
        "query_databaseId_fkey",
        "query",
        "database",
        ["databaseId"],
        ["id"],
    )

    # Revert project.databaseId foreign key
    op.drop_constraint("project_databaseId_fkey", "project", type_="foreignkey")
    op.create_foreign_key(
        "project_databaseId_fkey",
        "project",
        "database",
        ["databaseId"],
        ["id"],
    )

    # Revert document.database_id foreign key
    op.drop_constraint("document_database_id_fkey", "document", type_="foreignkey")
    op.create_foreign_key(
        "document_database_id_fkey",
        "document",
        "database",
        ["database_id"],
        ["id"],
    )

    # Revert dbt.database_id foreign key
    op.drop_constraint("dbt_database_id_fkey", "dbt", type_="foreignkey")
    op.create_foreign_key(
        "dbt_database_id_fkey",
        "dbt",
        "database",
        ["database_id"],
        ["id"],
    )

    # Catalog tables - revert to no cascade
    # Revert asset.database_id foreign key
    op.drop_constraint("asset_database_id_fkey", "asset", type_="foreignkey")
    op.create_foreign_key(
        "asset_database_id_fkey",
        "asset",
        "database",
        ["database_id"],
        ["id"],
    )

    # Revert database_facet.database_id foreign key
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

    # Revert schema_facet.database_id foreign key
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

    # Revert table_facet.database_id foreign key
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

    # Revert column_facet.database_id foreign key
    op.drop_constraint(
        "column_facet_database_id_fkey", "column_facet", type_="foreignkey"
    )
    op.create_foreign_key(
        "column_facet_database_id_fkey",
        "column_facet",
        "database",
        ["database_id"],
        ["id"],
    )

    # Revert asset_tag.database_id foreign key
    op.drop_constraint("asset_tag_database_id_fkey", "asset_tag", type_="foreignkey")
    op.create_foreign_key(
        "asset_tag_database_id_fkey",
        "asset_tag",
        "database",
        ["database_id"],
        ["id"],
    )

    # Revert term.database_id foreign key
    op.drop_constraint("term_database_id_fkey", "term", type_="foreignkey")
    op.create_foreign_key(
        "term_database_id_fkey",
        "term",
        "database",
        ["database_id"],
        ["id"],
    )

    # Quality tables - revert to no cascade
    # Revert issue.database_id foreign key
    op.drop_constraint("issues_database_id_fkey", "issues", type_="foreignkey")
    op.create_foreign_key(
        "issues_database_id_fkey",
        "issues",
        "database",
        ["database_id"],
        ["id"],
    )

    # Revert business_entity.database_id foreign key
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
