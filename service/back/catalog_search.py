"""
Catalog search functionality for both REST API and chat tools.

Provides search capabilities for catalog assets with PostgreSQL trigram similarity
matching and SQLite ILIKE fallback.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.catalog import Asset, AssetTag, Term

logger = logging.getLogger(__name__)


def search_assets(
    session: Session,
    database_id: UUID,
    text: str,
    asset_type: Optional[str] = None,
    limit: Optional[int] = 50,
    tag_ids: Optional[List[str]] = None,
    statuses: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Search catalog assets by text query. Returns ONLY assets (no terms).

    Uses PostgreSQL trigram similarity for fuzzy matching when available,
    falls back to ILIKE pattern matching for SQLite.

    Args:
        session: SQLAlchemy session
        database_id: UUID of the database to search within
        text: Search query string
        asset_type: Optional filter by asset type ("TABLE", "COLUMN", "SCHEMA", "DATABASE")
        limit: Maximum number of results (default 50)
        tag_ids: Optional list of tag UUIDs to filter by
        statuses: Optional list of status values to filter by ("validated", "needs_review", etc. or None/"unverified")

    Returns:
        List of matching assets as dictionaries with id, name, type, etc.
    """
    is_postgresql = session.bind.dialect.name == "postgresql"
    assets = _execute_asset_search(
        session, database_id, text, asset_type, limit, is_postgresql, tag_ids, statuses
    )

    # Convert Asset model instances to dictionaries
    return [_format_asset_result(asset) for asset in assets]


