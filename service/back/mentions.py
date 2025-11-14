"""API endpoints for @ mention functionality in markdown editors."""

import logging

from flask import Blueprint, g, jsonify, request
from sqlalchemy import and_, or_

from back.api import extract_context
from middleware import user_middleware
from models import Chart, Query

logger = logging.getLogger(__name__)
mentions_api = Blueprint("mentions_api", __name__)


@mentions_api.route("/contexts/<context_id>/mentions", methods=["GET"])
@user_middleware
def get_mentions(context_id: str):
    """
    Get all queries and charts available for @ mentions in a context.

    Query Parameters:
        - search: Optional search string to filter by title/SQL content
        - limit: Maximum number of results per type (default: 25)

    Returns:
        JSON with queries and charts arrays
    """
    try:
        # Extract database_id from context
        database_id, _ = extract_context(g.session, context_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Get query parameters
    search = request.args.get("search", "").strip()
    limit = min(int(request.args.get("limit", 25)), 50)  # Cap at 50

    # Query for queries
    queries_query = g.session.query(Query).filter(
        and_(
            Query.databaseId == database_id,
            Query.rows.isnot(None),  # Only completed queries with results
            Query.exception.is_(None),  # No failed queries
        )
    )

    # Apply search filter for queries
    if search:
        search_pattern = f"%{search}%"
        queries_query = queries_query.filter(
            or_(
                Query.title.ilike(search_pattern),
                Query.sql.ilike(search_pattern),
            )
        )

    # Order by most recent and limit
    queries_query = queries_query.order_by(Query.createdAt.desc()).limit(limit)
    queries = queries_query.all()

    # Query for charts
    charts_query = (
        g.session.query(Chart)
        .join(Query, Query.id == Chart.queryId)
        .filter(Query.databaseId == database_id)
    )

    # Apply search filter for charts using the title column
    if search:
        search_pattern = f"%{search}%"
        charts_query = charts_query.filter(Chart.title.ilike(search_pattern))

    # Order by most recent and limit
    charts_query = charts_query.order_by(Chart.createdAt.desc()).limit(limit)
    charts = charts_query.all()

    # Format response
    queries_data = []
    for query in queries:
        queries_data.append(
            {
                "id": str(query.id),
                "title": query.title or "Untitled Query",
                "sql": query.sql[:100] if query.sql else "",  # Truncate SQL for preview
                "updated_at": query.createdAt.isoformat() if query.createdAt else None,
            }
        )

    charts_data = []
    for chart in charts:
        charts_data.append(
            {
                "id": str(chart.id),
                "title": chart.title or "Untitled Chart",
                "updated_at": chart.createdAt.isoformat() if chart.createdAt else None,
            }
        )

    return jsonify(
        {
            "queries": queries_data,
            "charts": charts_data,
        }
    )
