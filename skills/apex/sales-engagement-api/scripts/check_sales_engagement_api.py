#!/usr/bin/env python3
"""Checker script for Sales Engagement API skill.

Analyzes Salesforce Apex metadata in a project directory for common Sales Engagement
API anti-patterns described in references/llm-anti-patterns.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_sales_engagement_api.py [--help]
    python3 check_sales_engagement_api.py --manifest-dir path/to/force-app
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Regex patterns keyed to anti-patterns documented in llm-anti-patterns.md
# ---------------------------------------------------------------------------

# AP-1: Direct DML insert of ActionCadenceTracker
_DML_TRACKER_INSERT = re.compile(
    r"\b(insert|Database\.insert)\s*\(?.*ActionCadenceTracker",
    re.IGNORECASE,
)

# AP-2: Standard Apex trigger on ActionCadenceTracker (without ChangeEvent suffix)
_TRIGGER_ON_TRACKER = re.compile(
    r"\btrigger\s+\w+\s+on\s+ActionCadenceTracker\b(?!\s*ChangeEvent)",
    re.IGNORECASE,
)

# AP-3: Invocable action called without result inspection (heuristic: invoke called but isSuccess not referenced in same file)
_INVOKE_CALL = re.compile(
    r"Invocable\.Action.*\.invoke\s*\(",
    re.IGNORECASE | re.DOTALL,
)
_IS_SUCCESS = re.compile(
    r"\.isSuccess\s*\(\)",
    re.IGNORECASE,
)

# AP-4: DML write on ActionCadence structure objects
_DML_CADENCE_STRUCTURE = re.compile(
    r"\b(insert|update|upsert|delete|Database\.(insert|update|upsert|delete))\s*\(?.*\b(ActionCadence|ActionCadenceStep|ActionCadenceStepVariant)\b",
    re.IGNORECASE,
)

# AP-5: invoke() called inside a for/while loop body (heuristic: invoke on same or next line after loop keyword)
_LOOP_WITH_INVOKE = re.compile(
    r"\b(for|while)\b[^\{]*\{[^\}]*Invocable\.Action[^\}]*\.invoke\s*\(",
    re.IGNORECASE | re.DOTALL,
)

# AP-6: Wrong field name or value on ActionCadenceTracker SOQL
_WRONG_STATE_FIELD = re.compile(
    r"ActionCadenceTracker[^;]*WHERE[^;]*(Status\s*=|State\s*=\s*'(Enrolled|Running|InProgress)')",
    re.IGNORECASE | re.DOTALL,
)

# Constructing ActionCadenceTracker inline (new ActionCadenceTracker(...))
_NEW_TRACKER = re.compile(
    r"\bnew\s+ActionCadenceTracker\s*\(",
    re.IGNORECASE,
)

# DML write on ActionCadenceTracker directly
_DML_TRACKER_ANY = re.compile(
    r"\b(update|upsert|delete|Database\.(update|upsert|delete))\s*\(?.*ActionCadenceTracker",
    re.IGNORECASE,
)


def _find_apex_files(root: Path) -> list[Path]:
    """Return all .cls and .trigger files under root."""
    return list(root.rglob("*.cls")) + list(root.rglob("*.trigger"))


def check_file(path: Path) -> list[str]:
    """Return a list of issue strings for a single Apex file."""
    issues: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues.append(f"{path}: cannot read file — {exc}")
        return issues

    rel = str(path)

    # AP-1 / DML tracker construction
    if _DML_TRACKER_INSERT.search(text) or _NEW_TRACKER.search(text):
        issues.append(
            f"{rel}: ANTI-PATTERN AP-1 — ActionCadenceTracker created or inserted via DML. "
            "Use the 'assignTargetToSalesCadence' invocable action instead."
        )

    # AP-1b / any DML mutation on tracker
    if _DML_TRACKER_ANY.search(text):
        issues.append(
            f"{rel}: ANTI-PATTERN AP-1b — Direct DML mutation (update/upsert/delete) on "
            "ActionCadenceTracker is not supported. Use designated invocable actions."
        )

    # AP-2 / standard trigger on tracker
    if _TRIGGER_ON_TRACKER.search(text):
        issues.append(
            f"{rel}: ANTI-PATTERN AP-2 — Standard Apex trigger on ActionCadenceTracker detected. "
            "ActionCadence objects are not triggerable. Use a CDC Async Apex Trigger on "
            "ActionCadenceTrackerChangeEvent."
        )

    # AP-3 / invoke without isSuccess check
    if _INVOKE_CALL.search(text) and not _IS_SUCCESS.search(text):
        issues.append(
            f"{rel}: ANTI-PATTERN AP-3 — Invocable.Action.invoke() called but .isSuccess() not "
            "referenced. Inspect each Invocable.Action.Result for errors — exceptions are not "
            "thrown on enrollment failure."
        )

    # AP-4 / DML on cadence structure
    if _DML_CADENCE_STRUCTURE.search(text):
        issues.append(
            f"{rel}: ANTI-PATTERN AP-4 — DML write on ActionCadence structure objects detected "
            "(ActionCadence, ActionCadenceStep, ActionCadenceStepVariant). "
            "Cadence structure is read-only via API — build cadences in the Cadence Builder UI."
        )

    # AP-5 / invoke inside loop (coarse heuristic using multiline scan)
    if _LOOP_WITH_INVOKE.search(text):
        issues.append(
            f"{rel}: ANTI-PATTERN AP-5 — Invocable.Action.invoke() appears to be called inside "
            "a loop body. Collect all inputs first, then invoke once for the full list."
        )

    # AP-6 / wrong SOQL field on tracker
    if _WRONG_STATE_FIELD.search(text):
        issues.append(
            f"{rel}: ANTI-PATTERN AP-6 — Incorrect SOQL field or State value on "
            "ActionCadenceTracker. Use State field with values: Active, Complete, Paused, Error."
        )

    return issues


def check_sales_engagement_api(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = _find_apex_files(manifest_dir)

    if not apex_files:
        # Not necessarily an error — the project may not have SE code
        return issues

    for apex_file in sorted(apex_files):
        issues.extend(check_file(apex_file))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Apex metadata for Sales Engagement API anti-patterns. "
            "Detects direct DML on ActionCadenceTracker, standard triggers on CDC-only objects, "
            "missing result inspection on invocable action calls, and other common mistakes."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata / force-app (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_sales_engagement_api(manifest_dir)

    if not issues:
        print("No Sales Engagement API issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
