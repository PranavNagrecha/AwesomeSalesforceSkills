#!/usr/bin/env python3
"""Checker script for the Data Skew and Sharing Performance skill.

Lints the artifacts a skew remediation actually produces: retrieved/DX metadata, the
measured skew plan, and the Bulk API job plan that will run inside the change window.

Checks performed
----------------
1. Sharing-rule fan-out       - one group or role sourcing many rules on one object.
2. Private OWD with no rules  - access is role-hierarchy-only, which amplifies owner skew.
3. Skew plan thresholds       - owners, parents, and lookup targets past the documented
                                ceiling of 10,000 (Large Data Volumes guide: "Avoid having
                                any user own more than 10,000 records"; "Distribute child
                                records so that no parent has more than 10,000 child
                                records").
4. Empty bucket groups        - a Group deployed in this manifest and referenced by a
                                sharing rule. Group metadata never carries members
                                ("Members of the public group aren't migrated when you
                                deploy the group type"), so the rule grants nothing until
                                GroupMember rows are loaded separately.
5. Criteria-rule selectivity  - sharingCriteriaRules filtering on a field with no index.
                                Indexed set = platform-indexed standard fields, lookups,
                                custom fields flagged externalId/unique in this manifest,
                                plus anything declared in skew-check-config.json.
6. Bulk job plan              - parallel concurrency aimed at a target the skew plan
                                flagged, unsorted child loads, and Bulk API 2.0 jobs that
                                ask for Serial (2.0 exposes concurrencyMode as reserved and
                                supports parallel only).

Uses stdlib only - no pip dependencies.

Usage:
    python3 check_data_skew_and_sharing_performance.py \
        [--manifest-dir PATH] [--skew-plan FILE] [--job-plan FILE] [--strict]

Exit codes:
    0 -- no ERROR-class finding (and no WARN when --strict is passed). This
         includes the normal case where only INFO/WARN findings are printed -
         e.g. an unreferenced bucket group, or a Private-OWD object with no
         sharing rules file yet.
    1 -- at least one ERROR-class finding (unparseable metadata, a missing
         --skew-plan/--job-plan file that was named explicitly, or a Bulk
         API 2.0 job pinned to concurrencyMode=Serial), or at least one WARN
         finding when --strict is passed, or --manifest-dir does not exist.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Documented ceiling for owners and for children per parent.
SKEW_THRESHOLD = 10000

# Fields the platform indexes for most objects, per the Large Data Volumes guide.
PLATFORM_INDEXED_FIELDS = {
    "id",
    "name",
    "ownerid",
    "createddate",
    "createdbyid",
    "lastmodifieddate",
    "systemmodstamp",
    "recordtypeid",
    "division",
    "email",
}

# Field name suffixes that indicate a relationship (lookup / master-detail), which the
# platform indexes as a foreign key.
RELATIONSHIP_SUFFIXES = ("id", "__c")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata, a measured skew plan, and a Bulk API job plan "
            "for data skew and sharing performance risk."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce metadata / SFDX project (default: current directory).",
    )
    parser.add_argument(
        "--skew-plan",
        default=None,
        help=(
            "Measured skew plan: JSON or CSV. Defaults to skew-plan.json or skew-plan.csv "
            "inside --manifest-dir when present."
        ),
    )
    parser.add_argument(
        "--job-plan",
        default=None,
        help=(
            "Bulk API job plan (JSON). Defaults to bulk-job-plan.json inside "
            "--manifest-dir when present."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on WARN findings as well as ERROR (INFO never fails the run).",
    )
    return parser.parse_args()


def _tag(name: str) -> str:
    return f"{{{SF_NS}}}{name}"


def _child(parent, name):
    """Return the named child Element, or None.

    Never chain these with `or`: an Element with no children is falsy even when it
    exists, so `a.find(x) or a.find(y)` silently discards real leaf nodes.
    """
    if parent is None:
        return None
    found = parent.find(_tag(name))
    if found is None:
        return None
    return found


def _text(parent, name, default: str = "") -> str:
    el = _child(parent, name)
    if el is None:
        return default
    if el.text is None:
        return default
    return el.text.strip()


def _local(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def _first_existing(*candidates: Path):
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _sharing_dir(manifest_dir: Path):
    return _first_existing(
        manifest_dir / "sharingRules",
        manifest_dir / "force-app" / "main" / "default" / "sharingRules",
    )


def _groups_dir(manifest_dir: Path):
    return _first_existing(
        manifest_dir / "groups",
        manifest_dir / "force-app" / "main" / "default" / "groups",
    )


def _queues_dir(manifest_dir: Path):
    return _first_existing(
        manifest_dir / "queues",
        manifest_dir / "force-app" / "main" / "default" / "queues",
    )


def _objects_dir(manifest_dir: Path):
    return _first_existing(
        manifest_dir / "objects",
        manifest_dir / "force-app" / "main" / "default" / "objects",
    )


def _sharing_rule_files(manifest_dir: Path):
    sharing_dir = _sharing_dir(manifest_dir)
    if sharing_dir is None:
        return []
    files = sorted(sharing_dir.glob("*.sharingRules"))
    files += sorted(sharing_dir.glob("*.sharingRules-meta.xml"))
    return files


def _object_name_from_rule_file(path: Path) -> str:
    return path.name.split(".")[0]


def _queue_files(manifest_dir: Path):
    queues_dir = _queues_dir(manifest_dir)
    if queues_dir is None:
        return []
    files = sorted(queues_dir.glob("*.queue"))
    files += sorted(queues_dir.glob("*.queue-meta.xml"))
    return files


def _iter_rules(root):
    """Yield (rule_kind, rule_element) for every rule in a SharingRules document."""
    for kind in (
        "sharingCriteriaRules",
        "sharingOwnerRules",
        "sharingTerritoryRules",
        "sharingGuestRules",
    ):
        for rule in root.findall(_tag(kind)):
            yield kind, rule


def _shared_targets(rule, element_name: str):
    """Return [(target_kind, target_name)] under sharedTo / sharedFrom."""
    container = _child(rule, element_name)
    if container is None:
        return []
    targets = []
    for child in container:
        name = child.text.strip() if child.text else ""
        if name:
            targets.append((_local(child.tag), name))
    return targets


# --------------------------------------------------------------------------------------
# Check 1 - sharing rule fan-out
# --------------------------------------------------------------------------------------
def check_sharing_rules(manifest_dir: Path) -> list[str]:
    """Detect groups/roles that source many sharing rules (recalculation fan-out risk)."""
    issues: list[str] = []
    group_rule_count: dict[str, list[str]] = defaultdict(list)

    for xml_file in _sharing_rule_files(manifest_dir):
        try:
            root = ET.parse(xml_file).getroot()
        except ET.ParseError as exc:
            issues.append(f"ERROR: Could not parse sharing rules file {xml_file.name}: {exc}")
            continue
        obj_name = _object_name_from_rule_file(xml_file)
        for _kind, rule in _iter_rules(root):
            for target_kind, target_name in _shared_targets(rule, "sharedTo"):
                if target_kind in ("group", "role", "roleAndSubordinates",
                                   "roleAndSubordinatesInternal", "queue"):
                    group_rule_count[target_name].append(f"{obj_name} ({target_kind})")

    for group_name, rules in sorted(group_rule_count.items()):
        if len(rules) > 3:
            issues.append(
                f"WARN: Public group / role '{group_name}' is the target of {len(rules)} "
                f"sharing rules ({', '.join(rules[:3])}, ...). If this group contains users "
                f"who own many records, any membership change triggers recalculation across "
                f"all {len(rules)} rule sets. Consider splitting into narrower groups."
            )

    return issues


# --------------------------------------------------------------------------------------
# Check 2 - Private OWD with no sharing rules
# --------------------------------------------------------------------------------------
def _object_files(manifest_dir: Path):
    obj_dir = _objects_dir(manifest_dir)
    if obj_dir is None:
        return []
    files = sorted(obj_dir.glob("**/*.object-meta.xml"))
    files += sorted(obj_dir.glob("*.object"))
    return files


def check_object_owd(manifest_dir: Path) -> list[str]:
    """Private OWD with no sharing rules file means role-hierarchy-only access."""
    issues: list[str] = []
    sharing_dir = _sharing_dir(manifest_dir)

    for xml_file in _object_files(manifest_dir):
        try:
            root = ET.parse(xml_file).getroot()
        except ET.ParseError:
            continue
        sharing_model = _text(root, "sharingModel")
        if sharing_model != "Private":
            continue
        obj_name = xml_file.name.split(".")[0]
        rule_file = None
        if sharing_dir is not None:
            rule_file = _first_existing(
                sharing_dir / f"{obj_name}.sharingRules",
                sharing_dir / f"{obj_name}.sharingRules-meta.xml",
            )
        if rule_file is None:
            issues.append(
                f"INFO: Object '{obj_name}' has Private OWD but no sharing rules file in "
                f"this manifest. Access is role-hierarchy-only, so any role change for a "
                f"user who owns many of its records triggers a full sharing recalculation."
            )

    return issues


# --------------------------------------------------------------------------------------
# Check 3 - measured skew plan
# --------------------------------------------------------------------------------------
def _load_skew_plan(manifest_dir: Path, explicit: str | None):
    """Return (plan_dict, source_path) or (None, None)."""
    if explicit:
        path = Path(explicit)
        if not path.exists():
            return {"_error": f"Skew plan not found: {path}"}, path
    else:
        path = _first_existing(
            manifest_dir / "skew-plan.json",
            manifest_dir / "skew-plan.csv",
        )
        if path is None:
            return None, None

    if path.suffix.lower() == ".csv":
        return _load_skew_plan_csv(path), path
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle), path
    except (json.JSONDecodeError, OSError) as exc:
        return {"_error": f"Could not read skew plan {path}: {exc}"}, path


def _load_skew_plan_csv(path: Path):
    """CSV columns: kind,object,field,key,label,count,concurrent_writes.

    kind is one of ownership | parent | lookup.
    """
    plan = {"ownership": [], "parents": [], "lookups": []}
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                kind = (row.get("kind") or "").strip().lower()
                try:
                    count = int(float((row.get("count") or "0").replace(",", "")))
                except ValueError:
                    count = 0
                entry = {
                    "object": (row.get("object") or "").strip(),
                    "field": (row.get("field") or "").strip(),
                    "key": (row.get("key") or "").strip(),
                    "label": (row.get("label") or "").strip(),
                    "count": count,
                    "concurrentWrites": (row.get("concurrent_writes") or "").strip().lower()
                    in ("1", "true", "yes", "y"),
                }
                if kind == "ownership":
                    entry["owner"] = entry["label"] or entry["key"]
                    plan["ownership"].append(entry)
                elif kind in ("parent", "account", "parent-child"):
                    entry["childObject"] = entry["object"]
                    entry["parentField"] = entry["field"]
                    entry["parentId"] = entry["key"]
                    entry["parentName"] = entry["label"]
                    plan["parents"].append(entry)
                elif kind == "lookup":
                    entry["targetId"] = entry["key"]
                    plan["lookups"].append(entry)
    except OSError as exc:
        return {"_error": f"Could not read skew plan {path}: {exc}"}
    return plan


def _as_int(value) -> int:
    try:
        return int(float(str(value).replace(",", "")))
    except (TypeError, ValueError):
        return 0


def check_skew_plan(plan, source_path) -> tuple[list[str], set[str]]:
    """Flag measured owners, parents, and lookup targets past the documented ceiling.

    Returns (issues, skewed_object_names) so the job-plan check can reuse the finding.
    """
    issues: list[str] = []
    skewed_objects: set[str] = set()

    if plan is None:
        return issues, skewed_objects
    if "_error" in plan:
        return [f"ERROR: {plan['_error']}"], skewed_objects

    label = source_path.name if source_path is not None else "skew plan"

    for row in plan.get("ownership", []) or []:
        count = _as_int(row.get("count"))
        if count > SKEW_THRESHOLD:
            obj = row.get("object") or "<unknown object>"
            owner = row.get("owner") or row.get("ownerId") or "<unknown owner>"
            skewed_objects.add(obj)
            issues.append(
                f"WARN [{label}]: Ownership skew - '{owner}' owns {count:,} {obj} records "
                f"(ceiling {SKEW_THRESHOLD:,}). Any role change or sharing-rule source group "
                f"change for this owner recalculates all {count:,}. Distribute across bucket "
                f"queues/groups, or take the owner out of the role hierarchy."
            )

    for row in plan.get("parents", []) or []:
        count = _as_int(row.get("count"))
        if count > SKEW_THRESHOLD:
            child = row.get("childObject") or row.get("object") or "<unknown child>"
            parent = row.get("parentName") or row.get("parentId") or "<unknown parent>"
            field = row.get("parentField") or "parent field"
            skewed_objects.add(child)
            issues.append(
                f"WARN [{label}]: Parent-child skew - parent '{parent}' has {count:,} "
                f"{child} children via {field} (ceiling {SKEW_THRESHOLD:,}). Every access "
                f"change on any one child scans the siblings to maintain the ImplicitParent "
                f"share. Split across segmented parents, or set the child OWD to "
                f"ControlledByParent if it needs no independent sharing."
            )

    for row in plan.get("lookups", []) or []:
        count = _as_int(row.get("count"))
        if count <= SKEW_THRESHOLD:
            continue
        obj = row.get("object") or "<unknown object>"
        field = row.get("field") or "<unknown lookup>"
        target = row.get("targetId") or row.get("label") or "<unknown target>"
        concurrent = bool(row.get("concurrentWrites"))
        skewed_objects.add(obj)
        if concurrent:
            issues.append(
                f"WARN [{label}]: Lookup skew - {count:,} {obj} records point at target "
                f"'{target}' via {field}, and the plan reports concurrent writes. The target "
                f"row is locked per DML, so concurrent jobs serialise on it and fail with "
                f"UNABLE_TO_LOCK_ROW. Distribute the lookup, or leave it blank where it does "
                f"not apply rather than pointing rows at a catchall."
            )
        else:
            issues.append(
                f"INFO [{label}]: Lookup concentration - {count:,} {obj} records point at "
                f"target '{target}' via {field}, but the plan reports no concurrent writes. "
                f"Lookup skew under low-concurrency usage may cause no locking problem at "
                f"all; record it and re-check if write volume grows. Note the value is still "
                f"non-selective for the query optimizer."
            )

    return issues, skewed_objects


# --------------------------------------------------------------------------------------
# Check 4 - bucket groups deployed without a membership step
# --------------------------------------------------------------------------------------
def _group_files(manifest_dir: Path):
    groups_dir = _groups_dir(manifest_dir)
    if groups_dir is None:
        return []
    files = sorted(groups_dir.glob("*.group"))
    files += sorted(groups_dir.glob("*.group-meta.xml"))
    return files


def _queue_member_group_names(queue_members) -> list[str]:
    """Group developer names under queueMembers/publicGroups/publicGroup.

    Shape confirmed in references/metadata-examples.md: `queueMembers`
    nests a `publicGroups` container of `publicGroup` leaves, each holding a
    Group developer name (not the `<name>` label).
    """
    if queue_members is None:
        return []
    names: list[str] = []
    public_groups = _child(queue_members, "publicGroups")
    if public_groups is not None:
        for child in public_groups:
            if _local(child.tag) != "publicGroup":
                continue
            value = child.text.strip() if child.text else ""
            if value:
                names.append(value)
    return names


def _nested_group_member_names(container) -> list[str]:
    """Group developer names nested under a Group's own membership element.

    The documented `Group` metadata type (references/metadata-examples.md)
    carries no such element today - membership is never part of Group
    metadata. This only fires if a manifest's Group XML shape adds one
    (e.g. a future API version, or a hand-authored fixture), so it is kept
    generic rather than assuming a fixed tag name is absent forever.
    """
    if container is None:
        return []
    names: list[str] = []
    for child in container:
        if _local(child.tag) not in ("group", "groupMember"):
            continue
        value = child.text.strip() if child.text else ""
        if value:
            names.append(value)
    return names


def check_group_membership(manifest_dir: Path) -> list[str]:
    """Groups deploy without members; a rule sourced from an empty bucket grants nothing."""
    issues: list[str] = []

    groups: dict[str, dict] = {}
    for xml_file in _group_files(manifest_dir):
        try:
            root = ET.parse(xml_file).getroot()
        except ET.ParseError as exc:
            issues.append(f"ERROR: Could not parse group file {xml_file.name}: {exc}")
            continue
        full_name = _text(root, "fullName") or xml_file.name.split(".")[0]
        groups[full_name] = {
            "file": xml_file.name,
            "doesIncludeBosses": _text(root, "doesIncludeBosses").lower() == "true",
        }

    if not groups:
        return issues

    referenced: dict[str, list[str]] = defaultdict(list)
    owner_sources: set[str] = set()

    # Sharing rules: sharedTo / sharedFrom group targets.
    for xml_file in _sharing_rule_files(manifest_dir):
        try:
            root = ET.parse(xml_file).getroot()
        except ET.ParseError:
            continue
        obj_name = _object_name_from_rule_file(xml_file)
        for kind, rule in _iter_rules(root):
            rule_name = _text(rule, "fullName") or "<unnamed rule>"
            for element_name in ("sharedTo", "sharedFrom"):
                for target_kind, target_name in _shared_targets(rule, element_name):
                    if target_kind != "group":
                        continue
                    referenced[target_name].append(
                        f"{obj_name}.{rule_name} ({element_name})"
                    )
                    if kind == "sharingOwnerRules" and element_name == "sharedFrom":
                        owner_sources.add(target_name)

    # Queues: queueMembers/publicGroups/publicGroup targets. A group that
    # only routes a queue is just as "used" as one named by a sharing rule -
    # missing the membership load step grants the queue nothing either way.
    for xml_file in _queue_files(manifest_dir):
        try:
            root = ET.parse(xml_file).getroot()
        except ET.ParseError as exc:
            issues.append(f"ERROR: Could not parse queue file {xml_file.name}: {exc}")
            continue
        queue_name = _text(root, "fullName") or xml_file.name.split(".")[0]
        queue_members = _child(root, "queueMembers")
        for group_name in _queue_member_group_names(queue_members):
            referenced[group_name].append(f"queue {queue_name} (queueMembers/publicGroups)")

    # Groups nested inside another Group's own membership element, if this
    # manifest's Group XML shape carries one (see _nested_group_member_names).
    for xml_file in _group_files(manifest_dir):
        try:
            root = ET.parse(xml_file).getroot()
        except ET.ParseError:
            continue
        owner_group_name = _text(root, "fullName") or xml_file.name.split(".")[0]
        nested_container = _child(root, "groupMembers")
        for nested_name in _nested_group_member_names(nested_container):
            referenced[nested_name].append(f"group {owner_group_name} (groupMembers)")

    for group_name, meta in sorted(groups.items()):
        uses = referenced.get(group_name, [])
        if uses:
            issues.append(
                f"WARN: Group '{group_name}' ({meta['file']}) is referenced by "
                f"{len(uses)} reference(s) ({', '.join(uses[:3])}) but Group "
                f"metadata never carries members - members are not migrated when the group "
                f"type is deployed. Pair this deploy with a GroupMember load step, or the "
                f"rule or queue resolves to an empty group and grants nothing."
            )
        else:
            issues.append(
                f"INFO: Group '{group_name}' ({meta['file']}) is deployed but no sharing "
                f"rule or queue in this manifest references it. Confirm it is used, or drop "
                f"it - an unused group still participates in group membership recalculation."
            )
        if meta["doesIncludeBosses"] and group_name in owner_sources:
            issues.append(
                f"WARN: Group '{group_name}' sources an ownership-based sharing rule and has "
                f"doesIncludeBosses=true (Grant Access Using Hierarchies). That adds role "
                f"hierarchy fan-out to a bucket whose purpose is to bound fan-out. Set it to "
                f"false unless hierarchy access is a stated requirement."
            )

    return issues


# --------------------------------------------------------------------------------------
# Check 5 - criteria rules filtering on unindexed fields
# --------------------------------------------------------------------------------------
def _indexed_fields_for_object(manifest_dir: Path, obj_name: str) -> set[str]:
    """Fields with an index: platform standard fields, relationships, externalId/unique."""
    indexed = set(PLATFORM_INDEXED_FIELDS)

    obj_dir = _objects_dir(manifest_dir)
    if obj_dir is None:
        return indexed

    field_files = list((obj_dir / obj_name / "fields").glob("*.field-meta.xml")) \
        if (obj_dir / obj_name / "fields").exists() else []

    for field_file in sorted(field_files):
        try:
            root = ET.parse(field_file).getroot()
        except ET.ParseError:
            continue
        full_name = _text(root, "fullName") or field_file.name.split(".")[0]
        field_type = _text(root, "type")
        is_external_id = _text(root, "externalId").lower() == "true"
        is_unique = _text(root, "unique").lower() == "true"
        if is_external_id or is_unique or field_type in ("Lookup", "MasterDetail", "Hierarchy"):
            indexed.add(full_name.lower())

    # Fields declared inside a single-file .object document.
    single_file = _first_existing(
        obj_dir / f"{obj_name}.object",
        obj_dir / obj_name / f"{obj_name}.object-meta.xml",
    )
    if single_file is not None:
        try:
            root = ET.parse(single_file).getroot()
        except ET.ParseError:
            root = None
        if root is not None:
            for field in root.findall(_tag("fields")):
                full_name = _text(field, "fullName")
                if not full_name:
                    continue
                field_type = _text(field, "type")
                if (
                    _text(field, "externalId").lower() == "true"
                    or _text(field, "unique").lower() == "true"
                    or field_type in ("Lookup", "MasterDetail", "Hierarchy")
                ):
                    indexed.add(full_name.lower())

    # Custom index components declared in this manifest.
    for candidate in (manifest_dir / "customindex",
                      manifest_dir / "force-app" / "main" / "default" / "customindex"):
        if candidate.exists():
            for index_file in sorted(candidate.glob("*.indx-meta*")):
                indexed.add(index_file.name.split(".")[0].lower())

    return indexed


def _load_check_config(manifest_dir: Path) -> dict:
    path = _first_existing(
        manifest_dir / "skew-check-config.json",
        manifest_dir / "config" / "skew-check-config.json",
    )
    if path is None:
        return {}
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return {}


def check_criteria_rule_selectivity(manifest_dir: Path) -> list[str]:
    """Criteria-based rules that filter on a field carrying no index."""
    issues: list[str] = []
    config = _load_check_config(manifest_dir)
    declared = {
        obj: {name.lower() for name in fields}
        for obj, fields in (config.get("indexedFields") or {}).items()
    }

    for xml_file in _sharing_rule_files(manifest_dir):
        try:
            root = ET.parse(xml_file).getroot()
        except ET.ParseError:
            continue
        obj_name = _object_name_from_rule_file(xml_file)
        indexed = _indexed_fields_for_object(manifest_dir, obj_name)
        indexed |= declared.get(obj_name, set())

        for rule in root.findall(_tag("sharingCriteriaRules")):
            rule_name = _text(rule, "fullName") or "<unnamed rule>"
            for criteria in rule.findall(_tag("criteriaItems")):
                field_name = _text(criteria, "field")
                if not field_name:
                    continue
                short_name = field_name.split(".")[-1]
                if short_name.lower() in indexed:
                    continue
                issues.append(
                    f"WARN: Criteria rule '{obj_name}.{rule_name}' filters on "
                    f"'{field_name}', which carries no index this manifest can see (not a "
                    f"platform-indexed standard field, not a relationship, not flagged "
                    f"externalId/unique, not in skew-check-config.json). The rule's own "
                    f"evaluation query scans, and every recalculation pays for it. Index the "
                    f"field, filter on an indexed one, or declare the index in "
                    f"skew-check-config.json if Support already created it."
                )

            include_all = _text(rule, "includeRecordsOwnedByAll")
            if include_all == "":
                issues.append(
                    f"WARN: Criteria rule '{obj_name}.{rule_name}' omits "
                    f"includeRecordsOwnedByAll. It is Required and cannot be edited after "
                    f"the rule is created - it decides whether records owned by users who "
                    f"cannot hold a role (integration and automated process users, the exact "
                    f"population ownership skew lives in) are shared. Set it explicitly."
                )

    return issues


# --------------------------------------------------------------------------------------
# Check 6 - Bulk API job plan
# --------------------------------------------------------------------------------------
def _load_job_plan(manifest_dir: Path, explicit: str | None):
    if explicit:
        path = Path(explicit)
        if not path.exists():
            return {"_error": f"Job plan not found: {path}"}, path
    else:
        path = _first_existing(
            manifest_dir / "bulk-job-plan.json",
            manifest_dir / "job-plan.json",
        )
        if path is None:
            return None, None
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle), path
    except (json.JSONDecodeError, OSError) as exc:
        return {"_error": f"Could not read job plan {path}: {exc}"}, path


def check_bulk_job_plan(plan, source_path, skewed_objects: set[str]) -> list[str]:
    """Parallel concurrency against a skewed target, unsorted child loads, 2.0 + Serial."""
    issues: list[str] = []

    if plan is None:
        return issues
    if "_error" in plan:
        return [f"ERROR: {plan['_error']}"]

    label = source_path.name if source_path is not None else "job plan"
    jobs = plan.get("jobs") or []
    if not jobs:
        return [f"INFO [{label}]: Job plan contains no jobs to check."]

    for job in jobs:
        name = job.get("name") or job.get("object") or "<unnamed job>"
        obj = job.get("object") or ""
        mode = (job.get("concurrencyMode") or "").strip().lower()
        api = (job.get("api") or "").strip().lower()
        sort_key = job.get("sortKey") or ""
        operation = (job.get("operation") or "").strip().lower()

        is_bulk_two = "2.0" in api or api in ("bulk2", "bulkv2", "bulk api 2")

        if is_bulk_two and mode == "serial":
            issues.append(
                f"ERROR [{label}]: Job '{name}' targets Bulk API 2.0 with "
                f"concurrencyMode=Serial. Bulk API 2.0 exposes concurrencyMode as reserved "
                f"for future use and supports parallel mode only - the mode is not user "
                f"configurable. Move this job to Bulk API v1 if serial processing is required."
            )

        if obj in skewed_objects and mode in ("", "parallel"):
            issues.append(
                f"WARN [{label}]: Job '{name}' loads {obj}, which the skew plan flagged, in "
                f"parallel mode ({mode or 'default'}). Parallel batches against a skewed "
                f"parent or lookup target contend on the same row. Sort the file by parent "
                f"first; if contention persists, run it as a Bulk API v1 job with "
                f"concurrencyMode=Serial."
            )

        if obj in skewed_objects and not sort_key:
            issues.append(
                f"WARN [{label}]: Job '{name}' loads {obj} with no sortKey. Sort main records "
                f"by their parent record so children of the same parent land in one batch "
                f"instead of several - the documented way to minimise locking conflicts."
            )

        if operation in ("upsert",) and obj in skewed_objects:
            issues.append(
                f"INFO [{label}]: Job '{name}' uses upsert on a skewed object. insert is "
                f"fastest, then update, then upsert; splitting upsert into insert and update "
                f"reduces the work done while the lock is held."
            )

    ordering = [str(step).strip().lower() for step in (plan.get("order") or [])]
    if ordering:
        def index_of(token: str) -> int:
            for position, step in enumerate(ordering):
                if token in step:
                    return position
            return -1

        roles_at = index_of("role")
        rules_at = index_of("sharing rule")
        groups_at = index_of("group")
        if roles_at > -1 and rules_at > -1 and roles_at > rules_at:
            issues.append(
                f"WARN [{label}]: Plan order loads sharing rules before roles. The documented "
                f"sequence is roles, then record data with owners, then public groups and "
                f"queues, then sharing rules one at a time."
            )
        if groups_at > -1 and rules_at > -1 and groups_at > rules_at:
            issues.append(
                f"WARN [{label}]: Plan order adds sharing rules before public groups and "
                f"queues are configured, so group computations have not propagated when the "
                f"rules begin evaluating."
            )

    return issues


# --------------------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------------------
def _severity(issue: str) -> str:
    """Classify an issue string by its leading tag.

    Every issue this checker produces is emitted as "SEVERITY: ..." or
    "SEVERITY [source]: ...". Anything without a recognised tag defaults to
    WARN rather than being silently dropped from the exit-code decision.
    """
    stripped = issue.lstrip()
    for severity in ("ERROR", "WARN", "INFO"):
        if stripped.startswith(severity):
            return severity
    return "WARN"


def check_data_skew_and_sharing_performance(
    manifest_dir: Path,
    skew_plan_arg: str | None = None,
    job_plan_arg: str | None = None,
) -> list[str]:
    issues: list[str] = []

    if not any(manifest_dir.iterdir()):
        return [
            f"WARN: Manifest directory {manifest_dir} is empty; nothing to check."
        ]

    issues.extend(check_sharing_rules(manifest_dir))
    issues.extend(check_object_owd(manifest_dir))
    issues.extend(check_group_membership(manifest_dir))
    issues.extend(check_criteria_rule_selectivity(manifest_dir))

    skew_plan, skew_path = _load_skew_plan(manifest_dir, skew_plan_arg)
    plan_issues, skewed_objects = check_skew_plan(skew_plan, skew_path)
    issues.extend(plan_issues)

    job_plan, job_path = _load_job_plan(manifest_dir, job_plan_arg)
    issues.extend(check_bulk_job_plan(job_plan, job_path, skewed_objects))

    if skew_plan is None:
        print(
            "NOTE: No skew plan supplied, so record-count checks were skipped. Skew is data, "
            "not metadata - the counts must come from a live org query. Run these, then pass "
            "the results as --skew-plan:\n"
            "  -- Ownership skew\n"
            "  SELECT OwnerId, COUNT(Id) cnt FROM <Object> GROUP BY OwnerId "
            "HAVING COUNT(Id) > 10000 ORDER BY COUNT(Id) DESC\n"
            "  -- Account (parent-child) skew\n"
            "  SELECT AccountId, COUNT(Id) cnt FROM Contact GROUP BY AccountId "
            "HAVING COUNT(Id) > 10000 ORDER BY COUNT(Id) DESC\n"
            "  -- Lookup skew: repeat per custom lookup field on the object\n"
            "  SELECT <Lookup_Field__c>, COUNT(Id) cnt FROM <Object> "
            "GROUP BY <Lookup_Field__c> HAVING COUNT(Id) > 10000 ORDER BY COUNT(Id) DESC\n"
            "Expected shape - skew-plan.json:\n"
            '  {"ownership": [{"object": "Lead", "owner": "Marketing Import User", '
            '"count": 120000}],\n'
            '   "parents":   [{"childObject": "Contact", "parentField": "AccountId", '
            '"parentName": "Unassigned Contacts", "count": 398000}],\n'
            '   "lookups":   [{"object": "Loan__c", "field": "Servicer__c", '
            '"targetId": "a0X...", "count": 903000, "concurrentWrites": true}]}\n'
            "Or skew-plan.csv with columns: "
            "kind,object,field,key,label,count,concurrent_writes\n"
            "Weight every lookup hit by write concurrency before remediating."
        )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ERROR: Manifest directory not found: {manifest_dir}")
        return 1

    issues = check_data_skew_and_sharing_performance(
        manifest_dir, args.skew_plan, args.job_plan
    )

    if not issues:
        print("No data skew or sharing performance issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    errors = [i for i in issues if _severity(i) == "ERROR"]
    warns = [i for i in issues if _severity(i) == "WARN"]
    infos = [i for i in issues if _severity(i) == "INFO"]

    print(
        f"\n{len(issues)} finding(s): {len(errors)} error, {len(warns)} warn, "
        f"{len(infos)} info."
    )

    if errors:
        return 1
    if args.strict and warns:
        print("--strict: failing on warnings.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
