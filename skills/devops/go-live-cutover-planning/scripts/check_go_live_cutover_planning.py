#!/usr/bin/env python3
"""Checker script for Go Live Cutover Planning skill.

Scans a Salesforce metadata directory for common go-live readiness issues:
- Flows deployed in active state without trigger order set
- Destructive changes mixed with constructive changes in the same manifest
- Scheduled Apex classes that may be aborted during deployment
- Named Credentials that will need post-deploy authentication

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_go_live_cutover_planning.py [--help]
    python3 check_go_live_cutover_planning.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


METADATA_NS = "http://soap.sforce.com/2006/04/metadata"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check go-live cutover readiness in a Salesforce metadata directory.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _find_files(root: Path, suffix: str) -> list[Path]:
    """Recursively find files with the given suffix."""
    results: list[Path] = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.endswith(suffix):
                results.append(Path(dirpath) / f)
    return results


def _parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse XML, returning None on failure."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except (ET.ParseError, OSError):
        return None


def check_flows_without_trigger_order(manifest_dir: Path) -> list[str]:
    """Check for record-triggered Flows deployed active without triggerOrder."""
    issues: list[str] = []
    flow_files = _find_files(manifest_dir, ".flow-meta.xml")

    for flow_path in flow_files:
        root = _parse_xml_safe(flow_path)
        if root is None:
            continue

        # Check for record-triggered flows (processType = AutoLaunchedFlow with triggerType)
        process_type = root.find(f"{{{METADATA_NS}}}processType")
        trigger_type = root.find(f"{{{METADATA_NS}}}triggerType")
        status = root.find(f"{{{METADATA_NS}}}status")
        trigger_order = root.find(f"{{{METADATA_NS}}}triggerOrder")

        if trigger_type is not None and trigger_type.text in (
            "RecordBeforeSave",
            "RecordAfterSave",
            "RecordBeforeDelete",
        ):
            if status is not None and status.text == "Active":
                if trigger_order is None:
                    issues.append(
                        f"CUTOVER-RISK: Flow '{flow_path.stem.replace('.flow-meta', '')}' is a "
                        f"record-triggered Flow deployed as Active without triggerOrder set. "
                        f"This can cause unpredictable execution order with other Flows on the same object."
                    )

    return issues


def check_destructive_changes_present(manifest_dir: Path) -> list[str]:
    """Check for destructiveChanges.xml and warn about sequencing."""
    issues: list[str] = []
    destructive_files = _find_files(manifest_dir, "destructiveChanges.xml")
    destructive_pre_files = _find_files(manifest_dir, "destructiveChangesPre.xml")
    destructive_post_files = _find_files(manifest_dir, "destructiveChangesPost.xml")

    all_destructive = destructive_files + destructive_pre_files + destructive_post_files

    if all_destructive:
        for df in all_destructive:
            root = _parse_xml_safe(df)
            if root is None:
                continue
            types_elements = root.findall(f"{{{METADATA_NS}}}types")
            member_count = sum(
                len(t.findall(f"{{{METADATA_NS}}}members")) for t in types_elements
            )
            issues.append(
                f"CUTOVER-WARNING: Destructive changes manifest found at '{df}' "
                f"with {member_count} member(s). Ensure destructive deploy runs AFTER "
                f"constructive changes and verify no remaining references to deleted components."
            )

    return issues


def check_named_credentials(manifest_dir: Path) -> list[str]:
    """Check for Named Credentials that will need post-deploy authentication."""
    issues: list[str] = []
    nc_files = _find_files(manifest_dir, ".namedCredential-meta.xml")

    for nc_path in nc_files:
        nc_name = nc_path.stem.replace(".namedCredential-meta", "")
        root = _parse_xml_safe(nc_path)
        if root is None:
            issues.append(
                f"CUTOVER-ACTION: Named Credential '{nc_name}' found. "
                f"Add a post-deployment step to verify authentication status in Setup."
            )
            continue

        # Check for OAuth-based auth
        auth_protocol = root.find(f"{{{METADATA_NS}}}authProtocol")
        if auth_protocol is not None and auth_protocol.text == "OAuth":
            issues.append(
                f"CUTOVER-ACTION: Named Credential '{nc_name}' uses OAuth. "
                f"OAuth tokens are NOT deployed with metadata. Add a post-deployment step "
                f"to complete the OAuth flow in Setup > Named Credentials."
            )
        else:
            issues.append(
                f"CUTOVER-ACTION: Named Credential '{nc_name}' found. "
                f"Verify authentication status post-deployment in Setup > Named Credentials."
            )

    return issues


def check_scheduled_apex(manifest_dir: Path) -> list[str]:
    """Check for Apex classes that implement Schedulable — these may be aborted during deploy."""
    issues: list[str] = []
    cls_files = _find_files(manifest_dir, ".cls")

    for cls_path in cls_files:
        try:
            content = cls_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if "implements" in content and "Schedulable" in content:
            class_name = cls_path.stem
            issues.append(
                f"CUTOVER-ACTION: Apex class '{class_name}' implements Schedulable. "
                f"Deploying changes to this class will abort its scheduled job (CronTrigger). "
                f"Add a post-deployment step to verify the job is rescheduled in Setup > Scheduled Jobs."
            )

    return issues


def check_go_live_cutover_planning(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_flows_without_trigger_order(manifest_dir))
    issues.extend(check_destructive_changes_present(manifest_dir))
    issues.extend(check_named_credentials(manifest_dir))
    issues.extend(check_scheduled_apex(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_go_live_cutover_planning(manifest_dir)

    if not issues:
        print("No cutover readiness issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
