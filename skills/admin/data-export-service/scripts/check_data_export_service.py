#!/usr/bin/env python3
"""Static auditor for an org's Data Export Service runbook.

Walks a documentation / runbook directory (typically under `docs/`,
`runbooks/`, or a checked-in compliance folder) and flags concrete
issues this skill cares about. Stdlib only — no pip dependencies.

Heuristics:

  1. Any file mentions "Data Export" or "weekly export" without also
     mentioning the 48-hour download window.
  2. Any file calls Data Export a "backup" without acknowledging the
     no-restore gap (must mention "no restore," "evidence archive,"
     or "Backup and Restore").
  3. Any file describes Data Export coverage without acknowledging Big
     Object / External Object / metadata exclusions.
  4. Any file recommends including binary content (Files / Documents /
     Attachments) without naming a specific consumer requirement.
  5. Any file claims a scriptable / API trigger for Data Export.

Usage:
    python3 check_data_export_service.py [--manifest-dir path]

Default scans common runbook roots: docs/, runbooks/, compliance/.
Exits 1 when any issue is found.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable


SCAN_GLOBS = ("**/*.md", "**/*.txt", "**/*.adoc", "**/*.rst")
DEFAULT_ROOTS = ("docs", "runbooks", "compliance", ".")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Data Export Service runbooks/documentation for common gaps.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory to scan (default: scans docs/, runbooks/, compliance/, current dir).",
    )
    return parser.parse_args()


def candidate_roots(arg: str | None) -> list[Path]:
    if arg:
        return [Path(arg)]
    found: list[Path] = []
    for name in DEFAULT_ROOTS:
        path = Path(name)
        if path.exists() and path.is_dir():
            found.append(path)
    return found or [Path(".")]


def iter_doc_files(roots: Iterable[Path]) -> Iterable[Path]:
    seen: set[Path] = set()
    for root in roots:
        for pattern in SCAN_GLOBS:
            for path in root.glob(pattern):
                if path in seen or not path.is_file():
                    continue
                # skip irrelevant trees
                parts = set(path.parts)
                if {"node_modules", ".git", "vendor", "__pycache__"} & parts:
                    continue
                seen.add(path)
                yield path


# ---------- pattern matchers ----------

DATA_EXPORT_MENTION = re.compile(
    r"\b(data\s*export\s*service|weekly\s*export|monthly\s*export|setup\s*[->/–]\s*data\s*export)\b",
    re.IGNORECASE,
)
HOUR_48_MENTION = re.compile(r"\b48[-\s]?hour|forty[-\s]?eight\s*hour\b", re.IGNORECASE)

BACKUP_CLAIM = re.compile(
    r"\b(backup\s*strategy|our\s*backup|nightly\s*backup|weekly\s*backup|backup\s*plan|disaster\s*recovery\s*backup)\b",
    re.IGNORECASE,
)
RESTORE_GAP_ACK = re.compile(
    r"\b(no\s*restore|cannot\s*restore|evidence\s*archive|backup\s*and\s*restore\s*\(?separate|managed\s*backup\s*product)\b",
    re.IGNORECASE,
)

BIG_OBJECT_GAP_ACK = re.compile(
    r"\b(big\s*object|external\s*object|metadata\s*excluded|metadata\s*api\s*\(?separately|skipped\s*by\s*data\s*export)\b",
    re.IGNORECASE,
)

BINARY_INCLUDE = re.compile(
    r"\b(include\s*(?:all\s*)?(?:images|documents|attachments|salesforce\s*files|chatter\s*files|binary))\b",
    re.IGNORECASE,
)
BINARY_JUSTIFY = re.compile(
    r"\b(legal\s*hold|discovery|legal\s*request|content\s*replication|specific\s*consumer\s*requirement|file\s*retention\s*regulation)\b",
    re.IGNORECASE,
)

API_CLAIM = re.compile(
    r"\b(sf\s+data\s+export\s+run|/dataExports?/|DataExport(?:Service)?(?:Client|Api)|trigger.{0,30}via.{0,30}(rest|cli|sfdx|api))\b",
    re.IGNORECASE,
)


def check_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rel = path.as_posix()
    issues: list[str] = []

    if not DATA_EXPORT_MENTION.search(text):
        return issues  # file isn't about Data Export; skip

    if not HOUR_48_MENTION.search(text):
        issues.append(
            f"{rel}: mentions Data Export but does not mention the 48-hour download window. "
            "The window must be in any operational doc."
        )

    if BACKUP_CLAIM.search(text) and not RESTORE_GAP_ACK.search(text):
        issues.append(
            f"{rel}: calls this a 'backup' without acknowledging the no-restore gap. "
            "Must reference 'evidence archive', 'no restore', or 'Backup and Restore (separate paid product)'."
        )

    if not BIG_OBJECT_GAP_ACK.search(text):
        issues.append(
            f"{rel}: does not acknowledge Big Object / External Object / metadata exclusions. "
            "These are silently skipped by Data Export."
        )

    if BINARY_INCLUDE.search(text) and not BINARY_JUSTIFY.search(text):
        issues.append(
            f"{rel}: recommends including binary content without naming a consumer requirement "
            "(legal hold, discovery, file replication). Default binary checkboxes to OFF."
        )

    if API_CLAIM.search(text):
        issues.append(
            f"{rel}: claims Data Export can be triggered via API/CLI. The service is UI-only — "
            "use Bulk API 2.0 for programmatic extracts."
        )

    return issues


def main() -> int:
    args = parse_args()
    roots = candidate_roots(args.manifest_dir)
    files = list(iter_doc_files(roots))

    if not files:
        print(f"No documentation files found under {[str(r) for r in roots]}.")
        return 0

    relevant = 0
    issues: list[str] = []
    for path in files:
        text_has_export = DATA_EXPORT_MENTION.search(
            path.read_text(encoding="utf-8", errors="replace")
        )
        if text_has_export:
            relevant += 1
        issues.extend(check_file(path))

    if not relevant:
        print(f"OK: scanned {len(files)} files; none mention Data Export Service.")
        return 0

    if not issues:
        print(f"OK: {relevant} Data-Export-related file(s) scanned, no issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
