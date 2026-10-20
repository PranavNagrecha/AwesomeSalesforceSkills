#!/usr/bin/env python3
"""Checker script for Experience Cloud SEO Settings skill.

Inspects Salesforce metadata retrieved into a local directory (--manifest-dir):

- CustomSite files (`*.site-meta.xml` or `*.site` under a `sites` folder; api_meta 264 L49364-49407)
    ERROR  unparseable XML
    WARN   `robotsTxtPage` names a Visualforce page that is not in `pages/`
    INFO   no `robotsTxtPage` (no custom robots.txt is wired to the site); the page lacks
           `contentType="text/plain"` (UNVERIFIED 2026-10-20: the attribute set is Help-only)
- robots page paths vs ExperienceBundle `urlPathPrefix` (api_meta 264 L62430-62435)
    WARN   the page uses `/s/` paths but a bundle's urlPathPrefix does not end in `/s`
           (or the reverse is not checked, because the prefix alone cannot say)
- ExperienceBundle meta files (`*.site-meta.xml` under `experiences`; api_meta 264 L62384-62444)
    ERROR  unparseable XML; missing Required `label` or `type`; `type` not ChatterNetworkPicasso
    INFO   a config JSON with no `preferredDomain` (L62656-62658)
- ExperienceBundle views (`experiences/**/views/*.json`; api_meta 264 L63443-63448)
    ERROR  invalid JSON
    INFO   an SEO assistant component whose pageTitle and description are both empty

The earlier rules were removed because their premises are not in the corpus: that the robots
page must be named `robots`, that a sandbox disables SEO, and that Knowledge articles need a
topic to enter a sitemap (the corpus has no sitemap line at all).

Exit codes: ERROR findings exit 1 always; WARN and INFO findings exit 0 unless --strict; a
directory with nothing to check prints one WARN and exits 0; a missing path is an ERROR and
exits 1. Stdlib only.

Usage:
    python3 check_experience_cloud_seo_settings.py --manifest-dir path/to/metadata [--strict]
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SEO_DEFINITIONS = ("community_builder:seoAssistant", "forceCommunity:seoAssistant")  # L63443-63444


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Experience Cloud SEO settings in a retrieved Salesforce metadata tree.",
    )
    parser.add_argument("--manifest-dir", default=".", help="Root directory of the Salesforce metadata (default: current directory).")
    parser.add_argument("--strict", action="store_true", help="exit 1 on WARN and INFO findings too")
    return parser.parse_args()


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def text_of(el: ET.Element, name: str) -> str | None:
    for c in el:
        if local(c.tag) == name:
            return (c.text or "").strip()
    return None


def site_files(root: Path, under: str) -> list[Path]:
    out = []
    for p in root.rglob("*"):
        if p.is_file() and (p.name.endswith(".site-meta.xml") or p.name.endswith(".site")) and under in p.parts:
            out.append(p)
    return sorted(out)


def bundle_prefixes(root: Path) -> list[str]:
    prefixes = []
    for p in site_files(root, "experiences"):
        try:
            el = ET.parse(p).getroot()
        except (ET.ParseError, OSError):
            continue
        value = text_of(el, "urlPathPrefix")
        if value:
            prefixes.append(value)
    return prefixes


def find_components(obj: object) -> list[dict]:
    found: list[dict] = []
    if isinstance(obj, dict):
        if obj.get("definition") in SEO_DEFINITIONS:
            found.append(obj)
        for v in obj.values():
            found.extend(find_components(v))
    elif isinstance(obj, list):
        for v in obj:
            found.extend(find_components(v))
    return found


def check_custom_sites(root: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    prefixes = bundle_prefixes(root)
    for path in site_files(root, "sites"):
        try:
            el = ET.parse(path).getroot()
        except (ET.ParseError, OSError) as exc:
            out.append(("ERROR", f"{path.name}: XML does not parse ({exc})"))
            continue
        page = text_of(el, "robotsTxtPage")
        if not page:
            out.append(("INFO", f"{path.name}: no robotsTxtPage; no custom robots.txt page is wired to this site (api_meta 264 L49406-49407)"))
            continue
        matches = list(root.rglob(f"{page}.page"))
        if not matches:
            out.append(("WARN", f"{path.name}: robotsTxtPage '{page}' has no {page}.page file in this tree"))
            continue
        content = matches[0].read_text(encoding="utf-8", errors="replace")
        if "text/plain" not in content:
            out.append(("INFO", f"{matches[0].name}: no contentType=\"text/plain\" (UNVERIFIED 2026-10-20: the attribute set is Help-only)"))
        if "/s/" in content and prefixes and not any(p.rstrip("/").endswith("/s") for p in prefixes):
            out.append(("WARN", f"{matches[0].name}: uses /s/ paths but no ExperienceBundle urlPathPrefix ends in /s (api_meta 264 L62430-62435)"))
    return out


def check_bundles(root: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for path in site_files(root, "experiences"):
        try:
            el = ET.parse(path).getroot()
        except (ET.ParseError, OSError) as exc:
            out.append(("ERROR", f"{path.name}: XML does not parse ({exc})"))
            continue
        label, btype = text_of(el, "label"), text_of(el, "type")
        if not label:
            out.append(("ERROR", f"{path.name}: <label> is Required (api_meta 264 L62422)"))
        if not btype:
            out.append(("ERROR", f"{path.name}: <type> is Required (L62424)"))
        elif btype != "ChatterNetworkPicasso":
            out.append(("ERROR", f"{path.name}: type '{btype}' is not ChatterNetworkPicasso, the only supported value (L62424-62425)"))
    for path in root.glob("**/experiences/**/config/*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if isinstance(data, dict) and "mainAppPageId" in data and not data.get("preferredDomain"):
            out.append(("INFO", f"{path.name}: no preferredDomain; it names the domain used for indexing the site's pages (api_meta 264 L62656-62658)"))
    return out


def check_views(root: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for path in root.glob("**/experiences/**/views/*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        except ValueError as exc:
            out.append(("ERROR", f"{path.name}: invalid JSON ({exc})"))
            continue
        for comp in find_components(data):
            attrs = comp.get("attributes") or {}
            if not (attrs.get("pageTitle") or "").strip() and not (attrs.get("description") or "").strip():
                out.append(("INFO", f"{path.name}: SEO assistant has empty pageTitle and description (api_meta 264 L63443-63448)"))
    return out


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    scanned = site_files(root, "sites") + site_files(root, "experiences") + list(root.glob("**/experiences/**/*.json"))
    if not scanned:
        print(f"WARN: no CustomSite or ExperienceBundle files under {root}; nothing to check")
        return 1 if args.strict else 0
    findings = check_custom_sites(root) + check_bundles(root) + check_views(root)
    if not findings:
        print("No SEO configuration issues found.")
        return 0
    for sev, msg in findings:
        print(f"{sev}: {msg}")
    if any(sev == "ERROR" for sev, _ in findings):
        return 1
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
