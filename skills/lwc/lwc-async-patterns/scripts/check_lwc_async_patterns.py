#!/usr/bin/env python3
"""Checker for LWC Async Patterns skill.

Scans LWC .js files for:
- `await` on an imperative Apex import with no try block in the file
- `this.isLoading = true` in a file without a `finally` block
- `connectedCallback` that starts a timer/controller/subscription with no `disconnectedCallback`

Usage:
    python3 check_lwc_async_patterns.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


APEX_IMPORT = re.compile(r"import\s+(\w+)\s+from\s+['\"]@salesforce/apex/")
AWAIT_CALL = re.compile(r"await\s+(\w+)\s*\(")
TRY_BLOCK = re.compile(r"\btry\s*\{")
LOAD_TRUE = re.compile(r"this\.isLoading\s*=\s*true")
FINALLY_BLOCK = re.compile(r"\bfinally\s*\{")
CONNECTED = re.compile(r"connectedCallback\s*\(\s*\)\s*\{")
DISCONNECTED = re.compile(r"disconnectedCallback\s*\(\s*\)\s*\{")
SET_TIMER = re.compile(r"setInterval\s*\(|new\s+AbortController\s*\(|\bsubscribe\s*\(")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check LWC async anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def check_lwc(root: Path) -> list[str]:
    issues: list[str] = []
    lwc_dir = root / "lwc"
    if not lwc_dir.exists():
        return issues
    for path in lwc_dir.rglob("*.js"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        apex_names = set(APEX_IMPORT.findall(text))

        # 1. await on imperative Apex with no try block in the file
        if apex_names and not TRY_BLOCK.search(text):
            for m in AWAIT_CALL.finditer(text):
                if m.group(1) in apex_names:
                    line_no = text[: m.start()].count("\n") + 1
                    issues.append(
                        f"{path.relative_to(root)}:{line_no}: await on imperative Apex '{m.group(1)}' with no try/catch"
                    )
                    break

        # 2. isLoading = true without a finally block
        if LOAD_TRUE.search(text) and not FINALLY_BLOCK.search(text):
            m = LOAD_TRUE.search(text)
            line_no = text[: m.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: isLoading set true without `finally` — spinner may stick on error"
            )

        # 3. connectedCallback starts timer/subscription with no disconnectedCallback
        if CONNECTED.search(text) and SET_TIMER.search(text) and not DISCONNECTED.search(text):
            m = CONNECTED.search(text)
            line_no = text[: m.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: connectedCallback starts timer/subscription with no disconnectedCallback cleanup"
            )
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    issues = check_lwc(root)
    if not issues:
        print("No LWC async anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
