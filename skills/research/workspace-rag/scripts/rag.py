#!/usr/bin/env python3
"""
workspace-rag: local semantic search over Hermes workspace notes.

Storage: SQLite + sqlite-vec (vec0 virtual table), embeddings via local
Ollama (nomic-embed-text, 768-dim). No network calls besides localhost
Ollama. No third-party HTTP client — stdlib urllib only.

Commands:
    rag.py index <path>...          # chunk + embed + store (default paths if none given)
    rag.py query "<question>" [-k 5]
    rag.py status
"""
import argparse
import json
import os
import sqlite3
import struct
import sys
import time
import urllib.error
import urllib.request

import sqlite_vec

OLLAMA_URL = "http://localhost:11434/api/embeddings"
MODEL = "nomic-embed-text"
EMBED_DIM = 768
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

DB_PATH = "/Users/josephhan/mac/Hermes/state/workspace-rag.db"
DEFAULT_PATHS = [
    "/Users/josephhan/mac/Hermes/memories",
    "/Users/josephhan/mac/Hermes/IMPROVEMENTS.md",
    "/Users/josephhan/mac/Hermes/WORKSPACE.md",
]
INDEXABLE_EXTENSIONS = (".md", ".txt")


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def embed(text):
    """Call local Ollama for a single embedding. Raises RuntimeError on failure."""
    payload = json.dumps({"model": MODEL, "prompt": text}).encode("utf-8")
    request = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read())
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"cannot reach Ollama at {OLLAMA_URL} ({exc}). "
            "Is Ollama running? Try: ollama serve"
        ) from exc
    embedding = body.get("embedding")
    if not embedding:
        raise RuntimeError(f"Ollama returned no embedding for model '{MODEL}'")
    return embedding


def normalize(vector):
    """L2-normalize so vec0's default L2 distance behaves like cosine distance."""
    norm = sum(component * component for component in vector) ** 0.5
    if norm == 0:
        return vector
    return [component / norm for component in vector]


def serialize_f32(vector):
    return struct.pack(f"{len(vector)}f", *vector)


