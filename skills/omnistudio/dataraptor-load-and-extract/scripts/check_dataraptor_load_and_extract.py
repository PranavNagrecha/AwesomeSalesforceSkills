#!/usr/bin/env python3
"""Checker for the dataraptor-load-and-extract skill.

Scans OmniDataTransform (DataRaptor / Omnistudio Data Mapper) metadata in Salesforce
DX source format (`omniDataTransforms/*.rpt-meta.xml`) or Metadata API format
(`*.omniDataTransform`) and reports findings grounded in the OmniDataTransform
reference (Industries Common Resources Developer Guide, Summer '26) and the
Trailhead "Omnistudio Data Mappers" module:

  ERROR   file does not parse
  HIGH    Turbo Extract with formula items (Turbo Extract doesn't support formulas)
  MEDIUM  Extract or Turbo Extract with fieldLevelSecurityEnabled=false
  MEDIUM  multi-object Load with rollbackOnError=false (partial commits possible)
  REVIEW  Load without any upsertKey item (every run creates records)
  REVIEW  errorIgnored=true (processing continues past errors)
  REVIEW  processSuperBulk=true or synchronousProcessThreshold>0 (large inputs run
          as Apex batch jobs, so the call can return before records exist)
  REVIEW  responseCacheTtlMinutes above 60 (stale cached responses)

Earlier versions flagged Integration Procedures that lacked an "iferror" string, and
leftover placeholder markers in DataPack JSON. The iferror node name is not documented
in the fetched sources, so that rule was removed.

Exit codes: 1 if the directory is missing, a file doesn't parse, or any HIGH finding
exists (MEDIUM and REVIEW too with --strict); 0 otherwise. Stdlib only.

Usage:
    python3 check_dataraptor_load_and_extract.py --source-dir force-app [--strict]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SUFFIXES = (".rpt-meta.xml", ".omniDataTransform", ".omniDataTransform-meta.xml")


def _local(tag: str) -> str:
    return tag.split("}")[-1]


def _text(parent: ET.Element, name: str) -> str:
    for el in parent:
        if _local(el.tag) == name:
            return (el.text or "").strip()
    return ""


def _float(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 0.0


def check_file(path: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [("ERROR", f"XML does not parse: {exc}")]
    if _local(root.tag) != "OmniDataTransform":
        return findings
    dtype = _text(root, "type").lower()
    items = [el for el in root if _local(el.tag) == "omniDataTransformItem"]

    if "turbo" in dtype and any(_text(i, "formulaExpression") for i in items):
        findings.append(("HIGH", "Turbo Extract has formula items; Turbo Extract doesn't support formulas"))
    if "extract" in dtype and _text(root, "fieldLevelSecurityEnabled") == "false":
        findings.append(("MEDIUM", "fieldLevelSecurityEnabled is false; restricted users may receive fields they can't see"))
    if dtype == "load":
        targets = {_text(i, "outputObjectName") for i in items if _text(i, "outputObjectName")}
        if len(targets) > 1 and _text(root, "rollbackOnError") != "true":
            findings.append(("MEDIUM", f"Load writes {len(targets)} objects with rollbackOnError not true; partial commits possible"))
        if not any(_text(i, "upsertKey") == "true" for i in items):
            findings.append(("REVIEW", "Load has no Upsert Key; every run creates new records"))
    if _text(root, "errorIgnored") == "true":
        findings.append(("REVIEW", "errorIgnored is true; processing continues after errors"))
    if _text(root, "processSuperBulk") == "true" or _float(_text(root, "synchronousProcessThreshold")) > 0:
        findings.append(("REVIEW", "inputs above synchronousProcessThreshold (or with processSuperBulk) run as Apex batch jobs"))
    if _float(_text(root, "responseCacheTtlMinutes")) > 60:
        findings.append(("REVIEW", f"responseCacheTtlMinutes is {_text(root, 'responseCacheTtlMinutes')}; cached responses may be stale"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check OmniDataTransform (DataRaptor) metadata for common issues.")
    parser.add_argument("--source-dir", default=".", help="Root directory of the Salesforce source (default: .)")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on MEDIUM and REVIEW findings too.")
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    if not source_dir.is_dir():
        print(f"ERROR: source directory not found: {source_dir}")
        sys.exit(1)

    files = sorted(p for p in source_dir.rglob("*") if p.is_file() and p.name.endswith(SUFFIXES))
    if not files:
        print(f"WARN: no OmniDataTransform files found under {source_dir}")
        return 0

    blocking = {"ERROR", "HIGH"} | ({"MEDIUM", "REVIEW"} if args.strict else set())
    failed = False
    count = 0
    for path in files:
        for severity, message in check_file(path):
            count += 1
            print(f"{severity}: {path}: {message}")
            failed = failed or severity in blocking
    if count == 0:
        print(f"OK: {len(files)} OmniDataTransform file(s) checked, no issues")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
