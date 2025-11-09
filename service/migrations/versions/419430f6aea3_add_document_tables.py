"""add_document_tables

Revision ID: 419430f6aea3
Revises: 2dc0b1830c41
Create Date: 2025-11-07 16:32:35.224960

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from db import UUID

# revision identifiers, used by Alembic.
revision: str = "419430f6aea3"
down_revision: Union[str, None] = "2dc0b1830c41"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create document table
    op.create_table(
        "document",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("database_id", UUID(), nullable=False),
        sa.Column("organisation_id", sa.String(), nullable=True),
        sa.Column("content", sa.String(), nullable=False, server_default=""),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.Column(
            "createdAt",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updatedAt",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["database_id"], ["database.id"]),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisation.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for efficient querying
    op.create_index("ix_document_database_id", "document", ["database_id"])
    op.create_index("ix_document_organisation_id", "document", ["organisation_id"])

    # Create document_version table
    op.create_table(
        "document_version",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("document_id", UUID(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column(
            "createdAt",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("change_description", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["document.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create index for efficient version lookups
    op.create_index(
        "ix_document_version_document_id", "document_version", ["document_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_document_version_document_id", "document_version")
    op.drop_table("document_version")
    op.drop_index("ix_document_organisation_id", "document")
    op.drop_index("ix_document_database_id", "document")
    op.drop_table("document")
