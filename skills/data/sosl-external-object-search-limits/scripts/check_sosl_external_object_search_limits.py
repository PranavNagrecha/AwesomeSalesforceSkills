#!/usr/bin/env python3
"""Linter for SOSL statements that target Salesforce Connect external objects.

Flags the query-level restrictions documented in the SOQL and SOSL Reference page
"SOSL Limits on External Object Search Results" whenever a SOSL statement's RETURNING
clause names an external object (an object whose API name ends in ``__x``):

  * unsupported operators: INCLUDES, LIKE, EXCLUDES
  * unsupported function:  toLabel()
  * unsupported clauses:   UPDATE TRACKING, UPDATE VIEWSTAT, WITH DATA CATEGORY
  * FIND search term longer than 100 characters
  * missing RETURNING clause (external objects are excluded from results without it)

Adapter-scoped rules are reported according to ``--adapter``:

  * odata  -> logical operators (AND / OR / AND NOT) in the FIND term are ERRORS
  * custom -> convertCurrency() and generic WITH clauses are ERRORS
  * any    -> those three are reported as WARN (adapter-dependent; the default)

Stdlib only — no pip dependencies.

Usage:
    python3 check_sosl_external_object_search_limits.py --query "FIND 'x*' RETURNING Order__x(Name__c)"
    python3 check_sosl_external_object_search_limits.py --file MyController.cls
    python3 check_sosl_external_object_search_limits.py --manifest-dir force-app/main/default
    python3 check_sosl_external_object_search_limits.py --manifest-dir . --adapter odata

Exit code 0 = no ERROR-level issues, 1 = at least one ERROR (WARN alone does not fail).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCANNED_SUFFIXES = {".cls", ".trigger", ".apex", ".soql", ".txt", ".md"}
MAX_TERM_CHARS = 100

# A SOSL statement: FIND <term-in-quotes-or-braces> ... up to ] , ; , next FIND, or end-of-text.
_STATEMENT_RE = re.compile(
    r"FIND\s+(?P<term>\{[^}]*\}|'[^']*'|\"[^\"]*\")(?P<tail>.*?)(?=\bFIND\b|\]|;|$)",
    re.IGNORECASE | re.DOTALL,
)
_EXTERNAL_OBJ_RE = re.compile(r"\b\w+__x\b")
_RETURNING_RE = re.compile(r"\bRETURNING\b", re.IGNORECASE)
# WITH DATA CATEGORY must be tested before generic WITH so it isn't mis-bucketed.
_WITH_DATA_CATEGORY_RE = re.compile(r"\bWITH\s+DATA\s+CATEGORY\b", re.IGNORECASE)
_GENERIC_WITH_RE = re.compile(r"\bWITH\b", re.IGNORECASE)
_LOGICAL_OP_RE = re.compile(r"\b(?:AND\s+NOT|AND|OR)\b", re.IGNORECASE)

# (regex, label) pairs for tokens unsupported on ALL external objects.
_UNIVERSAL_TOKENS = [
    (re.compile(r"\bINCLUDES\s*\(", re.IGNORECASE), "INCLUDES operator"),
    (re.compile(r"\bEXCLUDES\s*\(", re.IGNORECASE), "EXCLUDES operator"),
    (re.compile(r"\bLIKE\b", re.IGNORECASE), "LIKE operator"),
    (re.compile(r"\btoLabel\s*\(", re.IGNORECASE), "toLabel() function"),
    (re.compile(r"\bUPDATE\s+TRACKING\b", re.IGNORECASE), "UPDATE TRACKING clause"),
    (re.compile(r"\bUPDATE\s+VIEWSTAT\b", re.IGNORECASE), "UPDATE VIEWSTAT clause"),
]


class Issue:
    __slots__ = ("severity", "location", "message")

    def __init__(self, severity: str, location: str, message: str) -> None:
        self.severity = severity  # "ERROR" or "WARN"
        self.location = location
        self.message = message

    def __str__(self) -> str:
        return f"{self.severity}: {self.location}: {self.message}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint SOSL statements that target Salesforce Connect external objects (__x).",
    )
    src = parser.add_mutually_exclusive_group()
    src.add_argument("--query", help="A single SOSL statement to lint inline.")
    src.add_argument("--file", help="A single file to scan for SOSL statements.")
    src.add_argument(
        "--manifest-dir",
        help="Directory to scan recursively for SOSL statements "
        f"(files with suffixes: {', '.join(sorted(SCANNED_SUFFIXES))}).",
    )
    parser.add_argument(
        "--adapter",
        choices=("any", "odata", "custom"),
        default="any",
        help="Adapter of the external object, to scope adapter-specific rules "
        "(default: any -> report adapter-specific rules as WARN).",
    )
    return parser.parse_args()


def _term_text(raw_term: str) -> str:
    """Strip the surrounding braces or quotes from a captured FIND term."""
    inner = raw_term.strip()
    if inner and inner[0] in "{'\"":
        inner = inner[1:]
    if inner and inner[-1] in "}'\"":
        inner = inner[:-1]
    return inner


def check_statement(term_raw: str, tail: str, adapter: str, location: str) -> list[Issue]:
    """Check one SOSL statement; only enforce external-object rules when a __x object is present."""
    issues: list[Issue] = []
    statement = f"FIND {term_raw}{tail}"

    external_objs = sorted(set(_EXTERNAL_OBJ_RE.findall(tail)))
    if not external_objs:
        return issues  # no external object in RETURNING -> these rules don't apply

    objs = ", ".join(external_objs)

    # Universally unsupported operators / functions / clauses.
    for pattern, label in _UNIVERSAL_TOKENS:
        if pattern.search(statement):
            issues.append(Issue("ERROR", location, f"{label} is unsupported on external objects ({objs})"))
    if _WITH_DATA_CATEGORY_RE.search(statement):
        issues.append(Issue("ERROR", location, f"WITH DATA CATEGORY clause is unsupported on external objects ({objs})"))

    # FIND search-term length cap (external objects only).
    term = _term_text(term_raw)
    if len(term) > MAX_TERM_CHARS:
        issues.append(
            Issue(
                "ERROR",
                location,
                f"FIND search term is {len(term)} characters; external objects require 100 or fewer ({objs})",
            )
        )

    # RETURNING must be present (we only got here because a __x appeared in the tail, which
    # normally means RETURNING is present — but guard the edge case explicitly).
    if not _RETURNING_RE.search(tail):
        issues.append(
            Issue(
                "ERROR",
                location,
                f"external object ({objs}) referenced without a RETURNING clause; it will be excluded from results",
            )
        )

    # Adapter-scoped: OData -> logical operators in FIND term are unsupported.
    if _LOGICAL_OP_RE.search(term):
        if adapter == "odata":
            issues.append(Issue("ERROR", location, "logical operators in a FIND clause are unsupported by OData adapters"))
        elif adapter == "any":
            issues.append(
                Issue("WARN", location, "logical operators in FIND are unsupported by OData adapters; confirm the adapter type")
            )

    # Adapter-scoped: custom adapters -> convertCurrency() and generic WITH are unsupported.
    has_convert = re.search(r"\bconvertCurrency\s*\(", statement, re.IGNORECASE) is not None
    # generic WITH that is NOT "WITH DATA CATEGORY" (already handled above)
    has_generic_with = bool(_GENERIC_WITH_RE.search(statement)) and not _WITH_DATA_CATEGORY_RE.search(statement)
    for present, feature in ((has_convert, "convertCurrency() function"), (has_generic_with, "generic WITH clause")):
        if not present:
            continue
        if adapter == "custom":
            issues.append(Issue("ERROR", location, f"{feature} is unsupported by custom (Apex Connector Framework) adapters"))
        elif adapter == "any":
            issues.append(
                Issue("WARN", location, f"{feature} is unsupported by custom adapters; confirm the adapter type")
            )

    return issues


def check_text(text: str, adapter: str, location: str) -> list[Issue]:
    issues: list[Issue] = []
    for match in _STATEMENT_RE.finditer(text):
        issues.extend(check_statement(match.group("term"), match.group("tail"), adapter, location))
    return issues


def _iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in SCANNED_SUFFIXES:
            yield path


def run(args: argparse.Namespace) -> tuple[list[Issue], int]:
    """Return (issues, statements_scanned)."""
    issues: list[Issue] = []
    scanned = 0

    if args.query is not None:
        scanned = len(_STATEMENT_RE.findall(args.query))
        issues.extend(check_text(args.query, args.adapter, "<--query>"))
        return issues, scanned

    if args.file is not None:
        path = Path(args.file)
        if not path.exists():
            return [Issue("ERROR", str(path), "file not found")], 0
        text = path.read_text(encoding="utf-8", errors="replace")
        scanned = len(_STATEMENT_RE.findall(text))
        issues.extend(check_text(text, args.adapter, str(path)))
        return issues, scanned

    root = Path(args.manifest_dir) if args.manifest_dir else Path(".")
    if not root.exists():
        return [Issue("ERROR", str(root), "manifest directory not found")], 0
    for path in _iter_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            issues.append(Issue("WARN", str(path), f"could not read file ({exc})"))
            continue
        scanned += len(_STATEMENT_RE.findall(text))
        issues.extend(check_text(text, args.adapter, str(path)))
    return issues, scanned


def main() -> int:
    args = parse_args()
    issues, scanned = run(args)

    if scanned == 0 and not issues:
        print("No SOSL statements found — nothing to check.")
        return 0

    errors = [i for i in issues if i.severity == "ERROR"]
    warns = [i for i in issues if i.severity == "WARN"]

    if not issues:
        print(f"Scanned {scanned} SOSL statement(s). No external-object issues found.")
        return 0

    for issue in errors + warns:
        print(str(issue), file=sys.stderr)
    print(
        f"\nScanned {scanned} SOSL statement(s): {len(errors)} error(s), {len(warns)} warning(s).",
        file=sys.stderr,
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
