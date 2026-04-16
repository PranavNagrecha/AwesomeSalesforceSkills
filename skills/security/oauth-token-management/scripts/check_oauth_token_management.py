#!/usr/bin/env python3
"""Checker script for OAuth Token Management skill.

Inspects Connected App metadata for OAuth token *lifecycle* readiness:
  - oauthPolicy presence (required to reason about refresh token policy in XML)
  - refreshTokenPolicy under oauthPolicy when refresh-style scopes are granted
  - refreshTokenPolicy value ``zero`` (immediate expiry) vs unattended integrations

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_oauth_token_management.py --manifest-dir path/to/project
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _ns_strip(tag: str) -> str:
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _find_child(parent: ET.Element, local_name: str) -> ET.Element | None:
    for child in parent:
        if _ns_strip(child.tag) == local_name:
            return child
    return None


def _text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return (element.text or "").strip()


def _collect_scopes(root: ET.Element) -> set[str]:
    scopes: set[str] = set()
    for child in root:
        tag = _ns_strip(child.tag)
        if tag == "scopes" and child.text:
            scopes.add(child.text.strip().lower())
        elif tag == "oauthConfig":
            for sub in child:
                if _ns_strip(sub.tag) == "scopes" and sub.text:
                    scopes.add(sub.text.strip().lower())
    return scopes


def _needs_refresh_token_review(scopes: set[str]) -> bool:
    normalized = {"refresh_token", "offline_access", "refreshtoken"}
    for s in scopes:
        key = s.replace("-", "_")
        if key in normalized:
            return True
        if "refresh" in key:
            return True
    return False


def _find_oauth_policy(root: ET.Element) -> ET.Element | None:
    for child in root:
        if _ns_strip(child.tag) == "oauthPolicy":
            return child
    return None


def check_connected_app(path: Path) -> list[str]:
    """Return actionable issues for one Connected App metadata file."""
    issues: list[str] = []
    stem = path.name
    if stem.endswith(".connectedApp-meta.xml"):
        app_name = stem[: -len(".connectedApp-meta.xml")]
    elif stem.endswith(".connectedApp"):
        app_name = stem[: -len(".connectedApp")]
    else:
        app_name = path.stem

    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"[{app_name}] XML parse error: {exc}"]

    scopes = _collect_scopes(root)
    oauth_config = _find_child(root, "oauthConfig")
    if oauth_config is None and not scopes:
        return issues

    oauth_policy = _find_oauth_policy(root)
    if oauth_policy is None:
        if oauth_config is not None or _needs_refresh_token_review(scopes):
            issues.append(
                f"[{app_name}] Missing <oauthPolicy> block. "
                "Token session and refresh token policies cannot be verified from metadata."
            )
        return issues

    rt_el = _find_child(oauth_policy, "refreshTokenPolicy")
    rt_policy = _text(rt_el)

    if _needs_refresh_token_review(scopes):
        if not rt_policy:
            issues.append(
                f"[{app_name}] Grants refresh-style OAuth scopes but "
                "<oauthPolicy><refreshTokenPolicy> is empty or absent in metadata. "
                "Retrieve latest metadata after setting an explicit refresh policy."
            )
        elif rt_policy.lower() in {"zero", "0"}:
            issues.append(
                f"[{app_name}] refreshTokenPolicy is '{rt_policy}' (immediate expiry) "
                "while refresh scopes are present. Unattended jobs will fail when the "
                "access token expires unless the integration can re-authenticate interactively."
            )

    return issues


def check_oauth_token_management(manifest_dir: Path) -> list[str]:
    """Scan manifest tree for Connected Apps and return issues."""
    issues: list[str] = []
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    files = sorted(manifest_dir.rglob("*.connectedApp-meta.xml"))
    if not files:
        files = sorted(manifest_dir.rglob("*.connectedApp"))

    if not files:
        return [
            f"No Connected App metadata under {manifest_dir}. "
            "Retrieve with `sf project retrieve start --metadata ConnectedApp` "
            "to audit refresh token policies in source."
        ]

    for path in files:
        issues.extend(check_connected_app(path))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Connected App metadata for OAuth token lifecycle issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce project or metadata directory.",
    )
    args = parser.parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_oauth_token_management(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
