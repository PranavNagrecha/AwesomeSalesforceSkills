#!/usr/bin/env python3
"""Detect Lightning Bolt packaging hazards in a retrieved metadata tree.

Field names follow the Metadata API guide (api_meta 264):
- LightningBolt (L86523-86685): category, masterLabel, publisher, summary are
  Required; lightningBoltItems.type must be CommunityTemplateDefinition,
  CustomApplication or FlowCategory; lightningBoltImages.image/order and
  lightningBoltFeatures.title/order are Required (L86595, L86606, L86618).
    ERROR  a Required field is missing, an item type is not one of the three,
           or a file does not parse
    WARN   category not in the LightningBoltCategory list (the guide's own
           sample uses "Sales", which is not in the list, L86642)
    WARN   feature order above 4 or image order above 3
    WARN   an element LightningBolt does not define (templateApi,
           versionNumber, industries, flowCategories, images, description)
    WARN   an item whose component file is not in the tree
- FlowCategory (L76580-76610): masterLabel Required (ERROR); a listed flow
  with no flow file in the tree (WARN).
- ExperienceBundle JSON naming custom objects (__c), and navigation with
  hardcoded https:// URLs or record-ID-shaped values (WARN, heuristics).

Exit codes: 1 on any ERROR or a missing --manifest-dir; WARN findings exit 0
unless --strict; a tree with no LightningBolt, FlowCategory or ExperienceBundle
files prints one WARN and exits 0. Stdlib only.

Usage:
    python3 check_lightning_bolt_template_authoring.py --manifest-dir force-app/main/default [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"
CATEGORIES = {
    "Communications", "Education", "FinancialServices", "GeneralBusiness", "Government",
    "HealthcareLifeSciences", "HighTech", "Manufacturing", "Media", "Nonprofits",
    "ProfessionalServices", "RealEstate", "Retail", "TravelTransportationHospitality",
}
ITEM_TYPES = {
    "CommunityTemplateDefinition": ("communityTemplateDefinitions", ".communityTemplateDefinition"),
    "CustomApplication": ("applications", ".app"),
    "FlowCategory": ("flowCategories", ".flowCategory"),
}
KNOWN = {"category", "lightningBoltFeatures", "lightningBoltImages", "lightningBoltItems",
         "masterLabel", "publisher", "summary", "fullName"}
CUSTOM_OBJECT_RE = re.compile(r"\b([A-Za-z][A-Za-z0-9_]*__c)\b")
URL_RE = re.compile(r"https?://[^\s\"'<>]+")
ID_RE = re.compile(r"\b(00[0-9a-zA-Z]{13}|00[0-9a-zA-Z]{16})\b")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Check Lightning Bolt packaging hazards in a metadata tree.")
    p.add_argument("--manifest-dir", "--root", dest="manifest_dir", default="force-app/main/default",
                   help="Root of the retrieved metadata tree.")
    p.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings too.")
    return p.parse_args()


def local(tag: str) -> str:
    return tag.split("}", 1)[-1]


def kids(el: ET.Element, tag: str) -> list[ET.Element]:
    return el.findall(NS + tag) + el.findall(tag)


def text(el: ET.Element, tag: str) -> str:
    found = kids(el, tag)
    return (found[0].text or "").strip() if found else ""


def files(root: Path, suffix: str) -> list[Path]:
    return sorted(set(root.rglob(f"*{suffix}-meta.xml")) | set(root.rglob(f"*{suffix}")))


def has_component(root: Path, folder: str, suffix: str, name: str) -> bool:
    return any((d / f"{name}{suffix}{tail}").exists()
               for d in [root / folder] for tail in ("-meta.xml", ""))


def parse(path: Path, root: Path, errors: list[str]) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        errors.append(f"{path.relative_to(root)}: XML does not parse ({exc})")
        return None


def check_bolt(path: Path, root: Path, errors: list[str], warns: list[str]) -> None:
    bolt = parse(path, root, errors)
    if bolt is None:
        return
    rel = path.relative_to(root)
    for field in ("category", "masterLabel", "publisher", "summary"):
        if not text(bolt, field):
            errors.append(f"{rel}: missing Required <{field}>")
    category = text(bolt, "category")
    if category and category not in CATEGORIES:
        warns.append(f"{rel}: category '{category}' is not in the LightningBoltCategory list")
    for child in bolt:
        if local(child.tag) not in KNOWN:
            warns.append(f"{rel}: <{local(child.tag)}> is not a LightningBolt field")
    for feature in kids(bolt, "lightningBoltFeatures"):
        if not text(feature, "title"):
            errors.append(f"{rel}: lightningBoltFeatures entry missing Required <title>")
        if not text(feature, "order"):
            errors.append(f"{rel}: lightningBoltFeatures entry missing Required <order> (L86595)")
        if text(feature, "order").isdigit() and int(text(feature, "order")) > 4:
            warns.append(f"{rel}: feature order {text(feature, 'order')} exceeds the max position 4")
    for image in kids(bolt, "lightningBoltImages"):
        if not text(image, "image"):
            errors.append(f"{rel}: lightningBoltImages entry missing Required <image>")
        if not text(image, "order"):
            errors.append(f"{rel}: lightningBoltImages entry missing Required <order> (L86618)")
        if text(image, "order").isdigit() and int(text(image, "order")) > 3:
            warns.append(f"{rel}: image order {text(image, 'order')} exceeds the max position 3")
    for item in kids(bolt, "lightningBoltItems"):
        name, item_type = text(item, "name"), text(item, "type")
        if not name:
            errors.append(f"{rel}: lightningBoltItems entry missing Required <name>")
        if item_type not in ITEM_TYPES:
            errors.append(f"{rel}: item '{name}' has type '{item_type}'; valid types are "
                          "CommunityTemplateDefinition, CustomApplication, FlowCategory")
            continue
        folder, suffix = ITEM_TYPES[item_type]
        if name and not has_component(root, folder, suffix, name):
            warns.append(f"{rel}: {item_type} '{name}' is not in {folder}/ - deploy it with the Bolt")


def check_flow_category(path: Path, root: Path, errors: list[str], warns: list[str]) -> None:
    category = parse(path, root, errors)
    if category is None:
        return
    rel = path.relative_to(root)
    if not text(category, "masterLabel"):
        errors.append(f"{rel}: FlowCategory missing Required <masterLabel>")
    for item in kids(category, "flowCategoryItems"):
        flow = text(item, "flow")
        if flow and not has_component(root, "flows", ".flow", flow):
            warns.append(f"{rel}: lists flow '{flow}' but flows/{flow}.flow-meta.xml is not in the tree")


def check_experiences(root: Path, warns: list[str]) -> None:
    for path in sorted((root / "experiences").rglob("*.json")) if (root / "experiences").is_dir() else []:
        body = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(root)
        for obj in sorted(set(CUSTOM_OBJECT_RE.findall(body))):
            warns.append(f"{rel}: references custom object {obj}; ship it in a companion package")
        if "navigation" in path.name.lower():
            for url in sorted(set(URL_RE.findall(body))):
                warns.append(f"{rel}: hardcoded URL {url}")
            for rid in sorted(set(ID_RE.findall(body))):
                warns.append(f"{rel}: record-ID-shaped value {rid}")
    for path in files(root, ".navigationMenu"):
        body = path.read_text(encoding="utf-8", errors="replace")
        for url in sorted(set(URL_RE.findall(body))):
            warns.append(f"{path.relative_to(root)}: hardcoded URL {url}")


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    bolts = files(root, ".lightningBolt")
    categories = files(root, ".flowCategory")
    has_experiences = (root / "experiences").is_dir()
    if not bolts and not categories and not has_experiences:
        print(f"WARN: no LightningBolt, FlowCategory or experiences/ under {root}; nothing to check")
        return 0
    errors: list[str] = []
    warns: list[str] = []
    for path in bolts:
        check_bolt(path, root, errors, warns)
    for path in categories:
        check_flow_category(path, root, errors, warns)
    check_experiences(root, warns)
    for msg in errors:
        print(f"ERROR: {msg}")
    for msg in warns:
        print(f"WARN: {msg}")
    if not errors and not warns:
        print("OK: no Lightning Bolt packaging hazards detected.")
    if errors or (warns and args.strict):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
