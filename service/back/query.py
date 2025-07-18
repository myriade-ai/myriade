import uuid

from flask import Blueprint, g, jsonify, request

from middleware import database_middleware, user_middleware
from models import Database, Query, UserFavorite

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
def create_query():
    if not request.json:
        return jsonify({"message": "No JSON data provided"}), 400

    database_id = request.json.get("databaseId")
    if isinstance(database_id, str):
        try:
            database_id = uuid.UUID(database_id)
        except ValueError:
            return jsonify({"error": "Invalid databaseId"}), 400
    title = request.json.get("title")
    sql = request.json.get("sql")

    new_query = Query(
        databaseId=database_id,
        title=title,
        sql=sql,
    )

    g.session.add(new_query)
    g.session.flush()

    return jsonify({"id": new_query.id})


@api.route("/query/<uuid:query_id>", methods=["GET", "PUT"])
@user_middleware
def handle_query_by_id(query_id: uuid.UUID):
    """
    Run or Update a query based on the request method
    """
    query = g.session.query(Query).filter_by(id=query_id).first()
    if not query:
        return jsonify({"error": "Query not found"}), 404

    # Get databaseId from query
    databaseId = query.databaseId

    if request.method == "PUT":
        if not request.json:
            return jsonify({"message": "No JSON data provided"}), 400
        query.title = request.json.get("title")
        query.sql = request.json.get("sql")
        g.session.flush()

    # Check if query is favorited by current user
    favorite = (
        g.session.query(UserFavorite)
        .filter(UserFavorite.user_id == g.user.id, UserFavorite.query_id == query_id)
        .first()
    )

    response = {
        "databaseId": databaseId,
        "title": query.title,
        "sql": query.sql,
        "is_favorite": favorite is not None,
    }

    return jsonify(response)


@api.route("/query/<query_id>/results", methods=["GET"])
@user_middleware
def get_query_results_by_id(query_id):
    """
    Get the results of a query.
    Should only be use for conversation
    """
    query = g.session.query(Query).filter_by(id=query_id).first()
    if not query:
        return jsonify({"error": "Query not found"}), 404

    if not query.is_cached:
        # Backward compatibility
        # We temporarily support fetching results when we don't have them
        database = g.session.query(Database).filter_by(id=query.databaseId).first()
        data_warehouse = database.create_data_warehouse()
        rows, count = data_warehouse.query(query.sql, role="users")
        return jsonify({"rows": rows, "count": count})

    if query.exception:
        return jsonify({"message": query.exception}), 500
    return jsonify({"rows": query.rows, "count": query.count})
