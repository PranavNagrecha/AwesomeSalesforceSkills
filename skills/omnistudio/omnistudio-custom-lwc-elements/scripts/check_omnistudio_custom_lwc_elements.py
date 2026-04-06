#!/usr/bin/env python3
"""Checker script for OmniStudio Custom LWC Elements skill.

Inspects LWC component source files in a Salesforce metadata directory and
flags common issues specific to custom OmniScript elements:

  - Missing @api omniJsonData or @api omniOutputMap declarations
  - Missing connectedCallback or disconnectedCallback lifecycle hooks
  - Use of @wire adapters inside custom OmniScript elements
  - Missing omniOutputMap argument in pubsub.fireEvent calls
  - omniscriptvalidate listener registered without matching unregisterListener
  - Pubsub import from the wrong namespace (both paths in the same file)
  - dispatchEvent used instead of pubsub.fireEvent for OmniScript communication
  - Direct mutation of omniJsonData

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omnistudio_custom_lwc_elements.py [--help]
    python3 check_omnistudio_custom_lwc_elements.py --manifest-dir path/to/metadata
    python3 check_omnistudio_custom_lwc_elements.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check LWC source files for common OmniStudio custom element issues: "
            "missing lifecycle hooks, incorrect pubsub patterns, wire adapter usage, "
            "and namespace mismatches."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_js_files(root: Path) -> list[Path]:
    """Return all .js files under root that are likely LWC controllers."""
    return [
        p for p in root.rglob("*.js")
        if not p.name.endswith(".test.js") and "__tests__" not in str(p)
    ]


def is_omniscript_element(content: str) -> bool:
    """Return True if the file looks like a custom OmniScript element LWC.

    Heuristic: declares @api omniJsonData or @api omniOutputMap, or imports
    a pubsub module from omnistudio or vlocity_cmt namespaces.
    """
    markers = [
        r"@api\s+omniJsonData",
        r"@api\s+omniOutputMap",
        r"from\s+['\"]omnistudio/pubsub['\"]",
        r"from\s+['\"]vlocity_cmt/pubsub['\"]",
        r"from\s+['\"]vlocity_ins/pubsub['\"]",
        r"from\s+['\"]vlocity_ps/pubsub['\"]",
    ]
    return any(re.search(m, content) for m in markers)


def check_file(path: Path) -> list[str]:
    """Run all checks on a single JavaScript file. Returns a list of issue strings."""
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"{path}: cannot read file — {exc}"]

    if not is_omniscript_element(content):
        return []  # Not a custom OmniScript element — skip

    issues: list[str] = []
    name = str(path)

    # --- 1. Missing @api declarations ---
    if not re.search(r"@api\s+omniJsonData", content):
        issues.append(
            f"{name}: missing '@api omniJsonData' — the OmniScript runtime "
            "passes script data through this property; it must be an @api property."
        )

    if not re.search(r"@api\s+omniOutputMap", content):
        issues.append(
            f"{name}: missing '@api omniOutputMap' — required as the first "
            "argument to pubsub.fireEvent to scope events to this OmniScript instance."
        )

    # --- 2. Missing lifecycle hooks ---
    if not re.search(r"\bconnectedCallback\s*\(", content):
        issues.append(
            f"{name}: missing connectedCallback — custom OmniScript elements must "
            "implement connectedCallback to restore user state when navigating back."
        )

    if not re.search(r"\bdisconnectedCallback\s*\(", content):
        issues.append(
            f"{name}: missing disconnectedCallback — custom OmniScript elements must "
            "implement disconnectedCallback to clean up pubsub listeners."
        )

    # --- 3. @wire adapter usage inside an OmniScript element ---
    if re.search(r"@wire\s*\(", content):
        issues.append(
            f"{name}: @wire adapter detected inside a custom OmniScript element — "
            "wire adapters are unreliable inside the OmniScript step lifecycle. "
            "Use imperative Apex calls in connectedCallback instead."
        )

    # --- 4. pubsub.fireEvent without omniOutputMap as first argument ---
    # Match fireEvent calls where the first argument is a string literal (wrong)
    bad_fire = re.findall(
        r"\.fireEvent\s*\(\s*['\"][^'\"]+['\"]",
        content,
    )
    if bad_fire:
        issues.append(
            f"{name}: pubsub.fireEvent called with a string literal as the first "
            "argument instead of this.omniOutputMap — string channels are not scoped "
            "to this OmniScript instance. Use: "
            "pubsub.fireEvent(this.omniOutputMap, 'omniupdatebyfield', {{ ... }})"
        )

    # --- 5. omniscriptvalidate registered without unregisterListener ---
    registers_validate = bool(re.search(r"registerListener\s*\(\s*['\"]omniscriptvalidate['\"]", content))
    unregisters_validate = bool(re.search(r"unregisterListener\s*\(\s*['\"]omniscriptvalidate['\"]", content))

    if registers_validate and not unregisters_validate:
        issues.append(
            f"{name}: 'omniscriptvalidate' is registered via registerListener but "
            "unregisterListener is not called — listener accumulates on repeated step "
            "navigation, causing unpredictable validation behavior."
        )

    # --- 6. Both pubsub import paths present (namespace mismatch) ---
    has_native_pubsub = bool(re.search(r"from\s+['\"]omnistudio/pubsub['\"]", content))
    has_managed_pubsub = bool(
        re.search(r"from\s+['\"]vlocity_(?:cmt|ins|ps)/pubsub['\"]", content)
    )
    if has_native_pubsub and has_managed_pubsub:
        issues.append(
            f"{name}: both native (omnistudio/pubsub) and managed package "
            "(vlocity_cmt/pubsub) pubsub imports detected in the same file — "
            "only one runtime can be active in the org; remove the incorrect import."
        )

    # --- 7. dispatchEvent used for OmniScript communication ---
    if re.search(r"dispatchEvent\s*\(\s*new\s+CustomEvent", content):
        issues.append(
            f"{name}: CustomEvent dispatchEvent detected — OmniScript does not listen "
            "for DOM custom events from custom elements. Use "
            "pubsub.fireEvent(this.omniOutputMap, 'omniupdatebyfield', {{ ... }}) instead."
        )

    # --- 8. Direct mutation of omniJsonData ---
    if re.search(r"this\.omniJsonData\s*\.", content):
        # Narrow to assignment patterns (not just reads)
        mutations = re.findall(r"this\.omniJsonData(?:\.\w+)+\s*=", content)
        if mutations:
            issues.append(
                f"{name}: direct mutation of omniJsonData detected "
                f"({len(mutations)} assignment(s)) — mutating omniJsonData does not "
                "update the OmniScript data model. Use pubsub.fireEvent with "
                "'omniupdatebyfield' to push values back to OmniScript."
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_manifest(manifest_dir: Path) -> list[str]:
    """Run all checks across JS files in manifest_dir. Returns a flat list of issues."""
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    js_files = find_js_files(manifest_dir)
    if not js_files:
        return [f"No JavaScript files found under: {manifest_dir}"]

    all_issues: list[str] = []
    for js_file in sorted(js_files):
        all_issues.extend(check_file(js_file))

    return all_issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_manifest(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    print(f"\n{len(issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
