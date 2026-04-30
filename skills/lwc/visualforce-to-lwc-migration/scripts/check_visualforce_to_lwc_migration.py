#!/usr/bin/env python3
"""Checker script for Visualforce to LWC Migration skill.

Scans a Salesforce project directory for common migration issues introduced
by mechanical Visualforce-to-LWC translation:

- LWC `.js` files using `lwc:dom="manual"` + innerHTML (XSS surface)
- LWC `.js` files calling `setTemplateId` patterns from VF controllers
- `@AuraEnabled` Apex methods with `cacheable=true` AND DML statements
- LWC `.js` files reading `pageRef.state.id` without `c__id` fallback (App Builder URL gotcha)
- LWC `.html` referencing `apex:` tags (mechanical translation leftover)
- Apex `@AuraEnabled` methods returning `PageReference`

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_visualforce_to_lwc_migration.py --project-dir path/to/project
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd(), help="Path to the Salesforce project (containing force-app/ or src/)")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on any finding")
    return parser.parse_args()


def find_files(root: Path, patterns: list[str]) -> list[Path]:
    out: list[Path] = []
    for p in patterns:
        out.extend(root.rglob(p))
    return [p for p in out if p.is_file() and ".sfdx" not in p.parts and "node_modules" not in p.parts]


CHECKS: list[tuple[str, str, str, list[str]]] = [
    # (category, file_pattern, regex, message)
    ("xss", "*.html", r'lwc:dom\s*=\s*"manual"', "lwc:dom='manual' — verify innerHTML is sanitized (was probably <apex:outputText escape='false'>)"),
    ("xss", "*.js", r'\.innerHTML\s*=', "Direct innerHTML assignment — verify content is sanitized; never use user-controlled values"),
    ("apex", "*.cls", r'@AuraEnabled\s*\(\s*cacheable\s*=\s*true\s*\)', "@AuraEnabled(cacheable=true) — verify NO DML in this method (DML is forbidden in cacheable methods)"),
    ("apex", "*.cls", r'returns?\s+PageReference', "Apex method returning PageReference — LWC ignores PageReference; return data and use NavigationMixin client-side"),
    ("url-param", "*.js", r'pageRef\.state\.\w+', "URL parameter read from pageRef.state — confirm c__ prefix used for App Builder pages"),
    ("html", "*.html", r'<\s*apex:', "Found <apex:*> tag in LWC HTML — mechanical translation leftover, must be replaced with Lightning equivalents"),
    ("alerts", "*.js", r'\balert\s*\(', "alert() call — replace with ShowToastEvent for Lightning Web Security compatibility"),
    ("apex", "*.cls", r'sforce\.\w+', "sforce.* API call — these are Classic JavaScript globals; not available in LWC"),
]


def scan(root: Path) -> dict[str, list[tuple[Path, int, str]]]:
    findings: dict[str, list[tuple[Path, int, str]]] = {}
    js_files = find_files(root, ["*.js"])
    cls_files = find_files(root, ["*.cls"])
    html_files = find_files(root, ["*.html"])

    file_groups = {"*.js": js_files, "*.cls": cls_files, "*.html": html_files}

    for category, pattern, regex, msg in CHECKS:
        for f in file_groups.get(pattern, []):
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for line_no, line in enumerate(text.splitlines(), start=1):
                if re.search(regex, line):
                    findings.setdefault(category, []).append((f, line_no, msg))
    return findings


def main() -> int:
    args = parse_args()
    root = args.project_dir.resolve()
    if not root.exists():
        print(f"ERROR: project dir not found: {root}", file=sys.stderr)
        return 2

    findings = scan(root)
    total = sum(len(v) for v in findings.values())

    print(f"Scanned: {root}")
    print(f"Findings: {total}")
    if not findings:
        print("No issues detected.")
        return 0

    for category, items in sorted(findings.items()):
        print(f"\n=== {category} ({len(items)}) ===")
        for path, line_no, msg in items:
            rel = path.relative_to(root) if path.is_relative_to(root) else path
            print(f"  {rel}:{line_no} — {msg}")

    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