def open_db():
    db_dir = os.path.dirname(DB_PATH)
    os.makedirs(db_dir, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.execute("pragma journal_mode=WAL")
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    db.execute(
        f"create virtual table if not exists vec_chunks using vec0(embedding float[{EMBED_DIM}])"
    )
    db.execute(
        """
        create table if not exists chunk_meta (
            rowid integer primary key,
            path text not null,
            chunk_text text not null,
            mtime real not null
        )
        """
    )
    db.execute(
        "create index if not exists idx_chunk_meta_path on chunk_meta(path)"
    )
    return db


def iter_source_files(paths):
    """Yield absolute file paths under the given files/directories, filtered by extension."""
    for raw_path in paths:
        path = os.path.abspath(raw_path)
        if os.path.isfile(path):
            if path.endswith(INDEXABLE_EXTENSIONS):
                yield path
            continue
        if not os.path.isdir(path):
            print(f"warning: path not found, skipping: {path}", file=sys.stderr)
            continue
        for root, _dirs, files in os.walk(path):
            for name in files:
                if name.endswith(INDEXABLE_EXTENSIONS):
                    yield os.path.join(root, name)


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into ~chunk_size chunks, preferring paragraph boundaries."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    chunks = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= chunk_size:
            current = paragraph
        else:
            # Paragraph itself exceeds chunk_size: hard-split with overlap.
            for start in range(0, len(paragraph), chunk_size - overlap):
                chunks.append(paragraph[start:start + chunk_size])
            current = ""
    if current:
        chunks.append(current)
    return chunks


def existing_mtime(db, path):
    row = db.execute(
        "select max(mtime) from chunk_meta where path = ?", (path,)
    ).fetchone()
    return row[0] if row else None


def delete_file_chunks(db, path):
    rowids = [
        r[0] for r in db.execute(
            "select rowid from chunk_meta where path = ?", (path,)
        ).fetchall()
    ]
    for rowid in rowids:
        db.execute("delete from vec_chunks where rowid = ?", (rowid,))
    db.execute("delete from chunk_meta where path = ?", (path,))


def index_file(db, path):
    mtime = os.path.getmtime(path)
    previous_mtime = existing_mtime(db, path)
    if previous_mtime is not None and previous_mtime >= mtime:
        return 0

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    except OSError as exc:
        print(f"warning: cannot read {path}: {exc}", file=sys.stderr)
        return 0

    chunks = chunk_text(text)
    if not chunks:
        return 0

    delete_file_chunks(db, path)

    inserted = 0
    for chunk in chunks:
        try:
            vector = normalize(embed(chunk))
        except RuntimeError as exc:
            fail(str(exc))
        cursor = db.execute(
            "insert into chunk_meta(path, chunk_text, mtime) values (?, ?, ?)",
            (path, chunk, mtime),
        )
        rowid = cursor.lastrowid
        db.execute(
            "insert into vec_chunks(rowid, embedding) values (?, ?)",
            (rowid, serialize_f32(vector)),
        )
        inserted += 1
    return inserted


def command_index(args):
    paths = args.paths if args.paths else DEFAULT_PATHS
    for raw_path in paths:
        if not os.path.exists(raw_path):
            print(f"warning: path does not exist: {raw_path}", file=sys.stderr)

    db = open_db()
    files = list(iter_source_files(paths))
    if not files:
        fail("no indexable .md/.txt files found under the given paths")

    total_chunks = 0
    total_files_updated = 0
    start = time.time()
    for path in files:
        inserted = index_file(db, path)
        if inserted:
            total_files_updated += 1
            total_chunks += inserted
            print(f"indexed {inserted:3d} chunks  {path}")
        db.commit()
    elapsed = time.time() - start

    print(
        f"\ndone: {total_files_updated}/{len(files)} files (re)indexed, "
        f"{total_chunks} chunks embedded in {elapsed:.1f}s"
    )
    db.close()


def command_query(args):
    if not args.question.strip():
        fail("query text must not be empty")
    if not os.path.exists(DB_PATH):
        fail(f"no index found at {DB_PATH} — run 'rag.py index' first")

    db = open_db()
    try:
        query_vector = normalize(embed(args.question))
    except RuntimeError as exc:
        fail(str(exc))

    rows = db.execute(
        """
        select chunk_meta.path, chunk_meta.chunk_text, knn.distance
        from (
            select rowid, distance from vec_chunks
            where embedding match ? and k = ?
        ) as knn
        join chunk_meta on chunk_meta.rowid = knn.rowid
        order by knn.distance
        """,
        (serialize_f32(query_vector), args.k),
    ).fetchall()
    db.close()

    if not rows:
        print("no results")
        return

    for path, chunk, distance in rows:
        snippet = " ".join(chunk.split())[:200]
        print(f"[{distance:.4f}] {path}")
        print(f"    {snippet}")


def command_status(args):
    if not os.path.exists(DB_PATH):
        print(f"no index found at {DB_PATH}")
        return

    db = open_db()
    chunk_count = db.execute("select count(*) from chunk_meta").fetchone()[0]
    file_count = db.execute(
        "select count(distinct path) from chunk_meta"
    ).fetchone()[0]
    db.close()

    db_size = os.path.getsize(DB_PATH)
    print(f"db path:   {DB_PATH}")
    print(f"db size:   {db_size / 1024:.1f} KB")
    print(f"files:     {file_count}")
    print(f"chunks:    {chunk_count}")


def build_parser():
    parser = argparse.ArgumentParser(prog="rag.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="chunk, embed, and store files")
    index_parser.add_argument("paths", nargs="*", help="files or directories to index")
    index_parser.set_defaults(func=command_index)

    query_parser = subparsers.add_parser("query", help="semantic search over the index")
    query_parser.add_argument("question", help="natural-language question")
    query_parser.add_argument("-k", type=int, default=5, help="number of results (default 5)")
    query_parser.set_defaults(func=command_query)

    status_parser = subparsers.add_parser("status", help="show index stats")
    status_parser.set_defaults(func=command_status)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
