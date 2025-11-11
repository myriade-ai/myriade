"""add_tsvector_search_columns

Revision ID: f2a3b4c5d6e7
Revises: e1f2c3d4e5f6
Create Date: 2025-11-11 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, None] = "e1f2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()

    # Only add tsvector columns and indexes for PostgreSQL
    if connection.dialect.name == "postgresql":
        # Add tsvector columns to asset table
        op.add_column(
            "asset",
            sa.Column(
                "search_vector",
                postgresql.TSVECTOR,
                sa.Computed(
                    """
                    setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
                    setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
                    setweight(to_tsvector('english', coalesce(ai_suggestion, '')), 'C') ||
                    setweight(to_tsvector('english', coalesce(urn, '')), 'D')
                    """,
                    persisted=True,
                ),
            ),
        )

        # Add GIN index for fast tsvector search on assets
        op.create_index(
            "idx_asset_search_vector_gin",
            "asset",
            ["search_vector"],
            postgresql_using="gin",
        )

        # Add tsvector column to term table
        op.add_column(
            "term",
            sa.Column(
                "search_vector",
                postgresql.TSVECTOR,
                sa.Computed(
                    """
                    setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
                    setweight(to_tsvector('english', coalesce(definition, '')), 'B')
                    """,
                    persisted=True,
                ),
            ),
        )

        # Add GIN index for fast tsvector search on terms
        op.create_index(
            "idx_term_search_vector_gin",
            "term",
            ["search_vector"],
            postgresql_using="gin",
        )

        # Add tsvector column to asset_tag table
        op.add_column(
            "asset_tag",
            sa.Column(
                "search_vector",
                postgresql.TSVECTOR,
                sa.Computed(
                    """
                    setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
                    setweight(to_tsvector('english', coalesce(description, '')), 'B')
                    """,
                    persisted=True,
                ),
            ),
        )

        # Add GIN index for fast tsvector search on tags
        op.create_index(
            "idx_asset_tag_search_vector_gin",
            "asset_tag",
            ["search_vector"],
            postgresql_using="gin",
        )


def downgrade() -> None:
    connection = op.get_bind()

    if connection.dialect.name == "postgresql":
        # Drop indexes
        op.drop_index("idx_asset_tag_search_vector_gin", table_name="asset_tag")
        op.drop_index("idx_term_search_vector_gin", table_name="term")
        op.drop_index("idx_asset_search_vector_gin", table_name="asset")

        # Drop columns
        op.drop_column("asset_tag", "search_vector")
        op.drop_column("term", "search_vector")
        op.drop_column("asset", "search_vector")
