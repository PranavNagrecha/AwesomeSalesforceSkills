#!/usr/bin/env python3
"""Checker for Apex usage of Messaging.CustomNotification.

Flags high-signal mistakes:

  1. `setNotificationTypeId` called with a string literal Id.
  2. `Messaging.CustomNotification` used in a trigger without a Queueable hand-off.
  3. `send(...)` without try/catch.
  4. Missing `setTargetId` on a configured notification.
  5. SOQL on `CustomNotificationType` inside a loop.

Stdlib only. Emits JSON for scoring.

Usage:
    python3 check_apex_custom_notifications_from_apex.py --path force-app/main/default
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

LITERAL_TYPE_ID = re.compile(
    r"setNotificationTypeId\s*\(\s*'([0-9A-Za-z]{15,18})'\s*\)"
)
NEW_NOTIFICATION = re.compile(r"new\s+Messaging\.CustomNotification\s*\(\s*\)")
SEND_CALL = re.compile(r"\.send\s*\([^)]*\)")
SET_TARGET_ID = re.compile(r"\.setTargetId\s*\(")
SOQL_TYPE = re.compile(
    r"\[\s*SELECT[^\]]*FROM\s+CustomNotificationType[^\]]*\]",
    re.IGNORECASE | re.DOTALL,
)
LOOP_OPEN = re.compile(r"(for\s*\([^\)]*\)|while\s*\([^\)]*\))\s*\{")


def apex_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.cls"):
        if path.name.endswith("_Test.cls"):
            continue
        yield path
    for path in root.rglob("*.trigger"):
        yield path


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def inside_loop(text: str, offset: int) -> bool:
    depth = 0
    for m in re.finditer(r"\{|\}|for\s*\(|while\s*\(", text[:offset]):
        token = m.group(0)
        if token.startswith("for") or token.startswith("while"):
            depth += 1
        elif token == "{":
            pass
        elif token == "}":
            if depth > 0:
                depth -= 1
    return depth > 0


def check_file(path: Path) -> list[dict]:
    issues: list[dict] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    for m in LITERAL_TYPE_ID.finditer(text):
        issues.append(
            {
                "severity": "HIGH",
                "rule": "hardcoded-notification-type-id",
                "file": str(path),
                "line": line_of(text, m.start()),
                "message": (
                    f"setNotificationTypeId uses string literal {m.group(1)!r}. "
                    "Custom Notification Type Ids are org-specific — resolve by DeveloperName."
                ),
            }
        )

    if path.suffix == ".trigger" and NEW_NOTIFICATION.search(text):
        issues.append(
            {
                "severity": "HIGH",
                "rule": "sync-notification-in-trigger",
                "file": str(path),
                "line": line_of(text, NEW_NOTIFICATION.search(text).start()),
                "message": (
                    "Messaging.CustomNotification constructed directly inside a trigger. "
                    "Delegate to a Queueable so send() failures do not abort the DML."
                ),
            }
        )

    for m in NEW_NOTIFICATION.finditer(text):
        block_end = min(len(text), m.end() + 600)
        block = text[m.end() : block_end]
        if not SET_TARGET_ID.search(block):
            issues.append(
                {
                    "severity": "MEDIUM",
                    "rule": "missing-set-target-id",
                    "file": str(path),
                    "line": line_of(text, m.start()),
                    "message": (
                        "Messaging.CustomNotification configured without setTargetId. "
                        "The bell click will land on the home page with no context."
                    ),
                }
            )

    for m in SEND_CALL.finditer(text):
        window_start = max(0, m.start() - 200)
        if "Messaging.CustomNotification" not in text[window_start : m.end() + 100]:
            continue
        following = text[m.end() : m.end() + 120]
        preceding = text[max(0, m.start() - 200) : m.start()]
        if "try" not in preceding and "catch" not in following:
            issues.append(
                {
                    "severity": "MEDIUM",
                    "rule": "send-without-try-catch",
                    "file": str(path),
                    "line": line_of(text, m.start()),
                    "message": (
                        "CustomNotification.send() without try/catch. "
                        "Platform failures otherwise abort the enclosing DML."
                    ),
                }
            )

    for m in SOQL_TYPE.finditer(text):
        if inside_loop(text, m.start()):
            issues.append(
                {
                    "severity": "MEDIUM",
                    "rule": "notification-type-soql-in-loop",
                    "file": str(path),
                    "line": line_of(text, m.start()),
                    "message": (
                        "CustomNotificationType queried inside a loop. Hoist to "
                        "class scope or query once before the loop."
                    ),
                }
            )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lint Apex Custom Notification usage.")
    parser.add_argument(
        "--path",
        default="force-app/main/default",
        help="Root directory to scan (default: force-app/main/default).",
    )
    parser.add_argument("--format", choices=["json", "text"], default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.path)
    if not root.exists():
        print(json.dumps({"error": f"path not found: {root}"}))
        return 2

    issues: list[dict] = []
    for apex_path in apex_files(root):
        issues.extend(check_file(apex_path))

    score = sum(SEVERITY_WEIGHTS.get(i["severity"], 0) for i in issues)

    if args.format == "json":
        print(json.dumps({"score": score, "issues": issues}, indent=2))
    else:
        for issue in issues:
            print(
                f"{issue['severity']:8} {issue['file']}:{issue['line']}  "
                f"[{issue['rule']}] {issue['message']}"
            )
        print(f"\nTotal weighted score: {score}")

    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
