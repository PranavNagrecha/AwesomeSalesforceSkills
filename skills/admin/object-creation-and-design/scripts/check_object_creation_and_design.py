#!/usr/bin/env python3
"""Checker script for the Object Creation and Design skill.

Scans Salesforce metadata (SFDX source format or retrieved metadata) for custom
object configuration problems that the platform will not warn you about.

Checks performed on each ``*.object-meta.xml`` whose file name ends in ``__c``:

1.  ISSUE  — missing or empty ``<description>``.
2.  ISSUE  — very short object API name (likely an unreadable abbreviation).
3.  ISSUE  — ``<enableHistory>true</enableHistory>`` with no field marked
    ``<trackHistory>true</trackHistory>``, counting both fields nested in the
    object file (Metadata API shape) and fields in the sibling ``fields/``
    folder (DX source shape). History tracking that selects nothing captures
    nothing.
4.  ISSUE  — more than 20 fields marked for tracking. "Up to a total of twenty
    fields (standard or custom) can be tracked for a given object"
    (Object Reference, EntityHistory usage notes).
5.  ISSUE  — ``<nameField>`` of ``<type>AutoNumber</type>`` with no
    ``<displayFormat>``.
6.  ISSUE  — ``enableBulkApi`` / ``enableSharing`` / ``enableStreamingApi`` set
    inconsistently. Each element's description in the Metadata API Developer
    Guide states that the other two must also be enabled.
7.  WARN   — ``<deploymentStatus>InDevelopment</deploymentStatus>``. Objects
    left in development are invisible to non-admin users.
8.  WARN   — ``<sharingModel>ReadWrite</sharingModel>`` (Public Read/Write).
    Confirm this is intentional; an OWD cannot be tightened later without a
    full sharing recalculation.
9.  WARN   — many custom objects in one source tree, relative to common
    edition allocations.
10. OCD-DESC-01 (ISSUE) — a ``CustomObject`` ``<description>`` over 1000
    characters. Grounded directly: "A description of the object. Maximum of
    1000 characters." (Metadata API Developer Guide, CustomObject field table
    — api_meta.txt L42007). This is a different field, on a different type,
    from the 255-character ceiling documented for CustomPermission,
    PermissionSet, Profile and RecordType descriptions — do not reuse that
    number here.
11. OCD-DESC-02 (INFO, advisory — does not affect exit code) — any
    ``CustomObject`` or ``CustomField`` ``<description>`` over 200 characters.
    For ``CustomField`` there is no documented ceiling at all: the guide
    states only "Description of the field." with no ``Limit:`` clause
    anywhere in the CustomField field table (api_meta.txt L43360; section
    header confirmed at L43379). UNVERIFIED (2026-09-11): whether the
    255-character ceiling that applies to CustomPermission / PermissionSet /
    Profile / RecordType descriptions also applies to CustomField — until
    that is confirmed against a live org, this checker raises no ISSUE for a
    long CustomField description, only the WARN headroom hint.

Stdlib only. Exit code 1 if any of checks 1-6, 10 fired, or if any WARN from
checks 7-9 fired — that combined ISSUE-or-WARN policy is unchanged from
before this file added description-length checking. OCD-DESC-02 (check 11) is
the one exception: it is an INFO-level headroom hint, not a deploy-breaking
condition, so it is printed and counted but never contributes to the exit
code, even alone in an otherwise-clean tree.

Usage:
    python3 check_object_creation_and_design.py
    python3 check_object_creation_and_design.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SALESFORCE_NAMESPACE = "http://soap.sforce.com/2006/04/metadata"

# Minimum meaningful API name length (before __c) to flag as potentially ambiguous
MIN_API_NAME_LENGTH = 4

# Object Reference, EntityHistory usage notes: "Up to a total of twenty fields
# (standard or custom) can be tracked for a given object."
MAX_TRACKED_FIELDS = 20

# Metadata API Developer Guide, CustomObject fields: enableBulkApi, enableSharing
# and enableStreamingApi each require the other two to be enabled.
ENTERPRISE_APP_TRIO = ("enableBulkApi", "enableSharing", "enableStreamingApi")

# OCD-DESC-01: CustomObject.description is grounded directly in the Metadata
# API Developer Guide's CustomObject field table: "A description of the
# object. Maximum of 1000 characters." (api_meta.txt L42007). This is a
# different field, on a different type, from the 255-character ceiling
# documented for CustomPermission, PermissionSet, Profile and RecordType
# descriptions elsewhere in the same guide — do not reuse that number here.
OBJECT_DESC_MAX_LEN = 1000

# OCD-DESC-02 candidate ceiling for CustomField: the guide states only
# "Description of the field." with no `Limit:` clause anywhere in the
# CustomField field table (api_meta.txt L43360; CustomField section header
# confirmed at L43379). UNVERIFIED (2026-09-11): whether the 255-character
# ceiling used elsewhere in the guide also applies to CustomField. Carried
# here only as a documentation reference for the WARN message below — it is
# never enforced as an ERROR/ISSUE threshold.
FIELD_DESC_UNVERIFIED_CANDIDATE_LEN = 255  # UNVERIFIED (2026-09-11)

# OCD-DESC-02 headroom warning, shared by CustomObject and CustomField alike.
# Not tied to either type's own ceiling — just a "this is getting long, keep
# it terse" signal, consistent with keeping <description> a one-line label
# (rationale belongs in deploy-order.md or the configuration workbook).
DESC_WARN_LEN = 200


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check custom object configuration for common design issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata source (default: current directory).",
    )
    return parser.parse_args()


def find_object_files(manifest_dir: Path) -> list[Path]:
    """Locate .object-meta.xml files in the manifest directory tree."""
    return list(manifest_dir.rglob("*.object-meta.xml"))


def find_field_files(manifest_dir: Path) -> list[Path]:
    """Locate .field-meta.xml files anywhere in the manifest directory tree.

    Independent of find_object_files: a custom field's parent object file
    (e.g. a standard object like Account) may not itself be present in a
    partial manifest, but the field's own <description> length is still
    checkable (OCD-DESC-02).
    """
    return list(manifest_dir.rglob("*.field-meta.xml"))


def _tag(local_name: str) -> str:
    return f"{{{SALESFORCE_NAMESPACE}}}{local_name}"


def child_text(element: ET.Element | None, local_name: str) -> str:
    """Return the stripped text of a direct child, or '' if absent or empty.

    A leaf Element is falsy, so `element.find(x) or element.find(y)` is a trap.
    Every lookup here tests `is not None` explicitly.
    """
    if element is None:
        return ""
    child = element.find(_tag(local_name))
    if child is None:
        return ""
    return (child.text or "").strip()


def is_true(element: ET.Element | None, local_name: str) -> bool:
    return child_text(element, local_name).lower() == "true"


def has_child(element: ET.Element | None, local_name: str) -> bool:
    if element is None:
        return False
    return element.find(_tag(local_name)) is not None


def collect_tracked_fields(root: ET.Element, obj_path: Path) -> list[str]:
    """Return the API names of every field marked <trackHistory>true</trackHistory>.

    Looks in two places, because both metadata shapes occur in the wild:
      * <fields> elements nested in the object file (Metadata API .object shape)
      * <Name>.field-meta.xml files in the sibling fields/ folder (DX source shape)
    """
    tracked: list[str] = []

    for field in root.findall(_tag("fields")):
        if is_true(field, "trackHistory"):
            tracked.append(child_text(field, "fullName") or "(unnamed nested field)")

    fields_dir = obj_path.parent / "fields"
    if fields_dir.is_dir():
        for field_path in sorted(fields_dir.glob("*.field-meta.xml")):
            try:
                field_root = ET.parse(field_path).getroot()
            except ET.ParseError:
                continue
            if is_true(field_root, "trackHistory"):
                tracked.append(field_path.name.replace(".field-meta.xml", ""))

    return tracked


def check_object_file(obj_path: Path) -> tuple[list[str], list[str]]:
    """Return (issues, advisory) for a single custom object metadata file.

    `issues` feeds the checker's existing exit policy (any entry -> exit 1),
    unchanged from before this file had description-length checks. `advisory`
    holds OCD-DESC-02 only: printed, but never contributes to the exit code.
    """
    issues: list[str] = []
    advisory: list[str] = []

    try:
        tree = ET.parse(obj_path)
    except ET.ParseError as exc:
        issues.append(f"ISSUE: {obj_path.name}: XML parse error — {exc}")
        return issues, advisory

    root = tree.getroot()

    # Derive object API name from file name (e.g. "Project_Request__c.object-meta.xml")
    file_stem = obj_path.name.replace(".object-meta.xml", "")

    # Only check custom objects (ending in __c), skip standard objects
    if not file_stem.endswith("__c"):
        return issues, advisory

    local_name = file_stem[: -len("__c")]

    # 1. Flag objects with very short API names (potentially ambiguous abbreviations)
    if len(local_name) < MIN_API_NAME_LENGTH:
        issues.append(
            f"ISSUE: {file_stem}: Object API name '{local_name}' is very short "
            f"({len(local_name)} chars). Short names are often abbreviations that "
            f"reduce readability. The API name cannot be changed after save."
        )

    # 2. Check for a description element, and its length (OCD-DESC-01 / OCD-DESC-02).
    description = child_text(root, "description")
    if not description:
        issues.append(
            f"ISSUE: {file_stem}: Missing or empty <description>. "
            "Add a description recording the object's purpose, the reason each "
            "irreversible feature is enabled, and the Auto Number starting number "
            "(which cannot be retrieved through Metadata API)."
        )
    else:
        desc_len = len(description)
        if desc_len > OBJECT_DESC_MAX_LEN:
            issues.append(
                f"ISSUE: {file_stem}: OCD-DESC-01 <description> is {desc_len} characters, "
                f"over the {OBJECT_DESC_MAX_LEN}-character limit documented for CustomObject "
                "(Metadata API Developer Guide, CustomObject.description — api_meta.txt "
                "L42007). The deploy will be rejected."
            )
        elif desc_len > DESC_WARN_LEN:
            advisory.append(
                f"INFO: {file_stem}: OCD-DESC-02 <description> is {desc_len} characters, "
                f"approaching the {OBJECT_DESC_MAX_LEN}-character CustomObject limit "
                "(api_meta.txt L42007). Keep it terse — move rationale for irreversible "
                "feature choices to the build's deploy-order.md or the configuration "
                "workbook."
            )

    # 3/4. History tracking: enabled but capturing nothing, or over the ceiling.
    if is_true(root, "enableHistory"):
        tracked = collect_tracked_fields(root, obj_path)
        if not tracked:
            issues.append(
                f"ISSUE: {file_stem}: <enableHistory>true</enableHistory> but no field "
                "has <trackHistory>true</trackHistory> in the object file or in the "
                "sibling fields/ folder. History tracking is on and capturing nothing."
            )
        elif len(tracked) > MAX_TRACKED_FIELDS:
            issues.append(
                f"ISSUE: {file_stem}: {len(tracked)} fields marked <trackHistory>true"
                f"</trackHistory>; the platform ceiling is {MAX_TRACKED_FIELDS} per object. "
                f"Deploy will fail. Fields: {', '.join(sorted(tracked))}"
            )
    else:
        orphan_tracked = collect_tracked_fields(root, obj_path)
        if orphan_tracked:
            issues.append(
                f"ISSUE: {file_stem}: {len(orphan_tracked)} field(s) set "
                "<trackHistory>true</trackHistory> but the object does not set "
                "<enableHistory>true</enableHistory>. trackHistory requires enableHistory "
                f"on the object. Fields: {', '.join(sorted(orphan_tracked))}"
            )

    # 5. Auto Number name field with no display format.
    name_field = root.find(_tag("nameField"))
    if name_field is not None:
        name_type = child_text(name_field, "type")
        if name_type == "AutoNumber" and not child_text(name_field, "displayFormat"):
            issues.append(
                f"ISSUE: {file_stem}: <nameField> is AutoNumber but has no "
                "<displayFormat>. Records will be named with a bare sequence number "
                "instead of a readable identifier such as REQ-{00000}."
            )
        if name_type != "AutoNumber" and has_child(name_field, "displayFormat"):
            issues.append(
                f"ISSUE: {file_stem}: <nameField> has <displayFormat> but its type is "
                f"'{name_type or '(unset)'}'. displayFormat applies to AutoNumber only."
            )

    # 6. The Enterprise Application trio must be set consistently.
    trio_present = [e for e in ENTERPRISE_APP_TRIO if has_child(root, e)]
    trio_true = [e for e in ENTERPRISE_APP_TRIO if is_true(root, e)]
    if trio_true and len(trio_true) != len(ENTERPRISE_APP_TRIO):
        missing = [e for e in ENTERPRISE_APP_TRIO if e not in trio_true]
        issues.append(
            f"ISSUE: {file_stem}: {', '.join(trio_true)} set true but "
            f"{', '.join(missing)} not enabled. The Metadata API Developer Guide "
            "requires all three of enableBulkApi, enableSharing and enableStreamingApi "
            "to be enabled together."
        )
    elif trio_present and len(trio_present) != len(ENTERPRISE_APP_TRIO):
        missing = [e for e in ENTERPRISE_APP_TRIO if e not in trio_present]
        issues.append(
            f"WARN: {file_stem}: {', '.join(trio_present)} present but "
            f"{', '.join(missing)} absent from the file. Set all three explicitly or "
            "none of them, so a redeploy cannot flip the object's classification."
        )

    # 7. Deployment status.
    if child_text(root, "deploymentStatus") == "InDevelopment":
        issues.append(
            f"WARN: {file_stem}: <deploymentStatus>InDevelopment</deploymentStatus>. "
            "The object is invisible to non-admin users. Set Deployed before go-live."
        )

    # 8. Public Read/Write OWD.
    sharing_model = child_text(root, "sharingModel")
    if sharing_model == "ReadWrite":
        issues.append(
            f"WARN: {file_stem}: <sharingModel>ReadWrite</sharingModel> is Public "
            "Read/Write — every internal user can edit every record. Confirm this is "
            "intentional; tightening an OWD later forces a full sharing recalculation."
        )

    # Searchability is off by default on new custom objects; say so once per object.
    if not has_child(root, "enableSearch"):
        issues.append(
            f"WARN: {file_stem}: no <enableSearch> element. Search is disabled by "
            "default on new custom objects, so records will not be found by global "
            "search or SOSL. Set it explicitly either way."
        )

    return issues, advisory


def check_field_file(field_path: Path) -> list[str]:
    """Return advisory (WARN-only) findings for a single custom field file.

    OCD-DESC-02 only. Unlike CustomObject, CustomField.description carries no
    documented character limit (see FIELD_DESC_UNVERIFIED_CANDIDATE_LEN
    above), so this never raises an ISSUE — only the headroom WARN, which
    does not affect the exit code.
    """
    advisory: list[str] = []

    file_stem = field_path.name.replace(".field-meta.xml", "")
    if not file_stem.endswith("__c"):
        return advisory

    try:
        root = ET.parse(field_path).getroot()
    except ET.ParseError:
        # A malformed field file is not this check's job to report.
        return advisory

    description = child_text(root, "description")
    if description and len(description) > DESC_WARN_LEN:
        advisory.append(
            f"INFO: {file_stem}: OCD-DESC-02 <description> is {len(description)} "
            "characters. The Metadata API Developer Guide states no length limit for "
            "CustomField.description (api_meta.txt L43360) — UNVERIFIED (2026-09-11) "
            f"whether the {FIELD_DESC_UNVERIFIED_CANDIDATE_LEN}-character ceiling used "
            "elsewhere in the guide (CustomPermission, PermissionSet, Profile) also "
            "applies here. Keep it terse regardless — move rationale to the build's "
            "deploy-order.md or the configuration workbook."
        )
    return advisory


def check_object_count(object_files: list[Path]) -> list[str]:
    """Warn if the custom object count in the manifest approaches common edition limits."""
    issues: list[str] = []
    custom_count = sum(
        1 for f in object_files if f.name.replace(".object-meta.xml", "").endswith("__c")
    )

    # Edition allocations are not stated in the Metadata API Developer Guide; these
    # thresholds are advisory only. Always confirm against
    # Setup -> Company Information -> Used Custom Objects, which counts managed-package
    # objects as well.
    if custom_count >= 180:
        issues.append(
            f"WARN: Found {custom_count} custom objects in this metadata source. "
            "Enterprise Edition is commonly allocated 200. Verify the org's Used Custom "
            "Objects count in Setup → Company Information before deploying more."
        )
    elif custom_count >= 45:
        issues.append(
            f"WARN: Found {custom_count} custom objects in this metadata source. "
            "Professional Edition is commonly allocated 50. If this is a Professional "
            "Edition org, verify the org's Used Custom Objects count before deploying more."
        )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ISSUE: Manifest directory not found: {manifest_dir}")
        return 1

    object_files = find_object_files(manifest_dir)
    field_files = find_field_files(manifest_dir)

    if not object_files and not field_files:
        print(
            "No .object-meta.xml or .field-meta.xml files found. "
            "Provide a directory containing Salesforce object metadata."
        )
        return 0

    all_issues: list[str] = []
    all_advisory: list[str] = []

    for obj_path in sorted(object_files):
        issues, advisory = check_object_file(obj_path)
        all_issues.extend(issues)
        all_advisory.extend(advisory)

    for field_path in sorted(field_files):
        all_advisory.extend(check_field_file(field_path))

    all_issues.extend(check_object_count(object_files))

    if not all_issues and not all_advisory:
        print(
            f"No issues found across {len(object_files)} object file(s) and "
            f"{len(field_files)} field file(s)."
        )
        return 0

    for issue in all_issues:
        print(issue)
    for note in all_advisory:
        print(note)

    print(f"Summary: {len(all_issues)} issue(s)/warning(s), {len(all_advisory)} info.")

    return 1 if all_issues else 0


if __name__ == "__main__":
    sys.exit(main())
