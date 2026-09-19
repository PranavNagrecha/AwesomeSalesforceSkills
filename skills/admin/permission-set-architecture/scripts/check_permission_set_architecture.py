#!/usr/bin/env python3
"""Checker script for the Permission Set Architecture skill.

Static checks over a Salesforce DX source tree. Stdlib only.

Checks performed:
  1. fieldPermissions with editable=true and readable not true.
     Grounded: Object Reference, FieldPermissions.PermissionsEdit "Requires
     PermissionsRead for the same field to be true"; a FieldPermissions record
     with PermissionsRead false "will be deleted". Muting permission sets are
     exempt: muting edit while leaving read alone is a valid muting shape.
  2. objectPermissions dependency chain violations.
     Grounded: Object Reference, ObjectPermissions — Create/Edit require Read,
     Delete requires Read + Edit, ViewAllRecords requires Read,
     ModifyAllRecords requires Read + Delete + Edit + ViewAllRecords.
  3. modifyAllRecords / viewAllRecords present (sharing bypass) -> WARN.
  4. Permission set with more than --max-objects objectPermissions -> INFO
     (consider slicing into object-access sets).
  5. PermissionSetGroup referencing a permissionSets / mutingPermissionSets
     member that is not present in the tree.
  6. Muting permission set whose muted entries are not granted by any member
     permission set of a group that includes it (no-op muting).
  7. Permission set with hasActivationRequired=true included in a group.
     Grounded: Object Reference, SessionPermSetActivation — session-based
     permission sets in a permission set group don't require activation.
  8. Feature-heavy custom profiles (profile-sprawl signal).
  9. PSA-DESC-01 (ERROR) / PSA-DESC-02 (INFO, headroom only — never affects
     the exit code) — description length on PermissionSet,
     MutingPermissionSet, PermissionSetGroup, and Profile files.
     Grounded: Metadata API Developer Guide, PermissionSet.description and
     Profile.description are both "Limit: 255 characters" (api_meta L94788,
     L97678); MutingPermissionSet shares PermissionSet's field table.
     Empirically confirmed by `sf project deploy start --dry-run` against a
     Summer '26 developer org on 2026-09-11: four PermissionSet files and
     three Profile files were rejected with
     `Description: data value too large ... (max length=255)`
     (examples/builds/case-onboarding/reports/MOCK-DEPLOY-M2.md, once
     exported). PermissionSetGroup.description carries no documented limit
     (api_meta L95328) — UNVERIFIED (2026-09-11) whether 255 is enforced
     directly on the group itself; the same threshold is applied here anyway
     because a PSG that references a rejected member set fails to deploy as a
     cascade ("permission set names are invalid") regardless of its own
     description length.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

SEVERITIES = ("ERROR", "WARN", "INFO")

# PSA-DESC-01 / PSA-DESC-02 thresholds. 255 is the Metadata API's documented
# ceiling for PermissionSet.description and Profile.description; 200 is
# headroom to catch a description before it grows past the limit.
DESC_MAX_LEN = 255
DESC_WARN_LEN = 200


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check permission set, permission set group, and muting permission set metadata.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--max-objects",
        type=int,
        default=8,
        help="Object permission count above which a permission set is flagged for slicing (default: 8).",
    )
    return parser.parse_args()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_xml(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def children(root: ET.Element, name: str) -> list[ET.Element]:
    """Direct children of root whose local tag name matches."""
    return [child for child in root if local_name(child.tag) == name]


def descendants(root: ET.Element, name: str) -> list[ET.Element]:
    return [elem for elem in root.iter() if local_name(elem.tag) == name]


def child_text(elem: ET.Element, name: str) -> str | None:
    """Text of the first direct child with this local name, else None.

    Never rely on element truthiness: a leaf Element is falsy in ElementTree,
    so `elem.find(a) or elem.find(b)` silently discards real matches.
    """
    for child in elem:
        if local_name(child.tag) == name:
            return (child.text or "").strip()
    return None


def is_true(elem: ET.Element, name: str) -> bool:
    value = child_text(elem, name)
    return value is not None and value.lower() == "true"


def api_name(path: Path) -> str:
    """Foo.permissionset-meta.xml -> Foo"""
    return path.name.split(".")[0]


def check_field_permissions(path: Path, root: ET.Element, issues: list[tuple[str, str]]) -> None:
    granted_objects = {
        child_text(op, "object")
        for op in descendants(root, "objectPermissions")
        if is_true(op, "allowRead")
    }
    for fp in descendants(root, "fieldPermissions"):
        field = child_text(fp, "field") or "<unnamed>"
        editable = is_true(fp, "editable")
        readable = is_true(fp, "readable")
        if editable and not readable:
            issues.append((
                "ERROR",
                f"{path}: fieldPermissions {field} has editable=true with readable not true; "
                "PermissionsEdit requires PermissionsRead and the row is otherwise deleted.",
            ))
        if "." in field:
            owner = field.split(".", 1)[0]
            has_object_row = any(
                child_text(op, "object") == owner for op in descendants(root, "objectPermissions")
            )
            if has_object_row and owner not in granted_objects:
                issues.append((
                    "ERROR",
                    f"{path}: fieldPermissions {field} grants a field on {owner}, "
                    "but this set's objectPermissions for that object do not set allowRead=true.",
                ))


def check_description_length(
    path: Path, root: ET.Element, kind: str, issues: list[tuple[str, str]]
) -> None:
    """PSA-DESC-01 (ERROR, >255 chars) / PSA-DESC-02 (INFO, >200 chars).

    PSA-DESC-02 is headroom, not a deploy risk: it is printed and counted
    under the INFO severity bucket but never affects the exit code (this
    checker only fails on ERROR; there is no --strict flag to promote it).

    Grounded for PermissionSet and Profile: Metadata API Developer Guide,
    "The permission set description. Limit: 255 characters." (api_meta
    L94788) and "The profile description. Limit: 255 characters." (api_meta
    L97678). MutingPermissionSet has the same field table as PermissionSet.
    PermissionSetGroup.description has no documented limit (api_meta L95328)
    — UNVERIFIED (2026-09-11) as a direct rejection, applied here for
    symmetry because a PSG deploy fails as a cascade once a member
    PermissionSet it references is rejected on this exact error (verified by
    `sf project deploy start --dry-run` against a Summer '26 developer org on
    2026-09-11, examples/builds/case-onboarding/reports/MOCK-DEPLOY-M2.md,
    once exported).
    """
    description = child_text(root, "description")
    if not description:
        return
    length = len(description)
    if length > DESC_MAX_LEN:
        issues.append((
            "ERROR",
            f"PSA-DESC-01 {path}: {kind} description is {length} characters, "
            f"over the {DESC_MAX_LEN}-character limit; move rationale to "
            "deploy-order.md or the configuration workbook.",
        ))
    elif length > DESC_WARN_LEN:
        issues.append((
            "INFO",
            f"PSA-DESC-02 {path}: {kind} description is {length} characters, "
            f"approaching the {DESC_MAX_LEN}-character limit.",
        ))


def check_object_permissions(
    path: Path, root: ET.Element, max_objects: int, issues: list[tuple[str, str]]
) -> None:
    object_perms = descendants(root, "objectPermissions")
    for op in object_perms:
        obj = child_text(op, "object") or "<unnamed>"
        read = is_true(op, "allowRead")
        create = is_true(op, "allowCreate")
        edit = is_true(op, "allowEdit")
        delete = is_true(op, "allowDelete")
        view_all = is_true(op, "viewAllRecords")
        modify_all = is_true(op, "modifyAllRecords")

        missing: list[str] = []
        if (create or edit) and not read:
            missing.append("allowCreate/allowEdit require allowRead")
        if delete and not (read and edit):
            missing.append("allowDelete requires allowRead and allowEdit")
        if view_all and not read:
            missing.append("viewAllRecords requires allowRead")
        if modify_all and not (read and edit and delete and view_all):
            missing.append(
                "modifyAllRecords requires allowRead, allowEdit, allowDelete, and viewAllRecords"
            )
        for reason in missing:
            issues.append((
                "ERROR",
                f"{path}: objectPermissions for {obj} violates the dependency chain ({reason}).",
            ))

        if modify_all or view_all:
            granted = "modifyAllRecords" if modify_all else "viewAllRecords"
            issues.append((
                "WARN",
                f"{path}: objectPermissions for {obj} sets {granted}=true, which bypasses sharing "
                "for that object; keep sharing overrides in a named set that is not composed into a persona group.",
            ))

    if len(object_perms) > max_objects:
        issues.append((
            "INFO",
            f"{path}: {len(object_perms)} objectPermissions entries (threshold {max_objects}); "
            "consider slicing into one object-access set per object or access level.",
        ))


def collect_granted_keys(root: ET.Element) -> set[str]:
    """Permission identities a permission set grants, for no-op muting detection."""
    keys: set[str] = set()
    for up in descendants(root, "userPermissions"):
        if is_true(up, "enabled"):
            keys.add(f"userPermission:{child_text(up, 'name')}")
    for cp in descendants(root, "customPermissions"):
        if is_true(cp, "enabled"):
            keys.add(f"customPermission:{child_text(cp, 'name')}")
    for ca in descendants(root, "classAccesses"):
        if is_true(ca, "enabled"):
            keys.add(f"apexClass:{child_text(ca, 'apexClass')}")
    for fa in descendants(root, "flowAccesses"):
        if is_true(fa, "enabled"):
            keys.add(f"flow:{child_text(fa, 'flow')}")
    for op in descendants(root, "objectPermissions"):
        if is_true(op, "allowRead"):
            keys.add(f"object:{child_text(op, 'object')}")
    for fp in descendants(root, "fieldPermissions"):
        if is_true(fp, "readable"):
            keys.add(f"field:{child_text(fp, 'field')}")
    return keys


def collect_muted_keys(root: ET.Element) -> set[str]:
    """Permission identities a muting set turns off.

    A muting set enables what it wants removed, so the element shapes match a
    permission set — but the read/edit dependency does NOT apply: muting edit
    while leaving read alone is a normal muting shape, so a field counts when
    either flag is set.
    """
    keys = collect_granted_keys(root)
    for fp in descendants(root, "fieldPermissions"):
        if is_true(fp, "editable") or is_true(fp, "readable"):
            keys.add(f"field:{child_text(fp, 'field')}")
    for op in descendants(root, "objectPermissions"):
        if any(
            is_true(op, flag)
            for flag in ("allowRead", "allowCreate", "allowEdit", "allowDelete")
        ):
            keys.add(f"object:{child_text(op, 'object')}")
    return keys


def check_permission_set_architecture(
    manifest_dir: Path, max_objects: int, scanned: list[Path] | None = None
) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []

    if not manifest_dir.exists():
        return [("ERROR", f"Manifest directory not found: {manifest_dir}")]

    permission_sets = sorted(manifest_dir.rglob("*.permissionset-meta.xml"))
    muting_sets = sorted(manifest_dir.rglob("*.mutingpermissionset-meta.xml"))
    groups = sorted(manifest_dir.rglob("*.permissionsetgroup-meta.xml"))
    profiles = sorted(manifest_dir.rglob("*.profile-meta.xml"))

    if scanned is not None:
        # Every file this run will read. An empty list means the run asserted
        # nothing, which the caller reports rather than calling it clean.
        scanned.extend(permission_sets + muting_sets + groups + profiles)

    if not (permission_sets or muting_sets or groups or profiles):
        # Nothing to check is not a failure, but it must never read as a pass:
        # a step that was meant to build a permission set and built nothing would
        # otherwise print "No issues found."
        issues.append((
            "WARN",
            f"no PermissionSet, MutingPermissionSet, PermissionSetGroup or Profile "
            f"files found under --manifest-dir ({manifest_dir}). Nothing was checked.",
        ))

    ps_roots: dict[str, ET.Element] = {}
    ps_activation: dict[str, bool] = {}
    for path in permission_sets:
        root = parse_xml(path)
        if root is None:
            issues.append(("ERROR", f"{path}: unable to parse permission set metadata."))
            continue
        ps_roots[api_name(path)] = root
        ps_activation[api_name(path)] = is_true(root, "hasActivationRequired")
        check_field_permissions(path, root, issues)
        check_object_permissions(path, root, max_objects, issues)
        check_description_length(path, root, "PermissionSet", issues)

    muting_roots: dict[str, ET.Element] = {}
    for path in muting_sets:
        root = parse_xml(path)
        if root is None:
            issues.append(("ERROR", f"{path}: unable to parse muting permission set metadata."))
            continue
        muting_roots[api_name(path)] = root
        check_description_length(path, root, "MutingPermissionSet", issues)

    for path in groups:
        root = parse_xml(path)
        if root is None:
            issues.append(("ERROR", f"{path}: unable to parse permission set group metadata."))
            continue

        check_description_length(path, root, "PermissionSetGroup", issues)

        members = [(elem.text or "").strip() for elem in children(root, "permissionSets")]
        muters = [(elem.text or "").strip() for elem in children(root, "mutingPermissionSets")]

        for member in members:
            if member and member not in ps_roots:
                issues.append((
                    "ERROR",
                    f"{path}: permissionSets member '{member}' has no "
                    f"permissionsets/{member}.permissionset-meta.xml in this tree; "
                    "the group cannot recalculate against a member that is not deployed.",
                ))
            elif ps_activation.get(member):
                issues.append((
                    "WARN",
                    f"{path}: member '{member}' has hasActivationRequired=true; inside a group "
                    "its permissions no longer require session activation and are held continuously.",
                ))

        granted: set[str] = set()
        for member in members:
            member_root = ps_roots.get(member)
            if member_root is not None:
                granted |= collect_granted_keys(member_root)

        for muter in muters:
            if muter and muter not in muting_roots:
                issues.append((
                    "ERROR",
                    f"{path}: mutingPermissionSets member '{muter}' has no "
                    f"mutingpermissionsets/{muter}.mutingpermissionset-meta.xml in this tree.",
                ))
                continue
            muted = collect_muted_keys(muting_roots[muter])
            for key in sorted(muted - granted):
                issues.append((
                    "WARN",
                    f"{path}: muting set '{muter}' mutes {key}, which no member permission set of "
                    "this group grants; the entry is a no-op and reads as a grant to a future admin.",
                ))

    if len(permission_sets) >= 12 and not groups:
        issues.append((
            "INFO",
            f"Found {len(permission_sets)} permission sets but no permission set groups; "
            "recurring access bundles may be managed as manual assignments.",
        ))

    for profile_path in profiles:
        root = parse_xml(profile_path)
        if root is None:
            issues.append(("ERROR", f"{profile_path}: unable to parse profile metadata."))
            continue
        check_description_length(profile_path, root, "Profile", issues)

    custom_profiles = [path for path in profiles if "-" not in path.stem]
    if len(custom_profiles) > 8:
        issues.append((
            "INFO",
            f"Found {len(custom_profiles)} custom profiles; review whether feature access "
            "should move into permission sets and PSGs.",
        ))

    for profile_path in custom_profiles:
        root = parse_xml(profile_path)
        if root is None:
            issues.append(("ERROR", f"{profile_path}: unable to parse profile metadata."))
            continue
        object_permissions = len(descendants(root, "objectPermissions"))
        field_permissions = len(descendants(root, "fieldPermissions"))
        class_accesses = len(descendants(root, "classAccesses"))
        if object_permissions > 18 or field_permissions > 120 or class_accesses > 20:
            issues.append((
                "INFO",
                f"{profile_path}: profile is feature-heavy ({object_permissions} object perms, "
                f"{field_permissions} field perms, {class_accesses} Apex class grants); "
                "review for profile sprawl.",
            ))

    return issues


def main() -> int:
    args = parse_args()
    scanned: list[Path] = []
    issues = check_permission_set_architecture(
        Path(args.manifest_dir), args.max_objects, scanned
    )

    if not issues:
        if not scanned:
            print("Scanned 0 file(s) — nothing asserted; check --manifest-dir")
        else:
            print("No issues found.")
        return 0

    for severity in SEVERITIES:
        for level, message in issues:
            if level == severity:
                print(f"{severity}: {message}")

    if not scanned:
        print("Scanned 0 file(s) — nothing asserted; check --manifest-dir")

    return 1 if any(level == "ERROR" for level, _ in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
