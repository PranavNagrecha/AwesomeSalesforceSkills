#!/usr/bin/env python3
"""Checker for SOQL/SOSL FORMAT() localized-output usage.

Scans source files for queries that use the FORMAT() function and flags the
mistakes documented in references/gotchas.md and references/llm-anti-patterns.md:

  ERROR   FORMAT()/convertCurrency() used in a WHERE clause
          (convertCurrency() in a WHERE clause is a documented error, and
          filtering on FORMAT() output compares locale-dependent strings).
  ERROR   A field selected both raw and inside FORMAT() with no alias on the
          formatted column (aliasing is required when a field appears twice).
  ERROR   FORMAT() called with a second, comma-separated argument
          (FORMAT() takes a single field/expression — there is no format mask).
  WARN    FORMAT() used in an ORDER BY / HAVING clause (sorts/groups on a
          locale string rather than the underlying value).

Stdlib only — no pip dependencies. Exit code: 1 if any ERROR was found, else 0
(WARN findings are printed but do not fail the gate).

Usage:
    python3 check_soql_format_function_localization.py [--manifest-dir path]
    python3 check_soql_format_function_localization.py --self-test
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SOURCE_SUFFIXES = {".cls", ".trigger", ".apex", ".soql"}

# Clause keywords that terminate a WHERE / ORDER BY / HAVING window.
_WINDOW_TERMINATORS = re.compile(
    r"\b(?:GROUP\s+BY|ORDER\s+BY|HAVING|LIMIT|OFFSET|FOR\s+(?:UPDATE|VIEW|REFERENCE))\b|[\];]",
    re.IGNORECASE,
)
_CLAUSE_STARTS = re.compile(r"\b(WHERE|HAVING|ORDER\s+BY)\b", re.IGNORECASE)
_SELECT_LIST = re.compile(r"\bSELECT\b(.+?)\bFROM\b", re.IGNORECASE | re.DOTALL)
# SOSL RETURNING Object( field list ) — allow one level of nested parens.
_RETURNING_LIST = re.compile(
    r"\bRETURNING\b\s+\w+\s*\(((?:[^()]|\([^()]*\))*)\)", re.IGNORECASE | re.DOTALL
)
_FORMAT_CALL = re.compile(r"\bFORMAT\s*\(", re.IGNORECASE)
_BARE_FIELD = re.compile(r"^[A-Za-z_][\w.]*$")
_IDENT = re.compile(r"[A-Za-z_]\w*")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check SOQL/SOSL FORMAT() usage for localization mistakes.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for .cls/.trigger/.apex/.soql source (default: cwd).",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run built-in unit checks against known-good and known-bad queries and exit.",
    )
    return parser.parse_args()


def _match_paren(text: str, open_idx: int) -> int:
    """Return the index of the ')' matching the '(' at open_idx, or -1."""
    depth = 0
    for i in range(open_idx, len(text)):
        c = text[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _split_top_level(list_str: str) -> list[str]:
    """Split a SELECT/RETURNING field list on commas that are not inside parens."""
    items, depth, start = [], 0, 0
    for i, c in enumerate(list_str):
        if c == "(":
            depth += 1
        elif c == ")":
            depth = max(0, depth - 1)
        elif c == "," and depth == 0:
            items.append(list_str[start:i])
            start = i + 1
    items.append(list_str[start:])
    return [item.strip() for item in items if item.strip()]


def _has_top_level_comma(arg: str) -> bool:
    depth = 0
    for c in arg:
        if c == "(":
            depth += 1
        elif c == ")":
            depth = max(0, depth - 1)
        elif c == "," and depth == 0:
            return True
    return False


def _innermost_field(arg: str) -> str:
    """Peel nested single-function wrappers (convertCurrency/MIN/...) to the field."""
    expr = arg.strip()
    wrapper = re.compile(r"^\w+\s*\((.*)\)$", re.DOTALL)
    while True:
        m = wrapper.match(expr)
        if not m:
            break
        expr = m.group(1).strip()
    return expr


def _analyze_field_list(list_str: str, where: str, issues: list[tuple[str, str]]) -> None:
    items = _split_top_level(list_str)
    bare = {item.lower() for item in items if _BARE_FIELD.match(item)}

    for item in items:
        m = _FORMAT_CALL.search(item)
        if not m:
            continue
        open_idx = item.index("(", m.start())
        close_idx = _match_paren(item, open_idx)
        if close_idx == -1:
            issues.append(("ERROR", f"{where}: unbalanced FORMAT( ... ) in `{item.strip()}`"))
            continue
        arg = item[open_idx + 1 : close_idx].strip()
        alias = item[close_idx + 1 :].strip()
        alias = re.sub(r"^(?i:as)\s+", "", alias).strip()

        if _has_top_level_comma(arg):
            issues.append(
                (
                    "ERROR",
                    f"{where}: FORMAT() has more than one argument in `{item.strip()}` — "
                    f"FORMAT() takes a single field/expression, there is no format-mask argument",
                )
            )

        inner = _innermost_field(arg)
        if _BARE_FIELD.match(inner) and inner.lower() in bare and not alias:
            issues.append(
                (
                    "ERROR",
                    f"{where}: `{inner}` is selected both raw and inside FORMAT() without an "
                    f"alias — aliasing is required when the same field appears more than once "
                    f"(e.g. `FORMAT({inner}) {inner.split('.')[-1].lower()}Display`)",
                )
            )


def _analyze_clause_windows(text: str, rel: str, issues: list[tuple[str, str]]) -> None:
    for m in _CLAUSE_STARTS.finditer(text):
        clause = re.sub(r"\s+", " ", m.group(1)).upper()
        start = m.end()
        term = _WINDOW_TERMINATORS.search(text, start)
        window = text[start : term.start() if term else min(len(text), start + 400)]
        loc = f"{rel} ({clause} clause)"
        if re.search(r"\bconvertCurrency\s*\(", window, re.IGNORECASE) and clause == "WHERE":
            issues.append(
                ("ERROR", f"{loc}: convertCurrency() cannot be used in a WHERE clause "
                          f"— compare against an ISO currency literal (e.g. Amount > USD5000) instead")
            )
        if _FORMAT_CALL.search(window):
            sev = "ERROR" if clause == "WHERE" else "WARN"
            issues.append(
                (sev, f"{loc}: FORMAT() belongs in the SELECT list, not in {clause} "
                      f"— it renders a locale-dependent string, not a comparable/sortable value")
            )


def analyze_text(text: str, rel: str) -> list[tuple[str, str]]:
    """Return a list of (severity, message) findings for one file's text."""
    issues: list[tuple[str, str]] = []
    if not _FORMAT_CALL.search(text) and not re.search(r"\bconvertCurrency\s*\(", text, re.I):
        return issues

    for m in _SELECT_LIST.finditer(text):
        _analyze_field_list(m.group(1), f"{rel} (SELECT list)", issues)
    for m in _RETURNING_LIST.finditer(text):
        _analyze_field_list(m.group(1), f"{rel} (RETURNING list)", issues)
    _analyze_clause_windows(text, rel, issues)
    return issues


