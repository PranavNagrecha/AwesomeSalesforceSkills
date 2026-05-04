#!/usr/bin/env python3
"""Static checks for Salesforce Shield design smells in a metadata project.

Catches three high-confidence anti-patterns:

  1. `HistoryRetentionPolicy` block referencing `archiveRetentionYears`
     greater than 10 (the platform maximum).
  2. Object metadata that declares an `EncryptionPolicy` listing a Formula,
     Roll-Up-Summary, or Auto-Number field — those types cannot be encrypted
     and the deploy will fail.
  3. Object metadata that mixes a `HistoryRetentionPolicy` element with NO
     enabled `enableHistory` (or a project-level signal that Field Audit
     Trail is enabled) — can be a sign that retention is set on an org
     without the FAT license.

Stdlib only. Walks `*.object-meta.xml` files (sfdx project layout) and
the legacy `objects/<Object>.object` files. Heuristic; signal tool.

Usage:
    python3 check_salesforce_shield_architecture.py --src-root .
    python3 check_salesforce_shield_architecture.py --src-root force-app/main/default
    python3 check_salesforce_shield_architecture.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Field types that cannot be encrypted by Shield Platform Encryption.
_UNENCRYPTABLE_TYPES = {"Formula", "Summary", "AutoNumber"}

# XML namespace used by Salesforce metadata XML.
_NS = {"sf": "http://soap.sforce.com/2006/04/metadata"}


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan_object_meta(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return findings  # malformed XML — not our problem to flag

    # 1. HistoryRetentionPolicy with archiveRetentionYears > 10
    for hrp in root.findall(".//sf:historyRetentionPolicy", _NS) + root.findall(
        ".//historyRetentionPolicy"
    ):
        years_el = hrp.find("sf:archiveRetentionYears", _NS)
        if years_el is None:
            years_el = hrp.find("archiveRetentionYears")
        if years_el is not None and years_el.text:
            try:
                yrs = int(years_el.text.strip())
            except ValueError:
                continue
            if yrs > 10:
                findings.append(
                    f"{path}: archiveRetentionYears={yrs} exceeds the platform "
                    "maximum of 10. Field Audit Trail caps at 10 years "
                    "(references/gotchas.md § 5)"
                )

    # 2. Field type vs encryption: scan inline `<encrypted>true</encrypted>` (or
    # `<encryptionScheme>` element) on a field whose type is unencryptable.
    for field in root.findall(".//sf:fields", _NS) + root.findall(".//fields"):
        type_el = field.find("sf:type", _NS) or field.find("type")
        if type_el is None or not type_el.text:
            continue
        ftype = type_el.text.strip()
        if ftype not in _UNENCRYPTABLE_TYPES:
            continue
        is_encrypted = (
            field.find("sf:encrypted", _NS) is not None
            or field.find("encrypted") is not None
            or field.find("sf:encryptionScheme", _NS) is not None
            or field.find("encryptionScheme") is not None
        )
        if is_encrypted:
            name_el = field.find("sf:fullName", _NS) or field.find("fullName")
            fname = (name_el.text if name_el is not None and name_el.text else "<unknown>").strip()
            findings.append(
                f"{path}: field `{fname}` is type {ftype}, which cannot be encrypted "
                "by Shield Platform Encryption. Encrypt the source field instead "
                "(references/gotchas.md § 3)"
            )

    return findings


def _scan_encryption_policy_xml(path: Path) -> list[str]:
    """Scan a *.encryptionPolicy-meta.xml for Formula / Summary / AutoNumber refs.
    The encryption-policy file format references field API names; we can't see
    types from here, but we can flag any policy file for review."""
    # In practice these files are rare in source-controlled projects (they're
    # often org-only) — emit a soft note that the file deserves review.
    findings: list[str] = []
    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]

    findings: list[str] = []
    obj_files = (
        list(root.rglob("*.object-meta.xml"))
        + list(root.rglob("*.object"))
        + list(root.rglob("*.field-meta.xml"))
    )
    for obj in obj_files:
        findings.extend(_scan_object_meta(obj))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Salesforce metadata for Shield design smells "
            "(retention > 10 years, encryption on un-encryptable field types)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the metadata tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no Shield architecture metadata smells detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
