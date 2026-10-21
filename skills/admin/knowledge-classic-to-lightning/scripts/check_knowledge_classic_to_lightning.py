#!/usr/bin/env python3
"""Checker script for Knowledge Classic to Lightning Migration skill.

Scans Apex classes, triggers and Quick Actions for migration blockers:
- Apex trigger on an article-type `X__kav` object -> WARN: "you must remove any
  Apex triggers that reference the KAV article types" before migrating
  (apexdev 264 L16011-16014)
- reference to an article-type `X__kav` (prefix other than Knowledge) in Apex
  or a Quick Action -> WARN: those objects are deleted during a multi-type
  migration (apexdev 264 L16013-16014). If your org renamed the Knowledge
  object prefix (obj 264 L161753-161754), pass --kav-prefix.
- `PublishStatus = 'Online'` used as an assignment (object constructor or
  `.PublishStatus =`) -> WARN: the field has no Create/Update property
  (obj 264 L162102-162105); publish via KbManagement.PublishingService.
  SOQL WHERE clauses are not flagged.
- `FROM Knowledge__kav` with no RecordType filter within the statement -> WARN
  (returns every former article type).

Exit codes: 1 on a missing --manifest-dir; WARN findings exit 0 unless
--strict; a tree with no .cls/.trigger/.quickAction files prints one WARN and
exits 0. Stdlib only.

Usage:
    python3 check_knowledge_classic_to_lightning.py --manifest-dir path/to/project [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

KAV_REF = re.compile(r"\b([A-Za-z][A-Za-z0-9_]*)__kav\b")
TRIGGER_ON = re.compile(r"\btrigger\s+\w+\s+on\s+([A-Za-z][A-Za-z0-9_]*)__kav\b", re.IGNORECASE)
SOQL_BLOCK = re.compile(r"\[\s*SELECT\b[^\]]*\]", re.IGNORECASE | re.DOTALL)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Find Knowledge migration blockers in Apex and Quick Actions.")
    p.add_argument("--manifest-dir", "--project-dir", dest="manifest_dir", default=".",
                   help="Root of the Salesforce project.")
    p.add_argument("--kav-prefix", default="Knowledge", help="Prefix of the Lightning Knowledge object.")
    p.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings too.")
    return p.parse_args()


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def scan_apex(path: Path, rel: str, prefix: str, warns: list[str]) -> None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    for m in TRIGGER_ON.finditer(text):
        if m.group(1) != prefix:
            warns.append(f"{rel}:{line_of(text, m.start())}: trigger on article type {m.group(1)}__kav "
                         "blocks migration; remove it before running the Migration Tool")
    for m in KAV_REF.finditer(text):
        if m.group(1) != prefix:
            warns.append(f"{rel}:{line_of(text, m.start())}: references article type {m.group(1)}__kav, "
                         "which a multi-type migration deletes; rewrite to "
                         f"{prefix}__kav + RecordType.DeveloperName")
    soql_spans = [(m.start(), m.end()) for m in SOQL_BLOCK.finditer(text)]
    for m in re.finditer(r"PublishStatus\s*=\s*'Online'", text, re.IGNORECASE):
        if any(a <= m.start() < b for a, b in soql_spans):
            continue
        warns.append(f"{rel}:{line_of(text, m.start())}: assigns PublishStatus='Online'; the field is not "
                     "createable or updateable - use KbManagement.PublishingService.publishArticle()")
    for a, b in soql_spans:
        block = text[a:b]
        if re.search(rf"\bFROM\s+{re.escape(prefix)}__kav\b", block, re.IGNORECASE) and "RecordType" not in block:
            warns.append(f"{rel}:{line_of(text, a)}: {prefix}__kav query without a RecordType filter "
                         "returns every former article type - confirm intent")


def scan_quick_action(path: Path, rel: str, prefix: str, warns: list[str]) -> None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    for m in KAV_REF.finditer(text):
        if m.group(1) != prefix:
            warns.append(f"{rel}:{line_of(text, m.start())}: Quick Action references {m.group(1)}__kav; "
                         f"update to {prefix}__kav before migration")


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    apex = sorted(p for p in list(root.rglob("*.cls")) + list(root.rglob("*.trigger")) if ".sfdx" not in p.parts)
    actions = sorted(p for p in root.rglob("*.quickAction-meta.xml") if ".sfdx" not in p.parts)
    if not apex and not actions:
        print(f"WARN: no .cls, .trigger or .quickAction-meta.xml files under {root}; nothing to check")
        return 0
    warns: list[str] = []
    for path in apex:
        scan_apex(path, str(path.relative_to(root)), args.kav_prefix, warns)
    for path in actions:
        scan_quick_action(path, str(path.relative_to(root)), args.kav_prefix, warns)
    for msg in warns:
        print(f"WARN: {msg}")
    if not warns:
        print("OK: no Knowledge migration blockers found.")
    return 1 if (warns and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
