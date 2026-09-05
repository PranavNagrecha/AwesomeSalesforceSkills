#!/usr/bin/env python3
"""Checker for the Delegated Administration skill.

Inspects retrieved Salesforce metadata for privilege-escalation paths and dead
configuration in ``DelegateGroup`` files.

Grounded in the Metadata API Developer Guide, ``DelegateGroup`` type
(https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf):

- Fields are ``customObjects``, ``groups``, ``label`` (required),
  ``loginAccess`` (required boolean), ``permissionSetGroups``,
  ``permissionSets``, ``profiles``, ``roles`` -- every one but ``label`` and
  ``loginAccess`` is a ``string[]`` of bare names.
- ``roles`` is "the roles and subordinates for which delegated administrators
  of the group can create and edit users" -- the only field that scopes *which*
  users are managed.
- ``loginAccess`` "allows users in this group to log in as users in the role
  hierarchy that they administer".
- "Only users with the 'View Setup and Configuration' permission can be
  delegated administrators."

Stdlib only -- no pip dependencies.

Usage:
    python3 check_delegated_administration.py --manifest-dir force-app/main/default
    python3 check_delegated_administration.py --manifest-dir <dir> --quiet

Exit codes: 0 = no ERROR findings, 1 = at least one ERROR.

Run it over a *full* retrieve (``sf project retrieve start --metadata
DelegateGroup --metadata Role --metadata Profile --metadata PermissionSet``).
Over a partial retrieve, the dangling-reference warnings are all false.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Profiles that hand a delegated administrator the keys to the org.
BLOCKED_PROFILE_NAMES = {
    "system administrator",
    "systemadministrator",
    "admin",
}

# Permissions that make a listed profile / permission set an escalation path.
ESCALATION_PERMISSIONS = (
    "ModifyAllData",
    "ViewAllData",
    "AuthorApex",
    "ManageProfilesPermissionsets",
)

# The permission the guide names as the prerequisite for being a delegated admin.
DELEGATED_ADMIN_ENTRY_PERMISSION = "ViewSetup"

# Where each DelegateGroup list field's targets live in a DX / MDAPI tree, and
# which file-name stem identifies one target.
REFERENCE_DIRS = {
    "roles": ("roles", (".role", ".role-meta.xml")),
    "profiles": ("profiles", (".profile", ".profile-meta.xml")),
    "permissionSets": ("permissionsets", (".permissionset", ".permissionset-meta.xml")),
    "permissionSetGroups": (
        "permissionsetgroups",
        (".permissionsetgroup", ".permissionsetgroup-meta.xml"),
    ),
    "customObjects": ("objects", (".object", ".object-meta.xml")),
}


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------


def _tag(name: str) -> str:
    return f"{{{SF_NS}}}{name}"


def _parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file; return the root element, or None if it will not parse."""
    try:
        return ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None


def _child(parent: ET.Element, name: str) -> ET.Element | None:
    """Return the first child named `name`, namespaced or not.

    Never use `parent.find(a) or parent.find(b)` -- an Element with no children
    is falsy, so a real match would be discarded. Test `is not None` explicitly.
    """
    found = parent.find(_tag(name))
    if found is None:
        found = parent.find(name)
    return found


def _children(parent: ET.Element, name: str) -> list[ET.Element]:
    """Return every descendant named `name`, namespaced or not."""
    found = parent.findall(f".//{_tag(name)}")
    if not found:
        found = parent.findall(f".//{name}")
    return found


def _text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return (element.text or "").strip()


def _values(root: ET.Element, name: str) -> list[str]:
    """Return the non-empty text of every `name` element under root."""
    return [t for t in (_text(el) for el in _children(root, name)) if t]


# ---------------------------------------------------------------------------
# Metadata discovery
# ---------------------------------------------------------------------------


def _stem(path: Path) -> str:
    """Strip both `.foo` and `.foo-meta.xml` to get the developer name."""
    name = path.name
    if name.endswith("-meta.xml"):
        name = name[: -len("-meta.xml")]
    return name.rsplit(".", 1)[0]


def _find_type_dir(manifest_dir: Path, folder: str) -> Path | None:
    """Locate a metadata folder anywhere under the manifest dir, case-insensitively."""
    if manifest_dir.name.lower() == folder.lower():
        return manifest_dir
    direct = manifest_dir / folder
    if direct.is_dir():
        return direct
    for candidate in manifest_dir.rglob("*"):
        if candidate.is_dir() and candidate.name.lower() == folder.lower():
            return candidate
    return None


