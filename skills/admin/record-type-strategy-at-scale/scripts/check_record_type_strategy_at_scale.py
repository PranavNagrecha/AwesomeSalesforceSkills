#!/usr/bin/env python3
"""Checker script for the Record Type Strategy At Scale skill.

Lints the record type x persona x layout matrix in a retrieved metadata tree.
It reads RecordType, Profile, and PermissionSet metadata together, because
every finding below is a *relationship* between those files rather than a
property of any one of them.

Checks:
  1. ERROR  Hardcoded 15/18-character Record Type Ids in Apex.
  2. WARN   getRecordTypeInfosByName() where ByDeveloperName is portable.
  3. WARN   Orphan record type: active, but no Profile or PermissionSet in the
            tree grants it with <visible>true</visible>.
  4. ERROR  No default: a Profile grants one or more record types on an object
            with visible=true but sets default=true on none of them. The
            default is profile-only -- PermissionSetRecordTypeVisibility has no
            <default> field -- so those users fall back to the Master record
            type, which applies no picklist filtering.
  5. WARN   Active record type with no layoutAssignment naming it in any
            Profile in the tree.
  6. INFO   / WARN on record type count per object, using the count guide in
            admin/record-types-and-page-layouts (1-4 healthy, 5-8 monitor,
            9-12 warning, 13+ redesign).

Grounding for checks 3-6 is in ../references/metadata-examples.md and
../references/gotchas.md.

Uses stdlib only -- no pip dependencies.

Exit code: 1 if any ERROR or WARN finding is reported, else 0. INFO findings
are printed but do not fail the run.

Usage:
    python3 check_record_type_strategy_at_scale.py --help
    python3 check_record_type_strategy_at_scale.py --manifest-dir force-app/main/default
    python3 check_record_type_strategy_at_scale.py --manifest-dir force-app/main/default --profile-count 65
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"

SEV_ERROR = "ERROR"
SEV_WARN = "WARN"
SEV_INFO = "INFO"

# Findings that fail the run.
FAILING = (SEV_ERROR, SEV_WARN)

# Pattern to detect hardcoded 15- or 18-character Salesforce IDs assigned to RecordTypeId
HARDCODED_RT_ID_PATTERN = re.compile(
    r"""RecordTypeId\s*=\s*['"]([0-9a-zA-Z]{15}|[0-9a-zA-Z]{18})['"]""",
    re.IGNORECASE,
)

# Pattern to detect getRecordTypeInfosByName (should usually be ByDeveloperName)
BY_NAME_PATTERN = re.compile(r"getRecordTypeInfosByName\s*\(", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint the record type x profile/permission-set x layout matrix in a "
            "retrieved Salesforce metadata tree."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the retrieved Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--rt-info-threshold",
        type=int,
        default=8,
        help="Report INFO when an object has more than this many record types (default: 8).",
    )
    parser.add_argument(
        "--rt-warn-threshold",
        type=int,
        default=13,
        help="Report WARN when an object has this many record types or more (default: 13).",
    )
    parser.add_argument(
        "--profile-count",
        type=int,
        default=0,
        help="Org-wide profile count. If provided, the count findings show the N x M assignment total.",
    )
    return parser.parse_args()


# --------------------------------------------------------------------------
# XML helpers. Never use `elem.find(a) or elem.find(b)` -- a childless Element
# is falsy, so that idiom discards real matches.
# --------------------------------------------------------------------------


def find_child(parent, name):
    """Return the first child element named `name`, namespaced or not, else None."""
    found = parent.find(NS + name)
    if found is not None:
        return found
    found = parent.find(name)
    if found is not None:
        return found
    return None


def child_text(parent, name, default=None):
    """Return the stripped text of child `name`, or `default`."""
    found = find_child(parent, name)
    if found is None:
        return default
    if found.text is None:
        return default
    return found.text.strip()


def child_bool(parent, name, default=False):
    text = child_text(parent, name)
    if text is None:
        return default
    return text.lower() == "true"


