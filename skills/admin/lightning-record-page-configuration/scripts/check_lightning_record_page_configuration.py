#!/usr/bin/env python3
"""Checker for Lightning record page configuration and assignment.

The single most common failure in this domain is a Lightning page that is
perfectly built, successfully deployed, and pointed at by nothing. A FlexiPage
carries no assignment: the org default lives in an ``<actionOverrides>`` block
on the object's CustomObject metadata, and the app default and the
app + record type + profile rows live in ``<actionOverrides>`` and
``<profileActionOverrides>`` on each CustomApplication. Ship the flexipages
folder on its own and the deploy goes green while nothing a user sees changes.

This script reads a Salesforce source tree and reports:

  ERROR  a RecordPage FlexiPage that no override in the tree points at
  ERROR  a region holding more than 100 components (platform maximum)
  ERROR  a componentInstance / fieldInstance with no identifier
         (required from API 53.0) or an identifier over 120 characters
  ERROR  the pre-API-49.0 <componentInstances> region shape
  ERROR  a visibilityRule operator outside the documented enum
  ERROR  a {!Record.*} visibility expression on a page with no record context
  WARN   an override whose <content> names a page not present in the tree

Exit code is 1 when any ERROR is found, 0 otherwise.

Stdlib only. Python 3.8+.

Usage:
    python3 check_lightning_record_page_configuration.py --help
    python3 check_lightning_record_page_configuration.py --manifest-dir force-app/main/default
    python3 check_lightning_record_page_configuration.py --manifest-dir . --strict
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Metadata API Developer Guide -- FlexiPage.
MAX_COMPONENTS_PER_REGION = 100
MAX_IDENTIFIER_CHARS = 120
VALID_OPERATORS = {"EQUAL", "NE", "CONTAINS", "GT", "GE", "LT", "LE"}

# Page types that have a record in context, so {!Record.*} is legal on them.
RECORD_CONTEXT_TYPES = {
    "RecordPage",
    "RecordPreview",
    "CommRecordPage",
    "CdpRecordPage",
    "CommObjectPage",
}

# Only RecordPage needs an override in this tree to be reachable. App pages and
# Home pages are reached through app navigation, which this check does not model.
ASSIGNMENT_REQUIRED_TYPES = {"RecordPage"}

RECORD_EXPR = re.compile(r"\{!\s*Record\.", re.IGNORECASE)


class Finding:
    def __init__(self, severity: str, where: str, message: str) -> None:
        self.severity = severity
        self.where = where
        self.message = message

    def __str__(self) -> str:
        return "{}: {}: {}".format(self.severity, self.where, self.message)


def strip_ns(tag: str) -> str:
    """``{http://soap.sforce.com/2006/04/metadata}type`` -> ``type``."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def parse(path: Path) -> Tuple[ET.Element, List[Finding]]:
    try:
        return ET.parse(str(path)).getroot(), []
    except ET.ParseError as exc:
        return ET.Element("unparsed"), [
            Finding("ERROR", str(path), "not well-formed XML: {}".format(exc))
        ]


def child_text(node: ET.Element, name: str) -> str:
    for kid in node:
        if strip_ns(kid.tag) == name:
            return (kid.text or "").strip()
    return ""


def children(node: ET.Element, name: str) -> List[ET.Element]:
    return [kid for kid in node if strip_ns(kid.tag) == name]


def descendants(node: ET.Element, name: str) -> List[ET.Element]:
    return [kid for kid in node.iter() if strip_ns(kid.tag) == name]


# --------------------------------------------------------------------------- #
# Assignment side: who points at which page.
# --------------------------------------------------------------------------- #

def collect_assignments(root_dir: Path) -> Tuple[Dict[str, List[str]], List[Finding]]:
    """Map FlexiPage developer name -> list of human-readable override sources."""
    assignments: Dict[str, List[str]] = {}
    findings: List[Finding] = []

    object_files = list(root_dir.glob("objects/*/*.object-meta.xml"))
    object_files += list(root_dir.glob("objects/*.object"))
    app_files = list(root_dir.glob("applications/*.app-meta.xml"))
    app_files += list(root_dir.glob("applications/*.app"))

    for path in sorted(object_files):
        root, errs = parse(path)
        findings.extend(errs)
        for override in descendants(root, "actionOverrides"):
            if child_text(override, "type").lower() != "flexipage":
                continue
            content = child_text(override, "content")
            if content:
                label = "org default ({}, formFactor={})".format(
                    path.name, child_text(override, "formFactor") or "none/Classic"
                )
                assignments.setdefault(content, []).append(label)

    for path in sorted(app_files):
        root, errs = parse(path)
        findings.extend(errs)
        for override in descendants(root, "actionOverrides"):
            content = child_text(override, "content")
            if content:
                assignments.setdefault(content, []).append(
                    "app default ({})".format(path.name)
                )
        for override in descendants(root, "profileActionOverrides"):
            content = child_text(override, "content")
            if content:
                assignments.setdefault(content, []).append(
                    "app+recordType+profile ({}, profile={}, recordType={})".format(
                        path.name,
                        child_text(override, "profile") or "-",
                        child_text(override, "recordType") or "-",
                    )
                )

    return assignments, findings


# --------------------------------------------------------------------------- #
# Page side: shape and content of each .flexipage file.
# --------------------------------------------------------------------------- #

def check_visibility_rule(
    rule: ET.Element, where: str, owner: str, page_type: str
) -> List[Finding]:
    findings: List[Finding] = []
    for criterion in children(rule, "criteria"):
        operator = child_text(criterion, "operator")
        if operator and operator not in VALID_OPERATORS:
            findings.append(
                Finding(
                    "ERROR",
                    where,
                    "{}: visibility operator '{}' is not valid; use one of {}".format(
                        owner, operator, ", ".join(sorted(VALID_OPERATORS))
                    ),
                )
            )
        left = child_text(criterion, "leftValue")
        if left and RECORD_EXPR.search(left) and page_type not in RECORD_CONTEXT_TYPES:
            findings.append(
                Finding(
                    "ERROR",
                    where,
                    "{}: '{}' references the record in context, but the page type "
                    "is '{}' which has no record".format(owner, left, page_type),
                )
            )
    return findings


def check_flexipage(path: Path) -> Tuple[str, str, List[Finding]]:
    """Return (developer name, page type, findings)."""
    findings: List[Finding] = []
    root, errs = parse(path)
    findings.extend(errs)
    if errs:
        return path.name.split(".")[0], "", findings

    developer_name = path.name.split(".")[0]
    page_type = child_text(root, "type")
    where = str(path)

    if not page_type:
        findings.append(Finding("ERROR", where, "FlexiPage has no <type> element"))

    for region in children(root, "flexiPageRegions"):
        region_name = child_text(region, "name") or "(unnamed)"

        legacy = children(region, "componentInstances")
        if legacy:
            findings.append(
                Finding(
                    "ERROR",
                    where,
                    "region '{}' uses <componentInstances>, removed in API 49.0; "
                    "wrap each component in <itemInstances>".format(region_name),
                )
            )

        items = children(region, "itemInstances")
        if len(items) > MAX_COMPONENTS_PER_REGION:
            findings.append(
                Finding(
                    "ERROR",
                    where,
                    "region '{}' holds {} components; the platform maximum is "
                    "{}".format(region_name, len(items), MAX_COMPONENTS_PER_REGION),
                )
            )

        for item in items:
            for comp in children(item, "componentInstance"):
                name = child_text(comp, "componentName") or "(unnamed component)"
                findings.extend(
                    _check_identifier(comp, where, "region '{}' component '{}'".format(region_name, name))
                )
                for rule in children(comp, "visibilityRule"):
                    findings.extend(
                        check_visibility_rule(
                            rule, where,
                            "region '{}' component '{}'".format(region_name, name),
                            page_type,
                        )
                    )
            for field in children(item, "fieldInstance"):
                name = child_text(field, "fieldItem") or "(unnamed field)"
                findings.extend(
                    _check_identifier(field, where, "region '{}' field '{}'".format(region_name, name))
                )
                for rule in children(field, "visibilityRule"):
                    findings.extend(
                        check_visibility_rule(
                            rule, where,
                            "region '{}' field '{}'".format(region_name, name),
                            page_type,
                        )
                    )

    return developer_name, page_type, findings


def _check_identifier(node: ET.Element, where: str, owner: str) -> List[Finding]:
    identifier = child_text(node, "identifier")
    if not identifier:
        return [
            Finding(
                "ERROR", where,
                "{}: no <identifier>; required from API 53.0".format(owner),
            )
        ]
    if len(identifier) > MAX_IDENTIFIER_CHARS:
        return [
            Finding(
                "ERROR", where,
                "{}: identifier is {} characters; the maximum is {}".format(
                    owner, len(identifier), MAX_IDENTIFIER_CHARS
                ),
            )
        ]
    return []


# --------------------------------------------------------------------------- #

def run(root_dir: Path, strict: bool) -> List[Finding]:
    findings: List[Finding] = []

    if not root_dir.exists():
        return [Finding("ERROR", str(root_dir), "metadata directory not found")]

    page_files = sorted(root_dir.glob("flexipages/*.flexipage-meta.xml"))
    page_files += sorted(root_dir.glob("flexipages/*.flexipage"))
    if not page_files:
        return [
            Finding(
                "ERROR",
                str(root_dir),
                "no flexipages/*.flexipage-meta.xml found; point --manifest-dir at "
                "the package directory (for example force-app/main/default)",
            )
        ]

    assignments, assignment_findings = collect_assignments(root_dir)
    findings.extend(assignment_findings)

    known_pages: Set[str] = set()
    for path in page_files:
        developer_name, page_type, page_findings = check_flexipage(path)
        known_pages.add(developer_name)
        findings.extend(page_findings)

        if page_type in ASSIGNMENT_REQUIRED_TYPES and developer_name not in assignments:
            findings.append(
                Finding(
                    "ERROR",
                    str(path),
                    "record page '{}' has no override pointing at it in this tree. "
                    "Assignment lives in objects/<Object>/<Object>.object-meta.xml "
                    "(org default) and applications/<App>.app-meta.xml (app default, "
                    "app+recordType+profile) -- add them to the same manifest or the "
                    "deploy ships an inert page".format(developer_name),
                )
            )

    for page_name, sources in sorted(assignments.items()):
        if page_name not in known_pages:
            findings.append(
                Finding(
                    "WARN" if not strict else "ERROR",
                    str(root_dir),
                    "override(s) point at page '{}' which is not in this tree: {}. "
                    "It must already exist in the target org.".format(
                        page_name, "; ".join(sources)
                    ),
                )
            )

    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Lightning record pages and their assignment overrides. "
            "Flags unassigned record pages, over-capacity regions, missing "
            "identifiers, invalid visibility operators, and pre-API-49 metadata."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Salesforce package directory, e.g. force-app/main/default (default: .).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat overrides pointing at pages outside this tree as errors.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    findings = run(Path(args.manifest_dir), args.strict)

    errors = [f for f in findings if f.severity == "ERROR"]
    warnings = [f for f in findings if f.severity != "ERROR"]

    for finding in warnings:
        print(str(finding))
    for finding in errors:
        print(str(finding), file=sys.stderr)

    if errors:
        print(
            "\n{} error(s), {} warning(s).".format(len(errors), len(warnings)),
            file=sys.stderr,
        )
        return 1

    print("No errors found ({} warning(s)).".format(len(warnings)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
