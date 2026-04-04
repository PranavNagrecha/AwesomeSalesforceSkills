#!/usr/bin/env python3
"""Checker script for LWC in Flow Screens skill.

Scans LWC component source files in a Salesforce metadata directory for the most
common mistakes when building custom flow screen components:

  1. Direct @api mutation (this.propName = value) used instead of FlowAttributeChangeEvent.
  2. Missing lightning__FlowScreen target in the .js-meta.xml configuration file.
  3. Navigation events fired without an availableActions guard.
  4. A validate-like method exists but is not named exactly 'validate'.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_lwc_in_flow_screens.py [--help]
    python3 check_lwc_in_flow_screens.py --manifest-dir path/to/sfdx-project/force-app
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_API_MUTATION_RE = re.compile(
    r"this\.([A-Za-z_]\w*)\s*=",
)
_FLOW_ATTR_CHANGE_RE = re.compile(r"FlowAttributeChangeEvent")
_FLOW_NAV_EVENT_RE = re.compile(
    r"FlowNavigation(Next|Back|Pause|Finish)Event"
)
_AVAILABLE_ACTIONS_RE = re.compile(r"availableActions")
_VALIDATE_LIKE_RE = re.compile(
    r"\b(validate[A-Z]\w*|[a-z]+Validate[A-Z]?\w*)\s*\("
)
_VALIDATE_EXACT_RE = re.compile(r"\bvalidate\s*\(")
_AT_API_PROP_RE = re.compile(r"@api\s+(?:get\s+)?([A-Za-z_]\w*)")


def _find_lwc_dirs(manifest_dir: Path) -> list[Path]:
    """Return paths to all LWC component directories under manifest_dir."""
    return [p.parent for p in manifest_dir.rglob("*.js-meta.xml")]


def _is_flow_screen_component(meta_xml_path: Path) -> bool:
    """Return True if the component declares lightning__FlowScreen as a target."""
    try:
        content = meta_xml_path.read_text(encoding="utf-8")
    except OSError:
        return False
    return "lightning__FlowScreen" in content


def _find_js_file(component_dir: Path) -> Path | None:
    """Return the main JS file for the component, if it exists."""
    name = component_dir.name
    candidate = component_dir / f"{name}.js"
    return candidate if candidate.exists() else None


def _check_component(component_dir: Path) -> list[str]:
    """Run all checks for a single LWC component directory."""
    issues: list[str] = []
    meta_files = list(component_dir.glob("*.js-meta.xml"))
    if not meta_files:
        return issues  # Not an LWC bundle

    meta_path = meta_files[0]

    # Only audit components that target flow screens
    if not _is_flow_screen_component(meta_path):
        return issues

    js_path = _find_js_file(component_dir)
    if js_path is None:
        return issues

    try:
        js_text = js_path.read_text(encoding="utf-8")
    except OSError:
        return issues

    component_label = str(js_path)

    # ------------------------------------------------------------------
    # Check 1: Direct @api mutation
    # Detect this.<propName> = ... where propName is an @api property.
    # This pattern produces no error but silently fails at Flow runtime.
    # ------------------------------------------------------------------
    api_props = set(_AT_API_PROP_RE.findall(js_text))
    uses_flow_attr_change = bool(_FLOW_ATTR_CHANGE_RE.search(js_text))

    if api_props and uses_flow_attr_change:
        # Component is a flow screen and uses FlowAttributeChangeEvent — good.
        # Still look for direct mutation of @api props as a belt-and-suspenders check.
        for match in _API_MUTATION_RE.finditer(js_text):
            prop_name = match.group(1)
            if prop_name in api_props:
                # Exclude 'this.prop = ...' inside a setter (set propName)
                # by checking surrounding lines for 'set propName'
                start = max(0, match.start() - 200)
                snippet = js_text[start : match.start()]
                if not re.search(r"\bset\s+" + re.escape(prop_name), snippet):
                    issues.append(
                        f"{component_label}: possible direct @api mutation of '{prop_name}' — "
                        f"use FlowAttributeChangeEvent('{prop_name}', value) instead."
                    )
    elif api_props and not uses_flow_attr_change:
        # Flow screen component with @api props but no FlowAttributeChangeEvent at all.
        # Check whether any @api prop is assigned from inside the component.
        for match in _API_MUTATION_RE.finditer(js_text):
            prop_name = match.group(1)
            if prop_name in api_props:
                start = max(0, match.start() - 200)
                snippet = js_text[start : match.start()]
                if not re.search(r"\bset\s+" + re.escape(prop_name), snippet):
                    issues.append(
                        f"{component_label}: flow screen component mutates @api property '{prop_name}' "
                        f"directly and never fires FlowAttributeChangeEvent — "
                        f"output values will not reach Flow variables."
                    )

    # ------------------------------------------------------------------
    # Check 2: Navigation events without availableActions guard
    # ------------------------------------------------------------------
    uses_nav_event = bool(_FLOW_NAV_EVENT_RE.search(js_text))
    uses_available_actions_guard = bool(_AVAILABLE_ACTIONS_RE.search(js_text))

    if uses_nav_event and not uses_available_actions_guard:
        issues.append(
            f"{component_label}: fires a FlowNavigation*Event but never checks "
            f"'availableActions' — navigation will silently do nothing if the action "
            f"is not enabled in the flow. Add: if (this.availableActions.includes('NEXT')) {{ ... }}"
        )

    # ------------------------------------------------------------------
    # Check 3: Validate-like method with wrong name
    # ------------------------------------------------------------------
    has_exact_validate = bool(_VALIDATE_EXACT_RE.search(js_text))
    wrong_validate_matches = _VALIDATE_LIKE_RE.findall(js_text)

    if wrong_validate_matches and not has_exact_validate:
        for name in wrong_validate_matches:
            issues.append(
                f"{component_label}: method '{name}(...)' looks like a validation method "
                f"but the Flow runtime only calls a method named exactly 'validate'. "
                f"Rename to 'validate()' or it will never be invoked by the flow."
            )

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check LWC flow screen components for common integration mistakes: "
            "direct @api mutation, missing navigation guards, and misnamed validate methods."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_lwc_in_flow_screens(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found under manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    component_dirs = _find_lwc_dirs(manifest_dir)
    if not component_dirs:
        # No LWC bundles found — not necessarily an error
        return issues

    for comp_dir in component_dirs:
        issues.extend(_check_component(comp_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_lwc_in_flow_screens(manifest_dir)

    if not issues:
        print("No flow screen component issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
