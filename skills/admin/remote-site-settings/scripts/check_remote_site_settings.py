#!/usr/bin/env python3
"""Checker script for Remote Site Settings skill.

Checks RemoteSiteSetting metadata and Apex callout code for common issues.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_remote_site_settings.py [--help]
    python3 check_remote_site_settings.py --manifest-dir path/to/metadata [--strict]

Rules (Metadata API Developer Guide 264, RemoteSiteSetting, api_meta L106496-106545):
  ERROR  a .remoteSite file that does not parse as XML
  ERROR  a missing Required field: disableProtocolSecurity, isActive, url
  WARN   disableProtocolSecurity=true — lets code pass data between an HTTPS
         session and an HTTP session (L106516-106521); it is not a certificate switch
  WARN   url uses http://
  WARN   an Apex class sets a raw https?:// endpoint that no registered URL
         shares a scheme+host prefix with (matching rules are not documented,
         so this is a heuristic); classes using callout: named credentials
         need no Remote Site Setting (apexdev 264 L34761); callout: endpoints
         are never matched, raw endpoints in the same class still are

Exit codes: ERROR findings and a missing --manifest-dir exit 1; WARN findings
exit 0 unless --strict; an empty directory prints one WARN and exits 0.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REQUIRED_FIELDS = ("disableProtocolSecurity", "isActive", "url")
RSS_SUFFIXES = (".remoteSite", ".remoteSite-meta.xml")
URL_PATTERN = re.compile(r"""setEndpoint\(\s*["'](https?://[^"']+)["']""", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Remote Site Settings and Apex callout code for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument("--strict", action="store_true", help="Exit 1 when any WARN is reported.")
    return parser.parse_args()


def child(root: ET.Element, ns: str, name: str) -> ET.Element | None:
    found = root.find(f"{ns}{name}")
    return found if found is not None else None


def rss_files(manifest_dir: Path) -> list[Path]:
    return sorted(p for p in manifest_dir.rglob("*") if p.is_file() and p.name.endswith(RSS_SUFFIXES))


def check_metadata(manifest_dir: Path, registered: set[str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warns: list[str] = []
    for rss_file in rss_files(manifest_dir):
        name = rss_file.name.split(".remoteSite")[0]
        try:
            root = ET.parse(rss_file).getroot()
        except (ET.ParseError, OSError) as exc:
            errors.append(f"{rss_file}: does not parse as XML ({exc})")
            continue
        ns = root.tag.split("}")[0] + "}" if root.tag.startswith("{") else ""
        for field in REQUIRED_FIELDS:
            elem = child(root, ns, field)
            if elem is None or not (elem.text or "").strip():
                errors.append(f"Remote Site Setting '{name}': Required field <{field}> is missing or empty")
        dps = child(root, ns, "disableProtocolSecurity")
        if dps is not None and (dps.text or "").strip().lower() == "true":
            warns.append(
                f"Remote Site Setting '{name}': disableProtocolSecurity is true — code can pass data "
                "between HTTPS and HTTP sessions; keep false unless the security implication is signed off"
            )
        url = child(root, ns, "url")
        url_text = (url.text or "").strip() if url is not None else ""
        if url_text:
            registered.add(url_text.rstrip("/").lower())
            if url_text.lower().startswith("http://"):
                warns.append(f"Remote Site Setting '{name}': URL uses HTTP (not HTTPS): '{url_text}'")
    return errors, warns


def check_apex(manifest_dir: Path, registered: set[str]) -> list[str]:
    warns: list[str] = []
    for apex_file in sorted(manifest_dir.rglob("*.cls")):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Only raw https?:// endpoints match URL_PATTERN; callout: (named
        # credential) endpoints never do, so a class that mixes both still has
        # its raw endpoints checked.
        for match in URL_PATTERN.finditer(content):
            parts = match.group(1).split("/")
            if len(parts) < 3:
                continue
            base = "/".join(parts[:3]).lower()
            if not any(base.startswith(r) or r.startswith(base) for r in registered):
                warns.append(
                    f"Apex class '{apex_file.stem}': endpoint '{base}' has no Remote Site Setting in "
                    "this directory — register it, or switch the endpoint to a named credential"
                )
    return warns


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.is_dir():
        print(f"ERROR: manifest directory not found: {manifest_dir}")
        return 1
    if not rss_files(manifest_dir) and next(manifest_dir.rglob("*.cls"), None) is None:
        print(f"WARN: no .remoteSite or .cls files under {manifest_dir}; nothing was checked")
        return 0

    registered: set[str] = set()
    errors, warns = check_metadata(manifest_dir, registered)
    warns.extend(check_apex(manifest_dir, registered))

    for e in errors:
        print(f"ERROR: {e}")
    for w in warns:
        print(f"WARN: {w}")
    if not errors and not warns:
        print("No Remote Site Settings issues found.")
    if errors:
        return 1
    return 1 if (warns and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
