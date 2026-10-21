#!/usr/bin/env python3
"""Checker script for Lightning Experience Transition skill.

Scans a metadata source tree for assets that block or complicate a
Classic-to-Lightning rollout. Element names follow the Metadata API guide
(api_meta 264). Stdlib only.

Checks:
  1. JavaScript buttons: WebLink with <linkType>javascript</linkType>
     (L47926-47931), in objects/*/webLinks/*.webLink-meta.xml or inline
     <webLinks> blocks of an .object file -> WARN.
  2. S-controls (.scf files; the type is "Deprecated", L109760-109769) -> WARN.
  3. Visualforce pages / components using window.parent, location.hash,
     sforce.connection, or renderAs="pdf" -> REVIEW (heuristic).
  4. CustomApplication with <uiType>Aloha</uiType> (Classic; uiType is
     "Not updateable", L41933-41937) -> REVIEW.
  5. installedPackages present -> INFO (walk each package in LEX).
  6. A webLink, application or object file that does not parse -> ERROR.

Exit codes: 1 on any ERROR or a missing --manifest-dir; WARN/REVIEW/INFO exit
0 unless --strict; a tree with none of the scanned file types prints one
WARN and exits 0.

Usage:
    python3 check_lightning_experience_transition.py --manifest-dir force-app/main/default [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"
VF_RISKY = [
    (re.compile(r"<apex:page\b[^>]*\brenderAs\s*=\s*\"pdf\"", re.IGNORECASE),
     "renderAs=pdf - verify output inside Lightning Experience"),
    (re.compile(r"\bwindow\.parent\b"), "uses window.parent - test cross-frame access in LEX"),
    (re.compile(r"\bsforce\.connection\b"), "uses sforce.connection - Classic-era client API"),
    (re.compile(r"\blocation\.hash\b"), "manipulates location.hash - test inside LEX"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Triage metadata for Lightning Experience transition blockers.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of Salesforce metadata.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN/REVIEW/INFO findings too.")
    return parser.parse_args()


def by_suffix(root: Path, *suffixes: str) -> list[Path]:
    lowered = tuple(s.lower() for s in suffixes)
    return sorted(p for p in root.rglob("*") if p.is_file() and p.name.lower().endswith(lowered))


def text_of(el: ET.Element, tag: str) -> str:
    found = el.find(NS + tag)
    if found is None:
        found = el.find(tag)
    return (found.text or "").strip() if found is not None else ""


def parse(path: Path, root: Path, errors: list[str]) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        errors.append(f"{path.relative_to(root)}: XML does not parse ({exc})")
        return None


def is_js_button(link: ET.Element) -> bool:
    return text_of(link, "linkType") == "javascript"


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)

    weblinks = by_suffix(root, ".weblink-meta.xml")
    objects = by_suffix(root, ".object-meta.xml", ".object")
    scontrols = by_suffix(root, ".scf")
    vf = by_suffix(root, ".page", ".component")
    # Aura application bundles (aura/<name>/<name>.app) are not CustomApplication XML
    apps = [p for p in by_suffix(root, ".app-meta.xml", ".app") if "aura" not in p.parts]
    packages = by_suffix(root, ".installedpackage-meta.xml", ".installedpackage")
    if not (weblinks or objects or scontrols or vf or apps or packages):
        print(f"WARN: no webLink, object, scontrol, Visualforce, app or installedPackage files under {root}; nothing to check")
        return 0

    errors: list[str] = []
    findings: list[str] = []
    for path in weblinks:
        link = parse(path, root, errors)
        if link is not None and is_js_button(link):
            findings.append(f"WARN: {path.relative_to(root)}: JavaScript button (linkType javascript) - "
                            "replace with a Quick Action, flow or LWC before the wave that uses it")
    for path in objects:
        obj = parse(path, root, errors)
        if obj is None:
            continue
        # the guide's own sample spells the block <WebLinks> (api_meta 264 L48040)
        links = [el for tag in ("webLinks", "WebLinks") for el in obj.findall(NS + tag) + obj.findall(tag)]
        for link in links:
            if is_js_button(link):
                findings.append(f"WARN: {path.relative_to(root)}: JavaScript button "
                                f"{text_of(link, 'fullName') or '?'} (linkType javascript)")
    for path in scontrols:
        findings.append(f"WARN: {path.relative_to(root)}: S-control (deprecated type) - retire or rebuild")
    for path in vf:
        body = path.read_text(encoding="utf-8", errors="ignore")
        for pattern, note in VF_RISKY:
            if pattern.search(body):
                findings.append(f"REVIEW: {path.relative_to(root)}: {note}")
    for path in apps:
        app = parse(path, root, errors)
        if app is not None and text_of(app, "uiType") == "Aloha":
            findings.append(f"REVIEW: {path.relative_to(root)}: Classic (Aloha) app; uiType is not updateable, "
                            "so plan a separate Lightning app")
    if packages:
        findings.append(f"INFO: {len(packages)} installed package(s) - walk each cohort's workflows in LEX before its wave")

    for msg in errors:
        print(f"ERROR: {msg}")
    for msg in findings:
        print(msg)
    if not errors and not findings:
        print("OK: no Lightning Experience transition blockers detected.")
    if errors or (findings and args.strict):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
