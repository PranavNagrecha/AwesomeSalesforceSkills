#!/usr/bin/env python3
"""Lint validation rule metadata for common admin mistakes."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


# `.object` is metadata format (rules embedded in <CustomObject>);
# `.object-meta.xml` and `.validationRule-meta.xml` are DX source format.
METADATA_SUFFIXES = (".object", ".object-meta.xml", ".validationRule-meta.xml")
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

# Metadata API Developer Guide, ValidationRule: "As of API version 20.0,
# validation rules can't have compound fields." Uppercase; matched against the
# uppercased formula text.
COMPOUND_FIELDS = (
    "BILLINGADDRESS",
    "SHIPPINGADDRESS",
    "MAILINGADDRESS",
    "OTHERADDRESS",
    "GEOCODEACCURACY",
)


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def child_text(element: ET.Element, child_name: str) -> str:
    """Text of the first matching child, or "" when the child is absent.

    Deliberately loops instead of `element.find(a) or element.find(b)`:
    a childless ElementTree Element is falsy, so `or` chains on find() silently
    discard real leaf elements such as <active>false</active>.
    """
    for child in element:
        if local_name(child.tag) == child_name:
            return (child.text or "").strip()
    return ""


def has_child(element: ET.Element, child_name: str) -> bool:
    """True when the child element is present, even if it is empty."""
    for child in element:
        if local_name(child.tag) == child_name:
            return True
    return False


@dataclass(frozen=True)
class Rule:
    full_name: str
    active: bool
    formula: str
    error_message: str
    error_display_field: str
    has_error_message_element: bool


def read_rule(element: ET.Element, fallback_name: str) -> Rule:
    return Rule(
        full_name=child_text(element, "fullName") or fallback_name,
        active=child_text(element, "active").lower() == "true",
        formula=child_text(element, "errorConditionFormula"),
        error_message=child_text(element, "errorMessage"),
        error_display_field=child_text(element, "errorDisplayField"),
        has_error_message_element=has_child(element, "errorMessage"),
    )


def iter_metadata_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            for candidate in path.rglob("*"):
                if candidate.is_file() and candidate.name.endswith(METADATA_SUFFIXES):
                    files.append(candidate)
        elif path.is_file() and path.name.endswith(METADATA_SUFFIXES):
            files.append(path)
    return sorted(set(files))


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


BLOCKING_SEVERITIES = {"CRITICAL", "HIGH"}


def emit_result(findings: list[str], summary: str, strict: bool = False) -> int:
    """Print the JSON report and return the exit code.

    Exit 1 only on CRITICAL/HIGH findings (platform facts that will fail or
    misbehave at deploy or run time). MEDIUM/LOW/REVIEW are advisory and exit 0
    so a build that produced correct rules with natural formulas stays green;
    pass --strict to promote every finding to a failure.
    """
    normalized = [normalize_finding(finding) for finding in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    blocking = [item for item in normalized if item["severity"] in BLOCKING_SEVERITIES]
    print(json.dumps({"score": score, "findings": normalized, "summary": summary,
                      "blocking": len(blocking)}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected ({len(blocking)} blocking)", file=sys.stderr)
    if blocking:
        return 1
    return 1 if (strict and normalized) else 0


def collect_rules(path: Path) -> list[Rule]:
    """Read every ValidationRule in a file.

    Two shapes are supported: the metadata-format `.object` file, where rules
    are repeated `<validationRules>` children of `<CustomObject>`, and the DX
    source-format file whose root element is `<ValidationRule>` itself.
    """
    root = ET.parse(path).getroot()
    root_type = local_name(root.tag)
    rules: list[Rule] = []

    if root_type == "ValidationRule":
        rules.append(read_rule(root, fallback_name=path.stem))
        return rules

    if root_type != "CustomObject":
        return rules

    for child in root:
        if local_name(child.tag) == "validationRules":
            rules.append(read_rule(child, fallback_name="<unnamed rule>"))
    return rules


# Metadata API Developer Guide, ValidationRule: "The message must be 255
# characters or less."
ERROR_MESSAGE_MAX = 255


def audit_rule(path: Path, rule: Rule) -> list[str]:
    findings: list[str] = []
    name = rule.full_name
    upper_formula = rule.formula.upper()
    message = rule.error_message
    normalized_error = message.strip().lower()

    # --- errorMessage: required, capped at 255, and useless when generic -----
    if rule.active and not message.strip():
        findings.append(
            f"CRITICAL {path}::{name}: active rule has an empty or missing errorMessage; "
            "errorMessage is a required element and the user sees nothing actionable"
        )
    elif not rule.has_error_message_element:
        findings.append(
            f"HIGH {path}::{name}: no errorMessage element; the deploy will be rejected"
        )

    if len(message) > ERROR_MESSAGE_MAX:
        findings.append(
            f"HIGH {path}::{name}: errorMessage is {len(message)} characters; "
            f"the platform cap is {ERROR_MESSAGE_MAX}"
        )
    elif message.strip() and (len(message.strip()) < 20 or "validation error" in normalized_error):
        findings.append(
            f"MEDIUM {path}::{name}: error message is too generic to act on"
        )

    # --- $Profile.Name gating is an anti-pattern -----------------------------
    if "$PROFILE.NAME" in upper_formula:
        findings.append(
            f"HIGH {path}::{name}: formula gates on $Profile.Name; a renamed profile "
            "silently changes who the rule applies to. Use a Custom Permission"
        )

    if "$USER.ID" in upper_formula or "'005" in rule.formula or '"005' in rule.formula:
        findings.append(
            f"HIGH {path}::{name}: formula appears to reference a hardcoded User Id; "
            "it dies when that person leaves"
        )

    # --- formula correctness -------------------------------------------------
    if "PRIORVALUE(" in upper_formula and "ISNEW()" not in upper_formula:
        findings.append(
            f"HIGH {path}::{name}: PRIORVALUE is used without an ISNEW guard"
        )

    if "ISCHANGED(" in upper_formula and "ISNEW()" not in upper_formula:
        findings.append(
            f"MEDIUM {path}::{name}: ISCHANGED without an ISNEW guard also fires on insert"
        )

    if "RECORDTYPE.NAME" in upper_formula:
        findings.append(
            f"MEDIUM {path}::{name}: uses RecordType.Name; prefer RecordType.DeveloperName"
        )

    if "ISPICKVAL(RECORDTYPE.DEVELOPERNAME" in upper_formula:
        findings.append(
            f"MEDIUM {path}::{name}: RecordType.DeveloperName is text, not a picklist"
        )

    if "ISPICKVAL(" in upper_formula and "ISBLANK(" not in upper_formula:
        findings.append(
            f"REVIEW {path}::{name}: picklist logic has no explicit blank guard"
        )

    # Compound fields are not allowed in validation rules as of API version 20.0
    for compound in COMPOUND_FIELDS:
        if compound in upper_formula:
            findings.append(
                f"HIGH {path}::{name}: references the compound field {compound}; "
                "validation rules can't use compound fields (API 20.0+). "
                "Validate the component fields instead"
            )
            break

    # --- bypass guard --------------------------------------------------------
    # Custom metadata type rules (API 40.0+) fire on the metadata record save,
    # not on business-record DML, so a data-load bypass is not expected there.
    is_custom_metadata_type = "__MDT" in path.name.upper()
    if rule.active and not is_custom_metadata_type and "$PERMISSION." not in upper_formula:
        findings.append(
            f"REVIEW {path}::{name}: no custom-permission bypass detected; confirm data-load and integration strategy"
        )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan ValidationRule metadata for formula, bypass and error-message "
            "issues. Reads both the metadata-format `.object` shape and the DX "
            "source-format `.validationRule-meta.xml` shape."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or directories to scan (equivalent to --manifest-dir for a directory)",
    )
    parser.add_argument(
        "--manifest-dir",
        action="append",
        default=[],
        metavar="DIR",
        help=(
            "Directory to scan recursively, e.g. force-app/main/default/objects. "
            "Repeatable."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on any finding, including MEDIUM/LOW/REVIEW advisories.",
    )
    args = parser.parse_args()

    targets = [Path(value) for value in list(args.paths) + list(args.manifest_dir)]
    if not targets:
        parser.error("provide at least one path or --manifest-dir")

    missing = [str(target) for target in targets if not target.exists()]
    if missing:
        return emit_result(
            [f"HIGH path does not exist: {', '.join(missing)}"],
            f"Scanned 0 file(s); {len(missing)} supplied path(s) do not exist.",
        )

    files = iter_metadata_files(targets)
    if not files:
        return emit_result(
            ["HIGH no validation rule metadata files found"],
            "Scanned 0 validation rule metadata file(s); no files matched the provided paths.",
        )

    findings: list[str] = []
    rule_count = 0
    # fullName -> the files it was seen in. A rule name repeated across two
    # files is either a botched source-format split or two objects fighting
    # over one name in a manifest; both deploy unpredictably.
    seen_names: dict[str, list[str]] = defaultdict(list)

    for path in files:
        try:
            rules = collect_rules(path)
        except ET.ParseError as exc:
            findings.append(f"CRITICAL {path}: file is not well-formed XML ({exc})")
            continue
        for rule in rules:
            rule_count += 1
            seen_names[rule.full_name].append(str(path))
            findings.extend(audit_rule(path, rule))

    for full_name, sources in sorted(seen_names.items()):
        if len(sources) > 1:
            findings.append(
                f"HIGH {full_name}: duplicate rule fullName in {len(sources)} files "
                f"({', '.join(sorted(sources))})"
            )

    summary = (
        f"Scanned {rule_count} validation rule(s) across {len(files)} file(s); "
        f"{len(findings)} finding(s) detected."
    )
    return emit_result(findings, summary, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
