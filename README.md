# RAG Pipeline with pgvector

A retrieval-augmented generation (RAG) pipeline built on Postgres + pgvector:
ingest documents, chunk, embed, store vectors, retrieve, and answer with an LLM.

**Status:** work in progress

## Stack
- Python
- Postgres with pgvector (via Docker)
- sentence-transformers for embeddings

## Learning log
- Day 1: environment setup, repo structure
    1. Check if Docker and Python are working using below commands
        docker --version
        python --version

        Install them if not already installed
        Create your project folder with data/docker-compose.yml, data/README.md, data/requirements.txt and src folders

    2.  Open your terminal.
        Navigate to the directory containing your docker-compose.yml file.
        Execute:
            docker compose up -d

            docker ps  #To check if rag-db is running.

    3. Enable pgvector and test it

        docker exec -it rag-db psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
        docker exec -it rag-db psql -U postgres -c "SELECT '[1,2,3]'::vector <=> '[1,2,4]'::vector;"

            If above query returns a small number back, it means vector math is working.
        

    
