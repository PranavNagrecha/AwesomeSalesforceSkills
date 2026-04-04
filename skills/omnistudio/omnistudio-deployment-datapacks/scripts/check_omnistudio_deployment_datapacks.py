#!/usr/bin/env python3
"""Checker script for OmniStudio Deployment DataPacks skill.

Validates a local DataPack export directory for common issues that cause
import failures or post-import activation problems in the target org.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omnistudio_deployment_datapacks.py [--datapack-dir path/to/datapacks]
    python3 check_omnistudio_deployment_datapacks.py --datapack-dir ./datapacks --verbose
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Regex approximating a Salesforce 15- or 18-character record ID.
# Starts with a 3-char object key prefix (e.g. 001, 00Q, a0B), followed by
# alphanumeric characters totalling 15 or 18 chars overall.
_SFID_PATTERN = re.compile(r'\b([a-zA-Z0-9]{3}[a-zA-Z0-9]{12}|[a-zA-Z0-9]{3}[a-zA-Z0-9]{15})\b')

# Keys that legitimately hold Salesforce IDs as their primary value and should
# be flagged when found embedded in DataPack JSON.
_SUSPICIOUS_ID_KEYS = {
    "id", "Id", "recordId", "RecordId", "lookupId", "relatedId",
    "parentId", "ParentId", "ownerId", "OwnerId",
}

# DataPack type names expected in the JSON.
_KNOWN_DATAPACK_TYPES = {
    "OmniScript", "IntegrationProcedure", "DataRaptor",
    "FlexCard", "OmniProcess", "VlocityCard",
    "Product2", "AttributeAssignmentRule",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a local OmniStudio DataPack export directory for common issues "
            "that cause import failures or post-import activation problems."
        ),
    )
    parser.add_argument(
        "--datapack-dir",
        default="datapacks",
        help="Root directory of the DataPack export (default: ./datapacks).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print informational messages in addition to issues.",
    )
    return parser.parse_args()


def _find_json_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.json"))


def _check_file_is_valid_json(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        with path.open(encoding="utf-8") as fh:
            json.load(fh)
    except json.JSONDecodeError as exc:
        issues.append(f"[{path}] Invalid JSON: {exc}")
    return issues


def _check_datapack_structure(path: Path, data: dict) -> list[str]:
    """Check that the top-level DataPack JSON has expected structural keys."""
    issues: list[str] = []
    if "dataPacks" not in data and "VlocityDataPackType" not in data:
        issues.append(
            f"[{path}] Missing 'dataPacks' or 'VlocityDataPackType' key — "
            "this may not be a valid DataPack file."
        )
    return issues


def _check_embedded_record_ids(path: Path, raw_text: str) -> list[str]:
    """Warn when suspicious Salesforce record IDs are found in the DataPack JSON."""
    issues: list[str] = []
    # Look for patterns like "recordId": "001Xxxxxxxxxxxxxxx"
    # This is a heuristic — not all 15/18-char strings are IDs.
    for key in _SUSPICIOUS_ID_KEYS:
        pattern = re.compile(
            rf'"{re.escape(key)}"\s*:\s*"([a-zA-Z0-9]{{15,18}})"'
        )
        for match in pattern.finditer(raw_text):
            value = match.group(1)
            # Skip obvious non-ID strings (all lowercase, common words, etc.)
            if re.match(r'^[a-z]+$', value):
                continue
            issues.append(
                f"[{path}] Possible org-specific record ID in key '{key}': '{value}' — "
                "verify this is not a source-org ID that will break cross-org import."
            )
    return issues


def _check_activation_flag_hint(path: Path, data: dict) -> list[str]:
    """Remind about activation if the DataPack contains versioned component types."""
    issues: list[str] = []
    versioned_types = {"OmniScript", "IntegrationProcedure", "FlexCard", "OmniProcess"}
    dp_type = data.get("VlocityDataPackType", "")
    if dp_type in versioned_types:
        # Check whether IsActive is present and False in the top-level data records.
        raw = json.dumps(data)
        if '"IsActive": false' in raw or '"IsActive":false' in raw:
            issues.append(
                f"[{path}] Component type '{dp_type}' has IsActive=false. "
                "This DataPack exports an inactive version. "
                "Importing without --activate will leave the component inactive in the target org."
            )
    return issues


def _check_named_credential_references(path: Path, raw_text: str) -> list[str]:
    """Flag Named Credential references so they can be verified across environments."""
    issues: list[str] = []
    pattern = re.compile(r'"namedCredential"\s*:\s*"([^"]+)"', re.IGNORECASE)
    for match in pattern.finditer(raw_text):
        nc_name = match.group(1)
        issues.append(
            f"[{path}] Named Credential reference found: '{nc_name}' — "
            "confirm this credential name exists in the target org or configure an environment override."
        )
    return issues


def check_datapack_dir(datapack_dir: Path, verbose: bool = False) -> list[str]:
    """Return a list of issue strings found in the DataPack export directory."""
    issues: list[str] = []

    if not datapack_dir.exists():
        issues.append(f"DataPack directory not found: {datapack_dir}")
        return issues

    json_files = _find_json_files(datapack_dir)

    if not json_files:
        issues.append(
            f"No JSON files found in '{datapack_dir}'. "
            "Run a DataPack export first or verify the --datapack-dir path."
        )
        return issues

    if verbose:
        print(f"INFO: Found {len(json_files)} JSON file(s) in '{datapack_dir}'.")

    for json_path in json_files:
        # 1. Validate JSON syntax.
        parse_issues = _check_file_is_valid_json(json_path)
        if parse_issues:
            issues.extend(parse_issues)
            continue  # Cannot analyse further if JSON is invalid.

        with json_path.open(encoding="utf-8") as fh:
            raw_text = fh.read()

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            continue  # Already reported above.

        if not isinstance(data, dict):
            continue  # Top-level array or scalar — skip structural checks.

        # 2. Check DataPack structural keys.
        issues.extend(_check_datapack_structure(json_path, data))

        # 3. Check for embedded org-specific record IDs.
        issues.extend(_check_embedded_record_ids(json_path, raw_text))

        # 4. Check activation state of versioned components.
        issues.extend(_check_activation_flag_hint(json_path, data))

        # 5. Flag Named Credential references for cross-environment review.
        issues.extend(_check_named_credential_references(json_path, raw_text))

    return issues


def main() -> int:
    args = parse_args()
    datapack_dir = Path(args.datapack_dir)
    issues = check_datapack_dir(datapack_dir, verbose=args.verbose)

    if not issues:
        print("No issues found. DataPack export looks clean for deployment.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    print(f"\n{len(issues)} issue(s) found. Review before importing.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
