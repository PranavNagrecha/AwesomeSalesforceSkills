#!/usr/bin/env python3
"""Checker script for Analytics Data Manager skill.

Inspects Salesforce metadata files (WaveDataflow, WaveRecipe, WaveConnector,
WaveXmd) for common Data Manager configuration anti-patterns documented in
references/gotchas.md and references/llm-anti-patterns.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_analytics_data_manager.py [--help]
    python3 check_analytics_data_manager.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Analytics Data Manager configuration for common issues:\n"
            "  - Connected objects referenced directly in SAQL (not materialized via recipe/dataflow)\n"
            "  - Dataflow JSON nodes embedding remote connection credentials\n"
            "  - WaveConnector XML missing incremental sync configuration\n"
            "  - Sync object count approaching the 100-object limit\n"
            "  - Recipe/dataflow inputs that reference known external object names "
            "without a prior remote connection definition"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

SAQL_LOAD_PATTERN = re.compile(r'\bload\s+"([^"]+)"', re.IGNORECASE)

# Salesforce standard object API names that are commonly enabled as connected objects.
# LLMs frequently generate SAQL that loads these by API name instead of dataset name.
COMMON_CONNECTED_OBJECT_NAMES = {
    "account", "opportunity", "lead", "contact", "case", "user",
    "opportunitylineitem", "pricebook2", "product2", "task", "event",
    "campaignmember", "campaign", "contract", "quote", "order",
}

# Keywords that suggest remote connection credentials embedded in JSON.
CREDENTIAL_KEYS = {"host", "password", "username", "privatekey", "token", "secret"}


def check_saql_connected_object_references(manifest_dir: Path) -> list[str]:
    """Detect SAQL load() calls that reference Salesforce object API names directly.

    Connected objects must be materialized into datasets via recipe/dataflow before
    they can be loaded in SAQL. Loading a connected object by its Salesforce API name
    is an anti-pattern that will fail at query time.
    """
    issues: list[str] = []
    saql_files = list(manifest_dir.rglob("*.saql")) + list(manifest_dir.rglob("*.json"))

    for path in saql_files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for match in SAQL_LOAD_PATTERN.finditer(content):
            dataset_ref = match.group(1).lower()
            if dataset_ref in COMMON_CONNECTED_OBJECT_NAMES:
                issues.append(
                    f"{path}: SAQL `load \"{match.group(1)}\"` references a Salesforce "
                    f"object API name directly. Connected objects are staging-layer replicas "
                    f"and cannot be loaded in SAQL. Materialize via recipe/dataflow first, "
                    f"then load the output dataset name."
                )
    return issues


def check_remote_credentials_in_dataflow_json(manifest_dir: Path) -> list[str]:
    """Detect remote connection credential keys embedded inside dataflow JSON files.

    Remote connections (Snowflake, BigQuery, Redshift) must be configured in Data Manager
    UI, not embedded in dataflow JSON node parameters.
    """
    issues: list[str] = []
    dataflow_files = list(manifest_dir.rglob("*.json"))

    for path in dataflow_files:
        # Only inspect files that look like dataflow definitions.
        if "dataflow" not in path.name.lower() and "wave" not in path.name.lower():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except (json.JSONDecodeError, OSError):
            continue

        if not isinstance(data, dict):
            continue

        found_keys = _find_credential_keys_in_dict(data)
        if found_keys:
            issues.append(
                f"{path}: Possible remote connection credentials found in dataflow JSON "
                f"(keys: {', '.join(sorted(found_keys))}). Remote connection credentials "
                f"must be configured in Data Manager > Connect > Remote Connections, not "
                f"embedded in dataflow JSON."
            )
    return issues


def _find_credential_keys_in_dict(obj: object, _depth: int = 0) -> set[str]:
    """Recursively search a JSON structure for credential-like keys."""
    if _depth > 10:
        return set()
    found: set[str] = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.lower() in CREDENTIAL_KEYS and isinstance(value, str) and value:
                found.add(key.lower())
            found |= _find_credential_keys_in_dict(value, _depth + 1)
    elif isinstance(obj, list):
        for item in obj:
            found |= _find_credential_keys_in_dict(item, _depth + 1)
    return found


def check_wave_connector_sync_config(manifest_dir: Path) -> list[str]:
    """Check WaveDataConnector metadata XML for missing or misconfigured sync settings.

    Looks for WaveDataConnector XML files and flags connectors that do not specify
    a sync schedule or have no objects listed for sync.
    """
    issues: list[str] = []
    connector_files = list(manifest_dir.rglob("*.waveConnector")) + list(
        manifest_dir.rglob("WaveDataConnector*.xml")
    )

    for path in connector_files:
        try:
            tree = ET.parse(str(path))
        except (ET.ParseError, OSError):
            continue

        root = tree.getroot()
        ns = _xml_namespace(root)

        # Check for presence of connectedObjects or syncSchedule elements.
        connected_objects = root.findall(f"{ns}connectedObjects")
        sync_schedule = root.findall(f"{ns}syncSchedule")

        if not connected_objects:
            issues.append(
                f"{path}: WaveDataConnector has no connectedObjects defined. "
                f"Enable at least one object for sync before this connector is useful."
            )

        if not sync_schedule:
            issues.append(
                f"{path}: WaveDataConnector has no syncSchedule defined. "
                f"Sync will only run when manually triggered — consider adding a schedule."
            )

        if connected_objects:
            count = len(connected_objects)
            if count > 90:
                issues.append(
                    f"{path}: {count} connected objects found. "
                    f"Platform limit is 100 objects enabled for sync org-wide. "
                    f"Audit and disable unused objects before adding more."
                )

    return issues


def check_sync_object_count(manifest_dir: Path) -> list[str]:
    """Count total objects enabled for sync across all WaveConnector files.

    Warns when total count approaches the 100-object hard limit.
    """
    issues: list[str] = []
    connector_files = list(manifest_dir.rglob("*.waveConnector")) + list(
        manifest_dir.rglob("WaveDataConnector*.xml")
    )

    total_objects = 0
    for path in connector_files:
        try:
            tree = ET.parse(str(path))
        except (ET.ParseError, OSError):
            continue

        root = tree.getroot()
        ns = _xml_namespace(root)
        total_objects += len(root.findall(f"{ns}connectedObjects"))

    if total_objects >= 100:
        issues.append(
            f"Total sync objects across all connectors: {total_objects}. "
            f"This meets or exceeds the platform hard limit of 100. "
            f"No additional objects can be enabled until some are disabled."
        )
    elif total_objects >= 90:
        issues.append(
            f"Total sync objects across all connectors: {total_objects}. "
            f"Approaching the platform hard limit of 100. "
            f"Audit and disable unused objects before adding more."
        )

    return issues


def check_wave_recipe_for_connected_object_inputs(manifest_dir: Path) -> list[str]:
    """Check WaveRecipe JSON for input nodes that reference standard object names.

    Recipe input nodes that reference Salesforce object API names without a
    corresponding materialized dataset name suggest a connected-object-as-dataset confusion.
    """
    issues: list[str] = []
    recipe_files = list(manifest_dir.rglob("*.waveRecipe")) + list(
        manifest_dir.rglob("WaveRecipe*.json")
    )

    for path in recipe_files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            data = json.loads(content)
        except (json.JSONDecodeError, OSError):
            continue

        _check_recipe_nodes(data, path, issues)

    return issues


def _check_recipe_nodes(data: object, path: Path, issues: list[str]) -> None:
    """Recursively scan recipe JSON for input nodes referencing object API names."""
    if isinstance(data, dict):
        node_type = str(data.get("type", "")).lower()
        # Recipe input node types that read connected objects.
        if node_type in ("load", "connectedobjects", "input", "sfdcdigest"):
            source = str(data.get("source", data.get("object", data.get("name", "")))).lower()
            if source in COMMON_CONNECTED_OBJECT_NAMES:
                issues.append(
                    f"{path}: Recipe input node references '{source}' as a source. "
                    f"Confirm this refers to the connected object (staging layer) being "
                    f"consumed by this recipe — not a pre-existing dataset. "
                    f"Connected objects must not be referenced in dashboard SAQL directly; "
                    f"this recipe must output a named dataset for downstream use."
                )
        for value in data.values():
            _check_recipe_nodes(value, path, issues)
    elif isinstance(data, list):
        for item in data:
            _check_recipe_nodes(item, path, issues)


def _xml_namespace(element: ET.Element) -> str:
    """Extract the XML namespace string from an element tag, including braces."""
    if element.tag.startswith("{"):
        return element.tag.split("}")[0] + "}"
    return ""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_analytics_data_manager(manifest_dir: Path) -> list[str]:
    """Run all checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_saql_connected_object_references(manifest_dir))
    issues.extend(check_remote_credentials_in_dataflow_json(manifest_dir))
    issues.extend(check_wave_connector_sync_config(manifest_dir))
    issues.extend(check_sync_object_count(manifest_dir))
    issues.extend(check_wave_recipe_for_connected_object_inputs(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_analytics_data_manager(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
