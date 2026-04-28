#!/usr/bin/env python3
"""Validator for a Salesforce-project RACI matrix expressed as JSON.

Enforces the canonical rules defined in the stakeholder-raci-for-sf-projects skill:

  - exactly one A per row
  - no row has A on a Consulted (C) role
  - every row has at least one R
  - every R/A/C/I value is from the enum {R, A, C, I, --, ""} (-- and empty string mean "not involved")
  - every A cell has an escalation rule with trigger + target + time-box

Usage:
    python3 check_raci.py --json path/to/raci.json
    python3 check_raci.py --json path/to/raci.json --strict     # also fails on warnings
    python3 check_raci.py --help

Exit codes:
    0 - valid
    1 - errors found
    2 - usage error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

VALID_CELL_VALUES = {"R", "A", "C", "I", "--", "—", ""}
INVOLVED_VALUES = {"R", "A", "C", "I"}
REQUIRED_TOP_KEYS = ("project", "phase", "version", "stakeholders", "rows")
REQUIRED_ESCALATION_KEYS = ("trigger", "target", "time_box_business_days")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a Salesforce-project RACI matrix JSON file.",
    )
    parser.add_argument(
        "--json",
        required=True,
        help="Path to the RACI JSON file to validate.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (non-zero exit on warnings).",
    )
    return parser.parse_args()


def load_raci(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"ERROR: file not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR: invalid JSON in {path}: {exc}")


def check_top_level(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED_TOP_KEYS:
        if key not in data:
            errors.append(f"missing top-level key: '{key}'")
    if "stakeholders" in data and not isinstance(data["stakeholders"], list):
        errors.append("'stakeholders' must be a list")
    if "rows" in data and not isinstance(data["rows"], list):
        errors.append("'rows' must be a list")
    return errors


def check_stakeholders(stakeholders: list[Any]) -> tuple[list[str], list[str], set[str]]:
    """Return (errors, warnings, set of stakeholder codes)."""
    errors: list[str] = []
    warnings: list[str] = []
    codes: set[str] = set()
    for idx, sh in enumerate(stakeholders):
        if not isinstance(sh, dict):
            errors.append(f"stakeholders[{idx}]: must be an object")
            continue
        code = sh.get("code")
        role = sh.get("role")
        named = sh.get("named")
        if not code:
            errors.append(f"stakeholders[{idx}]: missing 'code'")
        else:
            if code in codes:
                errors.append(f"stakeholders[{idx}]: duplicate code '{code}'")
            codes.add(code)
        if not role:
            errors.append(f"stakeholders[{idx}] ({code}): missing 'role'")
        if not named or named.strip() in ("", "_____________", "TODO"):
            warnings.append(
                f"stakeholders[{idx}] ({code}): no named individual — surface as a project risk"
            )
    return errors, warnings, codes


def check_row(idx: int, row: Any, stakeholder_codes: set[str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(row, dict):
        errors.append(f"rows[{idx}]: must be an object")
        return errors, warnings

    decision = row.get("decision") or f"<row {idx}>"

    cells = row.get("cells")
    if not isinstance(cells, dict):
        errors.append(f"rows[{idx}] ({decision}): 'cells' must be an object")
        return errors, warnings

    a_holders: list[str] = []
    c_holders: list[str] = []
    r_holders: list[str] = []

    for code, value in cells.items():
        if value is None:
            value = ""
        if not isinstance(value, str):
            errors.append(
                f"rows[{idx}] ({decision}) cell '{code}': value must be a string from {sorted(VALID_CELL_VALUES)}"
            )
            continue
        normalized = value.strip().upper() if value.strip() not in ("--", "—") else value.strip()
        if normalized not in VALID_CELL_VALUES:
            errors.append(
                f"rows[{idx}] ({decision}) cell '{code}': invalid value '{value}' "
                f"(must be one of R / A / C / I / -- / empty)"
            )
            continue
        if normalized == "A":
            a_holders.append(code)
        elif normalized == "C":
            c_holders.append(code)
        elif normalized == "R":
            r_holders.append(code)
        if code not in stakeholder_codes and normalized in INVOLVED_VALUES:
            warnings.append(
                f"rows[{idx}] ({decision}) cell '{code}': stakeholder code not in roster"
            )

    # Rule: exactly one A per row.
    if len(a_holders) == 0:
        errors.append(f"rows[{idx}] ({decision}): no A — every row must have exactly one A")
    elif len(a_holders) > 1:
        errors.append(
            f"rows[{idx}] ({decision}): {len(a_holders)} As ({', '.join(a_holders)}) — "
            f"exactly one A allowed per row"
        )

    # Rule: A and C cannot be the same role.
    overlap = set(a_holders) & set(c_holders)
    if overlap:
        errors.append(
            f"rows[{idx}] ({decision}): role(s) {sorted(overlap)} are both A and C — "
            f"a Consulted role cannot also be Accountable"
        )

    # Rule: at least one R.
    if not r_holders:
        errors.append(
            f"rows[{idx}] ({decision}): no R — every row must have at least one Responsible"
        )

    # Rule: every A has an escalation rule with trigger + target + time-box.
    if a_holders:
        escalation = row.get("escalation")
        if not isinstance(escalation, dict):
            errors.append(
                f"rows[{idx}] ({decision}): A is held by {a_holders[0]} but no escalation rule "
                f"is defined (need trigger + target + time_box_business_days)"
            )
        else:
            for key in REQUIRED_ESCALATION_KEYS:
                if key not in escalation or escalation[key] in (None, "", "TODO"):
                    errors.append(
                        f"rows[{idx}] ({decision}): escalation rule missing '{key}'"
                    )
            tb = escalation.get("time_box_business_days")
            if isinstance(tb, (int, float)) and tb <= 0:
                errors.append(
                    f"rows[{idx}] ({decision}): escalation 'time_box_business_days' must be > 0"
                )

    return errors, warnings


def check_refusal_map(data: dict[str, Any], stakeholder_codes: set[str]) -> list[str]:
    warnings: list[str] = []
    rmap = data.get("refusal_code_map")
    if rmap is None:
        warnings.append(
            "no 'refusal_code_map' present — runtime agents that emit REFUSAL_* codes "
            "will not have a routing target"
        )
        return warnings
    if not isinstance(rmap, dict):
        warnings.append("'refusal_code_map' must be an object")
        return warnings
    for code, entry in rmap.items():
        if not isinstance(entry, dict):
            warnings.append(f"refusal_code_map['{code}']: must be an object")
            continue
        ping = entry.get("ping")
        if not ping:
            warnings.append(f"refusal_code_map['{code}']: missing 'ping' (the named A to page)")
        elif (
            isinstance(ping, str)
            and not ping.startswith("(")  # placeholders like "(matching A)" are acceptable
            and ping not in stakeholder_codes
        ):
            warnings.append(
                f"refusal_code_map['{code}']: 'ping' value '{ping}' not in stakeholder roster"
            )
    return warnings


def main() -> int:
    args = parse_args()
    path = Path(args.json)
    data = load_raci(path)

    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(check_top_level(data))
    if errors:
        report(errors, warnings)
        return 1

    sh_errors, sh_warnings, codes = check_stakeholders(data["stakeholders"])
    errors.extend(sh_errors)
    warnings.extend(sh_warnings)

    for idx, row in enumerate(data["rows"]):
        row_errors, row_warnings = check_row(idx, row, codes)
        errors.extend(row_errors)
        warnings.extend(row_warnings)

    warnings.extend(check_refusal_map(data, codes))

    report(errors, warnings)

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


def report(errors: list[str], warnings: list[str]) -> None:
    if not errors and not warnings:
        print("OK: RACI matrix is valid.")
        return
    if errors:
        print(f"ERRORS ({len(errors)}):", file=sys.stderr)
        for e in errors:
            print(f"  ERROR: {e}", file=sys.stderr)
    if warnings:
        print(f"WARNINGS ({len(warnings)}):", file=sys.stderr)
        for w in warnings:
            print(f"  WARN: {w}", file=sys.stderr)
    if not errors:
        print("OK with warnings.")


if __name__ == "__main__":
    sys.exit(main())
