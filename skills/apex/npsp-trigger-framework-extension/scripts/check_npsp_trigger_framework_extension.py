#!/usr/bin/env python3
"""Checker script for NPSP Trigger Framework Extension (TDTM) skill.

Checks Salesforce metadata for common TDTM anti-patterns:
- Custom Apex classes extending npsp.TDTM_Runnable that issue direct DML inside run()
- Trigger_Handler__c data files missing npsp__Owned_by_Namespace__c
- Test classes calling getTdtmConfig() before setTdtmConfig()
- Handler classes returning null instead of an empty DmlWrapper
- npsp__Class__c values that include an npsp. namespace prefix (likely wrong)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_npsp_trigger_framework_extension.py --manifest-dir path/to/metadata
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
            "Check Salesforce metadata for NPSP TDTM anti-patterns "
            "(direct DML in run(), missing Owned_by_Namespace__c, getTdtmConfig bug, etc.)"
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Apex class checks
# ---------------------------------------------------------------------------

_TDTM_CLASS_RE = re.compile(r"extends\s+npsp\.TDTM_Runnable", re.IGNORECASE)
_RUN_METHOD_START_RE = re.compile(
    r"public\s+override\s+npsp\.TDTM_Runnable\.DmlWrapper\s+run\s*\(", re.IGNORECASE
)
_DIRECT_DML_RE = re.compile(r"\b(insert|update|delete|upsert)\s+\w", re.IGNORECASE)
_RETURN_NULL_RE = re.compile(r"\breturn\s+null\s*;")
_GET_TDTM_RE = re.compile(r"getTdtmConfig\s*\(")
_SET_TDTM_RE = re.compile(r"setTdtmConfig\s*\(")
_NPSP_CLASS_PREFIX_RE = re.compile(r"npsp__Class__c\s*=\s*['\"]npsp\.", re.IGNORECASE)


def _extract_run_method_body(source: str) -> str:
    """Return the approximate body of the run() method (heuristic brace counting)."""
    match = _RUN_METHOD_START_RE.search(source)
    if not match:
        return ""
    start = match.start()
    depth = 0
    in_method = False
    body_chars: list[str] = []
    for ch in source[start:]:
        if ch == "{":
            depth += 1
            in_method = True
        elif ch == "}":
            depth -= 1
            if in_method and depth == 0:
                break
        if in_method:
            body_chars.append(ch)
    return "".join(body_chars)


def check_apex_classes(manifest_dir: Path) -> list[str]:
    """Check Apex classes under classes/ for TDTM anti-patterns."""
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.exists():
        classes_dir = manifest_dir  # fallback: search entire manifest dir

    apex_files = list(classes_dir.rglob("*.cls"))
    if not apex_files:
        return issues

    for apex_file in apex_files:
        try:
            source = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if not _TDTM_CLASS_RE.search(source):
            continue  # not a TDTM handler

        rel = apex_file.relative_to(manifest_dir)

        # Check 1: direct DML inside run() body
        run_body = _extract_run_method_body(source)
        if run_body:
            # Strip single-line comments before checking
            run_body_no_comments = re.sub(r"//[^\n]*", "", run_body)
            # Strip block comments
            run_body_no_comments = re.sub(r"/\*.*?\*/", "", run_body_no_comments, flags=re.DOTALL)
            for dml_match in _DIRECT_DML_RE.finditer(run_body_no_comments):
                keyword = dml_match.group(1).lower()
                issues.append(
                    f"{rel}: Direct DML '{keyword}' found inside run() method body. "
                    "Use DmlWrapper.objectsToInsert/Update/Delete instead."
                )

        # Check 2: return null inside run() body
        if run_body and _RETURN_NULL_RE.search(run_body):
            issues.append(
                f"{rel}: 'return null;' found inside run() method. "
                "Always return a DmlWrapper instance (even if empty)."
            )

        # Check 3: test class calls getTdtmConfig() before setTdtmConfig()
        if "@isTest" in source or "testSetup" in source:
            get_match = _GET_TDTM_RE.search(source)
            set_match = _SET_TDTM_RE.search(source)
            if get_match and set_match and get_match.start() < set_match.start():
                issues.append(
                    f"{rel}: getTdtmConfig() called before setTdtmConfig() in test context. "
                    "This causes a static cache bug that silently drops custom handlers. "
                    "Build the handler list from scratch and pass directly to setTdtmConfig()."
                )

        # Check 4: npsp__Class__c with npsp. prefix (likely wrong for custom classes)
        if _NPSP_CLASS_PREFIX_RE.search(source):
            issues.append(
                f"{rel}: npsp__Class__c value appears to include an 'npsp.' namespace prefix. "
                "Custom classes in subscriber orgs should not include this prefix."
            )

    return issues


# ---------------------------------------------------------------------------
# Data file checks (handler registration records)
# ---------------------------------------------------------------------------

def check_handler_data_files(manifest_dir: Path) -> list[str]:
    """Check CSV or XML data files that may contain Trigger_Handler__c records."""
    issues: list[str] = []

    # Look for CSV files that might be Trigger_Handler data exports
    for csv_file in manifest_dir.rglob("*Trigger_Handler*.csv"):
        try:
            content = csv_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel = csv_file.relative_to(manifest_dir)

        # Check for missing Owned_by_Namespace__c column
        header_line = content.splitlines()[0] if content.strip() else ""
        if "Owned_by_Namespace" not in header_line and header_line:
            issues.append(
                f"{rel}: CSV data file for Trigger_Handler__c does not include "
                "npsp__Owned_by_Namespace__c column. Records without this field "
                "may be deleted on next NPSP upgrade."
            )

        # Check for rows with npsp. prefix in class name column
        if re.search(r",npsp\.[A-Z][^,\n]+,", content):
            issues.append(
                f"{rel}: Possible 'npsp.' namespace prefix on a class name value in "
                "Trigger_Handler__c data file. Custom class names should not include this prefix."
            )

    return issues


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def check_npsp_trigger_framework_extension(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_apex_classes(manifest_dir))
    issues.extend(check_handler_data_files(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_npsp_trigger_framework_extension(manifest_dir)

    if not issues:
        print("No NPSP TDTM issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
