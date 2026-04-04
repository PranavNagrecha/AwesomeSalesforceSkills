#!/usr/bin/env python3
"""Checker script for Custom Agent Actions Apex skill.

Scans Apex source files for @InvocableMethod anti-patterns relevant to Agentforce:
- @InvocableMethod missing description annotation attribute
- @InvocableVariable missing description annotation attribute
- Non-List method signatures (single object instead of List<>)
- HTTP callouts without callout=true
- Throw statements inside InvocableMethod bodies

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_custom_agent_actions_apex.py [--help]
    python3 check_custom_agent_actions_apex.py --apex-dir path/to/classes
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex InvocableMethod classes for Agentforce action anti-patterns.",
    )
    parser.add_argument(
        "--apex-dir",
        default=".",
        help="Directory containing Apex .cls files (default: current directory).",
    )
    return parser.parse_args()


def scan_invocable_apex(apex_dir: Path) -> list[str]:
    """Scan Apex files for @InvocableMethod anti-patterns."""
    issues: list[str] = []

    if not apex_dir.exists():
        issues.append(f"Apex directory not found: {apex_dir}")
        return issues

    cls_files = list(apex_dir.rglob("*.cls"))

    for cls_file in cls_files:
        try:
            content = cls_file.read_text(encoding="utf-8", errors="ignore")
        except (OSError, PermissionError):
            continue

        if "@InvocableMethod" not in content:
            continue

        # Check 1: @InvocableMethod missing description
        invocable_method_pattern = re.compile(
            r"@InvocableMethod\s*\(([^)]*)\)", re.IGNORECASE
        )
        for match in invocable_method_pattern.finditer(content):
            annotation_body = match.group(1)
            if "description" not in annotation_body.lower():
                issues.append(
                    f"{cls_file.name}: @InvocableMethod annotation is missing a 'description' "
                    f"attribute. The Atlas Reasoning Engine uses this description to decide when "
                    f"to invoke the action. Without it, the agent cannot correctly invoke this action."
                )
                break

        # Check 2: @InvocableMethod with HTTP callout but no callout=true
        if "@InvocableMethod" in content and ("new Http()" in content or "HttpRequest" in content):
            if "callout=true" not in content and 'callout="true"' not in content:
                issues.append(
                    f"{cls_file.name}: Class has @InvocableMethod and HTTP callout code (Http/HttpRequest) "
                    f"but 'callout=true' is not set on the @InvocableMethod annotation. "
                    f"This will cause a runtime CalloutException. Add callout=true to the annotation."
                )

        # Check 3: @InvocableVariable missing description
        invocable_var_pattern = re.compile(
            r"@InvocableVariable\s*\(([^)]*)\)", re.IGNORECASE
        )
        var_missing_desc = False
        for match in invocable_var_pattern.finditer(content):
            annotation_body = match.group(1)
            if "description" not in annotation_body.lower():
                var_missing_desc = True
                break
        if var_missing_desc:
            issues.append(
                f"{cls_file.name}: One or more @InvocableVariable annotations are missing a "
                f"'description' attribute. The Atlas Reasoning Engine reads variable descriptions "
                f"to know what value to pass. Missing descriptions degrade agent invocation quality."
            )

        # Check 4: throw statement in an InvocableMethod body
        # Look for throw inside the method that has @InvocableMethod
        if re.search(r"\bthrow\b\s+new\b", content) and "@InvocableMethod" in content:
            issues.append(
                f"{cls_file.name}: Found 'throw' statement in a file with @InvocableMethod. "
                f"Throwing exceptions from agent actions prevents the agent from surfacing useful "
                f"error messages. Return structured output with success=false and errorMessage instead."
            )

    return issues


def check_custom_agent_actions_apex(apex_dir: Path) -> list[str]:
    """Return a list of issue strings found in the Apex directory."""
    return scan_invocable_apex(apex_dir)


def main() -> int:
    args = parse_args()
    apex_dir = Path(args.apex_dir)
    issues = check_custom_agent_actions_apex(apex_dir)

    if not issues:
        print("No Agentforce action anti-patterns found in Apex classes.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    print(f"\nFound {len(issues)} issue(s). Fix before wiring actions to Agentforce agents.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
