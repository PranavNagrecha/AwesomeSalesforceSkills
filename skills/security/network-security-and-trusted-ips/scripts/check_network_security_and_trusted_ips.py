#!/usr/bin/env python3
"""Checker script for Network Security and Trusted IPs skill.

Inspects a Salesforce metadata export directory for common network security
misconfiguration patterns: missing Login IP Ranges on privileged profiles,
CSP Trusted Sites with all directives enabled (overly broad), and
undocumented IP range entries.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_network_security_and_trusted_ips.py [--help]
    python3 check_network_security_and_trusted_ips.py --manifest-dir path/to/metadata
    python3 check_network_security_and_trusted_ips.py --manifest-dir force-app/main/default

Expected metadata layout (standard SFDX format):
    force-app/main/default/
        profiles/
            Admin.profile-meta.xml          (contains <loginIpRanges>)
        cspTrustedSites/
            *.cspTrustedSite-meta.xml
        corsWhitelistOrigins/
            *.corsWhitelistOrigin-meta.xml
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# Profiles that should have Login IP Ranges configured in a hardened org.
PRIVILEGED_PROFILE_NAMES = {
    "Admin",
    "System Administrator",
    "SystemAdministrator",
}

# CSP directives that, when all present simultaneously, suggest an overly
# permissive entry that allows all resource types from the trusted domain.
ALL_CSP_DIRECTIVES = {
    "connect-src",
    "font-src",
    "frame-src",
    "img-src",
    "media-src",
    "object-src",
    "script-src",
    "style-src",
    "worker-src",
}


def _xml_namespace(element: ET.Element) -> str:
    """Extract the namespace URI from an XML element tag, if present."""
    tag = element.tag
    if tag.startswith("{"):
        return tag.split("}")[0][1:]
    return ""


def check_profiles_for_login_ip_ranges(profiles_dir: Path) -> list[str]:
    """Check that privileged profiles have at least one Login IP Range defined."""
    issues: list[str] = []

    if not profiles_dir.exists():
        return issues

    for profile_file in profiles_dir.glob("*.profile-meta.xml"):
        stem = profile_file.stem.replace(".profile-meta", "")
        if stem not in PRIVILEGED_PROFILE_NAMES:
            continue

        try:
            tree = ET.parse(profile_file)
        except ET.ParseError as exc:
            issues.append(f"[profiles] Could not parse {profile_file.name}: {exc}")
            continue

        root = tree.getroot()
        ns = _xml_namespace(root)
        ns_prefix = f"{{{ns}}}" if ns else ""

        login_ip_ranges = root.findall(f"{ns_prefix}loginIpRanges")
        if not login_ip_ranges:
            issues.append(
                f"[profiles] Privileged profile '{stem}' has no loginIpRanges defined. "
                "Users on this profile can log in from any IP address. "
                "Consider adding Login IP Ranges to restrict access to known corporate IPs."
            )

    return issues


def check_csp_trusted_sites(csp_dir: Path) -> list[str]:
    """Check CSP Trusted Sites for overly permissive entries."""
    issues: list[str] = []

    if not csp_dir.exists():
        return issues

    for csp_file in csp_dir.glob("*.cspTrustedSite-meta.xml"):
        try:
            tree = ET.parse(csp_file)
        except ET.ParseError as exc:
            issues.append(f"[csp] Could not parse {csp_file.name}: {exc}")
            continue

        root = tree.getroot()
        ns = _xml_namespace(root)
        ns_prefix = f"{{{ns}}}" if ns else ""

        # Collect enabled directives
        enabled_directives: set[str] = set()
        for directive_elem in root.findall(f"{ns_prefix}cspDirectives"):
            directive_name_elem = directive_elem.find(f"{ns_prefix}directive")
            enabled_elem = directive_elem.find(f"{ns_prefix}enabled")
            if directive_name_elem is not None and enabled_elem is not None:
                if enabled_elem.text and enabled_elem.text.strip().lower() == "true":
                    if directive_name_elem.text:
                        enabled_directives.add(directive_name_elem.text.strip())

        # Warn if script-src is enabled alongside connect-src — common missed pairing
        if "script-src" in enabled_directives and "connect-src" not in enabled_directives:
            endpoint_elem = root.find(f"{ns_prefix}endpointUrl")
            url = endpoint_elem.text.strip() if endpoint_elem is not None and endpoint_elem.text else csp_file.stem
            issues.append(
                f"[csp] '{url}' has script-src enabled but connect-src is not enabled. "
                "If this script makes fetch() or XHR calls back to the same domain, those calls will be "
                "blocked by a connect-src CSP violation. Add connect-src if needed."
            )

        # Warn if all directives are enabled — suggests a catch-all entry
        if enabled_directives and ALL_CSP_DIRECTIVES.issubset(enabled_directives):
            endpoint_elem = root.find(f"{ns_prefix}endpointUrl")
            url = endpoint_elem.text.strip() if endpoint_elem is not None and endpoint_elem.text else csp_file.stem
            issues.append(
                f"[csp] '{url}' has all CSP directives enabled. "
                "This is overly permissive. Apply only the directives required for this resource. "
                "See references/gotchas.md for directive-to-resource-type mapping."
            )

    return issues


def check_cors_entries(cors_dir: Path) -> list[str]:
    """Check CORS whitelist origins for wildcard patterns and undocumented entries."""
    issues: list[str] = []

    if not cors_dir.exists():
        return issues

    for cors_file in cors_dir.glob("*.corsWhitelistOrigin-meta.xml"):
        try:
            tree = ET.parse(cors_file)
        except ET.ParseError as exc:
            issues.append(f"[cors] Could not parse {cors_file.name}: {exc}")
            continue

        root = tree.getroot()
        ns = _xml_namespace(root)
        ns_prefix = f"{{{ns}}}" if ns else ""

        url_elem = root.find(f"{ns_prefix}urlPattern")
        if url_elem is None or not url_elem.text:
            issues.append(
                f"[cors] {cors_file.name} has no urlPattern element. File may be malformed."
            )
            continue

        url = url_elem.text.strip()

        # Wildcard subdomains are permitted but should be flagged for review
        if url.startswith("https://*.") or url.startswith("http://*."):
            issues.append(
                f"[cors] CORS entry '{url}' uses a wildcard subdomain pattern. "
                "Verify this wildcard is intentional and that all subdomains of this domain "
                "are trusted to call the Salesforce API."
            )

        # HTTP (non-HTTPS) origins are insecure
        if url.startswith("http://") and not url.startswith("http://localhost"):
            issues.append(
                f"[cors] CORS entry '{url}' uses plain HTTP (not HTTPS). "
                "Non-localhost HTTP origins should not be allowed; use HTTPS."
            )

    return issues


def check_network_security_and_trusted_ips(manifest_dir: Path) -> list[str]:
    """Run all network security checks against the metadata manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Resolve standard SFDX source paths
    # Support both flat layout and force-app/main/default layout
    candidate_roots = [
        manifest_dir,
        manifest_dir / "force-app" / "main" / "default",
        manifest_dir / "src",
    ]

    source_root: Path | None = None
    for candidate in candidate_roots:
        if (candidate / "profiles").exists() or (candidate / "cspTrustedSites").exists():
            source_root = candidate
            break

    if source_root is None:
        # Fall back to the provided directory
        source_root = manifest_dir

    issues.extend(check_profiles_for_login_ip_ranges(source_root / "profiles"))
    issues.extend(check_csp_trusted_sites(source_root / "cspTrustedSites"))
    issues.extend(check_cors_entries(source_root / "corsWhitelistOrigins"))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for network security misconfiguration: "
            "missing Login IP Ranges on privileged profiles, overly permissive CSP Trusted Sites, "
            "and insecure CORS entries."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help=(
            "Root directory of the Salesforce metadata export or SFDX project "
            "(default: current directory)."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_network_security_and_trusted_ips(manifest_dir)

    if not issues:
        print("No network security issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
