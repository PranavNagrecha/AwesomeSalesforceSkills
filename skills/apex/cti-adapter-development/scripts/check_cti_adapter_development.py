#!/usr/bin/env python3
"""Checker script for CTI Adapter Development skill.

Validates callcenter.xml definition files and JavaScript adapter pages
for common Open CTI configuration mistakes described in gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_cti_adapter_development.py [--help]
    python3 check_cti_adapter_development.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Open CTI callcenter.xml files and adapter JavaScript "
            "for common configuration and anti-pattern issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata or project (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_callcenter_xml_files(manifest_dir: Path) -> list[str]:
    """Validate all callcenter.xml files found under manifest_dir."""
    issues: list[str] = []
    xml_files = list(manifest_dir.rglob("callcenter.xml"))

    if not xml_files:
        # Not an error — project may not have a callcenter.xml yet
        return issues

    for xml_file in xml_files:
        try:
            tree = ElementTree.parse(xml_file)
            root = tree.getroot()
        except ElementTree.ParseError as exc:
            issues.append(f"{xml_file}: XML parse error — {exc}")
            continue

        # Check CTIVersion
        cti_version_el = root.find("CTIVersion")
        if cti_version_el is None:
            issues.append(
                f"{xml_file}: Missing <CTIVersion> element. "
                "Must be '4.0' for Lightning Open CTI."
            )
        elif cti_version_el.text and cti_version_el.text.strip() == "3.0":
            issues.append(
                f"{xml_file}: CTIVersion is '3.0' (Classic only). "
                "Set to '4.0' for Lightning Experience — otherwise sforce.opencti "
                "will be undefined in the adapter page."
            )
        elif cti_version_el.text and cti_version_el.text.strip() not in ("4.0",):
            issues.append(
                f"{xml_file}: Unexpected CTIVersion '{cti_version_el.text.strip()}'. "
                "Expected '4.0' for Lightning Open CTI."
            )

        # Check AdapterUrl is HTTPS
        adapter_url_el = root.find("AdapterUrl")
        if adapter_url_el is None:
            issues.append(f"{xml_file}: Missing <AdapterUrl> element.")
        elif adapter_url_el.text:
            url = adapter_url_el.text.strip()
            if url.startswith("http://"):
                issues.append(
                    f"{xml_file}: AdapterUrl uses HTTP ('{url}'). "
                    "Open CTI adapter pages must be served over HTTPS."
                )
            elif not url.startswith("https://"):
                issues.append(
                    f"{xml_file}: AdapterUrl does not appear to be a valid HTTPS URL: '{url}'."
                )

        # Check InternalName has no spaces
        internal_name_el = root.find("InternalName")
        if internal_name_el is None:
            issues.append(f"{xml_file}: Missing <InternalName> element.")
        elif internal_name_el.text and " " in internal_name_el.text:
            issues.append(
                f"{xml_file}: InternalName '{internal_name_el.text}' contains spaces. "
                "InternalName must not contain spaces — it is used as a primary key."
            )

        # Check DisplayName is present
        display_name_el = root.find("DisplayName")
        if display_name_el is None or not (display_name_el.text or "").strip():
            issues.append(f"{xml_file}: Missing or empty <DisplayName> element.")

    return issues


def check_adapter_js_files(manifest_dir: Path) -> list[str]:
    """Scan HTML and JS files for common Open CTI anti-patterns."""
    issues: list[str] = []

    candidate_files = list(manifest_dir.rglob("*.html")) + list(manifest_dir.rglob("*.js"))

    for file_path in candidate_files:
        # Skip node_modules, .sfdx, and similar generated directories
        parts = file_path.parts
        if any(p in parts for p in ("node_modules", ".sfdx", "__pycache__", "dist", ".git")):
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Only check files that reference the Open CTI API
        if "sforce.opencti" not in content and "opencti" not in content.lower():
            continue

        # Anti-pattern: manually loading the opencti script
        if re.search(r'<script[^>]+opencti[^>]*>', content, re.IGNORECASE):
            issues.append(
                f"{file_path}: Detected manual <script> tag loading an opencti JS file. "
                "The sforce.opencti namespace is injected automatically by Salesforce — "
                "do not load it manually via a <script> tag."
            )

        # Anti-pattern: CTIVersion 3.0 referenced in a JS/HTML file comment or config
        if re.search(r'CTIVersion.*3\.0', content):
            issues.append(
                f"{file_path}: Reference to CTIVersion 3.0 found. "
                "Use 4.0 for Lightning Open CTI."
            )

        # Anti-pattern: onClickToDial called outside of enableClickToDial callback
        # Heuristic: both methods called as sibling statements (not nested)
        enable_pos = content.find("enableClickToDial")
        onclick_pos = content.find("onClickToDial")
        if enable_pos != -1 and onclick_pos != -1:
            # If onClickToDial appears before enableClickToDial, it is definitely wrong
            if onclick_pos < enable_pos:
                issues.append(
                    f"{file_path}: sforce.opencti.onClickToDial appears before "
                    "sforce.opencti.enableClickToDial. The listener must be registered "
                    "inside the enableClickToDial success callback."
                )

        # Anti-pattern: saveLog without checking response.success
        save_log_matches = list(re.finditer(r'saveLog\s*\(', content))
        for match in save_log_matches:
            # Look at the next 400 chars after saveLog( for a response.success check
            window = content[match.start():match.start() + 400]
            if "response.success" not in window and "res.success" not in window:
                issues.append(
                    f"{file_path} (near position {match.start()}): "
                    "saveLog callback does not appear to check response.success. "
                    "Add a response.success check and surface failures to the agent."
                )

        # Anti-pattern: potential hardcoded credentials (heuristic)
        credential_patterns = [
            r'password\s*[=:]\s*["\'][^"\']{6,}["\']',
            r'apiKey\s*[=:]\s*["\'][^"\']{6,}["\']',
            r'api_key\s*[=:]\s*["\'][^"\']{6,}["\']',
            r'secret\s*[=:]\s*["\'][^"\']{6,}["\']',
        ]
        for pattern in credential_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(
                    f"{file_path}: Possible hardcoded credential detected "
                    f"(pattern: {pattern}). Use callcenter.xml CustomSettings "
                    "or a server-side token exchange instead."
                )
                break  # One warning per file is enough

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_cti_adapter_development(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_callcenter_xml_files(manifest_dir))
    issues.extend(check_adapter_js_files(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_cti_adapter_development(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