def iter_children(parent, name):
    """Yield every child element named `name`, namespaced or not."""
    yielded = False
    for elem in parent.findall(NS + name):
        yielded = True
        yield elem
    if not yielded:
        for elem in parent.findall(name):
            yield elem


def parse_xml(path: Path):
    try:
        return ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None


def find_files(root: Path, extensions: set[str]) -> list[Path]:
    """Walk the directory tree and return files matching the given extensions."""
    matches = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules", "__pycache__"}]
        for fname in filenames:
            if any(fname.endswith(ext) for ext in extensions):
                matches.append(Path(dirpath) / fname)
    return matches


# --------------------------------------------------------------------------
# Collectors
# --------------------------------------------------------------------------


def collect_record_types(manifest_dir: Path) -> dict[tuple[str, str], bool]:
    """Return {(object, developerName): active} across both source shapes.

    DX source puts each record type in objects/<Obj>/recordTypes/<Name>.recordType-meta.xml.
    MDAPI format nests <recordTypes> blocks inside the <CustomObject> file.
    """
    record_types: dict[tuple[str, str], bool] = {}

    for fpath in find_files(manifest_dir, {".recordType-meta.xml"}):
        parts = fpath.parts
        obj_name = None
        for i, part in enumerate(parts):
            if part == "recordTypes" and i >= 1:
                candidate = parts[i - 1]
                if candidate != "objects":
                    obj_name = candidate
                break
        if obj_name is None:
            continue
        dev_name = fpath.name.split(".")[0]
        root = parse_xml(fpath)
        active = True if root is None else child_bool(root, "active", default=True)
        record_types[(obj_name, dev_name)] = active

    for fpath in find_files(manifest_dir, {".object-meta.xml", ".object"}):
        root = parse_xml(fpath)
        if root is None:
            continue
        obj_name = fpath.name.split(".")[0]
        for block in iter_children(root, "recordTypes"):
            dev_name = child_text(block, "fullName")
            if not dev_name:
                continue
            dev_name = dev_name.split(".")[-1]
            record_types[(obj_name, dev_name)] = child_bool(block, "active", default=True)

    return record_types


def split_qualified(value: str | None) -> tuple[str, str] | None:
    """'Opportunity.New_Business' -> ('Opportunity', 'New_Business')."""
    if not value or "." not in value:
        return None
    obj_name, _, dev_name = value.partition(".")
    obj_name = obj_name.strip()
    dev_name = dev_name.strip()
    if not obj_name or not dev_name:
        return None
    return (obj_name, dev_name)


def collect_profiles(manifest_dir: Path) -> list[dict]:
    """Return one dict per profile: name, visibilities, layout assignments."""
    profiles = []
    for fpath in find_files(manifest_dir, {".profile-meta.xml", ".profile"}):
        root = parse_xml(fpath)
        if root is None:
            continue
        entry = {
            "name": fpath.name.split(".")[0],
            "path": fpath,
            "visibilities": [],
            "layout_record_types": set(),
            "layout_fallback_objects": set(),
        }
        for vis in iter_children(root, "recordTypeVisibilities"):
            key = split_qualified(child_text(vis, "recordType"))
            if key is None:
                continue
            entry["visibilities"].append(
                {
                    "key": key,
                    "visible": child_bool(vis, "visible"),
                    "default": child_bool(vis, "default"),
                }
            )
        for assign in iter_children(root, "layoutAssignments"):
            layout = child_text(assign, "layout")
            key = split_qualified(child_text(assign, "recordType"))
            if key is not None:
                entry["layout_record_types"].add(key)
            elif layout:
                entry["layout_fallback_objects"].add(layout.split("-")[0])
        profiles.append(entry)
    return profiles


