#!/usr/bin/env python3
"""Check CRM Analytics XMD files and the scripts that write them.

Stdlib only. Scans a folder for:
  * XMD JSON documents (*.json) bound for PUT .../versions/<versionID>/xmds/user
  * WaveXmd metadata files (*.xmd, *.xmd-meta.xml)
  * scripts and notes (*.http, *.sh, *.py, *.js, *.cls, *.apex, *.md, *.txt) that call the Xmd REST resource

Every rule encodes a statement from a Summer '26 (262) guide:
  REST  = CRM Analytics REST API Developer Guide, "Xmd Resource"
  XMD   = Analytics Extended Metadata (XMD) Developer Guide
  MDAPI = Metadata API Developer Guide, "WaveXmd"

Rules
  XMD-WRITE-01   ERROR  PUT/PATCH/POST to xmds/main or xmds/system. REST: PUT works "on Xmd User type
                        only" and "cannot be used to update System or Main Xmd types."
  XMD-PATCH-01   ERROR  PATCH on any xmds/ URL. REST: the Xmd resource supports GET and PUT only.
  XMD-VER-01     ERROR  An xmds/main|system|user URL with no /versions/<id>/ segment. REST: every Xmd
                        resource URL is /wave/datasets/<datasetID>/versions/<versionID>/xmds/<type>.
  XMD-JSON-01    ERROR  XMD JSON does not parse. XMD: an invalid file is not applied and all
                        formatting reverts to defaults.
  XMD-EMPTY-01   ERROR  An empty string value. XMD: "XMD doesn't support empty strings."
  XMD-LABEL-01   ERROR  A label longer than 40 characters. XMD reference: label "up to 40 characters."
  XMD-DESC-01    ERROR  A description longer than 1,000 characters. XMD reference.
  XMD-REQ-01     ERROR  WaveXmd missing <dataset>, or a dimension/measure missing <field>,
                        <isDerived>, or <sortIndex>. MDAPI: all marked Required.
  XMD-MULT-01    WARN   customFormat multiplier of 0. XMD: downloads then show every value as 0.
  XMD-DATE-01    WARN   firstDayOfWeek or fiscalMonthOffset in dates. XMD: deprecated at the dataset level.
  XMD-DELIM-01   WARN   Custom delimiters. XMD: not honored in CSV downloads.
  XMD-DATASET-01 WARN   A populated "dataset" block. XMD: CRM Analytics maintains it; do not modify it.

Usage
  python3 check_einstein_analytics_data_model.py --manifest-dir path/to/folder
  python3 check_einstein_analytics_data_model.py --manifest-dir path --strict   # WARN fails too
  python3 check_einstein_analytics_data_model.py --self-test

Exit codes: 0 clean (or WARN only without --strict); 1 any ERROR, a missing folder,
or WARN under --strict.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

FIELD_SECTIONS = ("dimensions", "derivedDimensions", "measures", "derivedMeasures", "dates")
SCRIPT_SUFFIXES = (".http", ".sh", ".py", ".js", ".cls", ".apex", ".md", ".txt")
WRITE_RE = re.compile(r"\b(PUT|PATCH|POST)\b[^\n]{0,200}?xmds/(main|system)\b")
PATCH_RE = re.compile(r"\bPATCH\b[^\n]{0,200}?/xmds/")
XMD_URL_RE = re.compile(r"/wave/datasets/[^\s\"'`]*?xmds/(main|system|user)\b")
Finding = tuple[str, str, str]


def check_script_text(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if WRITE_RE.search(line) is not None:
            findings.append(("ERROR", "XMD-WRITE-01",
                             f"{path}:{line_no}: write to main/system XMD; only xmds/user accepts PUT."))
        elif PATCH_RE.search(line) is not None:
            findings.append(("ERROR", "XMD-PATCH-01",
                             f"{path}:{line_no}: PATCH on an Xmd URL; the resource supports GET and PUT only."))
        for match in XMD_URL_RE.finditer(line):
            if "/versions/" not in match.group(0):
                findings.append(("ERROR", "XMD-VER-01",
                                 f"{path}:{line_no}: Xmd URL without /versions/<versionID>/."))
    return findings


def _walk_strings(node, trail: str, out: list[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            _walk_strings(value, f"{trail}.{key}", out)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            _walk_strings(value, f"{trail}[{index}]", out)
    elif isinstance(node, str) and node == "":
        out.append(trail)


def _multiplier(custom_format: str):
    try:
        parsed = json.loads(custom_format)
    except (TypeError, ValueError):
        return None
    if isinstance(parsed, list) and len(parsed) >= 2:
        return parsed[1]
    return None


def check_xmd_json(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    try:
        doc = json.loads(text)
    except ValueError as exc:
        return [("ERROR", "XMD-JSON-01", f"{path}: JSON does not parse ({exc}); an invalid XMD reverts formatting.")]
    if not isinstance(doc, dict):
        return [("ERROR", "XMD-JSON-01", f"{path}: XMD root must be a JSON object.")]
    if not any(key in doc for key in FIELD_SECTIONS + ("dataset", "organizations", "showDetailsDefaultFields")):
        return findings  # not an XMD document
    empties: list[str] = []
    _walk_strings(doc, "$", empties)
    for trail in empties:
        findings.append(("ERROR", "XMD-EMPTY-01", f"{path}: empty string at {trail}; XMD does not support empty strings."))
    if isinstance(doc.get("dataset"), dict) and doc["dataset"]:
        findings.append(("WARN", "XMD-DATASET-01", f"{path}: populated 'dataset' block; CRM Analytics maintains it."))
    for section in FIELD_SECTIONS:
        entries = doc.get(section)
        if not isinstance(entries, list):
            continue
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            where = f"{section}[{index}]"
            label = entry.get("label")
            if isinstance(label, str) and len(label) > 40:
                findings.append(("ERROR", "XMD-LABEL-01", f"{path}: {where} label is {len(label)} characters; max 40."))
            description = entry.get("description")
            if isinstance(description, str) and len(description) > 1000:
                findings.append(("ERROR", "XMD-DESC-01", f"{path}: {where} description exceeds 1,000 characters."))
            fmt = entry.get("format")
            if isinstance(fmt, dict):
                if _multiplier(fmt.get("customFormat")) == 0:
                    findings.append(("WARN", "XMD-MULT-01", f"{path}: {where} multiplier 0; downloads show every value as 0."))
                if fmt.get("delimiters"):
                    findings.append(("WARN", "XMD-DELIM-01", f"{path}: {where} custom delimiters are not honored in CSV downloads."))
            if section == "dates":
                for key in ("firstDayOfWeek", "fiscalMonthOffset"):
                    if key in entry:
                        findings.append(("WARN", "XMD-DATE-01",
                                         f"{path}: {where}.{key} is deprecated at the dataset level; set it in sfdcDigest or the schema file."))
    return findings


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(element, name: str):
    for child in element:
        if _local(child.tag) == name:
            return child.text
    return None


def check_wavexmd(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return [("ERROR", "XMD-JSON-01", f"{path}: WaveXmd XML does not parse ({exc}).")]
    if _local(root.tag) != "WaveXmd":
        return findings
    if not (_child_text(root, "dataset") or "").strip():
        findings.append(("ERROR", "XMD-REQ-01", f"{path}: WaveXmd is missing the required <dataset> element."))
    for child in root:
        section = _local(child.tag)
        if section not in ("dimensions", "measures"):
            continue
        for required in ("field", "isDerived", "sortIndex"):
            if _child_text(child, required) is None:
                findings.append(("ERROR", "XMD-REQ-01", f"{path}: <{section}> is missing required <{required}>."))
        label = _child_text(child, "label")
        if label is not None and len(label) > 40:
            findings.append(("ERROR", "XMD-LABEL-01", f"{path}: <{section}> label is {len(label)} characters; max 40."))
    return findings


def scan(folder: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        name = path.name
        if name.endswith(".json"):
            findings.extend(check_xmd_json(path, text))
        elif name.endswith(".xmd") or name.endswith(".xmd-meta.xml"):
            findings.extend(check_wavexmd(path, text))
        elif name.endswith(SCRIPT_SUFFIXES):
            findings.extend(check_script_text(path, text))
    return findings


def report(findings: list[Finding], strict: bool) -> int:
    for level, rule, message in findings:
        print(f"{level}: [{rule}] {message}")
    errors = sum(1 for f in findings if f[0] == "ERROR")
    warns = sum(1 for f in findings if f[0] == "WARN")
    print(f"{errors} error(s), {warns} warning(s)")
    if errors or (strict and warns):
        return 1
    return 0


def self_test() -> int:
    base = Path(__file__).resolve().parent / "fixtures"
    good, bad = base / "good", base / "bad"
    if not good.is_dir() or not bad.is_dir():
        print("ERROR: fixtures/good or fixtures/bad is missing")
        return 1
    failures = 0
    good_findings = [f for f in scan(good) if f[0] == "ERROR"]
    if good_findings:
        failures += 1
        print("ERROR: self-test: fixtures/good produced errors:")
        for finding in good_findings:
            print(f"  {finding}")
    bad_findings = scan(bad)
    for path in sorted(p for p in bad.iterdir() if p.is_file()):
        if not any(f[2].startswith(str(path)) for f in bad_findings):
            failures += 1
            print(f"ERROR: self-test: {path.name} produced no finding")
    if failures:
        return 1
    print("self-test passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check CRM Analytics XMD files and Xmd REST calls.")
    parser.add_argument("--manifest-dir", help="folder to scan")
    parser.add_argument("--strict", action="store_true", help="treat WARN as failure")
    parser.add_argument("--self-test", action="store_true", help="run against scripts/fixtures")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.manifest_dir:
        parser.print_help()
        return 1
    folder = Path(args.manifest_dir)
    if not folder.is_dir():
        print(f"ERROR: {folder} is not a folder")
        sys.exit(1)
    candidates = [p for p in folder.rglob("*") if p.is_file() and (
        p.name.endswith((".json", ".xmd", ".xmd-meta.xml")) or p.name.endswith(SCRIPT_SUFFIXES))]
    if not candidates:
        print(f"WARN: no XMD JSON, WaveXmd, or script files under {folder}")
        return 1 if args.strict else 0
    findings = scan(folder)
    if not findings:
        print("No XMD findings. 0 error(s), 0 warning(s)")
        return 0
    return report(findings, args.strict)


if __name__ == "__main__":
    sys.exit(main())
