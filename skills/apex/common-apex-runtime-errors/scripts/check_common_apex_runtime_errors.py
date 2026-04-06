#!/usr/bin/env python3
"""Checker script for Common Apex Runtime Errors skill.

Scans Apex class files (.cls) in a Salesforce metadata directory for patterns
that commonly cause NullPointerException, QueryException, DmlException,
ListException, and LimitException at runtime.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_common_apex_runtime_errors.py --manifest-dir force-app/main/default/classes
    python3 check_common_apex_runtime_errors.py --manifest-dir .
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Pattern definitions
# Each entry: (pattern_name, compiled_regex, message_template)
# ---------------------------------------------------------------------------

# 1. Scalar SOQL assignment: SomeType varName = [SELECT ...
#    Heuristic: word char sequence, space, identifier, space, =, space, [SELECT
_SCALAR_SOQL_RE = re.compile(
    r'\b(?!List\b|Map\b|Set\b)([A-Z][A-Za-z0-9_]*)\s+\w+\s*=\s*\[SELECT\b',
    re.IGNORECASE,
)

# 2. Catching LimitException — dead code
_CATCH_LIMIT_RE = re.compile(
    r'catch\s*\(\s*(System\.)?LimitException\b',
    re.IGNORECASE,
)

# 3. SOQL inside a for loop — very rough heuristic
#    Match [SELECT on lines that appear to be indented inside loop blocks.
#    We use a stateful line scanner in the checker function instead of a single regex.

# 4. DmlException catch with only getMessage() — no getDmlMessage
_DML_CATCH_ONLY_GETMESSAGE_RE = re.compile(
    r'catch\s*\(\s*(System\.)?DmlException\b',
    re.IGNORECASE,
)

# 5. Trigger.new access without null guard when isDelete context
#    Look for Trigger.new[ or Trigger.new. inside a file that also has isDelete
_TRIGGER_NEW_IN_DELETE_RE = re.compile(r'Trigger\.new\s*[\.\[]', re.IGNORECASE)
_TRIGGER_IS_DELETE_RE = re.compile(r'Trigger\.isDelete', re.IGNORECASE)

# 6. List index access [0] without isEmpty guard on the immediately preceding lines
_LIST_ZERO_INDEX_RE = re.compile(r'\b\w+\s*\[\s*0\s*\]', re.IGNORECASE)
_IS_EMPTY_RE = re.compile(r'\.isEmpty\(\)', re.IGNORECASE)


def _scan_scalar_soql(lines: list[str], path: Path) -> list[str]:
    issues = []
    for lineno, line in enumerate(lines, start=1):
        if _SCALAR_SOQL_RE.search(line):
            issues.append(
                f"{path}:{lineno}: [NullPointerException / QueryException risk] "
                f"Scalar SObject SOQL assignment without List guard — "
                f"returns null on zero rows, throws on multiple rows. "
                f"Use List<SObject> + isEmpty() instead."
            )
    return issues


def _scan_catch_limit(lines: list[str], path: Path) -> list[str]:
    issues = []
    for lineno, line in enumerate(lines, start=1):
        if _CATCH_LIMIT_RE.search(line):
            issues.append(
                f"{path}:{lineno}: [LimitException dead code] "
                f"catch (LimitException) is uncatchable — this block never executes. "
                f"Remove it and add upstream Limits.getQueries() / Limits.getLimitQueries() guards."
            )
    return issues


def _scan_soql_in_loop(lines: list[str], path: Path) -> list[str]:
    """Rough heuristic: flag [SELECT that appears inside a for-loop body.

    Tracks brace depth after a for( line to determine if subsequent SOQL
    is inside the loop. False positives are possible; treat as advisory.
    """
    issues = []
    in_for_loop = False
    for_brace_depth = 0
    current_depth = 0

    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Track brace depth
        current_depth += stripped.count('{') - stripped.count('}')

        # Detect for-loop start (simple heuristic)
        if re.search(r'\bfor\s*\(', stripped, re.IGNORECASE):
            in_for_loop = True
            for_brace_depth = current_depth

        # If we have dropped back below for_brace_depth, we exited the loop
        if in_for_loop and current_depth < for_brace_depth:
            in_for_loop = False
            for_brace_depth = 0

        # Flag SOQL inside a for-loop body
        if in_for_loop and current_depth > for_brace_depth:
            if re.search(r'\[SELECT\b', stripped, re.IGNORECASE):
                issues.append(
                    f"{path}:{lineno}: [LimitException risk] "
                    f"SOQL query appears inside a for-loop body — "
                    f"will breach governor limits under bulk load. "
                    f"Move SOQL outside the loop and use IN :collection bind."
                )

    return issues


def _scan_dml_exception_catch(lines: list[str], path: Path) -> list[str]:
    """Flag DmlException catch blocks that do not call getDmlMessage."""
    issues = []
    full_text = ''.join(lines)

    # Find all DmlException catch blocks
    for m in _DML_CATCH_ONLY_GETMESSAGE_RE.finditer(full_text):
        # Find the matching catch block by scanning forward for braces
        start = m.start()
        # Find the opening brace of the catch block
        brace_pos = full_text.find('{', start)
        if brace_pos == -1:
            continue
        # Extract up to 500 chars of the block for inspection
        block_snippet = full_text[brace_pos:brace_pos + 500]
        if 'getDmlMessage' not in block_snippet and 'getNumDml' not in block_snippet:
            lineno = full_text[:start].count('\n') + 1
            issues.append(
                f"{path}:{lineno}: [DmlException incomplete logging] "
                f"catch (DmlException) block does not call getDmlMessage(i) or getNumDml(). "
                f"Per-row error details are lost. Add getDmlMessage(i) / getDmlIndex(i) logging."
            )
    return issues


def _scan_trigger_new_in_delete(lines: list[str], path: Path) -> list[str]:
    """Warn if a file references both Trigger.isDelete and Trigger.new[]."""
    full_text = ''.join(lines)
    if not _TRIGGER_IS_DELETE_RE.search(full_text):
        return []

    issues = []
    for lineno, line in enumerate(lines, start=1):
        if _TRIGGER_NEW_IN_DELETE_RE.search(line):
            issues.append(
                f"{path}:{lineno}: [NullPointerException risk in delete trigger] "
                f"File references Trigger.isDelete and Trigger.new[.] on this line — "
                f"Trigger.new is null on delete events. Use Trigger.old instead."
            )
    return issues


def _scan_list_index_without_guard(lines: list[str], path: Path) -> list[str]:
    """Heuristic: flag list[0] access not immediately preceded by an isEmpty() check."""
    issues = []
    for lineno, line in enumerate(lines, start=1):
        if _LIST_ZERO_INDEX_RE.search(line):
            # Check up to 3 preceding lines for an isEmpty guard
            preceding = lines[max(0, lineno - 4):lineno - 1]
            preceding_text = ' '.join(preceding)
            if not _IS_EMPTY_RE.search(preceding_text):
                issues.append(
                    f"{path}:{lineno}: [ListException / NullPointerException risk] "
                    f"List index [0] access without preceding isEmpty() guard. "
                    f"If the list is empty this throws ListException. "
                    f"Add 'if (!list.isEmpty())' or 'list.size() > 0' check before this line."
                )
    return issues


def check_apex_files(manifest_dir: Path) -> list[str]:
    """Scan all .cls files under manifest_dir for common runtime error patterns."""
    issues: list[str] = []

    cls_files = list(manifest_dir.rglob('*.cls'))
    if not cls_files:
        issues.append(
            f"No .cls files found under {manifest_dir}. "
            f"Provide the path to a Salesforce metadata classes directory."
        )
        return issues

    for cls_file in sorted(cls_files):
        try:
            lines = cls_file.read_text(encoding='utf-8', errors='replace').splitlines(keepends=True)
        except OSError as exc:
            issues.append(f"{cls_file}: Could not read file — {exc}")
            continue

        issues.extend(_scan_scalar_soql(lines, cls_file))
        issues.extend(_scan_catch_limit(lines, cls_file))
        issues.extend(_scan_soql_in_loop(lines, cls_file))
        issues.extend(_scan_dml_exception_catch(lines, cls_file))
        issues.extend(_scan_trigger_new_in_delete(lines, cls_file))
        issues.extend(_scan_list_index_without_guard(lines, cls_file))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Apex class files for common runtime error patterns: "
            "NullPointerException, QueryException, DmlException, "
            "ListException, LimitException."
        ),
    )
    parser.add_argument(
        '--manifest-dir',
        default='.',
        help='Root directory of the Salesforce metadata (default: current directory).',
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Print a one-line summary of issue counts grouped by exception type.',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ERROR: Manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 2

    issues = check_apex_files(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    if args.summary:
        # Group by exception type keyword in the message
        counts: dict[str, int] = {}
        for issue in issues:
            for key in ['NullPointerException', 'QueryException', 'DmlException',
                        'ListException', 'LimitException', 'TypeException']:
                if key in issue:
                    counts[key] = counts.get(key, 0) + 1
                    break
            else:
                counts['Other'] = counts.get('Other', 0) + 1
        print(f"Total issues: {len(issues)}")
        for exc_type, count in sorted(counts.items()):
            print(f"  {exc_type}: {count}")
    else:
        for issue in issues:
            print(f"ISSUE: {issue}")

    return 1


if __name__ == '__main__':
    sys.exit(main())
