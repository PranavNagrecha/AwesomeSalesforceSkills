#!/usr/bin/env python3
"""Checker script for Flow Screen Input Validation Patterns skill.

Audits Flow XML metadata for screen-flow input-validation anti-patterns:

- Screen input field marked `isRequired` with no `<validationRule>` and no
  obvious format constraint (warn — required without format check).
- `<validationRule>` whose `<formulaExpression>` looks like it returns Text
  (e.g. contains `IF(.*,"`) instead of a boolean.
- `<validationRule>` declared on a custom LWC `<extensionName>` block —
  silently ignored at runtime; the LWC must implement `@api validate()`.
- Decision element placed immediately after a screen, branching on a
  variable defined on that screen, with the default connector pointing back
  to the same screen — the "validation in a Decision" anti-pattern.

Stdlib only — uses xml.etree.ElementTree.

Usage:
    python3 check_flow_screen_input_validation_patterns.py [--manifest-dir DIR]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"f": "http://soap.sforce.com/2006/04/metadata"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Flow metadata for screen-flow input-validation anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _find_flow_files(manifest_dir: Path) -> list[Path]:
    """Return Flow metadata files under the manifest dir."""
    if not manifest_dir.exists():
        return []
    candidates: list[Path] = []
    for path in manifest_dir.rglob("*.flow-meta.xml"):
        candidates.append(path)
    for path in manifest_dir.rglob("*.flow"):
        candidates.append(path)
    return candidates


def _strip_ns(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _child_text(node: ET.Element, child: str) -> str | None:
    for c in node:
        if _strip_ns(c.tag) == child:
            return (c.text or "").strip()
    return None


def _children(node: ET.Element, child: str) -> list[ET.Element]:
    return [c for c in node if _strip_ns(c.tag) == child]


def _audit_flow(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        return [f"{path}: could not parse XML ({exc})"]

    root = tree.getroot()

    # Map screen names to set of variable names defined on them
    screen_to_vars: dict[str, set[str]] = {}
    screen_next_targets: dict[str, str | None] = {}

    for screen in _children(root, "screens"):
        sname = _child_text(screen, "name") or "<unnamed-screen>"
        screen_to_vars[sname] = set()
        # next connector target
        connector = next((c for c in screen if _strip_ns(c.tag) == "connector"), None)
        screen_next_targets[sname] = (
            _child_text(connector, "targetReference") if connector is not None else None
        )

        for field in _children(screen, "fields"):
            fname = _child_text(field, "name") or "<unnamed-field>"
            screen_to_vars[sname].add(fname)
            is_required = (_child_text(field, "isRequired") or "").lower() == "true"
            extension = _child_text(field, "extensionName")
            vrules = _children(field, "validationRule")

            # Anti-pattern: <validationRule> on a custom LWC extension
            if extension and vrules:
                issues.append(
                    f"{path}: screen `{sname}` field `{fname}` is a custom LWC "
                    f"({extension}) with a `<validationRule>` block — silently ignored. "
                    f"Implement `@api validate()` in the LWC instead."
                )

            # Required without any validation rule (warn — format unchecked)
            if is_required and not vrules and not extension:
                dtype = (_child_text(field, "dataType") or "").lower()
                if dtype in ("string", ""):
                    issues.append(
                        f"{path}: screen `{sname}` field `{fname}` is `isRequired=true` "
                        f"but has no `<validationRule>` — required-ness blocks empty values "
                        f"but does not validate format."
                    )

            # Anti-pattern: formula returns string
            for vr in vrules:
                expr = _child_text(vr, "formulaExpression") or ""
                # IF(cond, "...", "...") with quoted strings on both branches
                if re.search(r'IF\s*\([^,]+,\s*"[^"]*"\s*,\s*"[^"]*"\s*\)', expr):
                    issues.append(
                        f"{path}: screen `{sname}` field `{fname}` validation formula "
                        f"appears to return Text, not BOOLEAN. The formula must return "
                        f"TRUE/FALSE; put the user-facing string in `<errorMessage>`."
                    )
                # IF(cond, TRUE, FALSE) redundancy
                if re.search(r'IF\s*\([^,]+,\s*TRUE\s*,\s*FALSE\s*\)', expr, re.IGNORECASE):
                    issues.append(
                        f"{path}: screen `{sname}` field `{fname}` uses "
                        f"`IF(cond, TRUE, FALSE)` — use the boolean expression directly."
                    )

    # Anti-pattern: Decision after a screen referencing that screen's variables
    # and looping back to the same screen on the default branch
    for decision in _children(root, "decisions"):
        dname = _child_text(decision, "name") or "<unnamed-decision>"
        # find which screen connects into this decision
        source_screen = None
        for sname, target in screen_next_targets.items():
            if target == dname:
                source_screen = sname
                break
        if source_screen is None:
            continue

        default_connector = next(
            (c for c in decision if _strip_ns(c.tag) == "defaultConnector"), None
        )
        default_target = (
            _child_text(default_connector, "targetReference") if default_connector is not None else None
        )

        # check rules reference variables from the source screen
        screen_vars = screen_to_vars.get(source_screen, set())
        references_screen_var = False
        for rule in _children(decision, "rules"):
            for cond in _children(rule, "conditions"):
                lvr = _child_text(cond, "leftValueReference") or ""
                if any(v in lvr for v in screen_vars):
                    references_screen_var = True
                    break
            if references_screen_var:
                break

        if references_screen_var and default_target == source_screen:
            issues.append(
                f"{path}: decision `{dname}` after screen `{source_screen}` validates "
                f"that screen's inputs and loops back on failure — bad UX. Move the "
                f"check to a `<validationRule>` on the input field."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ERROR: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    flow_files = _find_flow_files(manifest_dir)
    if not flow_files:
        print(f"No .flow / .flow-meta.xml files found under {manifest_dir}.")
        return 0

    all_issues: list[str] = []
    for flow_file in flow_files:
        all_issues.extend(_audit_flow(flow_file))

    if not all_issues:
        print(f"OK — no screen-flow input-validation anti-patterns found in {len(flow_files)} flow file(s).")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    print(f"\nFound {len(all_issues)} issue(s) across {len(flow_files)} flow file(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
