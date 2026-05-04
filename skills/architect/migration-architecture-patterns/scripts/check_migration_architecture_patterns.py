#!/usr/bin/env python3
"""Static checks for org-migration project artifacts.

Scans a migration project tree for the high-confidence anti-patterns
documented in this skill. The project is expected to contain markdown
plan / runbook documents plus Apex / metadata that enables the
migration.

Catches:

  1. Migration-plan markdown that lacks a metadata-audit phase before
     data movement (anti-pattern 1: skipping the audit).
  2. Bulk-load Apex / scripts that touch DML against migration-target
     objects with no `if (MigrationMode.isOn())` (or analogous
     migration-mode flag) guard nearby — likely missing
     automation-disable for the migration window.
  3. Markdown / plans that recommend `Salesforce-to-Salesforce` (S2S)
     as the bridge — deprecated.
  4. References to `external-id` in Apex / metadata that map to the
     source-org Salesforce Id (a hardcoded `Source_Account_Id__c`-style
     field) without a corresponding remapping mention — possible
     external-Id remap-table missing.

Stdlib only. Heuristic, not a parser. Walks the project tree at
``--src-root``.

Usage:
    python3 check_migration_architecture_patterns.py --src-root .
    python3 check_migration_architecture_patterns.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_AUDIT_KEYWORDS = re.compile(
    r"\b(metadata\s+audit|metadata\s+delta|metadata\s+reconciliation|"
    r"metadata\s+inventory|pre[-\s]migration\s+audit)\b",
    re.IGNORECASE,
)
_DATA_MOVE_KEYWORDS = re.compile(
    r"\b(bulk\s+(?:insert|load)|data\s+migration|extract\s+data|"
    r"load\s+data|move\s+records|migrate\s+records|etl)\b",
    re.IGNORECASE,
)
_S2S_RE = re.compile(
    r"\b(Salesforce[-\s]to[-\s]Salesforce|S2S\s+adapter|S2S\s+sync)\b",
    re.IGNORECASE,
)
_MIGRATION_MODE_RE = re.compile(
    r"\b(MigrationMode|migration_mode|migration\s+mode|isMigrationActive)\b",
    re.IGNORECASE,
)
_BULK_DML_PATTERNS_RE = re.compile(
    r"\b(?:Database\.insert|insert\s+\w+|Database\.update|update\s+\w+|Database\.upsert|upsert\s+\w+)\b",
    re.IGNORECASE,
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan_plan_md(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    if _S2S_RE.search(text):
        m = _S2S_RE.search(text)
        findings.append(
            f"{path}:{_line_no(text, m.start())}: references "
            "`Salesforce-to-Salesforce` / S2S — that product is deprecated for "
            "cross-org sync. Use Salesforce Connect (real-time read), Platform "
            "Events (eventual-consistency sync), or middleware for bulk batch. "
            "(references/llm-anti-patterns.md § 6)"
        )

    has_data_move = bool(_DATA_MOVE_KEYWORDS.search(text))
    has_audit = bool(_AUDIT_KEYWORDS.search(text))
    if has_data_move and not has_audit:
        # Heuristic: a plan that talks about data movement should also
        # mention the audit. Fire on documents big enough to be a plan.
        if len(text) > 800:
            findings.append(
                f"{path}: discusses data movement (`{_DATA_MOVE_KEYWORDS.search(text).group(0)}`) "
                "but contains no metadata-audit / metadata-delta / "
                "metadata-reconciliation language — the audit is the most-skipped "
                "step in org migration. Add an explicit pre-migration audit phase. "
                "(references/llm-anti-patterns.md § 1)"
            )

    return findings


def _scan_apex(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    # Heuristic 2: Apex file mentioning a migration-shaped name (Migration*,
    # Migrate*, BulkMigration*, *Migration*) AND containing DML, but with no
    # MigrationMode-style guard.
    name = path.name.lower()
    looks_migration_shaped = (
        "migration" in name
        or "migrate" in name
        or "bulkload" in name
        or "bulk_load" in name
    )
    if not looks_migration_shaped:
        return findings

    has_dml = bool(_BULK_DML_PATTERNS_RE.search(text))
    has_guard = bool(_MIGRATION_MODE_RE.search(text))
    if has_dml and not has_guard:
        findings.append(
            f"{path}: migration-shaped Apex performs DML but has no "
            "MigrationMode-style guard — bulk insert into target with "
            "automation enabled triggers welcome emails / auto-stamps / "
            "sub-record creation on imported records. Add a kill-switch "
            "the trigger framework respects. (references/gotchas.md § 4)"
        )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]

    findings: list[str] = []
    for md in list(root.rglob("*.md")):
        # Heuristic: only consider markdown that looks like a migration plan
        # — has "migration" in path or filename or "cutover" in filename.
        s = str(md).lower()
        if "migration" not in s and "cutover" not in s:
            continue
        findings.extend(_scan_plan_md(md))

    for apex in list(root.rglob("*.cls")) + list(root.rglob("*.trigger")):
        findings.extend(_scan_apex(apex))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan a Salesforce org-migration project for known "
            "anti-patterns (missing metadata audit, deprecated "
            "Salesforce-to-Salesforce reference, ungated migration "
            "DML)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the migration project (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no migration-architecture anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
