#!/usr/bin/env python3
"""Structured reader for MASTER_QUEUE.md.

MASTER_QUEUE.md is authoritative. The orchestrator previously used ``grep`` and
``sed`` to find the next task and mutate status. That's fragile — a stray pipe
character, a renamed column, or a trailing whitespace breaks everything.

This script parses the markdown table into typed rows and exposes:

- ``--list``           print every parsed row as JSONL (piping friendly)
- ``--next``           print the first row whose status is in --status (default TODO,RESEARCHED,RESEARCH)
- ``--status``         comma-separated list of eligible statuses for --next
- ``--set-status``     atomically update one row's status (matched by row id)
- ``--id``             row id (the "#" column) required for --set-status
- ``--actor``          actor label to record in the Notes column (required for --set-status)
- ``--summary``        if set, print aggregate status counts and exit

The file is still the single source of truth — this script edits it in place,
preserving whitespace and row order. No migration to YAML is performed.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "MASTER_QUEUE.md"

# Recognized status keywords in the Status column.
STATUSES = {"TODO", "RESEARCHED", "RESEARCH", "IN_PROGRESS", "DONE", "DUPLICATE", "BLOCKED", "UPDATE", "SHIPPABLE"}


@dataclass
class QueueRow:
    line_no: int
    raw_line: str
    cells: list[str]
    id: str | None
    status: str | None
    skill_name: str | None
    domain: str | None
    col_index: dict[str, int]  # column name -> position, for the owning table

    def to_dict(self) -> dict:
        return {
            "line_no": self.line_no,
            "id": self.id,
            "status": self.status,
            "skill_name": self.skill_name,
            "domain": self.domain,
            "cells": self.cells,
        }


def _split_row(line: str) -> list[str]:
    """Split a markdown table row into cell strings.

    Handles escaped pipes (``\\|``) so values like `design \\| audit` don't split.
    """
    placeholder = "\x00"
    text = line.replace("\\|", placeholder)
    parts = [cell.strip().replace(placeholder, "|") for cell in text.split("|")]
    # A markdown row has empty strings at both ends (leading and trailing pipe).
    if parts and parts[0] == "":
        parts = parts[1:]
    if parts and parts[-1] == "":
        parts = parts[:-1]
    return parts


def _parse_queue(text: str) -> list[QueueRow]:
    rows: list[QueueRow] = []
    in_table = False
    header_cells: list[str] | None = None
    col_index: dict[str, int] = {}

    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            in_table = False
            header_cells = None
            col_index = {}
            continue

        cells = _split_row(line)

        # Detect header row (first table row with named columns) + separator (---|---).
        if all(re.fullmatch(r":?-+:?", cell) for cell in cells if cell):
            # separator row — skip but stay in_table
            continue

        if header_cells is None:
            header_cells = [c.lower() for c in cells]
            col_index = {name: i for i, name in enumerate(header_cells)}
            in_table = True
            continue

        # Data row.
        def get(col_names: list[str]) -> str | None:
            for name in col_names:
                if name in col_index and col_index[name] < len(cells):
                    value = cells[col_index[name]].strip()
                    if value:
                        return value
            return None

        status_value = get(["status"])
        status_normalized: str | None = None
        if status_value:
            upper = status_value.upper()
            for known in sorted(STATUSES, key=len, reverse=True):
                if known in upper:
                    status_normalized = known
                    break

        rows.append(
            QueueRow(
                line_no=line_no,
                raw_line=line,
                cells=cells,
                id=get(["#", "id"]),
                status=status_normalized,
                skill_name=get(["skill", "skill name", "name"]),
                domain=get(["domain"]),
                col_index=dict(col_index),
            )
        )
    return rows


def list_cmd(rows: list[QueueRow]) -> int:
    for row in rows:
        print(json.dumps(row.to_dict(), ensure_ascii=False))
    return 0


def next_cmd(rows: list[QueueRow], wanted: set[str]) -> int:
    for row in rows:
        if row.status in wanted:
            print(json.dumps(row.to_dict(), ensure_ascii=False))
            return 0
    print(json.dumps({"error": "no row matches", "wanted": sorted(wanted)}))
    return 1


def summary_cmd(rows: list[QueueRow]) -> int:
    counts: dict[str, int] = {}
    for row in rows:
        key = row.status or "(unparsed)"
        counts[key] = counts.get(key, 0) + 1
    total = len(rows)
    print(f"Queue rows: {total}")
    for status in sorted(counts):
        print(f"  {status:<14} {counts[status]}")
    return 0


def set_status_cmd(text: str, rows: list[QueueRow], row_id: str, new_status: str, actor: str) -> int:
    if new_status not in STATUSES:
        print(f"ERROR: unknown status `{new_status}` — must be one of {sorted(STATUSES)}", file=sys.stderr)
        return 3
    # Match by id first; fall back to skill_name for tables without an id column.
    candidates = [r for r in rows if r.id == row_id]
    if not candidates:
        candidates = [r for r in rows if r.skill_name == row_id]
    if not candidates:
        print(f"ERROR: no row with id or skill_name `{row_id}`", file=sys.stderr)
        return 2
    if len(candidates) > 1:
        print(
            f"ERROR: `{row_id}` matches {len(candidates)} rows; pass a unique id",
            file=sys.stderr,
        )
        return 2
    target = candidates[0]

    status_col = target.col_index.get("status")
    notes_col = target.col_index.get("notes") or target.col_index.get("note")
    if status_col is None:
        print(
            f"ERROR: row on line {target.line_no} has no Status column",
            file=sys.stderr,
        )
        return 2

    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    lines = text.splitlines(keepends=False)
    raw = lines[target.line_no - 1]
    cells = _split_row(raw)
    while len(cells) <= max(status_col, notes_col or 0):
        cells.append("")
    cells[status_col] = new_status
    if notes_col is not None:
        stamp = f"{actor} @ {now}"
        existing = cells[notes_col]
        cells[notes_col] = f"{stamp}; {existing}" if existing else stamp

    new_line = "| " + " | ".join(cells) + " |"
    lines[target.line_no - 1] = new_line
    QUEUE.write_text("\n".join(lines) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
    print(json.dumps({"id": row_id, "status": new_status, "line_no": target.line_no, "actor": actor}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--next", action="store_true")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument(
        "--status",
        type=str,
        default="TODO,RESEARCHED,RESEARCH,UPDATE",
        help="Comma-separated eligible statuses for --next",
    )
    parser.add_argument("--set-status", type=str, default=None)
    parser.add_argument("--id", type=str, default=None)
    parser.add_argument("--actor", type=str, default=None)
    args = parser.parse_args()

    if not QUEUE.exists():
        print(f"ERROR: {QUEUE} not found", file=sys.stderr)
        return 2

    text = QUEUE.read_text(encoding="utf-8")
    rows = _parse_queue(text)

    if args.summary:
        return summary_cmd(rows)
    if args.list:
        return list_cmd(rows)
    if args.next:
        wanted = {s.strip().upper() for s in args.status.split(",") if s.strip()}
        return next_cmd(rows, wanted)
    if args.set_status:
        if not args.id or not args.actor:
            print("ERROR: --set-status requires --id and --actor", file=sys.stderr)
            return 3
        return set_status_cmd(text=text, rows=rows, row_id=args.id, new_status=args.set_status, actor=args.actor)

    parser.print_help()
    return 3


if __name__ == "__main__":
    sys.exit(main())
