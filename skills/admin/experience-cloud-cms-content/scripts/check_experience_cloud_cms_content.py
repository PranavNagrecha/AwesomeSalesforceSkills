#!/usr/bin/env python3
"""Checker script for Experience Cloud CMS Content skill.

Scans a Salesforce metadata directory (--manifest-dir) for:

- ManagedContentType files (api_meta 264 L89063-89292)
    ERROR  unparseable XML; missing Required developerName / masterLabel;
           a node missing Required nodeName / nodeLabel / nodeType; an invalid nodeType;
           not exactly one NAMEFIELD node (L89221-89222); NAMEFIELD without isRequired
           true (L89231-89232); more than 15 nodes (L89160); a nodeName that breaks the
           naming rules (L89142-89145)
    WARN   no managedContentNodeTypes; isLocalizable true on IMG / URL / DATE / DATETIME; child elements the guide
           does not define (for example fieldType, label, name)
- ContentTypeBundle schema.json files (api_meta 264 L38404-38419)
    ERROR  invalid JSON
- Audience files (api_meta 264 L26225-26283)
    ERROR  unparseable XML; missing Required audienceName / container / criteria; an
           invalid criterion type or formulaFilterType
    INFO   ExperienceVariation targets with no ExperienceBundle folder in the tree (L26426)
- ExperienceBundle views (api_meta 264 L62393-62395)
    INFO   very long inline text values (a heuristic for hardcoded content; UNVERIFIED
           2026-10-20, the guide does not define "hardcoded content")

The earlier rule that flagged `PublicChannel` in a site-meta file was removed: that channel
type name is not in the corpus (the channel `Type` values are COMMUNITY, CloudToCloud,
ConnectedApp, PublicUnauthenticated, Record, UserPermission; object_reference 264
L180507-180523) and a ManagedContentChannel is a record, not a metadata file.

Exit codes: ERROR findings exit 1 always; WARN and INFO findings exit 0 unless --strict; a
directory with nothing to check prints one WARN and exits 0; a missing path is an ERROR
and exits 1. Stdlib only.

Usage:
    python3 check_experience_cloud_cms_content.py --manifest-dir path/to/metadata [--strict]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NODE_TYPES = {"TEXT", "MTEXT", "RTE", "IMG", "URL", "DATE", "DATETIME", "NAMEFIELD"}  # L89162-89203
NON_LOCALIZABLE = {"IMG", "URL", "DATE", "DATETIME"}  # L89125-89126, L89174-89200
NODE_CHILDREN = {"helpText", "isLocalizable", "isRequired", "nodeLabel", "nodeName", "nodeType", "placeholderText"}
TYPE_CHILDREN = {"description", "developerName", "isMetadataContent", "managedContentNodeTypes", "masterLabel", "fullName"}
NODE_NAME = re.compile(r"^[A-Za-z](?:_?[A-Za-z0-9])*$")  # L89142-89145, <= 100 chars
CRITERION_TYPES = {"GeoLocation", "Domain", "Profile", "FieldBased", "Permission", "Default", "Audience"}  # L26322-26330
FORMULA_TYPES = {"AllCriteriaMatch", "AnyCriterionMatches", "CustomLogicMatches"}  # L26270-26274
INLINE_TEXT_THRESHOLD = 500


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Experience Cloud CMS content metadata for common issues.",
    )
    parser.add_argument("--manifest-dir", default=".", help="Root directory of the Salesforce metadata (default: current directory).")
    parser.add_argument("--strict", action="store_true", help="exit 1 on WARN and INFO findings too")
    return parser.parse_args()


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def kids(el: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in el if local(c.tag) == name]


def text_of(el: ET.Element, name: str) -> str | None:
    found = kids(el, name)
    if not found:
        return None
    return (found[0].text or "").strip()


def check_managed_content_types(root: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for path in root.glob("**/*.managedContentType-meta.xml"):
        try:
            el = ET.parse(path).getroot()
        except (ET.ParseError, OSError) as exc:
            out.append(("ERROR", f"{path.name}: XML does not parse ({exc})"))
            continue
        for field in ("developerName", "masterLabel"):
            if not text_of(el, field):
                out.append(("ERROR", f"{path.name}: <{field}> is Required (api_meta 264 L89090, L89110)"))
        for child in el:
            if local(child.tag) not in TYPE_CHILDREN:
                out.append(("WARN", f"{path.name}: <{local(child.tag)}> is not a ManagedContentType field"))
        nodes = kids(el, "managedContentNodeTypes")
        if not nodes:
            out.append(("WARN", f"{path.name}: no <managedContentNodeTypes>; the content type will have no fields"))
            continue
        if len(nodes) > 15:
            out.append(("ERROR", f"{path.name}: {len(nodes)} nodes; the guide allows a maximum of 15 per content type (L89160)"))
        namefields = 0
        for node in nodes:
            ntype = (text_of(node, "nodeType") or "").upper()
            for field in ("nodeName", "nodeLabel", "nodeType"):
                if not text_of(node, field):
                    out.append(("ERROR", f"{path.name}: node is missing Required <{field}> (api_meta 264 L89136-89161)"))
            if ntype and ntype not in NODE_TYPES:
                out.append(("ERROR", f"{path.name}: nodeType '{ntype}' is not one of {sorted(NODE_TYPES)}"))
            for child in node:
                if local(child.tag) not in NODE_CHILDREN:
                    out.append(("WARN", f"{path.name}: <{local(child.tag)}> is not a ManagedContentNodeType field; use nodeName, nodeLabel, nodeType"))
            name = text_of(node, "nodeName") or ""
            if name and (len(name) > 100 or not NODE_NAME.match(name)):
                out.append(("ERROR", f"{path.name}: nodeName '{name}' breaks the naming rules (letters, digits, underscores; starts with a letter; no two consecutive underscores; no trailing underscore; 100 characters; L89142-89145)"))
            if ntype == "NAMEFIELD":
                namefields += 1
                if (text_of(node, "isRequired") or "").lower() != "true":
                    out.append(("ERROR", f"{path.name}: the NAMEFIELD node must also set isRequired true (L89133-89134, L89231-89232)"))
            if ntype in NON_LOCALIZABLE and (text_of(node, "isLocalizable") or "").lower() == "true":
                out.append(("WARN", f"{path.name}: {ntype} nodes can't be localized; set isLocalizable false"))
        if namefields != 1:
            out.append(("ERROR", f"{path.name}: {namefields} NAMEFIELD nodes; one, and only one, is required (L89221-89222)"))
    return out


def check_content_type_bundles(root: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for path in root.glob("**/contentTypes/*/schema.json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            out.append(("ERROR", f"{path.parent.name}/schema.json: invalid JSON ({exc})"))
    return out


def check_audiences(root: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    has_bundle = any(root.glob("**/experiences/*"))
    for path in list(root.glob("**/*.audience-meta.xml")) + list(root.glob("**/*.audience")):
        try:
            el = ET.parse(path).getroot()
        except (ET.ParseError, OSError) as exc:
            out.append(("ERROR", f"{path.name}: XML does not parse ({exc})"))
            continue
        for field in ("audienceName", "container"):
            if not text_of(el, field):
                out.append(("ERROR", f"{path.name}: <{field}> is Required (api_meta 264 L26254-26256)"))
        if not kids(el, "criteria"):
            out.append(("ERROR", f"{path.name}: <criteria> is Required (api_meta 264 L26258)"))
        for criterion in el.iter():
            if local(criterion.tag) == "criterion":
                ctype = text_of(criterion, "type")
                if ctype and ctype not in CRITERION_TYPES:
                    out.append(("ERROR", f"{path.name}: criterion type '{ctype}' is not one of {sorted(CRITERION_TYPES)}"))
        ftype = text_of(el, "formulaFilterType")
        if ftype and ftype not in FORMULA_TYPES:
            out.append(("ERROR", f"{path.name}: formulaFilterType '{ftype}' is not one of {sorted(FORMULA_TYPES)}"))
        if "ExperienceVariation" in path.read_text(encoding="utf-8", errors="ignore") and not has_bundle:
            out.append(("INFO", f"{path.name}: ExperienceVariation targets need ExperienceBundle in the same deployment (L26426); none found under this directory"))
    return out


def find_large(obj: object, threshold: int) -> int:
    if isinstance(obj, str):
        return 1 if len(obj) > threshold else 0
    if isinstance(obj, dict):
        return sum(find_large(v, threshold) for v in obj.values())
    if isinstance(obj, list):
        return sum(find_large(v, threshold) for v in obj)
    return 0


def check_views(root: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for path in root.glob("**/experiences/**/views/*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        n = find_large(data, INLINE_TEXT_THRESHOLD)
        if n:
            out.append(("INFO", f"{path.name}: {n} inline text value(s) over {INLINE_TEXT_THRESHOLD} characters; consider a managed content item (heuristic, UNVERIFIED 2026-10-20)"))
    return out


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    scanned = [p for p in root.rglob("*") if p.is_file() and (
        p.name.endswith(".managedContentType-meta.xml") or p.name.endswith(".audience-meta.xml")
        or p.name.endswith(".audience") or p.name == "schema.json" or "views" in p.parts)]
    if not scanned:
        print(f"WARN: no ManagedContentType, ContentTypeBundle, Audience or ExperienceBundle view files under {root}; nothing to check")
        return 1 if args.strict else 0
    findings = (check_managed_content_types(root) + check_content_type_bundles(root)
                + check_audiences(root) + check_views(root))
    if not findings:
        print("No issues found.")
        return 0
    for sev, msg in findings:
        print(f"{sev}: {msg}")
    if any(sev == "ERROR" for sev, _ in findings):
        return 1
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
