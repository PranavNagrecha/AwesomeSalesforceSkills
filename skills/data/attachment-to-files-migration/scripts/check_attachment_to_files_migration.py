#!/usr/bin/env python3
"""Checker script for Attachment to Files Migration skill.

Scans a Salesforce project for common migration anti-patterns:

- Apex querying Attachment.Body without batch context (heap risk)
- Apex inserting ContentDocument directly (unsupported)
- Apex setting both FirstPublishLocationId and explicit ContentDocumentLink (duplicate links)
- Apex inserting ContentVersion without Source_Attachment_Id__c (no idempotency)
- Apex calling delete on Attachment in same transaction as ContentVersion insert (no soak window)
- Apex inserting ContentNote without HTML wrapping (renders as one line)

Stdlib only.

Usage:
    python3 check_attachment_to_files_migration.py --project-dir path/to/project
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--project-dir", type=Path, default=Path.cwd())
    p.add_argument("--strict", action="store_true")
    return p.parse_args()


CHECKS = [
    ("heap", r'SELECT[^;]*\bBody\b[^;]*FROM\s+Attachment', "SOQL on Attachment.Body — confirm running inside Batch Apex with small scope (heap risk)"),
    ("model", r'\binsert\s+\w*\s*new\s+ContentDocument\s*\(', "Direct ContentDocument insert is not supported — insert ContentVersion; ContentDocument is auto-created"),
    ("model", r'FirstPublishLocationId', "FirstPublishLocationId set — verify you do NOT also insert an explicit ContentDocumentLink for the same parent (duplicate links)"),
    ("idempotency", r'new\s+ContentVersion\s*\([^)]*\)', "ContentVersion construction — verify Source_Attachment_Id__c is set for idempotent re-runs"),
    ("safety", r'delete\s+\w+;.*insert\s+.*ContentVersion', "Delete and insert in same code block — cleanup should be a separate gated batch"),
    ("notes", r'new\s+ContentNote\s*\([^)]*Content\s*=\s*Blob\.valueOf\s*\(\s*[^<\']', "ContentNote.Content set without HTML wrapping — body must be `<p>...</p>` with escaped/<br> conversion"),
    ("apex", r'@AuraEnabled\s*\(\s*cacheable\s*=\s*true\s*\)', "Cacheable @AuraEnabled — verify NO DML; otherwise migration code throws at runtime"),
]


def scan(root: Path) -> list[tuple[str, Path, int, str]]:
    findings: list[tuple[str, Path, int, str]] = []
    cls_files = [p for p in root.rglob("*.cls") if p.is_file() and ".sfdx" not in p.parts]
    for f in cls_files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for cat, regex, msg in CHECKS:
                if re.search(regex, line, flags=re.IGNORECASE):
                    findings.append((cat, f, line_no, msg))
    return findings


def main() -> int:
    args = parse_args()
    root = args.project_dir.resolve()
    if not root.exists():
        print(f"ERROR: project dir not found: {root}", file=sys.stderr)
        return 2
    findings = scan(root)
    print(f"Scanned: {root}")
    print(f"Findings: {len(findings)}")
    by_cat: dict[str, list] = {}
    for cat, f, ln, msg in findings:
        by_cat.setdefault(cat, []).append((f, ln, msg))
    for cat in sorted(by_cat):
        print(f"\n=== {cat} ({len(by_cat[cat])}) ===")
        for f, ln, msg in by_cat[cat]:
            rel = f.relative_to(root) if f.is_relative_to(root) else f
            print(f"  {rel}:{ln} — {msg}")
    return 1 if (args.strict and findings) else 0


if __name__ == "__main__":
    sys.exit(main())
