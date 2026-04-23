#!/usr/bin/env python3
"""Checker for Apex user and permission check usage.

Flags high-signal mistakes:

  1. Profile.Name string equality checks.
  2. `FeatureManagement.checkPermission` inside async execute blocks.
  3. `checkPermission` result stored in a class-level `static final` field.
  4. `UserInfo.getUserType()` compared to a string literal (should be the enum).
  5. `System.runAs(UserInfo.getUserId())` inside a test method.

Stdlib only. Emits JSON.

Usage:
    python3 check_apex_user_and_permission_checks.py --path force-app/main/default
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

PROFILE_NAME_CHECK = re.compile(
    r"Profile\.Name\s*==\s*'([^']+)'"
)
CHECK_PERMISSION = re.compile(r"FeatureManagement\.checkPermission\s*\(\s*'([^']+)'\s*\)")
STATIC_FINAL_PERM = re.compile(
    r"static\s+final\s+Boolean\s+\w+\s*=\s*FeatureManagement\.checkPermission\s*\("
)
USERTYPE_STRING_EQ = re.compile(
    r"UserInfo\.getUserType\s*\(\s*\)\s*==\s*'([^']+)'"
)
RUNAS_SELF = re.compile(
    r"System\.runAs\s*\(\s*(?:new\s+User\s*\(\s*Id\s*=\s*)?UserInfo\.getUserId\s*\(\s*\)"
)
ASYNC_EXECUTE = re.compile(
    r"public\s+void\s+execute\s*\(\s*(?:QueueableContext|Database\.BatchableContext|SchedulableContext)",
    re.IGNORECASE,
)
FUTURE_METHOD = re.compile(r"@future\b", re.IGNORECASE)


def apex_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.cls"):
        yield path
    for path in root.rglob("*.trigger"):
        yield path


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def in_async_block(text: str, offset: int) -> bool:
    preceding = text[:offset]
    async_markers = list(ASYNC_EXECUTE.finditer(preceding)) + list(
        FUTURE_METHOD.finditer(preceding)
    )
    if not async_markers:
        return False
    last = async_markers[-1]
    open_braces = preceding.count("{", last.end())
    close_braces = preceding.count("}", last.end())
    return open_braces > close_braces


def check_file(path: Path) -> list[dict]:
    issues: list[dict] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    is_test = path.name.endswith("_Test.cls") or "@IsTest" in text[:500]

    for m in PROFILE_NAME_CHECK.finditer(text):
        issues.append(
            {
                "severity": "HIGH",
                "rule": "profile-name-string-check",
                "file": str(path),
                "line": line_of(text, m.start()),
                "message": (
                    f"Profile.Name compared to {m.group(1)!r}. "
                    "Use FeatureManagement.checkPermission('CustomPerm') instead."
                ),
            }
        )

    for m in CHECK_PERMISSION.finditer(text):
        if in_async_block(text, m.start()):
            issues.append(
                {
                    "severity": "HIGH",
                    "rule": "checkpermission-in-async",
                    "file": str(path),
                    "line": line_of(text, m.start()),
                    "message": (
                        f"FeatureManagement.checkPermission({m.group(1)!r}) inside an async "
                        "execute/@future block checks the async context user, not the originator."
                    ),
                }
            )

    for m in STATIC_FINAL_PERM.finditer(text):
        issues.append(
            {
                "severity": "MEDIUM",
                "rule": "static-cached-permission",
                "file": str(path),
                "line": line_of(text, m.start()),
                "message": (
                    "checkPermission result cached in a static final field. "
                    "Admins can re-grant permissions at any time; check at the decision site."
                ),
            }
        )

    for m in USERTYPE_STRING_EQ.finditer(text):
        issues.append(
            {
                "severity": "MEDIUM",
                "rule": "usertype-string-compare",
                "file": str(path),
                "line": line_of(text, m.start()),
                "message": (
                    f"UserInfo.getUserType() == {m.group(1)!r}. Compare to the "
                    "UserType enum (e.g., UserType.Standard) instead."
                ),
            }
        )

    if is_test:
        for m in RUNAS_SELF.finditer(text):
            issues.append(
                {
                    "severity": "MEDIUM",
                    "rule": "runas-self-in-test",
                    "file": str(path),
                    "line": line_of(text, m.start()),
                    "message": (
                        "System.runAs(UserInfo.getUserId()) runs as the test runner "
                        "(usually admin), masking permission bugs. Use a low-priv test user."
                    ),
                }
            )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lint Apex user/permission checks.")
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