def search_assets_and_terms(
    session: Session,
    database_id: UUID,
    text: str,
    asset_type: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search both catalog assets and terms. Used by chat tools.

    Returns both assets and terms in a structured dictionary.

    Args:
        session: SQLAlchemy session
        database_id: UUID of the database to search within
        text: Search query string
        asset_type: Optional filter by asset type ("TABLE", "COLUMN", "TERM")
        limit: Maximum number of results (default 50)

    Returns:
        Dictionary with "assets" and "terms" keys containing matching results
    """
    is_postgresql = session.bind.dialect.name == "postgresql"

    assets = []
    terms = []

    # Handle terms separately
    if asset_type == "TERM":
        terms = _execute_term_search(session, database_id, text, limit, is_postgresql)
    else:
        # Handle assets
        assets = _execute_asset_search(
            session, database_id, text, asset_type, limit, is_postgresql
        )

        # If no specific asset type filter, also search terms
        if asset_type is None:
            terms = _execute_term_search(
                session, database_id, text, limit, is_postgresql
            )

    return {
        "assets": [_format_asset_result(asset) for asset in assets],
        "terms": [_format_term_result(term) for term in terms],
    }


def _execute_asset_search(
    session: Session,
    database_id: UUID,
    text: str,
    asset_type: Optional[str],
    limit: Optional[int],
    is_postgresql: bool,
    tag_ids: Optional[List[str]] = None,
    statuses: Optional[List[str]] = None,
) -> List[Asset]:
    """
    Execute asset search with fuzzy matching support.

    PostgreSQL: Uses similarity threshold to catch typos and fuzzy matches
    SQLite: Uses ILIKE pattern matching

    Args:
        session: SQLAlchemy session
        database_id: UUID of the database
        text: Search query string
        asset_type: Optional asset type filter
        limit: Maximum number of results
        is_postgresql: Whether using PostgreSQL
        tag_ids: Optional list of tag UUIDs to filter by
        statuses: Optional list of status values to filter by

    Returns:
        List of Asset model instances
    """
    if is_postgresql:
        similarity_threshold = 0.3
        similarity_score = func.similarity(Asset.name, text).label("similarity_score")

        query = (
            session.query(Asset, similarity_score)
            .outerjoin(Asset.asset_tags)
            .filter(Asset.database_id == database_id)
            .filter(
                # Use similarity for fuzzy matching
                (func.similarity(Asset.name, text) > similarity_threshold)
                | Asset.description.ilike(f"%{text}%")
                | Asset.urn.ilike(f"%{text}%")
                | AssetTag.name.ilike(f"%{text}%")
            )
            .distinct()
        )

        if asset_type:
            query = query.filter(Asset.type == asset_type.upper())

        # Apply tag filter if specified
        if tag_ids:
            tag_uuids = [UUID(tag_id) for tag_id in tag_ids]
            query = query.filter(AssetTag.id.in_(tag_uuids))

        # Apply status filter if specified (handles both explicit statuses and "unverified" as NULL)
        if statuses:
            from sqlalchemy import or_
            status_filters = []
            for status in statuses:
                if status == "unverified":
                    # "unverified" means status IS NULL
                    status_filters.append(Asset.status.is_(None))
                else:
                    status_filters.append(Asset.status == status)
            query = query.filter(or_(*status_filters))

        # Order by similarity BEFORE applying limit
        query = query.order_by(similarity_score.desc(), Asset.name.asc())

        if limit is not None:
            query = query.limit(limit)

        results = query.all()

        # Extract just the Asset objects
        return [asset for asset, _ in results]

    # SQLite: Simple ILIKE query without fuzzy matching
    else:
        query = (
            session.query(Asset)
            .outerjoin(Asset.asset_tags)
            .filter(Asset.database_id == database_id)
            .filter(
                Asset.name.ilike(f"%{text}%")
                | Asset.description.ilike(f"%{text}%")
                | Asset.urn.ilike(f"%{text}%")
                | AssetTag.name.ilike(f"%{text}%")
            )
            .distinct()
        )

        if asset_type:
            query = query.filter(Asset.type == asset_type.upper())

        # Apply tag filter if specified
        if tag_ids:
            tag_uuids = [UUID(tag_id) for tag_id in tag_ids]
            query = query.filter(AssetTag.id.in_(tag_uuids))

        # Apply status filter if specified (handles both explicit statuses and "unverified" as NULL)
        if statuses:
            from sqlalchemy import or_
            status_filters = []
            for status in statuses:
                if status == "unverified":
                    # "unverified" means status IS NULL
                    status_filters.append(Asset.status.is_(None))
                else:
                    status_filters.append(Asset.status == status)
            query = query.filter(or_(*status_filters))

        if limit is not None:
            return query.limit(limit).all()
        return query.all()


def _execute_term_search(
    session: Session,
    database_id: UUID,
    text: str,
    limit: int,
    is_postgresql: bool,
) -> List[Term]:
    """
    Execute term search with fuzzy matching support.

    PostgreSQL: Uses similarity threshold to catch typos and fuzzy matches
    SQLite: Uses ILIKE pattern matching

    Args:
        session: SQLAlchemy session
        database_id: UUID of the database
        text: Search query string
        limit: Maximum number of results
        is_postgresql: Whether using PostgreSQL

    Returns:
        List of Term model instances
    """
    if is_postgresql:
        similarity_threshold = 0.3
        similarity_score = func.similarity(Term.name, text).label("similarity_score")

        query = (
            session.query(Term, similarity_score)
            .filter(Term.database_id == database_id)
            .filter(
                # Use similarity for fuzzy matching
                (func.similarity(Term.name, text) > similarity_threshold)
                | Term.definition.ilike(f"%{text}%")
            )
        )

        results = (
            query.order_by(similarity_score.desc(), Term.name.asc()).limit(limit).all()
        )

        # Extract just the Term objects
        return [term for term, _ in results]

    # SQLite: Simple ILIKE query without fuzzy matching
    else:
        query = (
            session.query(Term)
            .filter(Term.database_id == database_id)
            .filter(Term.name.ilike(f"%{text}%") | Term.definition.ilike(f"%{text}%"))
        )

        return query.limit(limit).all()


def _format_asset_result(asset: Asset) -> Dict[str, Any]:
    """
    Format an Asset model instance as a dictionary for API responses.

    Args:
        asset: Asset model instance

    Returns:
        Dictionary with asset data
    """
    asset_dict = {
        "id": str(asset.id),
        "urn": asset.urn,
        "name": asset.name,
        "type": asset.type,
        "status": asset.status or None,
        "description": (
            asset.description[:200] + "..."
            if asset.description and len(asset.description) > 200
            else asset.description
        ),
        "tags": [{"id": str(tag.id), "name": tag.name} for tag in asset.asset_tags],
    }

    # Add type-specific information for tables
    if asset.type == "TABLE" and asset.table_facet:
        facet = asset.table_facet
        asset_dict.update(
            {
                "database_name": facet.database_name,
                "schema": facet.schema,
                "table_name": facet.table_name,
            }
        )

    # Add type-specific information for columns
    elif asset.type == "COLUMN" and asset.column_facet:
        facet = asset.column_facet
        asset_dict.update(
            {
                "column_name": facet.column_name,
                "data_type": facet.data_type,
                "ordinal": facet.ordinal,
                "parent_table_asset_id": str(facet.parent_table_asset_id),
            }
        )

    return asset_dict


def _format_term_result(term: Term) -> Dict[str, Any]:
    """
    Format a Term model instance as a dictionary for API responses.

    Args:
        term: Term model instance

    Returns:
        Dictionary with term data
    """
    return {
        "id": str(term.id),
        "name": term.name,
        "type": "TERM",
        "description": (
            term.definition[:200] + "..."
            if term.definition and len(term.definition) > 200
            else term.definition
        ),
        "synonyms": term.synonyms,
        "business_domains": term.business_domains,
    }
