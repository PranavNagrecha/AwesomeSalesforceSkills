#!/usr/bin/env python3
"""Checker script for Tableau ↔ Salesforce Connector skill.

Scans metadata for integration hygiene issues:
- Connected Apps for Tableau with Full scope
- CSP Trusted Sites missing for Tableau domains referenced in Lightning pages
- Lightning pages with iframe Tableau embeds

Usage:
    python3 check_tableau_salesforce_connector.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TABLEAU_NAME_PAT = re.compile(r"(?i)tableau")
FULL_SCOPE_PAT = re.compile(r"<scopes>Full</scopes>")
TABLEAU_IFRAME_PAT = re.compile(r"(?i)<iframe[^>]*src\s*=\s*['\"][^'\"]*tableau[^'\"]*['\"]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Tableau ↔ Salesforce connector hygiene.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of Salesforce metadata.")
    return parser.parse_args()


def check_connected_app_scopes(root: Path) -> list[str]:
    issues: list[str] = []
    ca_dir = root / "connectedApps"
    if not ca_dir.exists():
        return issues
    for path in ca_dir.glob("*.connectedApp-meta.xml"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if not TABLEAU_NAME_PAT.search(text) and not TABLEAU_NAME_PAT.search(path.name):
            continue
        if FULL_SCOPE_PAT.search(text):
            issues.append(
                f"{path.relative_to(root)}: Tableau Connected App with Full scope; narrow to api"
            )
    return issues


def collect_trusted_sites(root: Path) -> list[str]:
    trusted = []
    ts_dir = root / "cspTrustedSites"
    if not ts_dir.exists():
        return trusted
    for path in ts_dir.glob("*.cspTrustedSite-meta.xml"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        m = re.search(r"<endpointUrl>([^<]+)</endpointUrl>", text)
        if m:
            trusted.append(m.group(1))
    return trusted


def check_iframe_without_trust(root: Path) -> list[str]:
    issues: list[str] = []
    pages_dir = root / "flexipages"
    sections = [pages_dir] if pages_dir.exists() else []
    sections.append(root / "pages")
    sections.append(root / "lwc")
    sections.append(root / "aura")
    trusted = collect_trusted_sites(root)
    for section in sections:
        if not section.exists():
            continue
        for path in section.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            m = TABLEAU_IFRAME_PAT.search(text)
            if not m:
                continue
            url = m.group(0)
            if not any(site in url for site in trusted):
                issues.append(
                    f"{path.relative_to(root)}: Tableau iframe without matching CSP Trusted Site"
                )
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    issues: list[str] = []
    issues.extend(check_connected_app_scopes(root))
    issues.extend(check_iframe_without_trust(root))

    if not issues:
        print("No Tableau connector issues detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
