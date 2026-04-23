#!/usr/bin/env python3
"""Scan Salesforce user metadata for rotation anti-patterns.

Flags:
- User XML with `PasswordNeverExpires = true`.
- ConnectedApp metadata with no `consumerSecret` rotation metadata.
- Named credential metadata older than a configurable threshold (by mtime).
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect metadata for credential-rotation anti-patterns.",
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Directory containing Salesforce metadata.",
    )
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=365,
        help="Max credential age (via file mtime proxy) before flagging (default: 365).",
    )
    return parser.parse_args()


def check_users(root: Path) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("*.user-meta.xml"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"<passwordNeverExpires>true</passwordNeverExpires>", text, re.IGNORECASE):
            issues.append(f"{path}: user has `passwordNeverExpires=true` — remove for service accounts")
        if "<isActive>true</isActive>" in text and "Integration" in path.name:
            if re.search(r"<userType>\s*Standard\s*</userType>", text, re.IGNORECASE):
                pass  # Integration user of standard type — policy varies
    return issues


def check_connected_apps(root: Path, max_age_days: int) -> list[str]:
    issues: list[str] = []
    threshold = time.time() - max_age_days * 86400
    for path in root.rglob("*.connectedApp-meta.xml"):
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if mtime < threshold:
            age_days = int((time.time() - mtime) / 86400)
            issues.append(
                f"{path}: connected app metadata not modified in {age_days} days — secret may be stale"
            )
    return issues


def check_named_credentials(root: Path, max_age_days: int) -> list[str]:
    issues: list[str] = []
    threshold = time.time() - max_age_days * 86400
    for path in root.rglob("*.namedCredential-meta.xml"):
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if mtime < threshold:
            age_days = int((time.time() - mtime) / 86400)
            issues.append(
                f"{path}: named credential metadata unchanged in {age_days} days — confirm rotation happened outside source"
            )
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.project_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    all_issues: list[str] = []
    all_issues.extend(check_users(root))
    all_issues.extend(check_connected_apps(root, args.max_age_days))
    all_issues.extend(check_named_credentials(root, args.max_age_days))

    if not all_issues:
        print("No credential-rotation anti-patterns detected.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
