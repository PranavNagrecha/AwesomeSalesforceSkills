#!/usr/bin/env python3
"""Checker for the platform-encryption skill (stdlib only).

Reads a source-format metadata tree (objects/<Obj>/fields/*.field-meta.xml and
sharingRules/*.sharingRules-meta.xml) and reports:

  ERROR  a field or sharing-rule file that does not parse
  ERROR  an <encryptionScheme> value outside the documented enumeration
         (ProbabilisticEncryption, CaseSensitiveDeterministicEncryption,
         CaseInsensitiveDeterministicEncryption, None — api_meta 264 L45623-45630)
  WARN   a Shield-encrypted field used in a criteria-based sharing rule
         ("you can't use ... encrypted fields" — secguide 262 L3478-3479)
  WARN   a formula that names a Classic Encrypted Text field (Classic encrypted
         fields aren't available in formulas — secguide 262 L2526-2527)
  INFO   Classic Encrypted Text fields (a separate feature — secguide 262 L2548)
  INFO   encrypted fields present: confirm background encryption, history
         duplicates and FieldHistoryArchive copies (api_meta 264 L127877-127882;
         secguide 262 L4899-4904)

Exit codes: 1 on any ERROR (or on WARN with --strict); 0 otherwise. A missing
--manifest-dir is an ERROR; a directory with no field files is one WARN, exit 0.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"
SCHEMES = {
    "ProbabilisticEncryption",
    "CaseSensitiveDeterministicEncryption",
    "CaseInsensitiveDeterministicEncryption",
    "None",
}


def child_text(el: ET.Element, tag: str) -> str:
    found = el.find(NS + tag)
    if found is None:
        found = el.find(tag)
    return (found.text or "").strip() if found is not None else ""


def parse(path: Path, findings: list) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        findings.append(("ERROR", f"{path}: XML does not parse ({exc})"))
        return None


def owner_object(path: Path) -> str:
    # objects/<Object>/fields/<Field>.field-meta.xml
    parts = path.parts
    return parts[-3] if len(parts) >= 3 and parts[-2] == "fields" else ""


def run(root: Path) -> list:
    findings: list = []
    field_files = sorted(root.rglob("*.field-meta.xml"))
    if not field_files:
        findings.append(("WARN", f"no *.field-meta.xml files under {root}; nothing to check"))
        return findings

    encrypted: dict[str, Path] = {}
    classic: dict[str, Path] = {}
    formulas: list[tuple[Path, str]] = []
    for path in field_files:
        el = parse(path, findings)
        if el is None:
            continue
        key = f"{owner_object(path)}.{path.name[:-len('.field-meta.xml')]}".lower()
        scheme = child_text(el, "encryptionScheme")
        if scheme and scheme not in SCHEMES:
            findings.append(("ERROR", f"{path}: encryptionScheme '{scheme}' is not a documented value {sorted(SCHEMES)}"))
        elif scheme and scheme != "None":
            encrypted[key] = path
        if child_text(el, "type") == "EncryptedText":
            classic[key] = path
            findings.append(("INFO", f"{path}: Classic Encrypted Text field — Classic Encryption (128-bit AES, View Encrypted Data), not Shield"))
        formula = child_text(el, "formula")
        if formula:
            formulas.append((path, formula.lower()))

    for path in sorted(root.rglob("*.sharingRules-meta.xml")):
        el = parse(path, findings)
        if el is None:
            continue
        obj = path.name[:-len(".sharingRules-meta.xml")]
        for item in el.iter(NS + "criteriaItems"):
            field = child_text(item, "field")
            key = f"{obj}.{field}".lower()
            if key in encrypted:
                findings.append(("WARN", f"{path}: criteria-based sharing rule uses encrypted field {obj}.{field} — criteria can't use encrypted fields (secguide 262 L3478-3479)"))

    for path, formula in formulas:
        for key in classic:
            name = key.split(".", 1)[1]
            if name and name in formula:
                findings.append(("WARN", f"{path}: formula references Classic Encrypted Text field '{name}' — not available in formulas (secguide 262 L2526-2527)"))

    if encrypted:
        findings.append(("INFO", f"{len(encrypted)} Shield-encrypted field(s): confirm background encryption finished and decide enableEncryptFieldHistory / FieldHistoryArchive (secguide 262 L4899-4904)"))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description="Check Shield Platform Encryption metadata for documented pitfalls.")
    ap.add_argument("--manifest-dir", default=".", help="Root of the source-format metadata tree.")
    ap.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings as well as ERROR.")
    args = ap.parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    findings = run(root)
    if len(findings) == 1 and findings[0][1].startswith("no *.field-meta.xml"):
        print(f"WARN: {findings[0][1]}")
        return 0
    for sev, msg in findings:
        print(f"{sev}: {msg}")
    errors = sum(1 for s, _ in findings if s == "ERROR")
    warns = sum(1 for s, _ in findings if s == "WARN")
    print(f"Summary: {errors} error(s), {warns} warning(s)")
    if errors or (args.strict and warns):
        sys.exit(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
