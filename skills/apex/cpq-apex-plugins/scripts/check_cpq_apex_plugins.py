#!/usr/bin/env python3
"""Checker script for CPQ Apex Plugins skill.

Scans a Salesforce metadata directory for common anti-patterns related to
CPQ plugin implementation. Uses stdlib only — no pip dependencies.

Usage:
    python3 check_cpq_apex_plugins.py [--help]
    python3 check_cpq_apex_plugins.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for CPQ plugin anti-patterns. "
            "Reports issues with Apex plugin class declarations, JS QCP hooks, "
            "and Apex triggers on CPQ objects."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------

def check_apex_triggers_on_cpq_objects(manifest_dir: Path) -> list[str]:
    """Detect Apex triggers on SBQQ__Quote__c or SBQQ__QuoteLine__c.

    Triggers on CPQ-owned objects that modify calculation fields conflict with
    CPQ's multi-pass calculation engine and silently lose their changes.
    """
    issues: list[str] = []
    trigger_pattern = re.compile(
        r"trigger\s+\w+\s+on\s+SBQQ__(Quote|QuoteLine)__c",
        re.IGNORECASE,
    )
    price_field_pattern = re.compile(
        r"SBQQ__(CustomerPrice|NetPrice|RegularPrice|SpecialPrice|Discount|"
        r"UnitPrice|ListPrice|PartnerPrice|ProratedListPrice)__c",
    )

    for apex_file in manifest_dir.rglob("*.trigger"):
        content = apex_file.read_text(encoding="utf-8", errors="replace")
        rel = apex_file.relative_to(manifest_dir)
        if trigger_pattern.search(content):
            if price_field_pattern.search(content):
                issues.append(
                    f"{rel}: Apex trigger on SBQQ CPQ object modifies a price field "
                    "owned by the CPQ calculation engine — use a CPQ plugin hook instead "
                    "(references/llm-anti-patterns.md Anti-Pattern 1)"
                )
            else:
                issues.append(
                    f"{rel}: Apex trigger on SBQQ__Quote__c or SBQQ__QuoteLine__c — "
                    "verify this does not modify calculation fields; "
                    "prefer CPQ plugin hooks for any pricing logic"
                )
    return issues


def check_apex_plugin_class_visibility(manifest_dir: Path) -> list[str]:
    """Detect Apex classes implementing SBQQ interfaces that are not declared global.

    Managed-package interface implementations must be `global` to be callable
    from the SBQQ namespace at runtime. `public` classes compile but fail at runtime.
    """
    issues: list[str] = []
    # Match 'public class Foo implements SBQQ.<something>'
    public_implements_pattern = re.compile(
        r"\bpublic\s+(?:(?:abstract|virtual|with\s+sharing|without\s+sharing)\s+)*"
        r"class\s+\w+\s+implements\s+SBQQ\.",
        re.IGNORECASE,
    )
    # Also catch public methods inside a class that implements SBQQ interfaces
    sbqq_implements_in_file = re.compile(r"implements\s+SBQQ\.", re.IGNORECASE)

    for apex_file in manifest_dir.rglob("*.cls"):
        content = apex_file.read_text(encoding="utf-8", errors="replace")
        rel = apex_file.relative_to(manifest_dir)

        if sbqq_implements_in_file.search(content):
            if public_implements_pattern.search(content):
                issues.append(
                    f"{rel}: class implements SBQQ interface but is declared `public` — "
                    "must be `global` for cross-namespace instantiation at runtime "
                    "(references/llm-anti-patterns.md Anti-Pattern 3)"
                )
            # Check for public method overrides inside an SBQQ-implementing class
            public_method_pattern = re.compile(
                r"\bpublic\s+(?:override\s+)?void\s+(?:on(?:Before|After)Insert"
                r"|calculate|search|initialize)\b",
                re.IGNORECASE,
            )
            if public_method_pattern.search(content):
                issues.append(
                    f"{rel}: implements SBQQ interface but has `public` method overrides — "
                    "interface methods must be `global` to be callable from the SBQQ namespace"
                )
    return issues


def check_soql_in_plugin_loops(manifest_dir: Path) -> list[str]:
    """Detect SOQL queries inside for-loop bodies in CPQ plugin classes.

    N+1 SOQL patterns in plugin methods cause governor limit failures on
    quotes with more than a handful of lines.
    """
    issues: list[str] = []
    sbqq_implements_pattern = re.compile(r"implements\s+SBQQ\.", re.IGNORECASE)

    # Heuristic: look for [ SELECT inside a for ( loop block
    # This is a simplified scan — not a full AST parser
    soql_in_loop_pattern = re.compile(
        r"for\s*\([^)]+\)\s*\{[^}]*\[\s*SELECT",
        re.DOTALL | re.IGNORECASE,
    )

    for apex_file in manifest_dir.rglob("*.cls"):
        content = apex_file.read_text(encoding="utf-8", errors="replace")
        rel = apex_file.relative_to(manifest_dir)

        if sbqq_implements_pattern.search(content):
            if soql_in_loop_pattern.search(content):
                issues.append(
                    f"{rel}: SOQL query detected inside a for-loop in a CPQ plugin class — "
                    "bulk-collect IDs before the loop and use a Map for O(1) lookups "
                    "(references/llm-anti-patterns.md Anti-Pattern 5)"
                )
    return issues


def check_js_qcp_missing_promise_return(manifest_dir: Path) -> list[str]:
    """Detect JS QCP files where hook functions may not return a Promise.

    A JS QCP hook that returns undefined causes the CPQ calculation engine
    to hang indefinitely on quote save.
    """
    issues: list[str] = []
    # JS QCP files may have .js extension or be embedded; look for exported hook names
    hook_names = [
        "onInit", "onBeforeCalculate", "onAfterCalculate",
        "onBeforePriceRules", "onAfterPriceRules",
        "onBeforeCalculatePrices", "onAfterCalculatePrices",
    ]
    hook_export_pattern = re.compile(
        r"export\s+function\s+(" + "|".join(hook_names) + r")\s*\(",
        re.IGNORECASE,
    )
    # A bare `return;` or `return null;` or `return undefined;` inside a hook body
    bare_return_pattern = re.compile(
        r"return\s*(?:null|undefined|;|\n)",
    )

    for js_file in manifest_dir.rglob("*.js"):
        content = js_file.read_text(encoding="utf-8", errors="replace")
        rel = js_file.relative_to(manifest_dir)

        if hook_export_pattern.search(content):
            # This is likely a JS QCP file
            if bare_return_pattern.search(content):
                issues.append(
                    f"{rel}: JS QCP file contains a bare `return;`, `return null;`, or "
                    "`return undefined;` — every hook function must return a resolved Promise "
                    "in every code branch to avoid freezing the CPQ calculator "
                    "(references/llm-anti-patterns.md Anti-Pattern 4)"
                )

            # Check if any exported hook is missing a Promise.resolve() return entirely
            for hook in hook_names:
                fn_pattern = re.compile(
                    rf"export\s+function\s+{hook}\s*\([^)]*\)\s*\{{([^}}]*(?:\{{[^}}]*\}}[^}}]*)*)\}}",
                    re.DOTALL,
                )
                match = fn_pattern.search(content)
                if match:
                    body = match.group(1)
                    if "Promise" not in body:
                        issues.append(
                            f"{rel}: JS QCP hook `{hook}` does not appear to return a Promise — "
                            "add `return Promise.resolve()` at the end of every code path "
                            "(references/llm-anti-patterns.md Anti-Pattern 4)"
                        )
    return issues


def check_dual_calculator_plugin_registration(manifest_dir: Path) -> list[str]:
    """Warn if both Apex QuoteCalculatorPlugin and JS QCP patterns appear in the same codebase.

    Only one calculator plugin type can be active at a time. Having both
    is a likely configuration conflict.
    """
    issues: list[str] = []
    apex_calc_pattern = re.compile(
        r"implements\s+SBQQ\.QuoteCalculatorPlugin", re.IGNORECASE
    )
    js_qcp_hook_pattern = re.compile(
        r"export\s+function\s+(?:onInit|onBeforeCalculate|onAfterCalculate)",
        re.IGNORECASE,
    )

    has_apex_calc = False
    has_js_qcp = False

    for apex_file in manifest_dir.rglob("*.cls"):
        content = apex_file.read_text(encoding="utf-8", errors="replace")
        if apex_calc_pattern.search(content):
            has_apex_calc = True
            break

    for js_file in manifest_dir.rglob("*.js"):
        content = js_file.read_text(encoding="utf-8", errors="replace")
        if js_qcp_hook_pattern.search(content):
            has_js_qcp = True
            break

    if has_apex_calc and has_js_qcp:
        issues.append(
            "Both an Apex QuoteCalculatorPlugin class and a JS QCP (JavaScript) hook file "
            "are present in this metadata tree. Only one calculator plugin type can be active "
            "at a time — verify that only one is registered/active in CPQ Settings "
            "(references/llm-anti-patterns.md Anti-Pattern 2)"
        )
    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_cpq_apex_plugins(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_apex_triggers_on_cpq_objects(manifest_dir))
    issues.extend(check_apex_plugin_class_visibility(manifest_dir))
    issues.extend(check_soql_in_plugin_loops(manifest_dir))
    issues.extend(check_js_qcp_missing_promise_return(manifest_dir))
    issues.extend(check_dual_calculator_plugin_registration(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_cpq_apex_plugins(manifest_dir)

    if not issues:
        print("No CPQ plugin issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
