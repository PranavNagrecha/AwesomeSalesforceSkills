"""SQLite FTS helpers for lexical retrieval."""

from __future__ import annotations

from pathlib import Path
import sqlite3


_FTS5_SPECIAL = str.maketrans({c: " " for c in "'\".,$@#!?()[]{}|\\^~*:-"})


def tokenize_query(query: str) -> str:
    cleaned = query.replace("/", " ").translate(_FTS5_SPECIAL)
    tokens = [token.strip().lower() for token in cleaned.split() if token.strip()]
    if not tokens:
        return ""
    return " OR ".join(f"{token}*" for token in tokens)


def build_lexical_index(path: Path, chunks: list[dict], source_hash: str) -> None:
    if path.exists():
        existing_hash = read_source_hash(path)
        if existing_hash == source_hash:
            return
        path.unlink()

    connection = sqlite3.connect(path)
    try:
        connection.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        connection.execute(
            """
            CREATE VIRTUAL TABLE chunks_fts USING fts5(
                chunk_id UNINDEXED,
                source_id UNINDEXED,
                skill_id UNINDEXED,
                domain UNINDEXED,
                chunk_kind UNINDEXED,
                source_trust UNINDEXED,
                path UNINDEXED,
                title,
                tags,
                text
            )
            """
        )
        for chunk in chunks:
            connection.execute(
                """
                INSERT INTO chunks_fts
                (chunk_id, source_id, skill_id, domain, chunk_kind, source_trust, path, title, tags, text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk["id"],
                    chunk["source_id"],
                    chunk.get("skill_id"),
                    chunk.get("domain"),
                    chunk["chunk_kind"],
                    chunk["source_trust"],
                    chunk["path"],
                    chunk["title"],
                    " ".join(chunk.get("tags", [])),
                    chunk["text"],
                ),
            )
        connection.executemany(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            [
                ("source_hash", source_hash),
                ("chunk_count", str(len(chunks))),
            ],
        )
        connection.commit()
    finally:
        connection.close()


def read_source_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    connection = sqlite3.connect(path)
    try:
        row = connection.execute("SELECT value FROM meta WHERE key = 'source_hash'").fetchone()
        return row[0] if row else None
    except sqlite3.DatabaseError:
        return None
    finally:
        connection.close()


def search_index(path: Path, query: str, domain: str | None, limit: int) -> list[dict]:
    if not path.exists():
        return []
    fts_query = tokenize_query(query)
    if not fts_query:
        return []

    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        sql = """
            SELECT chunk_id, source_id, skill_id, domain, chunk_kind, source_trust, path, title, text,
                   bm25(chunks_fts) AS rank
            FROM chunks_fts
            WHERE chunks_fts MATCH ?
        """
        params: list = [fts_query]
        if domain:
            sql += " AND domain = ?"
            params.append(domain)
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)
        rows = connection.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()
