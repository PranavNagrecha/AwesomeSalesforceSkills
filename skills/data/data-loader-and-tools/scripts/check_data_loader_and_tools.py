#!/usr/bin/env python3
"""
check_data_loader_and_tools.py

Skill-local checker for data-loader-and-tools.
Scans Data Loader configuration files and permission metadata exports for
common security and configuration mistakes.

Usage:
    python3 check_data_loader_and_tools.py [--conf path/to/process-conf.xml]
                                            [--perms path/to/permissions.csv]
                                            [--dir path/to/scan/dir]

All dependencies are stdlib only.
"""

import argparse
import csv
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Findings collector
# ---------------------------------------------------------------------------

findings: list[dict] = []


def add_finding(severity: str, file: str, message: str) -> None:
    findings.append({"severity": severity, "file": file, "message": message})


# ---------------------------------------------------------------------------
# process-conf.xml checks
# ---------------------------------------------------------------------------

_PLAINTEXT_PASSWORD_PATTERN = re.compile(
    r'<entry\s+key="[^"]*(?:password|passwd|pwd)[^"]*"\s+value="([^"]{1,})"',
    re.IGNORECASE,
)
_ENCRYPTED_MARKER = re.compile(r"^[A-Za-z0-9+/=]{20,}$")

_USERNAME_PATTERN = re.compile(
    r'<entry\s+key="[^"]*(?:username|user\.name|sfdc\.username)[^"]*"\s+value="([^"]+)"',
    re.IGNORECASE,
)


def check_process_conf(conf_path: str) -> None:
    """Check process-conf.xml for plaintext passwords and hardcoded usernames."""
    path = Path(conf_path)
    if not path.exists():
        add_finding("ERROR", conf_path, "File not found.")
        return

    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        add_finding("ERROR", conf_path, f"XML parse error: {exc}")
        return

    raw_text = path.read_text(encoding="utf-8", errors="replace")

    # Check for plaintext passwords
    for match in _PLAINTEXT_PASSWORD_PATTERN.finditer(raw_text):
        value = match.group(1)
        if not _ENCRYPTED_MARKER.match(value):
            add_finding(
                "HIGH",
                conf_path,
                f"Possible plaintext password detected in config entry "
                f"(value starts with: {value[:6]}...). "
                "Use encrypt.sh/encrypt.bat or OAuth JWT instead.",
            )

    # Check for hardcoded usernames (emails in config are a signal)
    email_re = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
    for match in _USERNAME_PATTERN.finditer(raw_text):
        value = match.group(1)
        if email_re.match(value):
            add_finding(
                "MEDIUM",
                conf_path,
                f"Hardcoded username ('{value}') found in config. "
                "Use environment variables or a secrets manager for CI/headless runs.",
            )

    # Warn if sfdc.useBulkApi2 is not set (defaults to v1 for older installs)
    if "sfdc.useBulkApi2" not in raw_text and "bulkApi2" not in raw_text:
        add_finding(
            "INFO",
            conf_path,
            "sfdc.useBulkApi2 not explicitly set. Confirm Bulk API 2.0 is enabled "
            "for large loads (recommended for Data Loader v45+).",
        )


# ---------------------------------------------------------------------------
# Permission set / profile CSV checks (exported from org)
# ---------------------------------------------------------------------------

_HARD_DELETE_PERMISSION = "PermissionsHardDelete"
_BROAD_PROFILE_KEYWORDS = [
    "system administrator",
    "standard user",
    "read only",
    "solution manager",
    "contract manager",
    "marketing user",
    "partner community",
    "customer community",
]


