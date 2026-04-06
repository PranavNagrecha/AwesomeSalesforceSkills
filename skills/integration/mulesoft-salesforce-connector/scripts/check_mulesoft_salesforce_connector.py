#!/usr/bin/env python3
"""Checker script for MuleSoft Salesforce Connector skill.

Scans Mule 4 flow XML files for common anti-patterns when integrating with Salesforce:
- Username-password auth instead of OAuth JWT Bearer
- Mule 3 watermark syntax in Mule 4 projects
- Missing error handlers on streaming subscriptions
- Hardcoded instance URLs instead of login.salesforce.com
- Watermark store before processing logic

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_mulesoft_salesforce_connector.py --manifest-dir path/to/mule-project/src/main/mule
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check MuleSoft Salesforce Connector flows for common anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing Mule 4 XML flow files (default: current directory).",
    )
    return parser.parse_args()


def find_xml_files(root: Path) -> list[Path]:
    """Recursively find all .xml files under root."""
    return sorted(root.rglob("*.xml"))


def check_username_password_auth(content: str, filepath: str) -> list[str]:
    """Detect username-password auth instead of JWT Bearer."""
    issues = []
    if re.search(r"<salesforce:basic-connection", content):
        issues.append(
            f"{filepath}: Uses username-password auth (basic-connection). "
            "Prefer OAuth 2.0 JWT Bearer (oauth-jwt-connection) for server-to-server flows."
        )
    if re.search(r'securityToken\s*=\s*"', content):
        issues.append(
            f"{filepath}: Contains securityToken parameter — indicates username-password auth. "
            "Security tokens change on every password reset, creating a brittle integration."
        )
    return issues


def check_mule3_watermark(content: str, filepath: str) -> list[str]:
    """Detect Mule 3 watermark syntax that does not exist in Mule 4."""
    issues = []
    if re.search(r"<watermark\s", content):
        issues.append(
            f"{filepath}: Contains Mule 3 <watermark> element which does not exist in Mule 4. "
            "Replace with Object Store retrieve/store pattern."
        )
    if re.search(r"<poll\s", content) and not re.search(r"<poll-connection", content):
        issues.append(
            f"{filepath}: Contains Mule 3 <poll> element. "
            "Use <scheduler> with <scheduling-strategy> in Mule 4."
        )
    if re.search(r"flowVars\.", content):
        issues.append(
            f"{filepath}: References 'flowVars.' which is Mule 3 syntax. "
            "Use 'vars.' in Mule 4."
        )
    return issues


def check_hardcoded_instance_url(content: str, filepath: str) -> list[str]:
    """Detect hardcoded Salesforce instance URLs in auth config."""
    issues = []
    pattern = r'audienceUrl\s*=\s*"https?://[a-zA-Z0-9-]+\.my\.salesforce\.com'
    if re.search(pattern, content):
        issues.append(
            f"{filepath}: audienceUrl uses an org-specific My Domain URL. "
            "Use https://login.salesforce.com (production) or https://test.salesforce.com (sandbox)."
        )
    token_pattern = r'tokenUrl\s*=\s*"https?://[a-zA-Z0-9-]+\.my\.salesforce\.com'
    if re.search(token_pattern, content):
        issues.append(
            f"{filepath}: tokenUrl uses an org-specific My Domain URL. "
            "The connector should use the generic login endpoint."
        )
    return issues


def check_streaming_error_handling(content: str, filepath: str) -> list[str]:
    """Detect streaming subscriptions without error handlers."""
    issues = []
    # Check for replay-topic or subscribe-topic sources
    has_streaming = bool(
        re.search(r"<salesforce:(replay-topic|subscribe-topic|subscribe-channel)", content)
    )
    if has_streaming:
        # Check if there is an error-handler in the same flow
        # Simple heuristic: look for <error-handler> after the streaming source
        if not re.search(r"<error-handler>", content):
            issues.append(
                f"{filepath}: Streaming subscription found without <error-handler>. "
                "Add handlers for SALESFORCE:CONNECTIVITY and SALESFORCE:INVALID_REPLAY_ID."
            )
        # Check for autoReplay and objectStore on replay-topic
        replay_match = re.search(r"<salesforce:replay-topic[^>]*>", content, re.DOTALL)
        if replay_match:
            tag = replay_match.group(0)
            if "autoReplay" not in tag and "objectStore" not in tag:
                issues.append(
                    f"{filepath}: replay-topic source missing autoReplay and objectStore-ref. "
                    "Without these, replay position is lost on application restart."
                )
    return issues


def check_watermark_before_processing(content: str, filepath: str) -> list[str]:
    """Detect watermark store that appears before processing logic."""
    issues = []
    # Find os:store for watermark-like keys
    store_positions = [m.start() for m in re.finditer(r"<os:store\s", content)]
    batch_positions = [m.start() for m in re.finditer(r"<batch:job", content)]
    foreach_positions = [m.start() for m in re.finditer(r"<foreach", content)]

    processing_positions = batch_positions + foreach_positions
    if store_positions and processing_positions:
        earliest_store = min(store_positions)
        earliest_processing = min(processing_positions)
        if earliest_store < earliest_processing:
            # Check if the store is inside a query context (after query, before processing)
            query_positions = [m.start() for m in re.finditer(r"<salesforce:query", content)]
            if query_positions:
                latest_query = max(p for p in query_positions if p < earliest_store)
                if latest_query < earliest_store < earliest_processing:
                    issues.append(
                        f"{filepath}: Object Store write appears after query but before "
                        "batch/foreach processing. Watermark should only be advanced after "
                        "successful processing to prevent data loss on failure."
                    )
    return issues


def check_bulk_api_for_high_volume(content: str, filepath: str) -> list[str]:
    """Warn if query targets typically high-volume objects without Bulk API."""
    issues = []
    high_volume_objects = [
        "Task", "Event", "CaseComment", "EmailMessage",
        "ContentVersion", "FeedItem", "ContentDocumentLink",
    ]
    for obj in high_volume_objects:
        pattern = rf"FROM\s+{obj}\b"
        if re.search(pattern, content, re.IGNORECASE):
            if not re.search(r"(bulk|Bulk|BULK)", content):
                issues.append(
                    f"{filepath}: Queries high-volume object '{obj}' without Bulk API. "
                    "Consider enabling Bulk API for objects that commonly exceed 10,000 records."
                )
    return issues


def check_mulesoft_salesforce_connector(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    xml_files = find_xml_files(manifest_dir)
    if not xml_files:
        issues.append(f"No XML files found in {manifest_dir}. Is this a Mule project directory?")
        return issues

    salesforce_files_found = False

    for xml_file in xml_files:
        try:
            content = xml_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        # Only check files that reference the Salesforce connector
        if "salesforce:" not in content and "sfdc" not in content.lower():
            continue

        salesforce_files_found = True
        filepath = str(xml_file)

        issues.extend(check_username_password_auth(content, filepath))
        issues.extend(check_mule3_watermark(content, filepath))
        issues.extend(check_hardcoded_instance_url(content, filepath))
        issues.extend(check_streaming_error_handling(content, filepath))
        issues.extend(check_watermark_before_processing(content, filepath))
        issues.extend(check_bulk_api_for_high_volume(content, filepath))

    if not salesforce_files_found:
        issues.append(
            "No Mule XML files referencing the Salesforce connector found. "
            "Verify --manifest-dir points to the Mule project's src/main/mule directory."
        )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_mulesoft_salesforce_connector(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
