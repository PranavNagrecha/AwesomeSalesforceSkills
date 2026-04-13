#!/usr/bin/env python3
"""Checker script for Idempotent Integration Patterns skill.

Checks Salesforce metadata and Apex code for common idempotency anti-patterns:
  - External ID fields missing the unique constraint
  - Platform Events with Publish Behavior set to "PublishImmediately"
  - Apex files that generate idempotency keys inside execute() methods (retry path)
  - EventBus.publish() calls co-located with DML without a Publish After Commit note

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_idempotent_integration_patterns.py [--help]
    python3 check_idempotent_integration_patterns.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Idempotent Integration Patterns configuration and metadata "
            "for common issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Check 1: External ID fields without unique constraint
# ---------------------------------------------------------------------------

def check_external_id_fields_missing_unique(manifest_dir: Path) -> list[str]:
    """Return issues for External ID fields that lack <unique>true</unique>."""
    issues: list[str] = []

    # Object metadata files contain field definitions inline
    object_files = list(manifest_dir.rglob("*.object-meta.xml"))
    # Field metadata files (decomposed format)
    field_files = list(manifest_dir.rglob("*.field-meta.xml"))

    all_files = object_files + field_files

    ext_id_pattern = re.compile(r"<externalId>\s*true\s*</externalId>", re.IGNORECASE)
    unique_pattern = re.compile(r"<unique>\s*true\s*</unique>", re.IGNORECASE)

    for path in all_files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if not ext_id_pattern.search(content):
            continue

        # The file (or a field block within it) declares externalId=true.
        # Check whether <unique>true</unique> is also present.
        if not unique_pattern.search(content):
            issues.append(
                f"External ID field without unique constraint — {path}: "
                "Add <unique>true</unique> alongside <externalId>true</externalId>. "
                "Without unique, upsert retries can produce MULTIPLE_CHOICES (300) errors."
            )

    return issues


# ---------------------------------------------------------------------------
# Check 2: Platform Events with PublishImmediately behavior
# ---------------------------------------------------------------------------

def check_platform_event_publish_behavior(manifest_dir: Path) -> list[str]:
    """Return issues for Platform Events using PublishImmediately publish behavior."""
    issues: list[str] = []

    event_files = list(manifest_dir.rglob("*.object-meta.xml"))

    # PublishImmediately is the default and must be changed to PublishAfterCommit
    # for transactional safety.  Some deployments explicitly set PublishImmediately.
    publish_immediate_pattern = re.compile(
        r"<publishBehavior>\s*PublishImmediately\s*</publishBehavior>",
        re.IGNORECASE,
    )
    # Platform Event objects have <eventType> in their metadata
    event_type_pattern = re.compile(r"<eventType>", re.IGNORECASE)

    for path in event_files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if not event_type_pattern.search(content):
            continue  # Not a Platform Event object file

        if publish_immediate_pattern.search(content):
            issues.append(
                f"Platform Event uses PublishImmediately — {path}: "
                "Change <publishBehavior> to PublishAfterCommit for transactional "
                "event patterns. PublishImmediately fires before the publishing "
                "transaction commits, allowing phantom events if the transaction rolls back."
            )

    return issues


# ---------------------------------------------------------------------------
# Check 3: Apex files with key generation inside execute() — retry path
# ---------------------------------------------------------------------------

_KEY_GEN_PATTERNS = [
    re.compile(r"Crypto\.generateAesKey\s*\(", re.IGNORECASE),
    re.compile(r"EncodingUtil\.convertToHex\s*\(\s*Crypto\.", re.IGNORECASE),
    re.compile(r"Math\.random\s*\(", re.IGNORECASE),
    # UUID generation via a utility class commonly named UUIDUtil or similar
    re.compile(r"UUID\.randomUUID\s*\(", re.IGNORECASE),
]

# Patterns that indicate we are inside an execute() or process() method body
_EXECUTE_METHOD_PATTERN = re.compile(
    r"\bpublic\s+void\s+execute\s*\(", re.IGNORECASE
)


def check_apex_idempotency_key_in_execute(manifest_dir: Path) -> list[str]:
    """Return issues for Apex files that generate keys inside execute() methods."""
    issues: list[str] = []

    apex_files = list(manifest_dir.rglob("*.cls"))

    for path in apex_files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if not _EXECUTE_METHOD_PATTERN.search(content):
            continue  # No execute() method in this file

        for pattern in _KEY_GEN_PATTERNS:
            if pattern.search(content):
                issues.append(
                    f"Possible idempotency key regeneration in execute() — {path}: "
                    "Key-generation code ({}) found in a file containing an execute() method. "
                    "If the key is generated inside execute() rather than at enqueue time, "
                    "each retry produces a new key and the external system processes all "
                    "attempts as distinct requests. Move key generation to the enqueue path "
                    "and persist the key to a record field before the first callout.".format(
                        pattern.pattern
                    )
                )
                break  # One issue per file is enough

    return issues


# ---------------------------------------------------------------------------
# Check 4: EventBus.publish() in DML-containing Apex without Publish After Commit note
# ---------------------------------------------------------------------------

_EVENTBUS_PUBLISH_PATTERN = re.compile(r"\bEventBus\.publish\s*\(", re.IGNORECASE)
_DML_PATTERN = re.compile(
    r"\b(insert|update|upsert|delete|Database\.(insert|update|upsert|delete))\b",
    re.IGNORECASE,
)
_PUBLISH_AFTER_COMMIT_COMMENT = re.compile(
    r"Publish\s*After\s*Commit",
    re.IGNORECASE,
)


def check_apex_eventbus_without_publish_after_commit_note(
    manifest_dir: Path,
) -> list[str]:
    """Warn when EventBus.publish() and DML coexist without a Publish After Commit note."""
    issues: list[str] = []

    apex_files = list(manifest_dir.rglob("*.cls"))

    for path in apex_files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if not _EVENTBUS_PUBLISH_PATTERN.search(content):
            continue

        if not _DML_PATTERN.search(content):
            continue  # No DML present alongside the publish call

        if _PUBLISH_AFTER_COMMIT_COMMENT.search(content):
            continue  # Developer has already noted the setting

        issues.append(
            f"EventBus.publish() with DML and no Publish After Commit note — {path}: "
            "This file calls EventBus.publish() alongside DML statements. "
            "Verify that the Platform Event's Publish Behavior is set to "
            "PublishAfterCommit in Setup → Platform Events → [Event] → Edit. "
            "The default PublishImmediately setting can fire events for transactions "
            "that subsequently roll back."
        )

    return issues


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def check_idempotent_integration_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_external_id_fields_missing_unique(manifest_dir))
    issues.extend(check_platform_event_publish_behavior(manifest_dir))
    issues.extend(check_apex_idempotency_key_in_execute(manifest_dir))
    issues.extend(check_apex_eventbus_without_publish_after_commit_note(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_idempotent_integration_patterns(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
