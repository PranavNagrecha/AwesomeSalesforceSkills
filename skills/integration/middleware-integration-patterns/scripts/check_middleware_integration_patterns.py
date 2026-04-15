#!/usr/bin/env python3
"""Checker script for Middleware Integration Patterns skill.

Analyzes Salesforce metadata (Apex triggers, Flow metadata) for patterns
that indicate middleware may be needed but is not present, or that Apex
is being misused for multi-system orchestration.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_middleware_integration_patterns.py [--help]
    python3 check_middleware_integration_patterns.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for middleware integration anti-patterns: "
            "multi-callout Apex triggers, missing dead-letter design, "
            "and governor-limit-risk orchestration patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------

def check_multi_callout_apex_triggers(manifest_dir: Path) -> list[str]:
    """Warn when an Apex trigger file contains multiple Http.send() calls.

    Multiple outbound callouts in a single trigger indicate cross-system
    orchestration that should be moved to middleware.
    """
    issues: list[str] = []
    trigger_dir = manifest_dir / "triggers"
    if not trigger_dir.exists():
        return issues

    callout_pattern = re.compile(r"http\.send\s*\(", re.IGNORECASE)

    for apex_file in trigger_dir.glob("*.trigger"):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        matches = callout_pattern.findall(content)
        if len(matches) >= 2:
            issues.append(
                f"{apex_file.name}: contains {len(matches)} Http.send() calls. "
                "Multiple callouts in one trigger risks governor limits (100/transaction) "
                "and indicates orchestration that should be handled by middleware. "
                "Consider publishing a Platform Event and delegating fanout to an iPaaS."
            )
    return issues


def check_apex_callouts_in_triggers_without_platform_events(manifest_dir: Path) -> list[str]:
    """Warn when Apex triggers have outbound callouts but the metadata
    does not include any Platform Event object definitions.

    This suggests that cross-system integration is happening synchronously
    inside Salesforce transactions rather than asynchronously via events.
    """
    issues: list[str] = []
    trigger_dir = manifest_dir / "triggers"
    objects_dir = manifest_dir / "objects"

    if not trigger_dir.exists():
        return issues

    # Collect trigger files with callouts
    callout_triggers: list[str] = []
    callout_pattern = re.compile(r"http\.send\s*\(", re.IGNORECASE)
    for apex_file in trigger_dir.glob("*.trigger"):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if callout_pattern.search(content):
            callout_triggers.append(apex_file.name)

    if not callout_triggers:
        return issues

    # Check whether Platform Events exist in the objects directory
    platform_event_found = False
    if objects_dir.exists():
        for obj_dir in objects_dir.iterdir():
            if obj_dir.is_dir() and obj_dir.name.endswith("__e"):
                platform_event_found = True
                break

    if callout_triggers and not platform_event_found:
        issues.append(
            f"Apex triggers with outbound callouts found ({', '.join(callout_triggers)}) "
            "but no Platform Event objects (__e) detected. "
            "For multi-system integration, publish Platform Events from triggers and "
            "delegate downstream callouts to middleware for governor-limit safety."
        )
    return issues


def check_future_methods_with_callouts(manifest_dir: Path) -> list[str]:
    """Warn when @future(callout=true) methods appear in classes that are
    called from triggers — a common workaround for callout limits that
    can indicate orchestration logic that belongs in middleware.
    """
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.exists():
        return issues

    future_callout_pattern = re.compile(
        r"@future\s*\(\s*callout\s*=\s*true\s*\)", re.IGNORECASE
    )

    flagged: list[str] = []
    for cls_file in classes_dir.glob("*.cls"):
        try:
            content = cls_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if future_callout_pattern.search(content):
            flagged.append(cls_file.name)

    if len(flagged) >= 3:
        issues.append(
            f"Found {len(flagged)} classes with @future(callout=true): "
            f"{', '.join(flagged[:5])}{'...' if len(flagged) > 5 else ''}. "
            "High count of @future callout methods may indicate orchestration logic "
            "scattered across Apex classes. Evaluate whether a middleware platform "
            "would consolidate this with better error handling and observability."
        )
    return issues


def check_missing_platform_event_replay_id_comments(manifest_dir: Path) -> list[str]:
    """Warn when Platform Event subscriptions exist in metadata but no
    replay ID persistence is evident in class comments or code.

    Missing replay ID management is a common cause of event loss when
    middleware subscribers restart.
    """
    issues: list[str] = []
    triggers_dir = manifest_dir / "triggers"
    if not triggers_dir.exists():
        return issues

    replay_id_pattern = re.compile(r"replay\s*id", re.IGNORECASE)
    event_trigger_pattern = re.compile(r"trigger\s+\w+\s+on\s+\w+__e\s*\(", re.IGNORECASE)

    for apex_file in triggers_dir.glob("*.trigger"):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if event_trigger_pattern.search(content) and not replay_id_pattern.search(content):
            issues.append(
                f"{apex_file.name}: Platform Event trigger detected but no replay ID "
                "reference found. External middleware subscribers must persist replay IDs "
                "durably to avoid event loss on restart. Ensure the middleware platform "
                "is configured to store replay position in durable storage."
            )
    return issues


def check_flow_http_callout_count(manifest_dir: Path) -> list[str]:
    """Warn when Flow metadata files contain multiple HTTP callout steps,
    suggesting that middleware-level orchestration is being built in Flow.
    """
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    if not flows_dir.exists():
        return issues

    # Simple heuristic: count occurrences of ActionCall elements that likely
    # represent HTTP callouts in Flow XML
    http_action_pattern = re.compile(
        r"<actionType>\s*(ExternalService|InvocableApex)\s*</actionType>", re.IGNORECASE
    )

    for flow_file in flows_dir.glob("*.flow-meta.xml"):
        try:
            content = flow_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        matches = http_action_pattern.findall(content)
        if len(matches) >= 3:
            issues.append(
                f"{flow_file.name}: contains {len(matches)} External Service or Invocable Apex "
                "action steps. Flows with 3+ external callout steps may be orchestrating "
                "multi-system workflows that would be more reliable and observable in middleware. "
                "Review whether this Flow is approaching the 2,000-element limit or callout budget."
            )
    return issues


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def check_middleware_integration_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_multi_callout_apex_triggers(manifest_dir))
    issues.extend(check_apex_callouts_in_triggers_without_platform_events(manifest_dir))
    issues.extend(check_future_methods_with_callouts(manifest_dir))
    issues.extend(check_missing_platform_event_replay_id_comments(manifest_dir))
    issues.extend(check_flow_http_callout_count(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_middleware_integration_patterns(manifest_dir)

    if not issues:
        print("No middleware integration anti-patterns detected.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
