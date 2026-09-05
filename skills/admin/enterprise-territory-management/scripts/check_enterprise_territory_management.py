#!/usr/bin/env python3
"""Static checks for Salesforce Sales Territories (Enterprise Territory Management) source.

Reads the Territory2* metadata files in a Salesforce DX or Metadata API source tree and reports
structural problems that the platform will either reject at deploy time or accept silently and then
fail to act on. Standard library only.

Usage:
    python3 check_enterprise_territory_management.py --manifest-dir force-app/main/default
    python3 check_enterprise_territory_management.py --manifest-dir force-app/main/default --json

Expected layout (Metadata API Developer Guide, Territory2* "File Suffix and Directory Location"):

    territory2Models/<Model>/<Model>.territory2Model-meta.xml
    territory2Models/<Model>/territories/<Territory>.territory2-meta.xml
    territory2Models/<Model>/rules/<Rule>.territory2Rule-meta.xml
    territory2Types/<Type>.territory2Type-meta.xml
    settings/Territory2.settings-meta.xml

Checks (severity in brackets):

    1  [ERROR] Rule is active but declares no ruleItems.
    2  [ERROR] Rule declares more than 10 ruleItems (documented cap).
    3  [ERROR] Two territories in the same model share a <name>.
    4  [ERROR] An access-level element carries a value outside its documented enumeration.
    5  [WARN]  parentTerritory names a territory that is not a file in the same model's folder.
    6  [WARN]  Two territory types share a priority value (priority must be unique).
    7  [WARN]  Rule objectType is something other than Account.
    8  [WARN]  Rule item operation is not in the documented FilterOperation enumeration.
    9  [WARN]  booleanFilter references an index with no matching rule item.
    10 [WARN]  Territory references a territory2Type that is not present in source.
    11 [WARN]  Rule is not referenced by any territory's ruleAssociations in its model.
    12 [WARN]  Territory type is missing its required priority element.
    13 [INFO]  A model folder contains no territories.
    14 [INFO]  No Sales Territories metadata was found under --manifest-dir at all.

Exit status: 1 if any ERROR or WARN finding is reported, otherwise 0.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

# --------------------------------------------------------------------------------------
# Documented value sets (Metadata API Developer Guide, Territory2 / Territory2Rule sections)
# --------------------------------------------------------------------------------------

MAX_RULE_ITEMS = 10  # "A territory rule can have up to 10 rule items."

FILTER_OPERATIONS = {
    "equals", "notEqual", "lessThan", "greaterThan", "lessOrEqual", "greaterOrEqual",
    "contains", "notContain", "startsWith", "includes", "excludes", "within",
}

# Territory2.objectType: "For API version 32.0, the only available object is Account."
SUPPORTED_RULE_OBJECT_TYPES = {"Account"}

ACCESS_LEVEL_ENUMS = {
    "accountAccessLevel": {"Read", "Edit", "All"},
    "opportunityAccessLevel": {"None", "Read", "Edit"},
    "caseAccessLevel": {"None", "Read", "Edit"},
    "contactAccessLevel": {"None", "Read", "Edit"},
}

ERROR = "ERROR"
WARN = "WARN"
INFO = "INFO"


# --------------------------------------------------------------------------------------
# XML helpers
# --------------------------------------------------------------------------------------

def strip_ns(tag: str) -> str:
    """Return a tag name without its {namespace} prefix."""
    return tag.split("}", 1)[1] if "}" in tag else tag


def find_child(parent, tag):
    """Return the first direct child with the given local tag, or None.

    Written as an explicit ``is not None`` walk on purpose: an ElementTree Element with no
    children is falsy, so ``parent.find(a) or parent.find(b)`` silently discards a real leaf
    element. Never use ``or`` to chain element lookups.
    """
    if parent is None:
        return None
    for child in parent:
        if strip_ns(child.tag) == tag:
            return child
    return None


def child_text(parent, tag):
    """Return the stripped text of the first direct child with the given tag, or None."""
    child = find_child(parent, tag)
    if child is None:
        return None
    return (child.text or "").strip()


def children(parent, tag):
    """Return every direct child with the given local tag."""
    if parent is None:
        return []
    return [c for c in parent if strip_ns(c.tag) == tag]


def parse_xml(path: Path):
    """Parse an XML file. Returns (root, error_message); exactly one is None."""
    try:
        return ET.parse(path).getroot(), None
    except ET.ParseError as exc:
        return None, f"{path.name} is not well-formed XML: {exc}"
    except OSError as exc:
        return None, f"{path.name} could not be read: {exc}"


# --------------------------------------------------------------------------------------
# Source discovery
# --------------------------------------------------------------------------------------

def collect(root: Path, suffix: str) -> list[Path]:
    """Find components of one type in either DX (-meta.xml) or Metadata API layout."""
    found = list(root.rglob(f"*.{suffix}-meta.xml")) + list(root.rglob(f"*.{suffix}"))
    unique = {p.resolve(): p for p in found if p.is_file()}
    return sorted(unique.values())


def developer_name(path: Path, suffix: str) -> str:
    """Recover a component's developer name from its file name."""
    name = path.name
    for tail in (f".{suffix}-meta.xml", f".{suffix}"):
        if name.endswith(tail):
            return name[: -len(tail)]
    return path.stem


