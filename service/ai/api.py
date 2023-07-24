import json
from functools import wraps

from back.datalake import DatalakeFactory
from back.models import Database, Query
from back.session import session
from flask import Blueprint, g, jsonify, request
from middleware import user_middleware

api = Blueprint("ai_api", __name__)


def database_middleware(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        databaseId = request.json.get("databaseId")
        database = session.query(Database).filter_by(id=databaseId).first()
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

    result = g.datalake.query(sql_query)
    count = len(result)
    return jsonify({"rows": result[:50], "count": count})


@api.route("/query/<int:query_id>", methods=["GET"])
@user_middleware
def run_query_by_id(query_id):
    """
    Run a query against the database
    Return eg. {"rows":[{"count":"607"}],"count":1}
    """
    query = session.query(Query).filter_by(id=query_id).first()
    if not query:
        return jsonify({"error": "Query not found"}), 404

    # Get databaseId from query
    databaseId = query.databaseId
    database = session.query(Database).filter_by(id=databaseId).first()
    # Add a datalake object to the request
    datalake = DatalakeFactory.create(
        database.engine,
        **database.details,
    )

    #
    # sql is validatedSQL or first result from choices
    sql = query.validatedSQL or query.result["choices"][0]["text"].strip()
    result = datalake.query(sql)

    count = len(result)
    return jsonify(
        {
            "rows": result[:50],
            "count": count,
            "databaseId": databaseId,
            "query": query.query,
            "sql": sql,
            "validatedSQL": query.validatedSQL,
        }
    )
