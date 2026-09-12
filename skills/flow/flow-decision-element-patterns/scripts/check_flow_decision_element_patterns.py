#!/usr/bin/env python3
"""check_flow_decision_element_patterns.py — review Decision elements two ways.

Stdlib only.

Two independent modes, either or both:

  --docs-dir DIR       heuristic check of Decision review docs (*.md), the
                       original behaviour: each doc must cover outcomes,
                       checks, the default, null-safety, pick-list API values,
                       and nesting depth.

  --manifest-dir DIR   structural check of retrieved flow metadata
                       (*.flow-meta.xml and *.flow) against the FlowDecision /
                       FlowRule / FlowCondition contract in the Metadata API
                       Developer Guide. Every rule below names the guide fact
                       it enforces.

Findings are printed one per line as `ERROR: ...`, `WARN: ...` or `INFO: ...`.

Exit codes:
    0  no ERROR findings (WARN findings do not block unless --strict)
    1  at least one ERROR finding, or a path that does not exist

Metadata facts enforced (Metadata API Developer Guide, Flow):
    FlowDecision.rules            evaluated in listed order; first true rule's
                                  connector wins; otherwise defaultConnector
    FlowDecision.defaultConnector node to execute when no rule is true
    FlowRule.label                Required
    FlowRule.conditionLogic       `and`, `or`, or advanced logic such as
                                  `1 AND (2 OR 3)`; advanced logic is capped at
                                  1,000 characters
    FlowCondition.leftValueReference / .operator   Required
    FlowComparisonOperator.None   saves an *incomplete* condition on purpose
    FlowElementReferenceOrValue   specify only one of the typed fields
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"

DOC_REQUIRED_SECTIONS = ("outcomes", "checks", "default")

# FlowElementReferenceOrValue: "Make sure that you specify only one of the fields."
VALUE_CHILDREN = {
    "apexValue", "booleanValue", "complexValue", "dateTimeValue", "dateValue",
    "elementReference", "formulaExpression", "numberValue", "sobjectValue",
    "stringValue", "timeValue",
}

# Operators whose documented right-hand side is a boolean flag, not a literal.
BOOLEAN_RHS_OPERATORS = {"IsNull", "IsBlank", "IsChanged", "IsEmpty", "WasSet",
                         "WasSelected", "WasVisited", "HasError"}

# Operators that compare a value and therefore evaluate false against null.
COMPARING_OPERATORS = {"EqualTo", "NotEqualTo", "Contains", "StartsWith",
                       "EndsWith", "In", "NotIn"}

NULL_TEST_OPERATORS = {"IsNull", "IsBlank", "IsEmpty"}

GENERIC_DEFAULT_LABELS = {"", "default", "default outcome", "no", "yes", "else",
                          "none", "other", "otherwise", "fallback", "n/a"}

# Id prefixes worth refusing as literals in a routing condition.
ID_PREFIXES = ("005", "00G", "00E", "00e", "0Gp", "701", "00Q", "012")

ADVANCED_LOGIC_MAX = 1000


def _text(el: ET.Element | None) -> str:
    return (el.text or "").strip() if el is not None else ""


def _find(el: ET.Element, tag: str) -> ET.Element | None:
    return el.find(f"{NS}{tag}") if el.find(f"{NS}{tag}") is not None else el.find(tag)


def _findall(el: ET.Element, tag: str) -> list[ET.Element]:
    got = el.findall(f"{NS}{tag}")
    return got if got else el.findall(tag)


def _local(tag: str) -> str:
    return tag.split("}")[-1]


# --------------------------------------------------------------------------- docs


def check_doc(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()
    for section in DOC_REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"WARN: {path}: review doc never mentions '{section}'")
    if "null-safe" not in text and "null safe" not in text:
        issues.append(f"WARN: {path}: no null-safety column or check")
    if "api value" not in text:
        issues.append(f"WARN: {path}: no pick-list API-value check")
    if "nesting" not in text and "depth" not in text:
        issues.append(f"WARN: {path}: no depth/nesting check")
    return issues


# ----------------------------------------------------------------------- metadata


def _condition_signature(cond: ET.Element) -> tuple[str, str, str]:
    left = _text(_find(cond, "leftValueReference"))
    op = _text(_find(cond, "operator"))
    rv = _find(cond, "rightValue")
    val = ""
    if rv is not None:
        parts = [f"{_local(c.tag)}={(c.text or '').strip()}" for c in list(rv)]
        val = "|".join(sorted(parts))
    return (left, op, val)


def _check_rule(where: str, rule: ET.Element, issues: list[str]) -> list[tuple[str, str, str]]:
    name = _text(_find(rule, "name")) or "<unnamed>"
    at = f"{where} rule '{name}'"

    # FlowRule.label is Required
    if not _text(_find(rule, "label")):
        issues.append(f"ERROR: {at}: FlowRule.label is required and is missing")

    logic = _text(_find(rule, "conditionLogic"))
    conditions = _findall(rule, "conditions")
    if logic.lower() not in ("and", "or", ""):
        # advanced logic
        if len(logic) > ADVANCED_LOGIC_MAX:
            issues.append(
                f"ERROR: {at}: advanced conditionLogic is {len(logic)} characters; "
                f"the documented maximum is {ADVANCED_LOGIC_MAX}"
            )
        if logic.count("(") != logic.count(")"):
            issues.append(f"ERROR: {at}: unbalanced parentheses in conditionLogic '{logic}'")
        refs = {int(n) for n in re.findall(r"\d+", logic)}
        if refs and (max(refs) > len(conditions) or min(refs) < 1):
            issues.append(
                f"ERROR: {at}: conditionLogic '{logic}' references a condition number "
                f"outside 1..{len(conditions)}"
            )
        unref = sorted(set(range(1, len(conditions) + 1)) - refs)
        if unref:
            issues.append(
                f"WARN: {at}: conditionLogic '{logic}' never references condition(s) "
                f"{unref}; they are defined but unused"
            )
    elif len(conditions) > 1 and not logic:
        issues.append(f"WARN: {at}: {len(conditions)} conditions and no conditionLogic")

    sigs: list[tuple[str, str, str]] = []
    for idx, cond in enumerate(conditions, 1):
        cat = f"{at} condition {idx}"
        left = _text(_find(cond, "leftValueReference"))
        op = _text(_find(cond, "operator"))
        if not left:
            issues.append(f"ERROR: {cat}: FlowCondition.leftValueReference is required and is missing")
        if not op:
            issues.append(f"ERROR: {cat}: FlowCondition.operator is required and is missing")
        if op == "None":
            issues.append(
                f"ERROR: {cat}: operator 'None' saves an incomplete condition; "
                f"it is a work-in-progress marker and must not ship"
            )
        rv = _find(cond, "rightValue")
        if rv is not None:
            kids = [_local(c.tag) for c in list(rv) if _local(c.tag) in VALUE_CHILDREN]
            if len(kids) > 1:
                issues.append(
                    f"ERROR: {cat}: rightValue sets {len(kids)} typed children ({', '.join(kids)}); "
                    f"FlowElementReferenceOrValue permits exactly one"
                )
            if op in BOOLEAN_RHS_OPERATORS and kids and "booleanValue" not in kids:
                issues.append(
                    f"WARN: {cat}: operator '{op}' takes a boolean right-hand value; "
                    f"found <{kids[0]}> instead"
                )
            sv = _find(rv, "stringValue")
            lit = _text(sv)
            if lit.startswith(ID_PREFIXES) and len(lit) in (15, 18):
                issues.append(
                    f"WARN: {cat}: hardcoded Salesforce Id literal '{lit}'; route on a "
                    f"Queue, Public Group, Custom Permission, or Custom Metadata row instead"
                )
        sigs.append(_condition_signature(cond))
    return sigs


def _check_decision(path: Path, dec: ET.Element, decisions_by_name: dict,
                    issues: list[str]) -> None:
    name = _text(_find(dec, "name")) or "<unnamed>"
    where = f"{path.name} decision '{name}'"

    default_conn = _find(dec, "defaultConnector")
    default_label = _text(_find(dec, "defaultConnectorLabel"))
    if default_conn is None:
        issues.append(
            f"WARN: {where}: no defaultConnector; every record matching no rule "
            f"leaves this element with nowhere documented to go"
        )
    if default_label.strip().lower() in GENERIC_DEFAULT_LABELS:
        issues.append(
            f"WARN: {where}: defaultConnectorLabel is {default_label!r}; name it after "
            f"the case it represents so a defaulted record is distinguishable from an "
            f"unmatched one"
        )

    rules = _findall(dec, "rules")
    if not rules:
        issues.append(f"WARN: {where}: no rules; a decision with no outcome is a straight line")
        return

    per_rule: list[tuple[str, str, list[tuple[str, str, str]]]] = []
    for rule in rules:
        sigs = _check_rule(where, rule, issues)
        per_rule.append((_text(_find(rule, "name")) or "<unnamed>",
                         _text(_find(rule, "conditionLogic")).lower(), sigs))

    # rules are evaluated in listed order, first true rule wins: an earlier rule
    # whose AND-conditions are a subset of a later rule's makes the later one dead.
    for i, (ni, li, si) in enumerate(per_rule):
        if li not in ("and", ""):
            continue
        for nj, lj, sj in per_rule[i + 1:]:
            if lj not in ("and", ""):
                continue
            if si and set(si) < set(sj):
                issues.append(
                    f"WARN: {where}: outcome '{nj}' is unreachable — earlier outcome "
                    f"'{ni}' matches every record '{nj}' would match. Order most "
                    f"specific first."
                )

    # null guard: a text/picklist comparison with no IsNull/IsBlank test on the same field
    compared: set[str] = set()
    guarded: set[str] = set()
    for _n, _l, sigs in per_rule:
        for left, op, val in sigs:
            if op in NULL_TEST_OPERATORS:
                guarded.add(left)
            elif op in COMPARING_OPERATORS and "stringValue=" in val:
                compared.add(left)
    for left in sorted(compared - guarded):
        issues.append(
            f"WARN: {where}: '{left}' is compared to a text value but no outcome tests "
            f"it with IsNull or IsBlank; a null record falls to the default silently"
        )

    # nesting depth: decision -> decision -> decision
    def depth(dname: str, seen: frozenset[str]) -> int:
        d = decisions_by_name.get(dname)
        if d is None or dname in seen:
            return 0
        best = 0
        targets = []
        for r in _findall(d, "rules"):
            c = _find(r, "connector")
            if c is not None:
                targets.append(_text(_find(c, "targetReference")))
        dc = _find(d, "defaultConnector")
        if dc is not None:
            targets.append(_text(_find(dc, "targetReference")))
        for tref in targets:
            if tref in decisions_by_name:
                best = max(best, 1 + depth(tref, seen | {dname}))
        return best

    d = depth(name, frozenset())
    if d >= 2:
        issues.append(
            f"WARN: {where}: decisions chain {d + 1} deep from here; each level adds a "
            f"default that absorbs cases. Flatten, then extract a subflow."
        )


def check_manifest_file(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"ERROR: {path}: not parseable XML — {exc}"]
    if _local(root.tag) != "Flow":
        return [f"INFO: {path}: root element is <{_local(root.tag)}>, not <Flow>; skipped"]

    decisions = _findall(root, "decisions")
    if not decisions:
        return [f"INFO: {path}: no <decisions> in this flow; nothing to review"]

    by_name = {_text(_find(d, "name")): d for d in decisions}
    for dec in decisions:
        _check_decision(path, dec, by_name, issues)
    return issues


# ----------------------------------------------------------------------------- cli


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Review Decision elements in review docs and/or retrieved flow metadata."
    )
    parser.add_argument("--docs-dir", help="directory of Decision review docs (*.md)")
    parser.add_argument("--manifest-dir",
                        help="directory of retrieved flow metadata (*.flow-meta.xml, *.flow)")
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 on WARN findings as well as ERROR findings")
    args = parser.parse_args()
    if not args.docs_dir and not args.manifest_dir:
        args.docs_dir = "."
    return args


def main() -> int:
    args = parse_args()
    findings: list[str] = []
    missing = False

    if args.manifest_dir:
        root = Path(args.manifest_dir)
        if not root.exists():
            print(f"ERROR: manifest dir not found: {root}")
            missing = True
        else:
            targets = sorted(set(root.rglob("*.flow-meta.xml")) | set(root.rglob("*.flow")))
            if not targets:
                findings.append(f"WARN: no *.flow-meta.xml or *.flow under {root}; nothing to review")
            for t in targets:
                findings.extend(check_manifest_file(t))

    if args.docs_dir:
        root = Path(args.docs_dir)
        if not root.exists():
            print(f"ERROR: docs dir not found: {root}")
            missing = True
        else:
            targets = sorted(root.rglob("*.md"))
            if not targets:
                findings.append(f"WARN: no Decision review docs (*.md) under {root}; nothing to review")
            for t in targets:
                findings.extend(check_doc(t))

    if missing:
        return 1

    errors = sum(1 for f in findings if f.startswith("ERROR"))
    warns = sum(1 for f in findings if f.startswith("WARN"))
    for f in findings:
        print(f)
    print(f"-- {errors} ERROR, {warns} WARN, {len(findings) - errors - warns} INFO")
    if errors:
        return 1
    if warns and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
