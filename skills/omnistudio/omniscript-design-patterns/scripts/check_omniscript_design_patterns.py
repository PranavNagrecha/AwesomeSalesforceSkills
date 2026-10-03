#!/usr/bin/env python3
"""Checker for the omniscript-design-patterns skill.

Parses OmniScript metadata (`omniScripts/*.os-meta.xml` in Salesforce DX source
format, or `*.omniScript` in Metadata API format) and reports design findings
grounded in the OmniScript reference (Industries Common Resources Developer Guide,
Summer '26) and the Trailhead "Omnistudio Omniscripts" module:

  ERROR   file does not parse
  HIGH    two ACTIVE OmniScripts share Type + SubType + Language
          ("Only one active Omniscript may have the same Type, SubType, and Language")
  HIGH    duplicate element names inside one OmniScript ("Element names must be unique")
  MEDIUM  uniqueName is not Type_SubType_Language_VersionNumber
  REVIEW  more than 15 Step elements (journey may need simplifying)
  REVIEW  a Step with more than 6 action elements (round trips; prefer one IP action)

Exit codes: 1 if the directory is missing, a file doesn't parse, or any HIGH finding
exists (MEDIUM and REVIEW too with --strict); 0 otherwise. Stdlib only.

Usage:
    python3 check_omniscript_design_patterns.py --source-dir force-app [--strict]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

SUFFIXES = (".os-meta.xml", ".omniScript", ".omniScript-meta.xml")
MAX_STEPS = 15
MAX_ACTIONS_PER_STEP = 6


def _local(tag: str) -> str:
    return tag.split("}")[-1]


def _text(parent: ET.Element, name: str) -> str:
    for el in parent:
        if _local(el.tag) == name:
            return (el.text or "").strip()
    return ""


def _elements(root: ET.Element) -> list[ET.Element]:
    """Every omniProcessElements / childElements node, depth first."""
    out: list[ET.Element] = []

    def walk(node: ET.Element) -> None:
        for el in node:
            if _local(el.tag) in ("omniProcessElements", "childElements"):
                out.append(el)
                walk(el)

    walk(root)
    return out


def check_script(path: Path) -> tuple[list[tuple[str, str]], tuple[str, str, str] | None]:
    findings: list[tuple[str, str]] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [("ERROR", f"XML does not parse: {exc}")], None
    if _local(root.tag) != "OmniScript":
        return findings, None
    otype, sub, lang = _text(root, "type"), _text(root, "subType"), _text(root, "language")
    version = _text(root, "versionNumber")
    unique = _text(root, "uniqueName")
    if otype and sub and lang and version:
        expected = f"{otype}_{sub}_{lang}_{version.split('.')[0]}"
        if unique and unique != expected:
            findings.append(("MEDIUM", f"uniqueName '{unique}' differs from Type_SubType_Language_VersionNumber '{expected}'"))

    elements = _elements(root)
    names = Counter(_text(e, "name") for e in elements if _text(e, "name"))
    dupes = sorted(n for n, c in names.items() if c > 1)
    if dupes:
        findings.append(("HIGH", f"duplicate element names: {', '.join(dupes)}"))

    steps = [e for e in elements if _text(e, "type") == "Step"]
    if len(steps) > MAX_STEPS:
        findings.append(("REVIEW", f"{len(steps)} Step elements; review whether the journey can be simplified"))
    for step in steps:
        actions = [c for c in step.iter() if c is not step and _local(c.tag) == "childElements"
                   and "action" in _text(c, "type").lower()]
        if len(actions) > MAX_ACTIONS_PER_STEP:
            findings.append(("REVIEW", f"Step '{_text(step, 'name')}' has {len(actions)} action elements; "
                                       "prefer one Integration Procedure Action per user intent"))

    identity = (otype, sub, lang) if _text(root, "isActive") == "true" else None
    return findings, identity


def main() -> int:
    parser = argparse.ArgumentParser(description="Check OmniScript metadata for design issues.")
    parser.add_argument("--source-dir", "--manifest-dir", dest="source_dir", default=".",
                        help="Root directory of the Salesforce source (default: .)")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on MEDIUM and REVIEW findings too.")
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    if not source_dir.is_dir():
        print(f"ERROR: source directory not found: {source_dir}")
        sys.exit(1)

    files = sorted(p for p in source_dir.rglob("*") if p.is_file() and p.name.endswith(SUFFIXES))
    if not files:
        print(f"WARN: no OmniScript metadata files found under {source_dir}")
        return 0

    blocking = {"ERROR", "HIGH"} | ({"MEDIUM", "REVIEW"} if args.strict else set())
    failed = False
    count = 0
    active: dict[tuple[str, str, str], list[Path]] = defaultdict(list)
    for path in files:
        findings, identity = check_script(path)
        if identity:
            active[identity].append(path)
        for severity, message in findings:
            count += 1
            print(f"{severity}: {path}: {message}")
            failed = failed or severity in blocking
    for identity, paths in active.items():
        if len(paths) > 1:
            count += 1
            failed = True
            print(f"HIGH: {', '.join(str(p) for p in paths)}: {len(paths)} active OmniScripts share "
                  f"Type/SubType/Language {'/'.join(identity)}")
    if count == 0:
        print(f"OK: {len(files)} OmniScript file(s) checked, no issues")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
