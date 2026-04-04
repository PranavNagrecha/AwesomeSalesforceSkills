#!/usr/bin/env python3
"""Checker script for Apex Metadata API skill.

Scans Apex (.cls) files for usage of Metadata.Operations or Metadata.DeployCallback
and reports occurrences with file path and line context.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_apex_metadata_api.py [--help]
    python3 check_apex_metadata_api.py --src-dir path/to/force-app
    python3 check_apex_metadata_api.py --src-dir . --warn-only
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


# Patterns that indicate Apex Metadata API usage or common anti-patterns
USAGE_PATTERNS: list[tuple[str, str]] = [
    ("Metadata.Operations", "Apex Metadata API operation call"),
    ("Metadata.DeployCallback", "DeployCallback implementation or reference"),
    ("enqueueDeployment", "enqueueDeployment call"),
    ("Metadata.DeployContainer", "DeployContainer construction"),
    ("Metadata.DeployResult", "DeployResult handling"),
    ("Metadata.CustomField", "CustomField metadata construction"),
    ("Metadata.CustomObject", "CustomObject metadata construction"),
    ("Metadata.CustomLabel", "CustomLabel metadata construction"),
]

ANTI_PATTERN_PATTERNS: list[tuple[str, str]] = [
    (
        "enqueueDeployment(container, null)",
        "ANTI-PATTERN: null callback — deployment results will be silently discarded",
    ),
    (
        "enqueueDeployment(mdContainer, null)",
        "ANTI-PATTERN: null callback — deployment results will be silently discarded",
    ),
    (
        "MetadataService",
        "POSSIBLE CONFUSION: MetadataService is the SOAP API stub pattern, not the Apex Metadata API namespace",
    ),
]


def find_cls_files(src_dir: Path) -> list[Path]:
    """Recursively find all .cls files under src_dir."""
    return sorted(src_dir.rglob("*.cls"))


def scan_file(cls_file: Path, patterns: list[tuple[str, str]]) -> list[dict]:
    """Return a list of match records for each pattern found in the file."""
    matches: list[dict] = []
    try:
        lines = cls_file.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return matches

    for line_num, line in enumerate(lines, start=1):
        for pattern, description in patterns:
            if pattern in line:
                matches.append(
                    {
                        "file": str(cls_file),
                        "line": line_num,
                        "pattern": pattern,
                        "description": description,
                        "content": line.strip(),
                    }
                )
    return matches


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Apex .cls files for Metadata.Operations / Metadata.DeployCallback usage "
            "and flag common Apex Metadata API anti-patterns."
        ),
    )
    parser.add_argument(
        "--src-dir",
        default=".",
        help="Root directory to search for .cls files (default: current directory).",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Exit 0 even when anti-patterns are found (report only).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    src_dir = Path(args.src_dir)

    if not src_dir.exists():
        print(f"ERROR: Source directory not found: {src_dir}")
        return 1

    cls_files = find_cls_files(src_dir)
    if not cls_files:
        print(f"No .cls files found under: {src_dir}")
        return 0

    usage_matches: list[dict] = []
    anti_pattern_matches: list[dict] = []

    for cls_file in cls_files:
        usage_matches.extend(scan_file(cls_file, USAGE_PATTERNS))
        anti_pattern_matches.extend(scan_file(cls_file, ANTI_PATTERN_PATTERNS))

    # Report usage
    if usage_matches:
        print(f"\n=== Apex Metadata API Usage ({len(usage_matches)} occurrences) ===\n")
        for m in usage_matches:
            print(f"  {m['file']}:{m['line']}")
            print(f"    Pattern  : {m['pattern']}")
            print(f"    Meaning  : {m['description']}")
            print(f"    Line     : {m['content']}")
            print()
    else:
        print("\nNo Apex Metadata API usage detected in .cls files.")

    # Report anti-patterns
    if anti_pattern_matches:
        print(f"\n=== Apex Metadata API Anti-Patterns ({len(anti_pattern_matches)} occurrences) ===\n")
        for m in anti_pattern_matches:
            print(f"  {m['file']}:{m['line']}")
            print(f"    Pattern  : {m['pattern']}")
            print(f"    Issue    : {m['description']}")
            print(f"    Line     : {m['content']}")
            print()

        if not args.warn_only:
            print("Anti-patterns detected. Fix before shipping or re-run with --warn-only to suppress exit code.")
            return 1

    print(f"\nScanned {len(cls_files)} .cls file(s). Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