def check_permissions_csv(perms_path: str) -> None:
    """
    Check a CSV export of Profile or PermissionSet records for broad
    BulkApiHardDelete grants.

    Expected columns (case-insensitive): Name, PermissionsHardDelete
    Compatible with SOQL export:
        SELECT Name, PermissionsHardDelete FROM PermissionSet
        SELECT Name, PermissionsHardDelete FROM Profile
    """
    path = Path(perms_path)
    if not path.exists():
        add_finding("ERROR", perms_path, "File not found.")
        return

    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                add_finding("ERROR", perms_path, "CSV appears empty or has no header row.")
                return

            # Normalise column names for case-insensitive lookup
            col_map = {c.lower(): c for c in reader.fieldnames}
            name_col = col_map.get("name")
            perm_col = next(
                (col_map[k] for k in col_map if "harddelete" in k.replace(" ", "").lower()),
                None,
            )

            if not name_col or not perm_col:
                add_finding(
                    "INFO",
                    perms_path,
                    f"Could not find expected columns (Name, PermissionsHardDelete). "
                    f"Found: {list(reader.fieldnames)}. Skipping permission checks.",
                )
                return

            for row in reader:
                record_name = row.get(name_col, "").strip()
                perm_value = row.get(perm_col, "").strip().lower()
                if perm_value in ("true", "1", "yes"):
                    is_broad = any(
                        kw in record_name.lower() for kw in _BROAD_PROFILE_KEYWORDS
                    )
                    severity = "HIGH" if is_broad else "MEDIUM"
                    add_finding(
                        severity,
                        perms_path,
                        f"BulkApiHardDelete (PermissionsHardDelete) is enabled on "
                        f"'{record_name}'. "
                        + (
                            "This is a broad profile/permission set — review whether "
                            "this grant is intentional."
                            if is_broad
                            else "Confirm this is intentional and follows least-privilege."
                        ),
                    )
    except Exception as exc:
        add_finding("ERROR", perms_path, f"Failed to parse CSV: {exc}")


# ---------------------------------------------------------------------------
# Directory scan
# ---------------------------------------------------------------------------


def scan_directory(dir_path: str) -> None:
    """Recursively find and check process-conf.xml files under dir_path."""
    base = Path(dir_path)
    if not base.is_dir():
        add_finding("ERROR", dir_path, "Directory not found or not a directory.")
        return

    conf_files = list(base.rglob("process-conf.xml"))
    if not conf_files:
        add_finding("INFO", dir_path, "No process-conf.xml files found under this directory.")
        return

    for conf in conf_files:
        check_process_conf(str(conf))


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

_SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "INFO": 2, "ERROR": -1}


def print_report() -> int:
    """Print findings and return exit code (1 if any HIGH/ERROR, else 0)."""
    if not findings:
        print("OK — no issues found.")
        return 0

    sorted_findings = sorted(findings, key=lambda f: _SEVERITY_ORDER.get(f["severity"], 99))

    has_critical = False
    for f in sorted_findings:
        prefix = f"[{f['severity']}]"
        print(f"{prefix} {f['file']}")
        print(f"       {f['message']}")
        print()
        if f["severity"] in ("HIGH", "ERROR"):
            has_critical = True

    print(f"Total findings: {len(findings)}")
    return 1 if has_critical else 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Data Loader configuration and permission exports for security issues."
    )
    parser.add_argument(
        "--conf",
        metavar="PATH",
        help="Path to a process-conf.xml file to check.",
    )
    parser.add_argument(
        "--perms",
        metavar="PATH",
        help="Path to a CSV export of Profile or PermissionSet records to check "
             "for broad BulkApiHardDelete grants.",
    )
    parser.add_argument(
        "--dir",
        metavar="PATH",
        help="Directory to scan recursively for process-conf.xml files.",
    )
    args = parser.parse_args()

    if not any([args.conf, args.perms, args.dir]):
        parser.print_help()
        print("\nError: at least one of --conf, --perms, or --dir is required.")
        return 2

    if args.conf:
        check_process_conf(args.conf)
    if args.perms:
        check_permissions_csv(args.perms)
    if args.dir:
        scan_directory(args.dir)

    return print_report()


if __name__ == "__main__":
    sys.exit(main())
