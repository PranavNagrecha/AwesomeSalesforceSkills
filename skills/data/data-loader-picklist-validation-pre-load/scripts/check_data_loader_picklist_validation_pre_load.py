#!/usr/bin/env python3
"""
check_data_loader_picklist_validation_pre_load.py

Pre-load picklist validator for Salesforce Data Loader / Bulk API CSVs.

Reads:
    1. A CSV file ready to load.
    2. A JSON picklist map describing the target org's allowed values per
       (object, field, recordTypeDeveloperName).

Reports:
    Per-row, per-column findings where the value is invalid for the row's
    assigned record type. Supports restricted picklists, record-type slices,
    inactive values, multi-select delimiter checks, dependent picklists,
    label-vs-API-name distinction, and the 255-char per-value limit.

The picklist map JSON shape:

    {
      "<SObject>": {
        "__record_types__": ["Default", "Healthcare", "Manufacturing"],
        "<FieldApiName>": {
          "__field_level__": ["A", "B", "C"],
          "__inactive__": ["X"],
          "__multi_select__": false,
          "__gvs_backed__": false,
          "__max_length__": 255,
          "Default":      ["A", "B", "C"],
          "Healthcare":   ["A", "B"],
          "Manufacturing":["B", "C"]
        },
        "__dependencies__": {
          "<DependentField>": {
            "controlling": "<ControllingField>",
            "valid_pairs": {
              "<ControllingValue>": ["<allowedDependentValue>", ...]
            }
          }
        }
      }
    }

Severities:
    FAIL  - load will be rejected by the platform (exit 1)
    WARN  - load may succeed but produces non-conforming data (exit 1)
    INFO  - advisory (does not affect exit code)

stdlib only. No external dependencies.

Usage:
    python3 check_data_loader_picklist_validation_pre_load.py \
        --csv <csv-path> \
        --map <picklist-map.json> \
        --object <SObject> \
        [--rt-column RecordType.DeveloperName] \
        [--default-rt Default] \
        [--multi-select-fields F1,F2] \
        [--dependent-fields Dep1:Ctrl1,Dep2:Ctrl2] \
        [--max-length 255] \
        [--unrestricted-as-warn]

Exit codes:
    0  no FAIL or WARN findings
    1  one or more FAIL or WARN findings
    2  usage / input error
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Reason codes
# ---------------------------------------------------------------------------

REASON_INVALID_FOR_RT = "invalid-value-for-record-type"
REASON_VALUE_NOT_FOUND = "value-not-found"
REASON_INACTIVE = "inactive-value"
REASON_MULTI_SELECT_DELIM = "multi-select-delimiter"
REASON_DEPENDENT_PAIR_INVALID = "dependent-pair-invalid"
REASON_LENGTH_OVER_LIMIT = "length-over-255"
REASON_RT_NOT_FOUND = "record-type-not-found"
REASON_FIELD_NOT_IN_MAP = "field-not-in-map"
REASON_OBJECT_NOT_IN_MAP = "object-not-in-map"

Finding = Tuple[int, str, str, str, str, str]
# (line_number, column, value, record_type, severity, reason)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="check_data_loader_picklist_validation_pre_load.py",
        description="Pre-load picklist validator for Salesforce Data Loader / Bulk API CSVs.",
    )
    p.add_argument("--csv", required=True, help="Path to the CSV file ready to load.")
    p.add_argument("--map", required=True, help="Path to the picklist map JSON.")
    p.add_argument("--object", required=True, help="Target SObject API name (e.g. Account).")
    p.add_argument(
        "--rt-column",
        default="RecordType.DeveloperName",
        help="CSV column carrying the record-type developer name (default: RecordType.DeveloperName).",
    )
    p.add_argument(
        "--default-rt",
        default=None,
        help="Record-type developer name to use when the CSV row's RT cell is blank (defaults to picklist map's first __record_types__ entry).",
    )
    p.add_argument(
        "--multi-select-fields",
        default="",
        help="Comma-separated list of CSV columns that map to multi-select picklists (overrides __multi_select__ in the map).",
    )
    p.add_argument(
        "--dependent-fields",
        default="",
        help="Comma-separated list of dependentField:controllingField pairs (e.g. Sub_Industry__c:Industry).",
    )
    p.add_argument(
        "--max-length",
        type=int,
        default=255,
        help="Per-value max character length to flag (default: 255).",
    )
    p.add_argument(
        "--unrestricted-as-warn",
        action="store_true",
        help="Report invalid values on unrestricted picklists as WARN instead of FAIL.",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-finding output; print summary only.",
    )
    return p.parse_args(argv)


# ---------------------------------------------------------------------------
# Map loading and helpers
# ---------------------------------------------------------------------------


def load_map(path: Path) -> dict:
    if not path.exists():
        print(f"ERROR: picklist map not found: {path}", file=sys.stderr)
        raise SystemExit(2)
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"ERROR: picklist map is not valid JSON: {exc}", file=sys.stderr)
        raise SystemExit(2)
    if not isinstance(data, dict):
        print("ERROR: picklist map must be a JSON object at the top level.", file=sys.stderr)
        raise SystemExit(2)
    return data


def parse_dependent_pairs(spec: str) -> Dict[str, str]:
    """Parse 'Dep1:Ctrl1,Dep2:Ctrl2' into {Dep1: Ctrl1, Dep2: Ctrl2}."""
    pairs: Dict[str, str] = {}
    if not spec:
        return pairs
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            print(
                f"ERROR: --dependent-fields entry '{part}' missing ':' separator.",
                file=sys.stderr,
            )
            raise SystemExit(2)
        dep, ctrl = part.split(":", 1)
        dep = dep.strip()
        ctrl = ctrl.strip()
        if not dep or not ctrl:
            print(
                f"ERROR: --dependent-fields entry '{part}' has empty side.",
                file=sys.stderr,
            )
            raise SystemExit(2)
        pairs[dep] = ctrl
    return pairs


def parse_csv_list(spec: str) -> List[str]:
    return [s.strip() for s in spec.split(",") if s.strip()]


def is_multi_select(
    field: str,
    field_map: dict,
    cli_overrides: List[str],
) -> bool:
    if field in cli_overrides:
        return True
    return bool(field_map.get("__multi_select__", False))


def get_allowed_for_rt(
    field_map: dict,
    record_type: str,
) -> Optional[List[str]]:
    """Return the per-RT allowed list, falling back to __field_level__ if unknown."""
    if record_type and record_type in field_map and isinstance(field_map[record_type], list):
        return field_map[record_type]
    if "__field_level__" in field_map and isinstance(field_map["__field_level__"], list):
        return field_map["__field_level__"]
    return None


def is_inactive(value: str, field_map: dict) -> bool:
    inactive = field_map.get("__inactive__", [])
    return isinstance(inactive, list) and value in inactive


# ---------------------------------------------------------------------------
# Core validation
# ---------------------------------------------------------------------------


def validate_csv(
    csv_path: Path,
    picklist_map: dict,
    sobject: str,
    rt_column: str,
    default_rt: Optional[str],
    multi_select_overrides: List[str],
    dependent_pairs: Dict[str, str],
    max_length: int,
    unrestricted_as_warn: bool,
) -> List[Finding]:
    findings: List[Finding] = []

    if sobject not in picklist_map:
        findings.append(
            (
                0,
                "(map)",
                sobject,
                "",
                "FAIL",
                f"{REASON_OBJECT_NOT_IN_MAP}: object '{sobject}' missing from picklist map",
            )
        )
        return findings

    object_map: dict = picklist_map[sobject]
    known_rts = set(object_map.get("__record_types__", []) or [])
    dependencies_block: dict = object_map.get("__dependencies__", {}) or {}

    if default_rt is None:
        default_rt = next(iter(known_rts), "")

    if not csv_path.exists():
        print(f"ERROR: CSV not found: {csv_path}", file=sys.stderr)
        raise SystemExit(2)

    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            print("ERROR: CSV has no header row.", file=sys.stderr)
            raise SystemExit(2)
        header = list(reader.fieldnames)

        picklist_columns = [
            c for c in header
            if c in object_map and isinstance(object_map[c], dict) and c != "__dependencies__"
        ]

        if not picklist_columns:
            print(
                f"WARN: no CSV columns matched picklist fields on {sobject}. "
                f"Header={header}",
                file=sys.stderr,
            )

        # line numbering: header is line 1; first data row is line 2
        line_no = 1
        for row in reader:
            line_no += 1

            row_rt_raw = (row.get(rt_column) or "").strip() if rt_column in header else ""
            row_rt = row_rt_raw if row_rt_raw else default_rt

            # P0: RT not found (case-sensitive)
            if known_rts and row_rt and row_rt not in known_rts:
                findings.append(
                    (
                        line_no,
                        rt_column,
                        row_rt,
                        row_rt,
                        "FAIL",
                        f"{REASON_RT_NOT_FOUND}: '{row_rt}' not in known RTs "
                        f"{sorted(known_rts)} (lookup is case-sensitive)",
                    )
                )
                # Continue: downstream picklist validation cannot be trusted on a wrong RT,
                # but we still report length/multi-select-delimiter issues which are RT-independent.

            # Validate each picklist column on this row
            for col in picklist_columns:
                cell = (row.get(col) or "")
                if cell == "":
                    continue  # blank cells are not picklist violations

                field_map = object_map[col]
                multi = is_multi_select(col, field_map, multi_select_overrides)

                # Multi-select delimiter check (RT-independent)
                if multi and "," in cell and ";" not in cell:
                    findings.append(
                        (
                            line_no,
                            col,
                            cell,
                            row_rt,
                            "FAIL",
                            f"{REASON_MULTI_SELECT_DELIM}: cell uses ',' but multi-select picklists require ';'",
                        )
                    )
                    continue  # do not split on the wrong delimiter

                tokens: List[str]
                if multi:
                    tokens = [t.strip() for t in cell.split(";") if t.strip()]
                else:
                    tokens = [cell.strip()]

                # Per-token validation
                allowed = get_allowed_for_rt(field_map, row_rt)
                inactive_set = set(field_map.get("__inactive__", []) or [])
                restricted = bool(field_map.get("__restricted__", True))
                # default to restricted=True (modern Salesforce default for new picklists)
                field_max_len = int(field_map.get("__max_length__", max_length))

                for token in tokens:
                    # 255-char limit
                    if len(token) > field_max_len:
                        findings.append(
                            (
                                line_no,
                                col,
                                token,
                                row_rt,
                                "FAIL",
                                f"{REASON_LENGTH_OVER_LIMIT}: value length {len(token)} > {field_max_len}",
                            )
                        )
                        continue

                    # Inactive value (existed but deactivated)
                    if token in inactive_set:
                        findings.append(
                            (
                                line_no,
                                col,
                                token,
                                row_rt,
                                "FAIL",
                                f"{REASON_INACTIVE}: value present in metadata but inactive — "
                                f"reactivate temporarily or remap before load",
                            )
                        )
                        continue

                    # Allowed-list check
                    if allowed is None:
                        findings.append(
                            (
                                line_no,
                                col,
                                token,
                                row_rt,
                                "FAIL",
                                f"{REASON_FIELD_NOT_IN_MAP}: no allowed-values list found for {sobject}.{col}",
                            )
                        )
                        continue

                    if token not in allowed:
                        # Distinguish: value never existed vs valid for another RT
                        field_level = field_map.get("__field_level__", []) or []
                        if token in field_level:
                            severity = "WARN" if (not restricted and unrestricted_as_warn) else "FAIL"
                            findings.append(
                                (
                                    line_no,
                                    col,
                                    token,
                                    row_rt,
                                    severity,
                                    f"{REASON_INVALID_FOR_RT}: allowed for {row_rt}={allowed}; "
                                    f"value valid at field level but not for this record type",
                                )
                            )
                        else:
                            severity = "WARN" if (not restricted and unrestricted_as_warn) else "FAIL"
                            findings.append(
                                (
                                    line_no,
                                    col,
                                    token,
                                    row_rt,
                                    severity,
                                    f"{REASON_VALUE_NOT_FOUND}: value not in metadata for {sobject}.{col} "
                                    f"(typo, label-vs-API-name, or org-version drift)",
                                )
                            )

                # Dependent-picklist pair validation
                ctrl_field = dependent_pairs.get(col)
                dep_block = dependencies_block.get(col) if isinstance(dependencies_block, dict) else None
                if ctrl_field is None and isinstance(dep_block, dict):
                    ctrl_field = dep_block.get("controlling")
                if ctrl_field and isinstance(dep_block, dict):
                    valid_pairs = dep_block.get("valid_pairs", {}) or {}
                    ctrl_value = (row.get(ctrl_field) or "").strip()
                    allowed_for_pair = valid_pairs.get(ctrl_value, [])
                    for token in tokens:
                        if token and token not in allowed_for_pair:
                            findings.append(
                                (
                                    line_no,
                                    col,
                                    token,
                                    row_rt,
                                    "FAIL",
                                    f"{REASON_DEPENDENT_PAIR_INVALID}: ({ctrl_field}='{ctrl_value}', "
                                    f"{col}='{token}') not in allowed pairs {allowed_for_pair}",
                                )
                            )

    return findings


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def render(findings: List[Finding], quiet: bool) -> None:
    fail = sum(1 for f in findings if f[4] == "FAIL")
    warn = sum(1 for f in findings if f[4] == "WARN")
    info = sum(1 for f in findings if f[4] == "INFO")

    if not quiet:
        for line_no, col, value, rt, severity, reason in findings:
            print(
                f"[{severity}] line {line_no} column {col} value \"{value}\" "
                f"record_type={rt or '(none)'} reason={reason}"
            )
        if findings:
            print("")

    if not findings:
        print("OK - no picklist validation findings.")
        return

    print(f"Summary: {fail} FAIL, {warn} WARN, {info} INFO ({len(findings)} total).")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    csv_path = Path(args.csv)
    map_path = Path(args.map)

    picklist_map = load_map(map_path)
    multi_select_overrides = parse_csv_list(args.multi_select_fields)
    dependent_pairs = parse_dependent_pairs(args.dependent_fields)

    findings = validate_csv(
        csv_path=csv_path,
        picklist_map=picklist_map,
        sobject=args.object,
        rt_column=args.rt_column,
        default_rt=args.default_rt,
        multi_select_overrides=multi_select_overrides,
        dependent_pairs=dependent_pairs,
        max_length=args.max_length,
        unrestricted_as_warn=args.unrestricted_as_warn,
    )

    render(findings, args.quiet)

    has_fail = any(f[4] == "FAIL" for f in findings)
    has_warn = any(f[4] == "WARN" for f in findings)
    return 1 if (has_fail or has_warn) else 0


if __name__ == "__main__":
    sys.exit(main())
