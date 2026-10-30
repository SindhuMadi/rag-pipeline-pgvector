import hashlib
import os
import re
from pathlib import Path

import psycopg
from pypdf import PdfReader

RAW_DIR = Path("data/raw")

DB = dict(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", "5432")),
    user="postgres",
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    dbname="postgres",
)


def read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


READERS = {".pdf": read_pdf, ".txt": read_text, ".md": read_text}


def clean(text: str) -> str:
    text = text.replace("\x00", "")           # Postgres rejects null bytes
    text = re.sub(r"[ \t]+", " ", text)       # collapse spaces/tabs
    text = re.sub(r"\n{3,}", "\n\n", text)    # collapse blank lines
    return text.strip()


def main():
    files = sorted(p for p in RAW_DIR.rglob("*") if p.suffix.lower() in READERS)
    print(f"Found {len(files)} supported files in {RAW_DIR}")

    with psycopg.connect(**DB, autocommit=True) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id serial PRIMARY KEY,
                source_path text UNIQUE NOT NULL,
                content text NOT NULL,
                content_hash text NOT NULL,
                ingested_at timestamptz DEFAULT now()
            )
            """
        )

        loaded = skipped = failed = 0
        for path in files:
            try:
                text = clean(READERS[path.suffix.lower()](path))
                if not text:
                    print(f"  empty text, skipping: {path.name}")
                    skipped += 1
                    continue
                digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
                conn.execute(
                    """
                    INSERT INTO documents (source_path, content, content_hash)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (source_path) DO UPDATE
                      SET content = EXCLUDED.content,
                          content_hash = EXCLUDED.content_hash,
                          ingested_at = now()
                      WHERE documents.content_hash <> EXCLUDED.content_hash
                    """,
                    (str(path), text, digest),
                )
                loaded += 1
            except Exception as exc:
                print(f"  FAILED {path.name}: {exc}")
                failed += 1

        print(f"Done. processed={loaded} skipped={skipped} failed={failed}")


if __name__ == "__main__":
    main()