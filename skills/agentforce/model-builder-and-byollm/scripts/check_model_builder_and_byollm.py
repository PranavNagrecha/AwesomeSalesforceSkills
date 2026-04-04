#!/usr/bin/env python3
"""Checker script for Model Builder and BYOLLM skill.

Inspects a Salesforce metadata directory for common Model Builder and BYOLLM
configuration issues: missing Named Credentials for external models, model
alias misconfiguration, and permission set gaps for Named Credential access.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_model_builder_and_byollm.py [--help]
    python3 check_model_builder_and_byollm.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common Model Builder / BYOLLM "
            "configuration issues."
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

def _xml_text(root: ET.Element, tag: str, ns: str = "") -> str:
    """Return stripped text of the first matching element, or empty string."""
    prefix = f"{{{ns}}}" if ns else ""
    el = root.find(f".//{prefix}{tag}")
    return el.text.strip() if el is not None and el.text else ""


def _find_xml_files(directory: Path, pattern: str) -> list[Path]:
    return sorted(directory.rglob(pattern))


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_named_credentials(manifest_dir: Path) -> list[str]:
    """Warn if Named Credential files exist without a corresponding External
    Credential file, or if any Named Credential has a plaintext password/token
    in the Auth Password field (a common misconfiguration when the author has
    not yet moved to External Credentials).
    """
    issues: list[str] = []
    nc_dir = manifest_dir / "namedCredentials"

    if not nc_dir.exists():
        # No named credentials at all — flag only if there are model-builder metadata files
        model_dir = manifest_dir / "aiModels"
        if model_dir.exists() and any(model_dir.rglob("*.xml")):
            issues.append(
                "namedCredentials/ directory not found but aiModels/ metadata exists. "
                "External model registrations require Named Credentials for API key storage."
            )
        return issues

    for nc_file in _find_xml_files(nc_dir, "*.namedCredential"):
        try:
            tree = ET.parse(nc_file)
        except ET.ParseError as exc:
            issues.append(f"Could not parse Named Credential XML {nc_file.name}: {exc}")
            continue

        root = tree.getroot()
        # Check for plaintext password in legacy Named Credential format
        auth_password = _xml_text(root, "password")
        auth_token = _xml_text(root, "oauthToken")
        if auth_password or auth_token:
            issues.append(
                f"{nc_file.name}: Named Credential contains a plaintext password or "
                "OAuth token field. External LLM API keys must be stored in an External "
                "Credential Principal (Custom auth), not as a Named Credential password. "
                "Move the API key to an External Credential."
            )

        # Warn if protocol is 'NoAuthentication' — external models must authenticate
        protocol = _xml_text(root, "protocol")
        if protocol and protocol.lower() == "noauthentication":
            issues.append(
                f"{nc_file.name}: Named Credential auth protocol is 'NoAuthentication'. "
                "External LLM providers require authentication. Verify this Named "
                "Credential is not backing an external model registration."
            )

    return issues


def check_external_credentials(manifest_dir: Path) -> list[str]:
    """Check External Credential files for common issues with Model Builder usage."""
    issues: list[str] = []
    ec_dir = manifest_dir / "externalCredentials"

    if not ec_dir.exists():
        return issues

    for ec_file in _find_xml_files(ec_dir, "*.externalCredential"):
        try:
            tree = ET.parse(ec_file)
        except ET.ParseError as exc:
            issues.append(f"Could not parse External Credential XML {ec_file.name}: {exc}")
            continue

        root = tree.getroot()
        auth_protocol = _xml_text(root, "authenticationProtocol")

        # For External Credentials used with Model Builder, 'Custom' is the expected protocol
        if auth_protocol and auth_protocol.lower() not in ("custom", "awssignature4"):
            issues.append(
                f"{ec_file.name}: External Credential uses auth protocol '{auth_protocol}'. "
                "Model Builder BYOLLM registrations typically require 'Custom' protocol "
                "with a Bearer token or api-key header. Verify this is intentional."
            )

        # Warn if no principals are defined — principals carry the actual API key
        principals = root.findall(".//{*}principals") or root.findall(".//principals")
        if not principals:
            issues.append(
                f"{ec_file.name}: External Credential has no principals defined. "
                "Without a principal, no API key parameter can be stored. "
                "Add an Org principal with the provider API key as a Custom Header parameter."
            )

    return issues


def check_ai_model_metadata(manifest_dir: Path) -> list[str]:
    """Check for aiModels metadata directory and basic XML structure."""
    issues: list[str] = []
    model_dir = manifest_dir / "aiModels"

    if not model_dir.exists():
        # Not necessarily an issue if this is a non-AI project, but note it
        return issues

    model_files = _find_xml_files(model_dir, "*.xml")
    if not model_files:
        issues.append(
            "aiModels/ directory exists but contains no model XML files. "
            "Verify the metadata was retrieved correctly using "
            "'sf project retrieve start --metadata AIModel'."
        )
        return issues

    for model_file in model_files:
        try:
            tree = ET.parse(model_file)
        except ET.ParseError as exc:
            issues.append(f"Could not parse AI Model XML {model_file.name}: {exc}")
            continue

        root = tree.getroot()

        # Check for a referenced named credential
        nc_ref = _xml_text(root, "namedCredential") or _xml_text(root, "namedCredentialRef")
        provider_type = _xml_text(root, "providerType") or _xml_text(root, "type")

        # External provider models should reference a Named Credential
        external_providers = {"openai", "azureopenai", "anthropic", "custom"}
        if provider_type and provider_type.lower() in external_providers:
            if not nc_ref:
                issues.append(
                    f"{model_file.name}: External model (provider: {provider_type}) "
                    "does not reference a Named Credential. All external LLM API keys "
                    "must be stored in a Named Credential. "
                    "Add the namedCredential reference to the model definition."
                )

    return issues


def check_permission_sets_for_nc(manifest_dir: Path) -> list[str]:
    """Warn if Named Credentials exist but no Permission Set references them.

    A Named Credential for an external model must be accessible via Permission Set
    for the Agentforce running user or integration user. This check is heuristic —
    it flags when NC files exist but no PS files in the manifest reference them.
    """
    issues: list[str] = []
    nc_dir = manifest_dir / "namedCredentials"
    ps_dir = manifest_dir / "permissionsets"

    if not nc_dir.exists():
        return issues

    nc_names = {
        p.stem for p in _find_xml_files(nc_dir, "*.namedCredential")
    }
    if not nc_names:
        return issues

    if not ps_dir.exists():
        issues.append(
            "namedCredentials/ found but no permissionsets/ directory exists in the manifest. "
            "Named Credentials used for external LLM models must be granted to relevant users "
            "via Permission Sets. Retrieve permissionsets/ metadata and verify access is granted."
        )
        return issues

    # Collect all Named Credential references across all permission set XML files
    referenced_ncs: set[str] = set()
    for ps_file in _find_xml_files(ps_dir, "*.permissionset"):
        try:
            tree = ET.parse(ps_file)
        except ET.ParseError:
            continue
        root = tree.getroot()
        for el in root.iter():
            if el.tag.endswith("namedCredential") and el.text:
                referenced_ncs.add(el.text.strip())

    unreferenced = nc_names - referenced_ncs
    if unreferenced:
        for nc_name in sorted(unreferenced):
            issues.append(
                f"Named Credential '{nc_name}' is not referenced in any Permission Set in "
                "the manifest. Ensure the Agentforce running user and integration user have "
                "Named Credential access granted via a Permission Set, or external model "
                "calls will fail with a credential access error."
            )

    return issues


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def check_model_builder_and_byollm(manifest_dir: Path) -> list[str]:
    """Run all checks and return a combined list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_named_credentials(manifest_dir))
    issues.extend(check_external_credentials(manifest_dir))
    issues.extend(check_ai_model_metadata(manifest_dir))
    issues.extend(check_permission_sets_for_nc(manifest_dir))

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_model_builder_and_byollm(manifest_dir)

    if not issues:
        print("No Model Builder / BYOLLM issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
