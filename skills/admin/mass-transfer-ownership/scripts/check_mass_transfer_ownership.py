#!/usr/bin/env python3
"""Pre-flight check for a mass-transfer plan CSV.

Validates a transfer plan CSV with columns Id, OldOwnerId, NewOwnerId. Flags:

- duplicate Id rows
- empty NewOwnerId values
- malformed Salesforce IDs (non-15/18-char or wrong prefix)
- mixing User (005) and Queue (00G) targets in one file (usually a bug)

Stdlib only.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ID_PREFIX_USER = "005"
ID_PREFIX_QUEUE = "00G"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate a mass-transfer plan CSV.")
    p.add_argument("--plan", default="transfer-plan.csv", help="Path to the transfer plan CSV.")
    return p.parse_args()


def is_sf_id(value: str) -> bool:
    return len(value) in (15, 18) and value.isalnum()


def main() -> int:
    args = parse_args()
    plan = Path(args.plan)
    if not plan.exists():
        print(f"[mass-transfer-ownership] plan file not found: {plan}", file=sys.stderr)
        return 1

    issues: list[str] = []
    seen_ids: set[str] = set()
    target_prefixes: set[str] = set()

    with plan.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for required in ("Id", "OldOwnerId", "NewOwnerId"):
            if required not in (reader.fieldnames or []):
                issues.append(f"missing required column: {required}")
        if issues:
            for issue in issues:
                print(f"WARN: {issue}", file=sys.stderr)
            return 1

        for i, row in enumerate(reader, start=2):
            rid = (row.get("Id") or "").strip()
            new_owner = (row.get("NewOwnerId") or "").strip()

            if not rid:
                issues.append(f"row {i}: empty Id")
                continue
            if rid in seen_ids:
                issues.append(f"row {i}: duplicate Id {rid}")
            seen_ids.add(rid)

            if not new_owner:
                issues.append(f"row {i}: empty NewOwnerId")
                continue
            if not is_sf_id(new_owner):
                issues.append(f"row {i}: malformed NewOwnerId {new_owner}")
                continue
            target_prefixes.add(new_owner[:3])

    if {ID_PREFIX_USER, ID_PREFIX_QUEUE}.issubset(target_prefixes):
        issues.append(
            "plan mixes User (005) and Queue (00G) targets — usually a mistake; split into two plans"
        )

    if not issues:
        print(f"[mass-transfer-ownership] plan OK ({len(seen_ids)} rows)")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
