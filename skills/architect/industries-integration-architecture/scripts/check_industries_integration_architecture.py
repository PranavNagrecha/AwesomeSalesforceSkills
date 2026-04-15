#!/usr/bin/env python3
"""Checker script for Industries Integration Architecture skill.

Validates Salesforce metadata in a project directory for common Industries
integration architecture anti-patterns:
  - Hardcoded URLs in Integration Procedure HTTP Actions (should use Named Credentials)
  - MuleSoft Gateway configuration in Communications Cloud TM Forum API settings
  - Integration Procedure HTTP Actions without error-handling elements
  - DML writes to Insurance/E&U standard objects from write-path Integration Procedures
  - Missing Named Credential references where callout endpoints are configured

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_industries_integration_architecture.py [--manifest-dir path/to/metadata]
    python3 check_industries_integration_architecture.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


# ── constants ──────────────────────────────────────────────────────────────────

# Integration Procedure metadata type directory names (managed and unmanaged)
IP_METADATA_DIRS = (
    "OmniIntegrationProcedures",
    "integrationProcedures",
    "IntegrationProcedures",
    "vlocity_ins__IntegrationProcedure",
    "industries__IntegrationProcedure",
)

# Standard Industries objects that should not be DML-updated from Salesforce
# write-back paths (they are CIS/PAS-authoritative projections)
RESTRICTED_WRITE_OBJECTS = frozenset(
    [
        "InsurancePolicy",
        "InsurancePolicyCoverage",
        "InsurancePolicyParticipant",
        "InsurancePolicyAsset",
        "EnergyRatePlan",
        "EnergyRatePlanDef",
        "ServicePoint",
        "ServicePlan",
        "ProductCatalog",
        "ProductSpecification",
    ]
)

# Strings indicating a hardcoded URL in an endpoint field
HARDCODED_URL_PATTERNS = ("https://", "http://")

# Apex file extensions
APEX_EXTENSIONS = (".cls",)

# XML namespaces commonly found in Salesforce metadata XML
SALESFORCE_NAMESPACES = {
    "sf": "http://soap.sforce.com/2006/04/metadata",
}


# ── helpers ────────────────────────────────────────────────────────────────────


def iter_files(root: Path, *extensions: str):
    """Yield all files under root matching any of the given extensions."""
    for dirpath, _dirnames, filenames in os.walk(root):
        for filename in filenames:
            if any(filename.endswith(ext) for ext in extensions):
                yield Path(dirpath) / filename


def find_ip_dirs(root: Path) -> list[Path]:
    """Return all Integration Procedure metadata directories found under root."""
    found = []
    for dirpath, dirnames, _filenames in os.walk(root):
        for dirname in dirnames:
            if dirname in IP_METADATA_DIRS:
                found.append(Path(dirpath) / dirname)
    return found


def check_ip_xml_file(xml_file: Path, issues: list[str]) -> None:
    """Parse a single IP XML file and check for architectural anti-patterns."""
    try:
        tree = ET.parse(xml_file)
    except ET.ParseError as exc:
        issues.append(f"Could not parse IP XML file {xml_file}: {exc}")
        return

    root = tree.getroot()
    # Strip namespace for easier element lookup
    raw_xml = xml_file.read_text(encoding="utf-8", errors="replace")

    _check_hardcoded_urls_in_xml(xml_file, raw_xml, issues)
    _check_missing_error_handler_in_xml(xml_file, raw_xml, issues)


def _check_hardcoded_urls_in_xml(xml_file: Path, content: str, issues: list[str]) -> None:
    """Flag any Integration Procedure HTTP Actions with hardcoded endpoint URLs."""
    lines = content.splitlines()
    in_http_action = False
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        # Rough heuristic: detect HTTP Action blocks in IP XML
        if "HTTPAction" in stripped or "HttpAction" in stripped or "remoteClass" in stripped.lower():
            in_http_action = True
        if in_http_action:
            for pattern in HARDCODED_URL_PATTERNS:
                if pattern in stripped and "namedCredential" not in stripped.lower():
                    issues.append(
                        f"{xml_file}:{lineno} — Possible hardcoded URL in Integration Procedure "
                        f"endpoint field ('{stripped[:80]}...'). Use Named Credentials instead of "
                        f"hardcoded URLs for all external callouts."
                    )
                    break
        # Reset after closing tag heuristic
        if in_http_action and stripped.startswith("</") and "Action" in stripped:
            in_http_action = False


def _check_missing_error_handler_in_xml(xml_file: Path, content: str, issues: list[str]) -> None:
    """Warn if an IP file has an HTTP Action element but no error-handling element."""
    has_http_action = (
        "HTTPAction" in content
        or "HttpAction" in content
        or "remoteClass" in content.lower()
    )
    has_error_handler = (
        "errorHandler" in content.lower()
        or "SetErrors" in content
        or "setErrors" in content
        or "statusCode" in content.lower()
    )
    if has_http_action and not has_error_handler:
        issues.append(
            f"{xml_file} — Integration Procedure has an HTTP Action but no apparent error-handling "
            f"element (SetErrors, errorHandler, or statusCode condition). All external callouts must "
            f"handle backend unavailability gracefully."
        )


def check_apex_files(root: Path, issues: list[str]) -> None:
    """Check Apex classes for DML writes to restricted Industries objects from callout contexts."""
    for apex_file in iter_files(root, *APEX_EXTENSIONS):
        content = apex_file.read_text(encoding="utf-8", errors="replace")
        _check_restricted_object_dml(apex_file, content, issues)
        _check_hardcoded_callout_urls(apex_file, content, issues)


def _check_restricted_object_dml(apex_file: Path, content: str, issues: list[str]) -> None:
    """Flag DML operations on CIS/PAS-authoritative standard objects."""
    lines = content.splitlines()
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        # Look for insert/update/upsert statements referencing restricted objects
        if any(
            keyword in stripped.lower()
            for keyword in ("insert ", "update ", "upsert ", "database.insert", "database.update", "database.upsert")
        ):
            for obj in RESTRICTED_WRITE_OBJECTS:
                if obj.lower() in stripped.lower():
                    issues.append(
                        f"{apex_file}:{lineno} — DML write to Industries-authoritative object '{obj}' "
                        f"detected in Apex. If this is in a write-back callout context, verify that "
                        f"'{obj}' is not owned by an external backend (PAS, BSS, CIS). "
                        f"These objects should be read-only projections in most Industries architectures."
                    )
                    break


def _check_hardcoded_callout_urls(apex_file: Path, content: str, issues: list[str]) -> None:
    """Flag hardcoded setEndpoint calls without Named Credential prefix."""
    lines = content.splitlines()
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if "setendpoint" in stripped.lower():
            for pattern in HARDCODED_URL_PATTERNS:
                if pattern in stripped and "callout:" not in stripped.lower():
                    issues.append(
                        f"{apex_file}:{lineno} — Hardcoded endpoint URL in Apex callout "
                        f"('{stripped[:80]}'). Use Named Credentials: "
                        f"req.setEndpoint('callout:NamedCredentialName/path')."
                    )
                    break


def check_mulesoft_gateway_config(root: Path, issues: list[str]) -> None:
    """Check Custom Metadata or Custom Settings for MuleSoft Gateway Communications Cloud config."""
    for xml_file in iter_files(root, ".xml", ".md"):
        try:
            content = xml_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Check for MuleSoft Gateway access mode markers in metadata XML
        if "MulesoftGateway" in content or "MuleSoftGateway" in content or "MULESOFT_GATEWAY" in content:
            issues.append(
                f"{xml_file} — Possible MuleSoft API Gateway access mode configuration detected for "
                f"Communications Cloud TM Forum API. The MuleSoft Gateway integration path is deprecated "
                f"effective Winter '27. Migrate to Direct TM Forum API Access."
            )
        # Check for the string in YAML/JSON config variants
        if '"accessMode"' in content and ("mulesoft" in content.lower() or "gateway" in content.lower()):
            issues.append(
                f"{xml_file} — Possible MuleSoft Gateway access mode in Communications Cloud API config. "
                f"Verify TM Forum API Settings → Access Mode is set to Direct Access, not MuleSoft Gateway."
            )


# ── main ───────────────────────────────────────────────────────────────────────


def check_industries_integration_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # 1. Check Integration Procedure XML files
    ip_dirs = find_ip_dirs(manifest_dir)
    if ip_dirs:
        for ip_dir in ip_dirs:
            for xml_file in iter_files(ip_dir, ".xml", ".json"):
                check_ip_xml_file(xml_file, issues)
    else:
        # Also check for IP files anywhere under manifest (some project structures)
        for xml_file in iter_files(manifest_dir, ".xml"):
            content = xml_file.read_text(encoding="utf-8", errors="replace")
            if "IntegrationProcedure" in content or "integrationProcedure" in content:
                check_ip_xml_file(xml_file, issues)

    # 2. Check Apex classes for restricted object DML and hardcoded callout URLs
    check_apex_files(manifest_dir, issues)

    # 3. Check for MuleSoft Gateway configuration
    check_mulesoft_gateway_config(manifest_dir, issues)

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Industries integration architecture anti-patterns: "
            "hardcoded callout URLs, MuleSoft Gateway config, missing error handlers, "
            "and DML writes to CIS/PAS-authoritative standard objects."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_industries_integration_architecture(manifest_dir)

    if not issues:
        print("No Industries integration architecture issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
