#!/usr/bin/env python3
"""Checker script for Email-to-Case Configuration skill.

Inspects Salesforce metadata (retrieved via sf project retrieve or equivalent)
for common Email-to-Case configuration issues:

- Routing address missing or unverified
- On-Demand mode not enabled
- Auto-response rule From address matching a routing address (loop risk)
- Assignment rule absent (auto-response will not fire)
- Auto-response rule with no email template

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_email_to_case_configuration.py --manifest-dir path/to/metadata
    python3 check_email_to_case_configuration.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce metadata XML namespace
SF_NS = "http://soap.sforce.com/2006/04/metadata"

# On-Demand Email-to-Case total and per-attachment limits (bytes)
ON_DEMAND_TOTAL_EMAIL_LIMIT_MB = 25
ON_DEMAND_ATTACHMENT_LIMIT_MB = 10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common Email-to-Case configuration issues. "
            "Inspects Case.settings, assignment rules, and auto-response rules."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print informational notes in addition to issues.",
    )
    return parser.parse_args()


def find_xml_files(base: Path, subdir: str) -> list[Path]:
    """Return all XML files under base/subdir."""
    target = base / subdir
    if not target.is_dir():
        return []
    return sorted(target.rglob("*.xml"))


def xml_root(path: Path):
    """Parse an XML file and return the root element, or None on parse failure."""
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def text(element, *path: str) -> str:
    """Navigate a chain of child tag names and return the text of the final element."""
    current = element
    for step in path:
        if current is None:
            return ""
        current = current.find(f"{{{SF_NS}}}{step}")
    return (current.text or "").strip() if current is not None else ""


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------


def check_email_to_case_settings(manifest_dir: Path, verbose: bool) -> tuple[list[str], list[str]]:
    """Check Case.settings for Email-to-Case enabled state and routing addresses.

    Returns (issues, routing_email_addresses) so the caller can check for
    auto-response loop risk.
    """
    issues: list[str] = []
    notes: list[str] = []
    routing_emails: list[str] = []

    # Case settings live at settings/Case.settings or Case.settings-meta.xml
    candidate_paths: list[Path] = []
    settings_dir = manifest_dir / "settings"
    if settings_dir.is_dir():
        candidate_paths += list(settings_dir.glob("Case.settings"))
        candidate_paths += list(settings_dir.glob("Case.settings-meta.xml"))
    # Also search recursively in case of non-standard structure
    candidate_paths += [p for p in manifest_dir.rglob("Case.settings") if p not in candidate_paths]
    candidate_paths += [
        p for p in manifest_dir.rglob("Case.settings-meta.xml") if p not in candidate_paths
    ]

    if not candidate_paths:
        notes.append(
            "Case.settings metadata not found. "
            "Cannot verify Email-to-Case enabled state or routing address configuration. "
            "Retrieve Case.settings via: sf project retrieve --metadata Settings:Case"
        )
        if verbose:
            for note in notes:
                print(f"NOTE: {note}")
        return issues, routing_emails

    for path in candidate_paths:
        root = xml_root(path)
        if root is None:
            issues.append(f"Could not parse Case.settings: {path}")
            continue

        # Check Email-to-Case enabled
        email_to_case_enabled = text(root, "emailToCase", "enable")
        if email_to_case_enabled.lower() != "true":
            issues.append(
                "Email-to-Case is not enabled in Case.settings. "
                "Enable it at Setup → Email-to-Case before configuring routing addresses."
            )

        # Check On-Demand mode
        on_demand_enabled = text(root, "emailToCase", "enableOnDemandEmailToCase")
        if email_to_case_enabled.lower() == "true" and on_demand_enabled.lower() != "true":
            notes.append(
                "On-Demand Email-to-Case is not enabled. "
                "Standard Email-to-Case requires a locally installed Java agent and "
                "consumes API calls per email. "
                "Enable On-Demand mode unless data residency policy explicitly requires Standard."
            )

        # Check routing addresses
        routing_addresses = root.findall(
            f"{{{SF_NS}}}emailToCase/{{{SF_NS}}}routingAddresses"
        )

        if email_to_case_enabled.lower() == "true" and not routing_addresses:
            issues.append(
                "Email-to-Case is enabled but no routing addresses are configured. "
                "At least one routing address is required for inbound email to create cases."
            )

        for i, addr in enumerate(routing_addresses, start=1):
            name = text(addr, "routingName") or f"#{i}"
            email_address = text(addr, "emailAddress")

            if not email_address:
                issues.append(
                    f"Routing address '{name}': no email address configured. "
                    "Inbound emails cannot be received without an email address."
                )
            else:
                routing_emails.append(email_address.lower())

            # Check for a Salesforce-generated address (On-Demand target)
            # In metadata this is stored as emailServicesAddress or similar;
            # absence is flagged as a note since it may not always be exported.
            salesforce_address = text(addr, "emailServicesAddress")
            if on_demand_enabled.lower() == "true" and not salesforce_address:
                notes.append(
                    f"Routing address '{name}': no Salesforce-generated services address found "
                    "in metadata. Confirm the address was verified in Setup. "
                    "Unverified routing addresses silently drop inbound email."
                )

    if verbose:
        for note in notes:
            print(f"NOTE: {note}")

    return issues, routing_emails


def check_assignment_rule_active(manifest_dir: Path, verbose: bool) -> list[str]:
    """Check that an active case assignment rule exists (required for auto-response)."""
    issues: list[str] = []
    notes: list[str] = []

    candidate_paths = [
        manifest_dir / "assignmentRules" / "Case.assignmentRules",
        manifest_dir / "assignmentRules" / "Case.assignmentRules-meta.xml",
    ]
    files = [p for p in candidate_paths if p.exists()]
    if not files:
        files = find_xml_files(manifest_dir, "assignmentRules")
        files = [f for f in files if "case" in f.stem.lower()]

    if not files:
        issues.append(
            "No case assignment rule metadata found. "
            "Auto-response rules will NOT fire without an active case assignment rule. "
            "Retrieve via: sf project retrieve --metadata AssignmentRules:Case"
        )
        return issues

    active_count = 0
    for path in files:
        root = xml_root(path)
        if root is None:
            issues.append(f"Could not parse assignment rule file: {path}")
            continue
        active_val = text(root, "active")
        if active_val.lower() == "true":
            active_count += 1
            rule_entries = root.findall(f"{{{SF_NS}}}ruleEntry")
            if not rule_entries:
                issues.append(
                    f"Active assignment rule '{path.stem}' has no rule entries. "
                    "Cases will land with the default owner and auto-response will not fire."
                )

    if active_count == 0:
        issues.append(
            "No active case assignment rule found. "
            "Auto-response rules only fire when the assignment rule fires. "
            "Activate the assignment rule at Setup → Assignment Rules → Cases."
        )

    if verbose:
        for note in notes:
            print(f"NOTE: {note}")

    return issues


def check_auto_response_rules(
    manifest_dir: Path,
    routing_emails: list[str],
    verbose: bool,
) -> list[str]:
    """Check auto-response rule metadata for loop risk and missing templates."""
    issues: list[str] = []
    notes: list[str] = []

    candidate_paths = [
        manifest_dir / "autoResponseRules" / "Case.autoResponseRules",
        manifest_dir / "autoResponseRules" / "Case.autoResponseRules-meta.xml",
    ]
    files = [p for p in candidate_paths if p.exists()]
    if not files:
        files = find_xml_files(manifest_dir, "autoResponseRules")
        files = [f for f in files if "case" in f.stem.lower()]

    if not files:
        notes.append("No case auto-response rule metadata found. Skipping auto-response checks.")
        if verbose:
            for note in notes:
                print(f"NOTE: {note}")
        return issues

    for path in files:
        root = xml_root(path)
        if root is None:
            issues.append(f"Could not parse auto-response rule file: {path}")
            continue

        active_val = text(root, "active")
        if active_val.lower() != "true":
            notes.append(f"Auto-response rule '{path.stem}' is not active.")
            continue

        rule_entries = root.findall(f"{{{SF_NS}}}ruleEntry")
        for i, entry in enumerate(rule_entries, start=1):
            template = text(entry, "template")
            if not template:
                issues.append(
                    f"Auto-response rule '{path.stem}', entry {i}: "
                    "no email template assigned. "
                    "This entry will match cases but send no confirmation email."
                )

            sender_email = text(entry, "senderEmail") or text(entry, "replyToEmail") or ""
            if sender_email and routing_emails:
                if sender_email.lower() in routing_emails:
                    issues.append(
                        f"Auto-response rule '{path.stem}', entry {i}: "
                        f"sender email '{sender_email}' matches a configured Email-to-Case "
                        "routing address. This will create an email loop: auto-response → "
                        "customer inbox → customer reply → routing address → new case → "
                        "auto-response. Use a no-reply address that does not route to Salesforce."
                    )

    if verbose:
        for note in notes:
            print(f"NOTE: {note}")

    return issues


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def check_email_to_case_configuration(manifest_dir: Path, verbose: bool = False) -> list[str]:
    """Run all Email-to-Case configuration checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    setting_issues, routing_emails = check_email_to_case_settings(manifest_dir, verbose)
    issues.extend(setting_issues)

    issues.extend(check_assignment_rule_active(manifest_dir, verbose))
    issues.extend(check_auto_response_rules(manifest_dir, routing_emails, verbose))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_email_to_case_configuration(manifest_dir, verbose=args.verbose)

    if not issues:
        print("No Email-to-Case configuration issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
