#!/usr/bin/env python3
"""Static checker for RestrictionRule metadata (.rule files).

Validates the criteria-language and metadata-shape rules that the Salesforce
platform accepts at write time but that silently produce a rule matching the
wrong records, the wrong users, or nothing at all:

  * required Metadata API fields present
  * enforcementType is a documented enum value, and is not FieldRestrict,
    which the Metadata API reference marks "Don't use."
  * targetEntity is legal for the declared enforcementType
  * recordFilter / userCriteria contain exactly one EQUALS test and no
    AND / OR / negation / comparison / formula constructs, evaluated with
    quoted string literals masked out so that a legal value such as
    'Research and Development' is not mistaken for an AND operator
  * Id literals are 15 characters, not 18
  * Owner traversal uses the required `Owner:User.` object-type syntax
  * active rules per object stay under the edition ceiling, counted
    SEPARATELY per enforcementType — the restriction-rule and scoping-rule
    ceilings are documented independently and do not share a budget

Sources for every rule enforced here are listed in
references/well-architected.md ("Official Sources Used").

Stdlib only. Exits 0 when clean, 1 when findings exist or the input path is
unusable.

Usage:
    python3 check_restriction_rules.py --manifest-dir force-app/main/default
    python3 check_restriction_rules.py --manifest-dir . --edition unlimited
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

REQUIRED_FIELDS = (
    "description",
    "enforcementType",
    "masterLabel",
    "recordFilter",
    "targetEntity",
    "userCriteria",
    "version",
)

VALID_ENFORCEMENT_TYPES = ("FieldRestrict", "Restrict", "Scoping")

# The Metadata API reference documents three enum values but marks one of them
# "FieldRestrict-Don't use." It parses; it should never ship.
DISCOURAGED_ENFORCEMENT_TYPES = {
    "FieldRestrict": 'the Metadata API reference documents this value as "Don\'t use."',
}

# targetEntity values documented as valid per enforcementType. Custom (__c) and
# external (__x) objects are accepted for Restrict in addition to this list.
RESTRICT_STANDARD_ENTITIES = (
    "Contract",
    "Event",
    "Quote",
    "Task",
    "TimeSheet",
    "TimeSheetEntry",
)
SCOPING_STANDARD_ENTITIES = (
    "Account",
    "Case",
    "Contact",
    "Event",
    "Lead",
    "Opportunity",
    "Task",
)

# Active-rule ceiling per object, per edition, PER ENFORCEMENT TYPE. Salesforce
# documents the two ceilings in two separate guides and never combines them, so
# two active restriction rules and two active scoping rules on the same object
# are both legal at once. The Scoping Rules considerations page names only
# Developer, Performance and Unlimited editions; it states no Enterprise number,
# so none is asserted here.
RESTRICT_CEILING = {
    "enterprise": 2,
    "developer": 2,
    "performance": 5,
    "unlimited": 5,
}
SCOPING_CEILING = {
    "developer": 2,
    "performance": 5,
    "unlimited": 5,
}
EDITIONS = ("developer", "enterprise", "performance", "unlimited")
CEILINGS = {"Restrict": RESTRICT_CEILING, "Scoping": SCOPING_CEILING}

# Constructs the criteria language does not support.
BANNED_OPERATORS = (
    (re.compile(r"\bAND\b", re.IGNORECASE), "AND"),
    (re.compile(r"\bOR\b", re.IGNORECASE), "OR"),
    (re.compile(r"\bNOT\b", re.IGNORECASE), "NOT"),
    (re.compile(r"\bLIKE\b", re.IGNORECASE), "LIKE"),
    (re.compile(r"\bIN\s*\("), "IN ("),
    (re.compile(r"!="), "!="),
    (re.compile(r"<>"), "<>"),
    (re.compile(r"<"), "<"),
    (re.compile(r">"), ">"),
)

# 18-character Salesforce Id: 15 base characters plus the 3-character
# case-safe suffix, which is drawn from A-Z and 0-5.
ID_18_RE = re.compile(r"\b[a-zA-Z0-9]{15}[A-Z0-5]{3}\b")

# `Owner.Field` is rejected by the parser; `Owner:User.Field` is required.
BARE_OWNER_RE = re.compile(r"\bOwner\.[A-Za-z]")

# A quoted value is data, not syntax. Salesforce's own example criteria include
# `Name__c=\'Tom, Anita, "Torres, Jia"\'`, so a literal can legally contain
# commas, double quotes, and English words like "and". Operator scanning runs
# against a copy with literals masked out, or every department called
# "Research and Development" is reported as an illegal AND.
QUOTED_LITERAL_RE = re.compile(r"\'[^\']*\'|\"[^\"]*\"")


def mask_literals(value: str) -> str:
    """Replace each quoted string literal with an inert placeholder."""
    return QUOTED_LITERAL_RE.sub("'#'", value)


class Finding:
    """One problem, anchored to a file."""

    def __init__(self, path: Path, message: str) -> None:
        self.path = path
        self.message = message

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check RestrictionRule metadata for criteria-language and shape defects.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--edition",
        default="enterprise",
        choices=sorted(EDITIONS),
        help="Org edition, which sets the active-rule ceiling per object (default: enterprise).",
    )
    return parser.parse_args()


def strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def find_rule_files(root: Path) -> list[Path]:
    """Every RestrictionRule source file under root, in either metadata or
    source format."""
    found = {
        p
        for pattern in ("*.rule", "*.rule-meta.xml")
        for p in root.rglob(pattern)
        if p.is_file()
    }
    return sorted(found)


def read_fields(path: Path) -> tuple[dict, list[Finding]]:
    """Return the rule's direct child elements as a dict, plus parse findings."""
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return {}, [Finding(path, f"file is not parseable XML ({exc})")]

    if strip_ns(root.tag) != "RestrictionRule":
        return {}, []

    fields = {}
    for child in root:
        fields[strip_ns(child.tag)] = (child.text or "").strip()
    return fields, []


