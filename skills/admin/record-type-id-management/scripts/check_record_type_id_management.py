#!/usr/bin/env python3
"""Checker script for Record Type Id Management skill.

Scans Salesforce metadata for hard-coded record-type ID literals and other
anti-patterns documented in references/llm-anti-patterns.md.

Usage:
    python3 check_record_type_id_management.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


RT_ID_PAT = re.compile(r"['\"]012[A-Za-z0-9]{12,15}['\"]")
RECORDTYPE_NAME_PAT = re.compile(r"RecordType\.Name\s*=")
DOLLAR_RECORDTYPE_NAME_PAT = re.compile(r"\$RecordType\.Name")
STATIC_FINAL_ID_PAT = re.compile(r"static\s+final\s+Id\s+\w+\s*=\s*['\"]012[A-Za-z0-9]{12,15}['\"]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check metadata for record-type ID anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def iter_files(root: Path, suffixes: tuple[str, ...]):
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in suffixes:
            yield path


def check_hardcoded_ids(root: Path) -> list[str]:
    issues: list[str] = []
    for path in iter_files(root, (".cls", ".trigger", ".js")):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in RT_ID_PAT.finditer(text):
            line_no = text[: match.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: hard-coded record-type ID literal {match.group(0)}"
            )
    return issues


def check_static_final_rt(root: Path) -> list[str]:
    issues: list[str] = []
    for path in iter_files(root, (".cls", ".trigger")):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in STATIC_FINAL_ID_PAT.finditer(text):
            line_no = text[: match.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: static final Id initialised to literal ID; use lazy-init via Schema.describe"
            )
    return issues


def check_recordtype_name_refs(root: Path) -> list[str]:
    issues: list[str] = []
    for path in iter_files(root, (".cls", ".trigger", ".xml", ".flow-meta.xml", ".validationRule-meta.xml")):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if RECORDTYPE_NAME_PAT.search(text):
            issues.append(
                f"{path.relative_to(root)}: references RecordType.Name; prefer RecordType.DeveloperName"
            )
        if DOLLAR_RECORDTYPE_NAME_PAT.search(text):
            issues.append(
                f"{path.relative_to(root)}: references $RecordType.Name; prefer $RecordType.DeveloperName"
            )
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    issues: list[str] = []
    issues.extend(check_hardcoded_ids(root))
    issues.extend(check_static_final_rt(root))
    issues.extend(check_recordtype_name_refs(root))

    if not issues:
        print("No record-type ID anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
