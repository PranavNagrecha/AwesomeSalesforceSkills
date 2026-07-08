#!/usr/bin/env python3
"""Checker for per-object SOQL limits and restrictions.

Statically scans Apex source (.cls, .trigger, .apex) and standalone .soql files for
SOQL statements that violate a *per-object* restriction documented in the SOQL and SOSL
Reference — the rules that fail a query because of the object it targets, on top of the
generic governor limits. Stdlib only — no pip dependencies.

Checks performed per query:
  - ContentDocumentLink / ContentHubItem / Vote     -> must filter on an allowed field
  - Attachment                                       -> must be bounded (WHERE + LIMIT) for the 100,000 cap
  - TopicAssignment / NewsFeed / UserProfileFeed     -> must carry a LIMIT (unless View All Data)
  - UserRecordAccess                                 -> ORDER BY HasAccess when HasAccess is selected
  - KnowledgeArticleVersion (inline Apex SOQL)       -> no bind variable; must use dynamic SOQL
  - big objects (--big-objects)                      -> no unsupported operators (!=, LIKE, NOT IN, EXCLUDES, INCLUDES)

Usage:
    python3 check_soql_object_limits_and_restrictions.py [--manifest-dir path]
    python3 check_soql_object_limits_and_restrictions.py --manifest-dir force-app --big-objects Interaction__b,Event__b

Exit code 0 = no issues, 1 = issues found.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCAN_EXTENSIONS = {".cls", ".trigger", ".apex", ".soql"}

# Objects that require a WHERE filter on one of a fixed set of fields.
MANDATORY_FILTER_FIELDS = {
    "ContentDocumentLink": ("Id", "ContentDocumentId", "LinkedEntityId"),
    "ContentHubItem": ("Id", "ExternalId", "ContentHubRepositoryId"),
    "Vote": ("Id", "ParentId", "Parent.Type"),
}
# Objects that require a LIMIT clause unless the user holds View All Data.
REQUIRE_LIMIT = {
    "TopicAssignment": 1100,
    "NewsFeed": 1000,
    "UserProfileFeed": 1000,
}
# Operators a big-object SOQL filter may not use.
BIG_OBJECT_BAD_OPERATORS = ("!=", " LIKE ", " NOT IN ", " EXCLUDES ", " INCLUDES ")

# Capture inline Apex SOQL: [ SELECT ... ]  (non-greedy, DOTALL).
_INLINE_SOQL = re.compile(r"\[\s*(SELECT\b.*?)\]", re.IGNORECASE | re.DOTALL)
# Capture dynamic SOQL string literals passed to Database.query family.
_DYNAMIC_SOQL = re.compile(
    r"Database\.\s*(?:query|getQueryLocator|countQuery|queryWithBinds)\s*\(\s*"
    r"(['\"])(SELECT\b.*?)\1",
    re.IGNORECASE | re.DOTALL,
)
_FROM_OBJECT = re.compile(r"\bFROM\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)
_LINE_COMMENT = re.compile(r"//[^\n]*")
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check SOQL statements for per-object limit and restriction violations.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for Apex/SOQL files (default: current directory).",
    )
    parser.add_argument(
        "--big-objects",
        default="",
        help="Comma-separated big-object API names (e.g. 'Interaction__b,Event__b') to "
        "enable index-operator checks on. Optional.",
    )
    return parser.parse_args()


def _strip_comments(text: str) -> str:
    return _LINE_COMMENT.sub("", _BLOCK_COMMENT.sub("", text))


def _from_object(query: str) -> str | None:
    match = _FROM_OBJECT.search(query)
    return match.group(1) if match else None


def _norm(query: str) -> str:
    """Collapse whitespace and upper-case for keyword/operator matching."""
    return re.sub(r"\s+", " ", query).strip().upper()


def _has_where_field(query_upper: str, fields: tuple[str, ...]) -> bool:
    if "WHERE" not in query_upper:
        return False
    return any(field.upper() in query_upper for field in fields)


def _check_query(query: str, location: str, big_objects: set[str], issues: list[str]) -> None:
    obj = _from_object(query)
    if obj is None:
        return
    query_upper = _norm(query)

    if obj in MANDATORY_FILTER_FIELDS:
        fields = MANDATORY_FILTER_FIELDS[obj]
        if not _has_where_field(query_upper, fields):
            issues.append(
                f"{location}: query on {obj} must filter on one of "
                f"{', '.join(fields)} — an unfiltered query fails at runtime."
            )

    if obj in REQUIRE_LIMIT:
        if "LIMIT" not in query_upper:
            issues.append(
                f"{location}: query on {obj} needs a LIMIT clause "
                f"(<= {REQUIRE_LIMIT[obj]:,}) unless the running user holds View All Data."
            )

    if obj == "Attachment":
        bounded = "WHERE" in query_upper and "LIMIT" in query_upper
        if not bounded:
            issues.append(
                f"{location}: query on Attachment should be bounded with a WHERE and a "
                f"LIMIT — it fails past 100,000 records and does not paginate with OFFSET."
            )

    if obj == "UserRecordAccess":
        if "HASACCESS" in query_upper and "ORDER BY HASACCESS" not in query_upper:
            issues.append(
                f"{location}: query on UserRecordAccess selects HasAccess but is missing "
                f"'ORDER BY HasAccess' (required); note the result is capped at 200 rows."
            )

    if obj in big_objects:
        for bad in BIG_OBJECT_BAD_OPERATORS:
            if bad.strip() in query_upper:
                issues.append(
                    f"{location}: big-object query on {obj} uses unsupported operator "
                    f"'{bad.strip()}' — big objects filter only on index fields with "
                    f"=, <, >, <=, >=, IN."
                )
                break


def _check_inline_knowledge(text: str, location: str, issues: list[str]) -> None:
    """Inline (bracket) SOQL on KnowledgeArticleVersion may not use a bind variable."""
    for match in _INLINE_SOQL.finditer(text):
        query = match.group(1)
        if _from_object(query) == "KnowledgeArticleVersion" and ":" in query:
            issues.append(
                f"{location}: inline SOQL on KnowledgeArticleVersion uses a bind variable — "
                f"this object requires dynamic SOQL (Database.query/queryWithBinds)."
            )


def check(manifest_dir: Path, big_objects: set[str]) -> list[str]:
    issues: list[str] = []
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    files = sorted(
        p for p in manifest_dir.rglob("*") if p.is_file() and p.suffix in SCAN_EXTENSIONS
    )
    if not files:
        return [
            f"No Apex/SOQL files ({', '.join(sorted(SCAN_EXTENSIONS))}) found under "
            f"{manifest_dir} — nothing to check."
        ]

    for path in files:
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            issues.append(f"{path}: could not read ({exc})")
            continue
        text = _strip_comments(raw)

        for match in _INLINE_SOQL.finditer(text):
            _check_query(match.group(1), str(path), big_objects, issues)
        for match in _DYNAMIC_SOQL.finditer(text):
            _check_query(match.group(2), str(path), big_objects, issues)
        _check_inline_knowledge(text, str(path), issues)

    return issues


def main() -> int:
    args = parse_args()
    big_objects = {name.strip() for name in args.big_objects.split(",") if name.strip()}
    issues = check(Path(args.manifest_dir), big_objects)
    if not issues:
        print("No issues found.")
        return 0
    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