def iter_source_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix in SOURCE_SUFFIXES:
            yield path


def run(manifest_dir: Path) -> tuple[list[tuple[str, str]], int]:
    if not manifest_dir.exists():
        return [("ERROR", f"Manifest directory not found: {manifest_dir}")], 0
    all_issues: list[tuple[str, str]] = []
    scanned = 0
    for path in iter_source_files(manifest_dir):
        scanned += 1
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            all_issues.append(("WARN", f"{path}: could not read ({exc})"))
            continue
        rel = str(path.relative_to(manifest_dir)) if manifest_dir in path.parents else str(path)
        all_issues.extend(analyze_text(text, rel))
    return all_issues, scanned


def _self_test() -> int:
    cases = [
        # (text, expected_error_substring or None)
        ("SELECT Id, LastModifiedDate, FORMAT(LastModifiedDate) formattedDate FROM Account", None),
        ("SELECT Id, LastModifiedDate, FORMAT(LastModifiedDate) FROM Account", "aliasing is required"),
        ("SELECT amount, FORMAT(convertCurrency(amount)) convertedCurrency FROM Opportunity", None),
        ("SELECT FORMAT(MIN(CloseDate)) earliest FROM Opportunity", None),
        ("SELECT Id FROM Opportunity WHERE convertCurrency(Amount) > 5000", "WHERE clause"),
        ("SELECT FORMAT(Amount) amt FROM Opportunity ORDER BY FORMAT(Amount)", "ORDER BY"),
        ("SELECT FORMAT(CloseDate, 'yyyy-MM-dd') d FROM Opportunity", "single field/expression"),
        ("FIND {Acme} RETURNING Account(Id, LastModifiedDate, FORMAT(LastModifiedDate) FormattedDate)", None),
    ]
    failures = 0
    for text, expect in cases:
        issues = analyze_text(text, "<self-test>")
        joined = " || ".join(f"[{sev}] {msg}" for sev, msg in issues)
        if expect is None:
            if issues:
                failures += 1
                print(f"FAIL (expected clean): {text}\n   got: {joined}", file=sys.stderr)
        else:
            if expect not in joined:
                failures += 1
                print(f"FAIL (expected '{expect}'): {text}\n   got: {joined or '<none>'}", file=sys.stderr)
    if failures:
        print(f"self-test: {failures} case(s) failed", file=sys.stderr)
        return 1
    print(f"self-test: all {len(cases)} cases passed")
    return 0


def main() -> int:
    args = parse_args()
    if args.self_test:
        return _self_test()

    issues, scanned = run(Path(args.manifest_dir))
    errors = [i for i in issues if i[0] == "ERROR"]

    if not issues:
        print(f"No issues found ({scanned} source file(s) scanned).")
        return 0

    for sev, msg in issues:
        print(f"{sev}: {msg}", file=sys.stderr)
    print(f"\n{len(errors)} error(s), {len(issues) - len(errors)} warning(s) "
          f"across {scanned} source file(s).", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
