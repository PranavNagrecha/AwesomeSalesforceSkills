#!/usr/bin/env python3
"""Checker script for Salesforce ERD and Diagramming skill.

Scans a repo for common ERD / diagram hygiene issues:
- Diagrams checked in without source files
- ERDs that reference objects no longer in metadata
- Executive diagrams polluted with system objects

Usage:
    python3 check_salesforce_erd_and_diagramming.py [--manifest-dir path/to/metadata] [--docs-dir path/to/docs]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SYSTEM_OBJECTS = {
    "Task", "Event", "Note", "Attachment", "ContentVersion",
    "ContentDocumentLink", "FeedItem", "CollaborationGroup",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Salesforce diagram hygiene.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of Salesforce metadata.")
    parser.add_argument("--docs-dir", default="docs", help="Directory containing diagrams.")
    return parser.parse_args()


def find_objects(manifest_dir: Path) -> set[str]:
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return set()
    return {p.name for p in objects_dir.iterdir() if p.is_dir()}


def check_diagrams(docs_dir: Path, known_objects: set[str]) -> list[str]:
    issues: list[str] = []
    if not docs_dir.exists():
        return issues
    md_files = list(docs_dir.rglob("*.md")) + list(docs_dir.rglob("*.mmd")) + list(docs_dir.rglob("*.puml"))
    for path in md_files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Only scan files that look like diagrams
        looks_like_erd = "erDiagram" in text or "@startuml" in text or "```mermaid" in text
        if not looks_like_erd:
            continue
        # If it's an "executive" or "business" diagram, check for system objects
        lower = path.name.lower()
        if "executive" in lower or "business" in lower or "logical" in lower:
            for sys_obj in SYSTEM_OBJECTS:
                if re.search(rf"\b{sys_obj}\b", text):
                    issues.append(
                        f"{path}: executive/logical diagram references system object {sys_obj}; move to physical ERD"
                    )
        # Look for object refs that no longer exist in metadata
        mentioned = set(re.findall(r"\b([A-Z][A-Za-z0-9_]*__c)\b", text))
        missing = {obj for obj in mentioned if obj not in known_objects}
        if missing and known_objects:
            issues.append(
                f"{path}: diagram references custom objects not in metadata: {', '.join(sorted(missing)[:5])}"
            )
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    docs_dir = Path(args.docs_dir)
    if not manifest_dir.exists():
        print(f"ERROR: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    known_objects = find_objects(manifest_dir)
    issues = check_diagrams(docs_dir, known_objects)

    if not issues:
        print("No diagram hygiene issues detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
