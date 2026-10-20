#!/usr/bin/env python3
"""Checker script for Compliant Data Sharing Setup skill.

Scans retrieved Salesforce metadata for CDS configuration issues:

- ERROR: an IndustriesSettings / ParticipantRole / object file that does not parse
- ERROR: an `enableCompliantDataSharingFor*` element that is not an IndustriesSettings field
  (the table lists Account, CustomObjects, Interaction, InteractionSummary, Opportunity —
  api_meta 264 L122543-122578; there is no ...ForFinancialDeal)
- ERROR: a ParticipantRole missing a Required field (defaultAccessLevel, masterLabel,
  parentObject) or with defaultAccessLevel outside Edit / None / Read (api_meta 264 L97096-97118)
- REVIEW: a FinancialDeal participant role while IndustriesSettings has enableDealManagement
  not true (L122580-122582)
- REVIEW: sharing rules on a CDS-enabled object — they grant access alongside CDS
- REVIEW: a CDS-enabled object whose sharingModel is ReadWrite / ReadWriteTransfer /
  FullAccess — the Private/Read-Only prerequisite is UNVERIFIED (2026-10-20), Help-only

ParticipantRole files are `.participantRole` in `participantRoles/` (api_meta 264 L97087).
Stdlib only. Exit 1 on ERROR; REVIEW exits 0 unless --strict; empty dir one WARN;
missing dir ERROR exit 1.

Usage:
    python3 check_compliant_data_sharing_setup.py --manifest-dir path/to/metadata [--strict]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CDS_FLAGS = {
    "enableCompliantDataSharingForAccount": "Account",
    "enableCompliantDataSharingForCustomObjects": None,
    "enableCompliantDataSharingForInteraction": "Interaction",
    "enableCompliantDataSharingForInteractionSummary": "InteractionSummary",
    "enableCompliantDataSharingForOpportunity": "Opportunity",
}
ACCESS_LEVELS = {"Edit", "None", "Read"}
OPEN_MODELS = {"ReadWrite", "ReadWriteTransfer", "FullAccess"}


def local(tag: str) -> str:
    return tag.split("}", 1)[-1]


def text_of(el: ET.Element, name: str) -> str | None:
    for c in el:
        if local(c.tag) == name:
            return (c.text or "").strip()
    return None


def files(root: Path, *patterns: str) -> list[Path]:
    out: list[Path] = []
    for pat in patterns:
        out += [p for p in root.rglob(pat) if p.is_file()]
    return out


def parse(path: Path, out: list) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        out.append(("ERROR", f"{path}: does not parse: {exc}"))
        return None


def scan(root: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    enabled: set[str] = set()
    deal_mgmt: bool | None = None
    for f in files(root, "Industries.settings", "Industries.settings-meta.xml"):  # api_meta 264 L122376
        r = parse(f, out)
        if r is None:
            continue
        for el in r:
            name, val = local(el.tag), (el.text or "").strip().lower()
            if name.startswith("enableCompliantDataSharingFor"):
                if name not in CDS_FLAGS:
                    out.append(("ERROR", f"{f}: <{name}> is not an IndustriesSettings field (api_meta 264 L122543-122578)"))
                elif val == "true" and CDS_FLAGS[name]:
                    enabled.add(CDS_FLAGS[name])
            if name == "enableDealManagement":
                deal_mgmt = val == "true"
    deal_roles: list[Path] = []
    for f in files(root, "*.participantRole", "*.participantRole-meta.xml"):
        r = parse(f, out)
        if r is None:
            continue
        for req in ("defaultAccessLevel", "masterLabel", "parentObject"):
            if not text_of(r, req):
                out.append(("ERROR", f"{f}: ParticipantRole missing Required <{req}> (api_meta 264 L97096-97118)"))
        lvl = text_of(r, "defaultAccessLevel")
        if lvl and lvl not in ACCESS_LEVELS:
            out.append(("ERROR", f"{f}: defaultAccessLevel '{lvl}' is not Edit, None or Read (api_meta 264 L97099-97103)"))
        if text_of(r, "parentObject") == "FinancialDeal":
            deal_roles.append(f)
    if deal_roles and deal_mgmt is False:
        out.append(("REVIEW", f"{deal_roles[0]}: FinancialDeal participant role while enableDealManagement is not true (api_meta 264 L122580-122582)"))
    for f in files(root, "*.sharingRules", "*.sharingRules-meta.xml"):
        obj = f.name.split(".")[0]
        if obj in enabled:
            out.append(("REVIEW", f"{f}: sharing rules on CDS-enabled {obj} keep granting access alongside CDS — audit each rule"))
    for f in files(root, "*.object", "*.object-meta.xml"):
        obj = f.name.split(".")[0]
        if obj not in enabled:
            continue
        r = parse(f, out)
        if r is None:
            continue
        model = text_of(r, "sharingModel")
        if model in OPEN_MODELS:
            out.append(("REVIEW", f"{f}: CDS-enabled {obj} has sharingModel {model} — Private/Read-Only prerequisite is UNVERIFIED; confirm in Help"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest-dir", default=".", help="Root of the retrieved metadata.")
    ap.add_argument("--strict", action="store_true", help="Exit 1 on REVIEW findings too.")
    args = ap.parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest dir not found: {root}")
        sys.exit(1)
    if not any(root.rglob("*")):
        print(f"WARN: {root} is empty — nothing to check")
        return 0
    findings = scan(root)
    for sev, msg in findings:
        print(f"{sev}: {msg}")
    if not findings:
        print("OK: no CDS configuration issues found")
    if any(s == "ERROR" for s, _ in findings):
        return 1
    return 1 if (args.strict and findings) else 0


if __name__ == "__main__":
    sys.exit(main())
