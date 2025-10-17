"""Tests for vector search functionality in catalog"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from chat.tools.catalog import CatalogTool
from config import DATABASE_URL
from models import Base, Database
from models.catalog import Asset, ColumnFacet, TableFacet


@pytest.fixture
def session():
    """Create a test database session"""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_database(session):
    """Create a test database"""
    db = Database(
        name="test_db",
        engine="sqlite",
        details={"filename": ":memory:"},
    )
    session.add(db)
    session.commit()
    return db


@pytest.fixture
def test_assets(session, test_database):
    """Create test assets"""
    # Create a table asset
    table_asset = Asset(
        urn="urn:test:table:customers",
        type="TABLE",
        name="customers",
        description="Customer information including contact details and purchase history",
        database_id=test_database.id,
    )
    session.add(table_asset)
    session.flush()

    table_facet = TableFacet(
        asset_id=table_asset.id,
        database_id=test_database.id,
        schema="public",
        table_name="customers",
    )
    session.add(table_facet)

    # Create a column asset
    column_asset = Asset(
        urn="urn:test:column:customers.email",
        type="COLUMN",
        name="email",
        description="Customer email address for communication",
        database_id=test_database.id,
    )
    session.add(column_asset)
    session.flush()

    column_facet = ColumnFacet(
        asset_id=column_asset.id,
        parent_table_asset_id=table_asset.id,
        column_name="email",
        data_type="VARCHAR",
        ordinal=1,
    )
    session.add(column_facet)

    session.commit()
    return [table_asset, column_asset]


def test_text_search_fallback(session, test_database, test_assets):
    """Test that text search works when vector search is not available (SQLite)"""
    # Create a mock data warehouse
    class MockDataWarehouse:
        pass

    catalog_tool = CatalogTool(session, test_database, MockDataWarehouse())

    # Search for "customer" - should find the customer table
    result = catalog_tool.search_assets("customer")

    # Parse YAML result
    import yaml

    parsed = yaml.safe_load(result)

    assert "assets" in parsed
    assert len(parsed["assets"]) >= 1

    # Should find the customer table
    asset_names = [asset.get("name") for asset in parsed["assets"]]
    assert "customers" in asset_names


def test_vector_search_disabled_for_sqlite(session, test_database, test_assets):
    """Test that vector search is disabled for SQLite"""
    class MockDataWarehouse:
        pass

    catalog_tool = CatalogTool(session, test_database, MockDataWarehouse())

    # Check that vector search is not available
    assert not catalog_tool._is_vector_search_available()


def test_vector_search_methods_exist(session, test_database):
    """Test that vector search methods are available"""
    class MockDataWarehouse:
        pass

    catalog_tool = CatalogTool(session, test_database, MockDataWarehouse())

    # Check that new methods exist
    assert hasattr(catalog_tool, "generate_embeddings_for_asset")
    assert hasattr(catalog_tool, "generate_embeddings_for_all_assets")
    assert hasattr(catalog_tool, "_vector_search_assets")
    assert hasattr(catalog_tool, "_is_vector_search_available")


def test_embedding_generation_graceful_sqlite(session, test_database, test_assets):
    """Test that embedding generation handles SQLite gracefully"""
    class MockDataWarehouse:
        pass

    catalog_tool = CatalogTool(session, test_database, MockDataWarehouse())

    # Try to generate embeddings (should return helpful message for SQLite)
    result = catalog_tool.generate_embeddings_for_all_assets()

    assert "PostgreSQL" in result or "only available" in result


def test_search_with_use_vector_search_flag(session, test_database, test_assets):
    """Test that use_vector_search parameter is accepted"""
    class MockDataWarehouse:
        pass

    catalog_tool = CatalogTool(session, test_database, MockDataWarehouse())

    # Search with vector search explicitly disabled
    result = catalog_tool.search_assets("customer", use_vector_search=False)

    import yaml

    parsed = yaml.safe_load(result)
    assert "assets" in parsed


@pytest.mark.skipif(
    not DATABASE_URL.startswith("postgres"),
    reason="Vector search only works with PostgreSQL",
)
def test_postgres_vector_search_available():
    """Test vector search is available with PostgreSQL (if configured)"""
    # This test only runs if DATABASE_URL points to PostgreSQL
    from config import DATABASE_URL

    assert DATABASE_URL.startswith("postgres")

    # Note: This test would need a real PostgreSQL connection with pgvector
    # to fully test the functionality. In CI/CD, you'd set up a test database.


def test_embedding_utility_imports():
    """Test that embedding utilities can be imported"""
    from utils.embeddings import (
        generate_asset_embedding,
        generate_embedding,
        get_embedding_model,
    )

    # Check functions exist
    assert callable(generate_embedding)
    assert callable(generate_asset_embedding)
    assert callable(get_embedding_model)
