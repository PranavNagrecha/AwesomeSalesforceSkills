#!/usr/bin/env python3
"""Heuristic checker for outbound webhook design documents.

Scans markdown design docs for the minimum sections and flags common
omissions (no signing, no idempotency, no retry, no DLQ).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "trigger",
    "mechanism",
    "payload",
    "signing",
    "retry",
    "dead-letter",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect outbound webhook design docs.",
    )
    parser.add_argument(
        "--docs-dir",
        default=".",
        help="Directory containing design markdown files.",
    )
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    if "hmac" not in text and "signature" not in text:
        issues.append(f"{path}: no signing mechanism documented")

    if "idempot" not in text:
        issues.append(f"{path}: no idempotency key on payload")

    if "5xx" not in text and "retry" in text and "429" not in text:
        issues.append(f"{path}: retry policy does not mention status-code scoping (5xx/408/429)")

    if "external credential" not in text and "secret" in text:
        issues.append(f"{path}: secret referenced but External Credential storage not specified")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No design docs found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("Webhook design docs look complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