def model_of(path: Path, nested: bool) -> str:
    """Return the owning model folder name.

    nested=True for territories/ and rules/ (model folder is two levels up);
    nested=False for the model file itself (model folder is its own parent).
    """
    return path.parent.parent.name if nested else path.parent.name


class Finding:
    def __init__(self, severity: str, path: Path, message: str):
        self.severity = severity
        self.path = str(path)
        self.message = message

    def as_dict(self) -> dict:
        return {"severity": self.severity, "file": self.path, "message": self.message}

    def __str__(self) -> str:
        return f"{self.severity}: {self.path}\n    {self.message}"


# --------------------------------------------------------------------------------------
# Loaders
# --------------------------------------------------------------------------------------

def load_territories(root: Path, findings: list[Finding]) -> dict:
    """Return {model: {devname: {...}}} for every Territory2 component found."""
    by_model: dict = defaultdict(dict)
    for path in collect(root, "territory2"):
        element, error = parse_xml(path)
        if element is None:
            findings.append(Finding(ERROR, path, error))
            continue
        rule_names = []
        for assoc in children(element, "ruleAssociations"):
            name = child_text(assoc, "ruleName")
            if name:
                rule_names.append(name)
        by_model[model_of(path, nested=True)][developer_name(path, "territory2")] = {
            "path": path,
            "label": child_text(element, "name"),
            "parent": child_text(element, "parentTerritory"),
            "type": child_text(element, "territory2Type"),
            "rules": rule_names,
            "element": element,
        }
    return by_model


def load_rules(root: Path, findings: list[Finding]) -> dict:
    """Return {model: {devname: {...}}} for every Territory2Rule component found."""
    by_model: dict = defaultdict(dict)
    for path in collect(root, "territory2Rule"):
        element, error = parse_xml(path)
        if element is None:
            findings.append(Finding(ERROR, path, error))
            continue
        items = children(element, "ruleItems")
        by_model[model_of(path, nested=True)][developer_name(path, "territory2Rule")] = {
            "path": path,
            "label": child_text(element, "name"),
            "active": (child_text(element, "active") or "").lower() == "true",
            "object_type": child_text(element, "objectType"),
            "boolean_filter": child_text(element, "booleanFilter"),
            "items": [
                {"field": child_text(i, "field"), "operation": child_text(i, "operation")}
                for i in items
            ],
        }
    return by_model


def load_types(root: Path, findings: list[Finding]) -> dict:
    """Return {devname: {...}} for every Territory2Type component found."""
    types: dict = {}
    for path in collect(root, "territory2Type"):
        element, error = parse_xml(path)
        if element is None:
            findings.append(Finding(ERROR, path, error))
            continue
        types[developer_name(path, "territory2Type")] = {
            "path": path,
            "label": child_text(element, "name"),
            "priority": child_text(element, "priority"),
        }
    return types


def load_models(root: Path, findings: list[Finding]) -> dict:
    """Return {devname: path} for every Territory2Model component found."""
    models: dict = {}
    for path in collect(root, "territory2Model"):
        element, error = parse_xml(path)
        if element is None:
            findings.append(Finding(ERROR, path, error))
            continue
        models[developer_name(path, "territory2Model")] = path
    return models


# --------------------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------------------

