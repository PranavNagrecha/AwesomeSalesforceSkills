#!/usr/bin/env python3
"""Checker script for IP Range and Login Flow Strategy skill.

Scans a Salesforce metadata directory for Login Flow-related configuration
issues: flow type mismatches, missing fault handlers, hardcoded IPs in
flow formulas, and Login Flow assignment gaps.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_ip_range_and_login_flow_strategy.py [--help]
    python3 check_ip_range_and_login_flow_strategy.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Login Flow configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_files(root: Path, suffix: str) -> list[Path]:
    """Recursively find files matching a suffix."""
    matches: list[Path] = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.endswith(suffix):
                matches.append(Path(dirpath) / f)
    return matches


def strip_ns(tag: str) -> str:
    """Remove XML namespace prefix from a tag."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def check_flow_files(manifest_dir: Path) -> list[str]:
    """Check .flow-meta.xml files for Login Flow anti-patterns."""
    issues: list[str] = []
    flow_files = find_files(manifest_dir, ".flow-meta.xml")

    if not flow_files:
        return issues  # No flow metadata to check — not necessarily an issue

    # Patterns that suggest a flow is used as a Login Flow
    login_flow_indicators = [
        "LoginFlow",
        "login_flow",
        "loginflow",
        "Login_Flow",
        "PostAuth",
        "post_auth",
    ]

    ip_hardcode_pattern = re.compile(
        r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
    )

    for flow_file in flow_files:
        flow_name = flow_file.stem.replace(".flow-meta", "")
        is_login_flow_candidate = any(
            ind.lower() in flow_name.lower() for ind in login_flow_indicators
        )

        try:
            tree = ET.parse(flow_file)
            root = tree.getroot()
        except ET.ParseError:
            issues.append(f"{flow_file.name}: XML parse error — cannot validate")
            continue

        # Check flow type
        process_type_el = root.find(".//{*}processType")
        if process_type_el is not None and is_login_flow_candidate:
            ptype = process_type_el.text or ""
            if ptype not in ("Flow",):
                # "Flow" is the processType for Screen Flows
                issues.append(
                    f"{flow_name}: appears to be a Login Flow but processType "
                    f"is '{ptype}' — Login Flows must be Screen Flows (processType=Flow)"
                )

        # Check for hardcoded IPs in formula elements
        for formula_el in root.iter():
            tag = strip_ns(formula_el.tag)
            if tag in ("formula", "value", "stringValue", "expression"):
                text = formula_el.text or ""
                if ip_hardcode_pattern.search(text) and is_login_flow_candidate:
                    issues.append(
                        f"{flow_name}: hardcoded IP address found in {tag} element — "
                        "store IP ranges in Custom Metadata instead of flow formulas"
                    )

        # Check for Apex Action elements without fault connectors
        if is_login_flow_candidate:
            action_calls = [
                el for el in root.iter()
                if strip_ns(el.tag) == "actionCalls"
            ]
            for action in action_calls:
                action_name_el = action.find("{*}name") or action.find("name")
                action_label = (
                    action_name_el.text if action_name_el is not None else "unnamed"
                )
                # Check for faultConnector child
                fault_connector = action.find("{*}faultConnector") or action.find(
                    "faultConnector"
                )
                if fault_connector is None:
                    issues.append(
                        f"{flow_name}: Apex Action '{action_label}' has no fault "
                        "connector — unhandled faults in Login Flows block user login"
                    )

    return issues


def check_profile_files(manifest_dir: Path) -> list[str]:
    """Check .profile-meta.xml files for Login Flow assignment indicators."""
    issues: list[str] = []
    profile_files = find_files(manifest_dir, ".profile-meta.xml")

    # This is informational — we flag profiles that have loginFlows element
    # but note that Login Flow assignment is typically in LoginFlow metadata
    for pf in profile_files:
        profile_name = pf.stem.replace(".profile-meta", "")
        try:
            tree = ET.parse(pf)
            root = tree.getroot()
        except ET.ParseError:
            continue

        # Check for loginIpRanges combined with Login Flow references
        login_ip_ranges = [
            el for el in root.iter() if strip_ns(el.tag) == "loginIpRanges"
        ]
        if login_ip_ranges:
            # Informational: profile has Login IP Ranges — make sure the
            # practitioner knows Login Flows do NOT replace these
            pass  # Not flagged as issue — just context

    return issues


def check_apex_classes(manifest_dir: Path) -> list[str]:
    """Check Apex classes for Login Flow anti-patterns."""
    issues: list[str] = []
    cls_files = find_files(manifest_dir, ".cls")

    userinfo_pattern = re.compile(r"UserInfo\s*\.\s*getUserId\s*\(\s*\)")
    invocable_pattern = re.compile(r"@InvocableMethod")
    login_flow_pattern = re.compile(
        r"(LoginFlow|login_flow|loginflow|Login_Flow|SessionManagement)",
        re.IGNORECASE,
    )

    for cls_file in cls_files:
        try:
            content = cls_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Only check classes that appear related to Login Flows
        if not login_flow_pattern.search(content):
            continue

        if invocable_pattern.search(content) and userinfo_pattern.search(content):
            issues.append(
                f"{cls_file.name}: uses UserInfo.getUserId() in a Login Flow "
                "Invocable — this returns the Login Flow User ID, not the "
                "authenticating user. Pass $Flow.LoginFlow_UserId as a parameter instead."
            )

    return issues


def check_ip_range_and_login_flow_strategy(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_flow_files(manifest_dir))
    issues.extend(check_profile_files(manifest_dir))
    issues.extend(check_apex_classes(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_ip_range_and_login_flow_strategy(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
