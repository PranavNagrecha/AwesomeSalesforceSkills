#!/usr/bin/env python3
"""Checker script for Email Studio Administration skill.

Validates email send configuration files and work templates for common
Email Studio setup issues: missing Send Classification, unconfigured dynamic
content defaults, A/B test audience sizing, and Triggered Send activation.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_email_studio_administration.py [--help]
    python3 check_email_studio_administration.py --manifest-dir path/to/work
    python3 check_email_studio_administration.py --template path/to/template.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Email Studio Administration configuration and work templates "
            "for common issues: missing Send Classification, unconfigured dynamic "
            "content defaults, A/B test sizing problems, and Triggered Send "
            "activation status."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of the work artifacts (default: current directory).",
    )
    parser.add_argument(
        "--template",
        default=None,
        help="Path to a filled work template (.md) to validate.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------

def check_send_classification_present(text: str) -> list[str]:
    """Warn if Send Classification field is unfilled."""
    issues = []
    # Look for the Send Classification name line
    match = re.search(r"\*\*Send Classification name:\*\*\s*(.*)", text)
    if match:
        value = match.group(1).strip()
        if not value or value.startswith("("):
            issues.append(
                "Send Classification name is not filled in the template. "
                "Every send requires an explicit Send Classification."
            )
    return issues


def check_legal_classification_confirmed(text: str) -> list[str]:
    """Warn if Commercial vs Transactional is undecided."""
    issues = []
    match = re.search(r"\*\*Legal classification confirmed:\*\*\s*(.*)", text)
    if match:
        value = match.group(1).strip().lower()
        if not value or value.startswith("("):
            issues.append(
                "Legal classification (Commercial / Transactional) is not confirmed. "
                "Determine this before any other configuration step."
            )
        if "transactional" in value:
            # Soft warning: encourage review of content
            issues.append(
                "REVIEW: Send is marked Transactional. Confirm email content qualifies "
                "(no promotional offers, primary purpose is transaction facilitation). "
                "Misusing Transactional classification for commercial sends violates CAN-SPAM."
            )
    return issues


def check_canspam_footer(text: str) -> list[str]:
    """Warn if CAN-SPAM footer field is inconsistent with classification."""
    issues = []
    classification_match = re.search(
        r"\*\*Legal classification confirmed:\*\*\s*(.*)", text
    )
    footer_match = re.search(r"\*\*CAN-SPAM footer:\*\*\s*(.*)", text)

    if classification_match and footer_match:
        classification = classification_match.group(1).strip().lower()
        footer = footer_match.group(1).strip().lower()

        if "commercial" in classification and "no" in footer:
            issues.append(
                "CAN-SPAM footer is marked 'No' but classification is Commercial. "
                "Commercial sends require a CAN-SPAM-compliant footer with physical "
                "mailing address and unsubscribe link."
            )
        if "transactional" in classification and "yes" in footer and "required" not in footer:
            # Not an error — transactional can have a footer — but note it
            issues.append(
                "INFO: Transactional send has CAN-SPAM footer marked 'Yes'. "
                "Verify the footer content does not include a global unsubscribe link "
                "that would incorrectly trigger commercial opt-out for transactional messages."
            )
    return issues


def check_dynamic_content_defaults(text: str) -> list[str]:
    """Warn if dynamic content table rows lack a default variation."""
    issues = []
    # Find the dynamic content table
    table_match = re.search(
        r"\| Block Name \|.*?\n(.*?)(?:\n\n|\Z)", text, re.DOTALL
    )
    if table_match:
        table_body = table_match.group(1)
        for line in table_body.splitlines():
            if line.startswith("|") and "---" not in line and "Block Name" not in line:
                cols = [c.strip() for c in line.split("|") if c.strip()]
                if cols:
                    block_name = cols[0]
                    if len(cols) < 5:
                        continue  # Not enough columns to check
                    default_col = cols[-1]
                    if not default_col or default_col.startswith("("):
                        issues.append(
                            f"Dynamic content block '{block_name}' is missing a "
                            "default variation. Every block must have a default to "
                            "cover subscribers matching no rule."
                        )
    return issues


def check_ab_test_audience_size(text: str) -> list[str]:
    """Warn if A/B test evaluation window or audience sizing fields are unfilled."""
    issues = []
    # Check if A/B section is present and evaluation window is filled
    if "A/B Test Configuration" in text:
        window_match = re.search(r"\*\*Evaluation window:\*\*\s*(.*)", text)
        if window_match:
            window_val = window_match.group(1).strip()
            if window_val.startswith("(") or not window_val:
                issues.append(
                    "A/B test evaluation window is not set. "
                    "An unset window may default to platform minimum; "
                    "small lists need longer windows to accumulate open events."
                )

        min_opens_match = re.search(
            r"Minimum open events per arm to trust the result:\*\*\s*(.*)", text
        )
        if min_opens_match:
            opens_val = min_opens_match.group(1).strip()
            if opens_val.startswith("(") or not opens_val:
                issues.append(
                    "Minimum open events per arm is not calculated. "
                    "Target 300–500 open events per test arm within the evaluation "
                    "window. Use historical open rate to calculate required audience size."
                )
    return issues


def check_triggered_send_activation(text: str) -> list[str]:
    """Warn if send type is Triggered but activation status is not confirmed."""
    issues = []
    send_type_match = re.search(r"\*\*Send type:\*\*\s*(.*)", text)
    if send_type_match:
        send_type = send_type_match.group(1).strip().lower()
        if "triggered" in send_type:
            # Check for the activation checklist item
            activation_checked = bool(
                re.search(
                    r"-\s+\[x\].*Triggered Send.*definition status confirmed as.*Active",
                    text,
                    re.IGNORECASE,
                )
            )
            if not activation_checked:
                issues.append(
                    "Send type is Triggered but the checklist item confirming "
                    "Triggered Send Definition status as 'Active' is not checked. "
                    "A definition in 'Building' status silently drops all triggers."
                )
    return issues


def check_suppression_lists(text: str) -> list[str]:
    """Warn if suppression checklist items are unchecked."""
    issues = []
    suppression_checks = [
        (
            r"-\s+\[.\]\s+Auto-suppression active",
            "Auto-suppression (bounces, global unsubscribes, spam complaints) is not confirmed.",
        ),
        (
            r"-\s+\[.\]\s+Global Suppression List reviewed",
            "Global Suppression List review is not confirmed. "
            "Confirm GSL is active and address count is reviewed before send.",
        ),
    ]
    for pattern, message in suppression_checks:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Check if the box is checked (x) vs unchecked (space)
            line = match.group(0)
            if "[ ]" in line:
                issues.append(message)
    return issues


def check_content_detective(text: str) -> list[str]:
    """Warn if Content Detective result is not recorded."""
    issues = []
    detective_match = re.search(
        r"Content Detective run.*spam score result:\s*(.*)", text, re.IGNORECASE
    )
    if detective_match:
        score_val = detective_match.group(1).strip()
        if not score_val or score_val in ("____", ""):
            issues.append(
                "Content Detective spam score result is not recorded. "
                "Run Content Detective before finalizing the pre-send validation."
            )
    return issues


# ---------------------------------------------------------------------------
# File-level checks
# ---------------------------------------------------------------------------

def check_template_file(template_path: Path) -> list[str]:
    """Run all template checks on a filled work template markdown file."""
    issues: list[str] = []

    if not template_path.exists():
        issues.append(f"Template file not found: {template_path}")
        return issues

    text = template_path.read_text(encoding="utf-8")

    issues.extend(check_send_classification_present(text))
    issues.extend(check_legal_classification_confirmed(text))
    issues.extend(check_canspam_footer(text))
    issues.extend(check_dynamic_content_defaults(text))
    issues.extend(check_ab_test_audience_size(text))
    issues.extend(check_triggered_send_activation(text))
    issues.extend(check_suppression_lists(text))
    issues.extend(check_content_detective(text))

    return issues


def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Scan a directory for filled work templates and check each one."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    template_files = list(manifest_dir.glob("**/*.md"))
    if not template_files:
        issues.append(
            f"No .md files found in {manifest_dir}. "
            "Expected at least one filled work template."
        )
        return issues

    for tf in template_files:
        # Only check files that look like work templates (contain the skill name)
        content = tf.read_text(encoding="utf-8")
        if "email-studio-administration" in content.lower() or "email studio" in content.lower():
            file_issues = check_template_file(tf)
            for issue in file_issues:
                issues.append(f"[{tf.name}] {issue}")

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    issues: list[str] = []

    if args.template:
        template_path = Path(args.template)
        issues.extend(check_template_file(template_path))
    elif args.manifest_dir:
        manifest_dir = Path(args.manifest_dir)
        issues.extend(check_manifest_dir(manifest_dir))
    else:
        # Default: check current directory for work templates
        manifest_dir = Path(".")
        issues.extend(check_manifest_dir(manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
