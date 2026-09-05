#!/usr/bin/env python3
"""Scan Salesforce metadata for risky sharing defaults, bypass permissions, and
sharing rules that cannot grant what they claim.

Stdlib only. Point it at a DX source directory:

    python3 check_sharing_model.py --manifest-dir force-app/main/default

or at explicit files/directories:

    python3 check_sharing_model.py force-app/main/default/sharingRules

Checks implemented (each grounded in the Metadata API Developer Guide or the
Object Reference -- see references/well-architected.md for the source list):

1. Object-wide defaults that are wider than Private, internal or external.
2. Sharing bypasses: system View All Data / Modify All Data, and object-level
   viewAllRecords / modifyAllRecords.
3. A sharing rule whose accessLevel is not above the same object's sharingModel,
   so it grants nothing. "Access level must be more permissive than the
   object's default." Skipped when the object file is not in the scanned set.
4. A criteria-based rule with no criteriaItems (shares every record), or
   missing the required includeRecordsOwnedByAll field.
5. A sharedTo / sharedFrom naming an element that is not in the documented
   SharedTo type -- most often <user>, which does not exist: a sharing rule
   cannot target one named individual.
6. More than one root Role (a role file with no parentRole).
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


SUFFIXES = (
    ".object-meta.xml",
    ".profile-meta.xml",
    ".permissionset-meta.xml",
    ".sharingRules-meta.xml",
    ".role-meta.xml",
)
SYSTEM_BYPASSES = {"ViewAllData", "ModifyAllData"}
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0, "WARN": 3}

# SharingModel enumeration, Metadata API Developer Guide "Metadata Field Types".
# Ordered by permissiveness so a grant can be compared against the default.
SHARING_MODEL_RANK = {
    "Private": 0,
    "Read": 1,
    "ReadWrite": 2,
    "ReadWriteTransfer": 3,
    "FullAccess": 4,
}
# Share-row access levels a sharing rule can ask for.
ACCESS_LEVEL_RANK = {"None": -1, "Read": 1, "Edit": 2, "All": 4}

# SharedTo type, Metadata API Developer Guide. There is deliberately no "user".
SHARED_TO_ELEMENTS = {
    "allCustomerPortalUsers",
    "allInternalUsers",
    "allPartnerUsers",
    "channelProgramGroup",
    "channelProgramGroups",
    "group",
    "groups",
    "guestUser",
    "managerSubordinates",
    "managers",
    "portalRole",
    "portalRoleandSubordinates",
    "queue",
    "role",
    "roleAndSubordinates",
    "roleAndSubordinatesInternal",
    "roles",
    "rolesAndSubordinates",
    "territories",
    "territoriesAndSubordinates",
    "territory",
    "territoryAndSubordinates",
}

RULE_CONTAINERS = {
    "sharingCriteriaRules": "criteria-based",
    "sharingOwnerRules": "owner-based",
    "sharingTerritoryRules": "territory-based",
    "sharingGuestRules": "guest",
}


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def find_child(element: ET.Element, child_name: str) -> ET.Element | None:
    """Return the first child with this local name, or None.

    Never use `element.find(a) or element.find(b)`: a leaf Element is falsy,
    so a real match with no children is silently discarded.
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


def children_named(element: ET.Element, child_name: str) -> list[ET.Element]:
    return [child for child in element if local_name(child.tag) == child_name]


def iter_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            for candidate in path.rglob("*"):
                if candidate.is_file() and candidate.name.endswith(SUFFIXES):
                    files.append(candidate)
        elif path.is_file() and path.name.endswith(SUFFIXES):
            files.append(path)
    return sorted(set(files))


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(finding) for finding in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


