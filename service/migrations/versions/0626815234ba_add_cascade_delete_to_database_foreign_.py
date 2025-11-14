"""add cascade delete to database foreign keys

Revision ID: 0626815234ba
Revises: 4f56b3cc8a7d
Create Date: 2025-11-14 12:03:55.090186

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0626815234ba"
down_revision: Union[str, None] = "4f56b3cc8a7d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Foreign key constraint names
QUERY_DATABASE_FK = "query_databaseId_fkey"
PROJECT_DATABASE_FK = "project_databaseId_fkey"
GITHUB_INTEGRATION_DATABASE_FK = "github_integration_databaseId_fkey"
DOCUMENT_DATABASE_FK = "document_database_id_fkey"
ASSET_DATABASE_FK = "asset_database_id_fkey"
TERM_DATABASE_FK = "term_database_id_fkey"
ASSET_TAG_DATABASE_FK = "asset_tag_database_id_fkey"
ISSUE_DATABASE_FK = "issues_database_id_fkey"
BUSINESS_ENTITY_DATABASE_FK = "business_entity_database_id_fkey"
DATABASE_FACET_DATABASE_FK = "database_facet_database_id_fkey"
SCHEMA_FACET_DATABASE_FK = "schema_facet_database_id_fkey"
TABLE_FACET_DATABASE_FK = "table_facet_database_id_fkey"


def upgrade() -> None:
    # Query.databaseId
    with op.batch_alter_table("query", schema=None) as batch_op:
        batch_op.drop_constraint(QUERY_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            QUERY_DATABASE_FK,
            "database",
            ["databaseId"],
            ["id"],
            ondelete="CASCADE",
        )

    # Project.databaseId
    with op.batch_alter_table("project", schema=None) as batch_op:
        batch_op.drop_constraint(PROJECT_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            PROJECT_DATABASE_FK,
            "database",
            ["databaseId"],
            ["id"],
            ondelete="CASCADE",
        )

    # GithubIntegration.databaseId
    with op.batch_alter_table("github_integration", schema=None) as batch_op:
        batch_op.drop_constraint(GITHUB_INTEGRATION_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            GITHUB_INTEGRATION_DATABASE_FK,
            "database",
            ["databaseId"],
            ["id"],
            ondelete="CASCADE",
        )

    # Document.database_id
    with op.batch_alter_table("document", schema=None) as batch_op:
        batch_op.drop_constraint(DOCUMENT_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            DOCUMENT_DATABASE_FK,
            "database",
            ["database_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # Asset.database_id
    with op.batch_alter_table("asset", schema=None) as batch_op:
        batch_op.drop_constraint(ASSET_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            ASSET_DATABASE_FK,
            "database",
            ["database_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # Term.database_id
    with op.batch_alter_table("term", schema=None) as batch_op:
        batch_op.drop_constraint(TERM_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            TERM_DATABASE_FK,
            "database",
            ["database_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # AssetTag.database_id
    with op.batch_alter_table("asset_tag", schema=None) as batch_op:
        batch_op.drop_constraint(ASSET_TAG_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            ASSET_TAG_DATABASE_FK,
            "database",
            ["database_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # Issue.database_id (SET NULL since it's nullable)
    with op.batch_alter_table("issues", schema=None) as batch_op:
        batch_op.drop_constraint(ISSUE_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            ISSUE_DATABASE_FK,
            "database",
            ["database_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # BusinessEntity.database_id
    with op.batch_alter_table("business_entity", schema=None) as batch_op:
        batch_op.drop_constraint(BUSINESS_ENTITY_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            BUSINESS_ENTITY_DATABASE_FK,
            "database",
            ["database_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # DatabaseFacet.database_id
    with op.batch_alter_table("database_facet", schema=None) as batch_op:
        batch_op.drop_constraint(DATABASE_FACET_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            DATABASE_FACET_DATABASE_FK,
            "database",
            ["database_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # SchemaFacet.database_id
    with op.batch_alter_table("schema_facet", schema=None) as batch_op:
        batch_op.drop_constraint(SCHEMA_FACET_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            SCHEMA_FACET_DATABASE_FK,
            "database",
            ["database_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # TableFacet.database_id
    with op.batch_alter_table("table_facet", schema=None) as batch_op:
        batch_op.drop_constraint(TABLE_FACET_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            TABLE_FACET_DATABASE_FK,
            "database",
            ["database_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    # Reverse order for downgrade
    with op.batch_alter_table("table_facet", schema=None) as batch_op:
        batch_op.drop_constraint(TABLE_FACET_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            TABLE_FACET_DATABASE_FK,
            "database",
            ["database_id"],
            ["id"],
        )

    with op.batch_alter_table("schema_facet", schema=None) as batch_op:
        batch_op.drop_constraint(SCHEMA_FACET_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            SCHEMA_FACET_DATABASE_FK,
            "database",
            ["database_id"],
            ["id"],
        )

    with op.batch_alter_table("database_facet", schema=None) as batch_op:
        batch_op.drop_constraint(DATABASE_FACET_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            DATABASE_FACET_DATABASE_FK,
            "database",
            ["database_id"],
            ["id"],
        )

    with op.batch_alter_table("business_entity", schema=None) as batch_op:
        batch_op.drop_constraint(BUSINESS_ENTITY_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            BUSINESS_ENTITY_DATABASE_FK,
            "database",
            ["database_id"],
            ["id"],
        )

    with op.batch_alter_table("issues", schema=None) as batch_op:
        batch_op.drop_constraint(ISSUE_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            ISSUE_DATABASE_FK,
            "database",
            ["database_id"],
            ["id"],
        )

    with op.batch_alter_table("asset_tag", schema=None) as batch_op:
        batch_op.drop_constraint(ASSET_TAG_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            ASSET_TAG_DATABASE_FK,
            "database",
            ["database_id"],
            ["id"],
        )

    with op.batch_alter_table("term", schema=None) as batch_op:
        batch_op.drop_constraint(TERM_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            TERM_DATABASE_FK,
            "database",
            ["database_id"],
            ["id"],
        )

    with op.batch_alter_table("asset", schema=None) as batch_op:
        batch_op.drop_constraint(ASSET_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            ASSET_DATABASE_FK,
            "database",
            ["database_id"],
            ["id"],
        )

    with op.batch_alter_table("document", schema=None) as batch_op:
        batch_op.drop_constraint(DOCUMENT_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            DOCUMENT_DATABASE_FK,
            "database",
            ["database_id"],
            ["id"],
        )

    with op.batch_alter_table("github_integration", schema=None) as batch_op:
        batch_op.drop_constraint(GITHUB_INTEGRATION_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            GITHUB_INTEGRATION_DATABASE_FK,
            "database",
            ["databaseId"],
            ["id"],
        )

    with op.batch_alter_table("project", schema=None) as batch_op:
        batch_op.drop_constraint(PROJECT_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            PROJECT_DATABASE_FK,
            "database",
            ["databaseId"],
            ["id"],
        )

    with op.batch_alter_table("query", schema=None) as batch_op:
        batch_op.drop_constraint(QUERY_DATABASE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            QUERY_DATABASE_FK,
            "database",
            ["databaseId"],
            ["id"],
        )
