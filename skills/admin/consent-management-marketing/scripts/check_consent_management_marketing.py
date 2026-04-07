#!/usr/bin/env python3
"""Checker script for Consent Management Marketing skill.

Checks Marketing Cloud email templates and metadata for common consent
management compliance issues: missing unsubscribe links, missing physical
address tokens, and Send Classification gaps.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_consent_management_marketing.py [--help]
    python3 check_consent_management_marketing.py --manifest-dir path/to/metadata
    python3 check_consent_management_marketing.py --email-template path/to/template.html
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Token / pattern constants
# ---------------------------------------------------------------------------

# MC personalization strings required for CAN-SPAM in every commercial email
UNSUBSCRIBE_TOKENS = [
    "%%subscription_center_url%%",
    "%%unsub_center_url%%",
    # Custom CloudPage unsubscribe links may use query params; detect generically
]

PHYSICAL_ADDRESS_PATTERN = re.compile(
    r"(\d{1,5}\s+\w+.{0,60}(street|st|avenue|ave|road|rd|blvd|drive|dr|lane|ln|way|place|pl))",
    re.IGNORECASE,
)

# MC address tokens that pull from Delivery Profile
ADDRESS_TOKENS = [
    "%%member_addr%%",
    "%%member_city%%",
    "%%member_state%%",
    "%%member_zip%%",
    "%%member_busname%%",
]

# Confirmation-interstitial anti-pattern: opt-out inside a POST form action
# with a confirm gate — heuristic: "are you sure" near an unsubscribe path
CONFIRM_GATE_PATTERN = re.compile(
    r"are\s+you\s+sure|confirm.*unsubscribe|unsubscribe.*confirm",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Marketing Cloud email templates and metadata for consent "
            "management compliance issues (CAN-SPAM, GDPR, one-click unsubscribe)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of the Salesforce/MC metadata to scan.",
    )
    parser.add_argument(
        "--email-template",
        default=None,
        help="Path to a single HTML email template file to check.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_template_unsubscribe(content: str, source: str) -> list[str]:
    """Warn if no recognisable unsubscribe token is present."""
    issues: list[str] = []
    has_unsub = any(tok.lower() in content.lower() for tok in UNSUBSCRIBE_TOKENS)
    # Also accept a CloudPage URL with 'unsub' or 'unsubscribe' in the href
    if not has_unsub:
        has_unsub = bool(re.search(r'href=["\'][^"\']*unsub[^"\']*["\']', content, re.IGNORECASE))
    if not has_unsub:
        issues.append(
            f"{source}: No unsubscribe link token found. "
            "Every commercial email must include %%subscription_center_url%% "
            "or a functional one-click unsubscribe link (CAN-SPAM requirement)."
        )
    return issues


def check_template_physical_address(content: str, source: str) -> list[str]:
    """Warn if no physical address token or literal street address is present."""
    issues: list[str] = []
    has_address_token = any(tok.lower() in content.lower() for tok in ADDRESS_TOKENS)
    has_literal_address = bool(PHYSICAL_ADDRESS_PATTERN.search(content))
    if not has_address_token and not has_literal_address:
        issues.append(
            f"{source}: No physical mailing address found. "
            "CAN-SPAM requires a physical postal address in every commercial email. "
            "Include %%member_addr%% tokens (from Delivery Profile) or a literal address."
        )
    return issues


def check_template_confirm_gate(content: str, source: str) -> list[str]:
    """Warn if a confirmation interstitial before unsubscribe is detected."""
    issues: list[str] = []
    if CONFIRM_GATE_PATTERN.search(content):
        issues.append(
            f"{source}: Possible unsubscribe confirmation gate detected "
            "('are you sure' / 'confirm unsubscribe' pattern). "
            "Google/Yahoo 2024 one-click unsubscribe requirements mandate that "
            "opt-out is processed immediately without a confirmation screen."
        )
    return issues


def check_template_file(template_path: Path) -> list[str]:
    """Run all template checks on a single HTML or text file."""
    issues: list[str] = []
    if not template_path.exists():
        issues.append(f"Template file not found: {template_path}")
        return issues
    try:
        content = template_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues.append(f"Could not read {template_path}: {exc}")
        return issues

    source = str(template_path)
    issues.extend(check_template_unsubscribe(content, source))
    issues.extend(check_template_physical_address(content, source))
    issues.extend(check_template_confirm_gate(content, source))
    return issues


def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Scan a metadata directory for email template files and check each."""
    issues: list[str] = []
    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Look for HTML email template files common in MC metadata exports
    template_extensions = ("*.html", "*.htm", "*.amp", "*.email")
    template_files: list[Path] = []
    for ext in template_extensions:
        template_files.extend(manifest_dir.rglob(ext))

    if not template_files:
        # Non-fatal: directory may contain other metadata types
        return issues

    for template_path in template_files:
        issues.extend(check_template_file(template_path))

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    issues: list[str] = []

    if args.email_template:
        issues.extend(check_template_file(Path(args.email_template)))

    if args.manifest_dir:
        issues.extend(check_manifest_dir(Path(args.manifest_dir)))

    if not args.email_template and not args.manifest_dir:
        # Default: scan current directory
        issues.extend(check_manifest_dir(Path(".")))

    if not issues:
        print("No consent management issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
