#!/usr/bin/env python3
"""check_sharing_rules.py — SharingRules metadata checker.

Parses every ``<Object>.sharingRules-meta.xml`` under a Salesforce project and
reports rules that will not deploy, cannot be corrected later, or grant more
than the author probably meant.

What it actually checks (each one is a real, sourced constraint):

  ERROR  booleanFilter references a criteriaItems position that does not exist.
         The integers are 1-based indexes into the sibling criteriaItems, so
         "1 AND 3" over two criteria is a deploy failure.
  ERROR  A required field is missing. SharingBaseRule marks accessLevel,
         label and sharedTo required; SharingCriteriaRule additionally marks
         includeRecordsOwnedByAll required and SharingGuestRule marks
         includeHVUOwnedRecords required.
  ERROR  A guest rule with accessLevel other than Read. Metadata API:
         "For SharingGuestRule, the accessLevel field can be set only to Read."
  ERROR  An owner-based rule with no sharedFrom (required on SharingOwnerRule).
  ERROR  sharedTo present but empty — no recipient element inside it.
  WARN   Account rule with no accountSettings block, or one whose child access
         levels all equal the parent accessLevel. All three of
         caseAccessLevel / contactAccessLevel / opportunityAccessLevel are
         required and each takes None, Read or Edit; accepting the picker
         default is how account rules leak pipeline.
  WARN   sharedTo -> allInternalUsers ("a group containing all internal and
         nonportal users"), which is effectively org-wide.
  WARN   sharedTo -> queue on an object other than Lead, Case or a custom
         object. Metadata API SharedTo: queue "applies only to lead, case,
         and CustomObject".
  WARN   A criteriaItems entry present with no booleanFilter on a rule that
         has more than one criterion (the implicit AND is easy to get wrong).
  REVIEW Pre-Secure-Roles <roleAndSubordinates> / <rolesAndSubordinates>
         elements, reported for confirmation against the target org rather
         than as defects.
  WARN   Rule count per object against the documented platform caps. The
         Salesforce Security Guide: "You can define up to 300 total sharing
         rules for each object, including up to 50 criteria-based or guest
         user sharing rules, if available for the object." The 50 is a
         sub-limit INSIDE the 300, and criteria-based and guest rules share
         it. Override with --max-total-rules / --max-criteria-rules.

Sources:
  Metadata API Developer Guide — SharingRules
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_sharingrules.htm
  Metadata API Developer Guide — SharingBaseRule
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_sharingbaserule.htm
  Metadata API Developer Guide — SharedTo
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_sharedto.htm
  Salesforce Security Guide (v262) — Sharing Rules, Sharing Rule Considerations
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf

Stdlib only. Exit 0 when clean, 1 when any ERROR is found.

Usage:
    python3 check_sharing_rules.py --manifest-dir force-app
    python3 check_sharing_rules.py --manifest-dir . --max-criteria-rules 40
    python3 check_sharing_rules.py --strict          # warnings also exit 1
    python3 check_sharing_rules.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Directories a sharingRules file can live in, MDAPI and SFDX layouts.
SHARING_RULE_DIRS = [
    "sharingRules",
    "force-app/main/default/sharingRules",
    "src/sharingRules",
]

# The four rule collections on the SharingRules container.
RULE_COLLECTIONS = {
    "sharingOwnerRules": "owner-based",
    "sharingCriteriaRules": "criteria-based",
    "sharingTerritoryRules": "territory-based",
    "sharingGuestRules": "guest",
}

# Objects for which SharedTo -> queue is documented as valid. Anything else is
# a custom object, which is also valid, so only these standard names pass.
QUEUE_SHAREABLE_STANDARD_OBJECTS = {"Lead", "Case"}

# Documented per-object caps. Salesforce Security Guide, Sharing Rules:
# "You can define up to 300 total sharing rules for each object, including up
# to 50 criteria-based or guest user sharing rules, if available for the
# object." The 50 is a sub-limit inside the 300 and is shared between
# criteria-based and guest rules.
MAX_TOTAL_RULES_PER_OBJECT = 300
MAX_CRITERIA_OR_GUEST_RULES_PER_OBJECT = 50

ACCOUNT_CHILD_ACCESS_ELEMENTS = (
    "caseAccessLevel",
    "contactAccessLevel",
    "opportunityAccessLevel",
)

# Superseded role-hierarchy recipients. Reported for review, never as errors:
# roleAndSubordinates is still correct in an org with digital experiences
# enabled whose site users sit on external account roles. See
# skills/admin/queues-and-public-groups/references/gotchas.md Gotcha 6.
LEGACY_ROLE_ELEMENTS = ("roleAndSubordinates", "rolesAndSubordinates")

# Every recipient element SharedTo can carry.
RECIPIENT_ELEMENTS = {
    "allCustomerPortalUsers",
    "allInternalUsers",
    "allPartnerUsers",
    "channelProgramGroup",
    "channelProgramGroups",
    "group",
    "guestUser",
    "managerSubordinates",
    "managers",
    "portalRole",
    # Both spellings appear across the Metadata API reference rendering.
    "portalRoleAndSubordinates",
    "portalRoleandSubordinates",
    "queue",
    "role",
    "roleAndSubordinates",
    "roleAndSubordinatesInternal",
    "rolesAndSubordinates",
    "territory",
    "territoryAndSubordinates",
}

_INDEX_RE = re.compile(r"\d+")


class Finding:
    """One reportable observation. ``level`` is ERROR, WARN or REVIEW."""

    __slots__ = ("level", "where", "message")

    def __init__(self, level: str, where: str, message: str) -> None:
        self.level = level
        self.where = where
        self.message = message

    def __str__(self) -> str:
        return f"{self.level}: [{self.where}] {self.message}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce SharingRules metadata for non-deployable, "
            "write-once-and-wrong, and over-broad rule definitions."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce project or metadata package (default: current directory).",
    )
    parser.add_argument(
        "--max-total-rules",
        type=int,
        default=MAX_TOTAL_RULES_PER_OBJECT,
        help=(
            f"Cap on total sharing rules for one object (default: "
            f"{MAX_TOTAL_RULES_PER_OBJECT}, the documented platform limit). Lower it "
            "to use this as a design review budget."
        ),
    )
    parser.add_argument(
        "--max-criteria-rules",
        type=int,
        default=MAX_CRITERIA_OR_GUEST_RULES_PER_OBJECT,
        help=(
            f"Cap on criteria-based AND guest rules combined for one object "
            f"(default: {MAX_CRITERIA_OR_GUEST_RULES_PER_OBJECT}, the documented "
            "platform limit — it is a sub-limit inside the total, not an extra "
            "allowance). Lower it to use this as a design review budget."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on warnings as well as errors.",
    )
    return parser.parse_args()


def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def child_text(element: ET.Element, name: str) -> str | None:
    """Namespace-agnostic direct-child lookup. Returns None when absent."""
    for child in element:
        if strip_ns(child.tag) == name:
            return (child.text or "").strip()
    return None


def child_element(element: ET.Element, name: str) -> ET.Element | None:
    for child in element:
        if strip_ns(child.tag) == name:
            return child
    return None


def children_named(element: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in element if strip_ns(c.tag) == name]


def find_sharing_rule_files(base: Path) -> list[Path]:
    found: list[Path] = []
    for subdir in SHARING_RULE_DIRS:
        candidate = base / subdir
        if candidate.is_dir():
            found.extend(sorted(candidate.glob("*.sharingRules-meta.xml")))
            found.extend(sorted(candidate.glob("*.sharingRules")))
    if not found:
        # Fall back to a project-wide sweep for non-standard layouts.
        found = sorted(base.rglob("*.sharingRules-meta.xml"))
    # De-duplicate while preserving order.
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in found:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def object_name_from_path(path: Path) -> str:
    """Account.sharingRules-meta.xml -> Account"""
    return path.name.split(".", 1)[0]


def check_boolean_filter(rule: ET.Element, where: str) -> list[Finding]:
    """The integers in booleanFilter are 1-based indexes into criteriaItems."""
    findings: list[Finding] = []
    criteria = children_named(rule, "criteriaItems")
    raw_filter = child_text(rule, "booleanFilter")

    if raw_filter:
        indexes = [int(n) for n in _INDEX_RE.findall(raw_filter)]
        if not criteria:
            findings.append(
                Finding(
                    "ERROR",
                    where,
                    f"booleanFilter '{raw_filter}' is present but the rule has no "
                    "criteriaItems. The deployment will fail.",
                )
            )
            return findings
        bad = sorted({i for i in indexes if i < 1 or i > len(criteria)})
        if bad:
            findings.append(
                Finding(
                    "ERROR",
                    where,
                    f"booleanFilter '{raw_filter}' references criteria position(s) "
                    f"{bad} but only {len(criteria)} criteriaItems exist. "
                    "Indexes are 1-based positions in document order; this will "
                    "not deploy.",
                )
            )
        unreferenced = sorted(set(range(1, len(criteria) + 1)) - set(indexes))
        if unreferenced and not bad:
            findings.append(
                Finding(
                    "WARN",
                    where,
                    f"booleanFilter '{raw_filter}' never references criteria "
                    f"position(s) {unreferenced}. Those conditions have no effect "
                    "on the rule.",
                )
            )
    elif len(criteria) > 1:
        findings.append(
            Finding(
                "WARN",
                where,
                f"{len(criteria)} criteriaItems with no booleanFilter — the "
                "conditions are combined implicitly. State the logic explicitly "
                "so a reviewer can read the intent.",
            )
        )
    return findings


def check_shared_to(rule: ET.Element, where: str, object_name: str) -> list[Finding]:
    findings: list[Finding] = []
    shared_to = child_element(rule, "sharedTo")
    if shared_to is None:
        findings.append(
            Finding("ERROR", where, "sharedTo is missing. It is required on every sharing rule.")
        )
        return findings

    recipients = [strip_ns(c.tag) for c in shared_to]
    if not recipients:
        findings.append(
            Finding("ERROR", where, "sharedTo is present but empty — no recipient element inside it.")
        )
        return findings

    # Reported as REVIEW, never ERROR: the SharedTo recipient list grows with
    # each API version, so an unrecognised element is more often this script
    # being out of date than the metadata being wrong.
    unknown = [r for r in recipients if r not in RECIPIENT_ELEMENTS]
    if unknown:
        findings.append(
            Finding(
                "REVIEW",
                where,
                f"sharedTo contains recipient element(s) {unknown} that this script "
                "does not recognise. Confirm against the SharedTo metadata type "
                "reference for the project's API version.",
            )
        )

    if "allInternalUsers" in recipients:
        findings.append(
            Finding(
                "WARN",
                where,
                "sharedTo is allInternalUsers — 'a group containing all internal "
                "and nonportal users'. This is effectively org-wide access. "
                "Confirm it is intended and recorded.",
            )
        )

    if "queue" in recipients:
        is_custom = object_name.endswith("__c")
        if not is_custom and object_name not in QUEUE_SHAREABLE_STANDARD_OBJECTS:
            findings.append(
                Finding(
                    "WARN",
                    where,
                    f"sharedTo is a queue on '{object_name}'. The SharedTo reference "
                    "documents queue as applying only to lead, case, and CustomObject. "
                    "Share to a public group instead, and make the group a queue member.",
                )
            )

    for legacy in LEGACY_ROLE_ELEMENTS:
        if legacy in recipients:
            findings.append(
                Finding(
                    "REVIEW",
                    where,
                    f"sharedTo uses <{legacy}>. Confirm against Setup -> Release "
                    "Updates in the target org: under Secure Roles this becomes "
                    "roleAndSubordinatesInternal, except where digital experiences "
                    "is enabled with site users on external account roles.",
                )
            )
    return findings


def check_account_settings(rule: ET.Element, where: str, object_name: str) -> list[Finding]:
    if object_name != "Account":
        return []
    findings: list[Finding] = []
    settings = child_element(rule, "accountSettings")
    if settings is None:
        findings.append(
            Finding(
                "WARN",
                where,
                "Account rule with no accountSettings block. caseAccessLevel, "
                "contactAccessLevel and opportunityAccessLevel are each required "
                "and each take None, Read or Edit — the rule's effect on cases, "
                "contacts and pipeline is undeclared here.",
            )
        )
        return findings

    parent_access = child_text(rule, "accessLevel")
    child_values = {name: child_text(settings, name) for name in ACCOUNT_CHILD_ACCESS_ELEMENTS}
    missing = [name for name, value in child_values.items() if value is None]
    if missing:
        findings.append(
            Finding(
                "ERROR",
                where,
                f"accountSettings is missing required element(s) {missing}. "
                "All three child access levels are required on an Account rule.",
            )
        )
    present = [v for v in child_values.values() if v is not None]
    if present and parent_access and all(v == parent_access for v in present) and len(present) == 3:
        findings.append(
            Finding(
                "WARN",
                where,
                f"All three accountSettings values equal the rule accessLevel "
                f"('{parent_access}'). Cases, contacts and opportunities inherit the "
                "full grant. Default children to None and raise only what the "
                "requirement names.",
            )
        )
    return findings


def check_rule(
    rule: ET.Element,
    collection: str,
    object_name: str,
    file_label: str,
) -> list[Finding]:
    findings: list[Finding] = []
    full_name = child_text(rule, "fullName") or "<unnamed>"
    where = f"{file_label} :: {collection}/{full_name}"

    # SharingBaseRule required fields.
    access_level = child_text(rule, "accessLevel")
    if not access_level:
        findings.append(Finding("ERROR", where, "accessLevel is missing. It is required."))
    if not child_text(rule, "label"):
        findings.append(Finding("ERROR", where, "label is missing. It is required."))

    findings.extend(check_shared_to(rule, where, object_name))
    findings.extend(check_account_settings(rule, where, object_name))

    if collection in ("sharingOwnerRules", "sharingTerritoryRules"):
        if child_element(rule, "sharedFrom") is None:
            findings.append(
                Finding(
                    "ERROR",
                    where,
                    "sharedFrom is missing. It is required on an ownership-based "
                    "(and territory-based) sharing rule.",
                )
            )

    if collection == "sharingCriteriaRules":
        if child_text(rule, "includeRecordsOwnedByAll") is None:
            findings.append(
                Finding(
                    "ERROR",
                    where,
                    "includeRecordsOwnedByAll is missing. It is required on a "
                    "criteria-based rule, and it cannot be edited after the rule "
                    "is created — set it deliberately now.",
                )
            )
        findings.extend(check_boolean_filter(rule, where))

    if collection == "sharingGuestRules":
        if access_level and access_level != "Read":
            findings.append(
                Finding(
                    "ERROR",
                    where,
                    f"Guest rule accessLevel is '{access_level}'. The Metadata API "
                    "states that for SharingGuestRule the accessLevel field can be "
                    "set only to Read.",
                )
            )
        if child_text(rule, "includeHVUOwnedRecords") is None:
            findings.append(
                Finding(
                    "ERROR",
                    where,
                    "includeHVUOwnedRecords is missing. It is required on a guest "
                    "rule and cannot be edited after the rule is created.",
                )
            )
        findings.extend(check_boolean_filter(rule, where))

    return findings


def check_file(
    path: Path,
    base: Path,
    max_criteria_rules: int,
    max_total_rules: int,
) -> tuple[list[Finding], int]:
    """Return (findings, rules_seen) for one sharingRules file."""
    try:
        file_label = str(path.relative_to(base))
    except ValueError:
        file_label = str(path)

    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [Finding("ERROR", file_label, f"XML parse error: {exc}")], 0

    if strip_ns(root.tag) != "SharingRules":
        return (
            [
                Finding(
                    "ERROR",
                    file_label,
                    f"Root element is <{strip_ns(root.tag)}>, expected <SharingRules>.",
                )
            ],
            0,
        )

    object_name = object_name_from_path(path)
    findings: list[Finding] = []
    rules_seen = 0
    criteria_count = 0

    for collection in RULE_COLLECTIONS:
        for rule in children_named(root, collection):
            rules_seen += 1
            # The documented 50-rule sub-limit covers criteria-based AND guest
            # rules together, so both count here.
            if collection in ("sharingCriteriaRules", "sharingGuestRules"):
                criteria_count += 1
            findings.extend(check_rule(rule, collection, object_name, file_label))

    if criteria_count > max_criteria_rules:
        at_platform_cap = max_criteria_rules >= MAX_CRITERIA_OR_GUEST_RULES_PER_OBJECT
        findings.append(
            Finding(
                "WARN" if at_platform_cap else "REVIEW",
                file_label,
                f"{criteria_count} criteria-based + guest rules on {object_name}, "
                f"above the limit of {max_criteria_rules}. The Security Guide allows "
                f"up to {MAX_CRITERIA_OR_GUEST_RULES_PER_OBJECT} criteria-based or "
                "guest user rules per object, counted together and inside the total "
                f"of {MAX_TOTAL_RULES_PER_OBJECT}. Treat a climbing count as evidence "
                "the OWD or role hierarchy is the real problem.",
            )
        )

    if rules_seen > max_total_rules:
        at_platform_cap = max_total_rules >= MAX_TOTAL_RULES_PER_OBJECT
        findings.append(
            Finding(
                "WARN" if at_platform_cap else "REVIEW",
                file_label,
                f"{rules_seen} total sharing rules on {object_name}, above the limit "
                f"of {max_total_rules}. The Security Guide documents a cap of "
                f"{MAX_TOTAL_RULES_PER_OBJECT} total sharing rules per object.",
            )
        )

    return findings, rules_seen


def main() -> int:
    args = parse_args()
    base = Path(args.manifest_dir).resolve()

    if not base.exists():
        print(f"ERROR: Directory not found: {base}", file=sys.stderr)
        return 1

    print(f"Scanning: {base}\n")

    files = find_sharing_rule_files(base)
    if not files:
        print("No SharingRules metadata found.")
        print(f"  Searched: {[str(base / p) for p in SHARING_RULE_DIRS]}")
        print("  Run from the root of a Salesforce DX project or MDAPI package.")
        return 0

    all_findings: list[Finding] = []
    total_rules = 0

    print(f"SharingRules files found ({len(files)}):")
    for path in files:
        findings, rules_seen = check_file(
            path, base, args.max_criteria_rules, args.max_total_rules
        )
        total_rules += rules_seen
        try:
            label = str(path.relative_to(base))
        except ValueError:
            label = str(path)
        print(f"  {label} — {rules_seen} rule(s)")
        all_findings.extend(findings)
    print()

    errors = [f for f in all_findings if f.level == "ERROR"]
    warnings = [f for f in all_findings if f.level == "WARN"]
    reviews = [f for f in all_findings if f.level == "REVIEW"]

    for label, bucket in (("ERROR", errors), ("WARN", warnings), ("REVIEW", reviews)):
        if bucket:
            print(f"{label} ({len(bucket)}):")
            for finding in bucket:
                stream = sys.stderr if label == "ERROR" else sys.stdout
                print(f"  {finding}", file=stream)
            print()

    print(
        f"Checked {total_rules} rule(s) across {len(files)} file(s): "
        f"{len(errors)} error(s), {len(warnings)} warning(s), {len(reviews)} review item(s)."
    )

    if errors:
        return 1
    if warnings and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
