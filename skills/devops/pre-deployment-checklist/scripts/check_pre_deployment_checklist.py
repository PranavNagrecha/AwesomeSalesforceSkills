#!/usr/bin/env python3
"""Checker script for Pre-Deployment Checklist skill.

Scans a Salesforce metadata project directory for common pre-deployment issues:
- missing or unparseable package.xml; missing <version> (package.xml sample, api_meta 264 L1437-1444)
- Apex classes listed without any test class (RunLocalTests is the production default, api_meta 264 L4441-4442)
- Profiles in the manifest (Profile deploys overlay the target, api_meta 264 L100265-100268)
- destructive manifests: wildcards unsupported (L4707-4708), package.xml must sit beside them (L4722-4723)
- no backup directory

Severity contract: ERROR (unparseable XML, missing directory) exits 1 always. REVIEW and WARN
findings exit 0 unless --strict. An empty directory is one WARN, exit 0. Wildcard members in
package.xml are NOT flagged: the guide documents them for deploys (api_meta 264 L3169-3171).

Uses stdlib only. Usage:
    python3 check_pre_deployment_checklist.py --manifest-dir path/to/project [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"md": "http://soap.sforce.com/2006/04/metadata"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check pre-deployment readiness of a Salesforce metadata project.",
    )
    parser.add_argument("--manifest-dir", default=".", help="Root directory of the project (default: .).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on REVIEW/WARN findings too.")
    return parser.parse_args()


def find_package_xml(root: Path) -> Path | None:
    for candidate in (root / "manifest" / "package.xml", root / "package.xml", root / "src" / "package.xml"):
        if candidate.exists():
            return candidate
    return None


def read_manifest(path: Path) -> tuple[ET.Element | None, str | None]:
    try:
        return ET.parse(path).getroot(), None
    except ET.ParseError as exc:
        return None, f"ERROR: could not parse {path.name}: {exc}"


def members_by_type(root: ET.Element) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for types_el in root.findall("md:types", NS):
        name_el = types_el.find("md:name", NS)
        if name_el is None or not (name_el.text or "").strip():
            continue
        members = [(m.text or "").strip() for m in types_el.findall("md:members", NS) if (m.text or "").strip()]
        result.setdefault(name_el.text.strip(), []).extend(members)
    return result


def check_destructive(manifest_dir: Path, reviews: list[str], errors: list[str]) -> list[Path]:
    files = sorted(manifest_dir.rglob("destructiveChanges*.xml"))
    for path in files:
        root, err = read_manifest(path)
        if err:
            errors.append(err)
            continue
        if any("*" in m for ms in members_by_type(root).values() for m in ms):
            reviews.append(f"REVIEW: {path.name} uses a wildcard member; destructive manifests do not support wildcards.")
        if not (path.parent / "package.xml").exists():
            reviews.append(f"REVIEW: {path.name} has no package.xml in the same directory; the deploy needs one that lists no components.")
    return files


def scan(manifest_dir: Path) -> tuple[list[str], list[str], list[str]]:
    errors: list[str] = []
    reviews: list[str] = []
    warns: list[str] = []
    pkg_xml = find_package_xml(manifest_dir)
    destructive = check_destructive(manifest_dir, reviews, errors)
    has_destructive = bool(destructive)

    if pkg_xml is None:
        warns.append("WARN: no package.xml at manifest/package.xml, package.xml or src/package.xml (not needed for --source-dir deploys).")
    else:
        root, err = read_manifest(pkg_xml)
        if err:
            errors.append(err)
        elif root is not None:
            components = members_by_type(root)
            version_el = root.find("md:version", NS)
            if version_el is None or not (version_el.text or "").strip():
                warns.append(f"WARN: {pkg_xml.name} has no <version> element.")
            if not components and not has_destructive:
                warns.append(f"WARN: {pkg_xml.name} lists no <types>; nothing would be deployed.")
            if components and any(p.name == "destructiveChanges.xml" for p in destructive):
                reviews.append(
                    "REVIEW: destructiveChanges.xml deploys beside additions, so deletions run first by default; use destructiveChangesPre.xml "
                    "or destructiveChangesPost.xml when a package component still references a deleted one (api_meta 264 L4749-4758)."
                )
            apex = components.get("ApexClass", [])
            test_re = re.compile(r"test", re.IGNORECASE)
            if [c for c in apex if not test_re.search(c)] and not [c for c in apex if test_re.search(c)]:
                reviews.append("REVIEW: Apex classes are listed but no test class is; a production deploy with Apex runs RunLocalTests by default.")
            if components.get("Profile"):
                reviews.append(
                    f"REVIEW: {len(components['Profile'])} Profile(s) in the manifest. A Profile deploy overlays the target; a removed "
                    "permission stays unless the XML sets <value>false</value> explicitly."
                )

    backups = [manifest_dir / "backups", manifest_dir / "backup", manifest_dir.parent / "backups"]
    if not any(d.is_dir() and any(d.iterdir()) for d in backups):
        reviews.append("REVIEW: no backup directory found; retrieve the components being deployed first: sf project retrieve start --manifest package.xml --output-dir backups/YYYY-MM-DD/")
    return errors, reviews, warns


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.is_dir():
        print(f"ERROR: manifest directory not found: {manifest_dir}")
        sys.exit(1)
    if not any(manifest_dir.iterdir()):
        print(f"WARN: {manifest_dir} is empty; nothing to check.")
        return 1 if args.strict else 0

    errors, reviews, warns = scan(manifest_dir)
    for line in errors + warns + reviews:
        print(line)
    if errors:
        return 1
    if warns or reviews:
        return 1 if args.strict else 0
    print("Pre-deployment check passed. No issues found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
