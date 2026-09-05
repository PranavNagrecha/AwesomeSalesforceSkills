#!/usr/bin/env python3
"""Checker for the Lead Management and Conversion skill.

Runs against a Salesforce source-format (or MDAPI) directory and reports configuration
problems that Salesforce itself reports as silence.

Checks
------
1. LeadConvertSettings shape and referential integrity
   - `objectMapping` / `mappingFields` / `inputField` / `outputField` element names, and
     `inputObject` == Lead, `outputObject` in {Account, Contact, Opportunity}
     (Metadata API Guide, LeadConvertSettings).
   - Every `inputField` resolves to a CustomField on Lead in this manifest; every
     `outputField` resolves to a CustomField on the named output object.
   - Field types compatible where BOTH sides are present in the manifest.
   - Duplicate `outputObject` blocks (only one per object is meaningful).
   - `opportunityCreationOptions` restricted to the documented enum.
2. LeadStatus StandardValueSet has at least one `<converted>true</converted>` value.
3. Lead BusinessProcess subsets include at least one converted status value.
4. LeadConfigSettings: reports the values that change conversion behaviour, and flags
   the redundant NotVisible / doesSelectNoOpportunityOnConvertLead overlap.
5. Apex: `Database.convertLead` called inside a loop, or with a List and no
   partial-success (`allOrNone`) argument.
6. Cross-check: active Block duplicate rules on Lead with no User-table
   `duplicateRuleFilter`, and Lead auto-response rules with no active assignment rule.

Exit code 0 when nothing is reported, 1 otherwise.

Stdlib only.

Usage:
    python3 check_lead_management_and_conversion.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MDAPI_NS = "http://soap.sforce.com/2006/04/metadata"

VALID_OUTPUT_OBJECTS = {"Account", "Contact", "Opportunity"}
VALID_OPP_CREATION = {"VisibleOptional", "VisibleRequired", "NotVisible"}

# Metadata API FieldType values grouped by what can safely receive what.
# Conversion copies a value; a copy only lands if the target can hold the shape.
TYPE_FAMILY = {
    "Text": "text",
    "TextArea": "text",
    "LongTextArea": "text",
    "Html": "text",
    "Email": "email",
    "Phone": "phone",
    "Url": "url",
    "Picklist": "picklist",
    "MultiselectPicklist": "multipicklist",
    "Number": "number",
    "Currency": "currency",
    "Percent": "percent",
    "Integer": "number",
    "Long": "number",
    "Date": "date",
    "DateTime": "datetime",
    "Checkbox": "checkbox",
    "Lookup": "reference",
    "MasterDetail": "reference",
    "AutoNumber": "text",
    "Summary": "rollup",
    "Location": "location",
    "Time": "time",
}

# Families the platform will not silently coerce for you.
INCOMPATIBLE_MESSAGE = {
    ("text", "picklist"): "text into a picklist drops any value that is not an existing picklist entry",
    ("text", "number"): "text into a number field cannot be coerced",
    ("text", "checkbox"): "text into a checkbox cannot be coerced",
    ("text", "date"): "text into a date field cannot be coerced",
    ("text", "datetime"): "text into a datetime field cannot be coerced",
    ("picklist", "checkbox"): "picklist into a checkbox cannot be coerced",
    ("number", "picklist"): "number into a picklist drops any value that is not an existing picklist entry",
    ("number", "checkbox"): "number into a checkbox cannot be coerced",
    ("checkbox", "picklist"): "checkbox into a picklist cannot be coerced",
    ("date", "datetime"): "date into a datetime loses nothing but is not a like-for-like copy; confirm intent",
    ("datetime", "date"): "datetime into a date silently drops the time component",
    ("multipicklist", "picklist"): "multiselect into a single picklist drops every value after the first",
}


# ---------------------------------------------------------------------------
# XML helpers.  NEVER use `elem.find(a) or elem.find(b)` — a childless Element
# is falsy, so a real match can be discarded. Always test `is not None`.
# ---------------------------------------------------------------------------

def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def child_text(elem, name: str) -> str | None:
    """Return the text of the first direct child named `name`, namespace-agnostic."""
    if elem is None:
        return None
    for c in elem:
        if _strip_ns(c.tag) == name:
            return (c.text or "").strip()
    return None


def children(elem, name: str) -> list:
    if elem is None:
        return []
    return [c for c in elem if _strip_ns(c.tag) == name]


def descendants(root, name: str) -> list:
    return [e for e in root.iter() if _strip_ns(e.tag) == name]


def parse(path: Path, issues: list[str]):
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        issues.append(f"{path}: not well-formed XML ({exc})")
    except OSError as exc:
        issues.append(f"{path}: unreadable ({exc})")
    return None


def first_existing(*candidates: Path) -> Path | None:
    return next((p for p in candidates if p.is_file()), None)


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# Field inventory
# ---------------------------------------------------------------------------

def collect_fields(manifest_dir: Path, issues: list[str]) -> dict[str, dict[str, str]]:
    """Map {ObjectName: {fieldApiName: FieldType}} from both source and MDAPI layouts."""
    inventory: dict[str, dict[str, str]] = {}

    objects_dir = manifest_dir / "objects"
    if not objects_dir.is_dir():
        return inventory

    # Source format: objects/<Object>/fields/<Field>.field-meta.xml
    for field_file in objects_dir.glob("*/fields/*.field-meta.xml"):
        obj = field_file.parent.parent.name
        root = parse(field_file, issues)
        if root is None:
            continue
        name = child_text(root, "fullName") or field_file.name.split(".")[0]
        ftype = child_text(root, "type")
        if ftype:
            inventory.setdefault(obj, {})[name] = ftype

    # MDAPI / single-file format: objects/<Object>.object(-meta.xml) with nested <fields>
    for obj_file in list(objects_dir.glob("*.object")) + list(objects_dir.glob("*.object-meta.xml")):
        obj = obj_file.name.split(".")[0]
        root = parse(obj_file, issues)
        if root is None:
            continue
        for f in descendants(root, "fields"):
            name = child_text(f, "fullName")
            ftype = child_text(f, "type")
            if name and ftype:
                inventory.setdefault(obj, {})[name] = ftype

    # Source format also nests the object definition per folder
    for obj_file in objects_dir.glob("*/*.object-meta.xml"):
        obj = obj_file.parent.name
        root = parse(obj_file, issues)
        if root is None:
            continue
        for f in descendants(root, "fields"):
            name = child_text(f, "fullName")
            ftype = child_text(f, "type")
            if name and ftype:
                inventory.setdefault(obj, {})[name] = ftype

    return inventory


# ---------------------------------------------------------------------------
# Check 1: LeadConvertSettings
# ---------------------------------------------------------------------------

def check_lead_convert_settings(manifest_dir: Path, fields: dict, issues: list[str]) -> None:
    settings_file = first_existing(
        manifest_dir / "settings" / "LeadConvert.settings-meta.xml",
        manifest_dir / "settings" / "LeadConvert.settings",
        manifest_dir / "LeadConvertSettings" / "LeadConvert.leadConvertSetting",
        manifest_dir / "LeadConvert.settings-meta.xml",
    )
    if settings_file is None:
        issues.append(
            "LeadConvertSettings not present in this manifest. Custom Lead fields are dropped "
            "silently at conversion unless they are mapped. Retrieve it with "
            '`sf project retrieve start --metadata "Settings:LeadConvert"` and confirm the mapping '
            "is intentional before deploying Lead field changes."
        )
        return

    root = parse(settings_file, issues)
    if root is None:
        return
    where = rel(settings_file, manifest_dir)

    opp_option = child_text(root, "opportunityCreationOptions")
    if opp_option is not None and opp_option not in VALID_OPP_CREATION:
        issues.append(
            f"{where}: opportunityCreationOptions is '{opp_option}'. Valid values are "
            f"{sorted(VALID_OPP_CREATION)}."
        )

    mappings = children(root, "objectMapping")
    if not mappings:
        # Guard against the wrong element name, which parses fine and maps nothing.
        stray = descendants(root, "fieldMapping")
        if stray:
            issues.append(
                f"{where}: uses <fieldMapping>, which is not a LeadConvertSettings element. "
                "The correct shape is <objectMapping><mappingFields><inputField>/"
                "<outputField></mappingFields><outputObject>...</objectMapping>."
            )
        else:
            issues.append(
                f"{where}: no <objectMapping> blocks. No custom Lead field will transfer to "
                "Account, Contact, or Opportunity on conversion."
            )
        return

    if len(mappings) > 3:
        issues.append(
            f"{where}: {len(mappings)} objectMapping blocks. At most three are meaningful — "
            "one each for Account, Contact, and Opportunity."
        )

    seen_outputs: set[str] = set()
    lead_fields = fields.get("Lead", {})

    for om in mappings:
        input_object = child_text(om, "inputObject")
        output_object = child_text(om, "outputObject")

        if input_object != "Lead":
            issues.append(
                f"{where}: objectMapping has inputObject '{input_object}'. "
                "The value is always Lead."
            )
        if output_object not in VALID_OUTPUT_OBJECTS:
            issues.append(
                f"{where}: objectMapping has outputObject '{output_object}'. "
                f"Valid values are {sorted(VALID_OUTPUT_OBJECTS)}."
            )
            continue
        if output_object in seen_outputs:
            issues.append(
                f"{where}: more than one objectMapping block targets {output_object}. "
                "Merge them — only one block per output object is meaningful."
            )
        seen_outputs.add(output_object)

        pairs = children(om, "mappingFields")
        if not pairs:
            issues.append(
                f"{where}: objectMapping for {output_object} has no mappingFields entries."
            )
        target_fields = fields.get(output_object, {})
        seen_inputs: set[str] = set()

        for mf in pairs:
            src = child_text(mf, "inputField")
            dst = child_text(mf, "outputField")
            if not src or not dst:
                issues.append(
                    f"{where}: mappingFields entry for {output_object} is missing "
                    "inputField or outputField (both are required)."
                )
                continue

            if src in seen_inputs:
                issues.append(
                    f"{where}: Lead.{src} is mapped more than once to {output_object}. "
                    "One source field maps to one target field per object."
                )
            seen_inputs.add(src)

            src_type = lead_fields.get(src)
            dst_type = target_fields.get(dst)

            if lead_fields and src.endswith("__c") and src_type is None:
                issues.append(
                    f"{where}: inputField Lead.{src} has no CustomField definition in this "
                    "manifest. Deploying the mapping before the field fails; deploying it after a "
                    "field rename maps nothing."
                )
            if target_fields and dst.endswith("__c") and dst_type is None:
                issues.append(
                    f"{where}: outputField {output_object}.{dst} has no CustomField definition "
                    "in this manifest. The mapping cannot resolve its target."
                )

            if src_type and dst_type:
                fam_src = TYPE_FAMILY.get(src_type, src_type.lower())
                fam_dst = TYPE_FAMILY.get(dst_type, dst_type.lower())
                if fam_src != fam_dst:
                    reason = INCOMPATIBLE_MESSAGE.get((fam_src, fam_dst))
                    if reason:
                        issues.append(
                            f"{where}: Lead.{src} ({src_type}) -> {output_object}.{dst} "
                            f"({dst_type}) — {reason}. Conversion reports success and the target "
                            "is left blank."
                        )
                    else:
                        issues.append(
                            f"{where}: Lead.{src} ({src_type}) -> {output_object}.{dst} "
                            f"({dst_type}) — types differ. Verify the value actually lands "
                            "before releasing."
                        )
                elif fam_src == "picklist":
                    issues.append(
                        f"{where}: Lead.{src} -> {output_object}.{dst} is picklist-to-picklist. "
                        "Confirm every active Lead value exists on the target field, or the value "
                        "is dropped silently. A shared Global Value Set removes the drift."
                    )


# ---------------------------------------------------------------------------
# Check 2 + 3: converted status, and lead processes that can reach it
# ---------------------------------------------------------------------------

def check_lead_status(manifest_dir: Path, issues: list[str]) -> set[str]:
    """Return the set of Lead Status values flagged converted, if the file is present."""
    svs_file = first_existing(
        manifest_dir / "standardValueSets" / "LeadStatus.standardValueSet-meta.xml",
        manifest_dir / "standardValueSets" / "LeadStatus.standardValueSet",
        manifest_dir / "LeadStatus.standardValueSet-meta.xml",
    )
    if svs_file is None:
        return set()

    root = parse(svs_file, issues)
    if root is None:
        return set()
    where = rel(svs_file, manifest_dir)

    values = children(root, "standardValue")
    if not values:
        issues.append(
            f"{where}: no standardValue entries. A StandardValueSet deploy must contain at least "
            "one picklist value or it errors — and values omitted from the file are deactivated "
            "in the org."
        )
        return set()

    converted = set()
    for v in values:
        name = child_text(v, "fullName")
        if not name:
            continue
        if (child_text(v, "converted") or "").lower() == "true":
            if (child_text(v, "isActive") or "true").lower() == "false":
                issues.append(
                    f"{where}: '{name}' is flagged converted but isActive is false. "
                    "An inactive converted status cannot complete a conversion."
                )
            else:
                converted.add(name)

    if not converted:
        issues.append(
            f"{where}: no Lead Status value has <converted>true</converted>. Without one the "
            "Convert dialog has no status to finish with, and "
            "`SELECT ApiName FROM LeadStatus WHERE IsConverted = true` returns nothing."
        )
    return converted


def check_lead_processes(manifest_dir: Path, converted: set[str], issues: list[str]) -> None:
    if not converted:
        return  # nothing to check against

    candidates = [
        manifest_dir / "objects" / "Lead" / "Lead.object-meta.xml",
        manifest_dir / "objects" / "Lead.object",
        manifest_dir / "objects" / "Lead.object-meta.xml",
    ]
    obj_file = first_existing(*candidates)
    if obj_file is None:
        return

    root = parse(obj_file, issues)
    if root is None:
        return
    where = rel(obj_file, manifest_dir)

    for bp in descendants(root, "businessProcesses"):
        name = child_text(bp, "fullName") or "<unnamed>"
        if (child_text(bp, "isActive") or "true").lower() == "false":
            continue
        subset = {child_text(v, "fullName") for v in children(bp, "values")}
        if not subset & converted:
            issues.append(
                f"{where}: lead process '{name}' includes no converted status "
                f"(none of {sorted(converted)}). Users on the record types that use it cannot "
                "complete a conversion from the UI."
            )


# ---------------------------------------------------------------------------
# Check 4: LeadConfigSettings
# ---------------------------------------------------------------------------

def check_lead_config_settings(manifest_dir: Path, opp_not_visible: bool, issues: list[str]) -> None:
    cfg_file = first_existing(
        manifest_dir / "settings" / "LeadConfig.settings-meta.xml",
        manifest_dir / "settings" / "LeadConfig.settings",
        manifest_dir / "LeadConfig.settings-meta.xml",
    )
    if cfg_file is None:
        return

    root = parse(cfg_file, issues)
    if root is None:
        return
    where = rel(cfg_file, manifest_dir)

    require_validation = child_text(root, "shouldLeadConvertRequireValidation")
    if (require_validation or "").lower() == "false":
        issues.append(
            f"{where}: shouldLeadConvertRequireValidation is false. Validation rules, universally "
            "required custom fields, and lookup filters on Account, Contact, Opportunity, and Task "
            "are not enforced on the conversion path. Confirm this is a deliberate decision, not "
            "an inherited default."
        )

    preserve = child_text(root, "doesPreserveLeadStatus")
    if (preserve or "").lower() == "false":
        issues.append(
            f"{where}: doesPreserveLeadStatus is false. With record types in play, the lead status "
            "is replaced by the new owner's record-type default during conversion."
        )

    no_opp = (child_text(root, "doesSelectNoOpportunityOnConvertLead") or "").lower() == "true"
    if no_opp and opp_not_visible:
        issues.append(
            f"{where}: doesSelectNoOpportunityOnConvertLead is true while "
            "opportunityCreationOptions is NotVisible. Two switches suppress the same thing — keep "
            "one so the next admin knows which is load-bearing."
        )


# ---------------------------------------------------------------------------
# Check 5: Apex conversion code
# ---------------------------------------------------------------------------

LOOP_RE = re.compile(r"^\s*(for|while)\s*\(", re.IGNORECASE)
CONVERT_RE = re.compile(r"Database\s*\.\s*convertLead\s*\(", re.IGNORECASE)
CALL_ARG_RE = re.compile(r"Database\s*\.\s*convertLead\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)
# Locals declared as a collection of LeadConvert. A convertLead call inside a loop that passes
# one of these is a legitimate chunking loop, not a per-record DML loop.
LIST_DECL_RE = re.compile(
    r"(?:List\s*<\s*Database\s*\.\s*LeadConvert\s*>|Database\s*\.\s*LeadConvert\s*\[\s*\])"
    r"\s+([A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)


def check_apex(manifest_dir: Path, issues: list[str]) -> None:
    classes_dir = manifest_dir / "classes"
    triggers_dir = manifest_dir / "triggers"
    sources = []
    for d in (classes_dir, triggers_dir):
        if d.is_dir():
            sources.extend(sorted(d.rglob("*.cls")))
            sources.extend(sorted(d.rglob("*.trigger")))

    for src in sources:
        try:
            text = src.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not CONVERT_RE.search(text):
            continue

        where = rel(src, manifest_dir)
        list_vars = {m.group(1) for m in LIST_DECL_RE.finditer(text)}
        lines = text.splitlines()
        depth = 0
        loop_stack: list[int] = []

        for idx, line in enumerate(lines, start=1):
            stripped = line.split("//", 1)[0]
            if LOOP_RE.match(stripped):
                loop_stack.append(depth)
            opens = stripped.count("{")
            closes = stripped.count("}")

            call = CALL_ARG_RE.search(stripped)
            chunking = call is not None and call.group(1) in list_vars
            if CONVERT_RE.search(stripped) and loop_stack and not chunking:
                issues.append(
                    f"{where}:{idx}: Database.convertLead is called inside a loop. Each call spends "
                    "one of the 150 DML statements per transaction, so this fails at 151 leads. "
                    "Build a List<Database.LeadConvert>, chunk it at 100, and call convertLead once "
                    "per chunk."
                )

            depth += opens - closes
            while loop_stack and depth <= loop_stack[-1]:
                loop_stack.pop()

        # List form with no allOrNone / DMLOptions argument: a single failure rolls back the batch.
        for m in re.finditer(r"Database\s*\.\s*convertLead\s*\(([^;]*?)\)\s*;", text, re.DOTALL):
            args = m.group(1)
            if "," in args:
                continue
            line_no = text[: m.start()].count("\n") + 1
            issues.append(
                f"{where}:{line_no}: Database.convertLead called with no second argument, so "
                "allOrNone defaults to true. If this is the bulk path, one bad lead throws and "
                "rolls back every conversion in the call. Pass false and read "
                "LeadConvertResult.getErrors()."
            )

        if "IsConverted" not in text and "isConverted" not in text:
            issues.append(
                f"{where}: calls convertLead but never queries LeadStatus for IsConverted = true. "
                "A hardcoded converted-status label breaks the first time someone renames it."
            )


# ---------------------------------------------------------------------------
# Check 6: intake cross-checks
# ---------------------------------------------------------------------------

def check_intake_rules(manifest_dir: Path, issues: list[str]) -> None:
    # Block duplicate rules on Lead with no User-scoped filter
    dupe_dir = manifest_dir / "duplicateRules"
    if dupe_dir.is_dir():
        for f in sorted(dupe_dir.glob("Lead.*")):
            root = parse(f, issues)
            if root is None:
                continue
            if (child_text(root, "isActive") or "").lower() != "true":
                continue
            actions = {
                (child_text(root, "actionOnInsert") or ""),
                (child_text(root, "actionOnUpdate") or ""),
            }
            if "Block" not in actions:
                continue
            filt = children(root, "duplicateRuleFilter")
            tables = {child_text(i, "table") for f2 in filt for i in children(f2, "duplicateRuleFilterItems")}
            if "User" not in tables:
                issues.append(
                    f"{rel(f, manifest_dir)}: active duplicate rule on Lead with action Block and no "
                    "User-scoped duplicateRuleFilter. A matching Web-to-Lead submission is discarded "
                    "with no record and no notification. Add a filter item on table User excluding "
                    "the Web-to-Lead creator, or use Allow + alert."
                )

    # Auto-response without an active assignment rule
    arr_file = first_existing(
        manifest_dir / "autoResponseRules" / "Lead.autoResponseRules-meta.xml",
        manifest_dir / "autoResponseRules" / "Lead.autoResponseRules",
    )
    asn_file = first_existing(
        manifest_dir / "assignmentRules" / "Lead.assignmentRules-meta.xml",
        manifest_dir / "assignmentRules" / "Lead.assignmentRules",
    )
    if arr_file is None:
        return

    arr_root = parse(arr_file, issues)
    if arr_root is None:
        return

    active_arr = [
        r for r in descendants(arr_root, "autoResponseRule")
        if (child_text(r, "active") or "").lower() == "true"
    ]
    if not active_arr:
        return

    if asn_file is None:
        issues.append(
            f"{rel(arr_file, manifest_dir)}: an active Lead auto-response rule is deployed but no "
            "Lead assignment rules are in this manifest. Auto-response only fires when an "
            "assignment rule also fires on the record — confirm an active assignment rule with a "
            "catch-all entry exists in the target org."
        )
        return

    asn_root = parse(asn_file, issues)
    if asn_root is None:
        return
    active_asn = [
        r for r in descendants(asn_root, "assignmentRule")
        if (child_text(r, "active") or "").lower() == "true"
    ]
    if not active_asn:
        issues.append(
            f"{rel(asn_file, manifest_dir)}: no active Lead assignment rule, but "
            f"{rel(arr_file, manifest_dir)} has {len(active_arr)} active auto-response rule(s). "
            "Auto-response emails will not be sent."
        )
    else:
        # A catch-all entry has neither criteriaItems nor formula.
        has_catch_all = any(
            not children(entry, "criteriaItems") and child_text(entry, "formula") in (None, "")
            for rule in active_asn
            for entry in children(rule, "ruleEntry")
        )
        if not has_catch_all:
            issues.append(
                f"{rel(asn_file, manifest_dir)}: every active assignment rule entry has criteria, so "
                "leads matching none of them fall through — and their auto-response email is skipped "
                "too. Add a final catch-all entry."
            )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def opportunity_creation_not_visible(manifest_dir: Path) -> bool:
    f = first_existing(
        manifest_dir / "settings" / "LeadConvert.settings-meta.xml",
        manifest_dir / "settings" / "LeadConvert.settings",
    )
    if f is None:
        return False
    try:
        root = ET.parse(f).getroot()
    except (ET.ParseError, OSError):
        return False
    return child_text(root, "opportunityCreationOptions") == "NotVisible"


def run(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    if not manifest_dir.is_dir():
        return [f"Manifest directory not found: {manifest_dir}"]

    fields = collect_fields(manifest_dir, issues)
    check_lead_convert_settings(manifest_dir, fields, issues)
    converted = check_lead_status(manifest_dir, issues)
    check_lead_processes(manifest_dir, converted, issues)
    check_lead_config_settings(manifest_dir, opportunity_creation_not_visible(manifest_dir), issues)
    check_apex(manifest_dir, issues)
    check_intake_rules(manifest_dir, issues)
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Lead management and conversion metadata for configurations that fail silently. "
            "Point --manifest-dir at a Salesforce source or metadata directory "
            "(for example force-app/main/default)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce metadata directory (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    issues = run(Path(args.manifest_dir))
    if not issues:
        print("No issues found.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}")
    print(f"\n{len(issues)} issue(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
