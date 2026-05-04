#!/usr/bin/env python3
"""Checker script for Salesforce Maps Setup skill.

Scans force-app/ metadata for common Salesforce Maps configuration risks. Stdlib only.

Checks:
  1. installedPackages/ — detect Salesforce Maps and legacy MapAnything coexistence
     (legacy `ma` / modern `maps` namespace) which signals an in-flight migration.
  2. PermissionSet metadata — confirm Maps permission set assignments exist;
     warn if a Maps package is installed but no PermissionSetAssignment-bearing
     metadata references it.
  3. Custom object metadata — flag references to FSL ServiceTerritory mixed with
     MapsTerritory__c in the same flow/automation, which indicates the persona-
     boundary anti-pattern.
  4. Apex class metadata — flag Apex that queries `MapsTerritory__c.maps__Polygon__c`
     (or legacy equivalents) without a conversion path, signaling the polygon-
     export anti-pattern.
  5. Custom Object / Custom Setting — flag if Live Tracking-related objects
     are present without a `*__b` Big Object archival counterpart in scope.

Usage:
    python3 check_salesforce_maps_setup.py
    python3 check_salesforce_maps_setup.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Salesforce Maps configuration for common setup risks.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def find_installed_maps_packages(root: Path) -> tuple[bool, bool, list[str]]:
    """Return (has_modern_maps, has_legacy_mapanything, issues)."""
    has_modern = False
    has_legacy = False
    issues: list[str] = []
    for f in root.rglob("*.installedPackage-meta.xml"):
        text = _read(f).lower()
        name = f.stem.replace(".installedPackage-meta", "").lower()
        if "salesforcemaps" in name or "salesforce_maps" in name or "salesforce-maps" in name or "maps__" in text:
            has_modern = True
        if "mapanything" in name or "ma__" in text:
            has_legacy = True
    if has_modern and has_legacy:
        issues.append(
            "REVIEW: Both modern Salesforce Maps and legacy MapAnything packages are installed. "
            "This is normal during a migration window but should not persist long-term. "
            "Confirm a migration plan exists (export polygons + saved routes from legacy, import to modern, cut over permissions)."
        )
    return has_modern, has_legacy, issues


def find_permission_set_grants(root: Path, has_maps: bool) -> list[str]:
    issues: list[str] = []
    if not has_maps:
        return issues
    found_maps_perm = False
    for f in root.rglob("*.permissionset-meta.xml"):
        text = _read(f)
        if "Salesforce Maps" in text or "salesforce_maps" in text.lower() or "maps__" in text:
            found_maps_perm = True
            break
        if "MapAnything" in text or "ma__" in text:
            found_maps_perm = True
            break
    if not found_maps_perm:
        issues.append(
            "BLOCKER: A Salesforce Maps package is installed but no PermissionSet metadata in scope grants Maps permissions. "
            "Package install does not assign permissions automatically — users will see no Maps tab on Day 1 without an explicit assignment."
        )
    return issues


PERSONA_BOUNDARY_PATTERNS = [
    re.compile(r"ServiceTerritory", re.IGNORECASE),
    re.compile(r"Maps[A-Za-z]*Territory", re.IGNORECASE),
]


def find_persona_boundary_violations(root: Path) -> list[str]:
    issues: list[str] = []
    for f in list(root.rglob("*.flow-meta.xml")) + list(root.rglob("*.cls")):
        text = _read(f)
        has_fsl = bool(re.search(r"\bServiceTerritory\b", text))
        has_maps_t = bool(re.search(r"\bMapsTerritory", text)) or "maps__Territory" in text
        if has_fsl and has_maps_t:
            issues.append(
                f"REVIEW: {f.relative_to(root)} references both ServiceTerritory (FSL) and MapsTerritory (Maps). "
                f"These are different products with different territory models; mixing them in one automation usually indicates a persona-boundary violation."
            )
    return issues


def find_polygon_export_risk(root: Path) -> list[str]:
    issues: list[str] = []
    polygon_patterns = [
        re.compile(r"maps__Polygon__c", re.IGNORECASE),
        re.compile(r"MapsTerritory__c\.\s*Polygon", re.IGNORECASE),
        re.compile(r"ma__Territory_Polygon__c", re.IGNORECASE),
    ]
    for f in root.rglob("*.cls"):
        text = _read(f)
        for pat in polygon_patterns:
            if pat.search(text):
                # Check whether the same file mentions GeoJSON or KML conversion
                if not re.search(r"GeoJSON|geo_json|geo-json|KML|Shapefile|WKT", text, re.IGNORECASE):
                    issues.append(
                        f"REVIEW: {f.relative_to(root)} reads Maps polygon data without an obvious conversion to GeoJSON/KML/WKT. "
                        f"Maps stores polygons in a package-internal format; non-Maps consumers (Tableau, BI) need an explicit conversion."
                    )
                break
    return issues


def find_live_tracking_volume_signals(root: Path) -> list[str]:
    issues: list[str] = []
    has_live_tracking_signal = False
    has_archival = False
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        name = f.name
        if "LiveTracking" in name or "BreadcrumbEvent" in name or "live_tracking" in name.lower():
            has_live_tracking_signal = True
        if name.endswith(".bigobject") or "__b" in name or "Archive" in name:
            has_archival = True
    if has_live_tracking_signal and not has_archival:
        issues.append(
            "REVIEW: Live Tracking metadata signals are present but no Big Object (`*__b`) or archive metadata is in scope. "
            "Live Tracking generates 100k+ records per day per 100 reps. Confirm an archival job exists before enabling org-wide."
        )
    return issues


def check_salesforce_maps_setup(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    has_modern, has_legacy, pkg_issues = find_installed_maps_packages(manifest_dir)
    issues.extend(pkg_issues)
    has_maps = has_modern or has_legacy
    issues.extend(find_permission_set_grants(manifest_dir, has_maps))
    issues.extend(find_persona_boundary_violations(manifest_dir))
    issues.extend(find_polygon_export_risk(manifest_dir))
    issues.extend(find_live_tracking_volume_signals(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()
    issues = check_salesforce_maps_setup(manifest_dir)

    if not issues:
        print("No Salesforce Maps setup issues detected.")
        return 0

    blockers = [i for i in issues if i.startswith("BLOCKER")]
    reviews = [i for i in issues if i.startswith("REVIEW")]

    print(f"Salesforce Maps Setup checks — {manifest_dir}")
    print(f"  blockers: {len(blockers)}  review: {len(reviews)}")
    print()
    for group_name, group in [("BLOCKERS", blockers), ("REVIEWS", reviews)]:
        if not group:
            continue
        print(f"--- {group_name} ---")
        for issue in group:
            print(f"  {issue}")
        print()

    return 1 if blockers else 0


if __name__ == "__main__":
    sys.exit(main())
