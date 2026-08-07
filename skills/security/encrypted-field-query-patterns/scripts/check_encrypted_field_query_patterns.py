#!/usr/bin/env python3
"""Heuristic checker for encryption schema plan documents."""

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
    parser.add_argument("--docs-dir", default=".")
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
    # field-level READ. Plaintext is gated by FLS, not by a permission.
    if "field-level security" not in text and "fls" not in text:
        issues.append(
            f"{path}: no field-level security (FLS) test — Shield plaintext "
            f"visibility is controlled by FLS, not by a permission"
        )

    # 'View Encrypted Data' is a Classic Encryption permission. Relying on it
    # in a Shield plan is a false sense of protection.
    if "view encrypted data" in text and "classic" not in text:
        issues.append(
            f"{path}: relies on 'View Encrypted Data' — that permission is "
            f"Classic Encryption only and does not mask Shield-encrypted "
            f"fields (unnecessary for Shield since Spring '17)"
        )

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No encryption plan docs found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("Encryption schema plan looks complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
