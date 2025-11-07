"""extract dbt to separate table

Revision ID: b1c2d3e4f5g6
Revises: a1b2c3d4e5f8
Create Date: 2025-01-10 01:00:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from db import JSONB, UUID, UtcDateTime, UtcTimestamp

revision: str = "b1c2d3e4f5g6"
down_revision: Union[str, None] = "a1b2c3d4e5f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create dbt table
    op.create_table(
        "dbt",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("database_id", UUID(), nullable=False),
        sa.Column("catalog", JSONB(), nullable=True),
        sa.Column("manifest", JSONB(), nullable=True),
        sa.Column("last_commit_hash", sa.String(), nullable=True),
        sa.Column(
            "last_synced_at",
            UtcDateTime(),
            nullable=True,
        ),
        sa.Column("sync_status", sa.String(), nullable=False, server_default="idle"),
        sa.Column(
            "generation_started_at",
            UtcDateTime(),
            nullable=True,
        ),
        sa.Column("generation_error", sa.String(), nullable=True),
        sa.Column(
            "createdAt",
            UtcDateTime(),
            nullable=False,
            server_default=UtcTimestamp(),
        ),
        sa.Column(
            "updatedAt",
            UtcDateTime(),
            nullable=False,
            server_default=UtcTimestamp(),
        ),
        sa.ForeignKeyConstraint(["database_id"], ["database.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("database_id", name="uq_dbt_database_id"),
    )

    # Create index on database_id for faster lookups
    op.create_index(op.f("ix_dbt_database_id"), "dbt", ["database_id"], unique=True)

    # Migrate existing DBT data from database table to dbt table
    # Only migrate databases that have at least one non-null DBT field
    connection = op.get_bind()

    if connection.dialect.name == "postgresql":
        op.execute(
            """
            INSERT INTO dbt (
                id,
                database_id,
                catalog,
                manifest,
                last_commit_hash,
                last_synced_at,
                sync_status,
                generation_started_at,
                generation_error,
                "createdAt",
                "updatedAt"
            )
            SELECT
                gen_random_uuid(),
                id,
                dbt_catalog,
                dbt_manifest,
                last_dbt_commit_hash,
                dbt_last_synced_at,
                COALESCE(dbt_sync_status, 'idle'),
                dbt_generation_started_at,
                dbt_generation_error,
                now(),
                now()
            FROM database
            WHERE dbt_catalog IS NOT NULL
               OR dbt_manifest IS NOT NULL
               OR last_dbt_commit_hash IS NOT NULL
            """
        )
    else:
        # SQLite version
        op.execute(
            """
            INSERT INTO dbt (
                id,
                database_id,
                catalog,
                manifest,
                last_commit_hash,
                last_synced_at,
                sync_status,
                generation_started_at,
                generation_error,
                "createdAt",
                "updatedAt"
            )
            SELECT
                REPLACE(lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || '4' || substr(hex(randomblob(2)), 2) || '-' || substr('89ab', abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)), 2) || '-' || hex(randomblob(6))), '-', ''),
                id,
                dbt_catalog,
                dbt_manifest,
                last_dbt_commit_hash,
                dbt_last_synced_at,
                COALESCE(dbt_sync_status, 'idle'),
                dbt_generation_started_at,
                dbt_generation_error,
                STRFTIME('%Y-%m-%dT%H:%M:%fZ', 'now'),
                STRFTIME('%Y-%m-%dT%H:%M:%fZ', 'now')
            FROM database
            WHERE dbt_catalog IS NOT NULL
               OR dbt_manifest IS NOT NULL
               OR last_dbt_commit_hash IS NOT NULL
            """
        )

    # Drop old DBT columns from database table
    op.drop_column("database", "dbt_generation_error")
    op.drop_column("database", "dbt_generation_started_at")
    op.drop_column("database", "dbt_sync_status")
    op.drop_column("database", "dbt_last_synced_at")
    op.drop_column("database", "last_dbt_commit_hash")
    op.drop_column("database", "dbt_manifest")
    op.drop_column("database", "dbt_catalog")


def downgrade() -> None:
    # Add DBT columns back to database table
    op.add_column("database", sa.Column("dbt_catalog", JSONB(), nullable=True))
    op.add_column("database", sa.Column("dbt_manifest", JSONB(), nullable=True))
    op.add_column(
        "database", sa.Column("last_dbt_commit_hash", sa.String(), nullable=True)
    )
    op.add_column(
        "database",
        sa.Column("dbt_last_synced_at", UtcDateTime(), nullable=True),
    )
    op.add_column(
        "database",
        sa.Column(
            "dbt_sync_status", sa.String(), nullable=False, server_default="idle"
        ),
    )
    op.add_column(
        "database",
        sa.Column(
            "dbt_generation_started_at",
            UtcDateTime(),
            nullable=True,
        ),
    )
    op.add_column(
        "database", sa.Column("dbt_generation_error", sa.String(), nullable=True)
    )

    # Migrate data back from dbt table to database table
    op.execute(
        """
        UPDATE database
        SET
            dbt_catalog = dbt.catalog,
            dbt_manifest = dbt.manifest,
            last_dbt_commit_hash = dbt.last_commit_hash,
            dbt_last_synced_at = dbt.last_synced_at,
            dbt_sync_status = dbt.sync_status,
            dbt_generation_started_at = dbt.generation_started_at,
            dbt_generation_error = dbt.generation_error
        FROM dbt
        WHERE database.id = dbt.database_id
        """
    )

    # Drop dbt table
    op.drop_index(op.f("ix_dbt_database_id"), table_name="dbt")
    op.drop_table("dbt")
