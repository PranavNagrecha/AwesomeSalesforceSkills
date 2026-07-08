#!/usr/bin/env python3
"""Linter for an Agentforce Grid worksheet *design spec*.

Agentforce Grid is a no-code Studio tool, so there is no deployable metadata to
validate. Instead, this script lints a JSON design spec — the column plan you
capture before building a worksheet (see templates/grid-worksheet-spec.example.json).
It enforces the rules that actually bite in Grid:

  * columns have a known type (data / ai / action);
  * the pipeline processes left to right — every reference must point to a
    column to its LEFT (no forward or unknown references);
  * the first column is a data column (nothing to process otherwise);
  * AI columns declare a mode (prompt-template needs a template; use-ai needs a model);
  * data columns declare a known source and an object;
  * action columns (update-record) write back from an upstream column to an object/field;
  * the run is acknowledged as metered/Beta (Grid usage is metered in every lifecycle phase).

Stdlib only — no pip dependencies.

Usage:
    python3 check_agentforce_grid.py --spec path/to/worksheet.json
    python3 check_agentforce_grid.py --manifest-dir path/   # scans for *grid-worksheet*.json
    python3 check_agentforce_grid.py --self-test            # lint the bundled example

Exit code 0 = no issues, 1 = issues found (or spec not found).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

COLUMN_TYPES = {"data", "ai", "action"}
DATA_SOURCES = {"salesforce", "data-cloud", "data-360"}
AI_MODES = {"prompt-template", "use-ai"}
ACTION_KINDS = {"update-record", "formula"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint an Agentforce Grid worksheet design spec (JSON) for common issues.",
    )
    parser.add_argument("--spec", help="Path to a single worksheet spec JSON file.")
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Directory to scan for '*grid-worksheet*.json' specs (default: current directory).",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Lint the example spec bundled with this skill and exit.",
    )
    return parser.parse_args()


def _load_json(path: Path) -> tuple[object, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as exc:
        return None, str(exc)


def _check_metering(spec: dict, label: str, issues: list[str]) -> None:
    if not spec.get("beta_acknowledged"):
        issues.append(
            f"{label}: 'beta_acknowledged' is not true — Agentforce Grid is Beta "
            f"(introduced Winter '26); acknowledge it before relying on behavior."
        )
    if not spec.get("billing_reviewed"):
        issues.append(
            f"{label}: 'billing_reviewed' is not true — Grid usage is metered in every "
            f"lifecycle phase; review the Flex Credit / Billing Calculator estimate first."
        )


def _check_column(idx: int, col: dict, seen: set[str], label: str, issues: list[str]) -> None:
    name = col.get("name")
    where = f"{label}: column[{idx}]"
    if not name:
        issues.append(f"{where}: missing 'name'")
    elif name in seen:
        issues.append(f"{where}: duplicate column name '{name}'")

    ctype = col.get("type")
    if ctype not in COLUMN_TYPES:
        issues.append(
            f"{where} '{name}': type '{ctype}' is not one of {sorted(COLUMN_TYPES)}"
        )
        return

    if idx == 0 and ctype != "data":
        issues.append(
            f"{where} '{name}': first column is '{ctype}', but a worksheet should start with a "
            f"'data' column — downstream columns have nothing to process otherwise."
        )

    # References must resolve to a column to the LEFT (left-to-right processing).
    refs = col.get("references") or []
    if not isinstance(refs, list):
        issues.append(f"{where} '{name}': 'references' must be a list")
        refs = []
    for ref in refs:
        if ref not in seen:
            issues.append(
                f"{where} '{name}': reference '{ref}' does not resolve to a column to its left "
                f"(forward or unknown reference; columns process left to right)."
            )

    if ctype == "data":
        if col.get("source") not in DATA_SOURCES:
            issues.append(
                f"{where} '{name}': data column 'source' must be one of {sorted(DATA_SOURCES)}"
            )
        if not col.get("object"):
            issues.append(f"{where} '{name}': data column must name an 'object' to query")

    elif ctype == "ai":
        mode = col.get("mode")
        if mode not in AI_MODES:
            issues.append(
                f"{where} '{name}': AI column 'mode' must be one of {sorted(AI_MODES)}"
            )
        elif mode == "prompt-template" and not col.get("template"):
            issues.append(
                f"{where} '{name}': prompt-template AI column must name a 'template'"
            )
        elif mode == "use-ai" and not col.get("model"):
            issues.append(
                f"{where} '{name}': use-ai AI column must name a 'model' to run the transformation"
            )
        if not refs:
            issues.append(
                f"{where} '{name}': AI column has no 'references' — it has no input to transform"
            )

    elif ctype == "action":
        action = col.get("action")
        if action not in ACTION_KINDS:
            issues.append(
                f"{where} '{name}': action column 'action' must be one of {sorted(ACTION_KINDS)}"
            )
        if action == "update-record":
            if not col.get("object") or not col.get("field"):
                issues.append(
                    f"{where} '{name}': update-record action must name an 'object' and a 'field'"
                )
            if not refs:
                issues.append(
                    f"{where} '{name}': update-record action has no 'references' — it has no "
                    f"upstream value to write back."
                )

    if name:
        seen.add(name)


def check_spec(path: Path) -> list[str]:
    issues: list[str] = []
    data, err = _load_json(path)
    if err is not None:
        return [f"{path}: not valid JSON ({err})"]
    if not isinstance(data, dict):
        return [f"{path}: expected a JSON object at the top level"]

    label = str(path)
    columns = data.get("columns")
    if not isinstance(columns, list) or not columns:
        issues.append(f"{label}: 'columns' must be a non-empty list")
        _check_metering(data, label, issues)
        return issues

    _check_metering(data, label, issues)

    seen: set[str] = set()
    for idx, col in enumerate(columns):
        if not isinstance(col, dict):
            issues.append(f"{label}: column[{idx}] must be an object")
            continue
        _check_column(idx, col, seen, label, issues)
    return issues


def discover_specs(manifest_dir: Path) -> list[Path]:
    return sorted(manifest_dir.rglob("*grid-worksheet*.json"))


def main() -> int:
    args = parse_args()

    if args.self_test:
        example = Path(__file__).resolve().parent.parent / "templates" / "grid-worksheet-spec.example.json"
        specs = [example]
    elif args.spec:
        specs = [Path(args.spec)]
    else:
        root = Path(args.manifest_dir)
        if not root.exists():
            print(f"WARN: manifest directory not found: {root}", file=sys.stderr)
            return 1
        specs = discover_specs(root)
        if not specs:
            print(
                f"No '*grid-worksheet*.json' spec found under {root} — nothing to check.",
            )
            return 0

    all_issues: list[str] = []
    for spec in specs:
        if not spec.exists():
            all_issues.append(f"Spec not found: {spec}")
            continue
        all_issues.extend(check_spec(spec))

    if not all_issues:
        print("No issues found.")
        return 0
    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
