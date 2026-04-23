#!/usr/bin/env python3
"""Checker for Apex usage of Hierarchy Custom Settings.

Flags the high-signal mistakes from references/llm-anti-patterns.md:

  1. `getInstance()` result compared to `null` (never null for Hierarchy CS).
  2. Custom Setting insert/upsert inside a `for`/`while` loop.
  3. SOQL against an object that is likely a Custom Setting (inferred by
     `__c` suffix + `.getInstance`/`.getOrgDefaults` usage elsewhere).
  4. `getOrgDefaults()` used without a comment justifying the bypass of
     per-user/per-profile hierarchy.

Stdlib only. Emits JSON for scoring.

Usage:
    python3 check_apex_custom_settings_hierarchy.py --path force-app/main/default
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

GET_INSTANCE_CALL = re.compile(
    r"(\w+__c)\.getInstance\s*\([^)]*\)"
)
GET_INSTANCE_NULL_CHECK = re.compile(
    r"(\w+__c)\.getInstance\s*\([^)]*\)\s*(?:==|!=)\s*null"
)
GET_ORG_DEFAULTS = re.compile(r"(\w+__c)\.getOrgDefaults\s*\(\s*\)")
CS_INSERT_IN_LOOP = re.compile(
    r"(for\s*\([^\)]*\)|while\s*\([^\)]*\))[^{]*\{(?:[^{}]|\{[^{}]*\})*?\b(?:insert|upsert|update)\s+new\s+\w+__c",
    re.DOTALL,
)
SOQL_FROM = re.compile(r"\[\s*SELECT\s+[^\]]+?FROM\s+(\w+__c)", re.IGNORECASE | re.DOTALL)


def apex_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.cls"):
        if path.name.endswith("_Test.cls"):
            continue
        yield path
    for path in root.rglob("*.trigger"):
        yield path


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def custom_setting_candidates(root: Path) -> set[str]:
    candidates: set[str] = set()
    for path in root.rglob("*.object-meta.xml"):
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "<customSettingsType>" in content:
            candidates.add(path.stem.replace(".object-meta", ""))
    return candidates


def check_file(path: Path, cs_candidates: set[str]) -> list[dict]:
    issues: list[dict] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    for m in GET_INSTANCE_NULL_CHECK.finditer(text):
        issues.append(
            {
                "severity": "HIGH",
                "rule": "get-instance-null-compare",
                "file": str(path),
                "line": line_of(text, m.start()),
                "message": (
                    f"{m.group(1)}.getInstance() is compared to null. Hierarchy "
                    "Custom Settings `getInstance()` always returns a non-null record — "
                    "null-check the field instead."
                ),
            }
        )

    for m in GET_ORG_DEFAULTS.finditer(text):
        window_start = max(0, m.start() - 120)
        window = text[window_start : m.start()]
        if "//" not in window and "/*" not in window:
            issues.append(
                {
                    "severity": "MEDIUM",
                    "rule": "get-org-defaults-without-justification",
                    "file": str(path),
                    "line": line_of(text, m.start()),
                    "message": (
                        f"{m.group(1)}.getOrgDefaults() skips per-user/per-profile overrides. "
                        "Prefer getInstance() unless you have a documented reason."
                    ),
                }
            )

    for m in CS_INSERT_IN_LOOP.finditer(text):
        issues.append(
            {
                "severity": "HIGH",
                "rule": "custom-setting-dml-in-loop",
                "file": str(path),
                "line": line_of(text, m.start()),
                "message": (
                    "Custom Setting DML inside a loop. Accumulate rows and "
                    "`upsert rows SetupOwnerId` in one statement."
                ),
            }
        )

    for m in SOQL_FROM.finditer(text):
        obj = m.group(1)
        if obj in cs_candidates:
            issues.append(
                {
                    "severity": "MEDIUM",
                    "rule": "soql-on-custom-setting",
                    "file": str(path),
                    "line": line_of(text, m.start()),
                    "message": (
                        f"SOQL against Custom Setting {obj} — prefer "
                        f"{obj}.getInstance() / getOrgDefaults() which consume no SOQL."
                    ),
                }
            )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint Apex usage of Hierarchy Custom Settings."
    )
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

    cs_candidates = custom_setting_candidates(root)
    issues: list[dict] = []
    for apex_path in apex_files(root):
        issues.extend(check_file(apex_path, cs_candidates))

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