def check_required(path: Path, fields: dict) -> list[Finding]:
    missing = [name for name in REQUIRED_FIELDS if not fields.get(name)]
    if missing:
        return [
            Finding(
                path,
                "missing required Metadata API field(s): " + ", ".join(missing),
            )
        ]
    return []


def check_target_entity(path: Path, fields: dict) -> list[Finding]:
    enforcement = fields.get("enforcementType", "")
    entity = fields.get("targetEntity", "")
    findings: list[Finding] = []

    if enforcement and enforcement not in VALID_ENFORCEMENT_TYPES:
        findings.append(
            Finding(
                path,
                f"enforcementType '{enforcement}' is not a documented value "
                f"({', '.join(VALID_ENFORCEMENT_TYPES)})",
            )
        )
        return findings

    if enforcement in DISCOURAGED_ENFORCEMENT_TYPES:
        findings.append(
            Finding(
                path,
                f"enforcementType is '{enforcement}': "
                + DISCOURAGED_ENFORCEMENT_TYPES[enforcement]
                + " Use 'Restrict' to filter access, or 'Scoping' to set a default "
                "record set without changing access.",
            )
        )
        return findings

    if not entity:
        return findings

    is_custom = entity.endswith("__c") or entity.endswith("__x")

    if enforcement == "Restrict" and not is_custom:
        if entity not in RESTRICT_STANDARD_ENTITIES:
            findings.append(
                Finding(
                    path,
                    f"targetEntity '{entity}' is not valid for enforcementType Restrict. "
                    f"Standard objects supported: {', '.join(RESTRICT_STANDARD_ENTITIES)} "
                    "(plus custom and external objects). If this object needs narrowing, "
                    "change the OWD and the sharing layer instead.",
                )
            )
    elif enforcement == "Scoping":
        if entity.endswith("__x"):
            findings.append(
                Finding(
                    path,
                    f"targetEntity '{entity}' is an external object. Scoping rules are "
                    "documented for standard and custom objects only; external-object "
                    "support is documented for restriction rules, not scoping rules.",
                )
            )
        elif not is_custom and entity not in SCOPING_STANDARD_ENTITIES:
            findings.append(
                Finding(
                    path,
                    f"targetEntity '{entity}' is not valid for enforcementType Scoping. "
                    f"Standard objects supported: {', '.join(SCOPING_STANDARD_ENTITIES)} "
                    "(plus custom objects).",
                )
            )
    return findings


