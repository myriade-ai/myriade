"""create facet-based catalog models

Revision ID: 86127ef44269
Revises: 553085b11c12
Create Date: 2025-09-16 16:58:17.711357

"""
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from db import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = '86127ef44269'
down_revision: Union[str, None] = '553085b11c12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old catalog tables
    op.drop_table('business_glossary_term')
    op.drop_table('catalog_asset')

    # Create new Asset table
    op.create_table('asset',
        sa.Column('id', UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('urn', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('database_id', UUID(), nullable=False),
        sa.Column('tags', JSONB(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('createdAt', sa.DateTime(),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updatedAt', sa.DateTime(),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['database_id'], ['database.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('urn')
    )

    # Create TableFacet table
    op.create_table('table_facet',
        sa.Column('asset_id', UUID(), nullable=False),
        sa.Column('schema', sa.String(), nullable=True),
        sa.Column('table_name', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['asset.id'], ),
        sa.PrimaryKeyConstraint('asset_id'),
        sa.UniqueConstraint('schema', 'table_name')
    )

    # Create ColumnFacet table
    op.create_table('column_facet',
        sa.Column('asset_id', UUID(), nullable=False),
        sa.Column('parent_table_asset_id', UUID(), nullable=False),
        sa.Column('column_name', sa.String(), nullable=False),
        sa.Column('ordinal', sa.Integer(), nullable=True),
        sa.Column('data_type', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['asset.id'], ),
        sa.ForeignKeyConstraint(['parent_table_asset_id'], ['asset.id'], ),
        sa.PrimaryKeyConstraint('asset_id')
    )

    # Create Term table (business glossary)
    op.create_table('term',
        sa.Column('id', UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('definition', sa.Text(), nullable=False),
        sa.Column('database_id', UUID(), nullable=False),
        sa.Column('synonyms', JSONB(), nullable=True),
        sa.Column('business_domains', JSONB(), nullable=True),
        sa.Column('createdAt', sa.DateTime(),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updatedAt', sa.DateTime(),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['database_id'], ['database.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop new facet tables and term table
    try:
        op.drop_table('term')
    except Exception:
        pass  # Table might not exist if upgrade was never run
    op.drop_table('column_facet')
    op.drop_table('table_facet')
    op.drop_table('asset')

    # Recreate old catalog tables
    op.create_table('catalog_asset',
        sa.Column('id', UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('asset_type', sa.String(), nullable=False),
        sa.Column('database_id', UUID(), nullable=False),
        sa.Column('tags', JSONB(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('schema_name', sa.String(), nullable=True),
        sa.Column('table_name', sa.String(), nullable=True),
        sa.Column('column_name', sa.String(), nullable=True),
        sa.Column('data_type', sa.String(), nullable=True),
        sa.Column('query_id', UUID(), nullable=True),
        sa.Column('chart_id', UUID(), nullable=True),
        sa.Column('createdAt', sa.DateTime(),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updatedAt', sa.DateTime(),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['database_id'], ['database.id'], ),
        sa.ForeignKeyConstraint(['query_id'], ['query.id'], ),
        sa.ForeignKeyConstraint(['chart_id'], ['chart.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('business_glossary_term',
        sa.Column('id', UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('definition', sa.Text(), nullable=False),
        sa.Column('database_id', UUID(), nullable=False),
        sa.Column('business_domain', sa.String(), nullable=True),
        sa.Column('synonyms', JSONB(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('createdAt', sa.DateTime(),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updatedAt', sa.DateTime(),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['database_id'], ['database.id'], ),
        sa.PrimaryKeyConstraint('id')
    )