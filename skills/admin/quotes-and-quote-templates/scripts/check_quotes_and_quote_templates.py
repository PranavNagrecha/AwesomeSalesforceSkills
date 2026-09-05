#!/usr/bin/env python3
"""Checker for standard Salesforce Quotes metadata.

Scans a Salesforce source directory for configuration mistakes that the
Metadata API and Object Reference say will fail, silently no-op, or destroy
existing configuration on deploy.

Grounding for each check is cited inline against the Summer '26 (v66) guides:
  api_meta.txt        Metadata API Developer Guide
  object_reference.txt Object Reference for the Salesforce Platform

Scope: standard Quotes only. CPQ (SBQQ__*) is a different data model.

Usage:
    python3 check_quotes_and_quote_templates.py --manifest-dir force-app/main/default
    python3 check_quotes_and_quote_templates.py --manifest-dir . --quiet
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = "{http://soap.sforce.com/2006/04/metadata}"

# Quote.Status standard options, Object Reference L239996-240005.
STANDARD_QUOTE_STATUSES = [
    "Draft",
    "Needs Review",
    "In Review",
    "Approved",
    "Rejected",
    "Presented",
    "Accepted",
    "Denied",
]

# Quote fields with no Create and no Update property in the Object Reference
# field table (L239236-240010). Writing them from a Flow/field update is a
# deploy-time or run-time failure, not a warning.
QUOTE_READ_ONLY_FIELDS = {
    "AccountId": "Filter, Group, Nillable, Sort",
    "Discount": "Filter, Nillable, Sort - derived from QuoteLineItem subtotals",
    "GrandTotal": "Filter, Nillable - system-calculated summary",
    "IsSyncing": "Defaulted on create, Filter",
    "LineItemCount": "Filter, Nillable",
    "QuoteNumber": "Defaulted on create, Filter - system generated",
    "Subtotal": "Filter, Nillable",
    "TotalPrice": "Filter, Nillable",
}

# Object Reference L239630-239637: GrandTotal "is not directly referenceable or
# usable in custom formula fields on the Quote object".
QUOTE_FORMULA_FORBIDDEN = {"GrandTotal"}

CHECKLIST_REQUIRED_TOP = ["template_name", "org", "last_reviewed", "sections", "verified_in_org"]
CHECKLIST_REQUIRED_SECTIONS = ["header", "line_items", "footer"]
CHECKLIST_REQUIRED_VERIFIED = ["pdf_generated", "line_items_rendered", "email_quote_tested"]


# ---------------------------------------------------------------------------
# XML helpers. A leaf ElementTree Element is falsy, so `a.find(x) or a.find(y)`
# silently discards a real match. Everything below tests `is not None`.
# ---------------------------------------------------------------------------

def find_first(parent, *tags):
    """Return the first child matching any tag, namespaced or bare. Never falsy-tests."""
    for tag in tags:
        for candidate in (MD_NS + tag, tag):
            found = parent.find(candidate)
            if found is not None:
                return found
    return None


def find_all(parent, tag):
    """Return every descendant matching tag, namespaced or bare."""
    out = list(parent.iter(MD_NS + tag))
    if not out:
        out = list(parent.iter(tag))
    return out


def text_of(parent, *tags, default=""):
    node = find_first(parent, *tags)
    if node is None or node.text is None:
        return default
    return node.text.strip()


def parse_xml(path: Path):
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        return exc


def iter_files(root: Path, pattern: str):
    return sorted(root.rglob(pattern))


def has_quote_metadata(root: Path) -> list[Path]:
    """Every file in the manifest that is Quote or QuoteLineItem configuration."""
    hits: list[Path] = []
    for obj in ("Quote", "QuoteLineItem"):
        for d in root.rglob(f"objects/{obj}"):
            if d.is_dir():
                hits.extend(p for p in d.rglob("*.xml"))
        hits.extend(iter_files(root, f"{obj}.object-meta.xml"))
        hits.extend(iter_files(root, f"{obj}-*.layout-meta.xml"))
    hits.extend(iter_files(root, "QuoteStatus.standardValueSet-meta.xml"))
    for flow in iter_files(root, "*.flow-meta.xml"):
        root_el = parse_xml(flow)
        if isinstance(root_el, ET.ParseError):
            continue
        for obj_el in find_all(root_el, "object"):
            if (obj_el.text or "").strip() in ("Quote", "QuoteLineItem"):
                hits.append(flow)
                break
    return sorted(set(hits))


# ---------------------------------------------------------------------------
# Check 1 - QuoteSettings must enable Quotes when Quote metadata ships
# ---------------------------------------------------------------------------

def check_quote_settings(root: Path) -> list[str]:
    """api_meta.txt L124911: enableQuote true is the precondition for all Quote access."""
    issues: list[str] = []
    quote_meta = has_quote_metadata(root)
    settings_files = iter_files(root, "Quote.settings-meta.xml") + iter_files(root, "Quote.settings")

    if not settings_files:
        if quote_meta:
            sample = ", ".join(p.name for p in quote_meta[:3])
            issues.append(
                f"ERROR: {len(quote_meta)} Quote/QuoteLineItem component(s) in this manifest "
                f"({sample}...) but no settings/Quote.settings-meta.xml. Deploying Quote "
                "metadata into an org where Quotes are off fails. Add QuoteSettings with "
                "<enableQuote>true</enableQuote> (api_meta.txt L124911) as step 1 of the "
                "deploy order."
            )
        return issues

    for path in settings_files:
        el = parse_xml(path)
        if isinstance(el, ET.ParseError):
            issues.append(f"ERROR [{path.name}]: not well-formed XML - {el}")
            continue

        enable = text_of(el, "enableQuote").lower()
        if enable != "true":
            issues.append(
                f"ERROR [{path.name}]: enableQuote is '{enable or 'absent'}', not 'true'. "
                "Users cannot access Quotes and every other component here is inert "
                "(api_meta.txt L124911)."
            )

        without_opp = text_of(el, "enableQuotesWithoutOppEnabled").lower()
        uses_quote_account = any(
            "QuoteAccountId" in p.read_text(encoding="utf-8", errors="replace")
            for p in quote_meta
        )
        if uses_quote_account and without_opp != "true":
            issues.append(
                f"ERROR [{path.name}]: metadata references Quote.QuoteAccountId but "
                f"enableQuotesWithoutOppEnabled is '{without_opp or 'absent'}'. That field "
                "is only available when Create Quotes Without a Related Opportunity is "
                "enabled (object_reference.txt L239729-239736)."
            )
        if without_opp == "false":
            issues.append(
                f"REVIEW [{path.name}]: enableQuotesWithoutOppEnabled is false. If the "
                "target org currently has standalone quotes, the guide requires deleting "
                "them before this setting can go to false (api_meta.txt L124918). Query "
                "'SELECT COUNT() FROM Quote WHERE OpportunityId = NULL' before deploying."
            )
    return issues


# ---------------------------------------------------------------------------
# Check 2 - QuoteStatus StandardValueSet completeness and allowEmail
# ---------------------------------------------------------------------------

def _collect_status_literals(root: Path) -> dict[str, list[str]]:
    """Status strings referenced by Quote validation rules and Quote flows."""
    refs: dict[str, list[str]] = {}

    def record(value: str, source: str) -> None:
        refs.setdefault(value, []).append(source)

    pickval = re.compile(r"ISPICKVAL\s*\(\s*(?:\$Record\.)?Status\s*,\s*[\"']([^\"']+)[\"']", re.I)
    text_eq = re.compile(r"\bStatus\s*[=!]=?\s*[\"']([^\"']+)[\"']", re.I)

    for path in iter_files(root, "*.validationRule-meta.xml"):
        if "Quote" not in str(path):
            continue
        el = parse_xml(path)
        if isinstance(el, ET.ParseError):
            continue
        formula = text_of(el, "errorConditionFormula")
        for pattern in (pickval, text_eq):
            for match in pattern.findall(formula):
                record(match, path.name)

    for path in iter_files(root, "*.flow-meta.xml"):
        el = parse_xml(path)
        if isinstance(el, ET.ParseError):
            continue
        objects = {(o.text or "").strip() for o in find_all(el, "object")}
        if "Quote" not in objects:
            continue
        for field_el in find_all(el, "field"):
            if (field_el.text or "").strip() != "Status":
                continue
            parent_text = ET.tostring(el, encoding="unicode")
            for match in re.findall(
                r"<field>Status</field>.*?<stringValue>([^<]+)</stringValue>",
                parent_text,
                re.S,
            ):
                record(match.strip(), path.name)
            break
    return refs


def check_quote_status_value_set(root: Path) -> list[str]:
    """api_meta.txt L47481-47483 (omitted values deactivate) and L47538-47541 (allowEmail)."""
    issues: list[str] = []
    files = iter_files(root, "QuoteStatus.standardValueSet-meta.xml")
    referenced = _collect_status_literals(root)

    if not files:
        if referenced:
            for value, sources in sorted(referenced.items()):
                issues.append(
                    f"REVIEW: Status value '{value}' is referenced by "
                    f"{', '.join(sorted(set(sources)))} but QuoteStatus.standardValueSet-meta.xml "
                    "is not in this manifest, so the value cannot be verified. Retrieve "
                    "StandardValueSet:QuoteStatus and include it."
                )
        return issues

    for path in files:
        el = parse_xml(path)
        if isinstance(el, ET.ParseError):
            issues.append(f"ERROR [{path.name}]: not well-formed XML - {el}")
            continue

        values: dict[str, dict[str, str]] = {}
        for sv in find_all(el, "standardValue"):
            name = text_of(sv, "fullName")
            if not name:
                continue
            values[name] = {
                "isActive": text_of(sv, "isActive", default="true").lower(),
                "allowEmail": text_of(sv, "allowEmail").lower(),
            }

        if not values:
            issues.append(
                f"ERROR [{path.name}]: no <standardValue> entries. The guide states the "
                "array must contain at least one picklist value or the deploy errors "
                "(api_meta.txt L130770-130774)."
            )
            continue

        missing = [s for s in STANDARD_QUOTE_STATUSES if s not in values]
        if missing:
            issues.append(
                f"ERROR [{path.name}]: standard Quote statuses omitted: {', '.join(missing)}. "
                "'If picklist values are missing from a component definition, they get "
                "deactivated when deployed' (api_meta.txt L47481-47483). Deploying this file "
                "deactivates those statuses in the target org. Retrieve the full set, edit, "
                "then deploy."
            )

        for value, sources in sorted(referenced.items()):
            if value not in values:
                issues.append(
                    f"ERROR [{path.name}]: Status value '{value}' is referenced by "
                    f"{', '.join(sorted(set(sources)))} but is not defined in this value set. "
                    "The formula or flow will not resolve after deploy."
                )
            elif values[value]["isActive"] == "false":
                issues.append(
                    f"ERROR [{path.name}]: Status value '{value}' is referenced by "
                    f"{', '.join(sorted(set(sources)))} but is marked isActive=false. Users "
                    "can select only active values (api_meta.txt L47500-47506)."
                )

        emailable = sorted(k for k, v in values.items() if v["allowEmail"] == "true")
        if not any(v["allowEmail"] for v in values.values()):
            issues.append(
                f"REVIEW [{path.name}]: no <allowEmail> element on any status. allowEmail is "
                "the platform gate on emailing a quote PDF and 'is only relevant for the "
                "Status field in quotes' (api_meta.txt L47538-47541). Set it explicitly per "
                "status rather than relying on the org's current defaults."
            )
        elif not emailable:
            issues.append(
                f"ERROR [{path.name}]: allowEmail is present but false on every status. No "
                "user will be able to email a quote PDF from any status "
                "(api_meta.txt L47538-47541)."
            )
        elif values.get("Draft", {}).get("allowEmail") == "true":
            issues.append(
                f"REVIEW [{path.name}]: allowEmail is true on 'Draft'. Reps can email an "
                "unreviewed quote PDF to a customer directly from the draft status."
            )
    return issues


# ---------------------------------------------------------------------------
# Check 3 - Quote validation rules reference fields that exist and are legal
# ---------------------------------------------------------------------------

def _quote_custom_fields(root: Path) -> set[str]:
    names: set[str] = set()
    for d in root.rglob("objects/Quote/fields"):
        for f in d.glob("*.field-meta.xml"):
            el = parse_xml(f)
            if isinstance(el, ET.ParseError):
                continue
            full = text_of(el, "fullName") or f.name.split(".")[0]
            names.add(full)
    for f in iter_files(root, "Quote.object-meta.xml"):
        el = parse_xml(f)
        if isinstance(el, ET.ParseError):
            continue
        for fields_el in find_all(el, "fields"):
            full = text_of(fields_el, "fullName")
            if full:
                names.add(full)
    return names


def check_quote_validation_rules(root: Path) -> list[str]:
    """Custom fields referenced by Quote validation rules must ship in the same manifest."""
    issues: list[str] = []
    known = _quote_custom_fields(root)
    custom_ref = re.compile(r"\b([A-Za-z][A-Za-z0-9_]*__c)\b")

    for path in iter_files(root, "*.validationRule-meta.xml"):
        if "Quote" not in str(path):
            continue
        el = parse_xml(path)
        if isinstance(el, ET.ParseError):
            issues.append(f"ERROR [{path.name}]: not well-formed XML - {el}")
            continue

        formula = text_of(el, "errorConditionFormula")
        if not formula:
            issues.append(
                f"ERROR [{path.name}]: errorConditionFormula is empty. It is a Required "
                "field on ValidationRule (api_meta.txt L45376-45378)."
            )

        if find_first(el, "errorMessage") is None and find_first(el, "validationMessage") is not None:
            issues.append(
                f"REVIEW [{path.name}]: uses <validationMessage>. The documented Required "
                "element is <errorMessage> (api_meta.txt L45376-45378); the guide's own "
                "sample XML is inconsistent with its field table. Use errorMessage."
            )

        message = text_of(el, "errorMessage")
        if message and len(message) > 255:
            issues.append(
                f"ERROR [{path.name}]: errorMessage is {len(message)} characters. The guide "
                "caps it at 255 (api_meta.txt L45376-45378)."
            )

        for field in sorted(set(custom_ref.findall(formula))):
            bare = field.split(".")[-1]
            if bare not in known:
                issues.append(
                    f"REVIEW [{path.name}]: formula references custom field '{bare}' which "
                    "is not present under objects/Quote/fields in this manifest. If it does "
                    "not already exist in the target org, the deploy fails."
                )

        for forbidden in sorted(QUOTE_FORMULA_FORBIDDEN):
            if re.search(rf"\b{forbidden}\b", formula):
                issues.append(
                    f"ERROR [{path.name}]: formula references Quote.{forbidden}. The Object "
                    "Reference states it 'is not directly referenceable or usable in custom "
                    "formula fields on the Quote object' and produces 'Error: Field "
                    f"{forbidden} does not exist. Check spelling.' "
                    "(object_reference.txt L239630-239637). Roll up from QuoteLineItem "
                    "instead."
                )
    return issues


# ---------------------------------------------------------------------------
# Check 4 - Flows must not try to write read-only Quote fields
# ---------------------------------------------------------------------------

def check_flow_writes_to_readonly_quote_fields(root: Path) -> list[str]:
    """Object Reference Quote field table: these have neither Create nor Update."""
    issues: list[str] = []

    for path in iter_files(root, "*.flow-meta.xml"):
        el = parse_xml(path)
        if isinstance(el, ET.ParseError):
            issues.append(f"ERROR [{path.name}]: not well-formed XML - {el}")
            continue

        raw = ET.tostring(el, encoding="unicode")
        objects = {(o.text or "").strip() for o in find_all(el, "object")}
        touches_quote = "Quote" in objects or "$Record.Quote" in raw or "Quote." in raw
        if not touches_quote:
            continue

        for node_tag in ("inputAssignments", "recordUpdates", "assignmentItems"):
            for node in find_all(el, node_tag):
                for field_el in find_all(node, "field"):
                    name = (field_el.text or "").strip()
                    if name in QUOTE_READ_ONLY_FIELDS:
                        issues.append(
                            f"ERROR [{path.name}]: {node_tag} assigns to Quote.{name}, which "
                            f"has no Create/Update property ({QUOTE_READ_ONLY_FIELDS[name]}) "
                            "in the Object Reference Quote field table. The write fails or "
                            "is ignored at run time."
                        )
                for ref_el in find_all(node, "assignToReference"):
                    ref = (ref_el.text or "").strip()
                    tail = ref.split(".")[-1]
                    if tail in QUOTE_READ_ONLY_FIELDS and "Quote" in ref:
                        issues.append(
                            f"ERROR [{path.name}]: assignToReference '{ref}' targets the "
                            f"read-only Quote field {tail} "
                            f"({QUOTE_READ_ONLY_FIELDS[tail]})."
                        )

        if re.search(r"<field>Discount</field>", raw) and "Quote" in objects:
            issues.append(
                f"REVIEW [{path.name}]: writes Discount on a Quote-triggered flow. "
                "Quote.Discount is derived and read-only; the editable discount is "
                "QuoteLineItem.Discount (percent, 0-100, Create/Update - "
                "object_reference.txt L240758-240767). Confirm the flow targets the line, "
                "not the header."
            )

        if "SyncedQuoteId" in raw or "SyncedQuoteID" in raw:
            issues.append(
                f"REVIEW [{path.name}]: references Opportunity.SyncedQuoteID. It is 'Read "
                "only in an Apex trigger' (object_reference.txt L192906-192912) and the ID "
                "must belong to a quote that is a child of that opportunity. Verify the "
                "automation context before relying on it to start or stop sync."
            )
    return issues


# ---------------------------------------------------------------------------
# Check 5 - Quote template checklist lint (no metadata type exists; see
#           references/metadata-examples.md section 0)
# ---------------------------------------------------------------------------

def check_quote_template_checklist(root: Path) -> list[str]:
    issues: list[str] = []

    ghost = iter_files(root, "*.quoteTemplate-meta.xml") + iter_files(root, "*.quoteTemplate")
    for path in ghost:
        issues.append(
            f"ERROR [{path.name}]: there is no QuoteTemplate metadata type. The Metadata API "
            "Developer Guide mentions 'QuoteTemplate' only as a SummaryLayoutStyle "
            "enumeration value on Layout (api_meta.txt L83165-83167). This file will never "
            "deploy. Quote templates are Setup-only; track them with a "
            "quote-template-checklist.json instead."
        )

    checklists = [p for p in iter_files(root, "*quote-template-checklist*.json")]
    if not checklists:
        return issues

    for path in checklists:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            issues.append(f"ERROR [{path.name}]: not valid JSON - {exc}")
            continue

        if not isinstance(data, dict):
            issues.append(f"ERROR [{path.name}]: top level must be a JSON object.")
            continue

        for key in CHECKLIST_REQUIRED_TOP:
            if key not in data:
                issues.append(f"ERROR [{path.name}]: missing required key '{key}'.")

        sections = data.get("sections")
        if isinstance(sections, dict):
            for key in CHECKLIST_REQUIRED_SECTIONS:
                if key not in sections:
                    issues.append(
                        f"ERROR [{path.name}]: sections.{key} missing. A quote template has "
                        "Header, Body/line items and Footer; all three must be reviewed."
                    )
            lines = sections.get("line_items")
            if isinstance(lines, dict) and lines.get("sort_field") != "SortOrder":
                issues.append(
                    f"REVIEW [{path.name}]: sections.line_items.sort_field is "
                    f"'{lines.get('sort_field')}'. QuoteLineItem.SortOrder is the field that "
                    "'determines the order in which a quote line item appears in the Quote "
                    "Line Items related list and the Quote PDF' "
                    "(object_reference.txt L241417-241425)."
                )
        elif sections is not None:
            issues.append(f"ERROR [{path.name}]: 'sections' must be an object.")

        verified = data.get("verified_in_org")
        if isinstance(verified, dict):
            for key in CHECKLIST_REQUIRED_VERIFIED:
                if key not in verified:
                    issues.append(f"ERROR [{path.name}]: verified_in_org.{key} missing.")
                elif verified[key] is not True:
                    issues.append(
                        f"REVIEW [{path.name}]: verified_in_org.{key} is not true. The "
                        "template has not been proven end to end in an org."
                    )
            declared = verified.get("statuses_allowing_email")
            if isinstance(declared, list):
                issues.extend(_cross_check_allow_email(root, path, declared))
        elif verified is not None:
            issues.append(f"ERROR [{path.name}]: 'verified_in_org' must be an object.")

        reviewed = data.get("last_reviewed", "")
        if isinstance(reviewed, str) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", reviewed):
            issues.append(
                f"ERROR [{path.name}]: last_reviewed '{reviewed}' is not an ISO YYYY-MM-DD "
                "date."
            )

        for field, value in data.items():
            if isinstance(value, str) and value.startswith("REPLACE ME"):
                issues.append(
                    f"ERROR [{path.name}]: '{field}' still holds the scaffold placeholder."
                )
    return issues


def _cross_check_allow_email(root: Path, checklist: Path, declared: list) -> list[str]:
    issues: list[str] = []
    files = iter_files(root, "QuoteStatus.standardValueSet-meta.xml")
    if not files:
        return issues
    actual: set[str] = set()
    for path in files:
        el = parse_xml(path)
        if isinstance(el, ET.ParseError):
            continue
        for sv in find_all(el, "standardValue"):
            if text_of(sv, "allowEmail").lower() == "true":
                name = text_of(sv, "fullName")
                if name:
                    actual.add(name)
    if not actual:
        return issues
    declared_set = {str(x) for x in declared}
    if declared_set != actual:
        issues.append(
            f"ERROR [{checklist.name}]: verified_in_org.statuses_allowing_email is "
            f"{sorted(declared_set)} but QuoteStatus.standardValueSet-meta.xml sets "
            f"allowEmail=true on {sorted(actual)}. allowEmail is the platform gate on "
            "emailing a quote PDF (api_meta.txt L47538-47541); the checklist and the "
            "deployed value set must agree."
        )
    return issues


# ---------------------------------------------------------------------------
# Check 6 - CPQ coexistence
# ---------------------------------------------------------------------------

def check_cpq_coexistence(root: Path) -> list[str]:
    """Standard quote templates render QuoteLineItem; CPQ lines are SBQQ__QuoteLine__c."""
    issues: list[str] = []
    cpq = sorted({p.name for p in root.rglob("SBQQ__*") if p.is_dir()})
    if not cpq:
        return issues

    standard_quote = has_quote_metadata(root)
    checklists = iter_files(root, "*quote-template-checklist*.json")
    if standard_quote or checklists:
        issues.append(
            "CONFLICT: CPQ (SBQQ) components are present "
            f"({', '.join(cpq[:5])}{'...' if len(cpq) > 5 else ''}) alongside standard Quote "
            f"configuration ({len(standard_quote)} file(s), {len(checklists)} template "
            "checklist(s)). Standard quote templates render QuoteLineItem records; CPQ quote "
            "lines are SBQQ__QuoteLine__c and produce an empty line-item section. Label each "
            "template with the quote type it serves. See admin/cpq-quote-templates."
        )
    return issues


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

CHECKS = (
    ("quote-settings", check_quote_settings),
    ("quote-status-value-set", check_quote_status_value_set),
    ("quote-validation-rules", check_quote_validation_rules),
    ("flow-readonly-writes", check_flow_writes_to_readonly_quote_fields),
    ("quote-template-checklist", check_quote_template_checklist),
    ("cpq-coexistence", check_cpq_coexistence),
)


def run(manifest_dir: Path) -> list[str]:
    if not manifest_dir.exists():
        return [f"ERROR: manifest directory not found: {manifest_dir}"]
    if not manifest_dir.is_dir():
        return [f"ERROR: --manifest-dir must be a directory: {manifest_dir}"]

    issues: list[str] = []
    for _name, fn in CHECKS:
        issues.extend(fn(manifest_dir))
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check standard Salesforce Quotes metadata for deploy-breaking and "
            "silently-ignored configuration. Standard Quotes only; CPQ is out of scope."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source directory, e.g. force-app/main/default.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only ERROR lines; suppress REVIEW and CONFLICT lines.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    issues = run(Path(args.manifest_dir))

    if args.quiet:
        issues = [i for i in issues if i.startswith("ERROR")]

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(issue)

    errors = sum(1 for i in issues if i.startswith("ERROR"))
    print(f"\n{len(issues)} finding(s), {errors} error(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
