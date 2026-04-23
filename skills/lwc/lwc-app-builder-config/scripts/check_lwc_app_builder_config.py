#!/usr/bin/env python3
"""Checker for LWC js-meta.xml App Builder configuration.

Scans `lwc/**/*.js-meta.xml` files and flags common App Builder / Experience
Builder configuration mistakes. Stdlib only — no pip dependencies.

Findings:
    - isExposed=false (or missing) while <targets> has children
    - <target> entries with no matching <targetConfig> (info-level only)
    - <supportedFormFactors> declared at the bundle root instead of inside <targetConfig>
    - <property type="..."> using an unsupported design-attribute type
    - Missing root <masterLabel>

Usage:
    python3 check_lwc_app_builder_config.py [--manifest-dir path]
    python3 check_lwc_app_builder_config.py path/to/MyComponent.js-meta.xml
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

# App Builder / Experience Builder accept this closed set for design-attribute
# types on non-community targets. Community targets accept a few extras
# (e.g. ContentReference) which we allow too to avoid false positives.
VALID_PROPERTY_TYPES = {
    "String",
    "Integer",
    "Boolean",
    "Color",
    # Community-only types (LWR/Aura Experience Cloud)
    "ContentReference",
    "Source",
}

NS = "{http://soap.sforce.com/2006/04/metadata}"


def _strip_ns(tag: str) -> str:
    if tag.startswith(NS):
        return tag[len(NS):]
    if tag.startswith("{") and "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _line_positions(xml_path: Path) -> dict[int, int]:
    """Map id(element) -> line number using iterparse."""
    positions: dict[int, int] = {}
    try:
        for event, elem in ET.iterparse(str(xml_path), events=("start",)):
            # Python's ET exposes sourceline via element when parser set; fall back to
            # reading the position via the internal _start. We conservatively read
            # getattr to stay stdlib-safe across CPython versions.
            line = getattr(elem, "sourceline", None)
            if line is None:
                # CPython ET does not populate sourceline; skip.
                continue
            positions[id(elem)] = int(line)
    except ET.ParseError:
        pass
    return positions


def _iter_lwc_meta_files(root: Path) -> Iterable[Path]:
    if root.is_file() and root.name.endswith(".js-meta.xml"):
        yield root
        return
    # Typical sfdx layout: **/lwc/<bundle>/<bundle>.js-meta.xml
    yield from root.rglob("*.js-meta.xml")


def check_file(xml_path: Path) -> list[str]:
    issues: list[str] = []
    try:
        tree = ET.parse(str(xml_path))
    except ET.ParseError as exc:
        return [f"{xml_path}: XML parse error: {exc}"]

    root = tree.getroot()
    if _strip_ns(root.tag) != "LightningComponentBundle":
        # Not an LWC meta.xml — ignore.
        return []

    # ------- isExposed vs <targets> -----------------------------------------
    is_exposed_el = root.find(f"{NS}isExposed")
    is_exposed = (
        is_exposed_el is not None
        and (is_exposed_el.text or "").strip().lower() == "true"
    )
    targets_el = root.find(f"{NS}targets")
    target_children = list(targets_el) if targets_el is not None else []
    if target_children and not is_exposed:
        line = getattr(is_exposed_el, "sourceline", None) if is_exposed_el is not None else None
        where = f" (line {line})" if line else ""
        issues.append(
            f"{xml_path}: <isExposed> is false or missing{where} but <targets> lists "
            f"{len(target_children)} surface(s); the component will not appear in any builder."
        )

    # ------- master label ---------------------------------------------------
    master_label = root.find(f"{NS}masterLabel")
    if master_label is None or not (master_label.text or "").strip():
        issues.append(
            f"{xml_path}: missing <masterLabel> — builders will show the bundle API name instead of a friendly label."
        )

    # ------- supportedFormFactors at root -----------------------------------
    root_form_factors = root.find(f"{NS}supportedFormFactors")
    if root_form_factors is not None:
        line = getattr(root_form_factors, "sourceline", None)
        where = f" (line {line})" if line else ""
        issues.append(
            f"{xml_path}: <supportedFormFactors> is declared at the bundle root{where}; "
            f"it only takes effect inside a <targetConfig>."
        )

    # ------- target vs targetConfig coverage --------------------------------
    target_configs_el = root.find(f"{NS}targetConfigs")
    configured_targets: set[str] = set()
    if target_configs_el is not None:
        for tc in target_configs_el.findall(f"{NS}targetConfig"):
            for t in (tc.attrib.get("targets", "") or "").split(","):
                t = t.strip()
                if t:
                    configured_targets.add(t)

    declared_targets = {
        (t.text or "").strip() for t in target_children if (t.text or "").strip()
    }
    uncovered = declared_targets - configured_targets
    # This is informational only — not every target needs a targetConfig.
    for t in sorted(uncovered):
        issues.append(
            f"{xml_path}: target '{t}' has no matching <targetConfig> (info: OK if no per-surface "
            f"admin configuration is needed)."
        )

    # ------- property types & nested form-factor locations ------------------
    if target_configs_el is not None:
        for tc in target_configs_el.findall(f"{NS}targetConfig"):
            tc_targets = tc.attrib.get("targets", "?")
            # Properties
            for prop in tc.findall(f"{NS}property"):
                ptype = (prop.attrib.get("type") or "").strip()
                if ptype and ptype not in VALID_PROPERTY_TYPES:
                    line = getattr(prop, "sourceline", None)
                    where = f" (line {line})" if line else ""
                    issues.append(
                        f"{xml_path}: <property name=\"{prop.attrib.get('name','?')}\" "
                        f"type=\"{ptype}\"> in targetConfig '{tc_targets}'{where} uses an "
                        f"unsupported design-attribute type; valid types are "
                        f"{sorted(VALID_PROPERTY_TYPES)}."
                    )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check LWC js-meta.xml files for App Builder configuration issues.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or directories to scan (default: current directory).",
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Legacy alias for a single root directory.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    roots: list[Path] = []
    if args.manifest_dir:
        roots.append(Path(args.manifest_dir))
    roots.extend(Path(p) for p in args.paths)
    if not roots:
        roots = [Path(".")]

    all_issues: list[str] = []
    scanned = 0
    for root in roots:
        if not root.exists():
            all_issues.append(f"Path not found: {root}")
            continue
        for meta_path in _iter_lwc_meta_files(root):
            scanned += 1
            all_issues.extend(check_file(meta_path))

    if not all_issues:
        print(f"No issues found. Scanned {scanned} meta.xml file(s).")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)
    print(f"Scanned {scanned} meta.xml file(s); {len(all_issues)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
