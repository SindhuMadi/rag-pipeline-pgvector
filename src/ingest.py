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

MENU_LINE = re.compile(r"[A-Za-z][A-Za-z0-9 &/,'-]{0,40}\s\+")



def join_wrapped_lines(text: str) -> str:
    # "pro-\ncessing" -> "processing" (word split by a hyphen at line end)
    text = re.sub(r"(?<=[a-z])-\n(?=[a-z])", "", text)
    # a single newline inside a paragraph becomes a space;
    # blank-line paragraph breaks (\n\n) are left alone
    text = re.sub(r"(?<![.!?:\n])\n(?!\n)", " ", text)
    return text

def clean(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)    # trim spaces around newlines
    text = join_wrapped_lines(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def is_hidden(path: Path) -> bool:
    parts = path.relative_to(RAW_DIR).parts
    return any(part.startswith(".") for part in parts)


def main():
    
    #Skip hidden files
    candidates = [
                p for p in RAW_DIR.rglob("*")
                if p.is_file() and p.suffix.lower() in READERS
                ]
    files = sorted(p for p in candidates if not is_hidden(p))
    print(
    f"Found {len(files)} supported files in {RAW_DIR} "
    f"({len(candidates) - len(files)} skipped as hidden)"
    )
    
    

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
                
                dup = conn.execute(
                        "SELECT source_path FROM documents "
                        "WHERE content_hash = %s AND source_path <> %s LIMIT 1",
                        (digest, str(path)),
                        ).fetchone()
                if dup:
                    print(f"  duplicate of {dup[0]}, skipping: {path.name}")
                    skipped += 1
                    continue
                
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