def object_api_name(path: Path) -> str:
    """Object API name a sharingRules or object file belongs to."""
    name = path.name
    for suffix in (".sharingRules-meta.xml", ".object-meta.xml"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def collect_sharing_models(files: list[Path]) -> dict[str, str]:
    """Map object API name -> sharingModel, for files present in this scan."""
    models: dict[str, str] = {}
    for path in files:
        if not path.name.endswith(".object-meta.xml"):
            continue
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        if local_name(root.tag) != "CustomObject":
            continue
        model = child_text(root, "sharingModel")
        if model:
            models[object_api_name(path)] = model
    return models


def audit_object(path: Path, root: ET.Element) -> list[str]:
    findings: list[str] = []
    sharing_model = child_text(root, "sharingModel")
    external_model = child_text(root, "externalSharingModel")

    if sharing_model and sharing_model not in SHARING_MODEL_RANK and not sharing_model.startswith("ControlledBy"):
        findings.append(
            f"HIGH {path}: `{sharing_model}` is not a SharingModel value "
            "(Private, Read, ReadWrite, ReadWriteTransfer, FullAccess, ControlledByParent, "
            "ControlledByCampaign, ControlledByLeadOrContact)"
        )
    elif SHARING_MODEL_RANK.get(sharing_model, 0) >= SHARING_MODEL_RANK["ReadWrite"]:
        findings.append(
            f"REVIEW {path}: internal sharing model is `{sharing_model}` - no sharing rule "
            "can grant anything more permissive than this default"
        )
    elif sharing_model == "Read":
        findings.append(
            f"REVIEW {path}: internal sharing model is `Read` (Public Read Only) - "
            "Read-level grants on this object are no longer more permissive than the default"
        )

    if external_model and external_model in SHARING_MODEL_RANK and external_model != "Private":
        findings.append(
            f"REVIEW {path}: external sharing model is `{external_model}` - "
            "confirm external users are meant to see records they do not own"
        )
    if (
        external_model in SHARING_MODEL_RANK
        and sharing_model in SHARING_MODEL_RANK
        and SHARING_MODEL_RANK[external_model] > SHARING_MODEL_RANK[sharing_model]
    ):
        findings.append(
            f"MEDIUM {path}: externalSharingModel `{external_model}` is more permissive than "
            f"internal sharingModel `{sharing_model}` - external users would see more than internal ones"
        )
    return findings


def audit_permissions(path: Path, root: ET.Element) -> list[str]:
    findings: list[str] = []
    for block in root.iter():
        tag_name = local_name(block.tag)
        if tag_name == "userPermissions":
            name = child_text(block, "name")
            enabled = child_text(block, "enabled").lower() == "true"
            if enabled and name in SYSTEM_BYPASSES:
                findings.append(f"HIGH {path}: system bypass permission `{name}` enabled")
        if tag_name == "objectPermissions":
            object_name = child_text(block, "object") or "<unknown object>"
            if child_text(block, "viewAllRecords").lower() == "true":
                findings.append(f"HIGH {path}: `{object_name}` has viewAllRecords=true")
            if child_text(block, "modifyAllRecords").lower() == "true":
                findings.append(f"HIGH {path}: `{object_name}` has modifyAllRecords=true")
    return findings


def audit_shared_to(path: Path, rule_name: str, block: ET.Element, element_name: str) -> list[str]:
    findings: list[str] = []
    target = find_child(block, element_name)
    if target is None:
        return findings
    for child in target:
        name = local_name(child.tag)
        if name in SHARED_TO_ELEMENTS:
            continue
        if name == "user":
            findings.append(
                f"HIGH {path}: rule `{rule_name}` has `<user>` in `{element_name}` - the SharedTo "
                "type has no user element; use a public group, or manual/Apex managed sharing "
                "for one individual"
            )
        else:
            findings.append(
                f"HIGH {path}: rule `{rule_name}` has unknown `{element_name}` element `<{name}>`"
            )
    return findings


def audit_sharing_rules(path: Path, root: ET.Element, sharing_models: dict[str, str]) -> list[str]:
    findings: list[str] = []
    obj = object_api_name(path)
    owd = sharing_models.get(obj)

    for container, kind in RULE_CONTAINERS.items():
        for block in children_named(root, container):
            rule_name = child_text(block, "fullName") or child_text(block, "label") or "<unnamed>"
            access_level = child_text(block, "accessLevel")

            if not access_level:
                findings.append(
                    f"HIGH {path}: {kind} rule `{rule_name}` has no `accessLevel` (required on SharingBaseRule)"
                )
            elif owd is not None:
                owd_rank = SHARING_MODEL_RANK.get(owd)
                grant_rank = ACCESS_LEVEL_RANK.get(access_level)
                if owd_rank is not None and grant_rank is not None and grant_rank <= owd_rank:
                    findings.append(
                        f"HIGH {path}: {kind} rule `{rule_name}` grants `{access_level}` but "
                        f"`{obj}` has sharingModel `{owd}` - the grant is not above the object's "
                        "default, so it adds no access"
                    )

            if find_child(block, "sharedTo") is None:
                findings.append(
                    f"HIGH {path}: {kind} rule `{rule_name}` has no `sharedTo` (required on SharingBaseRule)"
                )
            findings.extend(audit_shared_to(path, rule_name, block, "sharedTo"))
            findings.extend(audit_shared_to(path, rule_name, block, "sharedFrom"))

            if container == "sharingOwnerRules" and find_child(block, "sharedFrom") is None:
                findings.append(
                    f"HIGH {path}: owner-based rule `{rule_name}` has no `sharedFrom` (required on SharingOwnerRule)"
                )

            if container == "sharingCriteriaRules":
                if not children_named(block, "criteriaItems"):
                    findings.append(
                        f"HIGH {path}: criteria-based rule `{rule_name}` has no `criteriaItems` - "
                        "it matches every record on the object"
                    )
                if find_child(block, "includeRecordsOwnedByAll") is None:
                    findings.append(
                        f"MEDIUM {path}: criteria-based rule `{rule_name}` has no "
                        "`includeRecordsOwnedByAll` - it is required, and cannot be edited "
                        "after the rule is created"
                    )
    return findings


def audit_file(path: Path, sharing_models: dict[str, str]) -> list[str]:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"HIGH {path}: file is not well-formed XML ({exc})"]

    findings: list[str] = []
    root_type = local_name(root.tag)

    if root_type == "CustomObject":
        findings.extend(audit_object(path, root))
    if root_type == "SharingRules":
        findings.extend(audit_sharing_rules(path, root, sharing_models))
    findings.extend(audit_permissions(path, root))
    return findings


