#!/usr/bin/env python3
"""Checker script for Salesforce Release Preparation skill.

Inspects a Salesforce metadata directory for signals that suggest release
preparation tasks are outstanding or that known-risky patterns are in place.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_salesforce_release_preparation.py [--manifest-dir path/to/metadata]
    python3 check_salesforce_release_preparation.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_files(root: Path, suffix: str) -> list[Path]:
    """Return all files under *root* with the given suffix."""
    return list(root.rglob(f"*{suffix}")) if root.exists() else []


def parse_xml(path: Path) -> ET.Element | None:
    """Parse an XML file and return the root element, or None on error."""
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_flow_null_comparisons(manifest_dir: Path) -> list[str]:
    """Warn about Flow Decision conditions that use literal null comparisons.

    Release Updates for null handling in Flow have been a repeated enforcement
    item across multiple releases.  Direct null comparisons in Decision elements
    break when stricter null evaluation is enforced.
    """
    issues: list[str] = []
    flow_files = find_files(manifest_dir, ".flow-meta.xml")

    for flow_path in flow_files:
        root = parse_xml(flow_path)
        if root is None:
            continue

        ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
        # Try both namespaced and non-namespaced element lookup
        decisions = root.findall(".//decisions") + root.findall(".//sf:decisions", ns)

        for decision in decisions:
            conditions = decision.findall(".//conditions") + decision.findall(
                ".//sf:conditions", ns
            )
            for condition in conditions:
                # Look for a rightValue element that is explicitly empty or
                # whose stringValue/elementReference is "null" as a literal.
                right_val = (
                    condition.find("rightValue")
                    or condition.find("sf:rightValue", ns)
                )
                if right_val is not None:
                    string_val = right_val.find("stringValue") or right_val.find(
                        "sf:stringValue", ns
                    )
                    if string_val is not None and string_val.text in (
                        "null",
                        "NULL",
                        "",
                        None,
                    ):
                        label_el = decision.find("label") or decision.find(
                            "sf:label", ns
                        )
                        label = label_el.text if label_el is not None else "unknown"
                        issues.append(
                            f"Flow {flow_path.name}: Decision '{label}' contains a "
                            "literal null comparison in a condition. This may break "
                            "when Release Updates enforce stricter null handling. "
                            "Replace with ISNULL() formula or $GlobalConstant.EmptyString."
                        )

    return issues


def check_deprecated_api_versions(manifest_dir: Path) -> list[str]:
    """Warn about Apex classes or LWC bundles using very old API versions.

    Salesforce deprecates older API versions over time. Classes and components
    on API versions below 40.0 (Spring '17) are candidates for a release-driven
    compilation or behavior change.
    """
    issues: list[str] = []
    MINIMUM_RECOMMENDED_API = 50  # API 50.0 = Winter '21

    meta_files = find_files(manifest_dir, "-meta.xml")
    for meta_path in meta_files:
        root = parse_xml(meta_path)
        if root is None:
            continue

        ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
        api_el = root.find("apiVersion") or root.find("sf:apiVersion", ns)
        if api_el is None or not api_el.text:
            continue

        try:
            api_version = float(api_el.text)
        except ValueError:
            continue

        if api_version < MINIMUM_RECOMMENDED_API:
            issues.append(
                f"{meta_path.name}: API version {api_el.text} is below the "
                f"recommended minimum of {MINIMUM_RECOMMENDED_API}.0. "
                "Upgrade to a current API version to avoid deprecated behavior "
                "changes in upcoming releases."
            )

    return issues


def check_scheduled_apex_without_comment(manifest_dir: Path) -> list[str]:
    """Warn about Schedulable Apex classes that lack a release-readiness comment.

    Scheduled jobs are a common failure point after a production upgrade because
    they run automatically, may interact with changed platform behavior, and are
    easy to overlook in release testing.  This check flags classes implementing
    Schedulable that have no comment mentioning release, upgrade, or test.
    """
    issues: list[str] = []
    apex_files = find_files(manifest_dir, ".cls")

    for cls_path in apex_files:
        try:
            source = cls_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        if "implements Schedulable" not in source and "implements schedulable" not in source.lower():
            continue

        comment_keywords = ("release", "upgrade", "schedule", "cron", "post-upgrade")
        has_comment = any(kw in source.lower() for kw in comment_keywords)
        if not has_comment:
            issues.append(
                f"{cls_path.name}: Implements Schedulable but has no comment "
                "referencing release, upgrade, or post-upgrade behavior. "
                "Confirm this job is included in sandbox release testing — "
                "scheduled jobs often break silently after platform upgrades."
            )

    return issues


def check_flows_without_fault_paths(manifest_dir: Path) -> list[str]:
    """Warn about active Flows missing fault connector paths on record operations.

    After a release, record operations in Flows may throw new exceptions if
    validation rules, triggers, or sharing recalculations change.  Flows without
    fault paths surface errors as uncaught runtime exceptions to end users.
    """
    issues: list[str] = []
    flow_files = find_files(manifest_dir, ".flow-meta.xml")

    for flow_path in flow_files:
        root = parse_xml(flow_path)
        if root is None:
            continue

        ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}

        # Only check active flows
        status_el = root.find("status") or root.find("sf:status", ns)
        if status_el is None or status_el.text not in ("Active", "active"):
            continue

        # Look for record-write elements (Create/Update/Delete)
        record_ops = (
            root.findall(".//recordCreates")
            + root.findall(".//recordUpdates")
            + root.findall(".//recordDeletes")
            + root.findall(".//sf:recordCreates", ns)
            + root.findall(".//sf:recordUpdates", ns)
            + root.findall(".//sf:recordDeletes", ns)
        )

        for op in record_ops:
            fault_connector = op.find("faultConnector") or op.find(
                "sf:faultConnector", ns
            )
            if fault_connector is None:
                label_el = op.find("label") or op.find("sf:label", ns)
                label = label_el.text if label_el is not None else "unknown element"
                issues.append(
                    f"Flow {flow_path.name}: Record operation '{label}' has no fault "
                    "connector. If this operation fails after a release update (e.g. "
                    "changed validation or trigger behavior), the error will surface as "
                    "an unhandled exception. Add a fault path."
                )

    return issues


def check_release_prep_doc_exists(manifest_dir: Path) -> list[str]:
    """Check whether a release readiness checklist doc exists in the project."""
    issues: list[str] = []
    keywords = ("release", "readiness", "upgrade")

    project_root = manifest_dir
    # Walk up from manifest dir to find project root (up to 4 levels)
    for _ in range(4):
        docs = list(project_root.glob("*.md")) + list(project_root.glob("docs/*.md"))
        if any(
            all(kw in p.name.lower() for kw in keywords[:2]) for p in docs
        ):
            return issues  # Found a likely release readiness doc
        parent = project_root.parent
        if parent == project_root:
            break
        project_root = parent

    issues.append(
        "No release readiness checklist document found in the project directory. "
        "Consider adding a release-readiness.md or using the "
        "skills/admin/salesforce-release-preparation/templates/ template to track "
        "preparation status for each seasonal release."
    )
    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_salesforce_release_preparation(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_flow_null_comparisons(manifest_dir))
    issues.extend(check_deprecated_api_versions(manifest_dir))
    issues.extend(check_scheduled_apex_without_comment(manifest_dir))
    issues.extend(check_flows_without_fault_paths(manifest_dir))
    issues.extend(check_release_prep_doc_exists(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for release-preparation risk signals: "
            "null comparisons in Flow decisions, low API versions, Schedulable Apex "
            "without release notes, and active Flows missing fault paths."
        ),
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
    issues = check_salesforce_release_preparation(manifest_dir)

    if not issues:
        print("No release-preparation issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
