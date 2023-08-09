import json

import click
from back.models import ConversationMessage, Query
from chat.datachat import save_query
from chat.memory_utils import find_closest_embeddings, generate_embedding
from chat.sql_utils import extract_sql
from flask import Blueprint, g
from sqlalchemy import and_

chat_cli = Blueprint("chat_cli", __name__)


def save_query_backlog():
    """Get all messages that have not been saved to the database yet"""
    messages = g.session.query(ConversationMessage)
    total = messages.count()
    click.echo(f"Found {total} messages to process.")
    # progress bar
    with click.progressbar(messages, length=total) as bar:
        for message in bar:
            try:
                sql_queries = extract_sql(message.content)

                for sql_query in sql_queries:
                    save_query(sql_query, message)

            except Exception as e:
                click.echo(f"Error while processing message {message.id}: {e}")
                print(e)

            # Get if functionCall is SQL_QUERY and get arguments.query
            if message.functionCall and message.functionCall["name"] == "SQL_QUERY":
                try:
                    arguments = message.functionCall["arguments"]
                    if isinstance(arguments, str):
                        arguments = json.loads(arguments)
                    sql_query = arguments["query"]
                    save_query(sql_query, message)
                except Exception as e:
                    click.echo(f"Error while processing  {message.id}: {e}")
                    print(e)


@chat_cli.cli.command("fetch-query-embedding")
def fetch_query_embedding():
    # Get all queries that don't have embedding yet
    queries = g.session.query(Query).filter(
        and_(
            Query.databaseId == 131,
            Query.query != "???",
            Query.embedding == None,
            Query.validatedSQL != None,  # Add this condition
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


@chat_cli.cli.command("save-query-backlog")
def save_query_backlog_command():
    """CLI command to run save_query_backlog."""
    save_query_backlog()
    click.echo("Query backlog has been processed.")


@chat_cli.cli.command("search-query")
@click.argument("query", type=str)
def search_query(query):
    # Test of memory search
    queries = find_closest_embeddings(g.session, query, top_n=3)
    # queries = Query.memory_search(session, "select * from users")
    for query in queries:
        print(query.query)
