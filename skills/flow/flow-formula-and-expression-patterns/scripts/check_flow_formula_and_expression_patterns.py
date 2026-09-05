#!/usr/bin/env python3
"""Checker for the Flow Formula And Expression Patterns skill.

Parses every ``*.flow-meta.xml`` (and ``*.flow``) under --manifest-dir and reports
formula-level defects that deploy cleanly and go wrong later. Stdlib only.

Rules (see ../references/gotchas.md and ../references/metadata-examples.md for grounding):

  FFX01  ERROR    <formulas> with no <dataType>. api_meta.txt L70609 states the default
                  outright: "dataType defaults to Number if it isn't defined in a formula."
                  A Text or Boolean formula silently becomes a Number formula, and the
                  error surfaces at the consuming element (Gotcha 41).
  FFX01b ERROR    <dataType> outside the seven documented FlowDataType values for a
                  formula (api_meta.txt L70599-L70609). Flow Builder's "Text" is String.
  FFX02  WARN     Number or Currency formula with no <scale>. api_meta.txt L70618-L70622
                  scopes scale to those two types and states no default, so the stored
                  value can differ from what the record displays (Gotcha 42).
  FFX02b WARN     <scale> present on a formula whose dataType is neither Number nor
                  Currency -- the guide says it is available only for those two.
  FFX03  ERROR    A {!name} inside a formula <expression> resolves to nothing in the flow:
                  not a variable, constant, formula, choice, text template, stage, element
                  name, or a documented/known global. Deploy fails naming the flow, not the
                  reference.
  FFX04  ERROR    Same, for a {!name} inside a <textTemplates> <text> body. The guide says
                  text "Supports merge fields" (api_meta.txt L72830) and says nothing about
                  what happens when one does not resolve (Gotcha 44).
  FFX05  WARN     <filterFormula> and <filters> both present on the same <start>.
                  api_meta.txt documents filterFormula (L72390), filterLogic (L72395) and
                  filters (L72402) as three independent fields with NO exclusivity
                  statement and no precedence rule -- unlike FlowElementReferenceOrValue
                  (L70411-L70413), which says "specify only one of the fields". The defect
                  is that a reader cannot tell which one runs, so this is a WARN (Gotcha 45).
  FFX06  ERROR    A decision <rules> block whose <conditionLogic> is a formula mode
                  (anything that is not and/or/advanced-logic) but whose formula body is
                  empty -- an outcome that can never be true.
  FFX07  ADVISORY An <expression> longer than the advisory character threshold.
                  UNVERIFIED (2026-09-05): no length bound is documented for FlowFormula
                  anywhere in api_meta.txt. The only grounded figure is 3,900 source
                  characters (apexdev.txt L28144), stated for formula FIELDS. The widely
                  quoted 5,000-character ceiling returns zero grep hits across api_meta,
                  object_reference, apexdev and the App Limits cheat sheet. Advisory only
                  (Gotcha 4).

Exit codes:
    0  no ERROR-severity findings (WARN and ADVISORY may be present)
    1  at least one ERROR, or --manifest-dir does not exist, or --strict was passed and
       any WARN/ADVISORY was found

Usage:
    python3 check_flow_formula_and_expression_patterns.py --manifest-dir force-app/main/default
    python3 check_flow_formula_and_expression_patterns.py --manifest-dir . --strict
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"

ERROR = "ERROR"
WARN = "WARN"
ADVISORY = "ADVISORY"

# api_meta.txt L70599-L70609 -- FlowDataType values documented for FlowFormula.
# Note: Flow Builder's "Text" is String here; "Text" is not a valid value.
FORMULA_DATA_TYPES = {
    "Boolean",
    "Currency",
    "Date",
    "DateTime",
    "Number",
    "String",
    "Time",
}

# api_meta.txt L70618-L70622 -- scale is "Available only when the data type is Number or
# Currency".
SCALE_TYPES = {"Number", "Currency"}

# api_meta.txt L71301-L71313 -- the only documented FlowRule.conditionLogic shapes are
# "and", "or", and advanced logic such as "1 AND (2 OR 3)". Anything else is the
# undocumented formula mode; see references/metadata-examples.md section 4.
ADVANCED_LOGIC_RE = re.compile(r"^[\d\s()]*(?:\b(?:AND|OR|NOT)\b[\d\s()]*)*$", re.I)

# UNVERIFIED (2026-09-05): no length bound is documented for FlowFormula. 3900 is the
# formula-FIELD source limit from apexdev.txt L28144, used here as an advisory ceiling.
ADVISORY_EXPRESSION_CHARS = 3900

# Merge-field tokens. Globals are matched by prefix because their members are open-ended.
# The three $Flow members below are the only ones that appear in api_meta.txt at all
# (L27212, L69784-L69840, L71996); the rest ($Flow.CurrentDate, $Flow.FaultMessage,
# $Flow.InterviewStartTime, $Flow.InterviewGuid) are real but undocumented in that guide,
# so they are accepted here without being cited as grounded.
GLOBAL_PREFIXES = (
    "$Record",
    "$Flow",
    "$User",
    "$Profile",
    "$Organization",
    "$Setup",
    "$Label",
    "$Permission",
    "$Api",
    "$System",
    "$Action",
    "$Resource",
    "$Site",
    "$Network",
    "$UserRole",
)

MERGE_RE = re.compile(r"\{!\s*([^}]+?)\s*\}")

# Every child of <Flow> whose entries carry a <name> that an expression may reference.
NAMED_COLLECTIONS = (
    "actionCalls",
    "apexPluginCalls",
    "assignments",
    "choices",
    "collectionProcessors",
    "constants",
    "decisions",
    "dynamicChoiceSets",
    "formulas",
    "loops",
    "orchestratedStages",
    "recordCreates",
    "recordDeletes",
    "recordLookups",
    "recordRollbacks",
    "recordUpdates",
    "screens",
    "stages",
    "steps",
    "subflows",
    "textTemplates",
    "transforms",
    "variables",
    "waits",
)


def _child(elem, tag):
    """Return the first child with ``tag``, or None.

    An ElementTree Element with no children is falsy, so ``a.find(x) or a.find(y)``
    silently discards real leaf nodes. Always compare against None.
    """
    if elem is None:
        return None
    found = elem.find(NS + tag)
    return found if found is not None else None


def _text(elem, tag, default=""):
    node = _child(elem, tag)
    if node is None or node.text is None:
        return default
    return node.text.strip()


def _has(elem, tag) -> bool:
    return _child(elem, tag) is not None


def _finding(severity: str, path: Path, rule: str, message: str) -> tuple[str, str]:
    return (severity, f"{path}: {rule} {message}")


def _resource_names(root) -> set[str]:
    """Every name an expression is allowed to reference inside this flow."""
    names: set[str] = set()
    for collection in NAMED_COLLECTIONS:
        for node in root.findall(NS + collection):
            name = _text(node, "name")
            if name:
                names.add(name)
            # Screen fields are addressable by their own name, not the screen's.
            for field in node.iter(NS + "fields"):
                field_name = _text(field, "name")
                if field_name:
                    names.add(field_name)
    return names


def _unresolved(expression: str, known: set[str]) -> list[str]:
    """Merge-field tokens in ``expression`` that resolve to nothing in this flow."""
    missing: list[str] = []
    for raw in MERGE_RE.findall(expression):
        token = raw.strip()
        if not token:
            continue
        head = token.split(".", 1)[0].strip()
        if head.startswith("$"):
            # A global namespace. Accepted whether or not the guide documents its members;
            # an unknown $-prefix is still reported because it is almost always a typo.
            if any(head == prefix or head.startswith(prefix) for prefix in GLOBAL_PREFIXES):
                continue
            missing.append(token)
            continue
        if head in known:
            continue
        missing.append(token)
    return missing


def _is_documented_condition_logic(logic: str) -> bool:
    """True for the shapes FlowRule.conditionLogic documents (api_meta.txt L71301-L71313)."""
    stripped = logic.strip()
    if stripped.lower() in ("and", "or"):
        return True
    if not stripped:
        return False
    # Advanced logic: digits, parens and AND/OR/NOT only, and at least one digit.
    return bool(re.search(r"\d", stripped)) and bool(ADVANCED_LOGIC_RE.match(stripped))


def _rule_formula_body(rule) -> str:
    """The formula text a formula-mode decision rule carries.

    api_meta.txt documents no <formula> child on FlowRule, so the shape Flow Builder emits
    is checked defensively: a direct <formula> child, or a single condition whose
    rightValue carries the expression as a stringValue with an empty leftValueReference.
    """
    direct = _text(rule, "formula")
    if direct:
        return direct
    parts: list[str] = []
    for condition in rule.findall(NS + "conditions"):
        if _text(condition, "leftValueReference"):
            continue
        right = _child(condition, "rightValue")
        if right is not None:
            parts.append(_text(right, "stringValue"))
    return " ".join(p for p in parts if p).strip()


def check_flow(path: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [_finding(ERROR, path, "FFX00", f"file does not parse as XML - {exc}")]

    known = _resource_names(root)

    # --- FFX01 / FFX01b / FFX02 / FFX02b / FFX03 / FFX07 -------------------------------
    for formula in root.findall(NS + "formulas"):
        name = _text(formula, "name") or "(unnamed)"
        data_type = _text(formula, "dataType")
        expression = _text(formula, "expression")

        if not data_type:
            findings.append(_finding(
                ERROR, path, "FFX01",
                f"formula '{name}' has no <dataType>. api_meta.txt L70609: \"dataType "
                "defaults to Number if it isn't defined in a formula\" - a Text or Boolean "
                "formula silently becomes a Number formula.",
            ))
        elif data_type not in FORMULA_DATA_TYPES:
            findings.append(_finding(
                ERROR, path, "FFX01b",
                f"formula '{name}' declares <dataType>{data_type}</dataType>, which is not "
                "one of the seven documented FlowDataType values for a formula "
                f"({', '.join(sorted(FORMULA_DATA_TYPES))}; api_meta.txt L70599-L70609). "
                "Flow Builder's \"Text\" is String in the XML.",
            ))

        has_scale = _has(formula, "scale")
        if data_type in SCALE_TYPES and not has_scale:
            findings.append(_finding(
                WARN, path, "FFX02",
                f"formula '{name}' is {data_type} with no <scale>. api_meta.txt "
                "L70618-L70622 scopes scale to Number and Currency and states no default, "
                "so the stored value can differ from the target field's display.",
            ))
        if has_scale and data_type and data_type not in SCALE_TYPES:
            findings.append(_finding(
                WARN, path, "FFX02b",
                f"formula '{name}' declares <scale> with dataType {data_type}. "
                "api_meta.txt L70618-L70622: scale is \"Available only when the data type "
                "is Number or Currency\".",
            ))

        for token in _unresolved(expression, known):
            findings.append(_finding(
                ERROR, path, "FFX03",
                f"formula '{name}' references {{!{token}}}, which is not a variable, "
                "constant, formula, choice, template, stage, screen field or element in "
                "this flow, and is not a global namespace.",
            ))

        if len(expression) > ADVISORY_EXPRESSION_CHARS:
            findings.append(_finding(
                ADVISORY, path, "FFX07",
                f"formula '{name}' <expression> is {len(expression)} characters. "
                "UNVERIFIED (2026-09-05): no length bound is documented for FlowFormula in "
                "api_meta.txt; 3,900 is the formula-FIELD source limit from apexdev.txt "
                "L28144 and the widely quoted 5,000 figure has zero grep hits in any guide. "
                "Compose into smaller resources regardless - this is unreviewable.",
            ))

    # --- FFX04 -------------------------------------------------------------------------
    for template in root.findall(NS + "textTemplates"):
        name = _text(template, "name") or "(unnamed)"
        body = _text(template, "text")
        for token in _unresolved(body, known):
            findings.append(_finding(
                ERROR, path, "FFX04",
                f"text template '{name}' merges {{!{token}}}, which resolves to nothing in "
                "this flow. api_meta.txt L72830: text \"Supports merge fields\" - and the "
                "deploy error for an unresolvable one names the flow, not the template.",
            ))

    # --- FFX05 -------------------------------------------------------------------------
    for start in root.findall(NS + "start"):
        if _has(start, "filterFormula") and start.findall(NS + "filters"):
            findings.append(_finding(
                WARN, path, "FFX05",
                "<start> carries both <filterFormula> and <filters>. api_meta.txt "
                "documents filterFormula (L72390), filterLogic (L72395) and filters "
                "(L72402) as independent fields with no exclusivity statement and no "
                "precedence rule, so a reader cannot tell which entry condition runs. "
                "Delete one.",
            ))

    # --- FFX06 -------------------------------------------------------------------------
    for decision in root.findall(NS + "decisions"):
        decision_name = _text(decision, "name") or "(unnamed)"
        for rule in decision.findall(NS + "rules"):
            rule_name = _text(rule, "name") or "(unnamed)"
            logic = _text(rule, "conditionLogic")
            if not logic or _is_documented_condition_logic(logic):
                continue
            if not _rule_formula_body(rule):
                findings.append(_finding(
                    ERROR, path, "FFX06",
                    f"decision '{decision_name}' rule '{rule_name}' uses formula-mode "
                    f"<conditionLogic>{logic}</conditionLogic> with an empty formula body, "
                    "so the outcome can never evaluate true. api_meta.txt L71301-L71313 "
                    "documents only and/or/advanced logic for conditionLogic; the formula "
                    "mode is undocumented, which is why the body must be read defensively.",
                ))

    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Flow metadata for formula defects that deploy cleanly.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote WARN and ADVISORY findings to failures (exit 1).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the 'no issues' line; exit code is unchanged.",
    )
    return parser.parse_args()


def collect(manifest_dir: Path) -> tuple[list[tuple[str, str]], bool]:
    """Return (findings, scanned_any_flow)."""
    flows = sorted(
        set(manifest_dir.rglob("*.flow-meta.xml")) | set(manifest_dir.rglob("*.flow"))
    )
    if not flows:
        return [(WARN, f"No *.flow-meta.xml files found under {manifest_dir}")], False
    findings: list[tuple[str, str]] = []
    for flow in flows:
        findings.extend(check_flow(flow))
    return findings, True


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ERROR: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    findings, _ = collect(manifest_dir)

    if not findings:
        if not args.quiet:
            print("No issues found.")
        return 0

    order = {ERROR: 0, WARN: 1, ADVISORY: 2}
    for severity, message in sorted(findings, key=lambda f: (order[f[0]], f[1])):
        print(f"{severity}: {message}", file=sys.stderr)

    counts = {level: sum(1 for s, _ in findings if s == level) for level in order}
    print(
        f"\n{counts[ERROR]} error(s), {counts[WARN]} warning(s), "
        f"{counts[ADVISORY]} advisory.",
        file=sys.stderr,
    )

    if counts[ERROR]:
        return 1
    if args.strict and (counts[WARN] or counts[ADVISORY]):
        print("--strict: promoting warnings and advisories to failure.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
