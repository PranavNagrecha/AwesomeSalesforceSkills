#!/usr/bin/env python3
"""Audit roll-up summary alternatives for scale, coverage, and metadata risks.

Stdlib only. Scans --manifest-dir for *.field-meta.xml, *.flow-meta.xml, *.cls, and
*.trigger, and prints a JSON report (score, findings, summary). Exit 1 when any
finding is reported.

Rules and the Summer '26 (262) source each one encodes:
  HIGH    Aggregate SOQL inside a loop. Apex Developer Guide: aggregate functions other
          than COUNT count each aggregated row as a query row; one query per record
          multiplies queries and rows.
  MEDIUM  A child trigger that maintains a rollup (aggregate SOQL or a *Rollup* call) but
          lacks after delete or after undelete. Apex Developer Guide, trigger events.
  MEDIUM  A RecordBeforeDelete flow that re-queries its own object without excluding
          $Record.Id. Metadata API Developer Guide, Flow: RecordBeforeDelete runs "before
          the record is deleted from the database", so the recount still sees it.
  REVIEW  35 or more roll-up summary fields in the scanned metadata. UNVERIFIED
          (2026-10-03): the per-object limit is documented only on help.salesforce.com.

Usage
  python3 check_roll_up_summary_alternatives.py --manifest-dir force-app
  python3 check_roll_up_summary_alternatives.py --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


SUMMARY_FIELD_RE = re.compile(r"<type>\s*Summary\s*</type>|<summarizedField>", re.IGNORECASE)
AGG_SOQL_RE = re.compile(r"\[\s*SELECT\b.*\b(COUNT|SUM|AVG|MIN|MAX)\s*\(", re.IGNORECASE)
LOOP_RE = re.compile(r"\b(for|while)\b")
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}
TRIGGER_HEADER_RE = re.compile(r"\btrigger\s+\w+\s+on\s+\w+\s*\(([^)]*)\)", re.IGNORECASE)
ROLLUP_CALL_RE = re.compile(r"\b\w*Rollup\w*\s*\.\s*\w+\s*\(|\b(COUNT|SUM|MIN|MAX|AVG)\s*\(", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check metadata and Apex for weak roll-up summary alternative patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan for metadata and Apex.")
    parser.add_argument("--self-test", action="store_true", help="Run against scripts/fixtures/good and bad.")
    return parser.parse_args()


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(item) for item in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


def iter_summary_fields(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*field-meta.xml") if path.is_file())


def iter_apex(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in {".cls", ".trigger"})


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child(element, name: str):
    for child in element:
        if _local(child.tag) == name:
            return child
    return None


def _text(element, name: str) -> str:
    child = _child(element, name) if element is not None else None
    return (child.text or "").strip() if child is not None and child.text else ""


def check_trigger(path: Path, text: str) -> list[str]:
    header = TRIGGER_HEADER_RE.search(text)
    if header is None or ROLLUP_CALL_RE.search(text) is None:
        return []
    events = re.sub(r"\s+", " ", header.group(1).lower())
    missing = [e for e in ("after delete", "after undelete") if e not in events]
    if missing:
        return [f"MEDIUM {path}: rollup trigger lacks {', '.join(missing)}; deleted or restored children leave the parent total wrong"]
    return []


def check_flow(path: Path, text: str) -> list[str]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []
    start = _child(root, "start")
    if start is None or _text(start, "triggerType") != "RecordBeforeDelete":
        return []
    flow_object = _text(start, "object")
    findings: list[str] = []
    for lookup in root:
        if _local(lookup.tag) != "recordLookups" or _text(lookup, "object") != flow_object:
            continue
        excludes_self = False
        for flt in lookup:
            if _local(flt.tag) != "filters":
                continue
            value = _child(flt, "value")
            ref = _text(value, "elementReference") if value is not None else ""
            if _text(flt, "operator") == "NotEqualTo" and ref == "$Record.Id":
                excludes_self = True
        if not excludes_self:
            name = _text(lookup, "name") or "recordLookups"
            findings.append(f"MEDIUM {path}: before-delete flow lookup '{name}' re-queries {flow_object} without Id != $Record.Id; the recount includes the record being deleted")
    return findings


def audit_paths(root: Path) -> tuple[list[str], int]:
    findings: list[str] = []
    summary_fields = [path for path in iter_summary_fields(root) if SUMMARY_FIELD_RE.search(path.read_text(encoding="utf-8", errors="ignore"))]
    if len(summary_fields) >= 35:
        findings.append(f"REVIEW {root}: {len(summary_fields)} roll-up summary field metadata file(s) found; verify the org is not approaching native summary limits")
    flows = sorted(p for p in root.rglob("*.flow-meta.xml") if p.is_file())
    for path in flows:
        findings.extend(check_flow(path, path.read_text(encoding="utf-8", errors="ignore")))
    apex = iter_apex(root)
    for path in apex:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if path.suffix.lower() == ".trigger":
            findings.extend(check_trigger(path, text))
        loop_depth = 0
        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            line = raw_line.strip()
            if LOOP_RE.search(line) and "for each" not in line.lower():
                loop_depth += line.count("{") or 1
            if loop_depth > 0 and AGG_SOQL_RE.search(line):
                findings.append(f"HIGH {path}:{line_number}: aggregate SOQL found inside a loop; collect parent IDs and aggregate once")
            if "}" in line and loop_depth > 0:
                loop_depth = max(0, loop_depth - line.count("}"))
    return findings, len(summary_fields) + len(flows) + len(apex)


def self_test() -> int:
    base = Path(__file__).resolve().parent / "fixtures"
    good, bad = base / "good", base / "bad"
    if not good.is_dir() or not bad.is_dir():
        print("ERROR: fixtures/good or fixtures/bad is missing")
        return 1
    failures = 0
    good_findings, _ = audit_paths(good)
    if good_findings:
        failures += 1
        print(f"ERROR: self-test: fixtures/good produced {good_findings}")
    bad_findings, _ = audit_paths(bad)
    for path in sorted(p for p in bad.rglob("*") if p.is_file()):
        if not any(str(path) in f for f in bad_findings):
            failures += 1
            print(f"ERROR: self-test: bad fixture {path.name} produced no finding")
    if failures:
        return 1
    print("self-test passed")
    return 0


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 files; manifest directory was missing.")

    findings, scanned = audit_paths(root)
    if scanned == 0:
        return emit_result([f"HIGH {root}: no relevant metadata or Apex files found"], "Scanned 0 files; no roll-up-related files were found.")
    summary = f"Scanned {scanned} file(s); {len(findings)} roll-up-alternative finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
