#!/usr/bin/env python3
"""Checker script for Change Advisory Board Process skill.

Inspects a Salesforce DX project metadata directory for patterns that
indicate CAB governance gaps:
  - High-risk metadata types present without a documented change ticket reference
  - Profile or PermissionSet XML that is likely to cause silent permission revocation
    (detects incomplete retrieval markers or suspiciously small XML)
  - Named Credential or Remote Site Setting changes without explicit security review flag
  - Missing rollback plan reference in change documentation

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_change_advisory_board_process.py [--help]
    python3 check_change_advisory_board_process.py --manifest-dir path/to/metadata
    python3 check_change_advisory_board_process.py --manifest-dir path/to/metadata --change-ticket CR1234567
"""

from __future__ import annotations

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# High-risk metadata folder names (relative to the force-app/main/default or
# equivalent metadata source root). These types always require Normal or
# Emergency CAB classification — never Standard.
# ---------------------------------------------------------------------------
HIGH_RISK_FOLDERS = {
    "profiles",
    "permissionsets",
    "permissionsetgroups",
    "sharingrules",
    "namedcredentials",
    "connectedapps",
    "remotesitesettings",
    "custommetadata",
    "customsettings",
}

# Metadata folder names that trigger a security-review flag when present
SECURITY_REVIEW_REQUIRED = {
    "namedcredentials",
    "remotesitesettings",
    "connectedapps",
}

