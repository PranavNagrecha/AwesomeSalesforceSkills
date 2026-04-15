#!/usr/bin/env python3
"""Checker script for Analytics Adoption Strategy skill.

Checks org metadata or configuration relevant to Analytics Adoption Strategy.
Uses stdlib only — no pip dependencies.

Checks performed:
  - Detects Lightning page metadata that embeds a CRM Analytics dashboard
    component and flags pages where no filter configuration is found
    (embedded dashboard without filter pass-through is the most common
    misconfiguration in analytics adoption deployments).
  - Detects CRM Analytics app metadata and flags apps with no shared
    users or groups (unshared apps cannot drive adoption).

Usage:
    python3 check_analytics_adoption_strategy.py [--help]
    python3 check_analytics_adoption_strategy.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Analytics Adoption Strategy configuration and metadata for "
            "common issues: embedded dashboards without filter pass-through, "
            "unshared analytics apps."
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

def _find_files(root: Path, suffix: str) -> list[Path]:
    """Return all files under root with the given suffix, recursively."""
    return sorted(root.rglob(f"*{suffix}"))


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Check 1: Embedded CRM Analytics dashboard without filter pass-through
# ---------------------------------------------------------------------------

# The CRM Analytics Dashboard component in a Lightning page XML looks like:
#   <component>analytics:analyticsCloudDashboard</component>  (older)
#   <component>c:analyticsDashboard</component>               (custom)
# or as a componentInstance with type containing "analytics" + "dashboard"
# The key signal is the component type name referencing analytics+dashboard
# AND no filter attribute value referencing {!recordId} or similar.

_ANALYTICS_DASHBOARD_COMPONENT_PATTERN = re.compile(
    r'<component[^>]*>\s*analytics:analyticsCloudDashboard\s*</component>|'
    r'componentType["\s]*[=:]["\s]*analytics:analyticsCloudDashboard',
    re.IGNORECASE,
)
_FILTER_CONFIGURED_PATTERN = re.compile(
    r'recordId|{!\s*recordId\s*}|filter.*=',
    re.IGNORECASE,
)


def check_embedded_dashboards_missing_filter(manifest_dir: Path) -> list[str]:
    """Flag Lightning pages that embed an analytics dashboard with no filter config."""
    issues: list[str] = []
    # Lightning page metadata files use the .flexipage-meta.xml suffix
    page_files = _find_files(manifest_dir, ".flexipage-meta.xml")
    for page_file in page_files:
        content = _read_text(page_file)
        if not _ANALYTICS_DASHBOARD_COMPONENT_PATTERN.search(content):
            continue  # no analytics dashboard component on this page
        # Page has an analytics dashboard component — check for filter config
        if not _FILTER_CONFIGURED_PATTERN.search(content):
            issues.append(
                f"EMBEDDED DASHBOARD — NO FILTER PASS-THROUGH: "
                f"{page_file} embeds a CRM Analytics dashboard but no filter "
                f"pass-through (recordId or filter attribute) was found. "
                f"The dashboard will show all data to all users. "
                f"Add a filter attribute mapping {{!recordId}} to the dashboard's "
                f"filter API name in the component configuration."
            )
    return issues


# ---------------------------------------------------------------------------
# Check 2: CRM Analytics app metadata with no sharing entries
# ---------------------------------------------------------------------------

# CRM Analytics app metadata (WaveApplication) uses .wapp-meta.xml
# Sharing entries appear as <shares> elements. An app with no sharing
# entries can never be discovered by non-admin users.

_SHARES_PATTERN = re.compile(r"<shares>", re.IGNORECASE)
_ACCESS_TYPE_PATTERN = re.compile(r"<accessType>", re.IGNORECASE)


def check_unshared_analytics_apps(manifest_dir: Path) -> list[str]:
    """Flag CRM Analytics app metadata files that have no sharing entries."""
    issues: list[str] = []
    wapp_files = _find_files(manifest_dir, ".wapp-meta.xml")
    for wapp_file in wapp_files:
        content = _read_text(wapp_file)
        if not _SHARES_PATTERN.search(content) and not _ACCESS_TYPE_PATTERN.search(content):
            issues.append(
                f"UNSHARED ANALYTICS APP: "
                f"{wapp_file} has no <shares> entries. "
                f"Non-admin users cannot see or open this app. "
                f"Configure app sharing in Analytics Studio > App > Share, "
                f"or add <shares> entries to the metadata before deployment."
            )
    return issues


# ---------------------------------------------------------------------------
# Check 3: Detect Adoption App presence (informational)
# ---------------------------------------------------------------------------

_ADOPTION_APP_NAME_PATTERN = re.compile(
    r"adoption|AdoptionAnalytics|analytics_adoption",
    re.IGNORECASE,
)


def check_adoption_app_present(manifest_dir: Path) -> list[str]:
    """Warn if no CRM Analytics app metadata resembles an Adoption App."""
    issues: list[str] = []
    wapp_files = _find_files(manifest_dir, ".wapp-meta.xml")
    if not wapp_files:
        return issues  # no analytics apps in manifest at all — skip
    adoption_apps = [
        f for f in wapp_files
        if _ADOPTION_APP_NAME_PATTERN.search(f.stem)
    ]
    if not adoption_apps:
        issues.append(
            "ADOPTION APP NOT FOUND: "
            "No CRM Analytics app metadata matching 'adoption' was found in the manifest. "
            "If the Analytics Adoption App has not been created, analytics usage cannot be measured. "
            "Confirm the Analytics Adoption Metadata managed package is installed, then create the "
            "Adoption Analytics template app in Analytics Studio."
        )
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_analytics_adoption_strategy(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_embedded_dashboards_missing_filter(manifest_dir))
    issues.extend(check_unshared_analytics_apps(manifest_dir))
    issues.extend(check_adoption_app_present(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_analytics_adoption_strategy(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
