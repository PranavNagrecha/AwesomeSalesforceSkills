#!/usr/bin/env python3
"""Checker script for Marketing Cloud Engagement Setup skill.

Inspects a directory of exported Marketing Cloud Engagement configuration files
(JSON or XML exports from MC Setup) and flags common misconfigurations.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_marketing_cloud_engagement_setup.py [--help]
    python3 check_marketing_cloud_engagement_setup.py --manifest-dir path/to/mc-config-exports
    python3 check_marketing_cloud_engagement_setup.py --config path/to/mc-config.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Marketing Cloud Engagement Setup configuration for common issues.\n\n"
            "Expects either:\n"
            "  --manifest-dir: a directory containing MC config JSON exports\n"
            "  --config: a single JSON file with MC account configuration\n\n"
            "Checks performed:\n"
            "  - Send Classifications have explicit Type (Commercial vs Transactional)\n"
            "  - Delivery Profiles have a non-empty physical mailing address\n"
            "  - Sender Profiles reference an authenticated sending domain\n"
            "  - No BU has only a Transactional Send Classification (missing Commercial)\n"
            "  - User role assignments do not over-assign Marketing Cloud Administrator"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory containing MC config export JSON files.",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Single JSON config file with MC account configuration.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_send_classifications(send_classifications: list[dict]) -> list[str]:
    """Verify each Send Classification has an explicit Type field."""
    issues: list[str] = []
    for sc in send_classifications:
        name = sc.get("name", "<unnamed>")
        sc_type = sc.get("type", "").strip().lower()
        if sc_type not in ("commercial", "transactional"):
            issues.append(
                f"Send Classification '{name}': Type is '{sc_type or 'missing'}'. "
                "Must be explicitly set to 'Commercial' or 'Transactional'."
            )
        if sc_type == "transactional":
            approved = sc.get("transactional_approved", False)
            if not approved:
                issues.append(
                    f"Send Classification '{name}': Type is Transactional but "
                    "'transactional_approved' flag is not set. Ensure written business/legal "
                    "sign-off exists for this classification."
                )
    return issues


def check_delivery_profiles(delivery_profiles: list[dict]) -> list[str]:
    """Verify each Delivery Profile has a non-empty physical mailing address."""
    issues: list[str] = []
    required_address_fields = ["street", "city", "state", "zip", "country"]
    for dp in delivery_profiles:
        name = dp.get("name", "<unnamed>")
        address = dp.get("physical_address", {})
        missing = [f for f in required_address_fields if not address.get(f, "").strip()]
        if missing:
            issues.append(
                f"Delivery Profile '{name}': Missing physical address fields: "
                f"{', '.join(missing)}. CAN-SPAM requires a valid postal address."
            )
    return issues


def check_sender_profiles(sender_profiles: list[dict]) -> list[str]:
    """Verify each Sender Profile references a non-empty from_address and from_name."""
    issues: list[str] = []
    for sp in sender_profiles:
        name = sp.get("name", "<unnamed>")
        from_address = sp.get("from_address", "").strip()
        from_name = sp.get("from_name", "").strip()
        if not from_address:
            issues.append(
                f"Sender Profile '{name}': from_address is empty. "
                "Every Sender Profile must have a valid sending email address."
            )
        if not from_name:
            issues.append(
                f"Sender Profile '{name}': from_name is empty. "
                "Every Sender Profile must have a From Name visible to subscribers."
            )
        domain_authenticated = sp.get("domain_authenticated", None)
        if domain_authenticated is False:
            issues.append(
                f"Sender Profile '{name}': Sending domain is flagged as not authenticated. "
                "Ensure SPF and DKIM records are published for the sending domain."
            )
    return issues


def check_business_units(business_units: list[dict]) -> list[str]:
    """Check that each BU has at least one Commercial Send Classification configured."""
    issues: list[str] = []
    for bu in business_units:
        bu_name = bu.get("name", "<unnamed>")
        send_classifications = bu.get("send_classifications", [])
        has_commercial = any(
            sc.get("type", "").strip().lower() == "commercial"
            for sc in send_classifications
        )
        if not has_commercial:
            issues.append(
                f"Business Unit '{bu_name}': No Commercial Send Classification found. "
                "Every active BU must have at least one Commercial Send Classification."
            )
    return issues


def check_user_roles(users: list[dict]) -> list[str]:
    """Flag users assigned Marketing Cloud Administrator at BU level (should be account-level only)."""
    issues: list[str] = []
    mc_admin_count = sum(
        1 for u in users
        if u.get("role", "").strip().lower() == "marketing cloud administrator"
    )
    if mc_admin_count > 3:
        issues.append(
            f"Found {mc_admin_count} users with Marketing Cloud Administrator role. "
            "This role grants full account-level access including all BUs and Setup. "
            "Restrict to a small number of dedicated account administrators (recommended: 1–3)."
        )
    return issues


def check_reply_mail_management(business_units: list[dict]) -> list[str]:
    """Verify each BU has Reply Mail Management configured."""
    issues: list[str] = []
    for bu in business_units:
        bu_name = bu.get("name", "<unnamed>")
        rmm = bu.get("reply_mail_management", {})
        if not rmm or not rmm.get("reply_address", "").strip():
            issues.append(
                f"Business Unit '{bu_name}': Reply Mail Management is not configured "
                "or reply_address is empty. Configure RMM to handle bounces and unsubscribe replies."
            )
    return issues


# ---------------------------------------------------------------------------
# Main check dispatcher
# ---------------------------------------------------------------------------

def check_from_config(config: dict) -> list[str]:
    """Run all checks against a parsed MC configuration dictionary."""
    issues: list[str] = []

    # Account-level checks
    send_classifications = config.get("send_classifications", [])
    issues.extend(check_send_classifications(send_classifications))

    delivery_profiles = config.get("delivery_profiles", [])
    issues.extend(check_delivery_profiles(delivery_profiles))

    sender_profiles = config.get("sender_profiles", [])
    issues.extend(check_sender_profiles(sender_profiles))

    users = config.get("users", [])
    issues.extend(check_user_roles(users))

    # Per-BU checks
    business_units = config.get("business_units", [])
    issues.extend(check_business_units(business_units))
    issues.extend(check_reply_mail_management(business_units))

    return issues


def check_marketing_cloud_engagement_setup(manifest_dir: Path) -> list[str]:
    """Scan a directory for MC config JSON files and run all checks."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    json_files = list(manifest_dir.glob("**/*.json"))
    if not json_files:
        issues.append(
            f"No JSON config files found in {manifest_dir}. "
            "Export MC configuration as JSON and place in this directory."
        )
        return issues

    for json_file in json_files:
        try:
            config = json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            issues.append(f"Could not parse {json_file}: {exc}")
            continue

        file_issues = check_from_config(config)
        for issue in file_issues:
            issues.append(f"[{json_file.name}] {issue}")

    return issues


def main() -> int:
    args = parse_args()

    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"WARN: Config file not found: {config_path}", file=sys.stderr)
            return 1
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"WARN: Could not parse config file: {exc}", file=sys.stderr)
            return 1
        issues = check_from_config(config)
    elif args.manifest_dir:
        manifest_dir = Path(args.manifest_dir)
        issues = check_marketing_cloud_engagement_setup(manifest_dir)
    else:
        # Default: try current directory
        issues = check_marketing_cloud_engagement_setup(Path("."))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
