#!/usr/bin/env python3
"""Checker script for Knowledge Classic to Lightning Migration skill.

Scans for code that still references Classic Article Type sObjects (`*__kav`
suffix where the prefix is NOT 'Knowledge'), missing record-type filters in
Knowledge__kav SOQL, direct PublishStatus DML attempts, and Quick Action XML
referencing legacy article-type sObjects.

Stdlib only.

Usage:
    python3 check_knowledge_classic_to_lightning.py --project-dir path/to/project
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

    # Apex files
    for f in find_files(root, "*.cls"):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            # Legacy __kav references (excluding Knowledge__kav itself)
            for m in re.finditer(r'\b([A-Z][A-Za-z0-9_]*)__kav\b', line):
                name = m.group(1)
                if name != "Knowledge":
                    findings.append(("legacy", f, line_no,
                                     f"Reference to legacy Article Type sObject `{name}__kav` — replace with Knowledge__kav + RecordType.DeveloperName filter"))
            # Knowledge__kav SOQL without record type filter
            if re.search(r'FROM\s+Knowledge__kav\b', line, re.IGNORECASE):
                # Heuristic: check if RecordType.DeveloperName appears within next 5 lines
                window = "\n".join(text.splitlines()[line_no - 1:line_no + 5])
                if "RecordType" not in window:
                    findings.append(("filter", f, line_no,
                                     "Knowledge__kav SOQL without RecordType.DeveloperName filter — verify intent (returns all article types)"))
            # Direct PublishStatus DML
            if re.search(r"PublishStatus\s*=\s*['\"]Online['\"]", line):
                findings.append(("publish", f, line_no,
                                 "Setting PublishStatus='Online' via DML — must use KbManagement.PublishingService.publishArticle()"))

    # Quick Action metadata files
    for f in find_files(root, "*.quickAction-meta.xml"):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for m in re.finditer(r'\b([A-Z][A-Za-z0-9_]*)__kav\b', line):
                if m.group(1) != "Knowledge":
                    findings.append(("quickaction", f, line_no,
                                     f"Quick Action references legacy `{m.group(1)}__kav` — update to Knowledge__kav"))

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
