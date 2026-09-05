#!/usr/bin/env python3
"""Lint a mass-transfer plan CSV before it is loaded.

The canonical plan file is Data-Loader shaped and carries its own rollback column:

    Id,OwnerId,Old_OwnerId
    001XX000003DHP0AAO,005XX0000012aBdAAI,005XX0000012aBcAAI

`OwnerId` is the value that will be written. `Old_OwnerId` is what the record holds
today; swapping the two columns and re-running the same job is the rollback. The
legacy header pair `NewOwnerId` / `OldOwnerId` is accepted as an alias.

Checks
------
ERROR   missing required column (Id, OwnerId)
ERROR   duplicate Id
ERROR   mixed Id key prefixes -- a plan file must target exactly one object
ERROR   malformed Id or OwnerId (not a 15/18-character alphanumeric Salesforce id)
ERROR   OwnerId that is neither a User (005) nor a Queue (00G)
WARN    no rollback column -- the reverse run cannot be built from this file
WARN    plan mixes User (005) and Queue (00G) targets in one file
INFO    row where OwnerId already equals Old_OwnerId -- a no-op write that still
        re-fires the full save order (Apex Developer Guide, Triggers and Order of
        Execution), so it costs automation time for no ownership change
INFO    row count above the batch heuristic (default 10,000, the number of records
        Bulk API 2.0 puts in one automatically created batch)

Exit status
-----------
1 if any ERROR or WARN finding was raised, 0 otherwise. INFO findings are printed
but do not fail the run.

Stdlib only.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ID_PREFIX_USER = "005"
ID_PREFIX_QUEUE = "00G"

# Bulk API 2.0 creates a separate batch for every 10,000 records in the job data.
DEFAULT_BATCH_HEURISTIC = 10_000

ERROR = "ERROR"
WARN = "WARN"
INFO = "INFO"

RECORD_ID_COL = "Id"
NEW_OWNER_COLS = ("OwnerId", "NewOwnerId")
OLD_OWNER_COLS = ("Old_OwnerId", "OldOwnerId")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate a mass-transfer plan CSV.")
    p.add_argument(
        "--plan",
        default="transfer-plan.csv",
        help="Path to the transfer plan CSV (default: transfer-plan.csv).",
    )
    p.add_argument(
        "--max-rows",
        type=int,
        default=DEFAULT_BATCH_HEURISTIC,
        help=(
            "Row count above which an INFO finding is raised. Default %d, the "
            "Bulk API 2.0 automatic batch size." % DEFAULT_BATCH_HEURISTIC
        ),
    )
    return p.parse_args(argv)


def is_sf_id(value: str) -> bool:
    """True for a 15- or 18-character alphanumeric Salesforce id."""
    return len(value) in (15, 18) and value.isalnum()


def pick_column(fieldnames: list[str], candidates: tuple[str, ...]) -> str | None:
    """Return the first candidate present in the header, or None.

    Header matching is case-insensitive so a spreadsheet round-trip that lower-cases
    the header row still lints.
    """
    lowered = {name.lower(): name for name in fieldnames}
    for candidate in candidates:
        actual = lowered.get(candidate.lower())
        if actual is not None:
            return actual
    return None


def lint_plan(plan: Path, max_rows: int) -> list[tuple[str, str]]:
    """Return a list of (severity, message) findings for the plan file."""
    findings: list[tuple[str, str]] = []

    with plan.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])

        id_col = pick_column(fieldnames, (RECORD_ID_COL,))
        new_owner_col = pick_column(fieldnames, NEW_OWNER_COLS)
        old_owner_col = pick_column(fieldnames, OLD_OWNER_COLS)

        if id_col is None:
            findings.append((ERROR, "missing required column: Id"))
        if new_owner_col is None:
            findings.append(
                (ERROR, "missing required column: OwnerId (or legacy NewOwnerId)")
            )
        if id_col is None or new_owner_col is None:
            # Nothing further can be checked row by row.
            return findings

        if old_owner_col is None:
            findings.append(
                (
                    WARN,
                    "no rollback column: add Old_OwnerId holding each record's current "
                    "owner, captured before the update, so the reverse run is a column "
                    "swap rather than a reconstruction",
                )
            )

        seen_ids: set[str] = set()
        id_prefixes: dict[str, int] = {}
        target_prefixes: set[str] = set()
        noop_rows: list[int] = []
        row_count = 0

        for line_no, row in enumerate(reader, start=2):
            row_count += 1

            record_id = (row.get(id_col) or "").strip()
            new_owner = (row.get(new_owner_col) or "").strip()
            old_owner = (row.get(old_owner_col) or "").strip() if old_owner_col else ""

            if not record_id:
                findings.append((ERROR, f"row {line_no}: empty Id"))
            elif not is_sf_id(record_id):
                findings.append((ERROR, f"row {line_no}: malformed Id {record_id!r}"))
            else:
                if record_id in seen_ids:
                    findings.append((ERROR, f"row {line_no}: duplicate Id {record_id}"))
                seen_ids.add(record_id)
                prefix = record_id[:3]
                id_prefixes[prefix] = id_prefixes.get(prefix, 0) + 1

            if not new_owner:
                findings.append((ERROR, f"row {line_no}: empty {new_owner_col}"))
                continue
            if not is_sf_id(new_owner):
                findings.append(
                    (ERROR, f"row {line_no}: malformed {new_owner_col} {new_owner!r}")
                )
                continue

            owner_prefix = new_owner[:3]
            if owner_prefix not in (ID_PREFIX_USER, ID_PREFIX_QUEUE):
                findings.append(
                    (
                        ERROR,
                        f"row {line_no}: {new_owner_col} {new_owner} has key prefix "
                        f"{owner_prefix} -- an owner must be a User (005) or a Queue (00G)",
                    )
                )
                continue
            target_prefixes.add(owner_prefix)

            if old_owner and old_owner == new_owner:
                noop_rows.append(line_no)

        if len(id_prefixes) > 1:
            summary = ", ".join(
                f"{prefix} x{count}" for prefix, count in sorted(id_prefixes.items())
            )
            findings.append(
                (
                    ERROR,
                    "plan mixes Id key prefixes ("
                    + summary
                    + ") -- a transfer job targets exactly one object; split the file",
                )
            )

        if {ID_PREFIX_USER, ID_PREFIX_QUEUE}.issubset(target_prefixes):
            findings.append(
                (
                    WARN,
                    "plan mixes User (005) and Queue (00G) targets -- usually a mistake, "
                    "and not every object accepts a queue owner; split into two plans",
                )
            )

        if noop_rows:
            shown = ", ".join(str(n) for n in noop_rows[:10])
            more = "" if len(noop_rows) <= 10 else f" (+{len(noop_rows) - 10} more)"
            findings.append(
                (
                    INFO,
                    f"{len(noop_rows)} row(s) where the new owner already equals the old "
                    f"owner: line(s) {shown}{more}. Each is a no-op write that still "
                    "re-fires validation rules, flows, and sharing recalculation",
                )
            )

        if row_count > max_rows:
            findings.append(
                (
                    INFO,
                    f"{row_count} rows exceeds the batch heuristic of {max_rows}; the load "
                    "will be split into multiple batches -- confirm the window and the "
                    "serial/parallel setting before running",
                )
            )

    return findings


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    plan = Path(args.plan)

    if not plan.exists():
        print(f"[mass-transfer-ownership] plan file not found: {plan}", file=sys.stderr)
        return 1

    try:
        findings = lint_plan(plan, args.max_rows)
    except UnicodeDecodeError as exc:
        print(
            f"[mass-transfer-ownership] {plan} is not UTF-8 text: {exc}",
            file=sys.stderr,
        )
        return 1

    blocking = [f for f in findings if f[0] in (ERROR, WARN)]

    for severity, message in findings:
        stream = sys.stdout if severity == INFO else sys.stderr
        print(f"{severity}: {message}", file=stream)

    if not blocking:
        print(f"[mass-transfer-ownership] plan OK: {plan}")
        return 0

    errors = sum(1 for severity, _ in blocking if severity == ERROR)
    warns = len(blocking) - errors
    print(
        f"[mass-transfer-ownership] {errors} error(s), {warns} warning(s) in {plan}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        sys.exit(1)
    sys.exit(0)
