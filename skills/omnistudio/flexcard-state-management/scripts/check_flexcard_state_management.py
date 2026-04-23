#!/usr/bin/env python3
"""Check FlexCard metadata for common state-management pitfalls.

Scans OmniStudio FlexCard definitions (JSON exported from the designer or
sObject records) for patterns that correlate with state bugs:
- Generic pubsub event names ("refresh", "update") — collision risk.
- `Reload Card` action used after a record mutation — likely overkill.
- Conditional visibility bound to a field that does not appear in the
  data source projection JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


GENERIC_EVENTS = {"refresh", "update", "reload", "change"}
RISKY_ACTIONS = {"Reload Card"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect FlexCard JSON for state-management smells.",
    )
    parser.add_argument(
        "--flexcard-dir",
        default=".",
        help="Directory containing exported FlexCard JSON files.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    data = load_json(path)
    if data is None:
        return [f"{path}: could not parse JSON"]

    text = json.dumps(data).lower()

    for event in GENERIC_EVENTS:
        needle = f'"eventname":"{event}"'
        if needle in text:
            issues.append(
                f"{path}: pubsub event name `{event}` is too generic; namespace it (e.g. `accountSummary.{event}`)"
            )

    for action in RISKY_ACTIONS:
        if action.lower() in text and ("record/update" in text or "record/create" in text):
            issues.append(
                f"{path}: `{action}` used after a Record/Update or Record/Create; consider `Refresh Card Data` instead"
            )

    conditional_visibility = []
    projection = set()

    def walk(node):
        if isinstance(node, dict):
            if "conditionalVisibility" in node and isinstance(node["conditionalVisibility"], (str, dict)):
                conditional_visibility.append(str(node["conditionalVisibility"]))
            if "fieldApiName" in node and isinstance(node["fieldApiName"], str):
                projection.add(node["fieldApiName"].lower())
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)

    for rule in conditional_visibility:
        for token in rule.replace("{", " ").replace("}", " ").replace(".", " ").split():
            if token.endswith("__c") and token.lower() not in projection and token.lower() not in text:
                issues.append(
                    f"{path}: conditional visibility references `{token}` which is not in the data source projection"
                )
                break

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.flexcard_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.json"))
    if not targets:
        print("No FlexCard JSON files found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("No FlexCard state-management issues found.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