def check_rules(rules_by_model: dict, findings: list[Finding]) -> None:
    for model, rules in sorted(rules_by_model.items()):
        for name, rule in sorted(rules.items()):
            path = rule["path"]
            item_count = len(rule["items"])

            # 1 — an active rule with no criteria.
            if rule["active"] and item_count == 0:
                findings.append(Finding(
                    ERROR, path,
                    f"Rule '{name}' in model '{model}' has active=true but declares no <ruleItems>. "
                    "An active rule with no selection criteria has nothing to evaluate. Add at least "
                    "one ruleItems block, or set active=false until the criteria are written.",
                ))

            # 2 — documented cap.
            if item_count > MAX_RULE_ITEMS:
                findings.append(Finding(
                    ERROR, path,
                    f"Rule '{name}' declares {item_count} rule items. The Metadata API guide states "
                    f"a territory rule can have up to {MAX_RULE_ITEMS} rule items. Split the criteria "
                    "across additional rules and associate each to the territory.",
                ))

            # 7 — objectType.
            object_type = rule["object_type"]
            if object_type and object_type not in SUPPORTED_RULE_OBJECT_TYPES:
                supported = ", ".join(sorted(SUPPORTED_RULE_OBJECT_TYPES))
                findings.append(Finding(
                    WARN, path,
                    f"Rule '{name}' has objectType '{object_type}'. The Metadata API guide documents "
                    f"only {supported} for Territory2Rule, and the Object Reference entry for "
                    "ObjectTerritory2AssignmentRule.ObjectType says the same. Confirm against a "
                    "current org describe before deploying.",
                ))
            elif not object_type:
                findings.append(Finding(
                    ERROR, path,
                    f"Rule '{name}' has no <objectType>. It is a required field.",
                ))

            # 8 — operation enumeration.
            for index, item in enumerate(rule["items"], start=1):
                operation = item["operation"]
                if operation and operation not in FILTER_OPERATIONS:
                    findings.append(Finding(
                        WARN, path,
                        f"Rule '{name}' rule item {index} uses operation '{operation}', which is not "
                        "in the documented FilterOperation enumeration ("
                        + ", ".join(sorted(FILTER_OPERATIONS)) +
                        "). Note the guide's own sample shows 'greater_than', which is not a valid "
                        "value — use 'greaterThan'.",
                    ))

            # 9 — booleanFilter indexes.
            boolean_filter = rule["boolean_filter"]
            if boolean_filter:
                referenced = {int(n) for n in re.findall(r"\d+", boolean_filter)}
                out_of_range = sorted(n for n in referenced if n < 1 or n > item_count)
                if out_of_range:
                    findings.append(Finding(
                        WARN, path,
                        f"Rule '{name}' has booleanFilter '{boolean_filter}' referencing index(es) "
                        f"{out_of_range} but declares {item_count} rule item(s). Numbering must start "
                        "at 1 and be contiguous, and item order is derived from position in the XML.",
                    ))
                missing = sorted(set(range(1, item_count + 1)) - referenced)
                if item_count and missing and not out_of_range:
                    findings.append(Finding(
                        WARN, path,
                        f"Rule '{name}' booleanFilter '{boolean_filter}' never references rule "
                        f"item(s) {missing}. Those criteria will not affect the rule.",
                    ))


def check_territories(territories_by_model: dict, types: dict, findings: list[Finding]) -> None:
    for model, territories in sorted(territories_by_model.items()):
        labels: dict = defaultdict(list)

        for name, territory in sorted(territories.items()):
            path = territory["path"]

            # 3 — duplicate labels within a model.
            if territory["label"]:
                labels[territory["label"]].append(name)

            # 4 — access-level enumerations.
            for tag, allowed in ACCESS_LEVEL_ENUMS.items():
                value = child_text(territory["element"], tag)
                if value and value not in allowed:
                    findings.append(Finding(
                        ERROR, path,
                        f"Territory '{name}' has <{tag}>{value}</{tag}>. The documented Metadata API "
                        f"values are {', '.join(sorted(allowed))}. UI and SOAP spellings such as "
                        "'Read Only', 'Read/Write', 'Owner' and 'Private' are not valid in metadata. "
                        "Omit the element entirely to inherit the Territory2Settings default.",
                    ))

            # 5 — dangling parentTerritory.
            parent = territory["parent"]
            if parent and parent not in territories:
                findings.append(Finding(
                    WARN, path,
                    f"Territory '{name}' names parentTerritory '{parent}', which is not a territory "
                    f"file in model '{model}'. parentTerritory takes the parent's developer name — "
                    "not its label and not a fully qualified name. If the parent already exists in "
                    "the target org this is fine; if not, the deploy fails or retries out of order.",
                ))

            # 10 — territory2Type present in source.
            territory_type = territory["type"]
            if not territory_type:
                findings.append(Finding(
                    ERROR, path,
                    f"Territory '{name}' has no <territory2Type>. Every Territory2 must have a type.",
                ))
            elif types and territory_type not in types:
                findings.append(Finding(
                    WARN, path,
                    f"Territory '{name}' references territory2Type '{territory_type}', which is not "
                    "among the Territory2Type files in this source tree. It must already exist in "
                    f"the target org. Types present here: {', '.join(sorted(types)) or 'none'}.",
                ))

        for label, owners in sorted(labels.items()):
            if len(owners) > 1:
                findings.append(Finding(
                    ERROR, territories[owners[0]]["path"],
                    f"Model '{model}' has {len(owners)} territories sharing the label '{label}': "
                    f"{', '.join(sorted(owners))}. Duplicate territory names make the hierarchy "
                    "ambiguous to read and to audit; give each territory a distinct <name>.",
                ))


