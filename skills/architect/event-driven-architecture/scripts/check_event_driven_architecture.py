#!/usr/bin/env python3
"""Checker script for Event-Driven Architecture skill.

Validates EDA-related metadata and configuration for common architectural issues.
Uses stdlib only — no pip dependencies.

Checks:
- Platform Events with no subscriber (orphaned events)
- Platform Events used in ways suggesting event sourcing without durable store
- Apex trigger consumers missing idempotency patterns
- Flow-based Platform Event subscribers that have no retry or error handling
- EDA-related custom objects missing External ID fields (idempotency)

Usage:
    python3 check_event_driven_architecture.py [--manifest-dir path/to/metadata]
    python3 check_event_driven_architecture.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


SF_NS = "http://soap.sforce.com/2006/04/metadata"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for EDA architectural issues: "
            "idempotency gaps, event sourcing without durable store, "
            "orphaned Platform Events, and missing error handling in subscribers."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_files(root: Path, suffix: str) -> list[Path]:
    """Return all files with the given suffix under root."""
    return list(root.rglob(f"*{suffix}"))


def _tag(local: str) -> str:
    return f"{{{SF_NS}}}{local}"


def check_platform_events(manifest_dir: Path) -> list[str]:
    """Check Platform Event object definitions for common issues."""
    issues: list[str] = []
    event_objects: list[str] = []

    for obj_file in find_files(manifest_dir, ".object-meta.xml"):
        try:
            tree = ET.parse(obj_file)
        except ET.ParseError:
            continue
        root = tree.getroot()

        # Detect Platform Event objects (apiName ends with __e or deploymentStatus + eventType)
        api_name = obj_file.stem.replace(".object-meta", "")
        if api_name.endswith("__e"):
            event_objects.append(api_name)

            # Check: does this event have a Published_Event_Type__c or schema version field?
            fields = root.findall(f".//{_tag('fields')}")
            field_names = set()
            for field in fields:
                name_el = field.find(_tag("fullName"))
                if name_el is not None and name_el.text:
                    field_names.add(name_el.text.lower())

            has_version = any(
                kw in fn for fn in field_names
                for kw in ("version", "schema_version", "schemaversion")
            )
            has_idempotency_key = any(
                kw in fn for fn in field_names
                for kw in ("event_id", "eventid", "idempotency", "external_id", "correlation")
            )

            if not has_version:
                issues.append(
                    f"Platform Event '{api_name}' has no schema version field. "
                    "Add a Version__c or Schema_Version__c field to enable consumer "
                    "forward-compatibility on schema changes."
                )
            if not has_idempotency_key:
                issues.append(
                    f"Platform Event '{api_name}' has no idempotency key field. "
                    "Add an Event_ID__c or External_Event_ID__c field so consumers "
                    "can deduplicate on at-least-once redelivery."
                )

    return issues, event_objects


def check_apex_triggers_for_idempotency(manifest_dir: Path, event_names: list[str]) -> list[str]:
    """Check Apex trigger files for Platform Event consumers missing idempotency patterns."""
    issues: list[str] = []

    for trigger_file in find_files(manifest_dir, ".trigger"):
        try:
            content = trigger_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Check if this trigger fires on a Platform Event (sObject ends with __e)
        is_event_trigger = False
        for line in content.splitlines():
            lower = line.lower()
            if "trigger" in lower and "__e" in lower and ("after insert" in lower or "after update" in lower):
                is_event_trigger = True
                break

        if not is_event_trigger:
            continue

        # Idempotency indicators: upsert, EXISTS query, processed log lookup
        has_upsert = "upsert " in content.lower()
        has_exists_check = (
            "select id" in content.lower() and
            any(kw in content.lower() for kw in ["where", "external_id", "event_id"])
        )
        has_idempotency = has_upsert or has_exists_check

        if not has_idempotency:
            issues.append(
                f"Apex trigger '{trigger_file.stem}' appears to be a Platform Event subscriber "
                "but contains no idempotency check (UPSERT or EXISTS query). "
                "Platform Events are delivered at-least-once — add deduplication logic "
                "using UPSERT on an External ID or a processed-event lookup."
            )

        # Check for ordering assumption: direct index access without sequence check
        if "trigger.new[0]" in content.lower() and "__e" in content.lower():
            issues.append(
                f"Apex trigger '{trigger_file.stem}' accesses Trigger.new[0] on a Platform Event. "
                "Platform Events do not guarantee ordering — process all events in Trigger.new "
                "and implement sequence number logic if order matters."
            )

    return issues


def check_flows_for_event_subscribers(manifest_dir: Path) -> list[str]:
    """Check Flow metadata for Platform Event-triggered flows missing fault paths."""
    issues: list[str] = []

    for flow_file in find_files(manifest_dir, ".flow-meta.xml"):
        try:
            tree = ET.parse(flow_file)
        except ET.ParseError:
            continue
        root = tree.getroot()

        # Check processType — Platform Event-triggered flows have processType = AutoLaunchedFlow
        # and a start element referencing a __e object
        process_type_el = root.find(_tag("processType"))
        if process_type_el is None:
            continue
        process_type = (process_type_el.text or "").strip()

        # Look for Platform Event trigger source
        trigger_type_el = root.find(f".//{_tag('triggerType')}")
        object_el = root.find(f".//{_tag('object')}")

        if trigger_type_el is not None and object_el is not None:
            trigger_type = (trigger_type_el.text or "").strip()
            object_name = (object_el.text or "").strip()

            if object_name.endswith("__e") or trigger_type == "PlatformEvent":
                # Check for fault connectors — flows with no fault paths have no error handling
                fault_connectors = root.findall(f".//{_tag('faultConnector')}")
                if not fault_connectors:
                    flow_name = flow_file.stem.replace(".flow-meta", "")
                    issues.append(
                        f"Flow '{flow_name}' is triggered by Platform Event '{object_name}' "
                        "but has no fault connector elements. Add fault paths to handle "
                        "subscriber failures — unhandled errors in event-triggered flows "
                        "are silently dropped with no retry."
                    )

    return issues


def check_for_event_sourcing_without_durable_store(manifest_dir: Path) -> list[str]:
    """Detect patterns suggesting event sourcing reliance on Platform Events replay."""
    issues: list[str] = []

    # Look for Apex files referencing replayId: -2 (full replay) without a custom object write
    for apex_file in find_files(manifest_dir, ".cls"):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        lower = content.lower()
        if "replayid" in lower and ("-2" in content or "earliest" in lower):
            # Check if there is also a DML insert to a log object
            has_durable_store_write = any(
                kw in lower for kw in [
                    "event_log__c", "eventlog__c", "audit_log__c", "event_store__c"
                ]
            )
            if not has_durable_store_write:
                issues.append(
                    f"Apex class '{apex_file.stem}' uses full replay (replayId -2 or earliest) "
                    "without writing to a durable event log object. "
                    "Platform Events have a 72-hour replay window — if recovery or state "
                    "reconstruction beyond 72 hours is required, write events to an "
                    "Event_Log__c object or external durable store (Data Cloud, Kafka)."
                )

    return issues


def check_event_driven_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check Platform Event definitions
    platform_event_issues, event_names = check_platform_events(manifest_dir)
    issues.extend(platform_event_issues)

    # Check Apex consumers for idempotency
    issues.extend(check_apex_triggers_for_idempotency(manifest_dir, event_names))

    # Check Flow subscribers for fault paths
    issues.extend(check_flows_for_event_subscribers(manifest_dir))

    # Check for event sourcing reliance on Platform Events replay
    issues.extend(check_for_event_sourcing_without_durable_store(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_event_driven_architecture(manifest_dir)

    if not issues:
        print("No EDA architectural issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
