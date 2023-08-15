"""create sample database

Revision ID: bdcf2c6aa3a6
Revises: 4b610242919c
Create Date: 2023-08-15 10:52:00.920707

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from back.models import Database

# revision identifiers, used by Alembic.
revision: str = "bdcf2c6aa3a6"
down_revision: Union[str, None] = "4b610242919c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tables with clients,products and orders tables
    op.execute(
        """
        CREATE SCHEMA sample;
        CREATE TABLE sample.clients (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            phone VARCHAR(255) NOT NULL,
            address VARCHAR(255) NOT NULL
        );
        CREATE TABLE sample.products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            price DECIMAL(10,2) NOT NULL
        );
        CREATE TABLE sample.orders (
            id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (client_id) REFERENCES sample.clients (id),
            FOREIGN KEY (product_id) REFERENCES sample.products (id)
        );
        
        -- Clients Table
        INSERT INTO sample.clients (name, email, phone, address) VALUES 
        ('John Doe', 'john.doe@example.com', '123-456-7890', '123 Elm Street, Springfield'),
        ('Jane Smith', 'jane.smith@example.com', '098-765-4321', '456 Oak Avenue, Rivertown'),
        ('Alice Johnson', 'alice.johnson@example.com', '555-444-3333', '789 Maple Lane, Hilltop'),
        ('Bob Brown', 'bob.brown@example.com', '222-333-4444', '101 Pine Road, Greenfield'),
        ('Charlie Green', 'charlie.green@example.com', '666-777-8888', '202 Birch Blvd, Lakeside'),
        ('Debbie White', 'debbie.white@example.com', '999-000-1111', '303 Cedar St, Cloudcity');

        -- Products Table
        INSERT INTO sample.products (name, price) VALUES 
        ('Laptop', 1200.00),
        ('Smartphone', 800.00),
        ('Headphones', 150.00),
        ('Keyboard', 50.00),
        ('Mouse', 30.00),
        ('Monitor', 250.00);

        -- Orders Table
        -- Assuming clients and products have IDs that start at 1 and increase sequentially.
        INSERT INTO sample.orders (client_id, product_id, quantity) VALUES 
        (1, 1, 1), -- John Doe bought 1 Laptop
        (1, 2, 1), -- John Doe bought 1 Smartphone
        (2, 3, 2), -- Jane Smith bought 2 Headphones
        (3, 4, 1), -- Alice Johnson bought 1 Keyboard
        (4, 5, 1), -- Bob Brown bought 1 Mouse
        (5, 6, 2), -- Charlie Green bought 2 Monitors
        (6, 1, 1); -- Debbie White bought 1 Laptop
    """
    )

    # Add sample database to Database table, details should be the same as alembic config
    uri = op.get_context().config.get_section("alembic").get("sqlalchemy.url")

    # Transform uri like this
    # 'postgresql://admin:XXX@localhost:5432/product'
    # into
    # config = {"host":"localhost","port":"5432","user":"admin","database":"production","password":"XXX"}
    # And add schema="sample"
    config = {
        "host": uri.split("@")[1].split(":")[0],
        "port": uri.split("@")[1].split(":")[1].split("/")[0],
        "user": uri.split("@")[0].split("//")[1].split(":")[0],
        "database": "sample",
        "password": uri.split("@")[0].split("//")[1].split(":")[1],
        # Add default path to schema "sample"
        "options": {"search_path": "sample"},
    }
    op.execute(
        sa.insert(Database).values(
            name="sample",
            description="Sample database with clients, products and orders tables",
            details=config,
            _engine="postgres",
            public=True,
            ownerId="admin",
        )
    )


def downgrade() -> None:
    op.execute("DROP SCHEMA sample CASCADE")
    op.execute("DELETE FROM database WHERE name='sample'")
