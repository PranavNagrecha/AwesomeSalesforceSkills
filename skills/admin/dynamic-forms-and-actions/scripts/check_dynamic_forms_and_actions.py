#!/usr/bin/env python3
"""Checker for Dynamic Forms and Dynamic Actions metadata.

Inspects a local Salesforce source-format project and reports structural
problems in `.flexipage-meta.xml` files and in the object / application
metadata that assigns those pages.

Every hard limit quoted below comes from the Metadata API Developer Guide,
FlexiPage section (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf):

  * "A Lightning page region can contain up to 100 components."  (FlexiPageRegion)
  * "Expressions in component visibility rules can span no more than five
     fields."                                                    (UiFormulaCriterion)
  * operator is one of CONTAINS, EQUAL, NE, GT, GE, LE, LT       (UiFormulaCriterion)
  * identifier "has a maximum limit of 120 characters"           (ComponentInstance, FieldInstance)
  * ActionOverride/AppProfileActionOverride content names the Lightning page used
    as the override.

Findings are prefixed ERROR / WARN / INFO. Any finding at all exits 1 so the
script is usable as a pipeline gate; INFO findings are review heuristics chosen
by this skill, not platform limits, and are labelled as such.

Stdlib only.

Usage:
    python3 check_dynamic_forms_and_actions.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

# --- Documented platform limits -------------------------------------------
MAX_COMPONENTS_PER_REGION = 100     # Metadata API Developer Guide, FlexiPageRegion
MAX_EXPRESSION_SPANS = 5            # Metadata API Developer Guide, UiFormulaCriterion
MAX_IDENTIFIER_CHARS = 120          # Metadata API Developer Guide, ComponentInstance
VALID_OPERATORS = {"CONTAINS", "EQUAL", "NE", "GT", "GE", "LE", "LT"}

# --- Review heuristics chosen by this skill (NOT platform limits) ----------
REVIEW_MAX_FIELD_SECTIONS = 8
REVIEW_MAX_VISIBILITY_RULES = 20

HIGHLIGHTS_PANEL = "force:highlightsPanel"
FIELD_SECTION = "flexipage:fieldSection"


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Dynamic Forms and Dynamic Actions "
            "configuration problems."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help=(
            "Root of the Salesforce source-format project, e.g. "
            "force-app/main/default (default: current directory)."
        ),
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# XML helpers
#
# NOTE: a leaf ElementTree Element is falsy, so `a.find(x) or a.find(y)` is a
# bug that silently discards a real match. Every lookup below tests
# `is not None` explicitly.
# ---------------------------------------------------------------------------

def _local(tag: str) -> str:
    """Strip the namespace from an ElementTree tag."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _first_child(parent: ET.Element, name: str) -> ET.Element | None:
    """Return the first direct child with the given local name, or None."""
    for child in parent:
        if _local(child.tag) == name:
            return child
    return None


def _children(parent: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in parent if _local(c.tag) == name]


def _descendants(root: ET.Element, name: str) -> list[ET.Element]:
    return [e for e in root.iter() if _local(e.tag) == name]


