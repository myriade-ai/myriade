"""API endpoints for @ mention functionality in markdown editors."""

import logging
from typing import Any

from flask import Blueprint, g, jsonify, request
from sqlalchemy import and_, or_

from back.api import extract_context
from middleware import user_middleware
from models import Chart, Query

logger = logging.getLogger(__name__)
mentions_api = Blueprint("mentions_api", __name__)


def extract_chart_title(config: dict[str, Any]) -> str:
    """
    Extract the title from a chart config object.
    ECharts config can have title in various places:
    - config.title (string)
    - config.title.text (string)
    - config.option.title.text (for some chart types)
    """
    if not config:
        return "Untitled Chart"

    # Try direct title field (string)
    if isinstance(config.get("title"), str):
        return config["title"]

    # Try title.text (ECharts format)
    title_obj = config.get("title", {})
    if isinstance(title_obj, dict):
        text = title_obj.get("text")
        if text:
            return text

    # Try option.title.text (nested format)
    option = config.get("option", {})
    if isinstance(option, dict):
        title_obj = option.get("title", {})
        if isinstance(title_obj, dict):
            text = title_obj.get("text")
            if text:
                return text

    return "Untitled Chart"


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

    # For charts, we need to search in the config JSON
    # Note: Searching in JSON is database-specific
    # For PostgreSQL, we can use JSON operators
    # For SQLite, we'll fetch all and filter in Python (less efficient but works)
    charts_query = charts_query.order_by(Chart.createdAt.desc())

    # Fetch charts (limit after filtering if search is provided)
    if search:
        # Fetch more than needed and filter in Python
        all_charts = charts_query.limit(limit * 3).all()
        search_lower = search.lower()

        filtered_charts = []
        for chart in all_charts:
            title = extract_chart_title(chart.config)
            if search_lower in title.lower():
                filtered_charts.append(chart)
                if len(filtered_charts) >= limit:
                    break
        charts = filtered_charts
    else:
        charts = charts_query.limit(limit).all()

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
                "title": extract_chart_title(chart.config),
                "updated_at": chart.createdAt.isoformat() if chart.createdAt else None,
            }
        )

    return jsonify(
        {
            "queries": queries_data,
            "charts": charts_data,
        }
    )
