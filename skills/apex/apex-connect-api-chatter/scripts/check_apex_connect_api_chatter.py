#!/usr/bin/env python3
"""Checker for Apex ConnectApi (Chatter) usage.

Flags high-signal mistakes:

  1. FeedItem DML with `@` literal in Body (literal mention, won't notify).
  2. Hardcoded Network Id literal (`0DB...`) as ConnectApi argument.
  3. ConnectApi call in a @IsTest method with no `Test.setMock` earlier.
  4. ConnectApi call with no surrounding `try/catch (ConnectApi.ConnectApiException)`.
  5. ConnectApi call inside a `for` loop inside a trigger.
  6. `SeeAllData=true` near a ConnectApi call.

Stdlib only. Emits JSON.

Usage:
    python3 check_apex_connect_api_chatter.py --path force-app/main/default
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

FEEDITEM_DML_AT_LITERAL = re.compile(
    r"FeedItem\s*\([^)]*Body\s*=\s*'[^']*@",
    re.IGNORECASE,
)
HARDCODED_NETWORK_ID = re.compile(r"'(0DB[A-Za-z0-9]{12,15})'")
CONNECTAPI_CALL = re.compile(r"ConnectApi\.(ChatterFeeds|ChatterUsers|ChatterGroups|UserProfiles|Mentions)\.[A-Za-z]+\s*\(")
TEST_METHOD = re.compile(r"@IsTest\s*(?:\([^)]*\))?\s*(?:static\s+)?void\s+(\w+)", re.IGNORECASE)
SEE_ALL_DATA_TRUE = re.compile(r"SeeAllData\s*=\s*true", re.IGNORECASE)
FOR_LOOP = re.compile(r"\bfor\s*\(", re.IGNORECASE)
TRIGGER_HEAD = re.compile(r"\btrigger\s+\w+\s+on\s+\w+", re.IGNORECASE)
TEST_SETMOCK_CONNECTAPI = re.compile(
    r"Test\.setMock\s*\(\s*ConnectApi\.ConnectApi\.class",
    re.IGNORECASE,
)


def apex_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.cls"):
        yield path
    for path in root.rglob("*.trigger"):
        yield path


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def in_try_catch(text: str, offset: int) -> bool:
    preceding = text[:offset]
    last_try = preceding.rfind("try")
    if last_try == -1:
        return False
    # open-braces after the try
    depth = 0
    i = last_try
    # find opening brace after try
    while i < offset and text[i] != "{":
        i += 1
    if i >= offset:
        return False
    depth = 1
    i += 1
    while i < offset and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return depth > 0


def in_for_loop(text: str, offset: int) -> bool:
    preceding = text[:offset]
    starts = [m.start() for m in FOR_LOOP.finditer(preceding)]
    for s in reversed(starts):
        # count braces between this for's opening brace and offset
        after = text[s:offset]
        if "{" in after:
            brace_idx = after.index("{")
            body_start = s + brace_idx + 1
            depth = 1
            for ch in text[body_start:offset]:
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        break
            else:
                return True
    return False


def check_file(path: Path) -> list[dict]:
    issues: list[dict] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    is_trigger = path.suffix == ".trigger" or TRIGGER_HEAD.search(text) is not None
    is_test = "@IsTest" in text[:500] or path.name.endswith("_Test.cls")

    for m in FEEDITEM_DML_AT_LITERAL.finditer(text):
        issues.append(
            {
                "severity": "HIGH",
                "rule": "feeditem-dml-at-literal",
                "file": str(path),
                "line": line_of(text, m.start()),
                "message": (
                    "FeedItem DML Body contains '@' literal. "
                    "Use ConnectApi.MentionSegmentInput for a real mention."
                ),
            }
        )

    for m in HARDCODED_NETWORK_ID.finditer(text):
        # Only flag if this literal is used within 200 chars of a ConnectApi call.
        window = text[max(0, m.start() - 200) : m.end() + 200]
        if "ConnectApi." in window:
            issues.append(
                {
                    "severity": "MEDIUM",
                    "rule": "hardcoded-network-id",
                    "file": str(path),
                    "line": line_of(text, m.start()),
                    "message": (
                        f"Hardcoded network Id {m.group(1)!r} near ConnectApi call. "
                        "Use Network.getNetworkId()."
                    ),
                }
            )

    has_setmock = bool(TEST_SETMOCK_CONNECTAPI.search(text))
    see_all_data = bool(SEE_ALL_DATA_TRUE.search(text))

    for m in CONNECTAPI_CALL.finditer(text):
        if not in_try_catch(text, m.start()):
            issues.append(
                {
                    "severity": "MEDIUM",
                    "rule": "connectapi-no-try-catch",
                    "file": str(path),
                    "line": line_of(text, m.start()),
                    "message": (
                        "ConnectApi call without surrounding try/catch. "
                        "Chatter disabled or rate-limited causes hard failures."
                    ),
                }
            )

        if is_test and not has_setmock and not see_all_data:
            issues.append(
                {
                    "severity": "HIGH",
                    "rule": "connectapi-in-test-without-mock",
                    "file": str(path),
                    "line": line_of(text, m.start()),
                    "message": (
                        "ConnectApi call in a test class with no Test.setMock(ConnectApi.ConnectApi.class, ...). "
                        "The test will throw UnsupportedOperationException."
                    ),
                }
            )

        if is_test and see_all_data:
            issues.append(
                {
                    "severity": "MEDIUM",
                    "rule": "connectapi-with-seealldata",
                    "file": str(path),
                    "line": line_of(text, m.start()),
                    "message": (
                        "ConnectApi test uses SeeAllData=true. Prefer Test.setMock for deterministic tests."
                    ),
                }
            )

        if is_trigger and in_for_loop(text, m.start()):
            issues.append(
                {
                    "severity": "HIGH",
                    "rule": "connectapi-in-trigger-loop",
                    "file": str(path),
                    "line": line_of(text, m.start()),
                    "message": (
                        "ConnectApi call inside a for loop in a trigger. "
                        "Enqueue a Queueable and post from there instead."
                    ),
                }
            )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lint Apex ConnectApi / Chatter usage.")
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
