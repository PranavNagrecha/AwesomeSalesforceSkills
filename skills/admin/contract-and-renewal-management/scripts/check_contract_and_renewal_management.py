#!/usr/bin/env python3
"""Checker script for the Contract and Renewal Management skill.

Lints the metadata this skill produces, in two layers:

Standard Contract / Order metadata (grounded in the Metadata API Developer Guide
and the Object Reference):
  1. Contract.settings and Order.settings parse, and contain only elements the
     Metadata API Developer Guide documents for their type.
  2. Order settings dependencies hold: enableNegativeQuantity, enableReductionOrders
     and enableZeroQuantity each require enableOrders; enableOrderWithMultiplePriceBooks
     additionally requires enableEnhancedCommerceOrders. Order metadata (objects,
     value set, fields) is only meaningful when enableOrders is true.
  3. The ContractStatus standard value set contains at least one Activated-category
     value, and every Activated-category label is named by any Contract validation
     rule that gates activation.
  4. Contract validation rules reference only fields that exist — standard Contract
     fields, or custom fields present in the manifest.
  5. Renewal / expiry SOQL embedded in Flows or Apex filters on EndDate rather than
     on a formula field, and prefers StatusCode over the Status label.

CPQ metadata (managed package; not covered by any platform guide):
  6. Product2 and Contract carry the CPQ fields the lifecycle needs.
  7. No Flow or Apex writes SBQQ__Subscription__c directly.

Uses stdlib only -- no pip dependencies.

Usage:
    python3 check_contract_and_renewal_management.py --help
    python3 check_contract_and_renewal_management.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = "http://soap.sforce.com/2006/04/metadata"


# --------------------------------------------------------------------------
# Documented element names.
#
# ContractSettings: api_meta.txt L113225-L113231 documents exactly two fields.
# OrderSettings:    api_meta.txt L123660-L123705 documents eight.
# Anything else in these files is a deploy failure, so flag it here instead.
# --------------------------------------------------------------------------
CONTRACT_SETTINGS_ELEMENTS = {
    "autoCalculateEndDate",
    "notifyOwnersOnContractExpiration",
}

ORDER_SETTINGS_ELEMENTS = {
    "enableEnhancedCommerceOrders",
    "enableNegativeQuantity",
    "enableOptionalPricebook",
    "enableOrderEvents",
    "enableOrders",
    "enableOrderWithMultiplePriceBooks",
    "enableReductionOrders",
    "enableZeroQuantity",
}

# Each key requires every flag in its value to be true as well.
ORDER_SETTINGS_DEPENDENCIES = {
    "enableNegativeQuantity": ("enableOrders",),
    "enableReductionOrders": ("enableOrders",),
    "enableZeroQuantity": ("enableOrders",),
    "enableOrderWithMultiplePriceBooks": ("enableOrders", "enableEnhancedCommerceOrders"),
}

# Contract.StatusCode valid values (object_reference.txt L81487-L81490).
CONTRACT_STATUS_CATEGORIES = {"Draft", "InApproval", "Activated"}

# Contract.Status out-of-the-box labels (object_reference.txt L81478-L81481) and
# the status category each one belongs to. Custom labels are org-specific, so the
# checker infers their category from the label text and says so when it guesses.
STANDARD_CONTRACT_STATUS_LABELS = {
    "Draft": "Draft",
    "In Approval Process": "InApproval",
    "Activated": "Activated",
}

# Standard Contract fields a validation rule may reference without the field
# appearing in the manifest (object_reference.txt L80851-L81529). Not exhaustive
# for address and system fields; those are added below.
STANDARD_CONTRACT_FIELDS = {
    "AccountId", "ActivatedById", "ActivatedDate", "BillingCity", "BillingCountry",
    "BillingPostalCode", "BillingState", "BillingStreet", "CompanySignedDate",
    "CompanySignedId", "ContractNumber", "ContractTerm", "CreatedById",
    "CreatedDate", "CurrencyIsoCode", "CustomerSignedDate", "CustomerSignedId",
    "CustomerSignedTitle", "Description", "EndDate", "Id", "IsDeleted",
    "LastActivityDate", "LastApprovedDate", "LastModifiedById", "LastModifiedDate",
    "Name", "OwnerExpirationNotice", "OwnerId", "Pricebook2Id", "PricingSource",
    "RecordTypeId", "RenewalTerm2", "RenewalTermUnit", "ShippingCity",
    "ShippingCountry", "ShippingPostalCode", "ShippingState", "ShippingStreet",
    "SpecialTerms", "StartDate", "Status", "StatusCode", "SystemModstamp",
}

# Formula functions and globals that look like field references but are not.
FORMULA_NOISE = {
    "AND", "OR", "NOT", "IF", "ISBLANK", "ISNULL", "ISPICKVAL", "ISCHANGED",
    "ISNEW", "PRIORVALUE", "TEXT", "VALUE", "CASE", "BLANKVALUE", "NULLVALUE",
    "TODAY", "NOW", "DATE", "DATEVALUE", "BEGINS", "CONTAINS", "INCLUDES",
    "LEN", "TRIM", "UPPER", "LOWER", "ABS", "FLOOR", "CEILING", "ROUND",
    "MOD", "MAX", "MIN", "TRUE", "FALSE", "NULL", "YEAR", "MONTH", "DAY",
    "ADDMONTHS", "REGEX", "HYPERLINK", "IMAGE", "VLOOKUP",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint Contract and Order metadata for the failures described in "
            "skills/admin/contract-and-renewal-management/references/gotchas.md."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# --------------------------------------------------------------------------
# XML helpers.
#
# NEVER write `elem.find(a) or elem.find(b)`: an Element with no children is
# falsy, so a found-but-empty element is discarded. Always test `is not None`.
# --------------------------------------------------------------------------
def _parse_xml_safe(path: Path) -> tuple[ET.Element | None, str | None]:
    """Parse an XML file. Returns (root, error_message)."""
    try:
        return ET.parse(path).getroot(), None
    except ET.ParseError as exc:
        return None, str(exc)
    except OSError as exc:  # pragma: no cover - unreadable file
        return None, str(exc)


def _local(tag: str) -> str:
    """Strip an XML namespace from a tag name."""
    return tag.split("}", 1)[1] if "}" in tag else tag


def _find(elem: ET.Element, name: str) -> ET.Element | None:
    """Namespace-tolerant single-child lookup that is safe on empty elements."""
    child = elem.find(f"{{{MD_NS}}}{name}")
    if child is None:
        child = elem.find(name)
    return child


def _findall(elem: ET.Element, name: str) -> list[ET.Element]:
    """Namespace-tolerant descendant lookup."""
    found = elem.findall(f".//{{{MD_NS}}}{name}")
    if not found:
        found = elem.findall(f".//{name}")
    return found


def _text(elem: ET.Element | None) -> str:
    if elem is None or elem.text is None:
        return ""
    return elem.text.strip()


def _flag(root: ET.Element, name: str) -> bool | None:
    """Read a boolean settings element. None when the element is absent."""
    child = _find(root, name)
    if child is None:
        return None
    return _text(child).lower() == "true"


# --------------------------------------------------------------------------
# Check 1 + 2: settings files parse and use only documented elements.
# --------------------------------------------------------------------------
def check_settings_files(manifest_dir: Path) -> tuple[list[str], bool]:
    """Validate Contract.settings and Order.settings.

    Returns (issues, orders_enabled).
    """
    issues: list[str] = []
    orders_enabled = False
    settings_dir = manifest_dir / "settings"
    if not settings_dir.exists():
        return issues, orders_enabled

    specs = [
        ("Contract.settings-meta.xml", "ContractSettings", CONTRACT_SETTINGS_ELEMENTS),
        ("Order.settings-meta.xml", "OrderSettings", ORDER_SETTINGS_ELEMENTS),
    ]

    for filename, type_name, documented in specs:
        path = settings_dir / filename
        if not path.exists():
            continue

        root, error = _parse_xml_safe(path)
        if root is None:
            issues.append(f"{path}: not well-formed XML ({error}). The deploy will fail before it reaches the org.")
            continue

        if _local(root.tag) != type_name:
            issues.append(
                f"{path}: root element is <{_local(root.tag)}>, expected <{type_name}>. "
                f"The file name decides which settings component this is, so the root element must agree with it."
            )
            continue

        for child in root:
            name = _local(child.tag)
            if name not in documented:
                issues.append(
                    f"{path}: <{name}> is not a documented {type_name} element. "
                    f"The Metadata API Developer Guide documents only: {', '.join(sorted(documented))}. "
                    f"An undocumented element fails the deploy with no partial success."
                )

        if type_name == "OrderSettings":
            values = {_local(c.tag): _text(c).lower() == "true" for c in root}
            orders_enabled = values.get("enableOrders", False)
            for flag, parents in ORDER_SETTINGS_DEPENDENCIES.items():
                if not values.get(flag, False):
                    continue
                for parent in parents:
                    if not values.get(parent, False):
                        issues.append(
                            f"{path}: <{flag}>true</{flag}> requires <{parent}>true</{parent}>, "
                            f"which is {'false' if parent in values else 'absent'}. "
                            f"The guide states this dependency explicitly; the deploy fails on it."
                        )
            if values.get("enableOptionalPricebook", False) and values.get("enableReductionOrders", False):
                issues.append(
                    f"{path}: enableOptionalPricebook and enableReductionOrders are both true. "
                    "Orders without price books do not support reduction orders or change orders "
                    "(Object Reference, Order, 'Orders Without Price Books'), so one of these two "
                    "features will not work in this org."
                )

    return issues, orders_enabled


# --------------------------------------------------------------------------
# Check 2b: Order metadata only makes sense when enableOrders is true.
# --------------------------------------------------------------------------
def check_order_metadata_gated(manifest_dir: Path, orders_enabled: bool) -> list[str]:
    issues: list[str] = []
    settings_path = manifest_dir / "settings" / "Order.settings-meta.xml"

    order_artifacts: list[Path] = []
    objects_dir = manifest_dir / "objects"
    for name in ("Order", "OrderItem"):
        candidate = objects_dir / name
        if candidate.exists():
            order_artifacts.append(candidate)
        flat = objects_dir / f"{name}.object-meta.xml"
        if flat.exists():
            order_artifacts.append(flat)

    svs = manifest_dir / "standardValueSets" / "OrderStatus.standardValueSet-meta.xml"
    if svs.exists():
        order_artifacts.append(svs)

    if order_artifacts and not orders_enabled:
        listed = ", ".join(str(p.relative_to(manifest_dir)) for p in order_artifacts)
        if settings_path.exists():
            issues.append(
                f"Order metadata is in the manifest ({listed}) but Order.settings has enableOrders false or absent. "
                "Deploy the settings with enableOrders true first, or the Order components resolve against a "
                "feature the org does not have."
            )
        else:
            issues.append(
                f"Order metadata is in the manifest ({listed}) but no settings/Order.settings-meta.xml is. "
                "Include it so the deploy is self-contained and enableOrders is not left to org state."
            )

    return issues


# --------------------------------------------------------------------------
# Check 3: ContractStatus value set has an Activated-category value.
# --------------------------------------------------------------------------
def _contract_status_labels(manifest_dir: Path) -> tuple[list[str], list[str]]:
    """Return (all labels, labels judged to be in the Activated category)."""
    path = manifest_dir / "standardValueSets" / "ContractStatus.standardValueSet-meta.xml"
    if not path.exists():
        return [], []

    root, _ = _parse_xml_safe(path)
    if root is None:
        return [], []

    labels: list[str] = []
    activated: list[str] = []
    for value in _findall(root, "standardValue"):
        full_name = _text(_find(value, "fullName"))
        if not full_name:
            continue
        labels.append(full_name)
        description = _text(_find(value, "description"))
        category = STANDARD_CONTRACT_STATUS_LABELS.get(full_name)
        if category is None:
            # Custom label: the value set carries no category element, so fall
            # back to the description, then to the label text.
            haystack = f"{description} {full_name}".lower()
            if "activated" in haystack:
                category = "Activated"
        if category == "Activated":
            activated.append(full_name)
    return labels, activated


def check_contract_status_value_set(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    path = manifest_dir / "standardValueSets" / "ContractStatus.standardValueSet-meta.xml"
    if not path.exists():
        return issues

    root, error = _parse_xml_safe(path)
    if root is None:
        issues.append(f"{path}: not well-formed XML ({error}).")
        return issues

    labels, activated = _contract_status_labels(manifest_dir)

    if not labels:
        issues.append(
            f"{path}: no <standardValue> entries. A StandardValueSet deploy must contain at least one "
            "picklist value or the deploy errors, and every value omitted from the file is deactivated in the org."
        )
        return issues

    if not activated:
        issues.append(
            f"{path}: no value belongs to the Activated status category. Contract.StatusCode is read-only, "
            "so the only way a contract can reach the Activated category is through a Status label that sits in it. "
            "Include 'Activated', or give the custom label a <description> naming its Activated category."
        )

    return issues


# --------------------------------------------------------------------------
# Check 3b + 4: Contract validation rules.
# --------------------------------------------------------------------------
def _manifest_contract_fields(manifest_dir: Path) -> set[str]:
    fields_dir = manifest_dir / "objects" / "Contract" / "fields"
    if not fields_dir.exists():
        return set()
    return {p.name.split(".")[0] for p in fields_dir.glob("*.field-meta.xml")}


def check_contract_validation_rules(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    rules_dir = manifest_dir / "objects" / "Contract" / "validationRules"
    if not rules_dir.exists():
        return issues

    known_fields = STANDARD_CONTRACT_FIELDS | _manifest_contract_fields(manifest_dir)
    _, activated_labels = _contract_status_labels(manifest_dir)

    for rule_file in sorted(rules_dir.glob("*.validationRule-meta.xml")):
        root, error = _parse_xml_safe(rule_file)
        if root is None:
            issues.append(f"{rule_file}: not well-formed XML ({error}).")
            continue

        formula = _text(_find(root, "errorConditionFormula"))
        if not formula:
            issues.append(
                f"{rule_file}: errorConditionFormula is empty or missing. It is a required "
                "ValidationRule field; the deploy fails without it."
            )
            continue

        if _find(root, "errorMessage") is None:
            extra = ""
            if _find(root, "validationMessage") is not None:
                extra = (
                    " The file uses <validationMessage>, which appears in the guide's inline CustomObject "
                    "sample; a standalone .validationRule-meta.xml needs <errorMessage>."
                )
            issues.append(f"{rule_file}: no <errorMessage>. It is a required ValidationRule field.{extra}")

        # Field references: bare identifiers, and X__c custom fields.
        referenced = set(re.findall(r"\b([A-Za-z][A-Za-z0-9_]*)\b", formula))
        # Drop quoted literals so picklist API names are not read as fields.
        for literal in re.findall(r"[\"']([^\"']*)[\"']", formula):
            referenced -= set(re.findall(r"\b([A-Za-z][A-Za-z0-9_]*)\b", literal))
        for name in sorted(referenced):
            if name.upper() in FORMULA_NOISE or name in FORMULA_NOISE:
                continue
            if name in known_fields:
                continue
            if name.endswith("__c") or name.endswith("__r"):
                issues.append(
                    f"{rule_file}: formula references custom field '{name}', which has no "
                    f"objects/Contract/fields/{name}.field-meta.xml in this manifest. "
                    "Deploy the field in the same package or the rule fails to compile."
                )
            elif name[0].isupper():
                issues.append(
                    f"{rule_file}: formula references '{name}', which is neither a standard Contract "
                    "field known to this checker nor a custom field in the manifest. Confirm the API name."
                )

        # Activation gates must name every Activated-category label.
        if "ISPICKVAL" in formula.upper() and "Status" in formula:
            named = set(re.findall(r"ISPICKVAL\s*\(\s*Status\s*,\s*[\"']([^\"']+)[\"']", formula))
            for label in activated_labels:
                if label not in named:
                    issues.append(
                        f"{rule_file}: the formula tests Status with ISPICKVAL but never names the "
                        f"Activated-category label '{label}' from ContractStatus.standardValueSet-meta.xml. "
                        "A contract activated under that label bypasses this rule entirely."
                    )

    return issues


# --------------------------------------------------------------------------
# Check 5: renewal / expiry queries.
# --------------------------------------------------------------------------
_QUERY_HINT = re.compile(r"FROM\s+Contract\b", re.IGNORECASE)


def _lint_contract_query(source: str, where: str) -> list[str]:
    """Flag renewal/expiry queries over Contract that filter on the wrong things."""
    issues: list[str] = []
    lowered = source.lower()

    renewal_context = any(word in lowered for word in ("renew", "expir", "enddate", "days_to_expiry"))
    if not renewal_context:
        return issues

    # Only the filter matters: EndDate in the SELECT list proves nothing.
    filters = " ".join(
        m.group(1) for m in re.finditer(
            r"\bwhere\b(.*?)(?:\bgroup\s+by\b|\border\s+by\b|\blimit\b|\]|$)",
            lowered, re.DOTALL,
        )
    )
    haystack = filters if filters.strip() else lowered
    if "enddate" not in haystack:
        issues.append(
            f"{where}: a renewal or expiry query over Contract whose filter does not mention EndDate. "
            "EndDate is the calculated contract end date and the only indexed date the renewal window can key on."
        )

    if "days_to_expiry__c" in haystack:
        issues.append(
            f"{where}: filters on Days_To_Expiry__c. That is a formula field — it is not indexed, so a "
            "daily scheduled job filtered on it scans the whole Contract table. Filter on EndDate instead."
        )

    if re.search(r"status\s*=\s*'activated'", haystack) and "statuscode" not in haystack:
        issues.append(
            f"{where}: filters on Status = 'Activated' rather than StatusCode = 'Activated'. "
            "Status is a label; any Activated-category label an admin adds later will silently drop "
            "those contracts out of this query."
        )

    return issues


def check_renewal_queries(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    for flow_file in sorted((manifest_dir / "flows").glob("*.flow-meta.xml")) if (manifest_dir / "flows").exists() else []:
        root, _ = _parse_xml_safe(flow_file)
        if root is None:
            continue
        blob_parts: list[str] = []
        for elem in root.iter():
            if elem.text:
                blob_parts.append(elem.text)
        blob = " ".join(blob_parts)
        if "Contract" in blob and any(w in blob.lower() for w in ("renew", "expir")):
            issues.extend(_lint_contract_query(blob, f"Flow '{flow_file.stem}'"))

    classes_dir = manifest_dir / "classes"
    if classes_dir.exists():
        for apex_file in sorted(classes_dir.glob("*.cls")):
            content = apex_file.read_text(encoding="utf-8", errors="replace")
            if not _QUERY_HINT.search(content):
                continue
            issues.extend(_lint_contract_query(content, f"Apex class '{apex_file.stem}'"))

    return issues


# --------------------------------------------------------------------------
# Check 6 + 7: CPQ layer.
# --------------------------------------------------------------------------
def check_subscription_fields_on_product(manifest_dir: Path) -> list[str]:
    """Product2 must carry the CPQ fields that make contract creation produce subscriptions."""
    issues: list[str] = []
    fields_dir = manifest_dir / "objects" / "Product2" / "fields"
    if not fields_dir.exists():
        return issues

    existing = {p.name.split(".")[0] for p in fields_dir.glob("*.field-meta.xml")}
    if not any(name.startswith("SBQQ__") for name in existing):
        # Not a CPQ manifest; nothing to say.
        return issues

    for field in sorted({"SBQQ__SubscriptionPricing__c", "SBQQ__SubscriptionType__c"} - existing):
        issues.append(
            f"Product2 is missing CPQ field {field}. Without it, CPQ contract creation will not "
            "generate SBQQ__Subscription__c records and the Amend and Renew buttons never appear."
        )
    return issues


def check_contract_object_for_cpq_fields(manifest_dir: Path) -> list[str]:
    """Contract must carry the CPQ renewal fields when the manifest is a CPQ manifest."""
    issues: list[str] = []
    fields_dir = manifest_dir / "objects" / "Contract" / "fields"
    if not fields_dir.exists():
        return issues

    existing = {p.name.split(".")[0] for p in fields_dir.glob("*.field-meta.xml")}
    if not any(name.startswith("SBQQ__") for name in existing):
        return issues

    key_fields = {
        "SBQQ__DefaultRenewalTerm__c",
        "SBQQ__RenewedContract__c",
        "SBQQ__RenewalQuoted__c",
    }
    for field in sorted(key_fields - existing):
        issues.append(
            f"Contract is missing CPQ field {field}. The CPQ renewal lifecycle reads it; without it, "
            "renewal quote generation or contract-history chaining breaks."
        )
    return issues


def check_flows_for_direct_subscription_edits(manifest_dir: Path) -> list[str]:
    """Flag Flow record updates that write SBQQ__Subscription__c directly."""
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    if not flows_dir.exists():
        return issues

    for flow_file in sorted(flows_dir.glob("*.flow-meta.xml")):
        root, _ = _parse_xml_safe(flow_file)
        if root is None:
            continue

        for tag in ("recordUpdates", "recordDeletes", "recordCreates"):
            for node in _findall(root, tag):
                object_elem = _find(node, "object")
                if object_elem is not None and _text(object_elem) == "SBQQ__Subscription__c":
                    issues.append(
                        f"Flow '{flow_file.stem}' has a {tag} element targeting SBQQ__Subscription__c. "
                        "Writing subscription records outside the CPQ amendment flow bypasses proration, "
                        "co-termination and approval routing, and leaves renewal generation reading "
                        "inconsistent data."
                    )

    return issues


def check_apex_for_direct_subscription_edits(manifest_dir: Path) -> list[str]:
    """Flag DML on SBQQ__Subscription__c in non-test Apex."""
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.exists():
        return issues

    dml = re.compile(
        r"\b(?:insert|update|upsert|delete)\s+\w+|Database\.(?:insert|update|upsert|delete)\s*\(",
        re.IGNORECASE,
    )

    for apex_file in sorted(classes_dir.glob("*.cls")):
        content = apex_file.read_text(encoding="utf-8", errors="replace")
        if "@istest" in content.lower() or "testmethod" in content.lower():
            continue
        if "sbqq__subscription__c" not in content.lower():
            continue
        if dml.search(content):
            issues.append(
                f"Apex class '{apex_file.stem}' references SBQQ__Subscription__c and performs DML. "
                "Direct writes to CPQ subscription records outside the amendment API corrupt contract "
                "and renewal state. Route the change through SBQQ.ContractManipulationAPI or an "
                "Amendment Quote."
            )

    return issues


# --------------------------------------------------------------------------
def check_contract_and_renewal_management(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    issues: list[str] = []
    settings_issues, orders_enabled = check_settings_files(manifest_dir)
    issues.extend(settings_issues)
    issues.extend(check_order_metadata_gated(manifest_dir, orders_enabled))
    issues.extend(check_contract_status_value_set(manifest_dir))
    issues.extend(check_contract_validation_rules(manifest_dir))
    issues.extend(check_renewal_queries(manifest_dir))
    issues.extend(check_subscription_fields_on_product(manifest_dir))
    issues.extend(check_contract_object_for_cpq_fields(manifest_dir))
    issues.extend(check_flows_for_direct_subscription_edits(manifest_dir))
    issues.extend(check_apex_for_direct_subscription_edits(manifest_dir))
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_contract_and_renewal_management(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
