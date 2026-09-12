#!/usr/bin/env python3
"""Audit Salesforce profiles and permission sets for risky access grants.

Two entry shapes, both supported:

    check_access_model.py force-app/main/default          # positional paths (legacy)
    check_access_model.py --manifest-dir force-app/main/default

Checks
------
1. HIGH   dangerous system permissions and object-level sharing bypass on any file
2. HIGH   a profile carrying object/field permissions or system permissions outside
          the documented residue allow-list -- those belong in a permission set.
          Kept blocking (not downgraded to WARN) alongside check 1: a permission
          still sitting on a profile after a permission-set-led decomposition is
          exactly the residual-access bug this skill exists to catch.
3. ERROR  a permission set carrying an element that only a Profile can hold
          (loginHours, loginIpRanges, layoutAssignments, `default` app/record type,
          tabVisibilities), which the PermissionSet schema has no home for
4. WARN   a standard profile (`custom` = false) carrying object-permission edits;
          editing standard objects on standard profiles is disabled in API 50.0+
5. INFO   the same object granted by both a profile and a permission set reachable
          through a permission set group -- redundant grant, ambiguous revocation
6. PSVP-DESC-01 (ERROR) / PSVP-DESC-02 (INFO) -- `description` length on any
          Profile, PermissionSet, or PermissionSetGroup file. PermissionSet.description
          and Profile.description are both "Limit: 255 characters" in the Metadata API
          Developer Guide (api_meta L94788, L97678). Empirically confirmed by
          `sf project deploy start --dry-run` against a Summer '26 developer org on
          2026-09-11: four PermissionSet files and three Profile files were rejected
          with `Description: data value too large ... (max length=255)`
          (examples/builds/case-onboarding/reports/MOCK-DEPLOY-M2.md, once exported).
          PermissionSetGroup.description carries no documented limit (api_meta L95328)
          -- UNVERIFIED (2026-09-11) as a direct rejection; the same 255-character
          threshold is applied here anyway because a PSG that references a rejected
          member PermissionSet fails to deploy as a cascade ("permission set names
          are invalid") regardless of its own description length. PSVP-DESC-02 is
          headroom, not a deploy risk: it is printed and counted in the JSON findings
          list but is exempt from --strict -- it never contributes to the exit code,
          unlike the WARN findings below.
7. PSVP-FLS-01 (WARN) -- a permission set grants `allowCreate` or `allowEdit` on an
          object but carries zero `fieldPermissions` on any *standard* (non-`__c`) field
          of that object. Standard fields carry field-level security exactly as custom
          fields do (api_meta L94802-L94805 documents `fieldPermissions` on
          `PermissionSet` with no standard/custom distinction), so a permission set that
          is a persona's only access source and skips every standard field is a persona
          that can create or edit the record but cannot populate the fields its layouts
          and processes actually write. Proven live: `case-onboarding` F-60 (M5 run 5) --
          a Tier 1 agent holding exactly this shape failed a fixture insert with
          `Operation failed due to fields being inaccessible on Sobject Case ...
          fieldNames: Subject,Origin,AccountId,Priority,EntitlementId`, five standard
          fields, none of them granted anywhere in the persona's permission sets. See
          `references/gotchas.md`, "An Object Grant Without Field Grants Is A Persona
          That Cannot Fill In A Form".
8. PSVP-FLS-02 (WARN) -- a `.profile-meta.xml` in the scanned tree carries zero
          `objectPermissions` and zero `fieldPermissions`, and the tree contains no
          `PermissionSetGroup` file at all. Deliberately simplified (see
          `check_empty_profile_without_group_coverage`'s docstring): it does not verify
          that a specific group grants the objects this profile's users need -- only
          that some group exists to be the claimed access source. An empty profile with
          a description that says "all access comes from the group" and zero groups
          anywhere in the same manifest-dir is a design with no reachable evidence
          behind it.

Exit policy
-----------
Exit 1 only on CRITICAL/ERROR/HIGH-class findings -- checks 1, 2, 3, and
PSVP-DESC-01. WARN/INFO findings (checks 4, 5, 7, 8, and an empty scan) print
but exit 0; pass --strict to promote those to a failure. PSVP-DESC-02 is a
separate advisory bucket: always printed and counted, never promoted by
--strict. A missing --manifest-dir is a usage error, not a finding, and exits
1 immediately with a single-line message on stderr.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


DANGEROUS_PERMISSIONS = {
    "ViewAllData",
    "ModifyAllData",
    "ManageUsers",
    "AuthorApex",
    "CustomizeApplication",
    "ManageAuthProviders",
    "SingleSignOn",
    "ApiEnabled",
}

# Elements a Profile is allowed to keep once permissions live in permission sets.
# Sourced from the Metadata API Developer Guide Profile field table: these are the
# entries with no counterpart in the PermissionSet field table.
PROFILE_RESIDUE_ELEMENTS = {
    "categoryGroupVisibilities",
    "custom",
    "description",
    "fullName",
    "layoutAssignments",
    "loginFlows",
    "loginHours",
    "loginIpRanges",
    "profileActionOverrides",
    "userLicense",
}

# Elements that exist only on Profile and therefore cannot appear in a permission set.
PROFILE_ONLY_ELEMENTS = {
    "categoryGroupVisibilities",
    "custom",
    "layoutAssignments",
    "loginFlows",
    "loginHours",
    "loginIpRanges",
    "profileActionOverrides",
    "tabVisibilities",
}

# System permissions that stay on a profile without being flagged as migratable.
# Everything else belongs in a permission set under a permission-set-led model.
PROFILE_ALLOWED_USER_PERMISSIONS: set[str] = set()

METADATA_SUFFIXES = (
    ".profile-meta.xml",
    ".permissionset-meta.xml",
    ".permissionsetgroup-meta.xml",
    ".profile",
    ".permissionset",
    ".permissionsetgroup",
)
# PSVP-DESC-01 / PSVP-DESC-02 thresholds. 255 is the Metadata API's documented
# ceiling for PermissionSet.description and Profile.description; 200 is
# headroom to catch a description before it grows past the limit.
DESC_MAX_LEN = 255
DESC_WARN_LEN = 200

SEVERITY_WEIGHTS = {
    "CRITICAL": 20,
    "ERROR": 15,
    "HIGH": 10,
    "MEDIUM": 5,
    "WARN": 3,
    "LOW": 1,
    "REVIEW": 0,
    "INFO": 0,
}


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def find_child(element: ET.Element, child_name: str) -> ET.Element | None:
    """Return the first child with this local name, or None.

    A leaf Element is falsy, so `element.find(a) or element.find(b)` silently
    discards a real match. Always compare against None.
    """
    for child in element:
        if local_name(child.tag) == child_name:
            return child
    return None


def child_text(element: ET.Element, child_name: str) -> str:
    child = find_child(element, child_name)
    if child is None:
        return ""
    return (child.text or "").strip()


def is_true(element: ET.Element, child_name: str) -> bool:
    return child_text(element, child_name).lower() == "true"


def api_name(path: Path) -> str:
    """Metadata API name for a profile/permission set file."""
    name = path.name
    for suffix in METADATA_SUFFIXES:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def iter_metadata_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            for candidate in path.rglob("*"):
                if candidate.is_file() and candidate.name.endswith(METADATA_SUFFIXES):
                    files.append(candidate)
        elif path.is_file() and path.name.endswith(METADATA_SUFFIXES):
            files.append(path)
    return sorted(set(files))


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


BLOCKING_SEVERITIES = {"CRITICAL", "ERROR", "HIGH"}


def emit_result(
    findings: list[str],
    summary: str,
    strict: bool = False,
    advisory: list[str] | None = None,
) -> int:
    """Print the JSON report and return the exit code.

    Exit 1 only on CRITICAL/ERROR/HIGH findings (platform facts that will fail
    or misbehave at deploy or run time -- dangerous grants, migratable
    permissions still on a profile, profile-only elements in a permission set,
    and PSVP-DESC-01). WARN/INFO findings (a standard-profile edit, a
    duplicate grant, an empty scan) are advisory and exit 0 so a build with
    only cosmetic findings stays green; pass --strict to promote every one of
    those to a failure.

    `advisory` is a second, always-exempt bucket -- currently PSVP-DESC-02
    headroom only. Its findings are merged into the printed/JSON output and
    counted like any other finding, but they are excluded from `blocking` and
    from the `strict` check below: headroom is informational, never a WARN
    that --strict is meant to promote.
    """
    normalized = [normalize_finding(finding) for finding in findings]
    advisory_normalized = [normalize_finding(finding) for finding in (advisory or [])]
    all_normalized = normalized + advisory_normalized
    score = max(
        0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in all_normalized)
    )
    blocking = [item for item in normalized if item["severity"] in BLOCKING_SEVERITIES]
    print(json.dumps(
        {
            "score": score,
            "findings": all_normalized,
            "summary": summary,
            "blocking": len(blocking),
        },
        indent=2,
    ))
    if all_normalized:
        print(
            f"WARN: {len(all_normalized)} finding(s) detected ({len(blocking)} blocking)",
            file=sys.stderr,
        )
    if blocking:
        return 1
    return 1 if (strict and normalized) else 0


# --------------------------------------------------------------------------- checks


def check_description_length(
    path: Path, root: ET.Element, root_type: str
) -> tuple[list[str], list[str]]:
    """PSVP-DESC-01 (ERROR, >255 chars) / PSVP-DESC-02 (INFO, >200 chars).

    Grounded for PermissionSet and Profile: Metadata API Developer Guide,
    "The permission set description. Limit: 255 characters." (api_meta
    L94788) and "The profile description. Limit: 255 characters." (api_meta
    L97678). PermissionSetGroup.description has no documented limit (api_meta
    L95328) -- UNVERIFIED (2026-09-11) as a direct rejection, applied here for
    symmetry because a PSG deploy fails as a cascade once a member
    PermissionSet it references is rejected on this exact error (verified by
    `sf project deploy start --dry-run` against a Summer '26 developer org on
    2026-09-11, examples/builds/case-onboarding/reports/MOCK-DEPLOY-M2.md,
    once exported).

    Returns (findings, advisory): PSVP-DESC-01 lands in `findings` (ERROR,
    blocking); PSVP-DESC-02 lands in `advisory` (INFO headroom, printed and
    counted by the caller, but never blocking and never promoted by
    --strict).
    """
    findings: list[str] = []
    advisory: list[str] = []
    description = child_text(root, "description")
    if not description:
        return findings, advisory
    length = len(description)
    if length > DESC_MAX_LEN:
        findings.append(
            f"ERROR {path}: PSVP-DESC-01 {root_type} description is {length} characters, "
            f"over the {DESC_MAX_LEN}-character limit; move rationale to deploy-order.md "
            "or the configuration workbook."
        )
    elif length > DESC_WARN_LEN:
        advisory.append(
            f"INFO {path}: PSVP-DESC-02 {root_type} description is {length} characters, "
            f"approaching the {DESC_MAX_LEN}-character limit."
        )
    return findings, advisory


def check_dangerous_grants(path: Path, root: ET.Element, root_type: str) -> list[str]:
    """Check 1 -- system permissions and object-level sharing bypass."""
    findings: list[str] = []

    for block in root.iter():
        tag = local_name(block.tag)

        if tag == "userPermissions":
            name = child_text(block, "name")
            if is_true(block, "enabled") and name in DANGEROUS_PERMISSIONS:
                findings.append(
                    f"HIGH {path}: {root_type} grants dangerous system permission `{name}`"
                )

        if tag == "objectPermissions":
            object_name = child_text(block, "object") or "<unknown object>"
            if is_true(block, "viewAllRecords"):
                findings.append(f"HIGH {path}: {object_name} has `viewAllRecords=true`")
            if is_true(block, "modifyAllRecords"):
                findings.append(f"HIGH {path}: {object_name} has `modifyAllRecords=true`")

    return findings


def check_profile_carries_migratable_grants(path: Path, root: ET.Element) -> list[str]:
    """Check 2 -- migratable permissions still sitting on a profile.

    HIGH, not WARN: this is a permission-set-led model's core residual-access
    bug -- a grant the design meant to move already has a permission-set
    equivalent and stayed reachable through the profile anyway.
    """
    findings: list[str] = []

    objects: list[str] = []
    fields: list[str] = []
    permissions: list[str] = []

    for block in root:
        tag = local_name(block.tag)
        if tag in PROFILE_RESIDUE_ELEMENTS:
            continue
        if tag == "objectPermissions":
            objects.append(child_text(block, "object") or "<unknown object>")
        elif tag == "fieldPermissions":
            fields.append(child_text(block, "field") or "<unknown field>")
        elif tag == "userPermissions":
            name = child_text(block, "name")
            if is_true(block, "enabled") and name not in PROFILE_ALLOWED_USER_PERMISSIONS:
                permissions.append(name or "<unnamed permission>")

    if objects:
        findings.append(
            f"HIGH {path}: profile grants object permissions on "
            f"{len(objects)} object(s) ({', '.join(sorted(set(objects))[:5])}"
            f"{', ...' if len(set(objects)) > 5 else ''}) — object CRUD has a "
            "permission-set equivalent and belongs there"
        )
    if fields:
        findings.append(
            f"HIGH {path}: profile grants field permissions on {len(fields)} field(s) "
            "— field-level security has a permission-set equivalent and belongs there"
        )
    if permissions:
        findings.append(
            f"HIGH {path}: profile enables {len(permissions)} system permission(s) "
            f"({', '.join(sorted(set(permissions))[:5])}"
            f"{', ...' if len(set(permissions)) > 5 else ''}) — `userPermissions` "
            "has a permission-set equivalent and belongs there"
        )

    return findings


def check_permission_set_holds_profile_only(path: Path, root: ET.Element) -> list[str]:
    """Check 3 -- a permission set carrying something only a profile can hold."""
    findings: list[str] = []

    for block in root:
        tag = local_name(block.tag)

        if tag in PROFILE_ONLY_ELEMENTS:
            findings.append(
                f"ERROR {path}: permission set contains `{tag}`, which exists only on "
                "the Profile metadata type — move it to the base profile"
            )
            continue

        # `default` is a Profile-only child of applicationVisibilities and
        # recordTypeVisibilities; the PermissionSet variants carry `visible` only.
        if tag in ("applicationVisibilities", "recordTypeVisibilities"):
            for child_name in ("default", "personAccountDefault"):
                if find_child(block, child_name) is not None:
                    subject = (
                        child_text(block, "application")
                        or child_text(block, "recordType")
                        or "<unnamed>"
                    )
                    findings.append(
                        f"ERROR {path}: `{tag}` for `{subject}` carries `{child_name}`, "
                        "which exists only on the Profile variant — the default stays "
                        "on the base profile"
                    )

    return findings


def check_standard_profile_edited(path: Path, root: ET.Element) -> list[str]:
    """Check 4 -- object-permission edits on a standard (`custom=false`) profile."""
    findings: list[str] = []

    custom = find_child(root, "custom")
    if custom is None or (custom.text or "").strip().lower() != "false":
        return findings

    edited = [
        local_name(block.tag)
        for block in root
        if local_name(block.tag) in ("objectPermissions", "fieldPermissions")
    ]
    if edited:
        findings.append(
            f"WARN {path}: standard profile (`custom` = false) carries "
            f"{len(edited)} object/field permission block(s); editing standard objects "
            "on standard profiles is disabled in API version 50.0 and later — clone to "
            "a custom profile before deploying this change"
        )

    return findings


def check_permission_set_object_grant_without_standard_fls(path: Path, root: ET.Element) -> list[str]:
    """Check 7 (PSVP-FLS-01, WARN) -- object Create/Edit granted with no standard-field FLS.

    Standard fields carry field-level security exactly as custom fields do -- the
    Metadata API Developer Guide's `fieldPermissions` entry on `PermissionSet` makes no
    standard/custom distinction (api_meta L94802-L94805). A permission set that grants
    `allowCreate` or `allowEdit` on an object but lists zero `fieldPermissions` for any
    of that object's *standard* (non-`__c`) fields is a persona that can create or edit
    the record but cannot populate the fields its layouts and processes actually write.

    This is exactly the case-onboarding F-60 shape: `Case_Agent_Core` granted
    Create+Edit on Case with a single custom-field grant (`Case.Severity__c`) and zero
    standard-field grants; a Tier 1 agent test user failed a fixture insert on
    `Subject, Origin, AccountId, Priority, EntitlementId`.

    WARN, not ERROR: a permission set legitimately granting Create/Edit with no
    standard-field FLS at all is unusual but not always wrong (e.g. a set scoped
    purely to a custom-field feature toggle on an object another set already covers
    for standard fields) -- the finding names the set and object so a reviewer decides.
    """
    findings: list[str] = []
    creatable_or_editable_objects: set[str] = set()
    standard_field_objects: set[str] = set()

    for block in root:
        tag = local_name(block.tag)
        if tag == "objectPermissions":
            object_name = child_text(block, "object")
            if object_name and (is_true(block, "allowCreate") or is_true(block, "allowEdit")):
                creatable_or_editable_objects.add(object_name)
        elif tag == "fieldPermissions":
            field = child_text(block, "field")
            object_name, sep, field_name = field.partition(".")
            if sep and not field_name.endswith("__c"):
                standard_field_objects.add(object_name)

    for object_name in sorted(creatable_or_editable_objects - standard_field_objects):
        findings.append(
            f"WARN {path}: PSVP-FLS-01 permission set grants Create/Edit on `{object_name}` "
            "with no field permissions on any of its standard fields — standard fields "
            "have FLS too; list the fields this persona writes"
        )

    return findings


def check_empty_profile_without_group_coverage(files: list[Path]) -> list[str]:
    """Check 8 (PSVP-FLS-02, WARN) -- an empty profile with no PSG anywhere in the tree.

    Deliberately simple, by design (see the "Exit policy" module docstring section for
    the rule statement). This does NOT verify that a specific PermissionSetGroup grants
    the objects this profile's population actually needs -- doing that precisely would
    require resolving PSG membership out to member PermissionSet objectPermissions per
    object and then asking "does *this* profile's users get *that* coverage", which the
    file's flat, per-file structure gives no link for (nothing in a Profile or
    PermissionSetGroup file names which users or profiles are meant to pair with it).
    So the check only asserts the cruder, unambiguous fact: a Profile file with zero
    `objectPermissions` and zero `fieldPermissions` exists, and not a single
    PermissionSetGroup file exists anywhere in the scanned tree to be its claimed
    access source. If a real coverage gap needs catching (this PSG doesn't grant that
    object), PSVP-FLS-01 above is the check that does it, one permission set at a time.
    """
    findings: list[str] = []
    empty_profiles: list[Path] = []
    has_any_group = False

    for path in files:
        root = parse_file(path)
        if root is None:
            continue
        root_type = local_name(root.tag)
        if root_type == "PermissionSetGroup":
            has_any_group = True
            continue
        if root_type != "Profile":
            continue
        has_object_perm = any(local_name(block.tag) == "objectPermissions" for block in root)
        has_field_perm = any(local_name(block.tag) == "fieldPermissions" for block in root)
        if not has_object_perm and not has_field_perm:
            empty_profiles.append(path)

    if not empty_profiles or has_any_group:
        return findings

    for path in empty_profiles:
        findings.append(
            f"WARN {path}: PSVP-FLS-02 profile carries zero objectPermissions and zero "
            "fieldPermissions, and no PermissionSetGroup exists anywhere in the scanned "
            "tree — if access is meant to come from a group, the group is missing from "
            "this manifest"
        )

    return findings


def check_duplicate_object_grants(files: list[Path]) -> list[str]:
    """Check 5 -- an object granted by both a profile and a PSG member."""
    findings: list[str] = []

    profile_objects: dict[str, set[str]] = {}
    permset_objects: dict[str, set[str]] = {}
    group_members: dict[str, list[str]] = {}

    for path in files:
        root = parse_file(path)
        if root is None:
            continue
        root_type = local_name(root.tag)
        name = api_name(path)

        if root_type == "PermissionSetGroup":
            members = [
                (block.text or "").strip()
                for block in root
                if local_name(block.tag) == "permissionSets" and (block.text or "").strip()
            ]
            if members:
                group_members[name] = members
            continue

        granted = {
            child_text(block, "object")
            for block in root
            if local_name(block.tag) == "objectPermissions" and child_text(block, "object")
        }
        if not granted:
            continue
        if root_type == "Profile":
            profile_objects[name] = granted
        elif root_type == "PermissionSet":
            permset_objects[name] = granted

    if not profile_objects or not group_members:
        return findings

    for group, members in sorted(group_members.items()):
        reachable: set[str] = set()
        for member in members:
            reachable |= permset_objects.get(member, set())
        if not reachable:
            continue
        for profile, granted in sorted(profile_objects.items()):
            overlap = sorted(granted & reachable)
            if overlap:
                findings.append(
                    f"INFO {profile}: object(s) {', '.join(overlap)} granted by both this "
                    f"profile and permission set group `{group}` — the duplicate grant "
                    "means removing it from one side revokes nothing"
                )

    return findings


# ----------------------------------------------------------------------------- run


def parse_file(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def audit_file(path: Path) -> tuple[list[str], list[str]]:
    """Return (findings, advisory) for one metadata file. See emit_result."""
    root = parse_file(path)
    if root is None:
        return [f"ERROR {path}: file is not well-formed XML and could not be parsed"], []

    root_type = local_name(root.tag)
    findings, advisory = check_description_length(path, root, root_type)

    if root_type == "PermissionSetGroup":
        return findings, advisory

    findings.extend(check_dangerous_grants(path, root, root_type))

    if root_type == "Profile":
        findings.extend(check_profile_carries_migratable_grants(path, root))
        findings.extend(check_standard_profile_edited(path, root))
    elif root_type == "PermissionSet":
        findings.extend(check_permission_set_holds_profile_only(path, root))
        findings.extend(check_permission_set_object_grant_without_standard_fls(path, root))

    return findings, advisory


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Salesforce profile and permission set metadata for dangerous "
            "system permissions, sharing bypass grants, migratable permissions "
            "left on a profile, and profile-only elements placed in a permission set."
        )
    )
    parser.add_argument("paths", nargs="*", help="Files or directories to scan")
    parser.add_argument(
        "--manifest-dir",
        help="Root directory of the Salesforce metadata (e.g. force-app/main/default).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on any finding, including WARN/INFO advisories.",
    )
    args = parser.parse_args()

    if args.manifest_dir and not Path(args.manifest_dir).exists():
        print(f"ERROR: --manifest-dir does not exist: {args.manifest_dir}", file=sys.stderr)
        return 1

    targets = [Path(value) for value in args.paths]
    if args.manifest_dir:
        targets.append(Path(args.manifest_dir))
    if not targets:
        targets = [Path(".")]

    files = iter_metadata_files(targets)
    if not files:
        return emit_result(
            ["WARN no profile, permission set, or permission set group metadata files found"],
            "Scanned 0 access-model metadata file(s); no files matched the provided paths.",
            strict=args.strict,
        )

    findings: list[str] = []
    advisory: list[str] = []
    for path in files:
        file_findings, file_advisory = audit_file(path)
        findings.extend(file_findings)
        advisory.extend(file_advisory)
    findings.extend(check_duplicate_object_grants(files))
    findings.extend(check_empty_profile_without_group_coverage(files))

    summary = (
        f"Scanned {len(files)} access-model metadata file(s); "
        f"{len(findings) + len(advisory)} finding(s) detected."
    )
    return emit_result(findings, summary, strict=args.strict, advisory=advisory)


if __name__ == "__main__":
    sys.exit(main())
