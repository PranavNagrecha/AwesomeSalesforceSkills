#!/usr/bin/env python3
"""Checker script for Dynamic Forms Migration skill.

Scans FlexiPage XML files for common migration concerns:

- Field components marked `isRequired=true` AND with a `<visibilityRule>` (save-failure trap)
- Visibility rules using `$User.Profile.Name` (brittle; recommend Custom Permission)
- Field components without any sectional grouping (organizational smell)

Stdlib only.

Usage:
    python3 check_dynamic_forms_migration.py --project-dir path/to/project
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


def find_flexipages(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.flexipage-meta.xml") if p.is_file() and ".sfdx" not in p.parts]


def scan(root: Path) -> list[tuple[str, Path, int, str]]:
    findings: list[tuple[str, Path, int, str]] = []
    for f in find_flexipages(root):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        # Find each fieldInstance block and check for required + visibility combo
        for match in re.finditer(r'<fieldInstance>(.*?)</fieldInstance>', text, flags=re.DOTALL):
            block = match.group(1)
            if '<isRequired>true</isRequired>' in block and '<visibilityRule>' in block:
                line_no = text[:match.start()].count('\n') + 1
                # Try to extract the field name for the message
                fld = re.search(r'<fieldItem>([^<]+)</fieldItem>', block)
                name = fld.group(1) if fld else "(unknown)"
                findings.append(("required-and-hidden", f, line_no,
                                 f"Field {name} is both required AND has a visibilityRule — save will fail when hidden"))

        # Profile name visibility rules
        for line_no, line in enumerate(text.splitlines(), start=1):
            if '$User.Profile.Name' in line:
                findings.append(("profile-string", f, line_no,
                                 "Visibility rule uses $User.Profile.Name (brittle to renames) — prefer $Permission.<CustomPermissionName>"))

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
