from functools import wraps

from back.datalake import DatalakeFactory, SizeLimitError
from back.models import Database, Query
from flask import Blueprint, g, jsonify, request
from middleware import user_middleware
from sqlalchemy.exc import SQLAlchemyError

api = Blueprint("ai_api", __name__)


def database_middleware(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        database_id = request.json.get("databaseId")
        database = g.session.query(Database).filter_by(id=database_id).first()
        # Add a datalake object to the request
        datalake = DatalakeFactory.create(
            database.engine,
            **database.details,
        )
        g.datalake = datalake

        return f(*args, **kwargs)

    return decorated_function


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
        result = g.datalake.query(sql_query)
        count = len(result)
        return jsonify({"rows": result, "count": count})
    except (SQLAlchemyError, SizeLimitError) as e:
        return jsonify({"message": str(e)}), 500


@api.route("/query", methods=["POST"])
@user_middleware
def create_query():
    database_id = request.json.get("databaseId")
    visualisationParams = request.json.get("visualisationParams")
    query = request.json.get("query")
    validatedSQL = request.json.get("sql")

    new_query = Query(
        databaseId=database_id,
        query=query,
        validatedSQL=validatedSQL,
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
        "sql": new_query.validatedSQL,
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
        query.validatedSQL = request.json.get("sql")
        g.session.commit()

    # sql is validatedSQL or first result from choices
    sql = query.validatedSQL or query.result["choices"][0]["text"].strip()

    response = {
        "databaseId": databaseId,
        "visualisationParams": query.visualisationParams,
        "query": query.query,
        "sql": sql,
        "validatedSQL": query.validatedSQL,
    }

    if request.method == "PUT":
        response["visualisationParams"] = updated_visualisationParams

    return jsonify(response)
