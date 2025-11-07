"""fix_schema_names_remove_database_prefix

Revision ID: af6ff2d17d32
Revises: 53de7f643cb2
Create Date: 2025-11-04 15:52:58.204075

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "af6ff2d17d32"
down_revision: Union[str, None] = "53de7f643cb2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fix schema names in table_facet that contain database prefix
    # (e.g., "DATABASE.SCHEMA" -> "SCHEMA"). This happens when Snowflake
    # returns fully qualified schema names
    op.execute("""
        UPDATE table_facet
        SET schema = SUBSTRING(schema FROM POSITION('.' IN schema) + 1)
        WHERE schema LIKE '%.%'
    """)

    # Also fix schema_name in schema_facet if it has the same issue
    op.execute("""
        UPDATE schema_facet
        SET schema_name = SUBSTRING(schema_name FROM POSITION('.' IN schema_name) + 1)
        WHERE schema_name LIKE '%.%'
    """)


def downgrade() -> None:
    pass
