"""add demo

Revision ID: 050bddebb99e
Revises: 8c6487931db9
Create Date: 2025-07-24 11:49:45.296326

"""

import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import (
    Boolean,
    DateTime,
    MetaData,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from back.data_warehouse import DataWarehouseFactory

# Create migration-specific metadata and base class
migration_metadata = MetaData()


class MigrationBase(DeclarativeBase):
    metadata = migration_metadata


@dataclass
class Database(MigrationBase):
    __tablename__ = "database"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    engine: Mapped[str] = mapped_column(String, nullable=False, name="engine")
    details: Mapped[Dict[Any, Any]] = mapped_column(sa.JSON, nullable=False)
    organisationId: Mapped[Optional[str]] = mapped_column(String)
    ownerId: Mapped[Optional[str]] = mapped_column(String)
    public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    memory: Mapped[Optional[str]] = mapped_column(String)
    tables_metadata: Mapped[Optional[List[Dict[Any, Any]]]] = mapped_column(sa.JSON)
    dbt_catalog: Mapped[Optional[Dict[Any, Any]]] = mapped_column(sa.JSON)
    dbt_manifest: Mapped[Optional[Dict[Any, Any]]] = mapped_column(sa.JSON)
    safe_mode: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    # Add timestamps for compatibility
    createdAt: Mapped[Optional[sa.DateTime]] = mapped_column(
        DateTime, nullable=True, server_default=func.now()
    )
    updatedAt: Mapped[Optional[sa.DateTime]] = mapped_column(
        DateTime, nullable=True, server_default=func.now()
    )

    def create_data_warehouse(self):
        data_warehouse = DataWarehouseFactory.create(
            self.engine,
            **self.details,
        )
        # For migrations, we don't need write_mode
        return data_warehouse


def create_database(
    name: str,
    description: str,
    engine: str,
    details: dict,
    public: bool,
    safe_mode: bool = False,
    owner_id: str | None = None,
    organisation_id: str | None = None,
    dbt_catalog: dict | None = None,
    dbt_manifest: dict | None = None,
):
    # Create a new database
    database = Database(
        name=name,
        description=description,
        engine=engine,
        details=details,
        organisationId=organisation_id,
        ownerId=owner_id,
        public=public,
        safe_mode=safe_mode,
        dbt_catalog=dbt_catalog,
        dbt_manifest=dbt_manifest,
    )

    try:
        data_warehouse = DataWarehouseFactory.create(engine, **details)
        updated_tables_metadata = data_warehouse.load_metadata()
        database.tables_metadata = updated_tables_metadata
    except Exception:
        # If metadata loading fails, continue without it
        database.tables_metadata = None

    return database


# revision identifiers, used by Alembic.
revision: str = "050bddebb99e"
down_revision: Union[str, None] = "8c6487931db9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get the current connection from Alembic
    connection = op.get_bind()

    # Create a session using the Alembic connection
    Session = sessionmaker(bind=connection)
    session = Session()

    try:
        # Create the Northwind database with full metadata loading
        northwind = create_database(
            name="Northwind - Traders",
            description="Trading/export company's operations",
            engine="postgres",
            public=True,
            safe_mode=True,
            details={
                "host": "34.65.255.212",
                "port": 5432,
                "user": "readonly_user",
                "database": "northwind",
                "password": "readonly123",
            },
        )

        # Create the Marker database with full metadata loading
        marker = create_database(
            name="Marker - SaaS",
            description="Demo from PopSQL",
            engine="postgres",
            public=True,
            safe_mode=True,
            details={
                "host": "sample-data.popsql.io",
                "port": 5432,
                "user": "demo",
                "database": "marker",
                "password": "demo",
            },
        )

        # Add to session and commit
        session.add(northwind)
        session.add(marker)
        session.commit()

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def downgrade() -> None:
    # Delete demo databases by name
    op.execute(sa.text("DELETE FROM database WHERE name = 'Northwind - Traders'"))
    op.execute(sa.text("DELETE FROM database WHERE name = 'Marker - SaaS'"))
