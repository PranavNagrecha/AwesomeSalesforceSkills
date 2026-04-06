#!/usr/bin/env python3
"""Checker script for Callout Limits And Async Patterns skill.

Checks org metadata or configuration relevant to Callout Limits And Async Patterns.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_callout_limits_and_async_patterns.py [--help]
    python3 check_callout_limits_and_async_patterns.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Callout Limits And Async Patterns configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_callout_limits_and_async_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    Checks Apex trigger and class files for DML-before-callout anti-patterns
    and @future methods with sObject-like parameter names.
    """
    import re

    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Find Apex class and trigger directories
    apex_dirs = []
    for base in [
        manifest_dir / "force-app" / "main" / "default",
        manifest_dir / "src",
        manifest_dir,
    ]:
        for sub in ["classes", "triggers"]:
            candidate = base / sub
            if candidate.exists():
                apex_dirs.append(candidate)

    for apex_dir in apex_dirs:
        for cls_file in apex_dir.glob("*.cls"):
            try:
                content = cls_file.read_text(encoding="utf-8", errors="replace")

                # Check for @future(callout=true) with sObject-looking parameter types
                # Pattern: @future(callout=true) followed by method with Account/Contact/etc. param
                future_methods = re.findall(
                    r'@future\s*\(\s*callout\s*=\s*true\s*\)[^}]*?public\s+static\s+\w+\s+\w+\s*\(([^)]+)\)',
                    content, re.DOTALL | re.IGNORECASE
                )
                for params in future_methods:
                    # Check if any param type looks like an sObject (capitalized, not primitive)
                    param_types = re.findall(r'(\w+)\s+\w+(?:,|$)', params)
                    primitives = {'String', 'Integer', 'Long', 'Boolean', 'Double', 'Decimal',
                                  'Id', 'List', 'Set', 'Map', 'void', 'Object'}
                    sobject_params = [p for p in param_types if p not in primitives and p[0].isupper()]
                    if sobject_params:
                        issues.append(
                            f"{cls_file.name}: @future(callout=true) method appears to accept "
                            f"sObject-type parameters ({', '.join(sobject_params)}). "
                            "@future methods cannot accept sObject parameters — use Queueable "
                            "implements Database.AllowsCallouts instead."
                        )

                # Check for Continuation usage outside of @AuraEnabled methods
                if "new Continuation(" in content:
                    is_aura_enabled = "@AuraEnabled" in content
                    is_queueable = "implements Queueable" in content
                    is_batch = "implements Database.Batchable" in content
                    is_future = "@future" in content

                    if is_queueable or is_batch or is_future:
                        issues.append(
                            f"{cls_file.name}: Continuation instantiated in a context that appears "
                            "to be Queueable, Batchable, or @future. Continuation is only valid "
                            "in @AuraEnabled controller methods or Visualforce controllers."
                        )

            except OSError:
                pass

        # Also check trigger files
        for trg_file in apex_dir.glob("*.trigger"):
            try:
                content = trg_file.read_text(encoding="utf-8", errors="replace")

                # Check for HttpRequest in a trigger without Queueable pattern
                has_http = "new Http()" in content or "HttpRequest" in content
                has_queueable = "enqueueJob" in content or "Queueable" in content

                if has_http and not has_queueable:
                    issues.append(
                        f"{trg_file.name}: Trigger appears to make a direct HTTP callout "
                        "without enqueueing a Queueable. If any DML occurs before this callout "
                        "in the same transaction, you will get CalloutException. "
                        "Consider using System.enqueueJob() with a Queueable that implements "
                        "Database.AllowsCallouts."
                    )

            except OSError:
                pass

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_callout_limits_and_async_patterns(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
