#!/usr/bin/env python3
"""Heuristic checker for Apex-Defined Type classes used by Flow.

Findings print as `WARN:` lines and exit 0; `--strict` exits 1 on any finding.
No .cls files prints one WARN line (exit 0, 1 with --strict). A missing
directory prints ERROR and exits 1.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


AURA = re.compile(r"@AuraEnabled")
PUBLIC_FIELD = re.compile(r"^\s*public\s+[A-Za-z0-9_<>,\s]+\s+\w+\s*;", re.MULTILINE)
MAP_FIELD = re.compile(r"Map<\s*[A-Za-z]+\s*,")
REQUIRED_CTOR = re.compile(r"public\s+\w+\s*\([^)]+\)\s*{", re.MULTILINE)
CLASS_DECL = re.compile(r"public\s+class\s+\w+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan Apex-Defined Types for Flow.")
    parser.add_argument("--src-dir", "--manifest-dir", dest="src_dir", default=".",
                        help="Root directory of Apex classes to scan (--manifest-dir is an alias).")
    parser.add_argument("--strict", action="store_true",
                        help="Exit 1 when any finding (or the empty-directory WARN) is reported.")
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")

    if not CLASS_DECL.search(text):
        return issues

    fields = PUBLIC_FIELD.findall(text)
    auras = AURA.findall(text)

    if fields and len(auras) < len(fields):
        issues.append(
            f"{path}: {len(fields)} public fields but only {len(auras)} @AuraEnabled annotations"
        )

    if MAP_FIELD.search(text):
        issues.append(f"{path}: Map<> field — Flow cannot bind; use List<KeyValue>")

    for match in REQUIRED_CTOR.finditer(text):
        snippet = match.group(0)
        if "()" not in snippet:
            issues.append(f"{path}: constructor with args — Flow cannot instantiate")
            break

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.src_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")  # missing path: ERROR, exit 1
        return 1

    targets = list(root.rglob("*.cls"))
    if not targets:
        print(f"WARN: no .cls files found under {root}")
        return 1 if args.strict else 0

    issues: list[str] = []
    for path in targets:
        issues.extend(check_file(path))

    if not issues:
        print("Apex-Defined Type scan clean.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
