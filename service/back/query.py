import uuid

from flask import Blueprint, g, jsonify, request

from middleware import database_middleware, query_middleware, user_middleware
from models import Query, UserFavorite

api = Blueprint("ai_api", __name__)


@api.route("/query/_run", methods=["POST"])
@user_middleware
@database_middleware
def run_query():
    """
    Run a query against the database
    Return eg. {"rows":[{"count":"607"}],"count":1}
    """
    if not request.json:
        return jsonify({"message": "No JSON data provided"}), 400

    sql_query = request.json.get("query")

    try:
        rows, count = g.data_warehouse.query(sql_query, role="users")
        return jsonify({"rows": rows, "count": count})
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@api.route("/query", methods=["POST"])
@user_middleware
@database_middleware
def create_query():
    if not request.json:
        return jsonify({"message": "No JSON data provided"}), 400

    title = request.json.get("title")
    sql = request.json.get("sql")

    new_query = Query(
        databaseId=g.database.id,
        title=title,
        sql=sql,
    )

    g.session.add(new_query)
    g.session.flush()

    return jsonify({"id": new_query.id})


@api.route("/query/<uuid:query_id>", methods=["GET", "PUT"])
@user_middleware
@query_middleware
def handle_query_by_id(query_id: uuid.UUID):
    """
    Run or Update a query based on the request method
    """
    # Get databaseId from query
    databaseId = g.query.databaseId

    if request.method == "PUT":
        if not request.json:
            return jsonify({"message": "No JSON data provided"}), 400
        g.query.title = request.json.get("title")
        g.query.sql = request.json.get("sql")
        g.session.flush()

    # Check if query is favorited by current user
    favorite = (
        g.session.query(UserFavorite)
        .filter(UserFavorite.user_id == g.user.id, UserFavorite.query_id == query_id)
        .first()
    )

    response = {
        "databaseId": databaseId,
        "title": g.query.title,
        "sql": g.query.sql,
        "is_favorite": favorite is not None,
    }

    return jsonify(response)


@api.route("/query/<query_id>/results", methods=["GET"])
@user_middleware
@query_middleware
def get_query_results_by_id(query_id):
    """
    Get the results of a query.
    Should only be use for conversation
    """
    if not g.query.is_cached:
        # Backward compatibility
        # We temporarily support fetching results when we don't have them
        data_warehouse = g.database.create_data_warehouse()
        rows, count = data_warehouse.query(g.query.sql, role="users")
        return jsonify({"rows": rows, "count": count})

    if g.query.exception:
        return jsonify({"message": g.query.exception}), 500
    return jsonify({"rows": g.query.rows, "count": g.query.count})
