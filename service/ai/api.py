from flask import Blueprint, g, jsonify, request

from back.models import Query
from middleware import database_middleware, user_middleware

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
        rows, count = g.datalake.query(sql_query)
        return jsonify({"rows": rows, "count": count})
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@api.route("/query", methods=["POST"])
@user_middleware
def create_query():
    database_id = request.json.get("databaseId")
    visualisationParams = request.json.get("visualisationParams")
    query = request.json.get("query")
    sql = request.json.get("sql")

    new_query = Query(
        databaseId=database_id,
        query=query,
        sql=sql,
    )
    if visualisationParams:
        new_query.visualisationParams = visualisationParams

    g.session.add(new_query)
    g.session.commit()

    response = {
        "id": new_query.id,
        "databaseId": new_query.databaseId,
        "visualisationParams": new_query.visualisationParams,
        "query": new_query.query,
        "sql": new_query.sql,
    }

    return jsonify(response)


@api.route("/query/<int:query_id>", methods=["GET", "PUT"])
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
        updated_visualisationParams = request.json.get("visualisationParams")
        query.visualisationParams = updated_visualisationParams
        query.query = request.json.get("query")
        query.sql = request.json.get("sql")
        g.session.commit()

    response = {
        "databaseId": databaseId,
        "visualisationParams": query.visualisationParams,
        "query": query.query,
        "sql": query.sql,
    }

    if request.method == "PUT":
        response["visualisationParams"] = updated_visualisationParams

    return jsonify(response)