def audit_roles(files: list[Path]) -> list[str]:
    roots: list[Path] = []
    for path in files:
        if not path.name.endswith(".role-meta.xml"):
            continue
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        if local_name(root.tag) != "Role":
            continue
        if find_child(root, "parentRole") is None:
            roots.append(path)
    if len(roots) > 1:
        listed = ", ".join(path.name for path in roots)
        return [
            f"WARN {roots[0].parent}: {len(roots)} role files have no `parentRole` "
            f"({listed}) - a hierarchy has one root; extra roots are usually a missing parent"
        ]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Salesforce metadata for risky sharing defaults, bypass grants, and unusable sharing rules."
    )
    parser.add_argument(
        "--manifest-dir",
        action="append",
        default=[],
        help="DX source directory to scan, e.g. force-app/main/default (repeatable)",
    )
    parser.add_argument("paths", nargs="*", help="Additional files or directories to scan")
    args = parser.parse_args()

    targets = [Path(value) for value in list(args.manifest_dir) + list(args.paths)]
    if not targets:
        parser.error("give --manifest-dir or at least one path")

    files = iter_files(targets)
    if not files:
        return emit_result(
            ["HIGH no object, profile, permission set, sharing rule, or role metadata files found"],
            "Scanned 0 sharing-model metadata file(s); no files matched the provided paths.",
        )

    sharing_models = collect_sharing_models(files)

    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path, sharing_models))
    findings.extend(audit_roles(files))

    summary = (
        f"Scanned {len(files)} sharing-model metadata file(s) "
        f"({len(sharing_models)} object OWD(s) resolved); {len(findings)} finding(s) detected."
    )
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
