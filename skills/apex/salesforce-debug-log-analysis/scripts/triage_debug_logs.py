#!/usr/bin/env python3
"""Triage Salesforce Apex debug logs before forensic analysis.

Scans .log files in a directory and reports:
- size, start timestamp, detected shape, trace flag levels
- truncation risk (within 1 KB of 20 MB cap, or missing EXECUTION_FINISHED)
- exception counts, DML counts, managed-package namespaces touched
- cross-log timeline with inter-log deltas

Stdlib-only. Designed to be the first thing an analyst runs on an uploaded set.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

LOG_CAP_BYTES = 20_000_000
CAP_WARN_WINDOW = 1_024

TIMESTAMP_RE = re.compile(r"^(\d{2}:\d{2}:\d{2}\.\d+)")
HEADER_CATEGORY_RE = re.compile(r"([A-Z_]+),([A-Z]+)")
SHAPE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("batch", re.compile(r"BATCH_APEX_START|BATCH_ID=")),
    ("scheduled", re.compile(r"CRON_TRIGGER_")),
    ("queueable", re.compile(r"CODE_UNIT_STARTED\|\[EventService[^]]*queueable", re.IGNORECASE)),
    ("future", re.compile(r"CODE_UNIT_STARTED\|\[future\]|System\.future", re.IGNORECASE)),
    ("lwc_aura", re.compile(r"CODE_UNIT_STARTED\|\[EventService[^]]*aura", re.IGNORECASE)),
    ("visualforce", re.compile(r"VF_PAGE_MESSAGE|VF_APEX_CALL")),
    ("platform_event", re.compile(r"CODE_UNIT_STARTED\|[^|]*__e[^|]*trigger", re.IGNORECASE)),
    ("cdc", re.compile(r"CODE_UNIT_STARTED\|[^|]*__ChangeEvent[^|]*trigger", re.IGNORECASE)),
    ("test", re.compile(r"CODE_UNIT_STARTED\|[^|]*\.test|TESTING_LIMITS", re.IGNORECASE)),
]
CASCADE_TRIGGER_RE = re.compile(r"CODE_UNIT_STARTED\|[^|]*trigger", re.IGNORECASE)
FLOW_INTERVIEW_RE = re.compile(r"FLOW_START_INTERVIEW_BEGIN")
EXCEPTION_RE = re.compile(r"EXCEPTION_THROWN|FATAL_ERROR|FLOW_ELEMENT_FAULT|VALIDATION_FAIL")
DML_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d+ \([0-9]+\)\|DML_BEGIN", re.MULTILINE)
MANAGED_PKG_RE = re.compile(r"ENTERING_MANAGED_PKG\|([A-Za-z0-9_]+)")
EXECUTION_FINISHED_RE = re.compile(r"EXECUTION_FINISHED")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Triage Salesforce debug logs before forensic analysis."
    )
    parser.add_argument(
        "--logs-dir",
        default=".",
        help="Directory containing .log files (default: current directory).",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="text",
        help="Output format.",
    )
    return parser.parse_args()


def detect_shape(head: str, body: str) -> str:
    for name, pattern in SHAPE_PATTERNS:
        if pattern.search(head) or pattern.search(body):
            return name
    cascade_triggers = len(CASCADE_TRIGGER_RE.findall(body))
    flow_interviews = len(FLOW_INTERVIEW_RE.findall(body))
    if cascade_triggers >= 5 or flow_interviews >= 5:
        return "cascade"
    return "synchronous"


def parse_header_levels(head: str) -> dict[str, str]:
    levels: dict[str, str] = {}
    for category, level in HEADER_CATEGORY_RE.findall(head):
        if category in {
            "APEX_CODE",
            "APEX_PROFILING",
            "CALLOUT",
            "DATA_ACCESS",
            "DB",
            "NBA",
            "SYSTEM",
            "VALIDATION",
            "VISUALFORCE",
            "WAVE",
            "WORKFLOW",
            "SCHEDULING",
        }:
            levels[category] = level
    return levels


def first_timestamp(text: str) -> str:
    for line in text.splitlines()[:10]:
        match = TIMESTAMP_RE.match(line)
        if match:
            return match.group(1)
    return ""


def analyze_file(path: Path) -> dict:
    size = path.stat().st_size
    text = path.read_text(encoding="utf-8", errors="ignore")
    head = text[:4_096]
    body = text
    levels = parse_header_levels(head)
    shape = detect_shape(head, body)
    exceptions = len(EXCEPTION_RE.findall(body))
    dml = len(DML_RE.findall(body))
    namespaces = sorted({ns for ns in MANAGED_PKG_RE.findall(body) if ns})
    truncated = size >= LOG_CAP_BYTES - CAP_WARN_WINDOW
    missing_finish = EXECUTION_FINISHED_RE.search(body) is None
    start = first_timestamp(text)
    warnings: list[str] = []
    if truncated:
        warnings.append(
            f"Log is within {CAP_WARN_WINDOW} bytes of the 20 MB cap; content may be truncated."
        )
    if missing_finish:
        warnings.append("No EXECUTION_FINISHED event; transaction may have been cut off.")
    if shape == "cascade" and levels.get("WORKFLOW", "NONE") in {"NONE", "ERROR", "WARN", "INFO"}:
        warnings.append(
            "WORKFLOW level below FINER; FLOW_ASSIGNMENT_DETAIL events will be missing."
        )
    return {
        "file": str(path),
        "size": size,
        "start": start,
        "shape": shape,
        "levels": levels,
        "exceptions": exceptions,
        "dml_statements": dml,
        "managed_packages": namespaces,
        "warnings": warnings,
    }


def seconds_since_midnight(ts: str) -> float:
    try:
        hours, minutes, rest = ts.split(":")
        return int(hours) * 3600 + int(minutes) * 60 + float(rest)
    except ValueError:
        return -1.0


def build_timeline(entries: list[dict]) -> list[dict]:
    sorted_entries = sorted(entries, key=lambda e: e["start"] or "")
    timeline: list[dict] = []
    previous_secs: float | None = None
    for entry in sorted_entries:
        current = seconds_since_midnight(entry["start"]) if entry["start"] else -1.0
        delta = None
        if previous_secs is not None and current >= 0 and previous_secs >= 0:
            delta = round(current - previous_secs, 2)
        timeline.append({
            "file": entry["file"],
            "start": entry["start"],
            "shape": entry["shape"],
            "size": entry["size"],
            "delta_seconds": delta,
        })
        if current >= 0:
            previous_secs = current
    return timeline


def format_text(entries: list[dict], timeline: list[dict]) -> str:
    lines: list[str] = ["# Debug log triage", ""]
    lines.append("## Inventory")
    lines.append("")
    lines.append(f"{'start':<17} {'size':>10}  shape           file")
    for entry in sorted(entries, key=lambda e: e["start"] or ""):
        lines.append(
            f"{entry['start'] or '-':<17} {entry['size']:>10}  {entry['shape']:<15} {entry['file']}"
        )
    lines.append("")
    lines.append("## Timeline")
    lines.append("")
    for step in timeline:
        delta = f"+{step['delta_seconds']:.1f}s" if step["delta_seconds"] is not None else "-"
        lines.append(f"{step['start'] or '-':<17} {delta:>7}  {step['shape']:<15} {step['file']}")
    lines.append("")
    lines.append("## Per-file detail")
    lines.append("")
    for entry in entries:
        lines.append(f"### {entry['file']}")
        lines.append(f"- shape: {entry['shape']}")
        lines.append(f"- exceptions: {entry['exceptions']}")
        lines.append(f"- DML statements: {entry['dml_statements']}")
        if entry["managed_packages"]:
            lines.append(f"- managed packages: {', '.join(entry['managed_packages'])}")
        if entry["levels"]:
            level_str = ", ".join(f"{cat}={lvl}" for cat, lvl in entry["levels"].items())
            lines.append(f"- trace levels: {level_str}")
        if entry["warnings"]:
            lines.append("- warnings:")
            for warning in entry["warnings"]:
                lines.append(f"  - {warning}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = Path(args.logs_dir)
    if not root.exists():
        print(f"ERROR: logs directory not found: {root}", file=sys.stderr)
        return 2
    files = sorted(path for path in root.glob("*.log") if path.is_file())
    if not files:
        print(f"ERROR: no .log files found in {root}", file=sys.stderr)
        return 2
    entries = [analyze_file(path) for path in files]
    timeline = build_timeline(entries)
    if args.format == "json":
        print(json.dumps({"entries": entries, "timeline": timeline}, indent=2))
    else:
        print(format_text(entries, timeline))
    any_warnings = any(entry["warnings"] for entry in entries)
    return 1 if any_warnings else 0


if __name__ == "__main__":
    sys.exit(main())
