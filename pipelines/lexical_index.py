"""SQLite FTS helpers for lexical retrieval."""

from __future__ import annotations

from pathlib import Path
import sqlite3


# ALLOW-list, deliberately, not a deny-list.
#
# `tokenize_query` emits an FTS5 MATCH *expression*, so every character that
# survives is parsed as query syntax. This was a deny-list until 2026-08-01 and
# it leaked in both directions:
#
#   crash    `% & ; < = > \`` reached MATCH and raised
#            `sqlite3.OperationalError: fts5: syntax error near "%"` straight
#            out of `search_index` on inputs users type constantly
#            ("100% test coverage", "A&B testing", "field<>value").
#   silent   `+` survived, so `trigger+recursion` became the expression
#            `trigger+recursion*`. Per the FTS5 grammar `+` CONCATENATES two
#            phrases, so the documented OR became an adjacency requirement and
#            the caller got zero rows with no error at all.
#
# A deny-list has to enumerate every operator SQLite has now and every one it
# adds later; the silent arm above shows a miss need not even announce itself.
# The allow-list is closed by construction: anything not listed becomes
# whitespace, so a new operator character is inert on the day it ships.
#
# What is kept is exactly the FTS5 "bareword" alphabet
# (https://sqlite.org/fts5.html, § Full-text Query Syntax) minus control
# codepoint 26: ASCII alphanumerics, the underscore, and every codepoint above
# 127. Non-ASCII is kept so accented and CJK queries still tokenize ("café"),
# and it is safe — `café*` and `🎉*` are legal barewords.
#
# `-` and `/` are NOT kept: both are illegal in a bareword, and splitting on
# them is load-bearing, since skill ids ("apex/trigger-recursion") are routinely
# pasted in as queries and must reach the index as separate prefix terms.
def _is_fts5_bareword_char(ch: str) -> bool:
    """True for characters FTS5 accepts inside an unquoted bareword.

    Written as an explicit predicate rather than a regex character class on
    purpose: the character-class form is a footgun here. Spelling the
    non-ASCII arm as an underscore followed by a dash and an upper codepoint
    reads like "alnum, underscore, and non-ASCII", but in a character class
    that is a RANGE starting at underscore (0x5F), which silently re-admits
    `{ | } ~` and reintroduces exactly the class of leak this replaced.
    """
    return (ch.isalnum() and ch.isascii()) or ch == "_" or ord(ch) > 127


def tokenize_query(query: str) -> str:
    cleaned = "".join(ch if _is_fts5_bareword_char(ch) else " " for ch in query)
    tokens = [token.lower() for token in cleaned.split() if token]
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


def search_index(
    path: Path,
    query: str,
    domain: str | None,
    limit: int,
    *,
    skills_only: bool = False,
) -> list[dict]:
    """Return the top ``limit`` chunks for ``query``, best BM25 rank first.

    ``skills_only`` restricts the result to chunks that belong to a skill
    package. The index also holds ``knowledge/`` imports and official-source
    chunks, which carry no ``skill_id``.

    Why that switch exists: ``limit`` is a budget, and a chunk with no
    ``skill_id`` can never be aggregated into a skill, so on a query whose
    vocabulary the knowledge corpus happens to share it spends the budget
    without ever being able to answer "which skill covers this". Measured on
    the 154-query held-out set, non-skill chunks take 7.5% of a 30-chunk
    window overall but up to 24 of 30 slots on the queries that returned no
    coverage at all — "share data between two lightning web components" lost
    24, "set up single sign on" 20. Callers that decide coverage should ask
    for a skill-scoped window; callers that display chunks or collect
    official sources want the unfiltered one.
    """
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
        if skills_only:
            # skill_id is '' (not NULL) for knowledge/official-source chunks.
            sql += " AND skill_id IS NOT NULL AND skill_id != ''"
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)
        rows = connection.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()
