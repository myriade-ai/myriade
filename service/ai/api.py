from flask import Blueprint, g, jsonify, request

from middleware import database_middleware, user_middleware
from models import Database, Query

api = Blueprint("ai_api", __name__)


@api.route("/query/_run", methods=["POST"])
@user_middleware
@database_middleware
def run_query():
    """
    Run a query against the database
    Return eg. {"rows":[{"count":"607"}],"count":1}
    """
    sql_query = request.json.get("query")

    try:
        rows, count = g.datalake.query(sql_query, role="users")
        return jsonify({"rows": rows, "count": count})
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@api.route("/query", methods=["POST"])
@user_middleware
def create_query():
    database_id = request.json.get("databaseId")
    title = request.json.get("title")
    sql = request.json.get("sql")

    new_query = Query(
        databaseId=database_id,
        title=title,
        sql=sql,
    )

    g.session.add(new_query)
    g.session.commit()

    response = {
        "id": new_query.id,
        "databaseId": new_query.databaseId,
        "title": new_query.title,
        "sql": new_query.sql,
    }

    return jsonify(response)


@api.route("/query/<query_id>", methods=["GET", "PUT"])
@user_middleware
def handle_query_by_id(query_id):
    """
    Run or Update a query based on the request method
    """
    query = g.session.query(Query).filter_by(id=query_id).first()
    if not query:
        return jsonify({"error": "Query not found"}), 404

    # Get databaseId from query
    databaseId = query.databaseId

    if request.method == "PUT":
        query.title = request.json.get("title")
        query.sql = request.json.get("sql")
        g.session.commit()

    response = {
        "databaseId": databaseId,
        "title": query.title,
        "sql": query.sql,
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
        datalake = database.create_datalake()
        rows, count = datalake.query(query.sql, role="users")
        return jsonify({"rows": rows, "count": count})

    if query.exception:
        return jsonify({"message": query.exception}), 500
    return jsonify({"rows": query.rows, "count": query.count})
