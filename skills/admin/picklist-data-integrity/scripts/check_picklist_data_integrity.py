#!/usr/bin/env python3
"""Static checks for picklist field metadata anti-patterns.

Scans Salesforce field metadata for the high-confidence picklist-design
issues documented in this skill:

  1. Picklist field with `<restricted>false</restricted>` (Unrestricted) —
     soft warning recommending a reconciliation strategy.
  2. Picklist with deactivated values (`<isActive>false</isActive>`) —
     reminder to verify records aren't still using them.
  3. Field metadata that defines a value list AND has an adjacent
     validation rule (in the same object's metadata folder) whose
     formula tests `ISPICKVAL(<same field>, "<value-in-the-list>")` for
     every active value — duplicates picklist enforcement.

Stdlib only. Walks `*.field-meta.xml` and looks at neighboring
`validationRules/*.validationRule-meta.xml`.

Usage:
    python3 check_picklist_data_integrity.py --src-root .
    python3 check_picklist_data_integrity.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_NS = "http://soap.sforce.com/2006/04/metadata"
_NS_TAG = f"{{{_NS}}}"


def _strip_ns(tag: str) -> str:
    return tag[len(_NS_TAG):] if tag.startswith(_NS_TAG) else tag


def _is_picklist_field(root: ET.Element) -> bool:
    if _strip_ns(root.tag) != "CustomField":
        return False
    type_el = root.find(f"{_NS_TAG}type")
    return type_el is not None and type_el.text in {"Picklist", "MultiselectPicklist"}


def _scan_field(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError):
        return findings
    root = tree.getroot()
    if not _is_picklist_field(root):
        return findings

    full_name_el = root.find(f"{_NS_TAG}fullName")
    field_name = full_name_el.text if full_name_el is not None else path.stem.replace(".field-meta", "")

    # 1. Restricted = false (Unrestricted)
    for vs in root.findall(f"{_NS_TAG}valueSet"):
        restricted = vs.find(f"{_NS_TAG}restricted")
        if restricted is not None and restricted.text and restricted.text.lower() == "false":
            findings.append(
                f"{path}: picklist `{field_name}` is Unrestricted — without a "
                "value-list reconciliation strategy, integration writes will "
                "produce phantom values silently invisible to reports "
                "(references/gotchas.md § 2)"
            )
        # 2. Deactivated values
        vsd = vs.find(f"{_NS_TAG}valueSetDefinition")
        values = vsd.findall(f"{_NS_TAG}value") if vsd is not None else []
        deactivated = [
            v for v in values
            if (v.find(f"{_NS_TAG}isActive") is not None
                and v.find(f"{_NS_TAG}isActive").text
                and v.find(f"{_NS_TAG}isActive").text.lower() == "false")
        ]
        if deactivated:
            names = []
            for v in deactivated[:5]:
                fn = v.find(f"{_NS_TAG}fullName")
                if fn is not None and fn.text:
                    names.append(fn.text)
            findings.append(
                f"{path}: picklist `{field_name}` has {len(deactivated)} deactivated "
                f"value(s) ({', '.join(names)}{'…' if len(deactivated) > 5 else ''}) — "
                "verify records aren't still using them; deactivation does NOT remove "
                "the value from existing records "
                "(references/gotchas.md § 1)"
            )

    return findings


def _find_validation_duplicates(field_path: Path) -> list[str]:
    """Look for validation rules in sibling validationRules/ folder that
    just enumerate ISPICKVAL for the same field's active values."""
    findings: list[str] = []
    try:
        tree = ET.parse(field_path)
    except (ET.ParseError, OSError):
        return findings
    root = tree.getroot()
    if not _is_picklist_field(root):
        return findings

    full_name_el = root.find(f"{_NS_TAG}fullName")
    if full_name_el is None or not full_name_el.text:
        return findings
    field_api_name = full_name_el.text

    # Collect active values.
    active_values = set()
    for vs in root.findall(f"{_NS_TAG}valueSet"):
        vsd = vs.find(f"{_NS_TAG}valueSetDefinition")
        if vsd is None:
            continue
        for v in vsd.findall(f"{_NS_TAG}value"):
            is_active = v.find(f"{_NS_TAG}isActive")
            fn = v.find(f"{_NS_TAG}fullName")
            if (
                fn is not None and fn.text
                and (is_active is None or is_active.text is None
                     or is_active.text.lower() != "false")
            ):
                active_values.add(fn.text)

    if not active_values:
        return findings

    # Find validation rules in the sibling folder.
    obj_dir = field_path.parent.parent  # objects/<Object>/fields/x.field-meta.xml → ../..
    vr_dir = obj_dir / "validationRules"
    if not vr_dir.is_dir():
        return findings

    for vr_path in vr_dir.glob("*.validationRule-meta.xml"):
        try:
            text = vr_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Heuristic: the formula references ISPICKVAL on this field for every active value.
        # We approximate by counting matches; if we see ISPICKVAL with the field name
        # and >= len(active_values) value strings, flag it.
        matches = re.findall(
            rf"ISPICKVAL\s*\(\s*\w*\.?{re.escape(field_api_name)}\s*,\s*[\"']([^\"']+)[\"']\s*\)",
            text,
            re.IGNORECASE,
        )
        if matches:
            covered = set(matches) & active_values
            if len(covered) >= len(active_values) and len(active_values) > 0:
                findings.append(
                    f"{vr_path}: validation rule formula tests ISPICKVAL on "
                    f"`{field_api_name}` for every active picklist value — "
                    "duplicates the picklist's own membership enforcement; "
                    "prefer Restricted picklist alone "
                    "(references/llm-anti-patterns.md § 2)"
                )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]
    findings: list[str] = []
    for f in root.rglob("*.field-meta.xml"):
        findings.extend(_scan_field(f))
        findings.extend(_find_validation_duplicates(f))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan picklist field metadata for design anti-patterns "
            "(Unrestricted without reconciliation, deactivated values "
            "still on records, validation rules duplicating picklist "
            "membership enforcement)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the metadata tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no picklist data-integrity anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
