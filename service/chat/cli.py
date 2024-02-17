import json

import click
from back.models import Conversation, Query
from back.session import Session
from chat.memory_utils import find_closest_embeddings, generate_embedding
from flask import Blueprint, g
from sqlalchemy import and_

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


@chat_cli.cli.command("export-conversations")
def export_conversations():
    session = Session()
    conversations = session.query(Conversation).all()

    export_conversations = []
    for conversation in conversations:
        export_messages = []
        # If less than 2 messages, skip
        if len(conversation.messages) <= 2:
            continue
        for message in conversation.messages:
            export_message = message.to_autochat_message().to_openai_dict()
            export_messages.append(export_message)
        export_conversations.append(
            {
                "messages": export_messages,
            }
        )

    with open("conversations_export.jsonl", "w") as f:
        for conversation in export_conversations:
            f.write(json.dumps(conversation) + "\n")
    click.echo("Conversations have been exported to 'conversations_export.jsonl'.")
