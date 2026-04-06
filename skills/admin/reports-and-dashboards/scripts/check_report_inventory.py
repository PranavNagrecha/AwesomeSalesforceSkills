#!/usr/bin/env python3
"""Audit report and dashboard inventory exports for governance risks."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path


CSV_SUFFIX = ".csv"
METADATA_SUFFIXES = (".dashboard-meta.xml", ".report-meta.xml")
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def child_text(element: ET.Element, child_name: str) -> str:
    for child in element:
        if local_name(child.tag) == child_name:
            return (child.text or "").strip()
    return ""


def parse_date(value: str) -> date | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    formats = ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y", "%m/%d/%Y %H:%M")
    for candidate in formats:
        try:
            return datetime.strptime(cleaned, candidate).date()
        except ValueError:
            continue
    return None


def iter_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            for candidate in path.rglob("*"):
                if candidate.is_file() and (
                    candidate.name.endswith(CSV_SUFFIX)
                    or candidate.name.endswith(METADATA_SUFFIXES)
                ):
                    files.append(candidate)
        elif path.is_file() and (
            path.name.endswith(CSV_SUFFIX) or path.name.endswith(METADATA_SUFFIXES)
        ):
            files.append(path)
    return sorted(set(files))


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(finding) for finding in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


def lookup(row: dict[str, str], *candidates: str) -> str:
    normalized = {key.strip().lower(): value for key, value in row.items()}
    for candidate in candidates:
        value = normalized.get(candidate.lower())
        if value:
            return value
    return ""


def audit_csv(path: Path) -> list[str]:
    findings: list[str] = []
    today = date.today()

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            folder = lookup(row, "folder", "folder name", "report folder", "dashboard folder")
            item_type = lookup(row, "type", "item type").lower()
            name = lookup(row, "name", "report name", "dashboard name") or "<unnamed item>"
            running_user = lookup(row, "running user", "dashboard running user")

            if "private" in folder.lower():
                findings.append(f"MEDIUM {path}::{name}: item is in a private folder `{folder}`")

            if "dashboard" in item_type and running_user and "logged" not in running_user.lower():
                findings.append(
                    f"MEDIUM {path}::{name}: dashboard runs as specific user `{running_user}`"
                )

            last_run = parse_date(lookup(row, "last run date", "last run"))
            last_viewed = parse_date(lookup(row, "last viewed date", "last viewed"))
            last_modified = parse_date(lookup(row, "last modified date", "last modified"))

            if "dashboard" in item_type and last_viewed and (today - last_viewed).days > 60:
                findings.append(
                    f"REVIEW {path}::{name}: dashboard not viewed in {(today - last_viewed).days} days"
                )

            if "report" in item_type:
                if last_run and (today - last_run).days > 90:
                    findings.append(
                        f"REVIEW {path}::{name}: report not run in {(today - last_run).days} days"
                    )
                if last_modified and (today - last_modified).days > 180:
                    findings.append(
                        f"REVIEW {path}::{name}: report not modified in {(today - last_modified).days} days"
                    )

    return findings


def audit_metadata(path: Path) -> list[str]:
    findings: list[str] = []
    if "private" in str(path).lower():
        findings.append(f"MEDIUM {path}: metadata is stored under a private folder path")

    if path.name.endswith(".dashboard-meta.xml"):
        root = ET.parse(path).getroot()
        running_user = child_text(root, "runningUser")
        if running_user:
            findings.append(
                f"MEDIUM {path}: dashboard runs as specific user `{running_user}`"
            )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan report/dashboard inventory exports or metadata for governance risks."
    )
    parser.add_argument("paths", nargs="+", help="CSV exports, metadata files, or directories")
    args = parser.parse_args()

    files = iter_files([Path(value) for value in args.paths])
    if not files:
        return emit_result(
            ["HIGH no CSV exports or report/dashboard metadata files found"],
            "Scanned 0 report/dashboard inventory file(s); no files matched the provided paths.",
        )

    findings: list[str] = []
    for path in files:
        if path.name.endswith(CSV_SUFFIX):
            findings.extend(audit_csv(path))
        else:
            findings.extend(audit_metadata(path))

    summary = f"Scanned {len(files)} report/dashboard inventory file(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
