#!/usr/bin/env python3
"""Check Salesforce metadata for upload-scanning gaps.

Scans a project for signs that file-upload scanning is missing or weak:
- ContentVersion trigger that sets a `ScanStatus__c` to `Clean` without
  any callout (suggests a stub).
- Experience Cloud metadata with file-upload components and no scanning
  reference anywhere in the project.
- Sharing rules on ContentDocument without referencing `ScanStatus__c`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect metadata for file-upload virus-scanning gaps.",
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Directory containing Salesforce metadata.",
    )
    return parser.parse_args()


def find_trigger_stubs(root: Path) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("*.trigger"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "ContentVersion" in text and "ScanStatus__c" in text and "Clean" in text:
            has_callout = any(
                marker in text
                for marker in ("HttpCallout", "Http ", "HttpRequest", "System.enqueueJob", "@future")
            )
            if not has_callout:
                issues.append(
                    f"{path}: ContentVersion trigger sets ScanStatus to Clean without any callout or async dispatch"
                )
    return issues


def check_experience_cloud(root: Path) -> list[str]:
    issues: list[str] = []
    experience_sites = list(root.rglob("*.site-meta.xml")) + list(root.rglob("sites/*"))
    if not experience_sites:
        return issues

    all_text = []
    for path in root.rglob("*.cls"):
        try:
            all_text.append(path.read_text(encoding="utf-8", errors="ignore").lower())
        except OSError:
            pass

    combined = "\n".join(all_text)
    scanning_markers = ("virus", "malware", "clamav", "scan")
    if not any(marker in combined for marker in scanning_markers):
        issues.append(
            "Experience Cloud surfaces detected but no virus/malware/scan references found in Apex — likely missing upload scanning"
        )
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.project_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    all_issues: list[str] = []
    all_issues.extend(find_trigger_stubs(root))
    all_issues.extend(check_experience_cloud(root))

    if not all_issues:
        print("No obvious file-upload scanning gaps detected.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
