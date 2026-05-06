#!/usr/bin/env python3
"""Static checks for Apex Schema describe anti-patterns.

Scans Apex sources for the high-confidence anti-patterns documented in
`references/llm-anti-patterns.md`:

  1. `Schema.getGlobalDescribe()` called inside a `for` / `while` loop.
  2. Per-field `.getDescribe()` calls inside loops.
  3. `getPicklistValues()` enumeration without an `isActive()` filter.
  4. `getRecordTypeInfosByName(...)` against a literal label (use
     `getRecordTypeInfosByDeveloperName` instead).
  5. `Type.forName('<API name>')` followed by a cast to `SObject`
     (wrong tool — use `Schema.getGlobalDescribe().get(...).newSObject()`).

Stdlib only.

Usage:
    python3 check_apex_schema_describe.py --src-root .
    python3 check_apex_schema_describe.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Locate `for (...) { ... }` and `while (...) { ... }` blocks. Apex doesn't
# allow nested code-block parsing with regex perfectly, but we approximate by
# matching from the loop header to the next closing brace at the same depth
# using a simple scanner.

_LOOP_HEADER_RE = re.compile(r"\b(for|while)\s*\(", re.IGNORECASE)
_GLOBAL_DESCRIBE_RE = re.compile(r"Schema\.getGlobalDescribe\s*\(\s*\)")
_GET_DESCRIBE_RE = re.compile(r"\b\w+\.\w+\.getDescribe\s*\(\s*\)")
_PICKLIST_VALUES_RE = re.compile(r"\.getPicklistValues\s*\(\s*\)")
_IS_ACTIVE_RE = re.compile(r"\.isActive\s*\(\s*\)")
_RT_BY_NAME_RE = re.compile(
    r"\.getRecordTypeInfosByName\s*\(\s*\)\s*\.get\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
)
_TYPE_FORNAME_SOBJECT_RE = re.compile(
    r"Type\.forName\s*\(\s*['\"](\w+(?:__c)?)['\"]\s*\)"
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _extract_loop_bodies(text: str) -> list[tuple[int, int]]:
    """Return list of (start, end) char offsets for each loop body."""
    bodies: list[tuple[int, int]] = []
    for header in _LOOP_HEADER_RE.finditer(text):
        # Skip past the matched parens
        i = header.end()
        depth = 1
        while i < len(text) and depth > 0:
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
            i += 1
        # Skip whitespace / newline to find `{`
        while i < len(text) and text[i] in " \t\r\n":
            i += 1
        if i >= len(text) or text[i] != "{":
            continue
        body_start = i + 1
        depth = 1
        i += 1
        while i < len(text) and depth > 0:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        body_end = i - 1
        bodies.append((body_start, body_end))
    return bodies


def _scan_apex(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    loop_bodies = _extract_loop_bodies(text)

    def _in_any_loop(pos: int) -> bool:
        return any(s <= pos <= e for s, e in loop_bodies)

    # 1. getGlobalDescribe() inside loops
    for m in _GLOBAL_DESCRIBE_RE.finditer(text):
        if _in_any_loop(m.start()):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: Schema.getGlobalDescribe() "
                "called inside a loop — hoist to a static final or assign once "
                "before the loop (references/llm-anti-patterns.md § 1)"
            )

    # 2. .getDescribe() inside loops (per-field describe in loop)
    for m in _GET_DESCRIBE_RE.finditer(text):
        if _in_any_loop(m.start()):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: per-field `.getDescribe()` "
                "inside a loop — describe the field once outside the loop "
                "(references/gotchas.md)"
            )

    # 3. getPicklistValues without isActive filter (file-level heuristic)
    if _PICKLIST_VALUES_RE.search(text) and not _IS_ACTIVE_RE.search(text):
        m = _PICKLIST_VALUES_RE.search(text)
        if m:
            findings.append(
                f"{path}:{_line_no(text, m.start())}: getPicklistValues() used "
                "without an isActive() filter — inactive picklist values will "
                "appear in output (references/llm-anti-patterns.md § 3)"
            )

    # 4. getRecordTypeInfosByName against a literal label
    for m in _RT_BY_NAME_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: getRecordTypeInfosByName(...)"
            f".get('{m.group(1)}') uses the label as a key — labels can be "
            "renamed; prefer getRecordTypeInfosByDeveloperName() with the stable "
            "DeveloperName (references/llm-anti-patterns.md § 4)"
        )

    # 5. Type.forName('<APIName>') followed by cast to SObject
    for m in _TYPE_FORNAME_SOBJECT_RE.finditer(text):
        # Look ahead ~120 chars for "(SObject)" cast
        window = text[m.end(): m.end() + 200]
        if re.search(r"\(\s*SObject\s*\)", window):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: Type.forName('{m.group(1)}') "
                "used to construct an SObject — Type.forName is for Apex types. "
                "Use Schema.getGlobalDescribe().get('<api>').newSObject() instead "
                "(references/llm-anti-patterns.md § 2)"
            )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]
    findings: list[str] = []
    for apex in list(root.rglob("*.cls")) + list(root.rglob("*.trigger")):
        findings.extend(_scan_apex(apex))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Apex sources for Schema describe anti-patterns "
            "(getGlobalDescribe in loops, per-field getDescribe in loops, "
            "getPicklistValues without isActive, getRecordTypeInfosByName, "
            "Type.forName for SObject construction)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the Apex source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no Apex Schema describe anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
