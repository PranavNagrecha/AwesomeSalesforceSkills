#!/usr/bin/env python3
"""Checker script for Permission Set Deployment Ordering skill.

Scans a Salesforce metadata directory (source format) for deployment-ordering risks:
- a ConnectedApp whose <permissionSetName> names a PermissionSet in the same directory
  (documented link, api_meta 264 L37225-37226; the same-batch error is UNVERIFIED, so REVIEW)
- a PermissionSetGroup whose <permissionSets> or <mutingPermissionSets> name a set that is
  not in the directory (a muting set is matched against MutingPermissionSet files, api_meta 264
  L92416-92419). That the set must already exist in the target or ship in a prior deploy is
  UNVERIFIED (2026-10-20); the deploy-one-at-a-time rule is api_meta 264 L4246-4249, so REVIEW

Severity contract: ERROR (unparseable XML, missing directory) exits 1 always.
REVIEW and WARN findings exit 0 unless --strict. An empty directory is one WARN, exit 0.

Uses stdlib only. Usage:
    python3 check_permission_set_deployment_ordering.py --manifest-dir path/to/metadata [--strict]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"
SUFFIXES = {
    "pset": (".permissionset-meta.xml", ".permissionset"),
    "psg": (".permissionsetgroup-meta.xml", ".permissionsetgroup"),
    "app": (".connectedApp-meta.xml", ".connectedApp"),
    # MutingPermissionSet is its own type: mutingpermissionsets/<Name>.mutingpermissionset (api_meta 264 L92416-92419)
    "mute": (".mutingpermissionset-meta.xml", ".mutingpermissionset"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Permission Set deployment metadata for ordering and safety issues.",
    )
    parser.add_argument("--manifest-dir", default=".", help="Root directory of the metadata (default: .).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on REVIEW/WARN findings too.")
    return parser.parse_args()


def collect(manifest_dir: Path, kind: str) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for suffix in SUFFIXES[kind]:
        for path in manifest_dir.rglob(f"*{suffix}"):
            found[path.name[: -len(suffix)]] = path
    return found


def texts(root: ET.Element, tag: str) -> list[str]:
    return [(e.text or "").strip() for e in root.findall(f"{NS}{tag}") if (e.text or "").strip()]


def load(path: Path, errors: list[str]) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        errors.append(f"ERROR: could not parse {path.name}: {exc}")
        return None


def scan(manifest_dir: Path) -> tuple[list[str], list[str], int]:
    errors: list[str] = []
    reviews: list[str] = []
    psets = collect(manifest_dir, "pset")
    psgs = collect(manifest_dir, "psg")
    apps = collect(manifest_dir, "app")
    mutes = collect(manifest_dir, "mute")

    for name, path in apps.items():
        root = load(path, errors)
        if root is None:
            continue
        for ps_name in texts(root, "permissionSetName"):
            if ps_name in psets:
                reviews.append(
                    f"REVIEW: ConnectedApp '{name}' names PermissionSet '{ps_name}' in permissionSetName and both are in "
                    f"this package. Deploy them as separate, ordered deploys as a precaution."
                )

    for name, path in psgs.items():
        root = load(path, errors)
        if root is None:
            continue
        for tag, pool in (("permissionSets", psets), ("mutingPermissionSets", mutes)):
            for ps_name in texts(root, tag):
                if ps_name not in pool:
                    reviews.append(
                        f"REVIEW: PermissionSetGroup '{name}' lists '{ps_name}' in {tag}, which is not in this package. "
                        f"Make sure it already exists in the target org or deploy it in a prior batch."
                    )
    for path in list(psets.values()) + list(mutes.values()):
        load(path, errors)
    return errors, reviews, len(psets) + len(psgs) + len(apps) + len(mutes)


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.is_dir():
        print(f"ERROR: manifest directory not found: {manifest_dir}")
        sys.exit(1)

    errors, reviews, count = scan(manifest_dir)
    if count == 0:
        print(f"WARN: no permission set, group or connected app metadata found under {manifest_dir}")
        return 1 if args.strict else 0

    for line in errors + reviews:
        print(line)
    if errors:
        return 1
    if reviews:
        return 1 if args.strict else 0
    print("No permission set deployment ordering issues found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