def check_criteria(path: Path, field_name: str, value: str) -> list[Finding]:
    findings: list[Finding] = []
    if not value:
        return findings

    # Syntax lives outside the quotes; everything inside them is a value.
    syntax = mask_literals(value)

    for pattern, label in BANNED_OPERATORS:
        if pattern.search(syntax):
            findings.append(
                Finding(
                    path,
                    f"{field_name} contains '{label}'. Only the EQUALS operator is "
                    "supported; AND, OR, negation, comparisons and formulas are not. "
                    "Precompute the composite into a single stored field and filter on that.",
                )
            )

    equals_count = syntax.count("=")
    if equals_count == 0:
        findings.append(
            Finding(path, f"{field_name} contains no '=' — it must be a single EQUALS test.")
        )
    elif equals_count > 1:
        findings.append(
            Finding(
                path,
                f"{field_name} contains {equals_count} '=' characters. A rule expresses "
                "exactly one EQUALS test per side.",
            )
        )

    for match in ID_18_RE.finditer(value):
        findings.append(
            Finding(
                path,
                f"{field_name} contains what looks like an 18-character Id "
                f"('{match.group(0)}'). Record criteria requires 15-character Ids — "
                "truncate it, and record the value in the cross-org Id remap table.",
            )
        )

    if BARE_OWNER_RE.search(syntax):
        findings.append(
            Finding(
                path,
                f"{field_name} traverses 'Owner.' without an object type. Owner is "
                "polymorphic and requires the colon form, e.g. 'Owner:User.ProfileId'. "
                "Use 'OwnerId' when comparing the raw Id.",
            )
        )

    if "$User." not in syntax and field_name == "userCriteria":
        findings.append(
            Finding(
                path,
                "userCriteria does not reference a $User field. The audience side of a "
                "rule is expressed as an EQUALS test on $User (ProfileId, UserRoleId, "
                "IsActive, UserType, Department).",
            )
        )

    return findings


def check_active_counts(per_entity: dict, edition: str) -> list[Finding]:
    """Compare active rules against the ceiling for their own enforcementType.

    `per_entity` is keyed by (targetEntity, enforcementType). Restriction rules
    and scoping rules are counted separately because Salesforce documents the
    two ceilings separately and never states a combined budget.
    """
    findings: list[Finding] = []
    for (entity, enforcement), paths in sorted(per_entity.items()):
        table = CEILINGS.get(enforcement)
        if table is None:
            continue
        ceiling = table.get(edition)
        if ceiling is None:
            print(
                f"Note: {len(paths)} active {enforcement} rule(s) target '{entity}'. "
                f"Salesforce documents no {edition}-edition ceiling for {enforcement} "
                "rules, so no limit is asserted here — confirm against the guide."
            )
            continue
        if len(paths) > ceiling:
            names = ", ".join(p.name for p in paths)
            noun = "restriction" if enforcement == "Restrict" else "scoping"
            findings.append(
                Finding(
                    paths[0],
                    f"{len(paths)} active {noun} rules target '{entity}', above the "
                    f"{edition} ceiling of {ceiling} per object. Files: {names}. "
                    "Consolidate by precomputing a composite field, or move the "
                    "requirement into the sharing model. (Restriction and scoping "
                    "ceilings are counted separately, but only one rule of either "
                    "kind may apply to a given user on a given object.)",
                )
            )
    return findings


def check_manifest(manifest_dir: Path, edition: str) -> list[Finding]:
    if not manifest_dir.exists():
        return [Finding(manifest_dir, "path does not exist")]
    if not manifest_dir.is_dir():
        return [Finding(manifest_dir, "path is not a directory")]

    findings: list[Finding] = []
    active_by_entity = defaultdict(list)

    rule_files = find_rule_files(manifest_dir)
    if not rule_files:
        print(f"No RestrictionRule files found under {manifest_dir} — nothing to check.")
        return findings

    for path in rule_files:
        fields, parse_findings = read_fields(path)
        findings.extend(parse_findings)
        if not fields:
            continue

        findings.extend(check_required(path, fields))
        findings.extend(check_target_entity(path, fields))
        findings.extend(check_criteria(path, "recordFilter", fields.get("recordFilter", "")))
        findings.extend(check_criteria(path, "userCriteria", fields.get("userCriteria", "")))

        if fields.get("active", "false").lower() == "true":
            entity = fields.get("targetEntity") or "(unknown)"
            enforcement = fields.get("enforcementType") or "(unknown)"
            active_by_entity[(entity, enforcement)].append(path)

    findings.extend(check_active_counts(active_by_entity, edition))

    print(
        f"Checked {len(rule_files)} RestrictionRule file(s) under {manifest_dir} "
        f"(edition: {edition})."
    )
    return findings


def main() -> int:
    args = parse_args()
    findings = check_manifest(Path(args.manifest_dir), args.edition)

    if not findings:
        print("No issues found.")
        return 0

    for finding in findings:
        print(f"ISSUE: {finding}", file=sys.stderr)
    print(f"\n{len(findings)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
