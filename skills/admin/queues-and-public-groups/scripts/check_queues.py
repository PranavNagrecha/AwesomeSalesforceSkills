#!/usr/bin/env python3
"""check_queues.py — Queue and Public Group metadata checker.

Scans a Salesforce metadata directory for Group (queue-type) and GroupMember
references in XML files, listing queue names and any members for review.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_queues.py [--manifest-dir path/to/metadata]
    python3 check_queues.py --help
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# Salesforce Metadata API namespace
SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Relative path inside a Salesforce DX project where queue metadata lives
QUEUE_METADATA_PATHS = [
    "queues",          # MDAPI format
    "force-app/main/default/queues",   # SFDX format
]

GROUP_METADATA_PATHS = [
    "groups",
    "force-app/main/default/groups",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Salesforce metadata for queue and public group references. "
            "Lists queue names, supported objects, queue email, and member types for review."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce project or metadata (default: current directory).",
    )
    return parser.parse_args()


def find_xml_files(base: Path, subdirs: list[str]) -> list[Path]:
    """Return all .xml files found under any of the given subdirectory candidates."""
    found: list[Path] = []
    for subdir in subdirs:
        candidate = base / subdir
        if candidate.is_dir():
            found.extend(sorted(candidate.glob("*.xml")))
    return found


def extract_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return (element.text or "").strip()


def parse_queue_file(path: Path) -> dict:
    """Parse a Queue metadata XML file and return a summary dict."""
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        return {"file": str(path), "error": f"XML parse error: {exc}"}

    root = tree.getroot()
    # Strip namespace for easier access
    ns = {"sf": SF_NS}

    label = extract_text(root.find("sf:label", ns) or root.find("label"))
    queue_email = extract_text(root.find("sf:queueEmail", ns) or root.find("queueEmail"))
    supported_objects = [
        extract_text(el)
        for el in (root.findall("sf:queueSobject/sf:sobjectType", ns)
                   or root.findall("queueSobject/sobjectType"))
    ]
    member_elements = (
        root.findall("sf:queueMembers/sf:users/sf:member", ns)
        or root.findall("queueMembers/users/member")
    )
    members = [extract_text(el) for el in member_elements]

    return {
        "type": "Queue",
        "file": path.name,
        "label": label or path.stem,
        "queue_email": queue_email,
        "supported_objects": supported_objects,
        "members": members,
    }


def parse_group_file(path: Path) -> dict:
    """Parse a Group (public group) metadata XML file and return a summary dict."""
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        return {"file": str(path), "error": f"XML parse error: {exc}"}

    root = tree.getroot()
    ns = {"sf": SF_NS}

    label = extract_text(root.find("sf:label", ns) or root.find("label"))
    member_elements = (
        root.findall("sf:members", ns)
        or root.findall("members")
    )
    members = []
    for el in member_elements:
        mtype = extract_text(el.find("sf:type", ns) or el.find("type"))
        mval = extract_text(el.find("sf:member", ns) or el.find("member"))
        if mtype or mval:
            members.append(f"{mtype}: {mval}" if mtype else mval)

    return {
        "type": "PublicGroup",
        "file": path.name,
        "label": label or path.stem,
        "members": members,
    }


def scan_metadata_for_group_references(base: Path) -> list[str]:
    """Search all XML files for any reference to Group Ids (00G prefix) or queue patterns."""
    references: list[str] = []
    for xml_file in base.rglob("*.xml"):
        try:
            content = xml_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Queue IDs start with 00G in Salesforce
        if "00G" in content or "<queueEmail>" in content or "<queueSobject>" in content:
            references.append(str(xml_file.relative_to(base)))
    return sorted(set(references))


def check_queue_issues(queue: dict) -> list[str]:
    """Return a list of issue strings for a parsed queue summary."""
    issues: list[str] = []
    if queue.get("error"):
        issues.append(f"[{queue['file']}] Parse error: {queue['error']}")
        return issues

    label = queue.get("label", queue.get("file", "unknown"))

    if not queue.get("queue_email"):
        issues.append(
            f"[Queue: {label}] No queueEmail configured — team will not receive "
            "notifications when records are assigned to this queue."
        )

    if not queue.get("supported_objects"):
        issues.append(
            f"[Queue: {label}] No supported objects (queueSobject) found in metadata. "
            "Confirm the queue is associated with at least one object."
        )

    unsupported = []
    supported_for_queues = {"Case", "Lead", "Order"}
    for obj in queue.get("supported_objects", []):
        # Custom objects are allowed; warn only on known unsupported standard objects
        if obj in {"Account", "Contact", "Opportunity", "Campaign", "Contract"}:
            unsupported.append(obj)
    if unsupported:
        issues.append(
            f"[Queue: {label}] Potentially unsupported standard objects for queue ownership: "
            f"{', '.join(unsupported)}. Queues only support Case, Lead, Order, and "
            "custom objects with 'Allow Queues' enabled."
        )

    return issues


def main() -> int:
    args = parse_args()
    base = Path(args.manifest_dir).resolve()

    if not base.exists():
        print(f"ERROR: Directory not found: {base}", file=sys.stderr)
        return 1

    print(f"Scanning: {base}\n")
    issues: list[str] = []
    found_any = False

    # --- Scan queue metadata files ---
    queue_files = find_xml_files(base, QUEUE_METADATA_PATHS)
    if queue_files:
        found_any = True
        print(f"Queues found ({len(queue_files)}):")
        for qf in queue_files:
            q = parse_queue_file(qf)
            if q.get("error"):
                print(f"  [ERROR] {q['file']}: {q['error']}")
                issues.append(f"Parse error in {q['file']}: {q['error']}")
                continue
            objs = ", ".join(q["supported_objects"]) if q["supported_objects"] else "(none)"
            email = q["queue_email"] or "(not configured)"
            members = f"{len(q['members'])} member(s)" if q["members"] else "(no members listed)"
            print(f"  Queue: {q['label']}")
            print(f"    Objects : {objs}")
            print(f"    Email   : {email}")
            print(f"    Members : {members}")
            issues.extend(check_queue_issues(q))
        print()
    else:
        print("No queue metadata files found in known locations.")
        print(f"  Searched: {[str(base / p) for p in QUEUE_METADATA_PATHS]}\n")

    # --- Scan public group metadata files ---
    group_files = find_xml_files(base, GROUP_METADATA_PATHS)
    if group_files:
        found_any = True
        print(f"Public Groups found ({len(group_files)}):")
        for gf in group_files:
            g = parse_group_file(gf)
            if g.get("error"):
                print(f"  [ERROR] {g['file']}: {g['error']}")
                issues.append(f"Parse error in {g['file']}: {g['error']}")
                continue
            members = ", ".join(g["members"]) if g["members"] else "(no members listed)"
            print(f"  Group: {g['label']}")
            print(f"    Members : {members}")
        print()
    else:
        print("No public group metadata files found in known locations.")
        print(f"  Searched: {[str(base / p) for p in GROUP_METADATA_PATHS]}\n")

    # --- Scan all XML files for queue/group references ---
    refs = scan_metadata_for_group_references(base)
    if refs:
        print(f"Files referencing queue or group patterns ({len(refs)}):")
        for r in refs:
            print(f"  {r}")
        print()

    # --- Report issues ---
    if issues:
        print(f"Issues found ({len(issues)}):")
        for issue in issues:
            print(f"  ISSUE: {issue}")
        return 1

    if not found_any and not refs:
        print("No queue or public group metadata found in this directory.")
        print("Run from the root of a Salesforce DX project or MDAPI package.")
        return 0

    print("No issues found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
