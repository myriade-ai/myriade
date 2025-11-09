"""fix_schema_names_remove_database_prefix

Revision ID: af6ff2d17d32
Revises: 53de7f643cb2
Create Date: 2025-11-04 15:52:58.204075

"""

from typing import Sequence, Union

import sqlalchemy as sa
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
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    # Check if tables exist before trying to update them
    # This is necessary because schema_facet is created in a later migration (03ca219fcee9)
    tables = inspector.get_table_names()
    has_table_facet = "table_facet" in tables
    has_schema_facet = "schema_facet" in tables

    if connection.dialect.name == "postgresql":
        # PostgreSQL syntax
        if has_table_facet:
            op.execute("""
                UPDATE table_facet
                SET schema = SUBSTRING(schema FROM POSITION('.' IN schema) + 1)
                WHERE schema LIKE '%.%'
            """)

        if has_schema_facet:
            op.execute("""
                UPDATE schema_facet
                SET schema_name = SUBSTRING(schema_name FROM POSITION('.' IN schema_name) + 1)
                WHERE schema_name LIKE '%.%'
            """)
    else:
        # SQLite syntax
        if has_table_facet:
            op.execute("""
                UPDATE table_facet
                SET schema = SUBSTR(schema, INSTR(schema, '.') + 1)
                WHERE schema LIKE '%.%'
            """)

        if has_schema_facet:
            op.execute("""
                UPDATE schema_facet
                SET schema_name = SUBSTR(schema_name, INSTR(schema_name, '.') + 1)
                WHERE schema_name LIKE '%.%'
            """)


def downgrade() -> None:
    pass
