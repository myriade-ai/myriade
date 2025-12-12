"""
Catalog search functionality for both REST API and chat tools.

Provides hybrid search capabilities combining:
- PostgreSQL trigram similarity (fuzzy matching for typos and variations)
- PostgreSQL full-text search with tsvector (semantic matching with stemming)
- SQLite ILIKE fallback for development environments

This hybrid approach gives the best of both worlds: catching typos while
understanding multi-word queries and word variations.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.orm import Query, Session, joinedload

from back.utils import get_dialect_name
from models.catalog import Asset, AssetTag, ColumnFacet, Term

logger = logging.getLogger(__name__)


def _apply_tag_filter(query: Query, tag_ids: Optional[List[str]]) -> Query:
    """Apply tag filter to query if tag_ids are provided."""
    if tag_ids:
        tag_uuids = [UUID(tag_id) for tag_id in tag_ids]
        return query.filter(AssetTag.id.in_(tag_uuids))
    return query


def _apply_status_filter(query: Query, statuses: Optional[List[str]]) -> Query:
    """Apply status filter to query if statuses are provided."""
    if statuses:
        status_filters = [
            Asset.status.is_(None) if status == "unverified" else Asset.status == status
            for status in statuses
        ]
        return query.filter(or_(*status_filters))
    return query


def _apply_asset_type_filter(query: Query, asset_type: Optional[str]) -> Query:
    """Apply asset type filter to query if asset_type is provided."""
    if asset_type:
        return query.filter(Asset.type == asset_type.upper())
    return query


def _apply_ai_suggestion_filter(
    query: Query, has_ai_suggestion: Optional[bool]
) -> Query:
    """Apply AI suggestion filter to query if specified."""
    if has_ai_suggestion is True:
        return query.filter(
            or_(
                Asset.ai_suggestion.isnot(None),
                Asset.ai_suggested_tags.isnot(None),
            )
        )
    elif has_ai_suggestion is False:
        return query.filter(
            Asset.ai_suggestion.is_(None),
            Asset.ai_suggested_tags.is_(None),
        )
    return query


def _apply_parent_asset_filter(query: Query, parent_asset_id: Optional[str]) -> Query:
    """Apply parent asset filter to query if parent_asset_id is provided.

    Filters assets based on their parent asset. Useful for:
    - Finding columns within a specific table
    - Finding tables within a specific schema
    - Finding schemas within a specific database
    """
    if not parent_asset_id:
        return query

    parent_id = UUID(parent_asset_id)

    return query.filter(
        or_(
            # Columns with matching parent table
            (Asset.type == "COLUMN")
            & (Asset.column_facet.has(parent_table_asset_id=parent_id)),
            # Tables with matching parent schema
            (Asset.type == "TABLE")
            & (Asset.table_facet.has(parent_schema_asset_id=parent_id)),
            # Schemas with matching parent database
            (Asset.type == "SCHEMA")
            & (Asset.schema_facet.has(parent_database_asset_id=parent_id)),
        )
    )


def _apply_common_filters(
    query: Query,
    asset_type: Optional[str],
    tag_ids: Optional[List[str]],
    statuses: Optional[List[str]],
    has_ai_suggestion: Optional[bool] = None,
    parent_asset_id: Optional[str] = None,
) -> Query:
    """Apply all common filters (asset_type, tags, statuses, ai_suggestion, parent_asset) to a query."""
    query = _apply_asset_type_filter(query, asset_type)
    query = _apply_tag_filter(query, tag_ids)
    query = _apply_status_filter(query, statuses)
    query = _apply_ai_suggestion_filter(query, has_ai_suggestion)
    query = _apply_parent_asset_filter(query, parent_asset_id)
    return query


def search_assets(
    session: Session,
    database_id: UUID,
    text: Optional[str] = None,
    asset_type: Optional[str] = None,
    limit: int = 50,
    tag_ids: Optional[List[str]] = None,
    statuses: Optional[List[str]] = None,
    has_ai_suggestion: Optional[bool] = None,
    parent_asset_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search catalog assets by text query and/or filters. Returns ONLY assets (no terms).

    Uses PostgreSQL trigram similarity for fuzzy matching when available,
    falls back to ILIKE pattern matching for SQLite.

    Args:
        session: SQLAlchemy session
        database_id: UUID of the database to search within
        text: Search query string (optional when filters are provided)
        asset_type: Optional filter by asset type ("TABLE", "COLUMN", "SCHEMA", "DATABASE")
        limit: Maximum number of results (default 50)
        tag_ids: Optional list of tag UUIDs to filter by
        statuses: Optional list of status values to filter by ("validated", "needs_review", etc. or None/"unverified")
        has_ai_suggestion: Optional filter for assets with/without AI suggestions
        parent_asset_id: Optional filter to find children of a specific asset (e.g., columns within a table)

    Returns:
        List of matching assets as dictionaries with id, name, type, etc.
    """
    is_postgresql = get_dialect_name(session) == "postgresql"
    assets, _ = _execute_asset_search(
        session,
        database_id,
        text,
        asset_type,
        limit,
        is_postgresql,
        tag_ids,
        statuses,
        has_ai_suggestion,
        parent_asset_id,
    )

    return [_format_asset_result(asset) for asset in assets]


