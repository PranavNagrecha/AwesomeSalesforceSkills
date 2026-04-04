#!/usr/bin/env python3
"""Certificate and Key Management checker script.

Scans a Salesforce metadata project directory for certificate-related references
in XML files (connected apps, Named Credentials, etc.) and warns if certificates
are referenced without documented rotation/expiry tracking.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_certificate.py [--manifest-dir path/to/metadata]
    python3 check_certificate.py --manifest-dir force-app/main/default

Exit codes:
    0 — no issues found
    1 — one or more issues found
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# XML tag names that contain certificate name references across metadata types.
CERT_REF_TAGS = {
    "certificate",
    "certificateName",
    "oauthClientCredentialUser",
}

# Metadata file suffixes that may reference certificates.
CERTIFICATE_BEARING_SUFFIXES = (
    ".connectedApp-meta.xml",
    ".namedCredential-meta.xml",
    ".externalCredential-meta.xml",
    ".remoteSiteSetting-meta.xml",
)

# Metadata folder names where certificate source files would live.
CERTIFICATE_METADATA_DIRS = {"certificates"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce metadata project for certificate references "
            "that may need expiry tracking or rotation documentation."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    return parser.parse_args()


def find_cert_references_in_xml(file_path: Path) -> list[str]:
    """Parse an XML metadata file and return all certificate name values found."""
    found: list[str] = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError:
        return found

    # Strip XML namespace from tag names for comparison.
    for elem in root.iter():
        local_tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if local_tag in CERT_REF_TAGS and elem.text and elem.text.strip():
            found.append(elem.text.strip())
    return found


def check_certificates(manifest_dir: Path) -> list[str]:
    """Scan the manifest directory and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # --- Check 1: Scan metadata files for certificate references ---
    cert_references: dict[str, list[str]] = {}  # file → list of cert names

    all_xml_files = list(manifest_dir.rglob("*.xml"))
    for xml_file in all_xml_files:
        name_lower = xml_file.name.lower()
        if any(name_lower.endswith(suffix.lower()) for suffix in CERTIFICATE_BEARING_SUFFIXES):
            cert_names = find_cert_references_in_xml(xml_file)
            if cert_names:
                cert_references[str(xml_file.relative_to(manifest_dir))] = cert_names

    if cert_references:
        issues.append(
            "CERTIFICATE REFERENCES FOUND — Certificates cannot be deployed via Metadata API/SFDX. "
            "These files reference certificates that must be manually imported or created in each "
            "target org via Setup > Certificate and Key Management. Add an out-of-band certificate "
            "migration step to your release runbook."
        )
        for rel_path, cert_names in sorted(cert_references.items()):
            unique_names = sorted(set(cert_names))
            issues.append(
                f"  File: {rel_path} — references certificate(s): {', '.join(unique_names)}"
            )

    # --- Check 2: Warn if certificate metadata source files are present ---
    cert_source_files: list[str] = []
    for xml_file in all_xml_files:
        # Certificate source files are in a 'certificates/' folder
        parts = [p.lower() for p in xml_file.parts]
        if any(part in CERTIFICATE_METADATA_DIRS for part in parts):
            cert_source_files.append(str(xml_file.relative_to(manifest_dir)))

    if cert_source_files:
        issues.append(
            "CERTIFICATE METADATA SOURCE FILES FOUND — These files contain only the public "
            "certificate, not the private key. A metadata deploy will NOT fully migrate the "
            "certificate. For CA-signed certificates, the original JKS/PKCS#12 must be re-imported "
            "manually in each target org. For self-signed certificates, a new certificate must be "
            "created in each org independently."
        )
        for rel_path in sorted(cert_source_files):
            issues.append(f"  File: {rel_path}")

    # --- Check 3: No issues found is a valid result ---
    if not issues:
        pass  # Explicitly clean — no certificate references detected.

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()
    issues = check_certificates(manifest_dir)

    if not issues:
        print("No certificate-related issues found.")
        return 0

    print(f"Found {len(issues)} certificate-related finding(s) in: {manifest_dir}\n")
    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
