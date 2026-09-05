#!/usr/bin/env python3
"""Checker script for the Duplicate Management skill.

Inspects Salesforce metadata in SFDX source format (or retrieved XML) for the
matching-rule / duplicate-rule defects documented in references/gotchas.md.

Uses stdlib only - no pip dependencies.

Usage:
    python3 check_duplicate_rules.py [--manifest-dir path/to/metadata]

Exit codes:
    0 - no issues found
    1 - one or more issues found
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Metadata API Developer Guide, MatchingRule: the complete matchingMethod enum.
MATCHING_METHODS = {
    "Exact",
    "FirstName",
    "LastName",
    "CompanyName",
    "Phone",
    "City",
    "Street",
    "Zip",
    "Title",
}

# Metadata API Developer Guide, MatchingRule: "The only valid values you can
# declare when deploying a package are Active and Inactive."
DEPLOYABLE_RULE_STATUSES = {"Active", "Inactive"}

BLANK_VALUE_BEHAVIORS = {"MatchBlanks", "NullNotAllowed"}

# Metadata API Developer Guide, DuplicateRule: DupeActionType / DupeSecurityOptionType.
DUPE_ACTIONS = {"Allow", "Block"}
SECURITY_OPTIONS = {"EnforceSharingRules", "BypassSharingRules"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check matching-rule and duplicate-rule metadata for activation gaps, "
            "illegal alertText pairings, silent no-op actions, and empty match criteria."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce project or retrieved metadata (default: current directory).",
    )
    return parser.parse_args()


def _tag(local: str) -> str:
    return f"{{{SF_NS}}}{local}"


def _find(parent: ET.Element, name: str) -> ET.Element | None:
    """Find a direct child by name in namespaced or bare XML.

    ``a.find(x) or a.find(y)`` must not be used here: an Element with no
    children is falsy, so a found leaf would be silently discarded and every
    namespaced rule would look unnamed and inactive (fail-open).
    """
    el = parent.find(_tag(name))
    return el if el is not None else parent.find(name)


def _findall(parent: ET.Element, name: str) -> list[ET.Element]:
    found = parent.findall(_tag(name))
    return found if found else parent.findall(name)


def _text(parent: ET.Element, name: str) -> str:
    el = _find(parent, name)
    if el is None or el.text is None:
        return ""
    return el.text.strip()


def _texts(parent: ET.Element, name: str) -> list[str]:
    return [el.text.strip() for el in _findall(parent, name) if el.text and el.text.strip()]


def find_files(root: Path, suffix: str) -> list[Path]:
    """Return metadata files with the given suffix, in DX or retrieved layout."""
    results = [p for p in root.rglob(f"*{suffix}-meta.xml") if p.is_file()]
    results.extend(p for p in root.rglob(f"*{suffix}") if p.is_file())
    return sorted(set(results))


def object_from_matching_rule_file(path: Path) -> str:
    """matchingRules/Contact.matchingRule-meta.xml -> Contact."""
    return path.name.split(".", 1)[0]


def object_from_duplicate_rule_file(path: Path) -> str:
    """duplicateRules/Contact.My_Rule.duplicateRule-meta.xml -> Contact."""
    return path.name.split(".", 1)[0]


def component_name(path: Path) -> str:
    """Strip the -meta.xml and type suffixes: Contact.My_Rule."""
    name = path.name
    for suffix in ("-meta.xml", ".duplicateRule", ".matchingRule"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name


# --------------------------------------------------------------------------- #
# Matching rules
# --------------------------------------------------------------------------- #


def collect_matching_rules(paths: list[Path]) -> tuple[dict[tuple[str, str], str], list[str]]:
    """Return {(object, fullName): ruleStatus} plus any issues found while parsing."""
    index: dict[tuple[str, str], str] = {}
    issues: list[str] = []

    for path in paths:
        obj = object_from_matching_rule_file(path)
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            issues.append(f"{path.name}: XML parse error - {exc}")
            continue

        # The object's rules live as <matchingRules> children of a <MatchingRules> root.
        rules = _findall(root, "matchingRules")
        if not rules:
            # Some retrieves emit a single bare rule as the root element.
            rules = [root]

        for rule in rules:
            name = _text(rule, "fullName") or _text(rule, "label") or "(unnamed)"
            status = _text(rule, "ruleStatus")
            index[(obj, name)] = status

            if status and status not in DEPLOYABLE_RULE_STATUSES:
                issues.append(
                    f"{path.name} / matching rule '{name}': ruleStatus is '{status}'. "
                    "Only Active and Inactive can be declared when deploying a package; "
                    "Activating, ActivationFailed, Deactivating and DeactivationFailed are "
                    "states you observe, not states you set."
                )
            if not status:
                issues.append(
                    f"{path.name} / matching rule '{name}': ruleStatus is missing. "
                    "It is a required field; without it the rule's activation state is undefined."
                )

            items = _findall(rule, "matchingRuleItems")
            if not items:
                issues.append(
                    f"{path.name} / matching rule '{name}': no matchingRuleItems. "
                    "A matching rule with no criteria compares nothing, so every duplicate "
                    "rule that references it detects nothing."
                )
                continue

            for position, item in enumerate(items, start=1):
                field = _text(item, "fieldName")
                method = _text(item, "matchingMethod")
                blank = _text(item, "blankValueBehavior")

                if not field:
                    issues.append(
                        f"{path.name} / matching rule '{name}' item {position}: "
                        "fieldName is missing (required)."
                    )
                if not method:
                    issues.append(
                        f"{path.name} / matching rule '{name}' item {position}: "
                        "matchingMethod is missing (required)."
                    )
                elif method not in MATCHING_METHODS:
                    issues.append(
                        f"{path.name} / matching rule '{name}' item {position}: "
                        f"matchingMethod '{method}' is not in the documented enum "
                        f"({', '.join(sorted(MATCHING_METHODS))}). Character-for-character "
                        "comparison on email or any other field uses Exact."
                    )
                if blank and blank not in BLANK_VALUE_BEHAVIORS:
                    issues.append(
                        f"{path.name} / matching rule '{name}' item {position}: "
                        f"blankValueBehavior '{blank}' is not MatchBlanks or NullNotAllowed."
                    )
                elif blank == "MatchBlanks":
                    issues.append(
                        f"{path.name} / matching rule '{name}' item {position} ('{field}'): "
                        "blankValueBehavior is MatchBlanks, so two records that are both blank "
                        "in this field count as a match. Confirm this is intended; "
                        "NullNotAllowed is the default."
                    )

            boolean_filter = _text(rule, "booleanFilter")
            if len(items) > 2 and not boolean_filter:
                issues.append(
                    f"{path.name} / matching rule '{name}': {len(items)} criteria and no "
                    "booleanFilter, so every item is ANDed and the rule only matches when "
                    "all of them agree. Supply booleanFilter (items are numbered in "
                    "document order) or confirm the AND is intended."
                )

    return index, issues


# --------------------------------------------------------------------------- #
# Duplicate rules
# --------------------------------------------------------------------------- #


def check_duplicate_rule(
    path: Path, matching_index: dict[tuple[str, str], str], saw_matching_files: bool
) -> tuple[list[str], str, bool]:
    """Return (issues, object name, is_active) for one duplicate rule file."""
    issues: list[str] = []
    obj = object_from_duplicate_rule_file(path)

    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"{path.name}: XML parse error - {exc}"], obj, False

    label = _text(root, "masterLabel") or path.stem
    is_active = _text(root, "isActive").lower() == "true"

    action_insert = _text(root, "actionOnInsert")
    action_update = _text(root, "actionOnUpdate")
    ops_insert = {v.lower() for v in _texts(root, "operationsOnInsert")}
    ops_update = {v.lower() for v in _texts(root, "operationsOnUpdate")}
    alert_text = _text(root, "alertText")
    security = _text(root, "securityOption")

    for name, value in (("actionOnInsert", action_insert), ("actionOnUpdate", action_update)):
        if not value:
            issues.append(f"{path.name} / '{label}': {name} is missing (required).")
        elif value not in DUPE_ACTIONS:
            issues.append(
                f"{path.name} / '{label}': {name} is '{value}'; the DupeActionType enum "
                "is Allow or Block."
            )

    # Gotcha: alertText is legal only when at least one action is Allow.
    if alert_text and action_insert == "Block" and action_update == "Block":
        issues.append(
            f"{path.name} / '{label}': alertText is set while both actionOnInsert and "
            "actionOnUpdate are Block. The Metadata API rejects this - alertText may only "
            "be set when at least one action is Allow. Remove alertText, or allow one "
            "operation with an alert."
        )

    # Gotcha: Allow + alert with no message shows an empty dialog.
    for op_name, action, ops in (
        ("insert", action_insert, ops_insert),
        ("update", action_update, ops_update),
    ):
        if action != "Allow":
            continue
        if "alert" in ops and not alert_text:
            issues.append(
                f"{path.name} / '{label}': actionOn{op_name.capitalize()} is Allow with "
                f"'alert' in operationsOn{op_name.capitalize()}, but alertText is empty. "
                "Users get a dialog with no explanation of what matched."
            )
        if not ops:
            issues.append(
                f"{path.name} / '{label}': actionOn{op_name.capitalize()} is Allow but "
                f"operationsOn{op_name.capitalize()} is empty, so the {op_name} proceeds "
                "with no alert and no report. The rule is inventory, not a control."
            )
        elif "alert" not in ops and "report" in ops:
            issues.append(
                f"{path.name} / '{label}': {op_name} is report-only. Nobody is warned; "
                "DuplicateRecordSet rows accumulate and need a named steward "
                "(templates/duplicate-governance-template.md)."
            )

    if not security:
        issues.append(f"{path.name} / '{label}': securityOption is missing (required).")
    elif security not in SECURITY_OPTIONS:
        issues.append(
            f"{path.name} / '{label}': securityOption is '{security}'; valid values are "
            "EnforceSharingRules and BypassSharingRules."
        )
    elif security == "EnforceSharingRules" and (action_insert == "Block" or action_update == "Block"):
        issues.append(
            f"{path.name} / '{label}': a Block rule with securityOption EnforceSharingRules "
            "silently allows the save when the running user cannot see the duplicate, and no "
            "message is issued. Confirm this is intended rather than BypassSharingRules."
        )

    match_rules = _findall(root, "duplicateRuleMatchRules")
    if not match_rules:
        issues.append(
            f"{path.name} / '{label}': no duplicateRuleMatchRules. A duplicate rule with no "
            "matching rule detects nothing."
        )

    for match_rule in match_rules:
        target_obj = _text(match_rule, "matchRuleSObjectType")
        rule_name = _text(match_rule, "matchingRule")

        if not rule_name:
            issues.append(
                f"{path.name} / '{label}': a duplicateRuleMatchRules entry has no "
                "matchingRule developer name."
            )
            continue
        if not target_obj:
            issues.append(
                f"{path.name} / '{label}' -> '{rule_name}': matchRuleSObjectType is missing "
                "(required); it names the object being searched."
            )
            continue

        mapping = _find(match_rule, "objectMapping")
        if mapping is not None:
            output_obj = _text(mapping, "outputObject")
            input_obj = _text(mapping, "inputObject")
            if output_obj and output_obj != target_obj:
                issues.append(
                    f"{path.name} / '{label}' -> '{rule_name}': objectMapping outputObject "
                    f"'{output_obj}' does not equal matchRuleSObjectType '{target_obj}'. "
                    "The guide requires them to be the same value."
                )
            if input_obj and input_obj != obj:
                issues.append(
                    f"{path.name} / '{label}' -> '{rule_name}': objectMapping inputObject "
                    f"'{input_obj}' does not match the object in the file name ('{obj}'). "
                    "The input object is the one the duplicate rule is defined for."
                )
            if not _findall(mapping, "mappingFields"):
                issues.append(
                    f"{path.name} / '{label}' -> '{rule_name}': objectMapping has no "
                    "mappingFields, so no field of the saving record reaches the target object."
                )

        # Cross-file check: an active duplicate rule pointing at a matching rule
        # that is not Active detects nothing.
        key = (target_obj, rule_name)
        if key in matching_index:
            status = matching_index[key]
            if is_active and status != "Active":
                issues.append(
                    f"{path.name} / '{label}': isActive is true but it references matching "
                    f"rule '{rule_name}' on {target_obj}, whose ruleStatus is "
                    f"'{status or '(missing)'}'. The duplicate rule will detect nothing "
                    "until that matching rule is Active."
                )
        elif saw_matching_files and not rule_name.startswith("Standard_"):
            issues.append(
                f"{path.name} / '{label}': references matching rule '{rule_name}' on "
                f"{target_obj}, which is not in this metadata set. Confirm it exists and is "
                f"Active in the target org (matchingRules/{target_obj}.matchingRule-meta.xml)."
            )

    return issues, obj, is_active


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #


def check(manifest_dir: Path) -> tuple[list[str], list[str]]:
    """Return (issues, informational notes)."""
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"], []

    matching_files = find_files(manifest_dir, ".matchingRule")
    duplicate_files = find_files(manifest_dir, ".duplicateRule")

    if not matching_files and not duplicate_files:
        return [], [
            f"No matching-rule or duplicate-rule metadata found under {manifest_dir}."
        ]

    matching_index, issues = collect_matching_rules(matching_files)

    active_by_object: dict[str, list[str]] = defaultdict(list)
    for path in duplicate_files:
        file_issues, obj, is_active = check_duplicate_rule(
            path, matching_index, bool(matching_files)
        )
        issues.extend(file_issues)
        if is_active:
            active_by_object[obj].append(component_name(path))

    notes = [
        f"Scanned {len(matching_files)} matching-rule file(s) covering "
        f"{len(matching_index)} rule(s) and {len(duplicate_files)} duplicate-rule file(s)."
    ]
    for obj in sorted(active_by_object):
        names = active_by_object[obj]
        # No per-object rule limit is stated in the Metadata API guide or the Object
        # Reference, so this is a count, not a threshold. sortOrder decides precedence.
        notes.append(
            f"{obj}: {len(names)} active duplicate rule(s) - {', '.join(sorted(names))}. "
            "Review their sortOrder values; sortOrder determines the order rules are applied."
        )

    return issues, notes


def main() -> int:
    args = parse_args()
    issues, notes = check(Path(args.manifest_dir))

    for note in notes:
        print(f"INFO: {note}")

    if not issues:
        print("No duplicate-management issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")
    print(f"\n{len(issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
