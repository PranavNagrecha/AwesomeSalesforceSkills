#!/usr/bin/env python3
"""Checker script for Transaction Security Policies skill.

Validates Salesforce metadata for Transaction Security Policy configuration issues.
Parses TransactionSecurityPolicy XML files for common anti-patterns described
in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_transaction_security.py [--help]
    python3 check_transaction_security.py --manifest-dir path/to/metadata
    python3 check_transaction_security.py --manifest-dir force-app/main/default

Checks performed:
  1. TransactionSecurityPolicy files — warns on event types that do not support policies
  2. TransactionSecurityPolicy files — flags policies that are in Monitor (inactive) mode
  3. TransactionSecurityPolicy files — warns if no execution user element is present
  4. TransactionSecurityPolicy files — flags Block actions with no block message
  5. General — warns if no TransactionSecurityPolicy metadata is found at all
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Event type classification
# ---------------------------------------------------------------------------

# RTEM event types confirmed to support Transaction Security Policy enforcement.
# Source: Salesforce Platform Events Developer Guide —
#   "Can Be Used in a Transaction Security Policy?" column
POLICY_SUPPORTED_EVENTS: frozenset[str] = frozenset(
    {
        "ApiAnomalyEvent",
        "ApiEventStream",
        "BulkApiResultEvent",
        "ConnectedApplication",
        "CredentialStuffingEvent",
        "FileEvent",
        "GuestUserAnomalyEvent",
        "ListViewEvent",
        "ListViewEventStream",
        "LoginAnomalyEvent",
        "LoginAsEvent",
        "LoginAsEventStream",
        "LoginEvent",
        "LoginEventStream",
        "LogoutEvent",
        "LogoutEventStream",
        "PermissionSetEvent",
        "ReportAnomalyEvent",
        "ReportEvent",
        "ReportEventStream",
        "SessionHijackingEvent",
        "UriEventStream",
    }
)

# RTEM event types explicitly confirmed NOT to support Transaction Security Policies.
# Policies on these event types silently never evaluate.
POLICY_UNSUPPORTED_EVENTS: frozenset[str] = frozenset(
    {
        "ConcurLongRunApexErrEvent",
        "IdentityProviderEvent",
        "IdentityVerificationEvent",
        "MobileEmailEvent",
        "MobileEnforcedPolicyEvent",
        "MobileScreenshotEvent",
        "MobileTelephonyEvent",
    }
)


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------


def _extract_xml_value(content: str, tag: str) -> str | None:
    """Extract the text content of the first occurrence of a simple XML element.

    Returns None if the tag is not found.
    """
    pattern = rf"<{re.escape(tag)}\s*>(.*?)</{re.escape(tag)}>"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def _extract_all_xml_values(content: str, tag: str) -> list[str]:
    """Extract the text content of all occurrences of a simple XML element."""
    pattern = rf"<{re.escape(tag)}\s*>(.*?)</{re.escape(tag)}>"
    return [m.group(1).strip() for m in re.finditer(pattern, content, re.DOTALL)]


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def check_event_type_support(path: Path, content: str) -> list[str]:
    """Flag policies whose event type does not support enforcement."""
    issues: list[str] = []
    event_type = _extract_xml_value(content, "eventType")

    if event_type is None:
        issues.append(
            f"WARN {path.name}: TransactionSecurityPolicy is missing <eventType> element. "
            "The policy cannot evaluate without an event type."
        )
        return issues

    if event_type in POLICY_UNSUPPORTED_EVENTS:
        issues.append(
            f"HIGH {path.name}: eventType='{event_type}' does NOT support Transaction Security "
            "Policy enforcement. This policy will silently never fire regardless of its Active "
            "flag or condition logic. Remove or retype this policy against a supported event type. "
            f"Supported types include: {', '.join(sorted(POLICY_SUPPORTED_EVENTS)[:6])}..."
        )
    elif event_type not in POLICY_SUPPORTED_EVENTS:
        issues.append(
            f"WARN {path.name}: eventType='{event_type}' is not in the confirmed "
            "policy-supported event type list. Verify this event type supports Transaction "
            "Security Policy enforcement in the Salesforce Platform Events Developer Guide "
            "before deploying."
        )

    return issues


def check_active_flag(path: Path, content: str) -> list[str]:
    """Warn on policies that are inactive (Monitor mode only)."""
    issues: list[str] = []
    active = _extract_xml_value(content, "active")

    if active is None:
        issues.append(
            f"WARN {path.name}: TransactionSecurityPolicy is missing <active> element. "
            "The policy may default to inactive (Monitor mode). Explicitly set <active>true</active> "
            "to enable enforcement, or <active>false</active> for Monitor mode."
        )
    elif active.lower() == "false":
        issues.append(
            f"INFO {path.name}: Policy is in Monitor mode (<active>false</active>). "
            "No enforcement actions will fire. This is expected during validation; "
            "switch to <active>true</active> to enable enforcement."
        )

    return issues


def check_execution_user(path: Path, content: str) -> list[str]:
    """Warn if no execution user is set on the policy."""
    issues: list[str] = []
    execution_user = _extract_xml_value(content, "executionUser")

    if execution_user is None or execution_user.strip() == "":
        issues.append(
            f"HIGH {path.name}: TransactionSecurityPolicy has no <executionUser> set. "
            "Policies without an execution user do not evaluate. "
            "Set <executionUser> to an active user ID or username."
        )

    return issues


def check_block_action_message(path: Path, content: str) -> list[str]:
    """Warn on Block actions that have no custom block message configured."""
    issues: list[str] = []

    # Check if any action has type=Block
    action_blocks = re.findall(
        r"<action>(.*?)</action>", content, re.DOTALL
    )
    for action_block in action_blocks:
        action_type = _extract_xml_value(action_block, "type")
        block_message = _extract_xml_value(action_block, "blockMessage")

        if action_type == "Block":
            if block_message is None or block_message.strip() == "":
                issues.append(
                    f"WARN {path.name}: Policy has a Block action but no <blockMessage> is "
                    "configured. Users who are blocked will see a generic platform error "
                    "rather than an actionable message. Add a <blockMessage> that explains "
                    "the restriction and how to seek assistance."
                )
            break  # Only report once per policy

    return issues


def check_apex_policy_flag(path: Path, content: str) -> list[str]:
    """Inform when a policy uses legacy Apex (apexPolicy=true) rather than Condition Builder."""
    issues: list[str] = []
    apex_policy = _extract_xml_value(content, "apexPolicy")

    if apex_policy is not None and apex_policy.lower() == "true":
        issues.append(
            f"INFO {path.name}: Policy uses legacy Apex (apexPolicy=true). "
            "Apex-based policies require the execution user to have 'Author Apex' permission. "
            "Consider migrating to Enhanced Condition Builder (apexPolicy=false) if the "
            "condition logic can be expressed without custom code. "
            "Verify the referenced PolicyCondition Apex class compiles without errors."
        )

    return issues


# ---------------------------------------------------------------------------
# Directory-level check
# ---------------------------------------------------------------------------


def check_for_any_policies(manifest_dir: Path) -> list[str]:
    """Warn if no TransactionSecurityPolicy metadata is found in the manifest."""
    issues: list[str] = []
    policy_files = list(manifest_dir.rglob("*.transactionSecurityPolicy"))

    if not policy_files:
        issues.append(
            "INFO: No TransactionSecurityPolicy metadata found "
            f"(searched '{manifest_dir}' recursively for *.transactionSecurityPolicy). "
            "If this org uses Transaction Security, retrieve the metadata with: "
            "sf project retrieve start -m TransactionSecurityPolicy"
        )

    return issues


# ---------------------------------------------------------------------------
# Main dispatch
# ---------------------------------------------------------------------------


def check_transaction_security(manifest_dir: Path) -> list[str]:
    """Run all Transaction Security Policy checks. Returns list of issue strings."""
    if not manifest_dir.exists():
        return [f"HIGH: Manifest directory not found: {manifest_dir}"]

    issues: list[str] = []
    policy_files = list(manifest_dir.rglob("*.transactionSecurityPolicy"))

    for path in policy_files:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            issues.append(f"WARN {path.name}: could not read file — skipping.")
            continue

        issues.extend(check_event_type_support(path, content))
        issues.extend(check_active_flag(path, content))
        issues.extend(check_execution_user(path, content))
        issues.extend(check_block_action_message(path, content))
        issues.extend(check_apex_policy_flag(path, content))

    issues.extend(check_for_any_policies(manifest_dir))
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Transaction Security Policy configuration issues. "
            "Validates .transactionSecurityPolicy XML files against known anti-patterns "
            "including unsupported event types, Monitor-mode policies, missing execution users, "
            "and Block actions without messages."
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
    issues = check_transaction_security(manifest_dir)

    high_count = sum(1 for i in issues if i.startswith("HIGH"))
    warn_count = sum(1 for i in issues if i.startswith("WARN"))
    info_count = sum(1 for i in issues if i.startswith("INFO"))

    if not issues:
        print("No Transaction Security Policy issues found.")
        return 0

    for issue in issues:
        print(issue)

    print()
    print(
        f"Summary: {high_count} HIGH, {warn_count} WARN, {info_count} INFO "
        f"({len(issues)} total)"
    )

    return 1 if high_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
