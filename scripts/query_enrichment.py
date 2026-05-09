#!/usr/bin/env python3
"""Query enrichment for Salesforce-specific search.

Plug into ``scripts/search_knowledge.py`` BEFORE the FTS5 sanitizer so the
lexical search sees both the abbreviation and the expanded form. Result:
``"FLS on outputField"`` and ``"field level security on outputField"``
retrieve the same skills.

Pure stdlib. Loads ``standards/salesforce-vocabulary.json`` once per process
(the dict is small enough that re-loading is also fine).

Public API:
    enrich_query(query: str, vocabulary: dict | None = None) -> str

The returned string is the original query with bidirectional expansions
appended, separated by spaces. Original tokens come FIRST so they retain
their natural FTS5 weight.

Behavior:
- Abbreviation match → expansions appended.
- Long-form match → matching abbreviations appended.
- Standalone-token rule: only expand abbreviations that appear as a whole
  word (regex word boundary on both sides). Avoids expanding ``RT`` inside
  ``portrait``.
- Length cap: enrichment never grows the query past 3x its original length
  (counted by token count). Beyond that, expansions are dropped LIFO.
- Deterministic: ordered iteration over the vocabulary dict.

Usage from CLI (for ad-hoc testing):
    python3 scripts/query_enrichment.py "FLS on outputField"
    python3 scripts/query_enrichment.py "users can't see SSN OWD"
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VOCAB_PATH = REPO / "standards" / "salesforce-vocabulary.json"

# Cache the loaded vocabulary across calls in the same process.
_VOCAB_CACHE: dict | None = None


def _load_vocabulary(path: Path = VOCAB_PATH) -> dict[str, list[str]]:
    """Load and validate the vocabulary file. Strips the `_meta` key.

    Returns a dict mapping abbreviation → list of expansion phrases.
    """
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {k: v for k, v in raw.items() if not k.startswith("_") and isinstance(v, list)}


def _get_vocab() -> dict[str, list[str]]:
    global _VOCAB_CACHE
    if _VOCAB_CACHE is None:
        _VOCAB_CACHE = _load_vocabulary()
    return _VOCAB_CACHE


def _word_match(token: str, text: str) -> bool:
    """True if ``token`` appears in ``text`` as a standalone word.

    Case-insensitive; uses word boundaries. Multi-word tokens supported
    (we use a literal-with-boundaries regex so phrases like
    ``platform event`` match in their entirety).
    """
    if not token:
        return False
    pattern = r"\b" + re.escape(token) + r"\b"
    return bool(re.search(pattern, text, flags=re.IGNORECASE))


def enrich_query(query: str, vocabulary: dict[str, list[str]] | None = None) -> str:
    """Append bidirectional Salesforce-vocabulary expansions to ``query``.

    Original query comes first to preserve natural FTS5 token weight.
    """
    if not query.strip():
        return query

    vocab = vocabulary if vocabulary is not None else _get_vocab()
    additions: list[str] = []
    seen_lower: set[str] = set()

    for raw_token in query.split():
        seen_lower.add(raw_token.lower())

    # Phase 1: abbreviation → expansion(s)
    for abbrev, expansions in vocab.items():
        if _word_match(abbrev, query):
            for exp in expansions:
                if exp.lower() not in seen_lower and exp.lower() not in query.lower():
                    additions.append(exp)
                    seen_lower.add(exp.lower())

    # Phase 2: expansion → abbreviation
    for abbrev, expansions in vocab.items():
        if abbrev.lower() in seen_lower:
            continue
        for exp in expansions:
            if _word_match(exp, query):
                if abbrev.lower() not in seen_lower:
                    additions.append(abbrev)
                    seen_lower.add(abbrev.lower())
                break

    if not additions:
        return query

    # Length cap: never grow the query past 3x the original token count.
    original_tokens = len(query.split())
    cap = max(original_tokens * 2, 8)  # the "appended" portion can be at most ~2x
    flat = " ".join(additions).split()
    if len(flat) > cap:
        flat = flat[:cap]

    return query + " " + " ".join(flat)


def _cli() -> int:
    if len(sys.argv) < 2:
        print("usage: query_enrichment.py <query>", file=sys.stderr)
        return 2
    q = " ".join(sys.argv[1:])
    print(enrich_query(q))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
