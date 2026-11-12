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

CREATE_CHUNKS_SQL = """
CREATE TABLE IF NOT EXISTS chunks (
    id serial PRIMARY KEY,
    document_id integer NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index integer NOT NULL,
    content text NOT NULL,
    embedding vector(384) NOT NULL,
    chunk_size integer NOT NULL,
    chunk_overlap integer NOT NULL,
    UNIQUE (document_id, chunk_index, chunk_size, chunk_overlap)
)
"""

INSERT_SQL = """
INSERT INTO chunks
    (document_id, chunk_index, content, embedding, chunk_size, chunk_overlap)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (document_id, chunk_index, chunk_size, chunk_overlap)
DO UPDATE SET content = EXCLUDED.content, embedding = EXCLUDED.embedding
"""


def main():
    model = SentenceTransformer("all-MiniLM-L6-v2")

    with psycopg.connect(**DB, autocommit=True) as conn:
        register_vector(conn)
        conn.execute(CREATE_CHUNKS_SQL)

        docs = conn.execute(
            "SELECT id, content FROM documents ORDER BY id"
        ).fetchall()

        total_chunks = 0
        for doc_id, content in docs:
            chunks = chunk_text(content, CHUNK_SIZE, CHUNK_OVERLAP)
            print(doc_id, len(content), len(chunks))
            #print(repr(chunks[0][:200]))
            
            if len(chunks)==0:
                continue
            
            embeddings = model.encode(chunks)
            print("Embedding shape:", embeddings.shape)
            
            

            for chunk_index, (text, emb) in enumerate(zip(chunks, embeddings)):
                conn.execute(
                    INSERT_SQL,
                    (doc_id, chunk_index, text, emb, CHUNK_SIZE, CHUNK_OVERLAP)
                )
            total_chunks = total_chunks+len(chunks)
            
            # TODO 1: chunk this document with CHUNK_SIZE and CHUNK_OVERLAP
            # TODO 2: if there are no chunks, continue to the next document
            # TODO 3: embed ALL of this document's chunks in ONE model.encode
            #         call (look up its batch_size parameter)
            # TODO 4: insert each chunk using INSERT_SQL
            #         (hint: enumerate gives you chunk_index)
            # TODO 5: add to total_chunks
            pass

        print(f"Summary :Total documents: {len(docs)}, Total Chunks: {total_chunks}")
        # TODO 6: print a summary: documents processed, total chunks,
        #         average chunk length (query the table, or track it)


if __name__ == "__main__":
    main()