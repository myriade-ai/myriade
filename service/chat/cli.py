
import click
from flask import Blueprint, g
from sqlalchemy import and_

from back.models import Query
from chat.memory_utils import find_closest_embeddings, generate_embedding

chat_cli = Blueprint("chat_cli", __name__)


@chat_cli.cli.command("fetch-query-embedding")
def fetch_query_embedding():
    # Get all queries that don't have embedding yet
    queries = g.session.query(Query).filter(
        and_(
            Query.databaseId == 131,
            Query.query != "???",
            Query.embedding == None,
            Query.sql != None,  # Add this condition
        )
    )
    total = queries.count()
    click.echo(f"Found {total} queries to process.")
    # progress bar
    with click.progressbar(queries, length=total) as bar:
        for query in bar:
            query.embedding = generate_embedding(query.query)
        g.session.commit()
    click.echo("Query embeddings have been processed.")


@chat_cli.cli.command("search-query")
@click.argument("query", type=str)
def search_query(query):
    # Test of memory search
    queries = find_closest_embeddings(g.session, query, top_n=3)
    # queries = Query.memory_search(session, "select * from users")
    for query in queries:
        print(query.query)
