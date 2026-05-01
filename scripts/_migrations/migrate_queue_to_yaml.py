#!/usr/bin/env python3
"""One-shot migration: MASTER_QUEUE.md row data → BACKLOG.yaml.

Reads every parsed row from MASTER_QUEUE.md (using the existing parser in
``scripts/queue_reader.py``) and emits the non-DONE rows to ``BACKLOG.yaml``
in the shape proposed in ``docs/QUEUE_FORMAT_PROPOSAL.md``.

Drops:
  - DONE rows (the filesystem under ``skills/`` is authoritative for what's done)
  - rows with no recognized status (summary tables, prose, etc.)

Idempotent: running again rebuilds BACKLOG.yaml from the queue, so it's safe
to re-run after edits.

Usage:
    python3 scripts/_migrations/migrate_queue_to_yaml.py
    python3 scripts/_migrations/migrate_queue_to_yaml.py --dry-run
    python3 scripts/_migrations/migrate_queue_to_yaml.py --include-done

After this lands and ``queue_reader.py`` switches to BACKLOG.yaml, this script
moves to ``scripts/_migrations/`` (already there) and stays as a one-shot
record. New queue edits should go directly to BACKLOG.yaml via queue_reader.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "MASTER_QUEUE.md"

# Rows in these statuses are NOT migrated by default — DONE skills are
# tracked by the filesystem, and rows without a recognized status are noise
# (progress summary tables, prose, headers).
DEFAULT_DROPPED_STATUSES = {"DONE"}

# Recognized status keywords. Self-contained copy — the original lived in
# scripts/queue_reader.py, which has since been rewritten to back from
# BACKLOG.yaml. Keeping this migration script standalone means it stays
# usable as a one-shot recovery tool even after the rewrite.
_STATUSES = {"TODO", "RESEARCHED", "RESEARCH", "IN_PROGRESS", "DONE", "DUPLICATE", "BLOCKED", "UPDATE", "SHIPPABLE"}


@dataclass
class _QueueRow:
    line_no: int
    cells: list[str]
    id: str | None
    status: str | None
    skill_name: str | None
    domain: str | None
    col_index: dict[str, int]


def _split_row(line: str) -> list[str]:
    """Split a markdown table row into cell strings, handling escaped pipes."""
    placeholder = "\x00"
    text = line.replace("\\|", placeholder)
    parts = [cell.strip().replace(placeholder, "|") for cell in text.split("|")]
    if parts and parts[0] == "":
        parts = parts[1:]
    if parts and parts[-1] == "":
        parts = parts[:-1]
    return parts


def _parse_queue(text: str) -> list[_QueueRow]:
    rows: list[_QueueRow] = []
    header_cells: list[str] | None = None
    col_index: dict[str, int] = {}
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            header_cells = None
            col_index = {}
            continue
        cells = _split_row(line)
        if all(re.fullmatch(r":?-+:?", cell) for cell in cells if cell):
            continue
        if header_cells is None:
            header_cells = [c.lower() for c in cells]
            col_index = {name: i for i, name in enumerate(header_cells)}
            continue

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
            for known in sorted(_STATUSES, key=len, reverse=True):
                if known in upper:
                    status_normalized = known
                    break

        rows.append(_QueueRow(
            line_no=line_no,
            cells=cells,
            id=get(["#", "id"]),
            status=status_normalized,
            skill_name=get(["skill", "skill name", "name"]),
            domain=get(["domain"]),
            col_index=dict(col_index),
        ))
    return rows


def _row_to_entry(row) -> OrderedDict:
    """Convert a QueueRow into a BACKLOG.yaml entry. Field order is fixed
    (OrderedDict) so the YAML output is stable across runs — important for
    git diffs and the drift check."""
    cells = row.cells
    col_index = row.col_index

    def cell(*candidates: str) -> str:
        for name in candidates:
            if name in col_index and col_index[name] < len(cells):
                value = cells[col_index[name]].strip()
                if value:
                    return value
        return ""

    summary = cell("summary", "description", "what")
    notes = cell("notes", "note")
    role = cell("role")
    cloud = cell("cloud")

    skill = row.skill_name or row.id or ""
    entry: OrderedDict = OrderedDict()
    entry["id"] = row.id or skill or f"row-{row.line_no}"
    entry["status"] = row.status or "UNKNOWN"
    entry["skill"] = skill
    if row.domain:
        entry["domain"] = row.domain
    if role:
        entry["role"] = role
    if cloud:
        entry["cloud"] = cloud
    if summary:
        entry["summary"] = summary
    if notes:
        entry["notes"] = notes
    entry["source_line"] = row.line_no
    entry["history"] = []
    return entry


def _yaml_quote(value: str) -> str:
    """Quote a string for safe YAML output. We use double-quotes and escape
    backslash + quote — that handles every character safely. Stays stdlib."""
    text = str(value)
    text = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def render_yaml(entries: list[OrderedDict]) -> str:
    """Render the entries as YAML. Hand-written (stdlib only) so the migration
    has no dependency on PyYAML — the output shape is intentionally narrow
    (flat list of dicts, no nesting beyond ``history: []``) which makes the
    custom emitter trivial and stable."""
    out: list[str] = []
    out.append("# Generated by scripts/_migrations/migrate_queue_to_yaml.py.")
    out.append("# Re-run the migration to rebuild from MASTER_QUEUE.md, OR edit this")
    out.append("# file directly via scripts/queue_reader.py.")
    out.append("# See docs/QUEUE_FORMAT_PROPOSAL.md for the field shape.")
    out.append("")
    if not entries:
        out.append("[]")
        return "\n".join(out) + "\n"
    for entry in entries:
        first = True
        for key, value in entry.items():
            prefix = "- " if first else "  "
            first = False
            if isinstance(value, list):
                if not value:
                    out.append(f"{prefix}{key}: []")
                else:
                    out.append(f"{prefix}{key}:")
                    for item in value:
                        out.append(f"    - {_yaml_quote(item)}")
            elif isinstance(value, int):
                out.append(f"{prefix}{key}: {value}")
            else:
                out.append(f"{prefix}{key}: {_yaml_quote(value)}")
    return "\n".join(out) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate MASTER_QUEUE.md rows to BACKLOG.yaml.",
    )
    parser.add_argument(
        "--out", type=Path, default=ROOT / "BACKLOG.yaml",
        help="Output YAML path (default ./BACKLOG.yaml).",
    )
    parser.add_argument(
        "--include-done", action="store_true",
        help="Include DONE rows (default: drop them — filesystem is authoritative).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print summary instead of writing the file.",
    )
    args = parser.parse_args()

    if not QUEUE.exists():
        print(f"ERROR: {QUEUE} not found", file=sys.stderr)
        return 2

    text = QUEUE.read_text(encoding="utf-8")
    rows = _parse_queue(text)

    dropped = set(DEFAULT_DROPPED_STATUSES)
    if args.include_done:
        dropped.discard("DONE")

    kept_rows = [r for r in rows if r.status and r.status not in dropped]
    skipped_no_status = sum(1 for r in rows if not r.status)
    skipped_done = sum(1 for r in rows if r.status == "DONE")

    entries = [_row_to_entry(r) for r in kept_rows]

    if args.dry_run:
        print(f"Would migrate {len(entries)} row(s) → {args.out.relative_to(ROOT)}")
        print(f"  parsed rows total: {len(rows)}")
        print(f"  skipped (no recognized status): {skipped_no_status}")
        print(f"  skipped (DONE — filesystem authoritative): {skipped_done}")
        from collections import Counter
        status_counts = Counter(e["status"] for e in entries)
        for status in sorted(status_counts):
            print(f"  kept ({status}): {status_counts[status]}")
        return 0

    rendered = render_yaml(entries)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(rendered, encoding="utf-8")
    print(
        f"Wrote {args.out.relative_to(ROOT)} — "
        f"{len(entries)} entries (skipped {skipped_done} DONE, "
        f"{skipped_no_status} unparsed)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