def _text(parent: ET.Element | None, name: str) -> str:
    """Text of the first direct child with this local name, stripped."""
    if parent is None:
        return ""
    child = _first_child(parent, name)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def _parse(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None


# ---------------------------------------------------------------------------
# Project inventory
# ---------------------------------------------------------------------------

def _flexipages(root_dir: Path) -> list[Path]:
    return sorted(root_dir.rglob("*.flexipage-meta.xml"))


def _page_api_name(path: Path) -> str:
    return path.name[: -len(".flexipage-meta.xml")]


def _object_field_names(root_dir: Path, sobject: str) -> set[str] | None:
    """Field API names declared under objects/<sobject>/fields/.

    Returns None when the folder is absent, which means "cannot judge" rather
    than "no fields" — callers must not warn in that case.
    """
    if not sobject:
        return None
    for objects_dir in root_dir.rglob("objects"):
        candidate = objects_dir / sobject / "fields"
        if candidate.is_dir():
            return {
                f.name[: -len(".field-meta.xml")]
                for f in candidate.glob("*.field-meta.xml")
            }
    return None


# ---------------------------------------------------------------------------
# Check 1 — the same field placed twice on one page
# ---------------------------------------------------------------------------

def check_duplicate_fields(root: ET.Element, page: str) -> list[str]:
    items = [_text(fi, "fieldItem") for fi in _descendants(root, "fieldInstance")]
    counts = Counter(i for i in items if i)
    return [
        f"WARN  [{page}] Field '{item}' is placed {n} times on this page. "
        f"Duplicate field instances render the field twice and make inline edit "
        f"ambiguous; keep one instance and move it, or give the second a "
        f"visibility rule that is mutually exclusive with the first."
        for item, n in sorted(counts.items())
        if n > 1
    ]


# ---------------------------------------------------------------------------
# Check 2 — visibility rules pointing at fields the object does not declare
# ---------------------------------------------------------------------------

_RECORD_REF = re.compile(r"^\{!Record\.([A-Za-z0-9_.]+)\}$")


def check_rule_fields_exist(
    root: ET.Element, page: str, known_fields: set[str] | None
) -> list[str]:
    if known_fields is None:
        return []  # objects/<Obj>/fields/ not in this tree — cannot judge.
    issues: list[str] = []
    seen: set[str] = set()
    for criterion in _descendants(root, "criteria"):
        left = _text(criterion, "leftValue")
        match = _RECORD_REF.match(left)
        if not match:
            continue
        path = match.group(1)
        if "." in path:
            continue  # cross-object / RecordType traversal; not a local field.
        if path in known_fields or not path.endswith("__c") or path in seen:
            continue
        seen.add(path)
        issues.append(
            f"WARN  [{page}] Visibility rule references '{left}' but "
            f"'{path}' is not declared under this object's fields/ folder. "
            f"The page deploys and the rule then evaluates against a field that "
            f"may not exist in the target org."
        )
    return issues


# ---------------------------------------------------------------------------
# Check 3 — criteria that cannot evaluate as written
# ---------------------------------------------------------------------------

def check_criteria(root: ET.Element, page: str) -> list[str]:
    issues: list[str] = []
    for criterion in _descendants(root, "criteria"):
        left = _text(criterion, "leftValue")
        operator = _text(criterion, "operator")
        right = _text(criterion, "rightValue")

        if operator and operator not in VALID_OPERATORS:
            issues.append(
                f"ERROR [{page}] Visibility criterion on '{left or '(no leftValue)'}' "
                f"uses operator '{operator}'. The documented set is "
                f"{', '.join(sorted(VALID_OPERATORS))}."
            )

        if operator in VALID_OPERATORS and left and not right:
            issues.append(
                f"ERROR [{page}] Visibility criterion on '{left}' uses operator "
                f"'{operator}' with an empty rightValue, so the condition can "
                f"never be satisfied and the component is permanently hidden."
            )

        if left.startswith("{!Record.") or left.startswith("{!$User."):
            body = left.strip("{}!").rstrip("}")
            spans = body.count(".")
            if spans > MAX_EXPRESSION_SPANS:
                issues.append(
                    f"ERROR [{page}] Visibility expression '{left}' spans {spans} "
                    f"fields. Documented maximum is {MAX_EXPRESSION_SPANS}. "
                    f"Collapse the traversal into a formula field on the record."
                )
    return issues


# ---------------------------------------------------------------------------
# Check 4 — region size and identifier length against documented limits
# ---------------------------------------------------------------------------

def check_region_limits(root: ET.Element, page: str) -> list[str]:
    issues: list[str] = []
    for region in _children(root, "flexiPageRegions"):
        name = _text(region, "name") or "(unnamed)"
        items = _children(region, "itemInstances")
        if len(items) > MAX_COMPONENTS_PER_REGION:
            issues.append(
                f"ERROR [{page}] Region '{name}' holds {len(items)} item "
                f"instances. A Lightning page region is documented as holding up "
                f"to {MAX_COMPONENTS_PER_REGION} components. Split the fields "
                f"across additional sections, columns, or tab facets."
            )
    for element_name in ("componentInstance", "fieldInstance"):
        for element in _descendants(root, element_name):
            identifier = _text(element, "identifier")
            if len(identifier) > MAX_IDENTIFIER_CHARS:
                issues.append(
                    f"ERROR [{page}] {element_name} identifier "
                    f"'{identifier[:40]}...' is {len(identifier)} characters; the "
                    f"documented maximum is {MAX_IDENTIFIER_CHARS}."
                )
    return issues


# ---------------------------------------------------------------------------
# Check 5 — record page shape review heuristics (INFO, not limits)
# ---------------------------------------------------------------------------

def check_page_shape(root: ET.Element, page: str) -> list[str]:
    issues: list[str] = []
    page_type = _text(root, "type")
    component_names = [
        _text(c, "componentName") for c in _descendants(root, "componentInstance")
    ]

    if page_type == "RecordPage" and HIGHLIGHTS_PANEL not in component_names:
        issues.append(
            f"INFO  [{page}] RecordPage has no {HIGHLIGHTS_PANEL} component. "
            f"Dynamic Actions are hosted by the highlights panel, so a record "
            f"page without one has no configurable action bar. Intentional on a "
            f"read-only or embedded page; a mistake on most others."
        )

    section_count = sum(1 for n in component_names if n == FIELD_SECTION)
    if section_count > REVIEW_MAX_FIELD_SECTIONS:
        issues.append(
            f"INFO  [{page}] {section_count} {FIELD_SECTION} components. "
            f"{REVIEW_MAX_FIELD_SECTIONS} is a review heuristic chosen by this "
            f"skill, not a platform limit — treat it as a prompt to check whether "
            f"the page should be tabbed rather than as a failure."
        )

    rule_count = len(_descendants(root, "visibilityRule"))
    if rule_count > REVIEW_MAX_VISIBILITY_RULES:
        issues.append(
            f"INFO  [{page}] {rule_count} visibility rules on one page. "
            f"{REVIEW_MAX_VISIBILITY_RULES} is a review heuristic chosen by this "
            f"skill, not a platform limit. Measure the page before and after with "
            f"the method in admin/lightning-page-performance-tuning rather than "
            f"assuming a number."
        )
    return issues


# ---------------------------------------------------------------------------
# Check 6 — assignments pointing at pages that are not in the tree
# ---------------------------------------------------------------------------

def check_assignment_targets(root_dir: Path, page_names: set[str]) -> list[str]:
    issues: list[str] = []
    sources = list(root_dir.rglob("*.object-meta.xml"))
    sources += list(root_dir.rglob("*.app-meta.xml"))

    for path in sorted(sources):
        root = _parse(path)
        if root is None:
            issues.append(f"ERROR [{path.name}] Could not parse XML.")
            continue
        for tag in ("actionOverrides", "profileActionOverrides"):
            for override in _descendants(root, tag):
                if _text(override, "type").lower() != "flexipage":
                    continue
                content = _text(override, "content")
                if not content:
                    continue
                if content not in page_names:
                    issues.append(
                        f"WARN  [{path.name}] <{tag}> assigns Lightning page "
                        f"'{content}', which is not present in this source tree. "
                        f"If the page is not already in the target org, the deploy "
                        f"fails; if it is, the assignment is invisible to review. "
                        f"Retrieve the FlexiPage into the same package."
                    )
    return issues


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def check_dynamic_forms_and_actions(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"ERROR Manifest directory not found: {manifest_dir}"]

    pages = _flexipages(manifest_dir)
    page_names = {_page_api_name(p) for p in pages}

    for path in pages:
        page = _page_api_name(path)
        root = _parse(path)
        if root is None:
            issues.append(f"ERROR [{page}] Could not parse XML — file is malformed.")
            continue

        known_fields = _object_field_names(manifest_dir, _text(root, "sobjectType"))

        issues.extend(check_duplicate_fields(root, page))
        issues.extend(check_rule_fields_exist(root, page, known_fields))
        issues.extend(check_criteria(root, page))
        issues.extend(check_region_limits(root, page))
        issues.extend(check_page_shape(root, page))

    issues.extend(check_assignment_targets(manifest_dir, page_names))
    return issues


def main() -> int:
    args = parse_args()
    issues = check_dynamic_forms_and_actions(Path(args.manifest_dir))

    if not issues:
        print("No Dynamic Forms / Dynamic Actions issues found.")
        return 0

    for issue in issues:
        print(issue)
    print(f"\n{len(issues)} finding(s).")
    return 1


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        sys.exit(1)
    sys.exit(0)