def check_types(types: dict, findings: list[Finding]) -> None:
    by_priority: dict = defaultdict(list)
    for name, entry in sorted(types.items()):
        priority = entry["priority"]
        # 12 — priority is required.
        if priority in (None, ""):
            findings.append(Finding(
                WARN, entry["path"],
                f"Territory type '{name}' has no <priority>. The field table marks priority as "
                "Required, even though the guide's own sample definition omits it. Without it the "
                "type cannot participate in filter-based opportunity territory assignment.",
            ))
            continue
        by_priority[priority].append(name)

    # 6 — duplicate priorities.
    for priority, names in sorted(by_priority.items()):
        if len(names) > 1:
            findings.append(Finding(
                WARN, types[names[0]]["path"],
                f"Territory types {', '.join(sorted(names))} all use priority {priority}. The guide "
                "states the priority value on each territory type must be unique. The highest "
                "priority wins opportunity territory assignment, and territories tied at the top "
                "leave the opportunity with no territory at all.",
            ))


def check_rule_associations(territories_by_model: dict, rules_by_model: dict,
                            findings: list[Finding]) -> None:
    # 11 — a rule nothing points at.
    for model, rules in sorted(rules_by_model.items()):
        associated = set()
        for territory in territories_by_model.get(model, {}).values():
            associated.update(territory["rules"])
        for name, rule in sorted(rules.items()):
            if name not in associated and (rule["label"] or "") not in associated:
                findings.append(Finding(
                    WARN, rule["path"],
                    f"Rule '{name}' in model '{model}' is not named by any <ruleAssociations> entry "
                    "on a territory in this source tree. A Territory2Rule belongs to the model, not "
                    "to a territory; without an association it deploys cleanly and assigns nothing.",
                ))


def check_models(models: dict, territories_by_model: dict, findings: list[Finding]) -> None:
    # 13 — empty model.
    for name, path in sorted(models.items()):
        if not territories_by_model.get(name):
            findings.append(Finding(
                INFO, path,
                f"Model '{name}' has no territory files in its territories/ folder. That is valid "
                "source — the model may already hold its territories in the target org — but this "
                "deployment adds no hierarchy.",
            ))


# --------------------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------------------

def run_all_checks(manifest_dir: Path) -> list[Finding]:
    findings: list[Finding] = []

    if not manifest_dir.exists():
        return [Finding(ERROR, manifest_dir, "Manifest directory not found.")]

    models = load_models(manifest_dir, findings)
    territories_by_model = load_territories(manifest_dir, findings)
    rules_by_model = load_rules(manifest_dir, findings)
    types = load_types(manifest_dir, findings)

    if not (models or territories_by_model or rules_by_model or types):
        findings.append(Finding(
            INFO, manifest_dir,
            "No Sales Territories metadata found (territory2Model, territory2, territory2Rule, "
            "territory2Type). If ETM is not part of this source tree, ignore this. Otherwise check "
            "the path — files are named <Name>.territory2-meta.xml in DX source format.",
        ))
        return findings

    check_rules(rules_by_model, findings)
    check_territories(territories_by_model, types, findings)
    check_types(types, findings)
    check_rule_associations(territories_by_model, rules_by_model, findings)
    check_models(models, territories_by_model, findings)
    return findings


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Sales Territories (Enterprise Territory Management) metadata for "
            "structural problems. Point --manifest-dir at force-app/main/default or the root of "
            "the retrieved metadata."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata source (default: current directory).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as JSON instead of text.",
    )
    return parser.parse_args(argv)


def main(argv=None) -> list[Finding]:
    args = parse_args(argv)
    manifest_dir = Path(args.manifest_dir).resolve()
    findings = run_all_checks(manifest_dir)

    order = {ERROR: 0, WARN: 1, INFO: 2}
    findings.sort(key=lambda f: (order.get(f.severity, 3), f.path, f.message))

    if args.json:
        print(json.dumps([f.as_dict() for f in findings], indent=2))
        return findings

    print(f"Sales Territories metadata check: {manifest_dir}\n")
    if not findings:
        print("No findings.")
        return findings

    for finding in findings:
        print(finding)
        print()

    counts = {level: sum(1 for f in findings if f.severity == level) for level in (ERROR, WARN, INFO)}
    print(f"{counts[ERROR]} error(s), {counts[WARN]} warning(s), {counts[INFO]} informational.")
    return findings


if __name__ == "__main__":
    results = main()
    blocking = [f for f in results if f.severity in (ERROR, WARN)]
    if blocking:
        sys.exit(1)
    sys.exit(0)
