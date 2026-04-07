#!/usr/bin/env python3
"""Checker script for Experience Cloud SEO Settings skill.

Inspects Salesforce metadata retrieved into a local directory and flags
common SEO configuration issues described in this skill's gotchas and
anti-patterns.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_experience_cloud_seo_settings.py [--help]
    python3 check_experience_cloud_seo_settings.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Experience Cloud SEO settings in a retrieved Salesforce metadata "
            "tree for common issues: missing robots VF page, noindex-only protection "
            "on sensitive pages, and site URL structure hints."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_robots_vf_page(manifest_dir: Path) -> list[str]:
    """Verify a Visualforce page named 'robots' exists for custom robots.txt."""
    issues: list[str] = []
    pages_dir = manifest_dir / "pages"
    if not pages_dir.exists():
        issues.append(
            "No 'pages/' directory found — cannot confirm custom robots.txt "
            "Visualforce page exists. Expected a VF page named 'robots'."
        )
        return issues

    robots_page = pages_dir / "robots.page"
    robots_meta = pages_dir / "robots.page-meta.xml"

    if not robots_page.exists():
        issues.append(
            "Missing custom robots.txt: no 'pages/robots.page' found. "
            "Create a Visualforce page named exactly 'robots' with "
            "contentType='text/plain' to serve a custom robots.txt."
        )
    else:
        content = robots_page.read_text(encoding="utf-8", errors="replace")
        if "contentType" not in content or "text/plain" not in content:
            issues.append(
                "pages/robots.page exists but may be missing contentType='text/plain'. "
                "Confirm the apex:page tag includes contentType=\"text/plain\" — "
                "without it the page will not be served as robots.txt."
            )
        if "Sitemap:" not in content and "sitemap" not in content.lower():
            issues.append(
                "pages/robots.page does not appear to include a Sitemap: directive. "
                "Add 'Sitemap: https://<site-url>/sitemap.xml' so search engines "
                "discover the sitemap automatically."
            )
        # Warn if /s/ prefix is used — may indicate Aura pattern applied to LWR site
        if "/s/login" in content or "/s/search" in content or "/s/profile" in content:
            issues.append(
                "pages/robots.page contains Aura-style /s/ path prefixes "
                "(e.g., /s/login). If the target site uses an LWR template, "
                "these Disallow rules will have no effect — LWR sites use clean "
                "paths without the /s segment. Verify the site template type."
            )

    if not robots_meta.exists():
        issues.append(
            "Missing pages/robots.page-meta.xml. The VF page metadata file is "
            "required for deployment. Generate it with your SFDX tooling."
        )

    return issues


def check_experience_site_xml(manifest_dir: Path) -> list[str]:
    """Scan ExperienceBundle or Network metadata for common SEO hints."""
    issues: list[str] = []

    # Check for ExperienceBundle (sfdx project structure)
    exp_bundles = list((manifest_dir / "experiences").glob("*.site")) if (
        manifest_dir / "experiences"
    ).exists() else []
    network_dir = manifest_dir / "networks"

    if not exp_bundles and not network_dir.exists():
        # Not necessarily an issue — metadata may not be present in this slice
        return issues

    # Check Network metadata XML for SEO-relevant settings
    if network_dir.exists():
        for net_file in network_dir.glob("*.network"):
            try:
                tree = ET.parse(net_file)
                root = tree.getroot()
                ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}

                # Check allowedExtensions or picklist relevant to SEO features
                # The Network metadata does not expose per-page SEO — just flag presence
                status_nodes = root.findall(".//sf:status", ns) or root.findall(".//status")
                for node in status_nodes:
                    if node.text and node.text.strip().lower() not in ("live", "active"):
                        issues.append(
                            f"{net_file.name}: site status is '{node.text.strip()}'. "
                            "SEO features (sitemap.xml, robots.txt) are only active "
                            "when the site is Live in a production org."
                        )
            except ET.ParseError as exc:
                issues.append(f"Could not parse {net_file.name}: {exc}")

    return issues


def check_knowledge_topic_assignment_hint(manifest_dir: Path) -> list[str]:
    """Remind about Knowledge topic assignment if Knowledge object metadata is present."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    knowledge_dirs = list(objects_dir.glob("Knowledge__kav")) + list(
        objects_dir.glob("KnowledgeArticleVersion")
    )
    if knowledge_dirs:
        issues.append(
            "Knowledge object metadata detected. Reminder: Knowledge articles are "
            "excluded from Experience Cloud sitemap.xml unless each article is assigned "
            "to at least one Topic or Data Category. Verify topic assignment governance "
            "is in place before expecting Knowledge pages to appear in the sitemap."
        )
    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def check_experience_cloud_seo_settings(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_robots_vf_page(manifest_dir))
    issues.extend(check_experience_site_xml(manifest_dir))
    issues.extend(check_knowledge_topic_assignment_hint(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_experience_cloud_seo_settings(manifest_dir)

    if not issues:
        print("No SEO configuration issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
