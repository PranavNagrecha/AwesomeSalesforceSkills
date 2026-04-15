#!/usr/bin/env python3
"""Checker script for Integration Security Architecture skill.

Scans a Salesforce metadata directory for integration security issues:
- Named Credentials without explicit port in URL (mTLS port 8443 detection)
- Connected Apps with overly broad OAuth scopes
- Certificate and Key Management metadata for expiry proximity
- IP-range-based trusted networks in security settings

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_integration_security_architecture.py [--help]
    python3 check_integration_security_architecture.py --manifest-dir path/to/metadata
    python3 check_integration_security_architecture.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path


# OAuth scopes that indicate over-provisioning
_BROAD_SCOPES = {"full", "api", "web"}

# Warn if certificate expires within this many days
_CERT_EXPIRY_WARN_DAYS = 90

# Hard limit for certificates per org
_CERT_HARD_LIMIT = 50
_CERT_WARN_THRESHOLD = 35


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for integration security architecture issues:\n"
            "  - Named Credential URLs missing explicit port for mTLS\n"
            "  - Connected App OAuth scope over-provisioning\n"
            "  - Certificate count approaching org limit\n"
            "  - Certificates with upcoming expiry\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _find_xml_files(root: Path, suffix: str) -> list[Path]:
    """Return all XML files matching *suffix under root."""
    return list(root.rglob(f"*{suffix}"))


def check_named_credentials(manifest_dir: Path) -> list[str]:
    """Check Named Credential metadata for missing mTLS port and other issues."""
    issues: list[str] = []
    nc_files = _find_xml_files(manifest_dir, ".namedCredential")

    for nc_path in nc_files:
        try:
            tree = ET.parse(nc_path)
            root = tree.getroot()
        except ET.ParseError as exc:
            issues.append(f"[named-credential] Cannot parse {nc_path.name}: {exc}")
            continue

        # Strip namespace if present
        ns_match = re.match(r"\{(.+?)\}", root.tag)
        ns = f"{{{ns_match.group(1)}}}" if ns_match else ""

        endpoint_el = root.find(f"{ns}endpoint")
        if endpoint_el is None or not endpoint_el.text:
            continue

        endpoint = endpoint_el.text.strip()
        label_el = root.find(f"{ns}label")
        label = label_el.text.strip() if label_el is not None and label_el.text else nc_path.stem

        # Check: if certificate element present but URL does not specify port,
        # it may silently connect to 443 instead of the mTLS port.
        cert_el = root.find(f"{ns}certificate")
        if cert_el is not None and cert_el.text:
            # URL should have an explicit port for mTLS (commonly 8443)
            url_has_port = bool(re.search(r"https?://[^/]+:\d+", endpoint))
            if not url_has_port:
                issues.append(
                    f"[named-credential] '{label}' has a client certificate configured but "
                    f"no explicit port in endpoint URL '{endpoint}'. "
                    f"If the mTLS endpoint uses port 8443, the URL must include ':8443' explicitly."
                )

        # Check for http:// (non-TLS) endpoints with certificate configured — unusual
        if cert_el is not None and cert_el.text and endpoint.startswith("http://"):
            issues.append(
                f"[named-credential] '{label}' uses http:// (non-TLS) but has a certificate "
                f"configured. mTLS requires TLS — use https://."
            )

    return issues


def check_connected_apps(manifest_dir: Path) -> list[str]:
    """Check Connected App metadata for broad OAuth scope over-provisioning."""
    issues: list[str] = []
    ca_files = _find_xml_files(manifest_dir, ".connectedApp")

    for ca_path in ca_files:
        try:
            tree = ET.parse(ca_path)
            root = tree.getroot()
        except ET.ParseError as exc:
            issues.append(f"[connected-app] Cannot parse {ca_path.name}: {exc}")
            continue

        ns_match = re.match(r"\{(.+?)\}", root.tag)
        ns = f"{{{ns_match.group(1)}}}" if ns_match else ""

        label_el = root.find(f"{ns}label")
        label = label_el.text.strip() if label_el is not None and label_el.text else ca_path.stem

        # Collect OAuth scopes
        scope_els = root.findall(f".//{ns}oauthScope")
        scopes = {el.text.strip() for el in scope_els if el.text}

        broad = scopes & _BROAD_SCOPES
        if broad:
            issues.append(
                f"[connected-app] '{label}' grants broad OAuth scope(s): {sorted(broad)}. "
                f"Review whether the integration requires these scopes or if narrower scopes suffice. "
                f"Broad scopes increase the blast radius of a compromised token."
            )

    return issues


def check_certificates(manifest_dir: Path) -> list[str]:
    """Check certificate metadata for count and upcoming expiry."""
    issues: list[str] = []
    cert_files = _find_xml_files(manifest_dir, ".certificate")

    cert_count = len(cert_files)
    if cert_count >= _CERT_HARD_LIMIT:
        issues.append(
            f"[certificates] Org has reached {cert_count} certificates — at or above the hard "
            f"limit of {_CERT_HARD_LIMIT}. New certificates cannot be created. "
            f"Review and retire certificates from decommissioned integrations."
        )
    elif cert_count >= _CERT_WARN_THRESHOLD:
        issues.append(
            f"[certificates] Org has {cert_count} certificates (warning threshold: {_CERT_WARN_THRESHOLD}, "
            f"hard limit: {_CERT_HARD_LIMIT}). Consider certificate consolidation "
            f"(API gateway pattern) before reaching the limit."
        )

    today = date.today()

    for cert_path in cert_files:
        try:
            tree = ET.parse(cert_path)
            root = tree.getroot()
        except ET.ParseError as exc:
            issues.append(f"[certificate] Cannot parse {cert_path.name}: {exc}")
            continue

        ns_match = re.match(r"\{(.+?)\}", root.tag)
        ns = f"{{{ns_match.group(1)}}}" if ns_match else ""

        label_el = root.find(f"{ns}masterLabel")
        label = label_el.text.strip() if label_el is not None and label_el.text else cert_path.stem

        expiry_el = root.find(f"{ns}expirationDate")
        if expiry_el is not None and expiry_el.text:
            expiry_str = expiry_el.text.strip()[:10]  # YYYY-MM-DD
            try:
                expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                days_remaining = (expiry_date - today).days
                if days_remaining < 0:
                    issues.append(
                        f"[certificate] '{label}' EXPIRED on {expiry_date}. "
                        f"Any integration using this certificate will fail."
                    )
                elif days_remaining <= _CERT_EXPIRY_WARN_DAYS:
                    issues.append(
                        f"[certificate] '{label}' expires in {days_remaining} days ({expiry_date}). "
                        f"Initiate rotation now: generate new cert, update Named Credential reference, "
                        f"install new cert on remote system."
                    )
            except ValueError:
                pass  # Unrecognized date format — skip

    return issues


def check_network_access(manifest_dir: Path) -> list[str]:
    """Check security settings for IP-range-only network access policies."""
    issues: list[str] = []
    settings_files = (
        list(manifest_dir.rglob("SecuritySettings.settings"))
        + list(manifest_dir.rglob("*.securitySettings"))
    )

    for settings_path in settings_files:
        try:
            content = settings_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        # Heuristic: large numbers of IP ranges suggest IP-allowlist-heavy security model
        ip_range_count = len(re.findall(r"<ipRanges>", content))
        if ip_range_count >= 5:
            issues.append(
                f"[security-settings] {settings_path.name} defines {ip_range_count} IP range entries. "
                f"If this org is on Hyperforce, IP-based allowlisting for integration authentication "
                f"is unreliable — Hyperforce IPs are ephemeral. Consider mTLS as the authentication "
                f"mechanism instead of IP allowlisting."
            )

    return issues


def check_integration_security_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_named_credentials(manifest_dir))
    issues.extend(check_connected_apps(manifest_dir))
    issues.extend(check_certificates(manifest_dir))
    issues.extend(check_network_access(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_integration_security_architecture(manifest_dir)

    if not issues:
        print("No integration security architecture issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
