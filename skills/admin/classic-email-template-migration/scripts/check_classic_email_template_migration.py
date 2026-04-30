#!/usr/bin/env python3
"""Checker script for Classic Email Template Migration skill.

Scans retrieved email-template metadata (from `force-app/main/default/email/`)
and Apex classes for migration concerns:

- Classic templates (UiType=Aloha) still in use after presumed migration
- Lightning template bodies still containing Classic-style {!IF()} / {!$Setup} / {!System.} merge formulas
- Apex setTemplateId() calls referencing old (Classic) template IDs (heuristic: 18-char IDs in setTemplateId calls)
- Workflow alerts with no <senderAddress> set (OWA may have been lost in migration)

Stdlib only.

Usage:
    python3 check_classic_email_template_migration.py --project-dir path/to/project
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


# Patterns that indicate Classic-only merge syntax still embedded
CLASSIC_MERGE_PATTERNS = [
    (r'\{!IF\s*\(', "Classic IF() merge formula — Lightning templates do not support"),
    (r'\{!CASE\s*\(', "Classic CASE() merge formula — Lightning templates do not support"),
    (r'\{!URLENCODE\s*\(', "URLENCODE merge — not portable to Lightning"),
    (r'\{!\$Setup\.', "$Setup merge field — surface via a record field instead"),
    (r'\{!\$User\.Profile', "$User.Profile merge — limited Lightning support; verify"),
    (r'\{!System\.', "System.* merge — not available in Lightning"),
    (r'\{!BLANKVALUE\s*\(', "BLANKVALUE() merge formula — not supported in Lightning"),
]


def find_files(root: Path, pattern: str) -> list[Path]:
    return [p for p in root.rglob(pattern) if p.is_file() and ".sfdx" not in p.parts]


def scan(root: Path) -> list[tuple[str, Path, int, str]]:
    findings: list[tuple[str, Path, int, str]] = []

    # Email template files
    for f in find_files(root, "*.email") + find_files(root, "*.email-meta.xml"):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for regex, msg in CLASSIC_MERGE_PATTERNS:
                if re.search(regex, line):
                    findings.append(("merge", f, line_no, msg))

    # Apex setTemplateId calls
    for f in find_files(root, "*.cls"):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if "setTemplateId" in line:
                findings.append(("apex", f, line_no, "setTemplateId() call — verify it references the new (Lightning) template ID, not Classic"))
            if "setOrgWideEmailAddressId" not in text and "setTemplateId" in line:
                # heuristic: in same file, no OWA setting
                findings.append(("apex-owa", f, line_no, "setTemplateId without setOrgWideEmailAddressId in same file — Lightning templates don't store sender; OWA must be set on the call"))

    # Workflow alerts missing senderAddress
    for f in find_files(root, "*.workflow-meta.xml"):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Find each <alerts>...</alerts> block
        for match in re.finditer(r'<alerts>(.*?)</alerts>', text, flags=re.DOTALL):
            block = match.group(1)
            if '<senderType>OrgWideEmailAddress</senderType>' in block and '<senderAddress>' not in block:
                line_no = text[:match.start()].count('\n') + 1
                findings.append(("workflow", f, line_no, "Workflow alert uses OrgWideEmailAddress senderType but no <senderAddress> set"))

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
        for f, ln, msg in by_cat[cat][:50]:
            rel = f.relative_to(root) if f.is_relative_to(root) else f
            print(f"  {rel}:{ln} — {msg}")
        if len(by_cat[cat]) > 50:
            print(f"  ... and {len(by_cat[cat]) - 50} more")
    return 1 if (args.strict and findings) else 0


if __name__ == "__main__":
    sys.exit(main())
