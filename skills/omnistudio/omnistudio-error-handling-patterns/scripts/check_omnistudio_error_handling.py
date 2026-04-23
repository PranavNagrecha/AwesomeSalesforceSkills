#!/usr/bin/env python3
"""Check Integration Procedure JSON for error-handling smells.

Scans exported IP definitions for:
- Write-like steps (record/update, record/create, HTTP POST/PUT/PATCH)
  with `failOnStepError = false` or missing.
- Retry-enabled HTTP actions with no correlation ID in the payload.
- Steps whose `Response Action` is set to `Continue on Error` on a
  record-mutation step (usually unsafe).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


WRITE_MARKERS = ("record/update", "record/create", "record/upsert", "post", "put", "patch")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect Integration Procedure JSON for error-handling misconfiguration.",
    )
    parser.add_argument(
        "--ip-dir",
        default=".",
        help="Directory containing exported Integration Procedure JSON files.",
    )
    return parser.parse_args()


def iter_steps(node):
    if isinstance(node, dict):
        if "type" in node and "name" in node:
            yield node
        for value in node.values():
            yield from iter_steps(value)
    elif isinstance(node, list):
        for item in node:
            yield from iter_steps(item)


def is_write_step(step: dict) -> bool:
    blob = json.dumps(step).lower()
    return any(marker in blob for marker in WRITE_MARKERS)


def has_correlation_id(step: dict) -> bool:
    blob = json.dumps(step).lower()
    return "correlationid" in blob or "correlation_id" in blob or "idempotencykey" in blob


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [f"{path}: could not parse JSON"]

    for step in iter_steps(data):
        name = step.get("name", "?")
        if is_write_step(step):
            if not step.get("failOnStepError", False):
                issues.append(
                    f"{path}:{name}: write-like step has `failOnStepError` unset or false"
                )
            if step.get("responseAction", "").lower() == "continue on error":
                issues.append(
                    f"{path}:{name}: write-like step configured `Continue on Error`"
                )
            if step.get("retryEnabled") and not has_correlation_id(step):
                issues.append(
                    f"{path}:{name}: retry enabled without correlation ID in payload"
                )

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.ip_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.json"))
    if not targets:
        print("No IP JSON files found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("No IP error-handling issues found.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
