import click
from back.models import ConversationMessage, Query
from back.session import session
from chat.datachat import save_query
from chat.sql_utils import extract_sql
from chat.utils import generate_embedding
from flask import Blueprint
from sqlalchemy import and_

chat_cli = Blueprint("chat_cli", __name__)


def save_query_backlog():
    """Get all messages that have not been saved to the database yet"""
    messages = session.query(ConversationMessage)
    total = messages.count()
    click.echo(f"Found {total} messages to process.")
    # progress bar
    with click.progressbar(messages, length=total) as bar:
        for message in bar:
            sql_queries = extract_sql(message.content)
            for sql_query in sql_queries:
                save_query(sql_query, message)
            session.commit()


@chat_cli.cli.command("fetch-query-embedding")
def fetch_query_embedding():
    # Get all queries that don't have embedding yet
    queries = session.query(Query).filter(
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
        session.commit()
    click.echo("Query embeddings have been processed.")


@chat_cli.cli.command("save-query-backlog")
def save_query_backlog_command():
    """CLI command to run save_query_backlog."""
    save_query_backlog()
    click.echo("Query backlog has been processed.")
