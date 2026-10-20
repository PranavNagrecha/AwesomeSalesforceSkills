#!/usr/bin/env python3
"""Checker script for Flow Custom Property Editors skill.

For each *.js-meta.xml that targets lightning__FlowScreen or lightning__FlowAction:
- reads the `configurationEditor` ATTRIBUTE of <targetConfig> (documented form:
  <targetConfig targets="lightning__FlowScreen" configurationEditor="c-volume-editor">,
  lwcguide use-flow-custom-property-editor-lwc-example); a <configurationEditor> child element is not
  the documented form and is not read;
- resolves the editor reference (c-volume-editor or c:volumeEditor) to an LWC bundle folder;
- confirms the bundle's JavaScript dispatches one of configuration_editor_input_value_changed,
  configuration_editor_input_value_deleted or configuration_editor_generic_type_mapping_changed
  (lwcguide use-flow-custom-property-editor-interface).

Severity contract: ERROR (unparseable XML, missing directory) exits 1 always. REVIEW and WARN
findings exit 0 unless --strict. An empty directory is one WARN, exit 0.

Uses stdlib only. Usage:
    python3 check_flow_custom_property_editors.py --manifest-dir path/to/metadata [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

FLOW_TARGETS = ("lightning__FlowScreen", "lightning__FlowAction")
EVENTS = (
    "configuration_editor_input_value_changed",
    "configuration_editor_input_value_deleted",
    "configuration_editor_generic_type_mapping_changed",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Flow custom property editor registration and eventing.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of the metadata (default: .).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on REVIEW/WARN findings too.")
    return parser.parse_args()


def bundle_name(editor_ref: str) -> str:
    """c-volume-editor or c:volumeEditor -> volumeEditor (kebab-case maps to the camelCase folder)."""
    ref = editor_ref.strip()
    if ":" in ref:
        return ref.split(":", 1)[1]
    parts = ref.split("-")[1:] if "-" in ref else [ref]
    return parts[0] + "".join(p.capitalize() for p in parts[1:]) if parts else ref


def find_bundle(root: Path, name: str) -> Path | None:
    for candidate in root.rglob(name):
        if candidate.is_dir():
            return candidate
    return None


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def scan(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    reviews: list[str] = []
    for meta in sorted(root.rglob("*.js-meta.xml")):
        text = meta.read_text(encoding="utf-8", errors="ignore")
        if not any(t in text for t in FLOW_TARGETS):
            continue
        try:
            tree = ET.fromstring(text)
        except ET.ParseError as exc:
            errors.append(f"ERROR: {meta}: XML parse error: {exc}")
            continue
        configs = [e for e in tree.iter() if local(e.tag) == "targetConfig" and any(t in (e.get("targets") or "") for t in FLOW_TARGETS)]
        for config in configs:
            editor = config.get("configurationEditor")
            props = [e for e in config if local(e.tag) == "property"]
            if not editor:
                if len(props) > 5:
                    reviews.append(f"REVIEW: {meta}: Flow targetConfig exposes {len(props)} properties without configurationEditor; check whether admins need a guided editor.")
                continue
            name = bundle_name(editor)
            bundle = find_bundle(root, name)
            if bundle is None:
                reviews.append(f"REVIEW: {meta}: configurationEditor '{editor}' does not resolve to an LWC bundle '{name}' under the project.")
                continue
            js_text = "".join(p.read_text(encoding="utf-8", errors="ignore") for p in bundle.glob("*.js"))
            if not js_text:
                reviews.append(f"REVIEW: {meta}: editor bundle '{name}' has no JavaScript controller.")
            elif not any(ev in js_text for ev in EVENTS):
                reviews.append(f"REVIEW: {meta}: editor bundle '{name}' dispatches none of the documented configuration_editor_* events, so Flow Builder is never told of changes.")
        if re.search(r"<configurationEditor>", text):
            reviews.append(f"REVIEW: {meta}: <configurationEditor> as a child element is not the documented form; use the targetConfig attribute.")
    return errors, reviews


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    if not any(root.rglob("*.js-meta.xml")):
        print(f"WARN: no *.js-meta.xml found under {root}")
        return 1 if args.strict else 0

    errors, reviews = scan(root)
    for line in errors + reviews:
        print(line)
    if errors:
        return 1
    if reviews:
        return 1 if args.strict else 0
    print("No issues found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