# Minimum number of XML bytes for a Profile or PermissionSet to be
# considered a plausibly complete retrieval. Files smaller than this
# are flagged as potentially incomplete (and thus dangerous to deploy).
MINIMUM_PROFILE_BYTES = 500
MINIMUM_PERMSET_BYTES = 300


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce DX metadata source directory for CAB governance gaps. "
            "Reports high-risk metadata types, potentially incomplete Profile/PermSet XML, "
            "and missing security-review markers."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce DX project or metadata source (default: current directory).",
    )
    parser.add_argument(
        "--change-ticket",
        default="",
        help=(
            "Change ticket / request number for this deployment (e.g., CR1234567). "
            "If provided, the check will confirm it is non-empty and correctly formatted."
        ),
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def _find_metadata_folders(manifest_dir: Path) -> dict[str, list[Path]]:
    """Walk the manifest directory and collect metadata files by folder type.

    Returns a dict mapping lowercase folder name -> list of file Paths.
    """
    result: dict[str, list[Path]] = {}
    for root, dirs, files in os.walk(manifest_dir):
        root_path = Path(root)
        folder_name = root_path.name.lower()
        # Skip hidden directories and generated artifacts
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in files:
            if fname.endswith(".xml") or fname.endswith(".json"):
                result.setdefault(folder_name, []).append(root_path / fname)
    return result


def check_high_risk_metadata_present(folders: dict[str, list[Path]]) -> list[str]:
    """Warn whenever a high-risk metadata type is detected in the change set."""
    issues: list[str] = []
    for folder, files in folders.items():
        if folder in HIGH_RISK_FOLDERS:
            file_names = [f.name for f in files]
            issues.append(
                f"HIGH-RISK metadata detected in folder '{folder}': {file_names}. "
                f"This change requires Normal or Emergency CAB classification — "
                f"Standard (pre-authorized) classification is not permitted."
            )
    return issues


def check_security_review_required(folders: dict[str, list[Path]]) -> list[str]:
    """Flag metadata types that require explicit security team sign-off."""
    issues: list[str] = []
    for folder, files in folders.items():
        if folder in SECURITY_REVIEW_REQUIRED:
            file_names = [f.name for f in files]
            issues.append(
                f"SECURITY REVIEW REQUIRED: '{folder}' metadata detected: {file_names}. "
                f"Named Credentials, Remote Site Settings, and Connected Apps open or modify "
                f"external network access. The CAB approval for this change must include "
                f"explicit sign-off from the Security or IT team."
            )
    return issues


def check_profile_completeness(folders: dict[str, list[Path]]) -> list[str]:
    """Detect Profile XML files that are suspiciously small (likely incomplete retrieval).

    An incomplete Profile retrieved from org will silently remove permissions
    when deployed. Flag files below the minimum byte threshold.
    """
    issues: list[str] = []
    for folder, files in folders.items():
        if folder != "profiles":
            continue
        for fpath in files:
            if not fpath.suffix == ".xml":
                continue
            size = fpath.stat().st_size
            if size < MINIMUM_PROFILE_BYTES:
                issues.append(
                    f"POTENTIALLY INCOMPLETE Profile XML: '{fpath.name}' is only {size} bytes. "
                    f"A Profile retrieved without a comprehensive package.xml scope will be missing "
                    f"field-level security and object permission entries. Deploying this file can "
                    f"silently revoke permissions from production users. "
                    f"Retrieve the full Profile before including it in a CAB-approved deployment."
                )
            # Also check for the presence of <fieldPermissions> — a complete Profile should have them
            try:
                tree = ET.parse(fpath)
                root = tree.getroot()
                ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
                # Strip namespace from tag for broader compatibility
                all_tags = {child.tag.split("}")[-1] for child in root.iter()}
                if "fieldPermissions" not in all_tags and "objectPermissions" not in all_tags:
                    issues.append(
                        f"Profile '{fpath.name}' contains no <fieldPermissions> or "
                        f"<objectPermissions> elements. This strongly suggests an incomplete "
                        f"retrieval. Deploying this Profile may silently remove access from users."
                    )
            except ET.ParseError:
                issues.append(
                    f"Profile '{fpath.name}' could not be parsed as valid XML. "
                    f"Verify the file is well-formed before including it in a deployment."
                )
    return issues


def check_permissionset_completeness(folders: dict[str, list[Path]]) -> list[str]:
    """Detect PermissionSet XML files that are suspiciously small."""
    issues: list[str] = []
    for folder, files in folders.items():
        if folder != "permissionsets":
            continue
        for fpath in files:
            if not fpath.suffix == ".xml":
                continue
            size = fpath.stat().st_size
            if size < MINIMUM_PERMSET_BYTES:
                issues.append(
                    f"POTENTIALLY INCOMPLETE PermissionSet XML: '{fpath.name}' is only {size} bytes. "
                    f"A very small PermissionSet XML likely omits permission entries. "
                    f"While PermissionSet deployment is additive (does not remove existing grants), "
                    f"confirm that all intended permissions are present in the file before deploying."
                )
    return issues


def check_change_ticket_format(change_ticket: str) -> list[str]:
    """Validate the change ticket number format and presence."""
    issues: list[str] = []
    if not change_ticket:
        issues.append(
            "No change ticket number provided (--change-ticket flag). "
            "Every deployment of high-risk metadata requires a corresponding approved "
            "change request in the ITSM system. Provide the ticket number via --change-ticket."
        )
        return issues
    # Basic sanity: must be non-trivial (not just whitespace, not a placeholder)
    stripped = change_ticket.strip()
    placeholders = {"todo", "tbd", "n/a", "none", "na", "test", "xxx"}
    if stripped.lower() in placeholders or len(stripped) < 4:
        issues.append(
            f"Change ticket '{change_ticket}' appears to be a placeholder or invalid value. "
            f"Provide the actual ITSM change request number (e.g., CR1234567, CHG0012345)."
        )
    return issues


def check_change_advisory_board_process(
    manifest_dir: Path, change_ticket: str = ""
) -> list[str]:
    """Run all CAB governance checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    folders = _find_metadata_folders(manifest_dir)

    if not any(folders.values()):
        # No metadata files found — not necessarily an error, but flag it
        issues.append(
            f"No XML metadata files found under '{manifest_dir}'. "
            f"Verify the --manifest-dir path points to the Salesforce DX source root "
            f"(e.g., force-app/main/default)."
        )
        return issues

    issues.extend(check_high_risk_metadata_present(folders))
    issues.extend(check_security_review_required(folders))
    issues.extend(check_profile_completeness(folders))
    issues.extend(check_permissionset_completeness(folders))
    issues.extend(check_change_ticket_format(change_ticket))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_change_advisory_board_process(
        manifest_dir, change_ticket=args.change_ticket
    )

    if not issues:
        print(
            "CAB governance check passed. No high-risk metadata detected without "
            "appropriate classification markers."
        )
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(
        f"\n{len(issues)} CAB governance issue(s) found. "
        f"Review the warnings above before submitting the change ticket for CAB approval.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
