#!/usr/bin/env python3
"""Detect Chatter-noise hotspots in retrieved org metadata.

Walks an SFDX-style metadata tree (force-app/) and reports:

1. Flows with `actionType` = `chatterPost` (Post to Chatter actions)
2. Apex classes/triggers that insert `FeedItem` records
3. Custom objects with > N tracked fields (Feed Tracking spam)
4. `FeedItem` inserts without `Visibility = 'InternalUsers'` (leak risk for
   Experience Cloud orgs)

Stdlib only — no pip dependencies.

Usage:
    python3 check_chatter_notification_tuning.py [--root force-app/main/default]
                                                 [--max-tracked-fields 5]

Exit codes:
    0  no findings
    1  findings present (informational, non-blocking)
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"s": "http://soap.sforce.com/2006/04/metadata"}

FEED_INSERT_RE = re.compile(
    r"\binsert\s+\w*\s*FeedItem\b|\bnew\s+FeedItem\b", re.IGNORECASE
)
VISIBILITY_RE = re.compile(
    r"\.Visibility\s*=\s*['\"]InternalUsers['\"]", re.IGNORECASE
)
CHATTER_POST_FLOW_ACTION = "chatterPost"


def find_flow_chatter_actions(flows_dir: Path) -> list[tuple[Path, str]]:
    findings: list[tuple[Path, str]] = []
    if not flows_dir.exists():
        return findings
    for fp in flows_dir.rglob("*.flow-meta.xml"):
        try:
            tree = ET.parse(fp)
        except ET.ParseError:
            continue
        root = tree.getroot()
        for action in root.findall(".//s:actionCalls", NS):
            atype = action.find("s:actionType", NS)
            if atype is not None and atype.text == CHATTER_POST_FLOW_ACTION:
                name_el = action.find("s:name", NS)
                action_name = name_el.text if name_el is not None else "(unnamed)"
                findings.append((fp, action_name))
    return findings


def find_apex_feeditem_inserts(apex_dirs: list[Path]) -> list[tuple[Path, int, str, bool]]:
    findings: list[tuple[Path, int, str, bool]] = []
    for d in apex_dirs:
        if not d.exists():
            continue
        for ext in ("*.cls", "*.trigger"):
            for fp in d.rglob(ext):
                try:
                    text = fp.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                lines = text.splitlines()
                for i, line in enumerate(lines):
                    if "FeedItem" in line and FEED_INSERT_RE.search(line):
                        window_start = max(0, i - 30)
                        window_end = min(len(lines), i + 5)
                        window = "\n".join(lines[window_start:window_end])
                        has_internal = bool(VISIBILITY_RE.search(window))
                        findings.append((fp, i + 1, line.strip(), has_internal))
    return findings


def find_objects_overtracked(objects_dir: Path, max_tracked: int) -> list[tuple[str, int, list[str]]]:
    findings: list[tuple[str, int, list[str]]] = []
    if not objects_dir.exists():
        return findings
    for obj_dir in objects_dir.iterdir():
        if not obj_dir.is_dir():
            continue
        tracked: list[str] = []
        fields_dir = obj_dir / "fields"
        if not fields_dir.exists():
            continue
        for field_xml in fields_dir.glob("*.field-meta.xml"):
            try:
                tree = ET.parse(field_xml)
            except ET.ParseError:
                continue
            root = tree.getroot()
            tff = root.find("s:trackFeedHistory", NS)
            if tff is not None and tff.text == "true":
                tracked.append(field_xml.stem.replace(".field-meta", ""))
        if len(tracked) > max_tracked:
            findings.append((obj_dir.name, len(tracked), tracked))
    return findings


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="force-app/main/default")
    p.add_argument("--max-tracked-fields", type=int, default=5)
    args = p.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"metadata root not found: {root}", file=sys.stderr)
        return 0

    flows_dir = root / "flows"
    classes_dir = root / "classes"
    triggers_dir = root / "triggers"
    objects_dir = root / "objects"

    findings_count = 0

    flow_findings = find_flow_chatter_actions(flows_dir)
    if flow_findings:
        print("\n## Flows posting to Chatter (consider migrating to Custom Notifications)")
        for fp, name in flow_findings:
            print(f"  - {fp.relative_to(root)}: action {name!r}")
        findings_count += len(flow_findings)

    apex_findings = find_apex_feeditem_inserts([classes_dir, triggers_dir])
    if apex_findings:
        print("\n## Apex inserting FeedItem")
        for fp, ln, snippet, has_internal in apex_findings:
            tag = " [InternalUsers visibility OK]" if has_internal else " [WARN: no InternalUsers visibility — possible leak]"
            print(f"  - {fp.relative_to(root)}:{ln}: {snippet}{tag}")
        findings_count += len(apex_findings)

    obj_findings = find_objects_overtracked(objects_dir, args.max_tracked_fields)
    if obj_findings:
        print(f"\n## Objects with more than {args.max_tracked_fields} fields under Feed Tracking")
        for obj, n, fields in obj_findings:
            print(f"  - {obj}: {n} tracked fields: {', '.join(fields[:10])}{' ...' if n > 10 else ''}")
        findings_count += len(obj_findings)

    if findings_count == 0:
        print("No Chatter-noise hotspots detected in this metadata tree.")
        return 0

    print(f"\nTotal findings: {findings_count}")
    print("Refer to the skill workflow for remediation steps.")
    print(f"ERROR: {findings_count} chatter-noise finding(s); see report above.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
