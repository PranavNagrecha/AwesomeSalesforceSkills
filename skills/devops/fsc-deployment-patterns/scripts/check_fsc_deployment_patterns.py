#!/usr/bin/env python3
"""Checker for the FSC Deployment Patterns skill.

Scans a Salesforce metadata directory (source format or Metadata API format)
for FSC deployment defects. Grounded in the Summer '26 Metadata API Developer
Guide: ParticipantRole (api_meta.txt L94367-94455) and IndustriesSettings
(L119187, L119332-119364).

ERROR (exit 1):
  - a ParticipantRole file that does not parse, has the wrong root element,
    or is missing a required field (defaultAccessLevel, masterLabel, parentObject)
  - defaultAccessLevel not one of Edit / None / Read
  - parentObject not a documented value and not a custom object (__c)
  - ParticipantRole modelled as custom metadata (customMetadata/ParticipantRole.*
    or a ParticipantRole__mdt object) -- it is its own Metadata API type
  - package.xml lists ParticipantRole records under CustomMetadata
WARN (exit 0, or 1 with --strict):
  - empty directory, or no FSC components found (nothing was checked)
  - ParticipantRole with isActive missing or false
  - ParticipantRole whose parentObject has no enableCompliantDataSharingFor*
    flag set to true in the Industries.settings file in the same tree
  - FinServ__ namespace present (only portable to managed-package FSC orgs)
  - RecordType, IndustriesSettings and ParticipantRole in one package.xml
  - package.xml naming IndustriesSettings as a type -- the manifest lists it as
    member Industries of type Settings (api_meta.txt L119183, L120234-120236)
NOTE (never affects exit code):
  - household Account record types present -> verify person accounts first
  - ParticipantRole files but no Industries.settings in the tree -> CDS flag
    cross-check skipped

Stdlib only.

Usage:
    python3 check_fsc_deployment_patterns.py --manifest-dir force-app/main/default
    python3 check_fsc_deployment_patterns.py --manifest-dir mdapi_out --strict
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

FINSERV_RE = re.compile(r"FinServ__\w+")

ACCESS_LEVELS = {"Edit", "None", "Read"}
# api_meta.txt L94414-94452
PARENT_OBJECTS = {
    "Account", "Budget", "IndividualApplication", "Interaction", "InteractionSummary",
    "FinancialDeal", "FundingAward", "FundingOpportunity", "Opportunity", "Team",
}
# parentObject -> IndustriesSettings flag (api_meta.txt L119332-119364)
CDS_FLAGS = {
    "Account": "enableCompliantDataSharingForAccount",
    "Opportunity": "enableCompliantDataSharingForOpportunity",
    "Interaction": "enableCompliantDataSharingForInteraction",
    "InteractionSummary": "enableCompliantDataSharingForInteractionSummary",
}
CUSTOM_OBJECT_FLAG = "enableCompliantDataSharingForCustomObjects"
SEQUENCED_TYPES = ["RecordType", "IndustriesSettings", "ParticipantRole"]


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1]


def _child_text(elem: ET.Element, name: str) -> str | None:
    """Text of the first direct child with this local name, or None. Uses an
    explicit `is not None` test -- an Element with no children is falsy."""
    for child in elem:
        if _local(child.tag) == name:
            return (child.text or "").strip()
    return None


def _files(root: Path, *suffixes: str) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file() and p.name.endswith(suffixes))


def load_cds_flags(root: Path, warns: list[str]) -> dict[str, bool] | None:
    """Return {flag: bool} from Industries.settings, or None when no file exists."""
    files = _files(root, "Industries.settings", "Industries.settings-meta.xml")
    if not files:
        return None
    flags: dict[str, bool] = {}
    for f in files:
        try:
            tree = ET.parse(f)
        except ET.ParseError as exc:
            warns.append(f"{f}: Industries settings file does not parse ({exc}); CDS flag cross-check skipped")
            continue
        for child in tree.getroot():
            name = _local(child.tag)
            if name.startswith("enableCompliantDataSharingFor"):
                flags[name] = (child.text or "").strip().lower() == "true"
    return flags


def check_participant_roles(root: Path, errors: list[str], warns: list[str]) -> int:
    files = _files(root, ".participantRole", ".participantRole-meta.xml")
    flags = load_cds_flags(root, warns)
    if files and flags is None:
        print(f"NOTE: {len(files)} ParticipantRole file(s) but no Industries.settings in {root} -- "
              "the enableCompliantDataSharingFor* cross-check was skipped; confirm the flags in the target org")
    for f in files:
        try:
            elem = ET.parse(f).getroot()
        except ET.ParseError as exc:
            errors.append(f"{f}: ParticipantRole does not parse: {exc}")
            continue
        if _local(elem.tag) != "ParticipantRole":
            errors.append(f"{f}: root element is <{_local(elem.tag)}>, expected <ParticipantRole>")
            continue
        missing = [n for n in ("defaultAccessLevel", "masterLabel", "parentObject") if not _child_text(elem, n)]
        if missing:
            errors.append(f"{f}: ParticipantRole missing required field(s): {', '.join(missing)}")
        level = _child_text(elem, "defaultAccessLevel")
        if level and level not in ACCESS_LEVELS:
            errors.append(f"{f}: defaultAccessLevel '{level}' is not one of Edit, None, Read")
        parent = _child_text(elem, "parentObject")
        if parent and parent not in PARENT_OBJECTS and not parent.endswith("__c"):
            errors.append(f"{f}: parentObject '{parent}' is not a documented ParticipantRole parent (or a custom object)")
        active = _child_text(elem, "isActive")
        if (active or "").lower() != "true":
            warns.append(f"{f}: isActive is {'missing' if active is None else active}; the role grants no access until activated")
        if parent and flags is not None:
            flag = CUSTOM_OBJECT_FLAG if parent.endswith("__c") else CDS_FLAGS.get(parent)
            if flag and not flags.get(flag, False):
                warns.append(f"{f}: parentObject {parent} but {flag} is not true in Industries.settings; the role has no CDS effect on that object")
    return len(files)


def check_cmdt_misuse(root: Path, errors: list[str], warns: list[str]) -> int:
    hits = 0
    for f in _files(root, ".md", ".md-meta.xml", ".object", ".object-meta.xml"):
        base = f.name
        if "ParticipantRole" not in base and "ParticipantRole" not in str(f.parent):
            continue
        if not (f.parent.name == "customMetadata" or "__mdt" in str(f)):
            continue
        hits += 1
        if "FinServ__" in str(f):
            warns.append(f"{f}: FinServ__ ParticipantRole custom metadata -- the Summer '26 Metadata API guide documents only the ParticipantRole type; confirm this record exists in the managed package")
        else:
            errors.append(f"{f}: ParticipantRole modelled as custom metadata; it is a Metadata API type stored as participantRoles/<Name>.participantRole")
    return hits


def check_namespace(root: Path, warns: list[str]) -> None:
    contaminated: dict[str, set[str]] = {}
    for f in _files(root, ".xml", ".participantRole", ".settings", ".object", ".layout", ".cls", ".trigger"):
        try:
            names = set(FINSERV_RE.findall(f.read_text(encoding="utf-8", errors="ignore")))
        except OSError:
            continue
        if names:
            contaminated[str(f.relative_to(root))] = names
    if contaminated:
        sample = "; ".join(f"{p}: {sorted(n)[:3]}" for p, n in list(contaminated.items())[:5])
        warns.append(f"FinServ__ namespace in {len(contaminated)} file(s) -- portable only to managed-package FSC orgs; rewrite API names before deploying to platform-native FSC. {sample}")


def check_package_xml(root: Path, errors: list[str], warns: list[str]) -> int:
    files = [p for p in root.rglob("package.xml") if p.is_file()]
    for f in files:
        try:
            pkg = ET.parse(f).getroot()
        except ET.ParseError as exc:
            errors.append(f"{f}: package.xml does not parse: {exc}")
            continue
        present: set[str] = set()
        for types in pkg:
            if _local(types.tag) != "types":
                continue
            name = _child_text(types, "name")
            if not name:
                continue
            present.add(name)
            if name == "IndustriesSettings":
                warns.append(f"{f}: <name>IndustriesSettings</name> -- a manifest lists it as "
                             f"<members>Industries</members> under <name>Settings</name>")
            members = [(m.text or "").strip() for m in types if _local(m.tag) == "members"]
            if name == "Settings" and ("Industries" in members or "*" in members):
                present.add("IndustriesSettings")  # package.xml lists it as Settings/Industries
            if name == "CustomMetadata":
                for m in types:
                    if _local(m.tag) == "members" and (m.text or "").strip().startswith("ParticipantRole."):
                        errors.append(f"{f}: CustomMetadata member {(m.text or '').strip()} -- list ParticipantRole under <name>ParticipantRole</name>")
        seq = [t for t in SEQUENCED_TYPES if t in present]
        if len(seq) > 1:
            warns.append(f"{f}: {seq} in one manifest -- deploy RecordType, then IndustriesSettings, then ParticipantRole as separate waves")
    return len(files)


def note_household(root: Path) -> int:
    rts = [p for p in root.rglob("*") if p.is_file() and "Household" in p.name and "recordType" in p.name]
    if rts:
        print(f"NOTE: {len(rts)} household record type file(s) -- confirm person accounts are enabled in the target "
              "(SELECT Id FROM RecordType WHERE SobjectType='Account' AND IsPersonType=true) before deploying them")
    return len(rts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest-dir", required=True, help="Metadata root (source or MDAPI format).")
    ap.add_argument("--strict", action="store_true", help="Treat WARN findings as errors (exit 1).")
    args = ap.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    if not any(p.is_file() for p in root.rglob("*")):
        print(f"WARN: {root} is empty -- nothing to check")
        return 1 if args.strict else 0

    errors: list[str] = []
    warns: list[str] = []
    found = check_participant_roles(root, errors, warns)
    found += check_cmdt_misuse(root, errors, warns)
    found += check_package_xml(root, errors, warns)
    found += len(_files(root, "Industries.settings", "Industries.settings-meta.xml"))
    found += note_household(root)
    check_namespace(root, warns)
    if not found and not warns:
        warns.append(f"{root}: no ParticipantRole, Industries settings, package.xml or household record type found -- nothing FSC-specific was checked")

    for e in errors:
        print(f"ERROR: {e}")
    for w in warns:
        print(f"WARN: {w}")
    if errors:
        sys.exit(1)
    if warns:
        return 1 if args.strict else 0
    print("OK: no FSC deployment issues found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
