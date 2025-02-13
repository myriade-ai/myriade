import openai

from back.models import Query


def generate_embedding(string):
    response = openai.Embedding.create(input=string, model="text-embedding-ada-002")
    # len => 1536
    embedding = response["data"][0]["embedding"]
    return embedding


def find_closest_embeddings(session, query, top_n=5):
    embedding = generate_embedding(query)
    results = (
        session.query(Query.query)
        # With embedding not null
        .filter(Query.embedding != None)
        # TODO: Should be at least 80% similar
        # .filter(func.similarity(func.array(Query.embedding), embedding) >= 0.8)
        # .filter(Query.embedding.op("<->")(func.array(embedding)) <= 1)
        .order_by(Query.embedding.op("<->")(embedding))
        .limit(top_n)
        .all()
    )
    return [r[0] for r in results]
