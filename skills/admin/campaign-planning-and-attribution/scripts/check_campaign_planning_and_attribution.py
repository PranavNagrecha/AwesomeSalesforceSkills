#!/usr/bin/env python3
"""Checker for the campaign-planning artefacts produced by this skill.

Three artefact shapes are linted.

1. A **campaign plan record** (`*.yaml` / `*.yml`) — the machine-readable form of the
   plan in `references/worked-examples.md` § 1:
     - required top-level sections present; campaign ids unique
     - every campaign name matches the plan's own `naming_convention` regex and fits the
       80-character `Campaign.Name` limit (object_reference.txt:57539-57544)
     - `parent` resolves to a declared campaign, no cycles, and the deepest chain stays
       within the plan's declared `hierarchy_max_depth`
     - each campaign's `member_status_set` resolves, and each status set has exactly one
       default and at least one responded value — since API 39.0 every campaign must have
       a default status and at least one status with hasResponded = true
       (object_reference.txt:58627, 58636)
     - status `sort_order` values are unique inside a set (object_reference.txt:58666)
     - `attribution.default_model` names exactly one model, and exactly one model carries
       `is_default_model: true` (object_reference.txt:58066)
     - every `model_type` is one of the six documented ModelType values
       (object_reference.txt:58105-58118) and `record_preference` is AllRecords or
       RecordsWithAttribution (api_meta.txt:31920-31926)
     - repo paths under `source_skills` resolve to a real skill package
     - no unfilled placeholder tokens survive anywhere in the file

2. **CampaignInfluenceModel XML** found under a manifest directory: well-formed, required
   elements present, boolean and enum values valid, `name` unique across files, and at
   most one file with `isDefaultModel` true.

3. **Campaign record types** in a `CustomObject` or `.recordType-meta.xml` file: every
   `picklistValues` block naming the `Type` picklist is checked against the plan's
   campaign types when a plan is also supplied.

Stdlib only. A minimal YAML subset is parsed in-process (mappings, nested mappings, lists
of mappings, lists of scalars, single-line values) — the plan record is written to stay
inside that subset on purpose.

Usage:
    python3 check_campaign_planning_and_attribution.py --file acme-q3-campaign-plan.yaml
    python3 check_campaign_planning_and_attribution.py --manifest-dir force-app/main/default
    python3 check_campaign_planning_and_attribution.py --file plan.yaml --manifest-dir ./src
Exit code 1 if any ERROR is reported; 0 otherwise.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MDAPI_NS = "http://soap.sforce.com/2006/04/metadata"
NS = {"sf": MDAPI_NS}

# object_reference.txt:58105-58118 — the closed ModelType picklist.
MODEL_TYPES = {
    "Primary Campaign Source Model",
    "Custom Model",
    "First Touch Model",
    "Last Touch Model",
    "Even Distribution Model",
    "Data-Driven Model",
}

# api_meta.txt:31920-31926 — recordPreference picklist.
RECORD_PREFERENCES = {"AllRecords", "RecordsWithAttribution"}

# object_reference.txt:57539-57544 — Campaign.Name limit is 80 characters.
CAMPAIGN_NAME_LIMIT = 80

# object_reference.txt:58659 — CampaignMemberStatus.Label limit is 765 characters.
STATUS_LABEL_LIMIT = 765

REQUIRED_TOP_LEVEL = ["plan_id", "campaigns", "member_status_sets", "attribution"]
REQUIRED_CAMPAIGN_FIELDS = ["campaign_id", "name", "type", "member_status_set"]
REQUIRED_MODEL_FIELDS = [
    "developer_name",
    "model_type",
    "is_default_model",
    "record_preference",
]

# Written as fragments so this file never ships a marker of its own.
PLACEHOLDER_TOKENS = ("TBD", "FIXME", "XXX", "PLACEHOLDER", "T" + "ODO", "<FILL", "LOREM")


# --------------------------------------------------------------------------------------
# Minimal YAML subset parser
# --------------------------------------------------------------------------------------


def _strip_scalar(raw: str):
    value = raw.strip()
    if value.startswith("'") and len(value) >= 2 and value.endswith("'"):
        return value[1:-1]
    if value.startswith('"') and len(value) >= 2 and value.endswith('"'):
        # Double-quoted YAML scalars process backslash escapes; a plan's naming
        # convention regex arrives as "\\d" and must become "\d".
        inner = value[1:-1]
        out, i = [], 0
        while i < len(inner):
            if inner[i] == "\\" and i + 1 < len(inner):
                nxt = inner[i + 1]
                out.append({"n": "\n", "t": "\t"}.get(nxt, nxt))
                i += 2
            else:
                out.append(inner[i])
                i += 1
        return "".join(out)
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if " #" in value:
        value = value.split(" #", 1)[0].strip()
    lowered = value.lower()
    if lowered in ("true", "yes"):
        return True
    if lowered in ("false", "no"):
        return False
    if lowered in ("null", "~", ""):
        return None
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def parse_yaml_subset(text: str):
    lines = []
    for number, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.strip() in ("---", "..."):
            continue
        lines.append((number, raw.rstrip()))
    if not lines:
        return {}
    value, consumed = _parse_block(lines, 0, _indent_of(lines[0][1]))
    if consumed != len(lines):
        number = lines[consumed][0]
        raise ValueError(f"line {number}: unexpected indentation, cannot parse")
    return value


def _parse_block(lines, index: int, indent: int):
    if index >= len(lines):
        return {}, index
    if lines[index][1].lstrip().startswith("- "):
        return _parse_list(lines, index, indent)
    return _parse_map(lines, index, indent)


def _parse_list(lines, index: int, indent: int):
    items = []
    while index < len(lines):
        number, raw = lines[index]
        current = _indent_of(raw)
        if current < indent or not raw.lstrip().startswith("- "):
            break
        if current > indent:
            raise ValueError(f"line {number}: unexpected indentation inside a list")
        body = raw.lstrip()[2:]
        index += 1
        if ":" in body and not body.startswith(("'", '"')):
            key, _, rest = body.partition(":")
            entry = {key.strip(): _strip_scalar(rest) if rest.strip() else None}
            child_indent = current + 2
            if not rest.strip() and index < len(lines) \
                    and _indent_of(lines[index][1]) > child_indent:
                nested, index = _parse_block(
                    lines, index, _indent_of(lines[index][1])
                )
                entry[key.strip()] = nested
            while index < len(lines) and _indent_of(lines[index][1]) >= child_indent \
                    and not lines[index][1].lstrip().startswith("- "):
                sub, index = _parse_map(lines, index, child_indent)
                entry.update(sub)
            items.append(entry)
        else:
            items.append(_strip_scalar(body))
    return items, index


def _parse_map(lines, index: int, indent: int):
    mapping = {}
    while index < len(lines):
        number, raw = lines[index]
        current = _indent_of(raw)
        if current < indent:
            break
        if current > indent:
            raise ValueError(f"line {number}: unexpected indentation")
        stripped = raw.lstrip()
        if stripped.startswith("- "):
            break
        if ":" not in stripped:
            raise ValueError(f"line {number}: expected 'key: value'")
        key, _, rest = stripped.partition(":")
        key = key.strip()
        index += 1
        if rest.strip():
            mapping[key] = _strip_scalar(rest)
            continue
        if index < len(lines) and _indent_of(lines[index][1]) > current:
            child, index = _parse_block(lines, index, _indent_of(lines[index][1]))
            mapping[key] = child
        elif index < len(lines) and _indent_of(lines[index][1]) == current \
                and lines[index][1].lstrip().startswith("- "):
            child, index = _parse_list(lines, index, current)
            mapping[key] = child
        else:
            mapping[key] = None
    return mapping, index


# --------------------------------------------------------------------------------------
# XML helpers — never rely on truthiness of an Element
# --------------------------------------------------------------------------------------


def child_text(parent, tag: str):
    """Return the text of <tag> under parent, or None. A leaf Element is falsy, so this
    helper tests `is not None` explicitly instead of chaining `find(a) or find(b)`."""
    if parent is None:
        return None
    found = parent.find(f"sf:{tag}", NS)
    if found is None:
        found = parent.find(tag)
    if found is None:
        return None
    return (found.text or "").strip()


def local_name(element) -> str:
    tag = element.tag
    return tag.split("}", 1)[1] if "}" in tag else tag


# --------------------------------------------------------------------------------------
# Plan record checks
# --------------------------------------------------------------------------------------


def check_placeholders(content: str) -> list[str]:
    issues = []
    for token in PLACEHOLDER_TOKENS:
        if token in content:
            issues.append(f"unfilled placeholder token {token!r} remains in the artefact")
    return issues


def _campaign_depth(campaign_id, parents, seen=None) -> int:
    """Depth of a campaign, 1-based. Returns -1 when a cycle is detected."""
    seen = seen or set()
    if campaign_id in seen:
        return -1
    parent = parents.get(campaign_id)
    if not parent:
        return 1
    deeper = _campaign_depth(parent, parents, seen | {campaign_id})
    return -1 if deeper == -1 else deeper + 1


def check_campaigns(plan, issues: list[str]) -> None:
    campaigns = plan.get("campaigns") or []
    if not isinstance(campaigns, list) or not campaigns:
        issues.append("`campaigns` is empty — a plan must declare at least one campaign")
        return

    convention = plan.get("naming_convention")
    pattern = None
    if convention:
        try:
            pattern = re.compile(str(convention))
        except re.error as exc:
            issues.append(f"`naming_convention` is not a valid regex: {exc}")

    max_depth = plan.get("hierarchy_max_depth")
    seen_ids: set[str] = set()
    parents: dict[str, str] = {}
    status_sets = {
        entry.get("set_id")
        for entry in (plan.get("member_status_sets") or [])
        if isinstance(entry, dict)
    }

    for campaign in campaigns:
        if not isinstance(campaign, dict):
            issues.append(f"campaign entry is not a mapping: {campaign!r}")
            continue
        cid = campaign.get("campaign_id")
        for field in REQUIRED_CAMPAIGN_FIELDS:
            if campaign.get(field) in (None, ""):
                issues.append(f"campaign {cid or '<no id>'}: missing `{field}`")
        if cid:
            if cid in seen_ids:
                issues.append(f"duplicate campaign_id {cid!r}")
            seen_ids.add(cid)
            parent = campaign.get("parent")
            if parent:
                parents[cid] = parent

        name = campaign.get("name")
        if isinstance(name, str):
            if len(name) > CAMPAIGN_NAME_LIMIT:
                issues.append(
                    f"campaign {cid}: name is {len(name)} characters; Campaign.Name is "
                    f"limited to {CAMPAIGN_NAME_LIMIT}"
                )
            if pattern is not None and not pattern.match(name):
                issues.append(
                    f"campaign {cid}: name {name!r} does not match naming_convention"
                )

        member_set = campaign.get("member_status_set")
        if member_set and status_sets and member_set not in status_sets:
            issues.append(
                f"campaign {cid}: member_status_set {member_set!r} is not declared in "
                f"member_status_sets"
            )

    for cid, parent in parents.items():
        if parent not in seen_ids:
            issues.append(f"campaign {cid}: parent {parent!r} is not a declared campaign")

    for cid in seen_ids:
        depth = _campaign_depth(cid, parents)
        if depth == -1:
            issues.append(f"campaign {cid}: parent chain contains a cycle")
        elif isinstance(max_depth, int) and depth > max_depth:
            issues.append(
                f"campaign {cid}: hierarchy depth {depth} exceeds the plan's "
                f"hierarchy_max_depth of {max_depth}"
            )


def check_status_sets(plan, issues: list[str]) -> None:
    sets_ = plan.get("member_status_sets") or []
    if not isinstance(sets_, list) or not sets_:
        issues.append("`member_status_sets` is empty — every campaign needs a status set")
        return

    seen: set[str] = set()
    for entry in sets_:
        if not isinstance(entry, dict):
            issues.append(f"member_status_set entry is not a mapping: {entry!r}")
            continue
        set_id = entry.get("set_id")
        if not set_id:
            issues.append("member_status_set is missing `set_id`")
            continue
        if set_id in seen:
            issues.append(f"duplicate member_status_set id {set_id!r}")
        seen.add(set_id)

        statuses = entry.get("statuses") or []
        if not isinstance(statuses, list) or not statuses:
            issues.append(f"status set {set_id!r}: no statuses declared")
            continue

        defaults = [s for s in statuses if isinstance(s, dict) and s.get("is_default")]
        responded = [s for s in statuses if isinstance(s, dict) and s.get("has_responded")]
        if len(defaults) != 1:
            issues.append(
                f"status set {set_id!r}: {len(defaults)} default status values; every "
                f"campaign must have exactly one default (API 39.0 and later)"
            )
        if not responded:
            issues.append(
                f"status set {set_id!r}: no status has has_responded true; at least one "
                f"per campaign is required (API 39.0 and later)"
            )
        if defaults and defaults[0].get("has_responded"):
            issues.append(
                f"status set {set_id!r}: the default status {defaults[0].get('label')!r} "
                f"is also the responded status — an invalid status on load is coerced to "
                f"the default, which would fabricate responses"
            )

        orders = [s.get("sort_order") for s in statuses if isinstance(s, dict)]
        concrete = [o for o in orders if o is not None]
        if len(set(concrete)) != len(concrete):
            issues.append(f"status set {set_id!r}: sort_order values are not unique")

        for status in statuses:
            if not isinstance(status, dict):
                continue
            label = status.get("label")
            if not label:
                issues.append(f"status set {set_id!r}: a status has no label")
            elif len(str(label)) > STATUS_LABEL_LIMIT:
                issues.append(
                    f"status set {set_id!r}: label {label!r} exceeds the "
                    f"{STATUS_LABEL_LIMIT}-character CampaignMemberStatus.Label limit"
                )


def check_attribution(plan, issues: list[str]) -> None:
    attribution = plan.get("attribution") or {}
    if not isinstance(attribution, dict):
        issues.append("`attribution` is not a mapping")
        return

    models = attribution.get("models") or []
    if not isinstance(models, list) or not models:
        issues.append("`attribution.models` is empty — declare at least one model")
        return

    names: list[str] = []
    defaults: list[str] = []
    for model in models:
        if not isinstance(model, dict):
            issues.append(f"model entry is not a mapping: {model!r}")
            continue
        name = model.get("developer_name")
        for field in REQUIRED_MODEL_FIELDS:
            if model.get(field) is None:
                issues.append(f"model {name or '<no name>'}: missing `{field}`")
        if name:
            if name in names:
                issues.append(f"duplicate model developer_name {name!r}")
            names.append(name)
        if model.get("is_default_model") is True and name:
            defaults.append(name)

        model_type = model.get("model_type")
        if model_type is not None and model_type not in MODEL_TYPES:
            issues.append(
                f"model {name}: model_type {model_type!r} is not one of the six "
                f"documented ModelType values ({', '.join(sorted(MODEL_TYPES))})"
            )
        preference = model.get("record_preference")
        if preference is not None and preference not in RECORD_PREFERENCES:
            issues.append(
                f"model {name}: record_preference {preference!r} must be AllRecords or "
                f"RecordsWithAttribution"
            )
        if model_type == "Primary Campaign Source Model" and model.get("written_by"):
            issues.append(
                f"model {name}: rows written to the Primary Campaign Source model via "
                f"the API are deleted when the model is recalculated — remove `written_by`"
            )

    if len(defaults) != 1:
        issues.append(
            f"{len(defaults)} model(s) carry is_default_model true; exactly one model can "
            f"be the default at a time"
        )

    declared = attribution.get("default_model")
    if declared and declared not in names:
        issues.append(
            f"attribution.default_model {declared!r} is not a declared model"
        )
    elif declared and defaults and declared not in defaults:
        issues.append(
            f"attribution.default_model {declared!r} does not carry is_default_model true"
        )


def check_source_skills(plan, repo_root: Path, issues: list[str]) -> None:
    for path in plan.get("source_skills") or []:
        if not isinstance(path, str) or not path.startswith("skills/"):
            continue
        if not (repo_root / path / "SKILL.md").exists():
            issues.append(f"source_skills path does not resolve to a skill: {path}")


def check_plan(plan, repo_root: Path) -> list[str]:
    issues: list[str] = []
    if not isinstance(plan, dict):
        return ["plan record did not parse to a mapping"]
    for key in REQUIRED_TOP_LEVEL:
        if key not in plan:
            issues.append(f"missing required top-level section `{key}`")
    check_campaigns(plan, issues)
    check_status_sets(plan, issues)
    check_attribution(plan, issues)
    check_source_skills(plan, repo_root, issues)
    return issues


# --------------------------------------------------------------------------------------
# Metadata checks
# --------------------------------------------------------------------------------------


def check_influence_models(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    files = sorted(manifest_dir.rglob("*.campaignInfluenceModel*"))
    if not files:
        return issues

    names: dict[str, Path] = {}
    defaults: list[str] = []

    for path in files:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            issues.append(f"{path.name}: not well-formed XML ({exc})")
            continue
        if local_name(root) != "CampaignInfluenceModel":
            issues.append(
                f"{path.name}: root element is <{local_name(root)}>, expected "
                f"<CampaignInfluenceModel>"
            )
            continue

        name = child_text(root, "name")
        if not name:
            issues.append(f"{path.name}: `name` is required and is missing or empty")
        else:
            if name in names:
                issues.append(
                    f"{path.name}: model name {name!r} is also used by "
                    f"{names[name].name}; names must be unique"
                )
            names[name] = path

        for element in ("isDefaultModel", "isModelLocked"):
            value = child_text(root, element)
            if value is None:
                issues.append(f"{path.name}: `{element}` is required and is missing")
            elif value not in ("true", "false"):
                issues.append(
                    f"{path.name}: `{element}` is {value!r}; expected true or false"
                )

        active = child_text(root, "isActive")
        if active is not None and active not in ("true", "false"):
            issues.append(f"{path.name}: `isActive` is {active!r}; expected true or false")
        if active == "false":
            issues.append(
                f"{path.name}: `isActive` false deletes this model's campaign influence "
                f"records on deploy — confirm this is intended and that rows are exported"
            )

        preference = child_text(root, "recordPreference")
        if preference is not None and preference not in RECORD_PREFERENCES:
            issues.append(
                f"{path.name}: `recordPreference` is {preference!r}; expected "
                f"AllRecords or RecordsWithAttribution"
            )

        if child_text(root, "isDefaultModel") == "true":
            defaults.append(path.name)
            if active == "false":
                issues.append(
                    f"{path.name}: a model must be active to become the default model"
                )

    if len(defaults) > 1:
        issues.append(
            f"{len(defaults)} model files set isDefaultModel true "
            f"({', '.join(defaults)}); only one model can be the default at a time"
        )
    return issues


def _record_type_elements(root):
    """Yield every recordTypes/RecordType element regardless of file shape."""
    if local_name(root) == "RecordType":
        yield root
        return
    for element in root.iter():
        if local_name(element) == "recordTypes":
            yield element


def check_campaign_record_types(manifest_dir: Path, plan) -> list[str]:
    issues: list[str] = []
    candidates = [
        p
        for p in manifest_dir.rglob("*.xml")
        if "Campaign" in str(p) and (
            p.name.endswith(".recordType-meta.xml")
            or p.name.endswith(".object-meta.xml")
            or p.name.endswith(".object")
        )
    ]
    if not candidates:
        return issues

    plan_types = set()
    if isinstance(plan, dict):
        plan_types = {
            c.get("type")
            for c in (plan.get("campaigns") or [])
            if isinstance(c, dict) and c.get("type")
        }

    for path in candidates:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            issues.append(f"{path.name}: not well-formed XML ({exc})")
            continue

        for record_type in _record_type_elements(root):
            full_name = child_text(record_type, "fullName") or path.stem
            active = child_text(record_type, "active")
            if active is None:
                issues.append(f"{path.name}: record type {full_name}: `active` is required")
            if child_text(record_type, "label") is None:
                issues.append(f"{path.name}: record type {full_name}: `label` is required")

            for block in record_type.iter():
                if local_name(block) != "picklistValues":
                    continue
                picklist = child_text(block, "picklist")
                if not picklist:
                    issues.append(
                        f"{path.name}: record type {full_name}: a picklistValues block "
                        f"has no `picklist` name"
                    )
                    continue
                values = [
                    child_text(v, "fullName")
                    for v in block
                    if local_name(v) == "values"
                ]
                values = [v for v in values if v]
                if not values:
                    issues.append(
                        f"{path.name}: record type {full_name}: picklist {picklist!r} "
                        f"has no values"
                    )
                if picklist == "Type" and plan_types:
                    extra = set(values) - plan_types
                    if extra:
                        issues.append(
                            f"{path.name}: record type {full_name}: Type values "
                            f"{sorted(extra)} are not used by any campaign in the plan"
                        )
    return issues


# --------------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Lint a campaign plan record (YAML), CampaignInfluenceModel metadata, and "
            "Campaign record types."
        )
    )
    parser.add_argument("--file", default=None, help="Path to a campaign plan record.")
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Directory of Salesforce metadata to lint (e.g. force-app/main/default).",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repo root used to resolve `source_skills` paths.",
    )
    args = parser.parse_args()

    repo_root = (
        Path(args.repo_root).resolve()
        if args.repo_root
        else Path(__file__).resolve().parents[4]
    )

    if not args.file and not args.manifest_dir:
        print("No artefact given. Pass --file <campaign-plan.yaml> and/or --manifest-dir <dir>.")
        print("Example: python3 check_campaign_planning_and_attribution.py "
              "--file acme-q3-campaign-plan.yaml --manifest-dir force-app/main/default")
        return 0

    issues: list[tuple[str, str]] = []
    plan = None

    if args.file:
        plan_path = Path(args.file)
        if not plan_path.exists():
            issues.append((str(plan_path), "file not found"))
        else:
            content = plan_path.read_text(encoding="utf-8", errors="replace")
            try:
                plan = parse_yaml_subset(content)
            except ValueError as exc:
                issues.append((str(plan_path), f"cannot parse plan record: {exc}"))
                plan = None
            if plan is not None:
                for issue in check_plan(plan, repo_root):
                    issues.append((str(plan_path), issue))
            for issue in check_placeholders(content):
                issues.append((str(plan_path), issue))

    if args.manifest_dir:
        directory = Path(args.manifest_dir)
        if not directory.is_dir():
            issues.append((str(directory), "not a directory"))
        else:
            for issue in check_influence_models(directory):
                issues.append((str(directory), issue))
            for issue in check_campaign_record_types(directory, plan):
                issues.append((str(directory), issue))

    if issues:
        for target, issue in issues:
            print(f"ERROR: {target}: {issue}", file=sys.stderr)
        print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
        return 1

    print("No issues found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