def _names_in_dir(manifest_dir: Path, folder: str, suffixes: tuple[str, ...]) -> set[str] | None:
    """Return developer names present for a metadata type, or None if not retrieved."""
    type_dir = _find_type_dir(manifest_dir, folder)
    if type_dir is None:
        return None
    names: set[str] = set()
    for path in type_dir.rglob("*"):
        if not path.is_file():
            continue
        lowered = path.name.lower()
        if any(lowered.endswith(sfx) for sfx in suffixes):
            names.add(_stem(path))
    return names or None


def _find_delegate_group_files(manifest_dir: Path) -> list[Path]:
    group_dir = _find_type_dir(manifest_dir, "delegateGroups")
    search_root = group_dir if group_dir is not None else manifest_dir
    files = [
        p
        for p in search_root.rglob("*")
        if p.is_file() and p.name.lower().endswith((".delegategroup", ".delegategroup-meta.xml"))
    ]
    return sorted(files)


def _permission_file_for(manifest_dir: Path, folder: str, suffixes: tuple[str, ...], name: str) -> Path | None:
    type_dir = _find_type_dir(manifest_dir, folder)
    if type_dir is None:
        return None
    for path in type_dir.rglob("*"):
        if path.is_file() and any(path.name.lower().endswith(s) for s in suffixes) and _stem(path) == name:
            return path
    return None


def _granted_permissions(path: Path) -> set[str]:
    """Return the userPermission names enabled in a .profile / .permissionset file."""
    root = _parse_xml_safe(path)
    if root is None:
        return set()
    granted: set[str] = set()
    for block in _children(root, "userPermissions"):
        name = _text(_child(block, "name"))
        enabled = _text(_child(block, "enabled")).lower()
        if name and enabled == "true":
            granted.add(name)
    return granted


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_delegate_group(path: Path, manifest_dir: Path) -> list[tuple[str, str]]:
    """Return (severity, message) findings for a single DelegateGroup file."""
    findings: list[tuple[str, str]] = []
    group = _stem(path)
    root = _parse_xml_safe(path)
    if root is None:
        findings.append(("ERROR", f"[{group}] could not be parsed as XML -- the file is malformed."))
        return findings

    roles = _values(root, "roles")
    profiles = _values(root, "profiles")
    permission_sets = _values(root, "permissionSets")
    permission_set_groups = _values(root, "permissionSetGroups")
    custom_objects = _values(root, "customObjects")
    public_groups = _values(root, "groups")
    label = _text(_child(root, "label"))
    login_access = _text(_child(root, "loginAccess")).lower()

    # Check 1 -- required fields. The guide marks label and loginAccess Required.
    if not label:
        findings.append(("ERROR", f"[{group}] no <label>. The guide marks label required (the delegated group's non-API name)."))
    if login_access not in ("true", "false"):
        findings.append(
            ("ERROR", f"[{group}] <loginAccess> is missing or not a boolean (found {login_access!r}). The guide marks it required.")
        )

    # Check 2 -- loginAccess true is an impersonation grant, not a detail.
    if login_access == "true":
        findings.append(
            (
                "WARN",
                f"[{group}] loginAccess is true: every administrator in this group can log in as the users "
                f"in the {len(roles) or 'configured'} role branch(es) it administers. Confirm this was a decision, "
                f"and record it as a privileged-access grant (references/gotchas.md #6).",
            )
        )

    # Check 3 -- no roles means the group manages nobody.
    if not roles:
        findings.append(
            (
                "INFO",
                f"[{group}] no <roles>: this group can manage no users. That is correct for a custom-object-only "
                f"group; if user administration was intended, add the role branches it should cover.",
            )
        )
        dead = []
        if profiles:
            dead.append(f"{len(profiles)} profile(s)")
        if permission_sets:
            dead.append(f"{len(permission_sets)} permission set(s)")
        if permission_set_groups:
            dead.append(f"{len(permission_set_groups)} permission set group(s)")
        if public_groups:
            dead.append(f"{len(public_groups)} public group(s)")
        if dead:
            findings.append(
                (
                    "WARN",
                    f"[{group}] lists {', '.join(dead)} but has no <roles>. The guide scopes those fields to "
                    f"'users in specified roles and all subordinate roles', so they are dead configuration here.",
                )
            )
    if not roles and not custom_objects:
        findings.append(("WARN", f"[{group}] has neither <roles> nor <customObjects>: the group delegates nothing."))

    # Check 4 -- assignable profiles that are the org's keys.
    for profile in profiles:
        if profile.strip().lower() in BLOCKED_PROFILE_NAMES:
            findings.append(
                (
                    "ERROR",
                    f"[{group}] assignable profile '{profile}' lets any delegated administrator in this group "
                    f"create full administrators. Remove it; there is no legitimate delegated use for it.",
                )
            )

    # Check 5 -- listed profiles / permission sets that carry escalation permissions.
    targets = [("profiles", profiles, "profiles", (".profile", ".profile-meta.xml"))]
    targets.append(("permissionSets", permission_sets, "permissionsets", (".permissionset", ".permissionset-meta.xml")))
    for field, names, folder, suffixes in targets:
        for name in names:
            perm_file = _permission_file_for(manifest_dir, folder, suffixes, name)
            if perm_file is None:
                continue
            escalations = sorted(_granted_permissions(perm_file) & set(ESCALATION_PERMISSIONS))
            if escalations:
                findings.append(
                    (
                        "ERROR",
                        f"[{group}] <{field}> names '{name}', whose file ({perm_file.name}) enables "
                        f"{', '.join(escalations)}. Delegated administrators could grant that to any user in scope. "
                        f"Split the permission out or drop the entry (references/gotchas.md #9).",
                    )
                )

    # Check 6 -- dangling name references. Every field is a bare string[].
    reference_fields = {
        "roles": roles,
        "profiles": profiles,
        "permissionSets": permission_sets,
        "permissionSetGroups": permission_set_groups,
        "customObjects": custom_objects,
    }
    for field, names in reference_fields.items():
        if not names:
            continue
        folder, suffixes = REFERENCE_DIRS[field]
        present = _names_in_dir(manifest_dir, folder, suffixes)
        if present is None:
            continue  # type not in this retrieve -- cannot judge
        for name in names:
            if name not in present:
                findings.append(
                    (
                        "WARN",
                        f"[{group}] <{field}> names '{name}', which has no matching file under {folder}/. "
                        f"Either the retrieve is partial, or the name is stale after a rename "
                        f"(references/gotchas.md #11).",
                    )
                )

    return findings


