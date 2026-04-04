#!/usr/bin/env python3
"""Checker script for LWC Imperative Apex skill.

Scans a Salesforce metadata directory for common issues in LWC components
that call Apex imperatively:

  1. LWC JS files that import from '@salesforce/apex' but lack error handling
     (.catch or try/catch) near the call site.
  2. Apex classes exposed with @AuraEnabled that use 'without sharing' — a
     security risk for components callable by guest or community users.
  3. LWC JS files that reference 'refreshApex' alongside an imperative Apex
     import but appear to apply it to an imperatively populated variable
     (heuristic: refreshApex called but no @wire decorator present).

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_lwc_imperative_apex.py [--help]
    python3 check_lwc_imperative_apex.py --manifest-dir path/to/metadata
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
            "Check LWC components and Apex classes for common imperative-Apex "
            "anti-patterns (stdlib only)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_lwc_missing_error_handling(lwc_root: Path) -> list[str]:
    """Warn when a LWC JS file imports from @salesforce/apex but has no
    .catch() call and no try/catch block anywhere in the file.

    This is a heuristic: it does not parse the AST, so it will miss
    error handling inside utility modules or components that delegate
    to a parent. Treat findings as review prompts, not definitive errors.
    """
    issues: list[str] = []
    apex_import_re = re.compile(r"from\s+['\"]@salesforce/apex/")

    for js_file in lwc_root.rglob("*.js"):
        try:
            content = js_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if not apex_import_re.search(content):
            continue

        has_catch = ".catch(" in content
        has_try_catch = "try {" in content or "try{" in content

        if not (has_catch or has_try_catch):
            issues.append(
                f"[LWC missing error handling] {js_file}: imports @salesforce/apex "
                "but has no .catch() or try/catch block. All imperative Apex calls "
                "must handle errors to avoid silent failures."
            )

    return issues


def check_apex_without_sharing(apex_root: Path) -> list[str]:
    """Flag Apex classes that are AuraEnabled-accessible and declared
    'without sharing', which bypasses record-level security for LWC callers.
    """
    issues: list[str] = []
    without_sharing_re = re.compile(r"\bwithout\s+sharing\b", re.IGNORECASE)
    aura_enabled_re = re.compile(r"@AuraEnabled", re.IGNORECASE)
    class_decl_re = re.compile(
        r"\bclass\b\s+\w+.*?\bwithout\s+sharing\b", re.IGNORECASE
    )

    for cls_file in apex_root.rglob("*.cls"):
        try:
            content = cls_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if not aura_enabled_re.search(content):
            continue

        if without_sharing_re.search(content) and class_decl_re.search(content):
            issues.append(
                f"[Apex without sharing + AuraEnabled] {cls_file}: class has "
                "'without sharing' and exposes @AuraEnabled methods. "
                "Guest and community users calling this LWC can bypass "
                "record-level security. Use 'with sharing' or 'inherited sharing'."
            )

    return issues


def check_refreshapex_on_imperative(lwc_root: Path) -> list[str]:
    """Warn when a LWC JS file imports refreshApex and also imports from
    @salesforce/apex, but appears to have no @wire decorator — suggesting
    refreshApex may be applied to an imperatively populated variable.

    refreshApex() silently does nothing on imperative results.
    """
    issues: list[str] = []
    refresh_import_re = re.compile(r"\brefreshApex\b")
    apex_import_re = re.compile(r"from\s+['\"]@salesforce/apex/")
    wire_re = re.compile(r"@wire\b")

    for js_file in lwc_root.rglob("*.js"):
        try:
            content = js_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        has_refresh_apex = refresh_import_re.search(content)
        has_apex_import = apex_import_re.search(content)

        if not (has_refresh_apex and has_apex_import):
            continue

        has_wire = wire_re.search(content)
        if not has_wire:
            issues.append(
                f"[refreshApex without @wire] {js_file}: uses refreshApex() and "
                "imports from @salesforce/apex but has no @wire decorator. "
                "refreshApex() only works with wire-provisioned values. "
                "To refresh imperative data, re-call the Apex method directly."
            )

    return issues


def check_apex_cacheable_with_dml_hint(apex_root: Path) -> list[str]:
    """Heuristic: flag Apex methods annotated cacheable=true that also
    contain DML keywords (insert/update/upsert/delete/merge) in the same
    class body. This is not a definitive check — DML in a helper invoked
    by a cacheable method also triggers a runtime error — but it catches
    the most obvious violations.
    """
    issues: list[str] = []
    cacheable_re = re.compile(r"@AuraEnabled\s*\(\s*cacheable\s*=\s*true\s*\)", re.IGNORECASE)
    dml_re = re.compile(r"\b(insert|update|upsert|delete|merge)\b\s+\w+", re.IGNORECASE)

    for cls_file in apex_root.rglob("*.cls"):
        try:
            content = cls_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if not cacheable_re.search(content):
            continue

        dml_matches = dml_re.findall(content)
        if dml_matches:
            issues.append(
                f"[cacheable=true with DML hint] {cls_file}: has "
                "@AuraEnabled(cacheable=true) and DML keywords in the class body "
                f"({', '.join(set(m[0].lower() for m in dml_re.finditer(content)))}). "
                "Salesforce throws a runtime error if a cacheable method performs DML. "
                "Verify that all @AuraEnabled(cacheable=true) methods are truly read-only."
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_lwc_imperative_apex(manifest_dir: Path) -> list[str]:
    """Run all checks and return a flat list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Locate standard SFDX layout paths; fall back to root if not found.
    lwc_root = manifest_dir / "force-app" / "main" / "default" / "lwc"
    if not lwc_root.exists():
        lwc_root = manifest_dir

    apex_root = manifest_dir / "force-app" / "main" / "default" / "classes"
    if not apex_root.exists():
        apex_root = manifest_dir

    issues.extend(check_lwc_missing_error_handling(lwc_root))
    issues.extend(check_apex_without_sharing(apex_root))
    issues.extend(check_refreshapex_on_imperative(lwc_root))
    issues.extend(check_apex_cacheable_with_dml_hint(apex_root))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_lwc_imperative_apex(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
