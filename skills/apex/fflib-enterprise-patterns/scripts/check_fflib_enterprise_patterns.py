#!/usr/bin/env python3
"""Checker script for fflib Enterprise Patterns skill.

Scans Apex source files for common fflib structural issues:
- Domain classes missing super() constructor calls
- Selectors missing FLS enforcement
- Direct DML outside UnitOfWork patterns
- Missing Application factory registrations
- Triggers with inline logic instead of triggerHandler dispatch

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fflib_enterprise_patterns.py --manifest-dir path/to/force-app/main/default/classes
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check fflib Enterprise Patterns for common structural issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce source (default: current directory).",
    )
    return parser.parse_args()


def find_apex_files(root: Path) -> list[Path]:
    """Recursively find all .cls files."""
    return sorted(root.rglob("*.cls"))


def read_text_safe(path: Path) -> str:
    """Read file text, returning empty string on decode errors."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def check_domain_constructors(files: list[Path]) -> list[str]:
    """Check that Domain classes extending fflib_SObjectDomain call super()."""
    issues: list[str] = []
    extends_re = re.compile(r"extends\s+fflib_SObjectDomain", re.IGNORECASE)
    super_re = re.compile(r"super\s*\(")

    for f in files:
        content = read_text_safe(f)
        if extends_re.search(content) and not super_re.search(content):
            issues.append(
                f"{f.name}: Domain class extends fflib_SObjectDomain but "
                f"no super() call found in constructor"
            )
    return issues


def check_selector_fls(files: list[Path]) -> list[str]:
    """Check that Selector classes override isEnforcingFLS."""
    issues: list[str] = []
    extends_re = re.compile(r"extends\s+fflib_SObjectSelector", re.IGNORECASE)
    fls_re = re.compile(r"isEnforcingFLS\s*\(")

    for f in files:
        content = read_text_safe(f)
        if extends_re.search(content) and not fls_re.search(content):
            issues.append(
                f"{f.name}: Selector extends fflib_SObjectSelector but "
                f"does not override isEnforcingFLS() — FLS is off by default"
            )
    return issues


def check_direct_dml_in_services(files: list[Path]) -> list[str]:
    """Flag direct DML statements in files that look like Service classes."""
    issues: list[str] = []
    dml_re = re.compile(
        r"\b(insert|update|delete|undelete|upsert)\s+[a-zA-Z]",
        re.IGNORECASE,
    )
    service_re = re.compile(r"Service", re.IGNORECASE)
    # Skip test classes
    test_re = re.compile(r"@isTest|testMethod", re.IGNORECASE)

    for f in files:
        if not service_re.search(f.stem):
            continue
        content = read_text_safe(f)
        if test_re.search(content):
            continue
        matches = dml_re.findall(content)
        if matches:
            ops = ", ".join(set(m.lower() for m in matches))
            issues.append(
                f"{f.name}: Service class contains direct DML ({ops}) — "
                f"use UnitOfWork.registerNew/registerDirty/registerDeleted instead"
            )
    return issues


def check_trigger_inline_logic(root: Path) -> list[str]:
    """Check that trigger files delegate to fflib_SObjectDomain.triggerHandler."""
    issues: list[str] = []
    trigger_files = sorted(root.rglob("*.trigger"))
    handler_re = re.compile(r"fflib_SObjectDomain\s*\.\s*triggerHandler")
    # Heuristic: triggers with more than 5 non-blank non-comment lines
    # likely contain inline logic
    for f in trigger_files:
        content = read_text_safe(f)
        lines = [
            ln.strip()
            for ln in content.splitlines()
            if ln.strip() and not ln.strip().startswith("//")
        ]
        if len(lines) > 5 and not handler_re.search(content):
            issues.append(
                f"{f.name}: Trigger has >5 lines of logic without "
                f"fflib_SObjectDomain.triggerHandler — consider using Domain dispatch"
            )
    return issues


def check_application_factory(files: list[Path]) -> list[str]:
    """Check that an Application.cls exists if fflib classes are present."""
    issues: list[str] = []
    has_fflib = any(
        re.search(r"fflib_SObject(Domain|Selector|UnitOfWork)", read_text_safe(f))
        for f in files
    )
    has_application = any(f.stem == "Application" for f in files)

    if has_fflib and not has_application:
        issues.append(
            "fflib layer classes found but no Application.cls factory detected — "
            "create Application.cls with Domain, Selector, Service, and UnitOfWork factories"
        )
    return issues


def check_fflib_enterprise_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = find_apex_files(manifest_dir)

    if not apex_files:
        issues.append(f"No .cls files found under {manifest_dir}")
        return issues

    issues.extend(check_domain_constructors(apex_files))
    issues.extend(check_selector_fls(apex_files))
    issues.extend(check_direct_dml_in_services(apex_files))
    issues.extend(check_trigger_inline_logic(manifest_dir))
    issues.extend(check_application_factory(apex_files))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fflib_enterprise_patterns(manifest_dir)

    if not issues:
        print("No fflib Enterprise Patterns issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
