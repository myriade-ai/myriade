"""fix cascade constraints for postgresql

Revision ID: 986d35afd76a
Revises: 9db848c6297c
Create Date: 2025-11-14 12:20:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "986d35afd76a"
down_revision: Union[str, None] = "9db848c6297c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # For PostgreSQL, we need to drop and recreate constraints directly
    # Asset self-references in facets (CASCADE)

    # ColumnFacet.parent_table_asset_id -> Asset.id
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

    # TableFacet.parent_schema_asset_id -> Asset.id
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

    # SchemaFacet.parent_database_asset_id -> Asset.id
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


def downgrade() -> None:
    # Reverse - remove CASCADE
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
