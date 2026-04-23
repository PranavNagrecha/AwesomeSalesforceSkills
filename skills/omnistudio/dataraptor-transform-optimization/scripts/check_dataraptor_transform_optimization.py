#!/usr/bin/env python3
"""Check DataRaptor Transform JSON for performance smells.

Flags:
- Transforms configured row-by-row on array inputs.
- Apex expressions used for pure string/arithmetic logic.
- Chains of adjacent Transforms in an IP with no intervening consumer.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SIMPLE_APEX_MARKERS = (
    "StringUtils.concat",
    "String.format",
    ".toUpperCase()",
    ".toLowerCase()",
    ".trim()",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect DataRaptor Transform JSON for optimization opportunities.",
    )
    parser.add_argument(
        "--dr-dir",
        default=".",
        help="Directory containing exported DataRaptor or Integration Procedure JSON files.",
    )
    return parser.parse_args()


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    data = load_json(path)
    if data is None:
        return [f"{path}: could not parse JSON"]

    blob = json.dumps(data)

    if '"type":"Transform"' in blob or '"transformType"' in blob:
        if '"isBulk":false' in blob.lower().replace(" ", ""):
            issues.append(
                f"{path}: Transform configured row-by-row; switch to bulk mode for array inputs"
            )

    for marker in SIMPLE_APEX_MARKERS:
        if marker in blob:
            issues.append(
                f"{path}: Apex expression uses `{marker}` which is expressible as a formula"
            )

    transform_count = blob.count('"type":"Transform"')
    if transform_count >= 3:
        issues.append(
            f"{path}: {transform_count} Transform steps — review for merge opportunities"
        )

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.dr_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.json"))
    if not targets:
        print("No JSON files found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("No DataRaptor Transform optimization issues found.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
