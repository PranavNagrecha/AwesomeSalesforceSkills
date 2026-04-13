#!/usr/bin/env python3
"""Checker script for OmniStudio Scalability Patterns skill.

Scans Salesforce metadata for OmniStudio scalability anti-patterns:
- Integration Procedures using fire-and-forget where Queueable Chainable is needed
- Missing IP-level caching on likely reference-data IPs
- OmniScript / Experience Cloud site metadata indicating Aura runtime (LWR not configured)
- Batch Apex scheduled classes that may conflict with portal peak hours

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omnistudio_scalability_patterns.py [--help]
    python3 check_omnistudio_scalability_patterns.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _walk_files(root: Path, suffix: str) -> List[Path]:
    """Return all files under root matching the given suffix."""
    results = []
    for dirpath, _dirs, files in os.walk(root):
        for fname in files:
            if fname.endswith(suffix):
                results.append(Path(dirpath) / fname)
    return results


def _parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file; return None on parse error."""
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_ip_fire_and_forget_misuse(manifest_dir: Path) -> List[str]:
    """Flag Integration Procedures using useFuture=true.

    Fire-and-forget (useFuture=true) does NOT escape SOQL governor limits.
    Practitioners who see limit errors and add fire-and-forget are applying
    the wrong fix. Flag these for manual review.
    """
    issues = []
    # OmniStudio IPs are stored as JSON or XML depending on deployment method.
    # Check JSON-based IP definitions (common in DX format).
    for ip_file in _walk_files(manifest_dir, ".json"):
        try:
            with ip_file.open(encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        # OmniStudio IP JSON has a top-level "Type" of "IntegrationProcedure"
        ip_type = data.get("Type") or data.get("type") or ""
        if "IntegrationProcedure" not in str(ip_type):
            # Check for nested IPs in omnistudio export bundles
            elements = data.get("elements") or data.get("Elements") or []
            if not elements:
                continue

        use_future = data.get("useFuture") or data.get("UseFuture")
        if str(use_future).lower() == "true":
            ip_name = data.get("Name") or data.get("name") or ip_file.stem
            issues.append(
                f"Integration Procedure '{ip_name}' uses fire-and-forget (useFuture=true). "
                f"This removes UI blocking but does NOT escape SOQL governor limits. "
                f"If limit errors occur under load, Queueable Chainable is required. "
                f"File: {ip_file}"
            )
    return issues


def check_missing_ip_caching(manifest_dir: Path) -> List[str]:
    """Flag IPs with no caching configured that query reference data patterns.

    Heuristic: IPs with 'lookup', 'catalog', 'reference', 'config', 'master'
    in their name and no cacheOutput setting are candidates for caching review.
    """
    issues = []
    reference_data_keywords = {"lookup", "catalog", "reference", "config", "master", "product", "tier"}

    for ip_file in _walk_files(manifest_dir, ".json"):
        try:
            with ip_file.open(encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        ip_type = data.get("Type") or data.get("type") or ""
        if "IntegrationProcedure" not in str(ip_type):
            continue

        ip_name = (data.get("Name") or data.get("name") or ip_file.stem).lower()
        name_parts = set(ip_name.replace("-", "_").replace(".", "_").split("_"))

        if name_parts & reference_data_keywords:
            cache_output = data.get("cacheOutput") or data.get("CacheOutput")
            if not cache_output or str(cache_output).lower() != "true":
                issues.append(
                    f"Integration Procedure '{data.get('Name') or ip_file.stem}' appears to handle "
                    f"reference data (name contains a reference-data keyword) but does not have "
                    f"cacheOutput enabled. Consider IP-level caching to reduce concurrent SOQL load. "
                    f"File: {ip_file}"
                )
    return issues


def check_aura_experience_cloud_sites(manifest_dir: Path) -> List[str]:
    """Flag Experience Cloud site metadata that may indicate non-LWR runtime.

    ExperienceBundle metadata in 'experiences/' folders contains site configuration.
    A non-LWR site at high volume lacks CDN page caching.
    """
    issues = []
    experiences_dir = manifest_dir / "experiences"
    if not experiences_dir.exists():
        # Try force-app path
        experiences_dir = manifest_dir / "force-app" / "main" / "default" / "experiences"

    if not experiences_dir.exists():
        return issues

    for config_file in _walk_files(experiences_dir, ".json"):
        if config_file.name != "config.json":
            continue
        try:
            with config_file.open(encoding="utf-8") as f:
                config = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        site_type = config.get("siteType") or config.get("type") or ""
        template = config.get("template") or config.get("Template") or ""

        # LWR sites have template type containing 'LWR' or 'BrandingSet'
        # Aura sites use 'Kokua', 'Aloha', 'Napili', 'Salesforce Tabs + Visualforce'
        aura_indicators = {"kokua", "aloha", "napili", "tabs", "visualforce", "aura"}
        template_lower = str(template).lower()
        is_aura = any(ind in template_lower for ind in aura_indicators)

        if is_aura:
            site_name = config.get("name") or config_file.parent.name
            issues.append(
                f"Experience Cloud site '{site_name}' appears to use an Aura-based template "
                f"('{template}'). Aura sites cannot leverage CDN page caching and will not scale "
                f"to high concurrent user loads. Migrate to LWR runtime for high-volume portal "
                f"deployments. File: {config_file}"
            )

    return issues


def check_scheduled_apex_naming_patterns(manifest_dir: Path) -> List[str]:
    """Flag Scheduled Apex that may indicate potential conflict with portal peak hours.

    Checks for Apex classes with ScheduledApex or Schedulable interface references
    that have names suggesting they run during business hours (contain 'daily', 'morning',
    'business', 'hourly') — these could compete with portal concurrent Apex slots.

    This is advisory only; actual schedule times cannot be inferred from metadata alone.
    """
    issues = []
    peak_hour_keywords = {"daily", "morning", "business", "hourly", "noon", "daytime"}

    apex_dir = manifest_dir / "classes"
    if not apex_dir.exists():
        apex_dir = manifest_dir / "force-app" / "main" / "default" / "classes"

    if not apex_dir.exists():
        return issues

    for cls_file in _walk_files(apex_dir, ".cls"):
        try:
            content = cls_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        if "implements Schedulable" not in content and "Schedulable" not in content:
            continue

        class_name = cls_file.stem.lower()
        name_parts = set(class_name.replace("_", " ").split())

        if name_parts & peak_hour_keywords:
            issues.append(
                f"Scheduled Apex class '{cls_file.stem}' implements Schedulable and its name "
                f"suggests it may run during business hours. Scheduled Apex consuming long-running "
                f"Apex slots during portal peak hours competes with portal user sessions against the "
                f"25-concurrent-long-running-Apex org-wide limit. Verify its schedule and consider "
                f"moving heavy scheduled jobs to off-peak hours. File: {cls_file}"
            )

    return issues


def check_ip_queueable_chainable_usage(manifest_dir: Path) -> List[str]:
    """Report Integration Procedures using Queueable Chainable (informational).

    This is a positive indicator — just report so reviewers can confirm
    it is used appropriately (governor limit escape, not just UI unblocking).
    """
    infos = []
    for ip_file in _walk_files(manifest_dir, ".json"):
        try:
            with ip_file.open(encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        ip_type = data.get("Type") or data.get("type") or ""
        if "IntegrationProcedure" not in str(ip_type):
            continue

        exec_mode = data.get("executionMode") or data.get("ExecutionMode") or ""
        if "QueueableChainable" in str(exec_mode) or "queueableChainable" in str(exec_mode).lower():
            ip_name = data.get("Name") or data.get("name") or ip_file.stem
            infos.append(
                f"INFO: Integration Procedure '{ip_name}' uses Queueable Chainable execution mode. "
                f"Confirm this is for governor limit escape (SOQL/CPU pressure under concurrency), "
                f"not merely for UI unblocking (which fire-and-forget would suffice for). "
                f"File: {ip_file}"
            )
    return infos


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_omnistudio_scalability_patterns(manifest_dir: Path) -> Tuple[List[str], List[str]]:
    """Return (issues, infos) found in the manifest directory.

    issues: actionable problems that should be addressed
    infos: informational findings for manual review
    """
    issues: List[str] = []
    infos: List[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues, infos

    issues.extend(check_ip_fire_and_forget_misuse(manifest_dir))
    issues.extend(check_missing_ip_caching(manifest_dir))
    issues.extend(check_aura_experience_cloud_sites(manifest_dir))
    issues.extend(check_scheduled_apex_naming_patterns(manifest_dir))
    infos.extend(check_ip_queueable_chainable_usage(manifest_dir))

    return issues, infos


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check OmniStudio metadata for scalability anti-patterns. "
            "Reports fire-and-forget misuse, missing IP caching, non-LWR Experience Cloud sites, "
            "and scheduled Apex that may conflict with portal concurrency."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--show-info",
        action="store_true",
        default=False,
        help="Also show informational findings (default: warnings and errors only).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues, infos = check_omnistudio_scalability_patterns(manifest_dir)

    if args.show_info:
        for info in infos:
            print(f"INFO:  {info}")

    if not issues:
        print("No scalability anti-patterns found.")
        if infos and not args.show_info:
            print(f"({len(infos)} informational finding(s) — run with --show-info to see)")
        return 0

    for issue in issues:
        print(f"WARN:  {issue}", file=sys.stderr)

    print(
        f"\n{len(issues)} issue(s) found. Review references/gotchas.md and "
        "references/llm-anti-patterns.md in the omnistudio-scalability-patterns skill.",
        file=sys.stderr,
    )

    return 1


if __name__ == "__main__":
    sys.exit(main())