def collect_permission_sets(manifest_dir: Path) -> list[dict]:
    perm_sets = []
    for fpath in find_files(manifest_dir, {".permissionset-meta.xml", ".permissionset"}):
        root = parse_xml(fpath)
        if root is None:
            continue
        entry = {"name": fpath.name.split(".")[0], "path": fpath, "visibilities": []}
        for vis in iter_children(root, "recordTypeVisibilities"):
            key = split_qualified(child_text(vis, "recordType"))
            if key is None:
                continue
            entry["visibilities"].append({"key": key, "visible": child_bool(vis, "visible")})
        perm_sets.append(entry)
    return perm_sets


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------


def check_hardcoded_ids(manifest_dir: Path) -> list[tuple[str, str]]:
    """Scan Apex files for hardcoded Record Type IDs."""
    findings = []
    for fpath in find_files(manifest_dir, {".cls", ".trigger"}):
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in HARDCODED_RT_ID_PATTERN.finditer(content):
            line_num = content[: match.start()].count("\n") + 1
            findings.append(
                (
                    SEV_ERROR,
                    f"Hardcoded RecordTypeId '{match.group(1)}' in {fpath.name}:{line_num} "
                    f"-- use Schema.SObjectType.<Obj>.getRecordTypeInfosByDeveloperName() instead",
                )
            )
    return findings


def check_by_name_usage(manifest_dir: Path) -> list[tuple[str, str]]:
    """Scan Apex files for getRecordTypeInfosByName() usage."""
    findings = []
    for fpath in find_files(manifest_dir, {".cls", ".trigger"}):
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in BY_NAME_PATTERN.finditer(content):
            line_num = content[: match.start()].count("\n") + 1
            findings.append(
                (
                    SEV_WARN,
                    f"getRecordTypeInfosByName() in {fpath.name}:{line_num} "
                    f"-- getName() returns the translatable label; prefer "
                    f"getRecordTypeInfosByDeveloperName()",
                )
            )
    return findings


def check_orphan_record_types(
    record_types: dict[tuple[str, str], bool],
    profiles: list[dict],
    perm_sets: list[dict],
) -> list[tuple[str, str]]:
    """Active record type that nothing in the tree grants."""
    granted: set[tuple[str, str]] = set()
    for profile in profiles:
        for vis in profile["visibilities"]:
            if vis["visible"]:
                granted.add(vis["key"])
    for perm_set in perm_sets:
        for vis in perm_set["visibilities"]:
            if vis["visible"]:
                granted.add(vis["key"])

    if not profiles and not perm_sets:
        return []

    findings = []
    for (obj_name, dev_name), active in sorted(record_types.items()):
        if not active:
            continue
        if (obj_name, dev_name) not in granted:
            findings.append(
                (
                    SEV_WARN,
                    f"Orphan record type '{obj_name}.{dev_name}': active, but no Profile or "
                    f"PermissionSet in this tree sets <visible>true</visible> for it. Either it is "
                    f"genuinely unused, or the carrier was not retrieved in this manifest",
                )
            )
    return findings


def check_missing_default(profiles: list[dict]) -> list[tuple[str, str]]:
    """Profile grants record types on an object but marks none of them default."""
    findings = []
    for profile in profiles:
        by_object: dict[str, list[dict]] = defaultdict(list)
        for vis in profile["visibilities"]:
            by_object[vis["key"][0]].append(vis)
        for obj_name in sorted(by_object):
            entries = by_object[obj_name]
            visible = [e for e in entries if e["visible"]]
            if not visible:
                continue
            if any(e["default"] for e in entries):
                continue
            names = ", ".join(sorted(e["key"][1] for e in visible))
            findings.append(
                (
                    SEV_ERROR,
                    f"Profile '{profile['name']}' grants {len(visible)} record type(s) on "
                    f"{obj_name} ({names}) with visible=true and default=true on none. "
                    f"PermissionSetRecordTypeVisibility has no <default> field, so no permission "
                    f"set can supply one -- these users fall back to the Master record type, "
                    f"which applies no picklist filtering",
                )
            )
    return findings


