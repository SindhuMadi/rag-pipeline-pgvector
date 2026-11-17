import json

import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

from src.retrieve import DB, retrieve

SIZE = 500
OVERLAP = 75
K = 3
EXCLUDE = ["interviews"]


def main():
    with open("eval/questions.json") as f:
        questions = json.load(f)

    model = SentenceTransformer("all-MiniLM-L6-v2")
    hits = 0

    with psycopg.connect(**DB, autocommit=True) as conn:
        register_vector(conn)
        for i, q in enumerate(questions, start=1):
            rows = retrieve(
                conn, model, q["question"], SIZE, OVERLAP,
                exclude_topics=EXCLUDE, k=K,
            )
            # rows look like (source_path, content, distance)
            
            retrieved_paths = [row[0] for row in rows]
            if any(path in q["expected_sources"] for path in retrieved_paths):
                hits+=1
                print(f"{i} is a hit, retrieved path: {retrieved_paths}")
            else:
                print(f"{i} is a miss, retrieved paths: {retrieved_paths}, expected_sources: {q['expected_sources']}")
            
            # TODO 1: build a list of the source paths in rows
            # TODO 2: decide if this is a hit: does ANY retrieved path
            #         appear in q["expected_sources"]?
            # TODO 3: add 1 to hits when it is a hit
            # TODO 4: print one line per question: its number, HIT or MISS,
            #         and the retrieved paths. For a MISS, also print
            #         q["expected_sources"] so you can compare them.
    
    print(f"Hits: {hits}, Number of questions: {len(questions)}, Hit rate: {hits/len(questions):.0%}")
    # TODO 5: print hits, number of questions, and hit rate as a percentage


if __name__ == "__main__":
    main()