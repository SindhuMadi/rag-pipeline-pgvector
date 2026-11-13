import os

import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

from chunking import chunk_text

CHUNK_SIZE = 500
CHUNK_OVERLAP = 75

DB = dict(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", "5432")),
    user="postgres",
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    dbname="postgres",
)

SEARCH_SQL = """
SELECT d.source_path, c.content, c.embedding <=> %s AS distance
FROM chunks c
JOIN documents d ON d.id = c.document_id
WHERE c.chunk_size = %s AND c.chunk_overlap = %s AND d.topic <> ALL(%s::text[])
ORDER BY distance
LIMIT %s
"""


def retrieve(conn, model, question, size, overlap, exclude_topics = [], k=3):
    # TODO 1: embed the question (a single string, not a list)
    exclude_topics = exclude_topics or []
    q_emb = model.encode(question)
    
        
    # TODO 2: run SEARCH_SQL with the right four parameters, in the right order
    rows = conn.execute(
            SEARCH_SQL,(q_emb, size, overlap, exclude_topics,  k)).fetchall()
    
    # TODO 3: return the rows
    
    return rows


conn = psycopg.connect(**DB, autocommit=True)
register_vector(conn)

model = SentenceTransformer("all-MiniLM-L6-v2")
question = "Data lake vs delta lake which is effective?"

results = retrieve(conn, model, question, size=500, overlap = 75, exclude_topics=["interviews","slides"])

print(results)