def check_missing_layout_assignment(
    record_types: dict[tuple[str, str], bool],
    profiles: list[dict],
) -> list[tuple[str, str]]:
    """Active record type that no profile assigns a layout to."""
    if not profiles:
        return []
    assigned: set[tuple[str, str]] = set()
    for profile in profiles:
        assigned |= profile["layout_record_types"]

    findings = []
    for (obj_name, dev_name), active in sorted(record_types.items()):
        if not active:
            continue
        if (obj_name, dev_name) not in assigned:
            findings.append(
                (
                    SEV_WARN,
                    f"Active record type '{obj_name}.{dev_name}' has no layoutAssignments entry "
                    f"in any Profile in this tree. Layout assignment is profile-only "
                    f"(PermissionSet has no layoutAssignments field), so no permission set can "
                    f"cover this",
                )
            )
    return findings


def check_record_type_counts(
    record_types: dict[tuple[str, str], bool],
    info_threshold: int,
    warn_threshold: int,
    profile_count: int,
) -> list[tuple[str, str]]:
    """Count active record types per object against the count guide."""
    counts: dict[str, int] = defaultdict(int)
    for (obj_name, _dev_name), active in record_types.items():
        if active:
            counts[obj_name] += 1

    findings = []
    for obj_name in sorted(counts):
        count = counts[obj_name]
        if count < warn_threshold and count <= info_threshold:
            continue
        severity = SEV_WARN if count >= warn_threshold else SEV_INFO
        msg = (
            f"Object '{obj_name}' has {count} active record types "
            f"(count guide in admin/record-types-and-page-layouts: 1-4 healthy, 5-8 monitor, "
            f"9-12 likely over-built, 13+ redesign)"
        )
        if profile_count > 0:
            msg += (
                f" -- at {profile_count} profiles that is {count * profile_count} "
                f"recordTypeVisibilities entries and {count * profile_count} layoutAssignments "
                f"entries plus one fallback per profile"
            )
        findings.append((severity, msg))
    return findings


# --------------------------------------------------------------------------
# Entry points
# --------------------------------------------------------------------------


def check_record_type_strategy_at_scale(
    manifest_dir: Path,
    info_threshold: int = 8,
    warn_threshold: int = 13,
    profile_count: int = 0,
) -> list[tuple[str, str]]:
    """Return a list of (severity, message) findings for the manifest directory."""
    if not manifest_dir.exists():
        return [(SEV_ERROR, f"Manifest directory not found: {manifest_dir}")]

    record_types = collect_record_types(manifest_dir)
    profiles = collect_profiles(manifest_dir)
    perm_sets = collect_permission_sets(manifest_dir)

    findings: list[tuple[str, str]] = []
    findings.extend(check_hardcoded_ids(manifest_dir))
    findings.extend(check_by_name_usage(manifest_dir))
    findings.extend(check_orphan_record_types(record_types, profiles, perm_sets))
    findings.extend(check_missing_default(profiles))
    findings.extend(check_missing_layout_assignment(record_types, profiles))
    findings.extend(
        check_record_type_counts(record_types, info_threshold, warn_threshold, profile_count)
    )
    return findings


def main() -> list[tuple[str, str]]:
    args = parse_args()
    findings = check_record_type_strategy_at_scale(
        Path(args.manifest_dir),
        info_threshold=args.rt_info_threshold,
        warn_threshold=args.rt_warn_threshold,
        profile_count=args.profile_count,
    )

    if not findings:
        print("No issues found.")
        return findings

    order = {SEV_ERROR: 0, SEV_WARN: 1, SEV_INFO: 2}
    for severity, message in sorted(findings, key=lambda f: order.get(f[0], 3)):
        print(f"{severity}: {message}")

    counts = defaultdict(int)
    for severity, _message in findings:
        counts[severity] += 1
    print(
        f"\n{counts[SEV_ERROR]} error(s), {counts[SEV_WARN]} warning(s), "
        f"{counts[SEV_INFO]} info."
    )
    return findings


if __name__ == "__main__":
    all_findings = main()
    if any(severity in FAILING for severity, _message in all_findings):
        sys.exit(1)
    sys.exit(0)
