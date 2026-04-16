#!/usr/bin/env python3
"""Checker script for Bulk API 2.0 integration patterns skill.

Scans Python, JavaScript, and TypeScript sources under a project directory for
common Bulk API 2.0 orchestration mistakes described in SKILL.md and references/.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_bulk_api_2_patterns.py [--help]
    python3 check_bulk_api_2_patterns.py --manifest-dir path/to/repo
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan integration source files for Bulk API 2.0 anti-patterns: "
            "missing UploadComplete, unsafe query pagination, and unconditional "
            "JobComplete success handling."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan (default: current directory).",
    )
    return parser.parse_args()


def _find_sources(root: Path) -> list[Path]:
    exts = {".py", ".js", ".ts", ".tsx", ".mjs", ".cjs"}
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in exts:
            # Skip huge dependency trees if present
            parts = set(path.parts)
            if "node_modules" in parts or ".venv" in parts or "venv" in parts:
                continue
            files.append(path)
    return files


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _mentions_ingest_job(text: str) -> bool:
    lowered = text.lower()
    return "jobs/ingest" in lowered or "/ingest/" in lowered and "job" in lowered


def _mentions_multipart_ingest(text: str) -> bool:
    t = text.lower()
    return "multipart/form-data" in t and "ingest" in t


def _mentions_upload_complete(text: str) -> bool:
    t = text.replace(" ", "")
    if "UploadComplete" in t:
        return True
    if '"state":"uploadcomplete"' in t.lower():
        return True
    if "'state':'uploadcomplete'" in t.lower():
        return True
    return False


def _mentions_put_upload(text: str) -> bool:
    if re.search(r"\brequests\.put\s*\(", text) or re.search(r"\.put\s*\(\s*['\"]", text):
        return True
    if re.search(r"-X\s+PUT", text) or re.search(r"method\s*=\s*['\"]PUT['\"]", text, re.I):
        return True
    return False


def check_missing_upload_complete(root: Path) -> list[str]:
    """Flag files that reference ingest jobs and PUT uploads but never UploadComplete."""
    issues: list[str] = []
    for path in _find_sources(root):
        text = _read_text(path)
        if not _mentions_ingest_job(text):
            continue
        if _mentions_multipart_ingest(text):
            continue
        if not _mentions_put_upload(text):
            continue
        if _mentions_upload_complete(text):
            continue
        issues.append(
            f"{path}: Bulk API 2.0 ingest upload detected without 'UploadComplete' in the same file. "
            "Non-multipart jobs require PATCH {\"state\":\"UploadComplete\"} after uploads or "
            "processing never starts (see Bulk API 2.0 Upload Complete)."
        )
    return issues


def check_query_pagination_without_locator(text: str, path: Path) -> list[str]:
    """Warn when query job results are fetched without locator handling."""
    issues: list[str] = []
    lowered = text.lower()
    if "jobs/query" not in lowered and "/query/" not in lowered:
        return issues
    if "results" not in lowered:
        return issues
    if "sforce-locator" in lowered or "sforce_locator" in lowered or "locator" in lowered:
        return issues
    issues.append(
        f"{path}: Query job results appear to be accessed without locator handling. "
        "Bulk API 2.0 requires following the Sforce-Locator header until the value is 'null'."
    )
    return issues


def check_jobcomplete_without_failure_signals(text: str, path: Path) -> list[str]:
    """Flag naive JobComplete checks that ignore failure metrics."""
    issues: list[str] = []
    if "JobComplete" not in text:
        return issues
    if "numberRecordsFailed" in text or "failedResults" in text:
        return issues
    if "jobs/ingest" not in text.lower() and "ingest" not in text.lower():
        return issues
    # Single-state string compare is a common LLM smell
    if re.search(r"['\"]JobComplete['\"]", text) and "==" in text:
        issues.append(
            f"{path}: 'JobComplete' branch without numberRecordsFailed or failedResults handling. "
            "JobComplete means processing finished, not that every row succeeded."
        )
    return issues


def check_bulk_api_2_patterns(manifest_dir: Path) -> list[str]:
    """Run all checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Directory not found: {manifest_dir}")
        return issues

    issues.extend(check_missing_upload_complete(manifest_dir))

    for path in _find_sources(manifest_dir):
        text = _read_text(path)
        issues.extend(check_query_pagination_without_locator(text, path))
        issues.extend(check_jobcomplete_without_failure_signals(text, path))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_bulk_api_2_patterns(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
