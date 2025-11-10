"""add_pg_trgm_extension_and_search_indexes

Revision ID: e1f2c3d4e5f6
Revises: 2dc0b1830c41
Create Date: 2025-11-07 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1f2c3d4e5f6"
down_revision: Union[str, None] = "2dc0b1830c41"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()

    # Enable pg_trgm extension on PostgreSQL only
    if connection.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

        # Add GIN indexes for text search on Asset model
        op.create_index(
            "idx_asset_name_trgm",
            "asset",
            ["name"],
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        )

        op.create_index(
            "idx_asset_description_trgm",
            "asset",
            ["description"],
            postgresql_using="gin",
            postgresql_ops={"description": "gin_trgm_ops"},
        )

        # Add GIN indexes for AssetTag model
        op.create_index(
            "idx_asset_tag_name_trgm",
            "asset_tag",
            ["name"],
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        )

        # Add GIN indexes for Term model
        op.create_index(
            "idx_term_name_trgm",
            "term",
            ["name"],
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        )

        op.create_index(
            "idx_term_definition_trgm",
            "term",
            ["definition"],
            postgresql_using="gin",
            postgresql_ops={"definition": "gin_trgm_ops"},
        )


def downgrade() -> None:
    connection = op.get_bind()

    if connection.dialect.name == "postgresql":
        # Drop indexes
        op.drop_index("idx_term_definition_trgm", table_name="term")
        op.drop_index("idx_term_name_trgm", table_name="term")
        op.drop_index("idx_asset_tag_name_trgm", table_name="asset_tag")
        op.drop_index("idx_asset_description_trgm", table_name="asset")
        op.drop_index("idx_asset_name_trgm", table_name="asset")

        # Note: We don't drop the extension to avoid breaking other potential dependencies
        # Users can manually drop it if needed with: DROP EXTENSION pg_trgm
