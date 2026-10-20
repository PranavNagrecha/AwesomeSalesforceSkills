#!/usr/bin/env python3
"""Heuristic checker for encryption schema plan documents.

Contract: missing directory -> ERROR, exit 1. Empty directory -> one WARN, exit 0.
Plan findings are WARN -> exit 0 unless --strict (then exit 1).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "field inventory",
    "indexing",
    "test plan",
    "sign-off",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect encryption schema plans.")
    parser.add_argument("--docs-dir", "--manifest-dir", dest="docs_dir", default=".")
    parser.add_argument("--strict", action="store_true", help="exit 1 on WARN findings")
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    if "probabilistic" not in text and "deterministic" not in text:
        issues.append(f"{path}: no scheme mentioned (probabilistic/deterministic)")

    if "like" in text and "probabilistic" in text and "display" not in text:
        issues.append(f"{path}: probabilistic + LIKE combination flagged")

    if "index" not in text:
        issues.append(f"{path}: no indexing plan mentioned")

    # Shield Platform Encryption decrypts transparently for any user with
    # field-level READ (UNVERIFIED (2026-10-20): Trailhead wording, not in the
    # corpus), so the plan must test FLS read granted and removed.
    if "field-level security" not in text and "fls" not in text:
        issues.append(
            f"{path}: no field-level security (FLS) test — the plan never "
            f"tests a user with FLS read removed"
        )

    # 'View Encrypted Data' is documented for Classic Encryption (secguide 262
    # L2484-2486, L2548). Relying on it in a Shield plan leaves FLS untested.
    if "view encrypted data" in text and "classic" not in text:
        issues.append(
            f"{path}: relies on 'View Encrypted Data' — the guide documents that "
            f"permission for Classic Encryption (secguide 262 L2484-2486, L2548); "
            f"a Shield plan must test FLS instead (that it has no effect on "
            f"Shield is UNVERIFIED (2026-10-20): Help only)"
        )

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.is_dir():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print(f"WARN: no encryption plan docs (*.md) found under {root}")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("Encryption schema plan looks complete.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
