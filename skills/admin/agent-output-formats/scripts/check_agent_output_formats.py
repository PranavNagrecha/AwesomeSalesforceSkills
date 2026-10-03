#!/usr/bin/env python3
"""Checker for the agent-output-formats skill.

Validates that a converted deliverable (CSV / spreadsheet export) still honours the
Deliverable Contract of the envelope it was converted from, and that the envelope itself is
convertible. Rules (see references/gotchas.md and agents/_shared/DELIVERABLE_CONTRACT.md):

  ENV-REQ-01   envelope carries every required key of output-envelope.schema.json
  ENV-RUNID-01 run_id is ISO-8601 UTC (Z) or a UUID of >= 8 chars, and matches the file stem
  ENV-FIND-01  every finding has id, severity (P0|P1|P2|INFO) and title
  ENV-DIM-01   dimensions_skipped entries carry dimension, state, reason; a LOW
               confidence_impact forces confidence LOW, a MEDIUM one forbids HIGH
  CSV-RUNID-01 every CSV converted from the envelope keeps a run_id column whose values equal
               the envelope run_id (anti-pattern 3: stripping run_id during conversion)
  CSV-XLSX-01  a CSV destined for Excel stays under 1,048,576 rows and 32,767 chars per cell
               (gotcha 6)
  CSV-ID-01    15/18-char Salesforce Ids in a CSV are not case-mangled relative to the envelope
               (gotcha 5: spreadsheets ignore Id case)

Converted CSVs are discovered as siblings of the envelope: ``<run_id>*.csv`` in the same
directory, or any ``*.csv`` under ``--converted-dir``.

Usage:
    python3 check_agent_output_formats.py --envelope docs/reports/<agent>/<run_id>.json
    python3 check_agent_output_formats.py --manifest-dir docs/reports   # every *.json below it
    python3 check_agent_output_formats.py --self-test

stdlib only.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

REQUIRED_KEYS = (
    "agent", "mode", "summary", "confidence", "process_observations",
    "citations", "run_id", "report_path", "envelope_path",
)
SEVERITIES = {"P0", "P1", "P2", "INFO"}
CONFIDENCE = {"HIGH", "MEDIUM", "LOW"}
RUN_ID_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z$")
RUN_ID_UUID = re.compile(r"^[0-9a-fA-F-]{8,}$")
SF_ID = re.compile(r"\b[a-zA-Z0-9]{15}(?:[a-zA-Z0-9]{3})?\b")
XLSX_MAX_ROWS = 1_048_576
XLSX_MAX_CELL = 32_767


def _load(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"__error__": f"{path.name}: envelope is not readable JSON ({exc})"}
    return data if isinstance(data, dict) else {"__error__": f"{path.name}: envelope root is not an object"}


def check_envelope(path: Path, env: dict) -> list[str]:
    issues: list[str] = []
    if "__error__" in env:
        return [f"ENV-REQ-01 {env['__error__']}"]
    missing = [k for k in REQUIRED_KEYS if k not in env]
    if missing:
        issues.append(f"ENV-REQ-01 {path.name}: missing required envelope keys {missing} "
                      "(agents/_shared/schemas/output-envelope.schema.json); a converter cannot "
                      "carry what the envelope never recorded.")
    run_id = str(env.get("run_id", ""))
    if run_id and not (RUN_ID_ISO.match(run_id) or RUN_ID_UUID.match(run_id)):
        issues.append(f"ENV-RUNID-01 {path.name}: run_id '{run_id}' is neither ISO-8601 UTC "
                      "(YYYY-MM-DDTHH-MM-SSZ) nor a UUID of 8+ chars (Deliverable Contract).")
    if run_id and path.stem != run_id:
        issues.append(f"ENV-RUNID-01 {path.name}: file stem '{path.stem}' differs from run_id "
                      f"'{run_id}'; the contract names the envelope <run_id>.json.")
    for i, f in enumerate(env.get("findings") or []):
        if not isinstance(f, dict):
            issues.append(f"ENV-FIND-01 {path.name}: findings[{i}] is not an object.")
            continue
        for key in ("id", "severity", "title"):
            if key not in f:
                issues.append(f"ENV-FIND-01 {path.name}: findings[{i}] lacks '{key}'.")
        if f.get("severity") not in SEVERITIES and "severity" in f:
            issues.append(f"ENV-FIND-01 {path.name}: findings[{i}] severity '{f.get('severity')}' "
                          f"is not one of {sorted(SEVERITIES)}.")
    conf = str(env.get("confidence", "")).upper()
    if conf and conf not in CONFIDENCE:
        issues.append(f"ENV-DIM-01 {path.name}: confidence '{conf}' is not HIGH/MEDIUM/LOW.")
    impacts: list[str] = []
    for i, d in enumerate(env.get("dimensions_skipped") or []):
        if not isinstance(d, dict):
            issues.append(f"ENV-DIM-01 {path.name}: dimensions_skipped[{i}] is not an object.")
            continue
        for key in ("dimension", "state", "reason"):
            if key not in d:
                issues.append(f"ENV-DIM-01 {path.name}: dimensions_skipped[{i}] lacks '{key}'; a "
                              "coverage CSV would show a blank column where the reader needs the gap.")
        impacts.append(str(d.get("confidence_impact", "")).upper())
    if "LOW" in impacts and conf and conf != "LOW":
        issues.append(f"ENV-DIM-01 {path.name}: a skipped dimension has confidence_impact LOW but "
                      f"confidence is {conf}; the contract forces LOW.")
    elif "MEDIUM" in impacts and conf == "HIGH":
        issues.append(f"ENV-DIM-01 {path.name}: a skipped dimension has confidence_impact MEDIUM "
                      "but confidence is HIGH; the contract caps it at MEDIUM.")
    return issues


def _ids_in(obj) -> set[str]:
    text = json.dumps(obj) if not isinstance(obj, str) else obj
    return set(SF_ID.findall(text))


def check_csv(csv_path: Path, env: dict) -> list[str]:
    issues: list[str] = []
    run_id = str(env.get("run_id", ""))
    try:
        with csv_path.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        return [f"CSV-RUNID-01 {csv_path.name}: unreadable CSV ({exc})"]
    if not rows:
        return [f"CSV-RUNID-01 {csv_path.name}: empty CSV (no header row)."]
    header = rows[0]
    if "run_id" not in header:
        issues.append(f"CSV-RUNID-01 {csv_path.name}: no run_id column; a row that leaves the "
                      "envelope must still say which run produced it (anti-pattern 3).")
    else:
        col = header.index("run_id")
        bad = [n for n, r in enumerate(rows[1:], start=2) if len(r) > col and r[col] != run_id]
        if bad:
            issues.append(f"CSV-RUNID-01 {csv_path.name}: run_id differs from the envelope "
                          f"('{run_id}') on {len(bad)} row(s), first at line {bad[0]}.")
    if len(rows) > XLSX_MAX_ROWS:
        issues.append(f"CSV-XLSX-01 {csv_path.name}: {len(rows):,} rows exceeds Excel's "
                      f"{XLSX_MAX_ROWS:,}-row sheet; split the export (gotcha 6).")
    long_cells = [(n, i) for n, r in enumerate(rows, start=1) for i, c in enumerate(r) if len(c) > XLSX_MAX_CELL]
    if long_cells:
        n, i = long_cells[0]
        issues.append(f"CSV-XLSX-01 {csv_path.name}: cell at line {n} column {i + 1} has more than "
                      f"{XLSX_MAX_CELL:,} characters; Excel truncates it silently (gotcha 6).")
    env_ids = _ids_in(env)
    if env_ids:
        lower = {i.lower(): i for i in env_ids}
        csv_ids = set()
        for r in rows[1:]:
            for c in r:
                csv_ids.update(SF_ID.findall(c))
        mangled = sorted(c for c in csv_ids if c.lower() in lower and lower[c.lower()] != c)
        if mangled:
            issues.append(f"CSV-ID-01 {csv_path.name}: {len(mangled)} Salesforce Id(s) changed case "
                          f"relative to the envelope (first: '{mangled[0]}'); 15-char Ids are "
                          "case-sensitive and spreadsheets are not (gotcha 5).")
    return issues


def converted_csvs(envelope: Path, converted_dir: Path | None) -> list[Path]:
    if converted_dir is not None:
        return sorted(converted_dir.rglob("*.csv"))
    return sorted(envelope.parent.glob(f"{envelope.stem}*.csv"))


def run(envelopes: list[Path], converted_dir: Path | None) -> list[str]:
    issues: list[str] = []
    for env_path in envelopes:
        env = _load(env_path) or {}
        issues.extend(check_envelope(env_path, env))
        if "__error__" in env:
            continue
        for c in converted_csvs(env_path, converted_dir):
            issues.extend(check_csv(c, env))
    return issues


def self_test() -> int:
    here = Path(__file__).resolve().parent / "fixtures"
    good = run(sorted((here / "good").glob("*.json")), None)
    bad = run(sorted((here / "bad").glob("*.json")), None)
    expected_bad = {"ENV-REQ-01", "ENV-RUNID-01", "ENV-FIND-01", "ENV-DIM-01", "CSV-RUNID-01", "CSV-ID-01"}
    seen = {i.split()[0] for i in bad}
    ok = not good and expected_bad <= seen
    print(f"good fixture: {len(good)} issue(s) (expected 0)")
    print(f"bad fixture: {len(bad)} issue(s); rules seen {sorted(seen)}")
    for i in bad:
        print("  ", i)
    print("SELF-TEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Check converted agent deliverables against their envelope.")
    ap.add_argument("--envelope", type=Path, help="one <run_id>.json envelope")
    ap.add_argument("--manifest-dir", type=Path, default=None,
                    help="directory scanned recursively for *.json envelopes (default: docs/reports)")
    ap.add_argument("--converted-dir", type=Path, default=None,
                    help="directory holding the converted CSVs (default: siblings named <run_id>*.csv)")
    ap.add_argument("--self-test", action="store_true", help="run the bundled fixtures and exit")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.envelope:
        envelopes = [args.envelope]
    else:
        root = args.manifest_dir or Path("docs/reports")
        if not root.exists():
            print(f"ISSUE: directory not found: {root}")
            return 1
        envelopes = sorted(p for p in root.rglob("*.json") if p.name != "package.json")
    issues = run(envelopes, args.converted_dir)
    if not issues:
        print(f"No issues found across {len(envelopes)} envelope(s).")
        return 0
    for i in issues:
        print(f"ISSUE: {i}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
