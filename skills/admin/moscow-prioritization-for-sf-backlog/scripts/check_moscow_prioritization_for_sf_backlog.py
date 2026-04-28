#!/usr/bin/env python3
"""Checker script for MoSCoW Prioritization for Salesforce Backlog skill.

Validates a prioritized-backlog file (JSON or CSV) against the canonical schema:
  - every row has moscow in {M, S, C, W}
  - every row has effort in {S, M, L, XL} and value in 1..5 (M and S rows must)
  - every W row has a moscow_subtag of won't-this-release or won't-ever
  - every W row has a non-empty rationale
  - sum(Must effort days) <= supplied capacity
  - sum(Must + Should effort days) <= 0.8 * capacity (warn-only)
  - Must rows account for <= 60% of total effort (warn-only, DSDM rule)

Stdlib only. No pip dependencies.

Usage:
    python3 check_moscow_prioritization_for_sf_backlog.py --backlog backlog.json --capacity 30
    python3 check_moscow_prioritization_for_sf_backlog.py --backlog backlog.csv  --capacity 30
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

VALID_MOSCOW = {"M", "S", "C", "W"}
VALID_EFFORT = {"S", "M", "L", "XL"}
VALID_SUBTAGS = {"won't-this-release", "won't-ever"}

# Default effort -> person-days mapping. Override per team via --effort-map JSON.
DEFAULT_EFFORT_DAYS = {"S": 0.5, "M": 2.0, "L": 6.0, "XL": 12.0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a MoSCoW-prioritized Salesforce backlog file.",
    )
    parser.add_argument(
        "--backlog",
        required=True,
        help="Path to the prioritized backlog file (.json or .csv).",
    )
    parser.add_argument(
        "--capacity",
        type=float,
        required=True,
        help="Team capacity for the target horizon, in person-days.",
    )
    parser.add_argument(
        "--effort-map",
        default=None,
        help="Optional JSON file mapping effort tier (S/M/L/XL) to person-days; overrides defaults.",
    )
    return parser.parse_args()


def load_rows(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Backlog file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".json":
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("JSON backlog must be a list of row objects.")
        return data
    if suffix == ".csv":
        with path.open(encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))
    raise ValueError(f"Unsupported backlog format: {suffix} (use .json or .csv).")


def load_effort_map(path: str | None) -> dict[str, float]:
    if path is None:
        return dict(DEFAULT_EFFORT_DAYS)
    with Path(path).open(encoding="utf-8") as f:
        override = json.load(f)
    if not isinstance(override, dict):
        raise ValueError("Effort map must be a JSON object {tier: days}.")
    merged = dict(DEFAULT_EFFORT_DAYS)
    for tier, days in override.items():
        if tier not in VALID_EFFORT:
            raise ValueError(f"Effort map contains invalid tier: {tier!r}")
        merged[tier] = float(days)
    return merged


def _coerce_int(value) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def check_rows(rows: list[dict], capacity: float, effort_days: dict[str, float]):
    errors: list[str] = []
    warnings: list[str] = []

    must_days = 0.0
    should_days = 0.0
    total_days = 0.0

    for idx, row in enumerate(rows, start=1):
        sid = row.get("story_id") or f"<row {idx}>"
        moscow = (row.get("moscow") or "").strip()
        subtag = (row.get("moscow_subtag") or "").strip() or None
        effort = (row.get("effort") or "").strip()
        value_raw = row.get("value")
        rationale = (row.get("rationale") or "").strip()

        # MoSCoW present and valid
        if moscow not in VALID_MOSCOW:
            errors.append(
                f"{sid}: moscow must be one of {sorted(VALID_MOSCOW)}; got {moscow!r}"
            )
            continue

        # Won't sub-tag rules
        if moscow == "W":
            if subtag not in VALID_SUBTAGS:
                errors.append(
                    f"{sid}: W rows require moscow_subtag in {sorted(VALID_SUBTAGS)}; got {subtag!r}"
                )
            if not rationale:
                errors.append(f"{sid}: W rows require a non-empty rationale")

        # Effort + value required for M and S rows
        if moscow in {"M", "S"}:
            if effort not in VALID_EFFORT:
                errors.append(
                    f"{sid}: {moscow} rows require effort in {sorted(VALID_EFFORT)}; got {effort!r}"
                )
            value = _coerce_int(value_raw)
            if value is None or not (1 <= value <= 5):
                errors.append(
                    f"{sid}: {moscow} rows require value as integer 1..5; got {value_raw!r}"
                )

        # Effort tier validity (when supplied) and accumulation
        if effort:
            if effort not in VALID_EFFORT:
                errors.append(
                    f"{sid}: effort must be one of {sorted(VALID_EFFORT)}; got {effort!r}"
                )
            else:
                days = effort_days[effort]
                total_days += days
                if moscow == "M":
                    must_days += days
                elif moscow == "S":
                    should_days += days

    # Capacity error: Must alone may not exceed capacity
    if must_days > capacity:
        errors.append(
            f"Must effort {must_days:.1f}d exceeds capacity {capacity:.1f}d "
            f"by {must_days - capacity:.1f}d — re-tag or raise capacity"
        )

    # Capacity advisory: Must + Should should fit under 80% of capacity
    soft_cap = 0.8 * capacity
    if (must_days + should_days) > soft_cap:
        warnings.append(
            f"Must+Should effort {must_days + should_days:.1f}d exceeds 80% of capacity "
            f"({soft_cap:.1f}d) — leaves no slack for estimate misses"
        )

    # DSDM 60% rule: warn if Must dominates the backlog
    if total_days > 0 and (must_days / total_days) > 0.60:
        warnings.append(
            f"Must rows are {must_days / total_days:.0%} of total effort — exceeds DSDM ~60% "
            f"guidance; the rubric has likely degraded into a wishlist"
        )

    return errors, warnings


def main() -> int:
    args = parse_args()
    backlog_path = Path(args.backlog)

    try:
        rows = load_rows(backlog_path)
        effort_days = load_effort_map(args.effort_map)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    errors, warnings = check_rows(rows, args.capacity, effort_days)

    for w in warnings:
        print(f"WARN: {w}", file=sys.stderr)
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        return 1
    print(f"OK: {len(rows)} row(s) validated against capacity {args.capacity:.1f}d.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
