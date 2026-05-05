#!/usr/bin/env python3
"""Static checks for Approval Process Apex API anti-patterns.

Scans Apex source for the high-confidence anti-patterns documented in
this skill:

  1. `setProcessDefinitionNameOrId` called with a literal record-Id
     pattern (`300...`) — non-portable across orgs.
  2. `setAction` called with a lowercase / wrong-case string
     (`'approve'`, `'reject'`, `'removed'` instead of capitalized
     forms).
  3. `Approval.process(...)` calls in apparent bulk contexts (loops,
     batches) without `false` second arg (allOrNone).

Stdlib only.

Usage:
    python3 check_approval_process_apex_patterns.py --src-root .
    python3 check_approval_process_apex_patterns.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 1. setProcessDefinitionNameOrId with a literal Salesforce Id (Approval
# Process record Id keyPrefix is 300).
_HARDCODED_PROCESS_ID_RE = re.compile(
    r"setProcessDefinitionNameOrId\s*\(\s*['\"](300[a-zA-Z0-9]{12,18})['\"]\s*\)",
    re.IGNORECASE,
)

# 2. setAction with non-capitalized values
_BAD_ACTION_RE = re.compile(
    r"setAction\s*\(\s*['\"]"
    r"(approve|reject|removed|"  # lowercase
    r"APPROVE|REJECT|REMOVED|"   # uppercase
    r"Approved|Rejected)"        # past-tense, also wrong
    r"['\"]\s*\)"
)

# 3. Approval.process(...) without explicit allOrNone in bulk-shaped contexts.
_APPROVAL_PROCESS_SINGLE_ARG_RE = re.compile(
    r"Approval\.process\s*\(\s*\w+\s*\)",
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan_apex(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    # 1. Hardcoded process Id
    for m in _HARDCODED_PROCESS_ID_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: setProcessDefinitionNameOrId uses a "
            f"hardcoded record Id `{m.group(1)}` — non-portable across orgs (sandbox "
            "refresh produces a new Id). Use the approval process API name instead "
            "(references/llm-anti-patterns.md § 1)"
        )

    # 2. Bad action case
    for m in _BAD_ACTION_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: setAction(`{m.group(1)}`) — must be "
            "exactly `'Approve'`, `'Reject'`, or `'Removed'` (case-sensitive) "
            "(references/llm-anti-patterns.md § 5)"
        )

    # 3. Approval.process called with single arg in apparent bulk context
    # Heuristic: the file contains a `for` loop AND a single-arg Approval.process call.
    has_loop = bool(re.search(r"\bfor\s*\(", text))
    if has_loop:
        for m in _APPROVAL_PROCESS_SINGLE_ARG_RE.finditer(text):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: Approval.process(...) called with "
                "a single argument inside a file containing loops — defaults to "
                "`allOrNone=true` which rolls back the whole batch on first failure. "
                "Use `Approval.process(requests, false)` for bulk with per-row error "
                "handling (references/llm-anti-patterns.md § 2)"
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
            "Scan Apex sources for Approval Process API anti-patterns "
            "(hardcoded process Ids, wrong-case action strings, "
            "single-arg Approval.process in bulk contexts)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the Apex source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no Approval Process API anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
