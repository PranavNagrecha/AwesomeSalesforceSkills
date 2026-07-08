#!/usr/bin/env python3
"""Checker for SOQL USING SCOPE clause usage in Apex / SOQL source.

Statically lints `.cls`, `.trigger`, `.apex`, and `.soql` files for the mistakes
documented in references/gotchas.md and references/llm-anti-patterns.md:

  * an invalid `USING SCOPE` value (not one of the eight documented SOQL scopes)
  * a Metadata API ListView `filterScope` value used where a SOQL scope belongs
    (e.g. `Queue`, `AssignedToMe`, `SalesTeam`, or PascalCase `MyTerritory`)
  * clause misplacement — `WHERE` appearing before `USING SCOPE`
  * `mine_and_my_groups` on an object other than `ProcessInstanceWorkItem`

SOQL keywords are case-insensitive, so scope values are compared case-insensitively;
underscores are significant (`my_territory` is valid, `myterritory` is not).

Comments are blanked (preserving line numbers) before scanning, and content inside
parentheses is removed before the structural checks so a subquery's inner `WHERE`
does not look like a misplaced outer clause. Scoping-rule metadata (which requires
`USING SCOPE EVERYTHING`) is not Apex source and is out of scope for this linter.

Stdlib only — no pip dependencies.

Usage:
    python3 check_soql_using_scope_clause.py [--manifest-dir path] [--file path]

Exit code 0 = no issues, 1 = issues found.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCANNED_SUFFIXES = {".cls", ".trigger", ".apex", ".soql"}

# The eight documented SOQL filterScope values (compared lowercase, underscores kept).
VALID_SOQL_SCOPES = {
    "delegated",
    "everything",
    "mine",
    "mine_and_my_groups",
    "my_territory",
    "my_team_territory",
    "scopingrule",
    "team",
}

# Metadata API ListView filterScope values frequently confused for SOQL scopes.
# Keyed by lowercase-with-underscores-removed; value is a targeted hint.
METADATA_CONFUSION = {
    "queue": "'Queue' is a Metadata API ListView filterScope, not a SOQL scope (no SOQL equivalent)",
    "assignedtome": "'AssignedToMe' is a Metadata API ListView filterScope, not a SOQL scope",
    "salesteam": "'SalesTeam' is a Metadata API ListView filterScope; the SOQL scope is 'team'",
    "mineandmygroups": "Metadata API casing; the SOQL scope is 'mine_and_my_groups'",
    "myterritory": "Metadata API casing; the SOQL scope is 'my_territory'",
    "myteamterritory": "Metadata API casing; the SOQL scope is 'my_team_territory'",
}

USING_SCOPE_VALUE_RE = re.compile(r"\bUSING\s+SCOPE\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)
INLINE_QUERY_RE = re.compile(r"\[\s*SELECT\b[\s\S]*?\]", re.IGNORECASE)
WHERE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)
USING_SCOPE_RE = re.compile(r"\bUSING\s+SCOPE\b", re.IGNORECASE)
MMG_OBJECT_RE = re.compile(
    r"\bFROM\s+([A-Za-z_][A-Za-z0-9_]*)[\s\S]*?\bUSING\s+SCOPE\s+mine_and_my_groups\b",
    re.IGNORECASE,
)
PARENS_RE = re.compile(r"\([^()]*\)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check SOQL USING SCOPE clause usage in Apex/SOQL source for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the source tree to scan (default: current directory).",
    )
    parser.add_argument(
        "--file",
        default=None,
        help="Lint a single file instead of walking --manifest-dir.",
    )
    return parser.parse_args()


def blank_comments(text: str) -> str:
    """Replace // and /* */ comments with spaces, preserving length and newlines.

    Respects single-quoted Apex string literals so a `//` inside a string is not
    treated as a comment. Because length and newlines are preserved, character
    offsets still map to the original line numbers.
    """
    out: list[str] = []
    i, n = 0, len(text)
    state = "normal"  # normal | string | line_comment | block_comment
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if state == "normal":
            if ch == "'":
                state = "string"
                out.append(ch)
            elif ch == "/" and nxt == "/":
                state = "line_comment"
                out.append("  ")
                i += 2
                continue
            elif ch == "/" and nxt == "*":
                state = "block_comment"
                out.append("  ")
                i += 2
                continue
            else:
                out.append(ch)
        elif state == "string":
            out.append(ch)
            if ch == "\\":
                # keep the escaped char verbatim
                if nxt:
                    out.append(nxt)
                    i += 2
                    continue
            elif ch == "'":
                state = "normal"
        elif state == "line_comment":
            out.append("\n" if ch == "\n" else " ")
            if ch == "\n":
                state = "normal"
        elif state == "block_comment":
            if ch == "*" and nxt == "/":
                out.append("  ")
                i += 2
                state = "normal"
                continue
            out.append("\n" if ch == "\n" else " ")
        i += 1
    return "".join(out)


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def strip_parens(query: str) -> str:
    """Remove parenthesized groups (subqueries, function args) repeatedly."""
    prev = None
    cur = query
    while prev != cur:
        prev = cur
        cur = PARENS_RE.sub(" ", cur)
    return cur


def check_scope_values(text: str, rel: str, issues: list[str]) -> None:
    for m in USING_SCOPE_VALUE_RE.finditer(text):
        token = m.group(1)
        low = token.lower()
        if low in VALID_SOQL_SCOPES:
            continue
        line = line_of(text, m.start())
        squished = low.replace("_", "")
        hint = METADATA_CONFUSION.get(squished)
        if hint:
            issues.append(
                f"{rel}:{line}: USING SCOPE '{token}' — {hint}. "
                f"Valid SOQL scopes: {', '.join(sorted(VALID_SOQL_SCOPES))}."
            )
        else:
            issues.append(
                f"{rel}:{line}: USING SCOPE '{token}' is not a valid SOQL filterScope. "
                f"Valid values: {', '.join(sorted(VALID_SOQL_SCOPES))}."
            )


def check_query_structure(text: str, rel: str, issues: list[str], whole_file: bool) -> None:
    if whole_file:
        queries = [(text, 0)]
    else:
        queries = [(m.group(0), m.start()) for m in INLINE_QUERY_RE.finditer(text)]
    for raw_query, start in queries:
        skeleton = strip_parens(raw_query)
        us = USING_SCOPE_RE.search(skeleton)
        if not us:
            continue
        where = WHERE_RE.search(skeleton)
        if where and where.start() < us.start():
            issues.append(
                f"{rel}:{line_of(text, start)}: USING SCOPE must come after FROM and before "
                f"WHERE — a WHERE clause precedes USING SCOPE in this query."
            )
        mmg = MMG_OBJECT_RE.search(skeleton)
        if mmg and mmg.group(1).lower() != "processinstanceworkitem":
            issues.append(
                f"{rel}:{line_of(text, start)}: USING SCOPE mine_and_my_groups is only valid on "
                f"ProcessInstanceWorkItem, but this query is FROM {mmg.group(1)}."
            )


def check_file(path: Path, root: Path, issues: list[str]) -> None:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues.append(f"{path}: could not read ({exc})")
        return
    text = blank_comments(raw)
    try:
        rel = str(path.relative_to(root))
    except ValueError:
        rel = str(path)
    check_scope_values(text, rel, issues)
    check_query_structure(text, rel, issues, whole_file=path.suffix.lower() == ".soql")


def iter_source_files(manifest_dir: Path):
    for path in sorted(manifest_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in SCANNED_SUFFIXES:
            yield path


def check(manifest_dir: Path, single_file: Path | None) -> tuple[list[str], int]:
    """Return (issues, files_scanned)."""
    issues: list[str] = []
    if single_file is not None:
        if not single_file.exists():
            return [f"File not found: {single_file}"], 0
        check_file(single_file, single_file.parent, issues)
        return issues, 1
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"], 0
    files = list(iter_source_files(manifest_dir))
    for path in files:
        check_file(path, manifest_dir, issues)
    return issues, len(files)


def main() -> int:
    args = parse_args()
    single = Path(args.file) if args.file else None
    issues, scanned = check(Path(args.manifest_dir), single)

    if single is None and scanned == 0:
        print(
            f"No {', '.join(sorted(SCANNED_SUFFIXES))} files found under "
            f"{args.manifest_dir} — nothing to check."
        )
        return 0

    if not issues:
        print(f"No issues found ({scanned} file(s) scanned).")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
