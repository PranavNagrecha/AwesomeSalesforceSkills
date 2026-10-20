#!/usr/bin/env python3
"""Checker script for Flow Screen Input Validation Patterns skill.

Audits Flow XML metadata for screen-flow input-validation anti-patterns. Stdlib only.
Grounding is the Metadata API Developer Guide 264 ("api_meta"); line numbers come
from `grep -n`.

ERROR (exit 1 always)
  * A flow file that does not parse.
  * A validationRule without formulaExpression or errorMessage. Both are marked
    Required on FlowInputValidationRule (api_meta 264 L73389-73392).
WARN (exit 0 unless --strict)
  * validationRule on a screen field whose fieldType is not InputField, LargeTextArea
    or PasswordField. The guide: the rule validates input "when the screen component
    is of type InputField, LargeTextArea, or PasswordField" (api_meta 264 L74550-74552).
    This covers a custom LWC (fieldType ComponentInstance, extensionName): the rule is
    not documented for it, and the LWC must validate itself (SKILL.md Gotcha 5).
  * isRequired true on a DisplayText or boolean input. The guide: "Not supported for
    DisplayText or boolean inputField" (api_meta 264 L74482-74484).
  * isRequired text input with no validationRule: required-ness blocks empty values
    but does not check format (SKILL.md Concept 2). REVIEW only.
  * A validationRule formula that looks like it returns Text (IF with two quoted
    branches) or uses IF(cond, TRUE, FALSE) (SKILL.md Gotcha 1, Review Checklist).
  * A Decision directly after a screen, branching on that screen's inputs, whose
    default connector returns to the same screen (SKILL.md Gotcha 3).

An empty tree prints one WARN and exits 0 (1 with --strict). A missing path prints an
ERROR and exits 1.

Usage:
    python3 check_flow_screen_input_validation_patterns.py --manifest-dir DIR [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

VALIDATABLE = {"InputField", "LargeTextArea", "PasswordField"}


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def _child_text(node: ET.Element, child: str) -> str | None:
    for c in node:
        if _strip_ns(c.tag) == child:
            return (c.text or "").strip()
    return None


def _children(node: ET.Element, child: str) -> list[ET.Element]:
    return [c for c in node if _strip_ns(c.tag) == child]


def _find_flow_files(manifest_dir: Path) -> list[Path]:
    return sorted(list(manifest_dir.rglob("*.flow-meta.xml")) + list(manifest_dir.rglob("*.flow")))


def _audit_flow(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warns: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"{path}: could not parse XML ({exc})"], warns

    screen_to_vars: dict[str, set[str]] = {}
    screen_next: dict[str, str | None] = {}
    for screen in _children(root, "screens"):
        sname = _child_text(screen, "name") or "<unnamed-screen>"
        screen_to_vars[sname] = set()
        connector = next((c for c in screen if _strip_ns(c.tag) == "connector"), None)
        screen_next[sname] = _child_text(connector, "targetReference") if connector is not None else None
        for field in _children(screen, "fields"):
            fname = _child_text(field, "name") or "<unnamed-field>"
            screen_to_vars[sname].add(fname)
            ftype = _child_text(field, "fieldType") or ""
            dtype = (_child_text(field, "dataType") or "").lower()
            required = (_child_text(field, "isRequired") or "").lower() == "true"
            vrules = _children(field, "validationRule")
            if vrules and ftype and ftype not in VALIDATABLE:
                warns.append(f"{path}: screen `{sname}` field `{fname}` (fieldType {ftype}) has a validationRule; the guide documents it only for InputField, LargeTextArea and PasswordField (api_meta 264 L74550-74552)")
            if required and (ftype == "DisplayText" or (ftype == "InputField" and dtype == "boolean")):
                warns.append(f"{path}: screen `{sname}` field `{fname}` is isRequired but the guide says it is not supported for DisplayText or boolean inputField (api_meta 264 L74482-74484)")
            if required and not vrules and ftype in VALIDATABLE and dtype in ("string", ""):
                warns.append(f"{path}: REVIEW screen `{sname}` field `{fname}` is isRequired with no validationRule; required-ness blocks empty values but does not validate format")
            for vr in vrules:
                expr = _child_text(vr, "formulaExpression") or ""
                if not expr or not (_child_text(vr, "errorMessage") or ""):
                    errors.append(f"{path}: screen `{sname}` field `{fname}` validationRule needs formulaExpression and errorMessage (api_meta 264 L73389-73392)")
                if re.search(r'IF\s*\([^,]+,\s*"[^"]*"\s*,\s*"[^"]*"\s*\)', expr):
                    warns.append(f"{path}: screen `{sname}` field `{fname}` validation formula appears to return Text, not BOOLEAN; put the message in errorMessage")
                if re.search(r'IF\s*\([^,]+,\s*TRUE\s*,\s*FALSE\s*\)', expr, re.IGNORECASE):
                    warns.append(f"{path}: screen `{sname}` field `{fname}` uses IF(cond, TRUE, FALSE); use the boolean expression directly")

    for decision in _children(root, "decisions"):
        dname = _child_text(decision, "name") or "<unnamed-decision>"
        source = next((s for s, t in screen_next.items() if t == dname), None)
        if source is None:
            continue
        dc = next((c for c in decision if _strip_ns(c.tag) == "defaultConnector"), None)
        default_target = _child_text(dc, "targetReference") if dc is not None else None
        screen_vars = screen_to_vars.get(source, set())
        uses_screen_var = any(
            any(v in (_child_text(cond, "leftValueReference") or "") for v in screen_vars)
            for rule in _children(decision, "rules")
            for cond in _children(rule, "conditions")
        )
        if uses_screen_var and default_target == source:
            warns.append(f"{path}: decision `{dname}` after screen `{source}` validates that screen's inputs and loops back; use a validationRule on the input field")
    return errors, warns


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Flow metadata for screen-flow input-validation anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory containing Salesforce metadata (default: current directory).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings too.")
    args = parser.parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.is_dir():
        print(f"ERROR: manifest directory not found: {manifest_dir}")
        sys.exit(1)
    files = _find_flow_files(manifest_dir)
    if not files:
        print(f"WARN: no .flow or .flow-meta.xml files found under {manifest_dir}")
        return 1 if args.strict else 0
    errors: list[str] = []
    warns: list[str] = []
    for f in files:
        e, w = _audit_flow(f)
        errors += e
        warns += w
    for e in errors:
        print(f"ERROR: {e}")
    for w in warns:
        print(f"WARN: {w}")
    if not errors and not warns:
        print(f"OK: no screen-flow input-validation anti-patterns found in {len(files)} flow file(s).")
    if errors:
        sys.exit(1)
    return 1 if (warns and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
