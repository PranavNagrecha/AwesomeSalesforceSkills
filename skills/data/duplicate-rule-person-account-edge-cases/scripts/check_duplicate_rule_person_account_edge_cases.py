#!/usr/bin/env python3
"""
check_duplicate_rule_person_account_edge_cases.py

Static checker for Person-Account-aware Duplicate Rules and Matching Rules.

Scans:
    <root>/objects/Account/duplicateRules/*.duplicateRule-meta.xml
    <root>/matchingRules/*.matchingRule-meta.xml
    (and any nested force-app/.../objects/Account/duplicateRules/... layout)

Findings:

    P0  An Account-targeted matching rule that references a `Contact.*` field.
        Action: rebuild on the Account side using PersonEmail / PersonMobilePhone.

    P0  In a PA-enabled context (the rule references PersonEmail / PersonHomePhone /
        PersonMobilePhone OR a sibling rule does, OR the user passed
        --assume-person-accounts), an Account-targeted matching rule has NO
        `IsPersonAccount` match item.
        Action: add an `IsPersonAccount` Exact match item and gate the boolean filter.

    P1  A phone-typed field (PersonMobilePhone, PersonHomePhone, Phone, OtherPhone,
        MobilePhone, HomePhone) is matched with `matchingMethod = Exact` instead of
        the platform `Phone` method.
        Action: change matchingMethod to `Phone` (strips formatting) or match a
        normalized custom field instead.

    P1  An email-typed field (PersonEmail, Email) is wrapped or replaced by a
        formula reference whose name suggests case normalization
        (`*_Lower__c`, `*Lowercase*`).
        Action: remove the wrapper - Exact on Email is already case-insensitive.

stdlib only. Exits 1 on any P0 or P1 finding, 0 otherwise.

Usage:
    python3 check_duplicate_rule_person_account_edge_cases.py <path> [<path> ...]
    python3 check_duplicate_rule_person_account_edge_cases.py --assume-person-accounts <path>

Each <path> may be a project root, a force-app/main/default directory, an objects
directory, or an individual matchingRules / duplicateRules directory. The scanner
walks them recursively.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from typing import Iterable, List, Tuple

# --- field name patterns -----------------------------------------------------

PHONE_FIELDS = {
    "personmobilephone",
    "personhomephone",
    "phone",
    "otherphone",
    "mobilephone",
    "homephone",
    "fax",
    "assistantphone",
}

EMAIL_FIELDS = {"personemail", "email"}

PERSON_INDICATOR_FIELDS = {"personemail", "personhomephone", "personmobilephone", "ispersonaccount"}

CONTACT_FIELD_PREFIX = re.compile(r"^contact\.", re.IGNORECASE)
LOWERCASE_HINT_RE = re.compile(r"(_lower__c$|lowercase|tolowercase)", re.IGNORECASE)

NAMESPACES = {"sf": "http://soap.sforce.com/2006/04/metadata"}


# --- file discovery ----------------------------------------------------------


def iter_metadata_files(paths: Iterable[str]) -> Iterable[str]:
    """Yield .matchingRule-meta.xml and .duplicateRule-meta.xml files under each path."""
    for raw in paths:
        if not os.path.exists(raw):
            print(f"WARN: skipping missing path: {raw}", file=sys.stderr)
            continue
        if os.path.isfile(raw):
            if raw.endswith(".matchingRule-meta.xml") or raw.endswith(".duplicateRule-meta.xml"):
                yield raw
            continue
        for root, _dirs, files in os.walk(raw):
            for name in files:
                if name.endswith(".matchingRule-meta.xml") or name.endswith(".duplicateRule-meta.xml"):
                    yield os.path.join(root, name)


# --- xml parsing helpers -----------------------------------------------------


def _parse(path: str):
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        return exc


def _local(tag: str) -> str:
    """Strip XML namespace from a tag name."""
    return tag.split("}", 1)[1] if "}" in tag else tag


def _children_local(elem, name: str):
    return [c for c in elem if _local(c.tag) == name]


def _text(elem, name: str) -> str:
    """Return the trimmed text of the first child with given local name, or ''."""
    for c in elem:
        if _local(c.tag) == name:
            return (c.text or "").strip()
    return ""


def _is_account_matching_rule(path: str, root_elem) -> bool:
    """A matching rule is Account-targeted when its filename or fullName starts with 'Account.'."""
    base = os.path.basename(path)
    if base.startswith("Account."):
        return True
    full = root_elem.attrib.get("fullName", "") if root_elem is not None else ""
    return full.startswith("Account.")


# --- per-file analysis -------------------------------------------------------


def analyse_matching_rule(path: str, root_elem, assume_pa: bool) -> List[Tuple[str, str]]:
    findings: List[Tuple[str, str]] = []
    if not _is_account_matching_rule(path, root_elem):
        return findings  # only Account-targeted rules are in scope for PA gotchas

    items = _children_local(root_elem, "matchingRuleItems")
    if not items:
        return findings

    field_names = []
    for item in items:
        fn = _text(item, "fieldName")
        method = _text(item, "matchingMethod")
        field_names.append(fn)

        # P0 - Contact.* referenced from an Account rule
        if CONTACT_FIELD_PREFIX.match(fn):
            findings.append((
                "P0",
                f"{path}: matching rule references '{fn}'. Account-targeted matching rules "
                f"cannot resolve Contact.* fields - use PersonEmail / PersonMobilePhone on Account.",
            ))

        # P1 - phone field with Exact instead of Phone matching method
        if fn.lower() in PHONE_FIELDS and method.lower() == "exact":
            findings.append((
                "P1",
                f"{path}: field '{fn}' matched with method 'Exact'. Phone fields should use "
                f"matchingMethod 'Phone' (strips formatting and country-code variants), or match "
                f"a normalized custom field.",
            ))

        # P1 - email-suggesting formula field with case-normalization hint
        if LOWERCASE_HINT_RE.search(fn):
            findings.append((
                "P1",
                f"{path}: field '{fn}' looks like a hand-rolled lowercase normalization. "
                f"Email matching with method 'Exact' on an Email-type field is already "
                f"case-insensitive; remove the LOWER() wrapper / formula field.",
            ))

    # P0 - PA-enabled context but no IsPersonAccount gate
    lower_fields = {f.lower() for f in field_names}
    references_person_field = bool(PERSON_INDICATOR_FIELDS & lower_fields - {"ispersonaccount"})
    pa_context = assume_pa or references_person_field
    has_ispa_gate = "ispersonaccount" in lower_fields
    if pa_context and not has_ispa_gate:
        findings.append((
            "P0",
            f"{path}: Account-targeted matching rule appears to be PA-aware (references "
            f"{sorted(PERSON_INDICATOR_FIELDS & lower_fields) or '[--assume-person-accounts]'}) "
            f"but has no `IsPersonAccount` match item. Add an Exact match on `IsPersonAccount` "
            f"and gate the booleanFilter to prevent cross-universe matching with B2B records.",
        ))

    return findings


def analyse_duplicate_rule(path: str, root_elem) -> List[Tuple[str, str]]:
    """Light checks on duplicate rules: surface stale or inactive PA-targeted rules,
    and warn when a Lead-targeted rule has no Account-side cross-object match in a PA context."""
    findings: List[Tuple[str, str]] = []
    is_active = _text(root_elem, "isActive").lower() == "true"
    full = root_elem.attrib.get("fullName", "") or os.path.basename(path)

    # If the duplicate rule is Account-targeted AND inactive, that is suspicious in a PA-enabled deploy.
    base = os.path.basename(path)
    if base.startswith("Account.") and not is_active:
        findings.append((
            "P1",
            f"{path}: Account-targeted Duplicate Rule '{full}' is inactive. "
            f"On a PA-enabled org, the Account-targeted rule is what fires on lead-convert; "
            f"confirm this is intentional.",
        ))
    return findings


def analyse(path: str, assume_pa: bool) -> List[Tuple[str, str]]:
    parsed = _parse(path)
    if isinstance(parsed, ET.ParseError):
        return [("P0", f"{path}: XML parse error ({parsed})")]
    if path.endswith(".matchingRule-meta.xml"):
        return analyse_matching_rule(path, parsed, assume_pa)
    if path.endswith(".duplicateRule-meta.xml"):
        return analyse_duplicate_rule(path, parsed)
    return []


# --- entry point -------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Person-Account-aware Duplicate / Matching rules for common defects.",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Project roots, force-app dirs, or individual matching/duplicate rule files.",
    )
    parser.add_argument(
        "--assume-person-accounts",
        action="store_true",
        help="Treat the org as PA-enabled even if individual rules don't reference Person fields. "
        "Use this for B2C orgs where every Account-targeted rule must be PA-aware.",
    )
    return parser.parse_args()


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    args = parse_args()

    files = list(iter_metadata_files(args.paths))
    if not files:
        print("No matchingRule-meta.xml / duplicateRule-meta.xml files found.", file=sys.stderr)
        return 0

    all_findings: List[Tuple[str, str]] = []
    for path in files:
        all_findings.extend(analyse(path, args.assume_person_accounts))

    if not all_findings:
        print(f"OK - scanned {len(files)} rule file(s); no PA edge-case violations found.")
        return 0

    p0 = [f for f in all_findings if f[0] == "P0"]
    p1 = [f for f in all_findings if f[0] == "P1"]

    for severity, message in all_findings:
        print(f"[{severity}] {message}")

    print("")
    print(f"Summary: {len(p0)} P0, {len(p1)} P1, scanned {len(files)} file(s).")

    return 1 if (p0 or p1) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
