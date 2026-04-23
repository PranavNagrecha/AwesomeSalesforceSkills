#!/usr/bin/env python3
"""Checker for Apex code invoking Flows via Flow.Interview.

Flags high-signal mistakes:

  1. `Flow.Interview.createInterview` inside a `for`/`while` loop.
  2. `.start()` on a `Flow.Interview` without try/catch.
  3. `(Type) i.getVariableValue(...)` cast without null check.
  4. `createInterview` with a string literal (hardcoded Flow name) — flagged REVIEW.

Stdlib only. Emits JSON.

Usage:
    python3 check_apex_flow_invocation_from_apex.py --path force-app/main/default
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

CREATE_INTERVIEW = re.compile(
    r"Flow\.Interview\.createInterview\s*\(\s*('([^']+)'|[A-Za-z_][\w.]*)\s*,"
)
START_CALL = re.compile(r"\.start\s*\(\s*\)")
CAST_GET_VAR = re.compile(
    r"\((\w+(?:<[^>]+>)?)\)\s*\w+\.getVariableValue\s*\(\s*'[^']+'\s*\)"
)
LOOP_COMPILE_TEST = re.compile(
    r"(for\s*\([^\)]*\)|while\s*\([^\)]*\))[^{]*\{[^}]*Flow\.Interview\.createInterview",
    re.DOTALL,
)


def apex_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.cls"):
        if path.name.endswith("_Test.cls"):
            continue
        yield path
    for path in root.rglob("*.trigger"):
        yield path


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def check_file(path: Path) -> list[dict]:
    issues: list[dict] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    for m in LOOP_COMPILE_TEST.finditer(text):
        issues.append(
            {
                "severity": "HIGH",
                "rule": "flow-invocation-in-loop",
                "file": str(path),
                "line": line_of(text, m.start()),
                "message": (
                    "Flow.Interview.createInterview inside a loop. Redesign the Flow "
                    "to accept a collection input and invoke once."
                ),
            }
        )

    for m in CREATE_INTERVIEW.finditer(text):
        if m.group(2):
            issues.append(
                {
                    "severity": "REVIEW",
                    "rule": "hardcoded-flow-name",
                    "file": str(path),
                    "line": line_of(text, m.start()),
                    "message": (
                        f"Flow name {m.group(2)!r} is a string literal. Centralize "
                        "Flow names in a constants class or CMDT to catch typos."
                    ),
                }
            )
        end = m.end()
        window = text[end : end + 400]
        if START_CALL.search(window):
            preceding = text[max(0, m.start() - 300) : m.start()]
            if "try" not in preceding and "try" not in window[: window.find(".start")]:
                issues.append(
                    {
                        "severity": "MEDIUM",
                        "rule": "start-without-try-catch",
                        "file": str(path),
                        "line": line_of(text, m.start()),
                        "message": (
                            "Flow.Interview.start() without an enclosing try/catch. "
                            "Flow failures otherwise abort the calling transaction."
                        ),
                    }
                )

    for m in CAST_GET_VAR.finditer(text):
        window = text[max(0, m.start() - 160) : m.start()]
        if "null" not in window and "?" not in window:
            issues.append(
                {
                    "severity": "MEDIUM",
                    "rule": "cast-without-null-check",
                    "file": str(path),
                    "line": line_of(text, m.start()),
                    "message": (
                        f"({m.group(1)}) getVariableValue(...) cast without null check. "
                        "Missing output variables or typos return null."
                    ),
                }
            )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lint Apex Flow invocation patterns.")
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
