#!/usr/bin/env python3
"""Static checks for Salesforce backup-and-restore anti-patterns.

Scans Apex source and Salesforce metadata XML for high-risk patterns
that indicate the backup-and-restore strategy is incomplete or that a
destructive operation is missing the safety rails this skill describes.

Anti-patterns detected:

  1. `Database.emptyRecycleBin(...)` calls in Apex — hard-purges
     records past the 15-day soft-delete window. Should never appear
     without a comment referencing the backup runbook.
  2. Bulk API hard-delete in Apex — `Database.delete(records, false)`
     followed by `emptyRecycleBin`, or `BulkConnection.createJob`
     with `operation` set to `hardDelete`.
  3. `[SELECT ... FROM Object]` snapshots used as "backup" without
     `ALL ROWS` — silently excludes soft-deleted rows.
  4. Permission set / profile XML granting `ModifyAllData` without
     guard — blast-radius indicator for restore-need scenarios.

Stdlib only.

Usage:
    python3 check_salesforce_backup_and_restore.py --src-root .
    python3 check_salesforce_backup_and_restore.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 1. emptyRecycleBin call.
_EMPTY_RECYCLE_BIN_RE = re.compile(
    r"\bDatabase\.emptyRecycleBin\s*\(",
    re.IGNORECASE,
)

# 2. Bulk hard delete via Apex DML option (placeholder — most are JSON
#    not Apex). Detect literal `hardDelete` in Apex string content.
_HARD_DELETE_RE = re.compile(
    r"['\"]hardDelete['\"]",
)

# 3. SOQL snapshot without ALL ROWS — heuristic looks for
#    `SELECT ... FROM <Sobj>` inside an Apex file that contains the
#    word `backup` or `snapshot` in a comment, but no `ALL ROWS`.
_SOQL_RE = re.compile(
    r"\[\s*SELECT[^\]]+FROM\s+\w+[^\]]*\]",
    re.IGNORECASE | re.DOTALL,
)
_ALL_ROWS_RE = re.compile(r"\bALL\s+ROWS\b", re.IGNORECASE)
_BACKUP_HINT_RE = re.compile(r"\b(backup|snapshot|export)\b", re.IGNORECASE)

# 4. Permission XML granting ModifyAllData
_MODIFY_ALL_DATA_RE = re.compile(
    r"<name>ModifyAllData</name>\s*<enabled>true</enabled>",
    re.IGNORECASE | re.DOTALL,
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan_apex(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    for m in _EMPTY_RECYCLE_BIN_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: Database.emptyRecycleBin(...) "
            "is a hard-purge that bypasses the 15-day soft-delete window. "
            "Records cannot be recovered from Recycle Bin afterwards. Confirm "
            "a backup snapshot exists before this runs "
            "(references/llm-anti-patterns.md § 1, gotchas.md § 2)."
        )

    for m in _HARD_DELETE_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: literal 'hardDelete' detected — "
            "Bulk API hard delete skips Recycle Bin entirely. Confirm a backup "
            "exists for the records being deleted (gotchas.md § 2)."
        )

    if _BACKUP_HINT_RE.search(text):
        for m in _SOQL_RE.finditer(text):
            soql = m.group(0)
            if not _ALL_ROWS_RE.search(soql):
                findings.append(
                    f"{path}:{_line_no(text, m.start())}: SOQL in a file "
                    "mentioning backup/snapshot/export but without `ALL ROWS` "
                    "silently excludes soft-deleted rows. Use `ALL ROWS` for "
                    "complete snapshots (llm-anti-patterns.md § 7, gotchas.md "
                    "§ 7)."
                )

    return findings


def _scan_permissionset(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    for m in _MODIFY_ALL_DATA_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: grants ModifyAllData=true. "
            "Users with this permission can mass-delete production records — "
            "ensure backup coverage is in place and restore drills exercise "
            "this scenario (well-architected.md § Security)."
        )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]
    findings: list[str] = []
    for apex in list(root.rglob("*.cls")) + list(root.rglob("*.trigger")):
        findings.extend(_scan_apex(apex))
    for ps in list(root.rglob("*.permissionset-meta.xml")) + list(
        root.rglob("*.profile-meta.xml")
    ):
        findings.extend(_scan_permissionset(ps))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Apex source and Salesforce metadata XML for backup-and-"
            "restore anti-patterns: emptyRecycleBin calls, hard-delete "
            "literals, snapshot SOQL missing ALL ROWS, and permission grants "
            "with high blast radius."
        ),
    )
    parser.add_argument(
        "--src-root",
        default=".",
        help="Root of the metadata / Apex source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no backup-and-restore anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
