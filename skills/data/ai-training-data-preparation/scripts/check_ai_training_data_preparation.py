#!/usr/bin/env python3
"""Audit a training-data CSV extract before it trains an Einstein predictive model.

Stdlib only. Scans --manifest-dir for *.csv extracts. The outcome column and use case
come from --outcome / --type, or from a sidecar file <stem>.training.json such as
{"outcome": "IsWon", "type": "binary", "exclude": ["Id"]}.

Rules (sources: Data Cloud guide, Summer '26, "Create Predictive AI Models From Scratch",
"Address Data Issues", "Glossary for Predictive AI"; thresholds marked heuristic are team
review defaults, not platform rules):
  TRN-ROWS-01   ERROR  Rows outside 400..20,000,000 (Einstein Studio data source requirement).
  TRN-COLS-01   ERROR  Columns outside 3..50 (1 outcome plus 2 others minimum; 50 maximum).
  TRN-OUT-01    ERROR  Outcome column not in the CSV header.
  TRN-OUT-02    ERROR  Binary outcome without exactly two values, or a regression outcome with
                       non-numeric values (Einstein Studio supports regression and binary classification).
  TRN-OUT-03    WARN   Rows with a blank outcome; they cannot train.
  TRN-LEAK-01   ERROR  A predictor whose values determine the outcome on every row (leakage:
                       "variables that contain the information that you're trying to predict").
  TRN-LEAK-02   WARN   Predictor name suggests a post-outcome field (stage, close, reason, won...). Heuristic.
  TRN-ID-01     WARN   One distinct value per row (IDs, names); high-cardinality fields are rarely useful.
  TRN-CARD-01   WARN   Categorical predictor with more than 100 distinct values (Einstein Studio supports
                       up to 100 categories per variable).
  TRN-FILL-01   WARN   Predictor fill rate below --min-fill (default 0.70). Heuristic.
  TRN-CONST-01  WARN   Predictor with one value or none.
  TRN-BAL-01    WARN   Binary minority class below --min-minority (default 0.05). Heuristic.

Usage
  python3 check_ai_training_data_preparation.py --manifest-dir extract --outcome IsWon --type binary
  python3 check_ai_training_data_preparation.py --self-test

Exit codes: 0 clean (WARN allowed unless --strict); 1 on ERROR, a missing folder, or WARN with --strict.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

MIN_ROWS, MAX_ROWS = 400, 20_000_000
MIN_COLS, MAX_COLS = 3, 50
MAX_CATEGORIES = 100
POST_OUTCOME_NAME = re.compile(
    r"(stage|closed|close_?date|reason|is_?won|is_?lost|won_|lost_|probability|resolution|outcome|result)",
    re.IGNORECASE,
)


def _is_number(value: str) -> bool:
    try:
        float(value.replace(",", ""))
        return True
    except ValueError:
        return False


def load_config(csv_path: Path, outcome: str | None, use_case: str | None) -> dict:
    sidecar = csv_path.with_name(f"{csv_path.stem}.training.json")
    config: dict = {}
    if sidecar.exists():
        config = json.loads(sidecar.read_text(encoding="utf-8"))
    if outcome:
        config["outcome"] = outcome
    if use_case:
        config["type"] = use_case
    config.setdefault("exclude", [])
    return config


def audit(csv_path: Path, config: dict, min_fill: float, min_minority: float) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        header = [h.strip() for h in next(reader, [])]
        rows = [r for r in reader if any(cell.strip() for cell in r)]
    n_rows, n_cols = len(rows), len(header)
    name = csv_path.name
    if not MIN_ROWS <= n_rows <= MAX_ROWS:
        out.append(("ERROR", "TRN-ROWS-01", f"{name}: {n_rows} rows; Einstein Studio needs 400 to 20,000,000."))
    if not MIN_COLS <= n_cols <= MAX_COLS:
        out.append(("ERROR", "TRN-COLS-01", f"{name}: {n_cols} columns; Einstein Studio needs 3 to 50."))
    columns = {h: [r[i].strip() if i < len(r) else "" for r in rows] for i, h in enumerate(header)}

    outcome = config.get("outcome")
    use_case = (config.get("type") or "").lower()
    outcome_values: list[str] | None = None
    if outcome:
        if outcome not in columns:
            out.append(("ERROR", "TRN-OUT-01", f"{name}: outcome column '{outcome}' not in header."))
        else:
            outcome_values = columns[outcome]
            known = [v for v in outcome_values if v]
            if len(known) < n_rows:
                out.append(("WARN", "TRN-OUT-03", f"{name}: {n_rows - len(known)} row(s) have a blank outcome."))
            distinct = set(known)
            if use_case == "binary":
                if len(distinct) != 2:
                    out.append(("ERROR", "TRN-OUT-02",
                                f"{name}: binary outcome '{outcome}' has {len(distinct)} distinct value(s), not 2."))
                elif known:
                    minority = min(sum(1 for v in known if v == d) for d in distinct) / len(known)
                    if minority < min_minority:
                        out.append(("WARN", "TRN-BAL-01",
                                    f"{name}: minority class is {minority:.1%} of rows; report AUC and recall, plan the threshold."))
            elif use_case == "regression":
                bad = [v for v in known if not _is_number(v)]
                if bad:
                    out.append(("ERROR", "TRN-OUT-02",
                                f"{name}: regression outcome '{outcome}' has {len(bad)} non-numeric value(s), e.g. '{bad[0]}'."))

    skip = set(config.get("exclude") or []) | ({outcome} if outcome else set())
    for col, values in columns.items():
        if col in skip:
            continue
        filled = [v for v in values if v]
        fill = len(filled) / n_rows if n_rows else 0.0
        distinct = set(filled)
        numeric = bool(filled) and sum(1 for v in filled if _is_number(v)) / len(filled) >= 0.95
        if fill < min_fill:
            out.append(("WARN", "TRN-FILL-01", f"{name}: '{col}' is {fill:.0%} filled (review threshold {min_fill:.0%})."))
        if len(distinct) <= 1:
            out.append(("WARN", "TRN-CONST-01", f"{name}: '{col}' has {len(distinct)} distinct value(s)."))
            continue
        if POST_OUTCOME_NAME.search(col):
            out.append(("WARN", "TRN-LEAK-02",
                        f"{name}: '{col}' looks like a post-outcome field; confirm it is known before the outcome."))
        unique_per_row = len(distinct) == len(filled) and len(filled) >= 0.9 * n_rows
        if unique_per_row:
            out.append(("WARN", "TRN-ID-01", f"{name}: '{col}' has one value per row; drop IDs and names."))
        elif not numeric and len(distinct) > MAX_CATEGORIES:
            out.append(("WARN", "TRN-CARD-01",
                        f"{name}: '{col}' has {len(distinct)} categories; Einstein Studio supports up to 100."))
        if outcome_values is not None and not unique_per_row and 2 <= len(distinct) <= max(2, min(MAX_CATEGORIES, n_rows // 10)):
            mapping: dict[str, set[str]] = defaultdict(set)
            paired = 0
            for value, target in zip(values, outcome_values):
                if value and target:
                    mapping[value].add(target)
                    paired += 1
            if paired >= 0.95 * n_rows and all(len(t) == 1 for t in mapping.values()) \
                    and len({next(iter(t)) for t in mapping.values()}) > 1:
                out.append(("ERROR", "TRN-LEAK-01",
                            f"{name}: '{col}' determines '{outcome}' on every row; this is leakage, exclude it."))
    return out


def scan(root: Path, outcome: str | None, use_case: str | None, min_fill: float,
         min_minority: float) -> tuple[int, list[tuple[str, str, str]]]:
    files = sorted(root.rglob("*.csv"))
    findings: list[tuple[str, str, str]] = []
    for path in files:
        findings.extend(audit(path, load_config(path, outcome, use_case), min_fill, min_minority))
    return len(files), findings


def self_test() -> int:
    here = Path(__file__).resolve().parent / "fixtures"
    _, good = scan(here / "good", None, None, 0.70, 0.05)
    _, bad = scan(here / "bad", None, None, 0.70, 0.05)
    expected = {"TRN-ROWS-01", "TRN-COLS-01", "TRN-OUT-01", "TRN-OUT-02", "TRN-OUT-03", "TRN-LEAK-01",
                "TRN-LEAK-02", "TRN-ID-01", "TRN-CARD-01", "TRN-FILL-01", "TRN-CONST-01", "TRN-BAL-01"}
    seen = {rule for _, rule, _ in bad}
    ok = not good and expected <= seen
    print(f"good fixtures: {len(good)} finding(s) (expected 0)")
    for f in good:
        print("   ", *f)
    print(f"bad fixtures: rules seen {sorted(seen)}; missing {sorted(expected - seen)}")
    print("SELF-TEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit a training-data CSV before an Einstein model trains on it.")
    ap.add_argument("--manifest-dir", default=".", help="Folder scanned recursively for *.csv extracts.")
    ap.add_argument("--outcome", help="Outcome column name (overrides any <stem>.training.json).")
    ap.add_argument("--type", choices=["binary", "regression"], help="Use case type for the outcome.")
    ap.add_argument("--min-fill", type=float, default=0.70, help="Fill-rate review threshold (heuristic).")
    ap.add_argument("--min-minority", type=float, default=0.05, help="Minority-class review threshold (heuristic).")
    ap.add_argument("--strict", action="store_true", help="Treat WARN findings as failures.")
    ap.add_argument("--self-test", action="store_true", help="Run the bundled fixtures and exit.")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    count, findings = scan(root, args.outcome, args.type, args.min_fill, args.min_minority)
    if count == 0:
        print(f"WARN: no CSV extracts found under {root}; nothing checked.")
        return 0
    for severity, rule, message in findings:
        print(f"{severity} {rule}: {message}")
    errors = sum(1 for f in findings if f[0] == "ERROR")
    warns = sum(1 for f in findings if f[0] == "WARN")
    print(f"Checked {count} extract(s): {errors} error(s), {warns} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
