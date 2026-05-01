#!/usr/bin/env python3
"""Checker script for Data Cloud Zero Copy Federation skill.

Heuristically scans a Salesforce DX-style metadata tree (force-app/) plus
associated config / documentation to surface federation anti-patterns:

  - Cross-connector segment / CI joins that cannot push down.
  - Federated DLOs likely participating in identity resolution without a
    materialized acceleration cache on the matching keys.
  - Unsupported source platforms claimed in config / docs (Postgres,
    MySQL, Oracle, MongoDB, generic JDBC) framed as Zero Copy /
    federation targets.
  - Federation credentials referenced inline in code (a rotation hazard).
  - Documents / code asserting federation is "free" / "no cost" without
    a paired source-warehouse cost note.

Stdlib only.

Usage:
    python3 check_data_cloud_zero_copy_federation.py [--manifest-dir path]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

SUPPORTED_PLATFORMS = {"snowflake", "databricks", "bigquery", "redshift"}
UNSUPPORTED_FEDERATION_PLATFORMS = {
    "postgres", "postgresql", "mysql", "oracle", "mongodb",
    "mssql", "sqlserver", "mariadb", "db2", "sqlite",
}
FEDERATION_KEYWORDS = ("zero copy", "zero-copy", "federation", "federated", "lakehouse")
IR_KEYWORDS = ("identity resolution", "match rule", "individual dmo", "unifiedindividual", "matchrule")
ACCELERATION_KEYWORDS = ("acceleration cache", "query acceleration", "materialize", "accelerated")
CRED_PATTERNS = [
    re.compile(r"(snowflake|databricks|bigquery|redshift).{0,40}(token|key|password|secret)\s*[:=]\s*['\"][^'\"]{8,}", re.I),
    re.compile(r"deltaSharing\.bearerToken\s*[:=]\s*['\"][^'\"]+", re.I),
    re.compile(r"service[_-]?account[_-]?key\s*[:=]\s*['\"][^'\"]+", re.I),
]
TEXT_EXTS = {".md", ".txt", ".json", ".yaml", ".yml", ".xml", ".cls", ".py", ".js", ".ts", ".sql"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Data Cloud Zero Copy Federation configuration and code for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata or repo (default: current directory).",
    )
    return parser.parse_args()


def iter_text_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_EXTS:
            continue
        try:
            if path.stat().st_size > 2_000_000:
                continue
        except OSError:
            continue
        yield path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def mentions_federation(text_lower: str) -> bool:
    return any(k in text_lower for k in FEDERATION_KEYWORDS)


def mentions_ir(text_lower: str) -> bool:
    return any(k in text_lower for k in IR_KEYWORDS)


def mentions_acceleration(text_lower: str) -> bool:
    return any(k in text_lower for k in ACCELERATION_KEYWORDS)


def find_platforms(text_lower: str) -> set[str]:
    return {p for p in SUPPORTED_PLATFORMS | UNSUPPORTED_FEDERATION_PLATFORMS if p in text_lower}


def check_cross_connector_join(path: Path, text_lower: str, issues: list[str]) -> None:
    if not mentions_federation(text_lower):
        return
    platforms = find_platforms(text_lower) & SUPPORTED_PLATFORMS
    if len(platforms) >= 2 and ("join" in text_lower or "segment" in text_lower):
        issues.append(
            f"{path}: References federation across {sorted(platforms)} together with "
            "join/segment language. Cross-connector joins cannot push down to source warehouses; "
            "pre-join at source or physically ingest one side."
        )


def check_unsupported_platforms(path: Path, text_lower: str, issues: list[str]) -> None:
    if not mentions_federation(text_lower):
        return
    bad = find_platforms(text_lower) & UNSUPPORTED_FEDERATION_PLATFORMS
    if bad:
        issues.append(
            f"{path}: Names unsupported source platform(s) {sorted(bad)} in a federation/zero-copy "
            "context. Only Snowflake, Databricks, BigQuery, and Redshift are supported as Lakehouse "
            "Federation targets — others require physical ingestion."
        )


def check_ir_without_acceleration(path: Path, text_lower: str, issues: list[str]) -> None:
    if not mentions_federation(text_lower):
        return
    if mentions_ir(text_lower) and not mentions_acceleration(text_lower):
        issues.append(
            f"{path}: Federation + identity-resolution language present without any acceleration "
            "cache / materialization mention. Identity resolution against bare federation degrades "
            "silently — materialize matching keys via a query-acceleration cache."
        )


def check_inline_credentials(path: Path, text: str, issues: list[str]) -> None:
    for pat in CRED_PATTERNS:
        if pat.search(text):
            issues.append(
                f"{path}: Possible inline federation credential / token. Federation auth must live "
                "in a Named Credential or external secret store, never in source — auth rotation "
                "originates at the source warehouse and inline values silently expire."
            )
            return


def check_free_claim(path: Path, text_lower: str, issues: list[str]) -> None:
    if not mentions_federation(text_lower):
        return
    free_tokens = ("no cost", "no-cost", "free of charge", "no storage cost", "zero cost", "no extra cost")
    if any(t in text_lower for t in free_tokens):
        if "source warehouse" not in text_lower and "credit" not in text_lower and "compute cost" not in text_lower:
            issues.append(
                f"{path}: Frames federation as cost-free without naming source-warehouse compute / "
                "credit cost. Federation bills queries on the source side; cost ceilings must be modeled."
            )


def check_data_cloud_zero_copy_federation(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    for path in iter_text_files(manifest_dir):
        text = read_text(path)
        if not text:
            continue
        text_lower = text.lower()
        check_cross_connector_join(path, text_lower, issues)
        check_unsupported_platforms(path, text_lower, issues)
        check_ir_without_acceleration(path, text_lower, issues)
        check_inline_credentials(path, text, issues)
        check_free_claim(path, text_lower, issues)

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_data_cloud_zero_copy_federation(manifest_dir)

    if not issues:
        print("No Data Cloud Zero Copy Federation issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
