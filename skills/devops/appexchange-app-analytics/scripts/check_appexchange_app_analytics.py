#!/usr/bin/env python3
"""Checker for AppExchange App Analytics request specs (AppAnalyticsQueryRequest).

Validates JSON request-definition files (like the one produced from
templates/appexchange-app-analytics-template.md) against the documented rules of
the AppAnalyticsQueryRequest object: DataType picklist values, time-window rules
(StartTime/AvailableSince), FileType/FileCompression combinations, PackageIds /
OrganizationIds list constraints, and retention-window sanity. Stdlib only.

A JSON file is treated as a request spec when it is an object (or a list of
objects) containing a "DataType" key, or whose "attributes.type" is
"AppAnalyticsQueryRequest".

Usage:
    python3 check_appexchange_app_analytics.py [--manifest-dir path]

Exit code 0 = no issues, 1 = issues found.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

VALID_DATA_TYPES = {"PackageUsageLog", "PackageUsageSummary", "SubscriberSnapshot"}
LEGACY_DATA_TYPES = {"CustomObjectUsageLog", "CustomObjectUsageSummary"}
VALID_FILE_TYPES = {"csv", "parquet"}
VALID_COMPRESSION = {"csv": {"none", "gzip"}, "parquet": {"snappy", "gzip", "none"}}
KNOWN_FIELDS = {
    "attributes",
    "DataType",
    "StartTime",
    "EndTime",
    "AvailableSince",
    "FileType",
    "FileCompression",
    "PackageIds",
    "OrganizationIds",
}
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
LOG_RETENTION_DAYS = 45  # package usage logs and subscriber snapshots
MAX_ID_LIST_ENTRIES = 16


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check AppAnalyticsQueryRequest request-spec JSON files for the common "
            "mistakes documented in references/gotchas.md and references/llm-anti-patterns.md."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Directory to scan recursively for *.json request specs (default: current directory).",
    )
    return parser.parse_args()


def _parse_dt(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, DATETIME_FORMAT)
    except (TypeError, ValueError):
        return None


def _is_request_spec(obj: object) -> bool:
    if not isinstance(obj, dict):
        return False
    if "DataType" in obj:
        return True
    attrs = obj.get("attributes")
    return isinstance(attrs, dict) and attrs.get("type") == "AppAnalyticsQueryRequest"


def _check_id_list(path: Path, label: str, raw: object, issues: list[str], prefix: str | None) -> None:
    if raw in (None, ""):
        return
    if not isinstance(raw, str):
        issues.append(f"{path}: {label} must be a comma-separated string, got {type(raw).__name__}")
        return
    if " " in raw:
        issues.append(f"{path}: {label} must not contain spaces between IDs")
    ids = [i for i in raw.split(",") if i]
    if len(ids) > MAX_ID_LIST_ENTRIES:
        issues.append(
            f"{path}: {label} has {len(ids)} IDs — the documented maximum is "
            f"{MAX_ID_LIST_ENTRIES} comma-separated IDs per request"
        )
    if prefix:
        for entry in ids:
            if not entry.startswith(prefix):
                issues.append(
                    f"{path}: {label} entry '{entry}' doesn't look like a subscriber "
                    f"package ID (expected key prefix '{prefix}')"
                )


def _check_spec(path: Path, spec: dict, issues: list[str]) -> None:
    for key in spec:
        if key not in KNOWN_FIELDS:
            issues.append(
                f"{path}: unknown field '{key}' — writable request fields are: "
                f"{', '.join(sorted(KNOWN_FIELDS - {'attributes'}))}"
            )

    data_type = spec.get("DataType")
    if data_type in LEGACY_DATA_TYPES:
        issues.append(
            f"{path}: DataType '{data_type}' is the pre-Summer '20 legacy name and works "
            f"only with API v47.0 and earlier — use one of: {', '.join(sorted(VALID_DATA_TYPES))}"
        )
    elif data_type not in VALID_DATA_TYPES:
        issues.append(
            f"{path}: DataType is '{data_type}' — expected one of: "
            f"{', '.join(sorted(VALID_DATA_TYPES))}"
        )

    start_raw = spec.get("StartTime")
    end_raw = spec.get("EndTime")
    since_raw = spec.get("AvailableSince")

    if not start_raw and not since_raw:
        issues.append(
            f"{path}: a query must include StartTime, AvailableSince, or both — this spec has neither"
        )

    parsed: dict[str, datetime | None] = {}
    for label, raw in (("StartTime", start_raw), ("EndTime", end_raw), ("AvailableSince", since_raw)):
        if raw in (None, ""):
            parsed[label] = None
            continue
        dt = _parse_dt(raw) if isinstance(raw, str) else None
        parsed[label] = dt
        if dt is None:
            issues.append(
                f"{path}: {label} '{raw}' is not in the documented format yyyy-MM-ddTHH:mm:ss "
                f"(example: 2026-07-04T00:00:00)"
            )

    start, end, since = parsed["StartTime"], parsed["EndTime"], parsed["AvailableSince"]
    if start and end and end <= start:
        issues.append(f"{path}: EndTime must be after StartTime ({end_raw} <= {start_raw})")
    if since:
        for label, dt, raw in (("StartTime", start, start_raw), ("EndTime", end, end_raw)):
            if dt and since <= dt:
                issues.append(
                    f"{path}: AvailableSince must be later than {label} if specified "
                    f"({since_raw} <= {raw})"
                )

    if data_type in {"PackageUsageLog", "SubscriberSnapshot"} and start:
        utc_now = datetime.now(timezone.utc).replace(tzinfo=None)
        if start < utc_now - timedelta(days=LOG_RETENTION_DAYS):
            issues.append(
                f"{path}: StartTime {start_raw} is more than {LOG_RETENTION_DAYS} days ago — "
                f"package usage logs and subscriber snapshots are retained {LOG_RETENTION_DAYS} "
                f"days, so this window can't be fully served"
            )

    file_type = spec.get("FileType")
    if file_type is not None and file_type not in VALID_FILE_TYPES:
        issues.append(
            f"{path}: FileType '{file_type}' is invalid — valid values: csv (default), parquet"
        )
    compression = spec.get("FileCompression")
    if compression is not None:
        effective_type = file_type if file_type in VALID_FILE_TYPES else "csv"
        allowed = VALID_COMPRESSION[effective_type]
        if compression not in allowed:
            issues.append(
                f"{path}: FileCompression '{compression}' is invalid for FileType "
                f"'{effective_type}' — allowed: {', '.join(sorted(allowed))}"
            )

    _check_id_list(path, "PackageIds", spec.get("PackageIds"), issues, prefix="033")
    _check_id_list(path, "OrganizationIds", spec.get("OrganizationIds"), issues, prefix=None)


def check(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    specs_found = 0
    for json_path in sorted(manifest_dir.rglob("*.json")):
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue  # not a readable/valid JSON file — not ours to police
        candidates = data if isinstance(data, list) else [data]
        for candidate in candidates:
            if _is_request_spec(candidate):
                specs_found += 1
                _check_spec(json_path, candidate, issues)

    if specs_found == 0:
        return [
            f"No AppAnalyticsQueryRequest request specs found under {manifest_dir} — "
            f"nothing to check. (A spec is a JSON object with a 'DataType' key or "
            f"attributes.type = 'AppAnalyticsQueryRequest'.)"
        ]
    return issues


def main() -> int:
    args = parse_args()
    issues = check(Path(args.manifest_dir))
    if not issues:
        print("No issues found.")
        return 0
    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
