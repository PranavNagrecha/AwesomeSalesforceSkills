#!/usr/bin/env python3
"""Check DataRaptor Transform JSON for performance smells.

Flags:
- Transforms configured row-by-row on array inputs.
- Apex expressions used for pure string/arithmetic logic.
- Chains of adjacent Transforms in an IP with no intervening consumer.

Exit codes: 1 when --dr-dir does not exist; findings exit 0 unless --strict (then 1).
An empty directory prints one WARN and exits 0 (1 with --strict).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SIMPLE_APEX_MARKERS = (
    "StringUtils.concat",
    "String.format",
    ".toUpperCase()",
    ".toLowerCase()",
    ".trim()",
)


# json.dumps emits `"type": "Transform"` (with a space); exported files may not. Be tolerant.
_RE_TRANSFORM_TYPE = re.compile(r'"type"\s*:\s*"Transform"')
_RE_TRANSFORM_TYPE_KEY = re.compile(r'"transformType"')
_RE_IS_BULK_FALSE = re.compile(r'"isBulk"\s*:\s*false', re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect DataRaptor Transform JSON for optimization opportunities.",
    )
    parser.add_argument(
        "--dr-dir",
        default=".",
        help="Directory containing exported DataRaptor or Integration Procedure JSON files.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on any finding (and on an empty directory). Default: findings exit 0.",
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

    if _RE_TRANSFORM_TYPE.search(blob) or _RE_TRANSFORM_TYPE_KEY.search(blob):
        if _RE_IS_BULK_FALSE.search(blob):
            issues.append(
                f"{path}: Transform carries isBulk=false. A Data Mapper Transform has no documented "
                "bulk-mode setting to switch on (batch size applies to Data Mapper Load only; "
                "Gotcha 12) -- check instead whether the caller invokes it once per record rather "
                "than once per array (dataMapperInput is a List<String>)"
            )

    for marker in SIMPLE_APEX_MARKERS:
        if marker in blob:
            issues.append(
                f"{path}: Apex expression uses `{marker}` which is expressible as a formula"
            )

    transform_count = len(_RE_TRANSFORM_TYPE.findall(blob))
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
        print(f"WARN: no *.json files found under {root}; nothing to check.")
        return 1 if args.strict else 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("No DataRaptor Transform optimization issues found.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