def check_entry_permission(manifest_dir: Path) -> list[tuple[str, str]]:
    """Report which retrieved profiles / permission sets grant ViewSetup.

    The guide: "Only users with the 'View Setup and Configuration' permission
    can be delegated administrators." A delegate group grants scope, not entry.
    """
    findings: list[tuple[str, str]] = []
    holders: list[str] = []
    for folder, suffixes in (
        ("profiles", (".profile", ".profile-meta.xml")),
        ("permissionsets", (".permissionset", ".permissionset-meta.xml")),
    ):
        type_dir = _find_type_dir(manifest_dir, folder)
        if type_dir is None:
            continue
        for path in sorted(type_dir.rglob("*")):
            if not path.is_file() or not any(path.name.lower().endswith(s) for s in suffixes):
                continue
            if DELEGATED_ADMIN_ENTRY_PERMISSION in _granted_permissions(path):
                holders.append(_stem(path))
    if holders:
        findings.append(
            (
                "INFO",
                f"{DELEGATED_ADMIN_ENTRY_PERMISSION} (View Setup and Configuration) is granted by: "
                f"{', '.join(sorted(holders))}. A delegated administrator needs it from one of these; "
                f"group membership alone grants no Setup entry (references/gotchas.md #1).",
            )
        )
    return findings


def check_delegated_administration(manifest_dir: Path) -> list[tuple[str, str]]:
    if not manifest_dir.exists():
        return [("ERROR", f"Manifest directory not found: {manifest_dir}")]

    group_files = _find_delegate_group_files(manifest_dir)
    if not group_files:
        return [
            (
                "INFO",
                f"No .delegateGroup or .delegateGroup-meta.xml files under {manifest_dir}. "
                f"Retrieve them with: sf project retrieve start --metadata DelegateGroup",
            )
        ]

    findings: list[tuple[str, str]] = []
    for path in group_files:
        findings.extend(check_delegate_group(path, manifest_dir))
    findings.extend(check_entry_permission(manifest_dir))
    return findings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check DelegateGroup metadata for escalation paths and dead configuration.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the retrieved Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only ERROR and WARN findings.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    findings = check_delegated_administration(Path(args.manifest_dir))

    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    findings.sort(key=lambda f: (order.get(f[0], 3), f[1]))

    shown = [f for f in findings if not (args.quiet and f[0] == "INFO")]
    for severity, message in shown:
        print(f"{severity}: {message}")

    errors = sum(1 for severity, _ in findings if severity == "ERROR")
    warns = sum(1 for severity, _ in findings if severity == "WARN")
    if not shown:
        print("No delegated administration findings.")
    print(f"\n{errors} error(s), {warns} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
