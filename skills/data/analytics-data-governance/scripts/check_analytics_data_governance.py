#!/usr/bin/env python3
"""Checker script for Analytics Data Governance skill.

Checks Salesforce metadata project artifacts for CRM Analytics governance
configuration issues. Inspects wave/ metadata files, dataflow/recipe JSON,
and related XML for common compliance and governance gaps.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_analytics_data_governance.py [--help]
    python3 check_analytics_data_governance.py --manifest-dir path/to/metadata
    python3 check_analytics_data_governance.py --manifest-dir . --strict
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import NamedTuple


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class Issue(NamedTuple):
    severity: str   # "ERROR" | "WARN" | "INFO"
    code: str       # short machine-readable code
    message: str    # human-readable description


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check CRM Analytics metadata for data governance issues: "
            "dataset lineage coverage, event monitoring event type enablement, "
            "and common anti-patterns."
        )
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat WARN-level findings as failures (exit code 1).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Check: Wave directory presence
# ---------------------------------------------------------------------------

def check_wave_directory_present(manifest_dir: Path) -> list[Issue]:
    """Verify that a wave/ directory exists (CRM Analytics metadata)."""
    issues: list[Issue] = []
    wave_dir = manifest_dir / "wave"
    if not wave_dir.exists():
        # Also check force-app paths
        alt_wave = manifest_dir / "force-app" / "main" / "default" / "wave"
        if not alt_wave.exists():
            issues.append(Issue(
                severity="INFO",
                code="WAVE_DIR_MISSING",
                message=(
                    "No wave/ metadata directory found. "
                    "If this project includes CRM Analytics assets, ensure the "
                    "wave/ directory is included in the metadata manifest. "
                    "This check cannot verify analytics governance without it."
                ),
            ))
    return issues


# ---------------------------------------------------------------------------
# Check: Dataflow files for output dataset names (lineage surface check)
# ---------------------------------------------------------------------------

def check_dataflow_lineage_coverage(manifest_dir: Path) -> list[Issue]:
    """Check dataflow JSON files for register nodes (output datasets).

    A dataflow that produces no sfdcRegister nodes is suspicious —
    it reads data but documents no output datasets, making lineage tracing
    incomplete.
    """
    issues: list[Issue] = []

    # Locate .wdf and .json files in wave/dataflow paths
    wave_dirs = [
        manifest_dir / "wave",
        manifest_dir / "force-app" / "main" / "default" / "wave",
    ]
    df_files: list[Path] = []
    for wave_dir in wave_dirs:
        if wave_dir.exists():
            df_files.extend(wave_dir.rglob("*.wdf"))
            df_files.extend(
                p for p in wave_dir.rglob("*.json")
                if "dataflow" in p.parts or "dataflow" in p.name.lower()
            )

    if not df_files:
        return issues  # Nothing to check; not an error at this layer

    for df_file in df_files:
        try:
            data = json.loads(df_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            issues.append(Issue(
                severity="WARN",
                code="DATAFLOW_PARSE_ERROR",
                message=f"Could not parse dataflow file {df_file}: {exc}",
            ))
            continue

        nodes: dict = data if isinstance(data, dict) else data.get("nodes", {})
        if not isinstance(nodes, dict):
            continue

        # Find nodes that look like sfdcRegister (output) nodes
        register_nodes = [
            node for node in nodes.values()
            if isinstance(node, dict)
            and (
                node.get("action") == "sfdcRegister"
                or "dataset" in (node.get("parameters") or {})
            )
        ]

        if not register_nodes:
            issues.append(Issue(
                severity="WARN",
                code="DATAFLOW_NO_OUTPUT_DATASET",
                message=(
                    f"Dataflow file '{df_file.name}' contains no identifiable output dataset "
                    "(sfdcRegister) nodes. Lineage tracing will not find datasets produced by "
                    "this dataflow. Verify the dataflow schema is complete and not a stub."
                ),
            ))
        else:
            # Check each register node documents a dataset name
            for node_name, node in nodes.items():
                if not isinstance(node, dict):
                    continue
                if node.get("action") == "sfdcRegister":
                    params = node.get("parameters", {})
                    ds_info = params.get("dataset", {})
                    ds_name = ds_info.get("name") if isinstance(ds_info, dict) else None
                    if not ds_name:
                        issues.append(Issue(
                            severity="WARN",
                            code="DATAFLOW_REGISTER_NO_NAME",
                            message=(
                                f"Dataflow '{df_file.name}', node '{node_name}': "
                                "sfdcRegister node has no dataset.name. "
                                "Lineage map cannot identify the output dataset."
                            ),
                        ))

    return issues


# ---------------------------------------------------------------------------
# Check: Wave app metadata for Event Monitoring event types
# ---------------------------------------------------------------------------

def check_event_monitoring_event_types(manifest_dir: Path) -> list[Issue]:
    """Check WaveApplication XML for WaveChange / WaveInteraction event type references.

    This is a best-effort check — Event Monitoring is configured at the org level,
    not in WaveApplication metadata. But WaveApplication files that explicitly
    reference event monitoring dashboards are a signal that access auditing is in scope.
    """
    issues: list[Issue] = []

    wave_dirs = [
        manifest_dir / "wave",
        manifest_dir / "force-app" / "main" / "default" / "wave",
    ]

    app_files: list[Path] = []
    for wave_dir in wave_dirs:
        if wave_dir.exists():
            app_files.extend(wave_dir.rglob("*.wapp"))
            app_files.extend(wave_dir.rglob("*-app.json"))

    if not app_files:
        return issues

    wave_event_types = {"WaveChange", "WaveInteraction", "WavePerformance"}
    found_event_ref = False

    for app_file in app_files:
        content = ""
        try:
            content = app_file.read_text(encoding="utf-8")
        except OSError:
            continue

        for ev_type in wave_event_types:
            if ev_type in content:
                found_event_ref = True
                break

    # If no app files reference event monitoring types and there are wave apps,
    # surface as an informational note.
    if app_files and not found_event_ref:
        issues.append(Issue(
            severity="INFO",
            code="EVENT_MONITORING_NOT_REFERENCED",
            message=(
                "CRM Analytics app files were found but none reference Event Monitoring "
                "event types (WaveChange, WaveInteraction, WavePerformance). "
                "If access audit logging is a governance requirement, confirm that "
                "the Event Monitoring add-on is licensed and these event types are enabled "
                "at the org level. This cannot be verified from metadata alone."
            ),
        ))

    return issues


# ---------------------------------------------------------------------------
# Check: Dataset metadata for sensitivity-relevant field naming patterns
# ---------------------------------------------------------------------------

def check_dataset_pii_column_patterns(manifest_dir: Path) -> list[Issue]:
    """Scan dataset XMD JSON files for columns with PII-suggestive names.

    If PII-suggestive columns are found, warn that they require governance
    treatment since Data Classification does not propagate from source objects.
    """
    issues: list[Issue] = []

    # Common PII-suggestive column name substrings (case-insensitive)
    pii_patterns = [
        "ssn", "social_security", "dob", "date_of_birth", "birthdate",
        "passport", "license_number", "tax_id", "ein", "credit_card",
        "card_number", "salary", "compensation", "email", "phone",
        "address", "postal_code", "zip_code", "gender", "race",
        "ethnicity", "religion", "health", "medical", "diagnosis",
        "hipaa", "pii", "sensitive", "restricted",
    ]

    wave_dirs = [
        manifest_dir / "wave",
        manifest_dir / "force-app" / "main" / "default" / "wave",
    ]

    xmd_files: list[Path] = []
    for wave_dir in wave_dirs:
        if wave_dir.exists():
            xmd_files.extend(wave_dir.rglob("*.xmd"))
            xmd_files.extend(
                p for p in wave_dir.rglob("*.json")
                if "xmd" in p.name.lower() or "extended_metadata" in p.name.lower()
            )

    for xmd_file in xmd_files:
        try:
            data = json.loads(xmd_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        # XMD structure: top-level "dataset" object with "dimensions" and "measures"
        dimensions = data.get("dataset", {}).get("dimensions", [])
        measures = data.get("dataset", {}).get("measures", [])
        all_columns = dimensions + measures

        for col in all_columns:
            col_name = (col.get("name") or col.get("label") or "").lower()
            col_field = (col.get("field") or "").lower()
            combined = f"{col_name} {col_field}"
            matched_patterns = [p for p in pii_patterns if p in combined]
            if matched_patterns:
                issues.append(Issue(
                    severity="WARN",
                    code="DATASET_PII_COLUMN_UNGOVERNED",
                    message=(
                        f"XMD file '{xmd_file.name}': column '{col.get('name', '?')}' "
                        f"matches PII-suggestive patterns ({', '.join(matched_patterns)}). "
                        "Salesforce Data Classification does NOT propagate from source "
                        "objects into CRM Analytics datasets. Confirm this column has "
                        "explicit governance controls: column exclusion, row-level predicate, "
                        "or documented classification in the governance register."
                    ),
                ))

    return issues


# ---------------------------------------------------------------------------
# Check: Permission set metadata for Event Monitoring permission
# ---------------------------------------------------------------------------

def check_event_monitoring_permission(manifest_dir: Path) -> list[Issue]:
    """Check PermissionSet XML files for EventMonitoring system permission.

    If no permission set grants EventMonitoring, surface as a warning that
    access audit capability may not be in place.
    """
    issues: list[Issue] = []

    ps_dirs = [
        manifest_dir / "permissionsets",
        manifest_dir / "force-app" / "main" / "default" / "permissionsets",
    ]

    ps_files: list[Path] = []
    for ps_dir in ps_dirs:
        if ps_dir.exists():
            ps_files.extend(ps_dir.rglob("*.permissionset-meta.xml"))
            ps_files.extend(ps_dir.rglob("*.permissionset"))

    if not ps_files:
        return issues  # No permission sets in project — can't check

    event_monitoring_granted = False

    for ps_file in ps_files:
        try:
            tree = ET.parse(ps_file)
        except ET.ParseError:
            continue

        root = tree.getroot()
        # Handle XML namespaces
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        for sys_perm in root.findall(f"{ns}systemPermissions"):
            name_el = sys_perm.find(f"{ns}name")
            enabled_el = sys_perm.find(f"{ns}enabled")
            if (
                name_el is not None
                and enabled_el is not None
                and name_el.text == "ViewEventLogFiles"
                and enabled_el.text == "true"
            ):
                event_monitoring_granted = True
                break

        if event_monitoring_granted:
            break

    if ps_files and not event_monitoring_granted:
        issues.append(Issue(
            severity="INFO",
            code="EVENT_MONITORING_PERM_NOT_FOUND",
            message=(
                "No permission set in this metadata project grants 'ViewEventLogFiles' "
                "(the system permission required to access Event Monitoring logs). "
                "If CRM Analytics access audit logging is required, ensure at least one "
                "permission set grants this permission and is assigned to the audit team. "
                "Note: EventLogFile and Event Log Object access requires this permission "
                "plus the Event Monitoring add-on license."
            ),
        ))

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_checks(manifest_dir: Path) -> list[Issue]:
    """Run all governance checks and return consolidated issue list."""
    all_issues: list[Issue] = []

    checks = [
        check_wave_directory_present,
        check_dataflow_lineage_coverage,
        check_event_monitoring_event_types,
        check_dataset_pii_column_patterns,
        check_event_monitoring_permission,
    ]

    for check_fn in checks:
        try:
            all_issues.extend(check_fn(manifest_dir))
        except Exception as exc:  # noqa: BLE001
            all_issues.append(Issue(
                severity="WARN",
                code="CHECK_EXECUTION_ERROR",
                message=f"Check '{check_fn.__name__}' failed unexpectedly: {exc}",
            ))

    return all_issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ERROR: Manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 2

    issues = run_checks(manifest_dir)

    if not issues:
        print("No analytics data governance issues found.")
        return 0

    errors = [i for i in issues if i.severity == "ERROR"]
    warnings = [i for i in issues if i.severity == "WARN"]
    infos = [i for i in issues if i.severity == "INFO"]

    for issue in errors:
        print(f"ERROR [{issue.code}]: {issue.message}", file=sys.stderr)
    for issue in warnings:
        print(f"WARN  [{issue.code}]: {issue.message}", file=sys.stderr)
    for issue in infos:
        print(f"INFO  [{issue.code}]: {issue.message}")

    summary = (
        f"\nSummary: {len(errors)} error(s), {len(warnings)} warning(s), "
        f"{len(infos)} info(s)."
    )
    print(summary)

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
