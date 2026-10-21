#!/usr/bin/env python3
"""Checker script for OmniStudio Admin Configuration skill.

Validates retrieved Salesforce metadata for OmniStudio admin configuration issues.

  O1  ERROR  A permission set or settings/custom-settings XML file that does not parse.
  O2  WARN   A runtimeNamespace element that is blank or not one of omnistudio,
             vlocity_ins, vlocity_cmt, vlocity_ps. The field and its values are
             Help-only (no Metadata API type in the corpus), so this is a WARN.
  O3  WARN   A permission set whose file name or label says OmniStudio but that
             declares no <license>. A permission set tied to a permission set
             license can be assigned only to users who hold it (secguide 262
             L1999-2004); `license` is the PermissionSet field that records the
             link (api_meta 264 L97527-97529).
  O4  INFO   A community/portal permission set that grants OmniStudio access but
             no custom permission named like OmniStudioCommunityUser. The
             permission name is Help-only; INFO never fails the run.

Removed rule (false premise): "OmniStudioAdmin referenced in a non-admin
profile" — profiles do not carry permission set assignments.

Exit codes: 1 on any ERROR or a missing --manifest-dir, or on a WARN under
--strict; 0 otherwise. An empty directory prints one WARN and exits 0.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omnistudio_admin_configuration.py --manifest-dir path/to/metadata [--strict]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Tuple

# Runtime Namespace values documented in Salesforce Help (not in the corpus).
VALID_NAMESPACES = {"omnistudio", "vlocity_ins", "vlocity_cmt", "vlocity_ps"}
COMMUNITY_HINTS = ("community", "portal", "experiencecloud", "guest")

Finding = Tuple[str, str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check OmniStudio admin configuration metadata for common issues.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of the Salesforce metadata (default: current directory).")
    parser.add_argument("--strict", action="store_true", help="Treat WARN findings as failures (exit 1).")
    return parser.parse_args()


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _parse(path: Path, findings: List[Finding]) -> Optional[ET.Element]:
    try:
        return ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        findings.append(("ERROR", f"O1  {path}: XML does not parse ({exc})"))
        return None


def _first_text(root: ET.Element, name: str) -> Optional[str]:
    for elem in root.iter():
        if _local(elem.tag) == name:
            return (elem.text or "").strip()
    return None


def check_namespace(manifest_dir: Path, findings: List[Finding]) -> None:
    for sub in ("settings", "customSettings", "objects", "customMetadata"):
        base = manifest_dir / sub
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or not (path.suffix == ".xml" or path.name.endswith((".settings", ".settings-meta.xml"))):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if "untimeNamespace" not in text:
                continue
            root = _parse(path, findings)
            if root is None:
                continue
            for name in ("runtimeNamespace", "RuntimeNamespace"):
                val = _first_text(root, name)
                if val is None:
                    continue
                if not val:
                    findings.append(("WARN", f"O2  {path}: Runtime Namespace is blank — set it to the installed namespace"))
                elif val not in VALID_NAMESPACES:
                    findings.append(("WARN", f"O2  {path}: Runtime Namespace '{val}' is not one of {', '.join(sorted(VALID_NAMESPACES))}"))


def check_permission_sets(manifest_dir: Path, findings: List[Finding]) -> None:
    paths = sorted(set(manifest_dir.rglob("*.permissionset-meta.xml")) | set(manifest_dir.rglob("*.permissionset")))
    for path in paths:
        root = _parse(path, findings)
        if root is None:
            continue
        label = _first_text(root, "label") or ""
        is_omni = "omnistudio" in (path.name + label).lower().replace("_", "").replace(" ", "")
        if is_omni and _first_text(root, "license") is None:
            findings.append(("WARN", f"O3  {path}: OmniStudio permission set declares no <license>; assign the OmniStudio permission set license first"))
        text = ET.tostring(root, encoding="unicode").lower()
        targets_community = any(h in (path.name + label).lower() for h in COMMUNITY_HINTS)
        if targets_community and "omnistudio" in text and "omnistudiocommunityuser" not in text:
            findings.append(("INFO", f"O4  {path}: community permission set with OmniStudio access but no OmniStudioCommunityUser custom permission (Help-only name)"))


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.is_dir():
        print(f"ERROR: manifest directory not found: {manifest_dir}")
        sys.exit(1)
    if not any(p.is_file() for p in manifest_dir.rglob("*")):
        print(f"WARN: {manifest_dir} is empty — nothing to check")
        return 0

    findings: List[Finding] = []
    check_namespace(manifest_dir, findings)
    check_permission_sets(manifest_dir, findings)

    for sev, msg in findings:
        print(f"{sev}: {msg}")
    errors = sum(1 for s, _ in findings if s == "ERROR")
    warns = sum(1 for s, _ in findings if s == "WARN")
    if not findings:
        print("OK: no OmniStudio admin configuration issues found.")
    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
