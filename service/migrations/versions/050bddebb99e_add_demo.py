"""add demo

Revision ID: 050bddebb99e
Revises: 8c6487931db9
Create Date: 2025-07-24 11:49:45.296326

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import sessionmaker

# Type imports

# revision identifiers, used by Alembic.
revision: str = "050bddebb99e"
down_revision: Union[str, None] = "8c6487931db9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Import here to avoid module loading issues during migration
    from back.utils import create_database

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
