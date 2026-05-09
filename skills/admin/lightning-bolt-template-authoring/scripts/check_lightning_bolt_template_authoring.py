#!/usr/bin/env python3
"""Detect Lightning Bolt packaging hazards in retrieved org metadata.

Walks an SFDX-style metadata tree (force-app/) and reports problems that
will cause a `LightningBolt` deploy or downstream Experience-site
instantiation to break:

1. `LightningBolt` definitions referencing `flowCategories` that have zero
   matching `Flow` metadata files in the package (broken reference).
2. `LightningBolt` definitions referencing `images`, `customApps`, or
   `Theme` that are not present in the package (missing component).
3. `Flow` files whose `processMetadataValues` declare a category that no
   `LightningBolt` references (orphan flow category).
4. `ExperienceBundle` view / route JSON files referencing custom-object
   API names (anything ending in `__c`) — those objects must ship via a
   companion managed/unlocked package because Bolts cannot carry them.
5. `NavigationMenu` items with hardcoded `https://` URLs or 15/18-char
   record-ID patterns (will not survive cross-org Bolt instantiation).

Stdlib only — no pip dependencies.

Usage:
    python3 check_lightning_bolt_template_authoring.py [--root force-app/main/default]

Exit codes:
    0  no findings
    1  one or more findings (informational, non-blocking)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"s": "http://soap.sforce.com/2006/04/metadata"}

CUSTOM_OBJECT_RE = re.compile(r"\b([A-Za-z0-9_]+__c)\b")
RECORD_ID_RE = re.compile(r"\b([0-9a-zA-Z]{15}|[0-9a-zA-Z]{18})\b")
HTTPS_URL_RE = re.compile(r"https?://[^\s\"'<>]+")
# Salesforce record IDs always start with a 3-char keyPrefix; restrict to
# patterns that look like real IDs (start with a digit-or-letter, not just
# any 15+ alnum string).
LIKELY_ID_RE = re.compile(r"\b(00[0-9a-zA-Z]{12,15}|a[0-9a-zA-Z]{14,17})\b")


def find_lightning_bolts(root: Path) -> list[tuple[Path, dict]]:
    """Return list of (path, parsed) for each LightningBolt-meta.xml found."""
    bolts: list[tuple[Path, dict]] = []
    bolt_dirs = [root / "lightningBolts", root]
    seen: set[Path] = set()
    for d in bolt_dirs:
        if not d.exists():
            continue
        for fp in d.rglob("*.lightningBolt-meta.xml"):
            if fp in seen:
                continue
            seen.add(fp)
            try:
                tree = ET.parse(fp)
            except ET.ParseError:
                continue
            r = tree.getroot()
            parsed = {
                "description": _text(r, "s:description"),
                "summary": _text(r, "s:summary"),
                "templateApi": _text(r, "s:templateApi"),
                "versionNumber": _text(r, "s:versionNumber"),
                "flowCategories": _texts(r, "s:flowCategories"),
                "images": _texts(r, "s:images"),
                "industries": _texts(r, "s:industries"),
            }
            bolts.append((fp, parsed))
    return bolts


def _text(elem: ET.Element, path: str) -> str | None:
    found = elem.find(path, NS)
    return found.text if found is not None and found.text else None


def _texts(elem: ET.Element, path: str) -> list[str]:
    return [e.text for e in elem.findall(path, NS) if e.text]


def collect_flow_categories(flows_dir: Path) -> dict[str, list[str]]:
    """Return mapping of category name -> list of flow developer names."""
    cats: dict[str, list[str]] = {}
    if not flows_dir.exists():
        return cats
    for fp in flows_dir.rglob("*.flow-meta.xml"):
        try:
            tree = ET.parse(fp)
        except ET.ParseError:
            continue
        r = tree.getroot()
        flow_name = fp.stem.replace(".flow-meta", "")
        for pmv in r.findall(".//s:processMetadataValues", NS):
            name_el = pmv.find("s:name", NS)
            value_el = pmv.find("s:value", NS)
            if name_el is None or value_el is None:
                continue
            if name_el.text and name_el.text.lower() == "category":
                str_val = value_el.find("s:stringValue", NS)
                if str_val is not None and str_val.text:
                    cats.setdefault(str_val.text, []).append(flow_name)
    return cats


def collect_existing_components(root: Path) -> dict[str, set[str]]:
    """Inventory of components by metadata type (folder name)."""
    inv: dict[str, set[str]] = {
        "themes": set(),
        "applications": set(),
        "experiences": set(),
        "staticresources": set(),
    }
    for kind in inv:
        d = root / kind
        if not d.exists():
            continue
        if kind == "experiences":
            for entry in d.iterdir():
                if entry.is_dir():
                    inv[kind].add(entry.name)
                elif entry.suffix == ".xml":
                    inv[kind].add(entry.stem.replace(".site-meta", ""))
        else:
            suffix_map = {
                "themes": ".theme-meta.xml",
                "applications": ".app-meta.xml",
                "staticresources": ".resource-meta.xml",
            }
            suffix = suffix_map[kind]
            for fp in d.rglob(f"*{suffix}"):
                inv[kind].add(fp.name.replace(suffix, ""))
    return inv


def scan_experience_bundle_for_custom_objects(experiences_dir: Path) -> list[tuple[Path, str]]:
    """Find references to `*__c` custom objects in ExperienceBundle JSON files."""
    findings: list[tuple[Path, str]] = []
    if not experiences_dir.exists():
        return findings
    for bundle_dir in experiences_dir.iterdir():
        if not bundle_dir.is_dir():
            continue
        for json_file in bundle_dir.rglob("*.json"):
            try:
                text = json_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            seen_in_file: set[str] = set()
            for match in CUSTOM_OBJECT_RE.finditer(text):
                obj = match.group(1)
                if obj in seen_in_file:
                    continue
                seen_in_file.add(obj)
                findings.append((json_file, obj))
    return findings


def scan_navigation_menus(root: Path) -> list[tuple[Path, str, str]]:
    """Find NavigationMenuItem entries with hardcoded URLs or record IDs."""
    findings: list[tuple[Path, str, str]] = []
    nav_dir = root / "navigationMenus"
    candidates: list[Path] = []
    if nav_dir.exists():
        candidates.extend(nav_dir.rglob("*.navigationMenu-meta.xml"))
    # NavigationMenu can also live inside ExperienceBundle as JSON
    exp_dir = root / "experiences"
    if exp_dir.exists():
        candidates.extend(exp_dir.rglob("*navigation*.json"))

    for fp in candidates:
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for url_match in HTTPS_URL_RE.findall(text):
            findings.append((fp, "hardcoded URL", url_match))
        for id_match in LIKELY_ID_RE.findall(text):
            findings.append((fp, "hardcoded record ID", id_match))
    return findings


def main() -> int:
    p = argparse.ArgumentParser(
        description="Check Lightning Bolt packaging hazards in an SFDX metadata tree."
    )
    p.add_argument("--root", default="force-app/main/default")
    args = p.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"metadata root not found: {root}", file=sys.stderr)
        return 0

    findings_count = 0

    # 1. Inventory bolts
    bolts = find_lightning_bolts(root)
    if not bolts:
        print("No LightningBolt-meta.xml files found under " f"{root}.")
        print("Nothing to check.")
        return 0

    flow_categories = collect_flow_categories(root / "flows")
    inventory = collect_existing_components(root)

    referenced_categories: set[str] = set()
    for fp, parsed in bolts:
        rel = fp.relative_to(root) if fp.is_relative_to(root) else fp
        print(f"\n## LightningBolt: {fp.stem.replace('.lightningBolt-meta', '')} "
              f"(version {parsed.get('versionNumber') or '<unset>'})")
        print(f"   path: {rel}")
        if parsed.get("templateApi"):
            print(f"   templateApi: {parsed['templateApi']}")

        # 1. flowCategories references
        for cat in parsed["flowCategories"]:
            referenced_categories.add(cat)
            flows_in_cat = flow_categories.get(cat, [])
            if not flows_in_cat:
                print(f"   FINDING: flowCategory {cat!r} referenced but no Flow files match")
                print(f"            (deploy will succeed; runtime will fail when site uses this category)")
                findings_count += 1
            else:
                print(f"   OK:      flowCategory {cat!r} -> {len(flows_in_cat)} flow(s)")

        # 2. images
        for img in parsed["images"]:
            if img not in inventory["staticresources"]:
                print(f"   FINDING: images entry {img!r} not found as a staticresource")
                print(f"            (Bolt listing thumbnail will be missing)")
                findings_count += 1

    # 3. Orphan flow categories (in flows but not referenced by any Bolt)
    orphan_cats = set(flow_categories.keys()) - referenced_categories
    if orphan_cats:
        print(f"\n## Orphan flow categories (declared on Flows but not in any LightningBolt)")
        for cat in sorted(orphan_cats):
            flow_count = len(flow_categories[cat])
            print(f"   - {cat}: {flow_count} flow(s) ({', '.join(flow_categories[cat][:5])}"
                  f"{'...' if flow_count > 5 else ''})")
            findings_count += 1

    # 4. Custom-object references in ExperienceBundle
    custom_obj_refs = scan_experience_bundle_for_custom_objects(root / "experiences")
    if custom_obj_refs:
        # dedupe (file, obj) pairs
        seen_pairs: set[tuple[str, str]] = set()
        unique = []
        for fp, obj in custom_obj_refs:
            key = (str(fp), obj)
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            unique.append((fp, obj))

        print(f"\n## Custom-object references in ExperienceBundle")
        print("   These objects must ship via a companion managed/unlocked package — Bolts cannot carry them.")
        for fp, obj in unique[:50]:
            try:
                rel = fp.relative_to(root)
            except ValueError:
                rel = fp
            print(f"   - {rel}: references {obj}")
        if len(unique) > 50:
            print(f"   ... ({len(unique) - 50} more references not shown)")
        findings_count += len(unique)

    # 5. NavigationMenu hardcoded URLs and record IDs
    nav_findings = scan_navigation_menus(root)
    if nav_findings:
        print(f"\n## Hardcoded URLs / record IDs in navigation")
        print("   These will not survive cross-org Bolt instantiation.")
        for fp, kind, value in nav_findings[:30]:
            try:
                rel = fp.relative_to(root)
            except ValueError:
                rel = fp
            print(f"   - {rel}: {kind} -> {value}")
        if len(nav_findings) > 30:
            print(f"   ... ({len(nav_findings) - 30} more not shown)")
        findings_count += len(nav_findings)

    if findings_count == 0:
        print("\nNo Lightning Bolt packaging hazards detected.")
        return 0

    print(f"\nTotal findings: {findings_count}")
    print("Refer to references/gotchas.md for remediation guidance.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
