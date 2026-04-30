#!/usr/bin/env python3
"""Checker script for Custom Button to Action Migration skill.

Scans for migration concerns in Apex / LWC / metadata:

- Apex methods returning PageReference but called from `@AuraEnabled` (Lightning ignores PageReference)
- LWC `.js` files using alert() or confirm() (LWS-incompatible)
- LWC `.js` referencing sforce.* / $A.* (Classic patterns; not available)
- Apex `@AuraEnabled` methods used by Quick Actions without `with sharing`
- WebLink (custom buttons) metadata still present with OnClickJavaScript content (Lightning won't render)

Stdlib only.

Usage:
    python3 check_custom_button_to_action_migration.py --project-dir path/to/project
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


def find_files(root: Path, pattern: str) -> list[Path]:
    return [p for p in root.rglob(pattern) if p.is_file() and ".sfdx" not in p.parts]


def scan(root: Path) -> list[tuple[str, Path, int, str]]:
    findings: list[tuple[str, Path, int, str]] = []

    # LWC JS files
    for f in find_files(root, "*.js"):
        # Skip Aura controllers (.js inside aura/) and tests
        if "/aura/" in str(f) or f.name.endswith(".test.js"):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if re.search(r'\balert\s*\(', line):
                findings.append(("lws", f, line_no, "alert() — LWS-incompatible; use ShowToastEvent"))
            if re.search(r'\bconfirm\s*\(', line):
                findings.append(("lws", f, line_no, "confirm() — LWS-incompatible; use LightningConfirm"))
            if re.search(r'\bsforce\.\w+', line):
                findings.append(("classic", f, line_no, "sforce.* API — Classic JavaScript only; not available in LWC"))
            if re.search(r'\$A\.\w+', line):
                findings.append(("classic", f, line_no, "$A.* API — Aura framework only; not available in LWC"))
            if re.search(r'window\.opener', line):
                findings.append(("classic", f, line_no, "window.opener — popup pattern not supported in Lightning"))

    # Apex files
    for f in find_files(root, "*.cls"):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Find @AuraEnabled methods returning PageReference
        for m in re.finditer(r'@AuraEnabled[^@]*?\b(public|global)\s+static\s+PageReference\s+\w+', text):
            line_no = text[:m.start()].count('\n') + 1
            findings.append(("pageref", f, line_no, "@AuraEnabled method returns PageReference — Lightning ignores it; return data and navigate client-side"))
        # @AuraEnabled in a class without `with sharing`
        if re.search(r'@AuraEnabled', text) and not re.search(r'\bwith\s+sharing\b', text):
            findings.append(("sharing", f, 1, f"Class contains @AuraEnabled methods but does not declare `with sharing` — explicit sharing required"))

    # WebLink metadata files (custom buttons)
    for f in find_files(root, "*.weblink-meta.xml"):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if '<linkType>javascript</linkType>' in text or '<openType>onClickJavaScript</openType>' in text:
            findings.append(("js-button", f, 1,
                             "JavaScript Custom Button — does not render in Lightning Experience; plan a Lightning Action replacement"))

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
