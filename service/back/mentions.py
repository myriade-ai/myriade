"""API endpoints for @ mention functionality in markdown editors."""

import logging

from flask import Blueprint, g, jsonify, request
from sqlalchemy import and_, or_

from back.api import extract_context
from middleware import user_middleware
from models import Chart, Query

logger = logging.getLogger(__name__)
mentions_api = Blueprint("mentions_api", __name__)


@mentions_api.route("/contexts/<context_id>/mentions/recent", methods=["GET"])
@user_middleware
def get_recent_mentions(context_id: str):
    """
    Get the last 10 recently updated items (max 5 queries + 5 charts).

    Returns:
        JSON with queries and charts arrays sorted by updatedAt
    """
    try:
        # Extract database_id from context
        database_id, _ = extract_context(g.session, context_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Get last 5 queries sorted by updatedAt
    queries = (
        g.session.query(Query)
        .filter(
            and_(
                Query.databaseId == database_id,
                Query.rows.isnot(None),  # Only completed queries with results
                Query.exception.is_(None),  # No failed queries
            )
        )
        .order_by(Query.updatedAt.desc())
        .limit(5)
        .all()
    )

    # Get last 5 charts sorted by updatedAt
    charts = (
        g.session.query(Chart)
        .join(Query, Query.id == Chart.queryId)
        .filter(Query.databaseId == database_id)
        .order_by(Chart.updatedAt.desc())
        .limit(5)
        .all()
    )

    # Format response
    queries_data = [
        {
            "id": str(q.id),
            "title": q.title or "Untitled Query",
            "sql": q.sql[:100] if q.sql else "",  # Truncate SQL for preview
            "updated_at": q.updatedAt.isoformat() if q.updatedAt else None,
        }
        for q in queries
    ]

    charts_data = [
        {
            "id": str(c.id),
            "title": c.title or "Untitled Chart",
            "updated_at": c.updatedAt.isoformat() if c.updatedAt else None,
        }
        for c in charts
    ]

    return jsonify(
        {
            "queries": queries_data,
            "charts": charts_data,
        }
    )


@mentions_api.route("/contexts/<context_id>/mentions/search", methods=["GET"])
@user_middleware
def search_mentions(context_id: str):
    """
    Search queries and charts by title/SQL content.

    Query Parameters:
        - q: Search string to filter by title/SQL content (required)
        - limit: Maximum number of results per type (default: 25, max: 50)

    Returns:
        JSON with queries and charts arrays matching the search
    """
    try:
        # Extract database_id from context
        database_id, _ = extract_context(g.session, context_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Get search query parameter
    search = request.args.get("q", "").strip()
    if not search:
        return jsonify({"queries": [], "charts": []})

    limit = min(int(request.args.get("limit", 25)), 50)  # Cap at 50
    search_pattern = f"%{search}%"

    # Search queries
    queries = (
        g.session.query(Query)
        .filter(
            and_(
                Query.databaseId == database_id,
                Query.rows.isnot(None),  # Only completed queries with results
                Query.exception.is_(None),  # No failed queries
                or_(
                    Query.title.ilike(search_pattern),
                    Query.sql.ilike(search_pattern),
                ),
            )
        )
        .order_by(Query.updatedAt.desc())
        .limit(limit)
        .all()
    )

    # Search charts
    charts = (
        g.session.query(Chart)
        .join(Query, Query.id == Chart.queryId)
        .filter(
            and_(
                Query.databaseId == database_id,
                Chart.title.ilike(search_pattern),
            )
        )
        .order_by(Chart.updatedAt.desc())
        .limit(limit)
        .all()
    )

    # Format response
    queries_data = [
        {
            "id": str(q.id),
            "title": q.title or "Untitled Query",
            "sql": q.sql[:100] if q.sql else "",  # Truncate SQL for preview
            "updated_at": q.updatedAt.isoformat() if q.updatedAt else None,
        }
        for q in queries
    ]

    charts_data = [
        {
            "id": str(c.id),
            "title": c.title or "Untitled Chart",
            "updated_at": c.updatedAt.isoformat() if c.updatedAt else None,
        }
        for c in charts
    ]

    return jsonify(
        {
            "queries": queries_data,
            "charts": charts_data,
        }
    )
