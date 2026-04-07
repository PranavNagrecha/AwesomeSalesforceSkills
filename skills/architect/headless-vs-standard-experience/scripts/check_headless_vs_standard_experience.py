#!/usr/bin/env python3
"""Checker script for Headless vs Standard Experience skill.

Inspects a Salesforce metadata directory for signals relevant to the
Headless vs LWR vs Aura architecture decision:

- Detects Aura components in the metadata (migration cost signal)
- Detects LWR site configuration files
- Detects Aura-based Experience Cloud templates
- Checks for known LWS-incompatible library patterns in static resources
- Warns if an LWR site exists but no publish automation evidence is found

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_headless_vs_standard_experience.py [--help]
    python3 check_headless_vs_standard_experience.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for signals relevant to the "
            "Headless vs LWR vs Aura Experience Cloud architecture decision."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def count_aura_components(manifest_dir: Path) -> int:
    """Return the number of Aura component bundles found in the metadata."""
    aura_dir = manifest_dir / "aura"
    if not aura_dir.exists():
        return 0
    return sum(1 for p in aura_dir.iterdir() if p.is_dir())


def count_lwc_components(manifest_dir: Path) -> int:
    """Return the number of LWC component bundles found in the metadata."""
    lwc_dir = manifest_dir / "lwc"
    if not lwc_dir.exists():
        return 0
    return sum(1 for p in lwc_dir.iterdir() if p.is_dir())


def find_experience_cloud_sites(manifest_dir: Path) -> list[dict]:
    """Return a list of Experience Cloud site configurations found."""
    sites: list[dict] = []
    sites_dir = manifest_dir / "experiences"
    if not sites_dir.exists():
        return sites

    for config_file in sites_dir.rglob("*.json"):
        try:
            import json
            data = json.loads(config_file.read_text(encoding="utf-8"))
            site_type = data.get("type", "unknown")
            site_name = config_file.parent.name
            sites.append({"name": site_name, "type": site_type, "path": str(config_file)})
        except Exception:
            sites.append({"name": config_file.parent.name, "type": "parse-error", "path": str(config_file)})

    return sites


def check_network_metadata_for_template(manifest_dir: Path) -> list[dict]:
    """Check Network metadata XML files for template type (Aura vs LWR)."""
    findings: list[dict] = []
    networks_dir = manifest_dir / "networks"
    if not networks_dir.exists():
        return findings

    for xml_file in networks_dir.glob("*.network"):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
            # Template element identifies Aura vs LWR
            template_el = root.find(".//template", ns) or root.find(".//template")
            template_name = template_el.text if template_el is not None else "unknown"
            findings.append({"network": xml_file.stem, "template": template_name})
        except Exception:
            findings.append({"network": xml_file.stem, "template": "parse-error"})

    return findings


# Known LWS-incompatible patterns in JavaScript source
LWS_RISK_PATTERNS = [
    ("eval(", "uses eval() — incompatible with Lightning Web Security"),
    ("new Function(", "uses new Function() constructor — incompatible with Lightning Web Security"),
    ("__proto__", "accesses __proto__ directly — may fail under Lightning Web Security"),
    ("document.write(", "uses document.write() — blocked by Lightning Web Security"),
]


def check_static_resources_for_lws_risk(manifest_dir: Path) -> list[str]:
    """Scan static resource JS files for patterns known to fail under LWS."""
    warnings: list[str] = []
    static_dir = manifest_dir / "staticresources"
    if not static_dir.exists():
        return warnings

    for js_file in static_dir.rglob("*.js"):
        try:
            content = js_file.read_text(encoding="utf-8", errors="ignore")
            for pattern, description in LWS_RISK_PATTERNS:
                if pattern in content:
                    warnings.append(
                        f"Static resource '{js_file.name}' {description}. "
                        f"Test in LWR sandbox before migration."
                    )
                    break  # One warning per file is enough
        except Exception:
            pass

    return warnings


def check_headless_vs_standard_experience(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # --- Aura component count ---
    aura_count = count_aura_components(manifest_dir)
    if aura_count > 0:
        severity = "HIGH" if aura_count > 10 else "MEDIUM" if aura_count > 3 else "LOW"
        issues.append(
            f"[{severity}] Found {aura_count} Aura component bundle(s) in metadata. "
            f"Each must be rewritten as LWC before migrating to LWR. "
            f"This is the primary migration cost driver."
        )

    # --- LWC component count (informational) ---
    lwc_count = count_lwc_components(manifest_dir)
    if lwc_count > 0 and aura_count > 0:
        ratio = round(lwc_count / (aura_count + lwc_count) * 100)
        issues.append(
            f"[INFO] LWC readiness: {lwc_count} LWC components vs {aura_count} Aura components "
            f"({ratio}% already LWC). Remaining Aura components require rewrite for LWR migration."
        )

    # --- Experience Cloud site template detection ---
    network_findings = check_network_metadata_for_template(manifest_dir)
    for finding in network_findings:
        template = finding["template"].lower()
        if "aura" in template or "kokua" in template or "napili" in template:
            issues.append(
                f"[INFO] Network '{finding['network']}' uses an Aura-based template "
                f"('{finding['template']}'). Site is on Aura engine. "
                f"Migration to LWR requires Aura component rewrite."
            )
        elif "lwr" in template or "enhanced_lwr" in template:
            issues.append(
                f"[INFO] Network '{finding['network']}' uses an LWR template "
                f"('{finding['template']}'). Confirm publish workflow is automated in CI/CD."
            )

    # --- LWS compatibility risk in static resources ---
    lws_warnings = check_static_resources_for_lws_risk(manifest_dir)
    for warning in lws_warnings:
        issues.append(f"[LWS-RISK] {warning}")

    # --- Experience Cloud site config files ---
    sites = find_experience_cloud_sites(manifest_dir)
    lwr_sites = [s for s in sites if "lwr" in s["type"].lower()]
    if lwr_sites:
        issues.append(
            f"[INFO] {len(lwr_sites)} LWR site(s) detected. "
            f"Reminder: all component and content changes require explicit Publish "
            f"before users see them. Confirm this is in your deployment runbook."
        )

    if not issues:
        issues.append(
            "[INFO] No Aura components, LWS-risk libraries, or Experience Cloud site "
            "metadata detected in this directory. "
            "Run from the root of your Salesforce source directory for accurate results."
        )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    print(f"Checking: {manifest_dir.resolve()}")
    print("-" * 60)

    issues = check_headless_vs_standard_experience(manifest_dir)

    error_count = 0
    for issue in issues:
        if issue.startswith("[HIGH]") or issue.startswith("[LWS-RISK]"):
            print(f"WARN: {issue}", file=sys.stderr)
            error_count += 1
        elif issue.startswith("[MEDIUM]"):
            print(f"WARN: {issue}", file=sys.stderr)
            error_count += 1
        else:
            print(f"INFO: {issue}")

    print("-" * 60)
    if error_count == 0:
        print("No blocking issues found.")
        return 0
    else:
        print(f"{error_count} warning(s) require attention before migration.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
