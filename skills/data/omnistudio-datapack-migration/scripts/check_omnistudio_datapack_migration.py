#!/usr/bin/env python3
"""Checker script for OmniStudio DataPack Migration skill.

Validates DataPack JSON files and migration scripts for common issues:
- Missing --activate flag in deploy commands
- Version conflict indicators
- Incorrect tool usage (OMA vs DataPack)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omnistudio_datapack_migration.py [--help]
    python3 check_omnistudio_datapack_migration.py --script-file path/to/deploy-script.sh
    python3 check_omnistudio_datapack_migration.py --datapack-file path/to/datapack.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check OmniStudio DataPack migration scripts and packages for common issues.",
    )
    parser.add_argument(
        "--script-file",
        default=None,
        help="Path to a shell script containing DataPack deploy commands.",
    )
    parser.add_argument(
        "--datapack-file",
        default=None,
        help="Path to a DataPack JSON export file.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for DataPack JSON files (default: current directory).",
    )
    return parser.parse_args()


def check_deploy_script(file_path: Path) -> list[str]:
    """Check a shell script for DataPack deployment anti-patterns."""
    issues: list[str] = []

    if not file_path.exists():
        issues.append(f"Script file not found: {file_path}")
        return issues

    content = file_path.read_text(encoding="utf-8")

    # Check for packDeploy or sf omnistudio datapack deploy without --activate
    deploy_lines = [
        line for line in content.splitlines()
        if re.search(r"packDeploy|omnistudio datapack deploy", line, re.IGNORECASE)
        and not line.strip().startswith("#")
    ]
    for line in deploy_lines:
        if "--activate" not in line:
            issues.append(
                f"MISSING --activate flag in deploy command: '{line.strip()}'\n"
                "  packDeploy without --activate creates the component but does NOT change the active version.\n"
                "  The previous active version continues serving traffic."
            )

    # Check for OMA tool being used for org-to-org migration
    if re.search(r"omnistudio.*migration.assistant|oma.*deploy|oma.*migrate", content, re.IGNORECASE):
        issues.append(
            "POSSIBLE incorrect tool: Script references OmniStudio Migration Assistant (OMA). "
            "OMA is for managed-package-to-Standard-Runtime conversion, NOT org-to-org DataPack migrations. "
            "For org-to-org migrations, use sf omnistudio datapack deploy."
        )

    return issues


def check_datapack_json(file_path: Path) -> list[str]:
    """Check a DataPack JSON file for common migration issues."""
    issues: list[str] = []

    if not file_path.exists():
        issues.append(f"DataPack file not found: {file_path}")
        return issues

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        issues.append(f"DataPack JSON is invalid: {e}")
        return issues

    # Check for custom matchingKey overrides (potential duplicate creation risk)
    content_str = json.dumps(data)
    if "matchingKey" in content_str:
        issues.append(
            "WARN: DataPack contains custom matchingKey fields. "
            "Custom matchingKey values (post-VBT v15) override default matching strategy. "
            "If the target org uses different matchingKey settings, import may create duplicate components "
            "instead of updating existing ones. Review matchingKey values before import."
        )

    # Check for environment-specific references
    env_patterns = [
        (r"https?://[a-z0-9-]+\.salesforce\.com", "Salesforce org URL"),
        (r'"NamedCredential":\s*"[^"]{5,}"', "Named Credential reference"),
        (r'"orgId":\s*"00D[a-zA-Z0-9]{12}"', "Org ID"),
    ]
    for pattern, label in env_patterns:
        if re.search(pattern, content_str):
            issues.append(
                f"WARN: DataPack contains a {label} that may be environment-specific. "
                "Verify this value is appropriate for the target org before importing."
            )

    return issues


def scan_for_datapacks(manifest_dir: Path) -> list[str]:
    """Scan a directory for DataPack JSON files and check each."""
    issues: list[str] = []
    datapack_files = list(manifest_dir.rglob("*.json"))
    for dp_file in datapack_files:
        try:
            data = json.loads(dp_file.read_text(encoding="utf-8", errors="ignore"))
            # Heuristic: DataPack JSONs typically have OmniProcess or DataPack keys
            if isinstance(data, dict) and any(
                k in data for k in ["OmniProcess", "DataPack", "dataPacks"]
            ):
                issues.extend(check_datapack_json(dp_file))
        except (json.JSONDecodeError, OSError):
            pass
    return issues


def main() -> int:
    args = parse_args()
    issues: list[str] = []

    if args.script_file:
        issues.extend(check_deploy_script(Path(args.script_file)))

    if args.datapack_file:
        issues.extend(check_datapack_json(Path(args.datapack_file)))

    if not args.script_file and not args.datapack_file:
        # Scan manifest dir for DataPack files
        issues.extend(scan_for_datapacks(Path(args.manifest_dir)))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
