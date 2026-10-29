import os

import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

DB = dict(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", "5432")),
    user="postgres",
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    dbname="postgres",
)

# Small, fast model that outputs 384-dimensional vectors
model = SentenceTransformer("all-MiniLM-L6-v2")

sentences = [
    "Boil the noodles for ten minutes and drain them.",
    "The stock market fell sharply on Monday.",
    "Our pipeline loads customer data into the warehouse every night.",
    "Puppies need plenty of exercise and regular vet visits.",
    "Airflow schedules tasks and tracks dependencies between them.",
    "Interest rates affect how much a mortgage costs.",
]

with psycopg.connect(**DB, autocommit=True) as conn:
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)

    conn.execute("DROP TABLE IF EXISTS demo_docs")
    conn.execute(
        "CREATE TABLE demo_docs ("
        "id serial PRIMARY KEY, content text, embedding vector(384))"
    )

    embeddings = model.encode(sentences)
    print("Embedding shape:", embeddings.shape)

    for text, emb in zip(sentences, embeddings):
        conn.execute(
            "INSERT INTO demo_docs (content, embedding) VALUES (%s, %s)",
            (text, emb),
        )

    query = "How do I cook pasta?"
    q_emb = model.encode(query)

    rows = conn.execute(
        "SELECT content, embedding <=> %s AS distance "
        "FROM demo_docs ORDER BY distance LIMIT 3",
        (q_emb,),
    ).fetchall()

    print(f"\nQuery: {query}")
    for content, distance in rows:
        print(f"  {distance:.3f}  {content}")