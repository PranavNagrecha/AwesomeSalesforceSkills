#!/usr/bin/env python3
"""Checker script for Data Reconciliation Patterns skill.

Scans Salesforce metadata (retrieved via sfdx/sf CLI or manually exported)
for common data reconciliation anti-patterns.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_reconciliation_patterns.py [--help]
    python3 check_data_reconciliation_patterns.py --manifest-dir path/to/metadata
    python3 check_data_reconciliation_patterns.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SF_NS = "http://soap.sforce.com/2006/04/metadata"


def _parse_xml(path: Path) -> ET.Element | None:
    """Return the root element of an XML file, or None on parse failure."""
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def _tag(local: str) -> str:
    """Return a namespace-qualified tag name for Salesforce metadata XML."""
    return f"{{{SF_NS}}}{local}"


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------


def check_external_id_fields_have_unique(manifest_dir: Path) -> list[str]:
    """Warn when an External ID field does not also have the Unique constraint.

    Without the Unique constraint, upserts against the field will fail with
    MULTIPLE_CHOICES if any two records share the same value.
    """
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    # Support both sfdx source format (objects/<ObjName>/<ObjName>.object-meta.xml)
    # and mdapi format (objects/<ObjName>.object)
    field_files: list[Path] = []
    for p in objects_dir.rglob("*.field-meta.xml"):
        field_files.append(p)
    # mdapi format: fields are child elements inside the object XML
    for p in objects_dir.glob("*.object"):
        field_files_mdapi = list(objects_dir.rglob("*.object"))
        break
    else:
        field_files_mdapi = []

    # --- sfdx source format ---
    for fpath in field_files:
        root = _parse_xml(fpath)
        if root is None:
            continue
        is_ext_id = root.findtext(_tag("externalId")) == "true"
        is_unique = root.findtext(_tag("unique")) == "true"
        if is_ext_id and not is_unique:
            issues.append(
                f"External ID field lacks Unique constraint: {fpath.relative_to(manifest_dir)}"
                " — upserts will fail with MULTIPLE_CHOICES if duplicate values exist."
                " Add the Unique constraint or validate source data for uniqueness before loading."
            )

    # --- mdapi format ---
    for opath in field_files_mdapi:
        root = _parse_xml(opath)
        if root is None:
            continue
        for field_el in root.findall(_tag("fields")):
            is_ext_id = field_el.findtext(_tag("externalId")) == "true"
            is_unique = field_el.findtext(_tag("unique")) == "true"
            label = field_el.findtext(_tag("fullName")) or "(unknown)"
            obj_name = opath.stem
            if is_ext_id and not is_unique:
                issues.append(
                    f"External ID field '{label}' on {obj_name} lacks Unique constraint"
                    " — upserts will fail with MULTIPLE_CHOICES if duplicate values exist."
                )

    return issues


def check_no_cdc_retention_comment(manifest_dir: Path) -> list[str]:
    """Warn if Apex classes that reference CDC replayId lack a retention comment.

    CDC events are retained for 72 hours only. Integrations that reconnect
    without handling the expired-replayId case silently drop gap events.
    """
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.exists():
        return issues

    REPLAY_PATTERNS = ("replayId", "ReplayId", "replay_id")
    RETENTION_HINTS = ("72", "retention", "RETENTION", "gap recovery", "gap_recovery")

    for cls_file in classes_dir.glob("*.cls"):
        content = cls_file.read_text(encoding="utf-8", errors="replace")
        has_replay = any(p in content for p in REPLAY_PATTERNS)
        if not has_replay:
            continue
        has_retention_hint = any(h in content for h in RETENTION_HINTS)
        if not has_retention_hint:
            issues.append(
                f"Apex class uses CDC replayId but lacks a retention-window comment: "
                f"{cls_file.relative_to(manifest_dir)}"
                " — CDC events expire after 72 hours. Add handling for the case where"
                " the stored replayId falls outside the retention window."
            )

    return issues


def check_bulk_api_failed_results_check(manifest_dir: Path) -> list[str]:
    """Warn if Apex classes submit Bulk API jobs but do not check failedResults.

    A Bulk API 2.0 job that reaches JobComplete may still have failed rows.
    Integrations that only check job state silently miss partial failures.
    """
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.exists():
        return issues

    JOB_SUBMIT_HINTS = ("HttpRequest", "callout", "Callout", "BulkAPI", "bulk_api", "ingest/")
    FAILED_RESULTS_HINTS = ("failedResults", "failed_results", "numberRecordsFailed")

    for cls_file in classes_dir.glob("*.cls"):
        content = cls_file.read_text(encoding="utf-8", errors="replace")
        has_bulk_hint = any(h in content for h in JOB_SUBMIT_HINTS)
        if not has_bulk_hint:
            continue
        # Only flag files that also mention job completion state, suggesting they handle post-job logic
        has_job_complete = "JobComplete" in content or "jobComplete" in content
        if not has_job_complete:
            continue
        has_failed_check = any(h in content for h in FAILED_RESULTS_HINTS)
        if not has_failed_check:
            issues.append(
                f"Apex class checks JobComplete but does not fetch failedResults: "
                f"{cls_file.relative_to(manifest_dir)}"
                " — Bulk API 2.0 jobs can reach JobComplete with failed rows."
                " Fetch the failedResults endpoint and check numberRecordsFailed."
            )

    return issues


def check_external_id_field_type(manifest_dir: Path) -> list[str]:
    """Warn when a Text External ID field may have case-sensitivity issues.

    Text-type External ID fields in Salesforce are case-sensitive by default.
    If the source system sends mixed-case keys, upserts will create duplicates.
    """
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    for fpath in objects_dir.rglob("*.field-meta.xml"):
        root = _parse_xml(fpath)
        if root is None:
            continue
        is_ext_id = root.findtext(_tag("externalId")) == "true"
        field_type = root.findtext(_tag("type")) or ""
        if is_ext_id and field_type.lower() == "text":
            # Only warn; case-sensitivity may be intentional
            issues.append(
                f"Text-type External ID field: {fpath.relative_to(manifest_dir)}"
                " — Text External ID fields are case-sensitive."
                " Confirm that source data is normalized to consistent casing before upsert."
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def check_data_reconciliation_patterns(manifest_dir: Path) -> list[str]:
    """Run all reconciliation-pattern checks. Return list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_external_id_fields_have_unique(manifest_dir))
    issues.extend(check_external_id_field_type(manifest_dir))
    issues.extend(check_no_cdc_retention_comment(manifest_dir))
    issues.extend(check_bulk_api_failed_results_check(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for data reconciliation anti-patterns:\n"
            "  - External ID fields missing Unique constraint\n"
            "  - Text External ID fields (case-sensitive by default)\n"
            "  - CDC replayId usage without retention-window handling\n"
            "  - Bulk API job completion checks missing failedResults fetch"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_data_reconciliation_patterns(manifest_dir)

    if not issues:
        print("No data reconciliation issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
