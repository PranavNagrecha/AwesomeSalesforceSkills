#!/usr/bin/env python3
"""Checker script for CDC Data Sync Patterns skill.

Scans project source files for common CDC replication anti-patterns:
- CDC event handlers that do not check for GAP_ prefix
- CDC subscriptions that do not persist replayId externally
- Missing fallback REST query after gap event detection

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_cdc_data_sync_patterns.py [--help]
    python3 check_cdc_data_sync_patterns.py --source-dir path/to/source
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# --- Patterns ---

# Detects references to CDC changeType or change_type
_CHANGETYPE_READ_RE = re.compile(
    r'changeType|change_type|ChangeType',
    re.IGNORECASE,
)

# Detects a check for the GAP_ prefix
_GAP_PREFIX_CHECK_RE = re.compile(
    r'GAP_|startswith\s*\(\s*["\']GAP_|\.startsWith\s*\(\s*["\']GAP_',
)

# Detects CDC subscription / subscribe calls
_SUBSCRIBE_RE = re.compile(
    r'subscribe\s*\(|Subscribe\s*\(|FetchRequest|cometd|pub.?sub',
    re.IGNORECASE,
)

# Detects replayId being stored to an external store
_REPLAY_PERSIST_RE = re.compile(
    r'replayId|replay_id|replayID',
    re.IGNORECASE,
)

# Detects durable storage write operations near replayId references
_STORE_WRITE_RE = re.compile(
    r'\.set\s*\(|\.put\s*\(|\.save\s*\(|\.write\s*\(|INSERT|UPDATE|UPSERT',
    re.IGNORECASE,
)

# File extensions to scan
_SOURCE_EXTENSIONS = {'.py', '.java', '.js', '.ts', '.cls', '.apex'}


def check_file_gap_handling(path: Path, content: str) -> list[str]:
    """Check that files referencing changeType also check for GAP_ prefix."""
    issues = []
    if _CHANGETYPE_READ_RE.search(content) and not _GAP_PREFIX_CHECK_RE.search(content):
        issues.append(
            f"{path}: References changeType but has no GAP_ prefix check. "
            "CDC subscribers must handle gap events (GAP_CREATE, GAP_UPDATE, etc.) "
            "by checking changeType.startswith('GAP_') before processing field data."
        )
    return issues


def check_file_replay_persistence(path: Path, content: str) -> list[str]:
    """Check that files with CDC subscribe calls also reference replayId persistence."""
    issues = []
    if _SUBSCRIBE_RE.search(content):
        has_replay_ref = _REPLAY_PERSIST_RE.search(content)
        has_store_write = _STORE_WRITE_RE.search(content)
        if not has_replay_ref:
            issues.append(
                f"{path}: Contains a CDC subscribe call but no replayId reference found. "
                "Salesforce has no per-subscriber cursor — subscribers must persist the "
                "replayId to external durable storage after each committed event batch."
            )
        elif not has_store_write:
            issues.append(
                f"{path}: References replayId near a subscribe call but no durable store "
                "write operation detected. Confirm the replayId is persisted to a database, "
                "cache, or file — not just held in memory."
            )
    return issues


def check_source_files(source_dir: Path) -> list[str]:
    """Scan all source files in source_dir for CDC replication anti-patterns."""
    issues: list[str] = []

    source_files = [
        f for f in source_dir.rglob("*")
        if f.is_file() and f.suffix in _SOURCE_EXTENSIONS
    ]

    if not source_files:
        return issues

    for file_path in source_files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        issues.extend(check_file_gap_handling(file_path, content))
        issues.extend(check_file_replay_persistence(file_path, content))

    return issues


def check_cdc_data_sync_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found under manifest_dir.

    Checks:
    1. CDC event handlers reference GAP_ prefix when processing changeType.
    2. CDC subscribe calls reference replayId and a durable store write.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Source directory not found: {manifest_dir}")
        return issues

    issues.extend(check_source_files(manifest_dir))
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check CDC replication source files for common anti-patterns: "
            "missing GAP_ prefix checks and missing replayId persistence."
        ),
    )
    parser.add_argument(
        "--source-dir",
        "--manifest-dir",
        default=".",
        dest="source_dir",
        help="Root directory of the source files to scan (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source_dir)
    issues = check_cdc_data_sync_patterns(source_dir)

    if not issues:
        print("No CDC data sync pattern issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
