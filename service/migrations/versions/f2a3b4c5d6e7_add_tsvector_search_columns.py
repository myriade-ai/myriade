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

    if connection.dialect.name == "postgresql":
        # PostgreSQL: Add tsvector computed columns with GIN indexes
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

        op.create_index(
            "idx_asset_search_vector_gin",
            "asset",
            ["search_vector"],
            postgresql_using="gin",
        )

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

        op.create_index(
            "idx_term_search_vector_gin",
            "term",
            ["search_vector"],
            postgresql_using="gin",
        )

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

        op.create_index(
            "idx_asset_tag_search_vector_gin",
            "asset_tag",
            ["search_vector"],
            postgresql_using="gin",
        )
    else:
        # SQLite/other databases: Add nullable string columns (not used, but required for ORM)
        op.add_column(
            "asset",
            sa.Column("search_vector", sa.String(), nullable=True),
        )

        op.add_column(
            "term",
            sa.Column("search_vector", sa.String(), nullable=True),
        )

        op.add_column(
            "asset_tag",
            sa.Column("search_vector", sa.String(), nullable=True),
        )


def downgrade() -> None:
    connection = op.get_bind()

    if connection.dialect.name == "postgresql":
        # Drop indexes
        op.drop_index("idx_asset_tag_search_vector_gin", table_name="asset_tag")
        op.drop_index("idx_term_search_vector_gin", table_name="term")
        op.drop_index("idx_asset_search_vector_gin", table_name="asset")

    # Drop columns for all databases
    op.drop_column("asset_tag", "search_vector")
    op.drop_column("term", "search_vector")
    op.drop_column("asset", "search_vector")