def search_assets_and_terms(
    session: Session,
    database_id: UUID,
    text: str,
    asset_type: Optional[str] = None,
    limit: int = 50,
    statuses: Optional[List[str]] = None,
    parent_asset_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search both catalog assets and terms. Used by chat tools.

    Returns both assets and terms in a structured dictionary with total counts.

    Args:
        session: SQLAlchemy session
        database_id: UUID of the database to search within
        text: Search query string
        asset_type: Optional filter by asset type ("TABLE", "COLUMN", "TERM")
        limit: Maximum number of results (default 50)
        statuses: Optional list of status values to filter by ("draft", "published", "unverified")
        parent_asset_id: Optional filter to find children of a specific asset (e.g., columns within a table)

    Returns:
        Dictionary with "assets", "terms", "total_assets", and "total_terms" keys
    """
    is_postgresql = get_dialect_name(session) == "postgresql"

    assets: List[Asset] = []
    terms: List[Term] = []
    total_assets = 0
    total_terms = 0

    if asset_type == "TERM":
        terms, total_terms = _execute_term_search(
            session, database_id, text, limit, is_postgresql
        )
    else:
        assets, total_assets = _execute_asset_search(
            session,
            database_id,
            text,
            asset_type,
            limit,
            is_postgresql,
            statuses=statuses,
            parent_asset_id=parent_asset_id,
        )

        # If no specific asset type filter, also search terms
        if asset_type is None:
            terms, total_terms = _execute_term_search(
                session, database_id, text, limit, is_postgresql
            )

    # Get column counts for TABLE assets in a single query
    table_asset_ids = [asset.id for asset in assets if asset.type == "TABLE"]
    column_counts = _get_column_counts_for_tables(session, table_asset_ids)

    return {
        "assets": [
            _format_asset_result(asset, column_counts.get(asset.id)) for asset in assets
        ],
        "terms": [_format_term_result(term) for term in terms],
        "total_assets": total_assets,
        "total_terms": total_terms,
    }


def _execute_postgresql_search(
    session: Session,
    database_id: UUID,
    text: Optional[str],
    asset_type: Optional[str],
    limit: Optional[int],
    tag_ids: Optional[List[str]],
    statuses: Optional[List[str]],
    has_ai_suggestion: Optional[bool] = None,
    parent_asset_id: Optional[str] = None,
) -> Tuple[List[Asset], int]:
    """Execute PostgreSQL asset search with optional text matching.

    Returns:
        Tuple of (list of matching assets, total count before limit applied)
    """
    similarity_threshold = 0.3

    # Build base query
    base_query = (
        session.query(Asset)
        .options(joinedload(Asset.asset_tags))  # Eager load to prevent N+1
        .outerjoin(Asset.asset_tags)  # Join for searching tag names or filtering
        .filter(Asset.database_id == database_id)
        .distinct()
    )

    # If no text search, use simple query without similarity scoring
    if not text:
        query = _apply_common_filters(
            base_query,
            asset_type,
            tag_ids,
            statuses,
            has_ai_suggestion,
            parent_asset_id,
        )
        query = query.order_by(Asset.name.asc())

        # Get total count before applying limit
        total = query.count()

        if limit is not None:
            query = query.limit(limit)

        return query.all(), total

    # Text search with similarity scoring
    tsquery = func.plainto_tsquery("english", text)

    # Calculate weighted similarity scores
    name_score = func.coalesce(func.similarity(Asset.name, text), 0) * 5
    tag_score = func.coalesce(func.similarity(AssetTag.name, text), 0)
    description_score = func.coalesce(func.similarity(Asset.description, text), 0)
    ai_suggestion_score = func.coalesce(func.similarity(Asset.ai_suggestion, text), 0)
    fts_score = func.coalesce(func.ts_rank(Asset.search_vector, tsquery), 0) * 2

    similarity_score = (
        name_score + tag_score + description_score + ai_suggestion_score + fts_score
    ).label("similarity_score")

    # Query with similarity scoring
    query = (
        session.query(Asset, similarity_score)
        .options(joinedload(Asset.asset_tags))
        .outerjoin(Asset.asset_tags)
        .filter(Asset.database_id == database_id)
        .filter(
            (func.similarity(Asset.name, text) > similarity_threshold)
            | (func.similarity(AssetTag.name, text) > similarity_threshold)
            | (func.similarity(Asset.description, text) > similarity_threshold)
            | (func.similarity(Asset.ai_suggestion, text) > similarity_threshold)
            | (Asset.search_vector.op("@@")(tsquery))
            | Asset.urn.ilike(f"%{text}%")
        )
        .distinct()
    )

    query = _apply_common_filters(
        query, asset_type, tag_ids, statuses, has_ai_suggestion, parent_asset_id
    )
    query = query.order_by(similarity_score.desc(), Asset.name.asc())

    # Get total count before applying limit
    total = query.count()

    if limit is not None:
        query = query.limit(limit)

    results = query.all()
    return [asset for asset, _ in results], total


def _execute_asset_search(
    session: Session,
    database_id: UUID,
    text: Optional[str],
    asset_type: Optional[str],
    limit: Optional[int],
    is_postgresql: bool,
    tag_ids: Optional[List[str]] = None,
    statuses: Optional[List[str]] = None,
    has_ai_suggestion: Optional[bool] = None,
    parent_asset_id: Optional[str] = None,
) -> Tuple[List[Asset], int]:
    """
    Execute asset search with fuzzy matching support.

    PostgreSQL: Uses similarity threshold to catch typos and fuzzy matches
    SQLite: Uses ILIKE pattern matching

    Args:
        session: SQLAlchemy session
        database_id: UUID of the database
        text: Search query string (optional when filters are provided)
        asset_type: Optional asset type filter
        limit: Maximum number of results
        is_postgresql: Whether using PostgreSQL
        tag_ids: Optional list of tag UUIDs to filter by
        statuses: Optional list of status values to filter by
        has_ai_suggestion: Optional filter for assets with/without AI suggestions
        parent_asset_id: Optional filter to find children of a specific asset

    Returns:
        Tuple of (list of Asset model instances, total count before limit applied)
    """

    if is_postgresql:
        return _execute_postgresql_search(
            session,
            database_id,
            text,
            asset_type,
            limit,
            tag_ids,
            statuses,
            has_ai_suggestion,
            parent_asset_id,
        )

    # SQLite: Simple ILIKE query without fuzzy matching
    query = (
        session.query(Asset)
        .options(joinedload(Asset.asset_tags))  # Eager load to prevent N+1
        .outerjoin(Asset.asset_tags)  # Join for searching tag names
        .filter(Asset.database_id == database_id)
        .distinct()
    )

    # Add text search filters if text is provided
    if text:
        query = query.filter(
            Asset.name.ilike(f"%{text}%")
            | Asset.description.ilike(f"%{text}%")
            | Asset.ai_suggestion.ilike(f"%{text}%")
            | Asset.urn.ilike(f"%{text}%")
            | AssetTag.name.ilike(f"%{text}%")  # Search tag names
        )

    query = _apply_common_filters(
        query, asset_type, tag_ids, statuses, has_ai_suggestion, parent_asset_id
    )

    # Get total count before applying limit
    total = query.count()

    if limit is not None:
        return query.limit(limit).all(), total
    return query.all(), total


def _execute_term_search(
    session: Session,
    database_id: UUID,
    text: str,
    limit: int,
    is_postgresql: bool,
) -> Tuple[List[Term], int]:
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
        Tuple of (list of Term model instances, total count before limit applied)
    """
    if is_postgresql:
        similarity_threshold = 0.3

        # Create tsquery for full-text search
        tsquery = func.plainto_tsquery("english", text)

        # Calculate weighted similarity score: name is 5x more important than definition
        # Use COALESCE to handle NULL values (treat as 0 similarity)
        name_score = func.coalesce(func.similarity(Term.name, text), 0) * 5
        definition_score = func.coalesce(func.similarity(Term.definition, text), 0)

        # Calculate full-text search score using ts_rank
        fts_score = func.coalesce(func.ts_rank(Term.search_vector, tsquery), 0) * 2

        similarity_score = (name_score + definition_score + fts_score).label(
            "similarity_score"
        )

        query = (
            session.query(Term, similarity_score)
            .filter(Term.database_id == database_id)
            .filter(
                # Use similarity for fuzzy matching on both name and definition
                (func.similarity(Term.name, text) > similarity_threshold)
                | (func.similarity(Term.definition, text) > similarity_threshold)
                # Full-text search matching using @@ operator
                | (Term.search_vector.op("@@")(tsquery))
            )
        )

        # Get total count before applying limit
        total = query.count()

        results = (
            query.order_by(similarity_score.desc(), Term.name.asc()).limit(limit).all()
        )

        return [term for term, _ in results], total

    # SQLite: Simple ILIKE query without fuzzy matching
    else:
        query = (
            session.query(Term)
            .filter(Term.database_id == database_id)
            .filter(Term.name.ilike(f"%{text}%") | Term.definition.ilike(f"%{text}%"))
        )

        # Get total count before applying limit
        total = query.count()

        return query.limit(limit).all(), total


def _get_column_counts_for_tables(
    session: Session, table_asset_ids: List[UUID]
) -> Dict[UUID, int]:
    """
    Get column counts for multiple table assets in a single query.

    Args:
        session: SQLAlchemy session
        table_asset_ids: List of table asset UUIDs

    Returns:
        Dictionary mapping table asset ID to column count
    """
    if not table_asset_ids:
        return {}

    counts = (
        session.query(
            ColumnFacet.parent_table_asset_id,
            func.count(ColumnFacet.asset_id).label("column_count"),
        )
        .filter(ColumnFacet.parent_table_asset_id.in_(table_asset_ids))
        .group_by(ColumnFacet.parent_table_asset_id)
        .all()
    )

    return {parent_id: count for parent_id, count in counts}


def _format_asset_result(
    asset: Asset, column_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Format an Asset model instance as a dictionary for API responses.

    Args:
        asset: Asset model instance
        column_count: Optional pre-computed column count for TABLE assets

    Returns:
        Dictionary with asset data
    """
    asset_dict = {
        "id": str(asset.id),
        "urn": asset.urn,
        "name": asset.name,
        "type": asset.type,
        "status": asset.status or None,
        "published_by": asset.published_by,
        "published_at": asset.published_at.isoformat() if asset.published_at else None,
        "description": (
            asset.description[:200] + "..."
            if asset.description and len(asset.description) > 200
            else asset.description
        ),
        "tags": [{"id": str(tag.id), "name": tag.name} for tag in asset.asset_tags],
        "has_ai_suggestion": asset.ai_suggestion is not None,
        "has_ai_suggested_tags": (
            asset.ai_suggested_tags is not None and len(asset.ai_suggested_tags) > 0
        ),
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
        if column_count is not None:
            asset_dict["column_count"] = column_count

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
