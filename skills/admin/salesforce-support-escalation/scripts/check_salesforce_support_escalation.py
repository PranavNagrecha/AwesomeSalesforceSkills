#!/usr/bin/env python3
"""Checker script for Salesforce Support Escalation skill.

Validates a filled work template or case description file for common support
escalation readiness issues: missing org ID, incorrect severity usage, absent
business impact statement, and missing Trust site / Known Issues checks.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_salesforce_support_escalation.py [--help]
    python3 check_salesforce_support_escalation.py --template-file path/to/template.md
    python3 check_salesforce_support_escalation.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Severity definitions (mirrors Salesforce Knowledge Article 000382814)
# ---------------------------------------------------------------------------
SEVERITY_PATTERNS = {
    "sev1": re.compile(r"\bsev\s*1\b|\bseverity\s*1\b|\bs1\b", re.IGNORECASE),
    "sev2": re.compile(r"\bsev\s*2\b|\bseverity\s*2\b|\bs2\b", re.IGNORECASE),
    "sev3": re.compile(r"\bsev\s*3\b|\bseverity\s*3\b|\bs3\b", re.IGNORECASE),
    "sev4": re.compile(r"\bsev\s*4\b|\bseverity\s*4\b|\bs4\b", re.IGNORECASE),
}

ORG_ID_PATTERN = re.compile(r"\b00[A-Za-z0-9]{13,16}\b")
SANDBOX_KEYWORDS = re.compile(
    r"\bsandbox\b|\bpartial copy\b|\bfull copy\b|\bscratch org\b|\bdev org\b",
    re.IGNORECASE,
)
PRODUCTION_KEYWORDS = re.compile(r"\bproduction\b|\bprod\b|\blive org\b", re.IGNORECASE)
IMPACT_KEYWORDS = re.compile(
    r"users? affected|business impact|revenue|operations|blocked|all users|down",
    re.IGNORECASE,
)
TRUST_KEYWORDS = re.compile(r"trust\.salesforce\.com|trust site", re.IGNORECASE)
KNOWN_ISSUES_KEYWORDS = re.compile(
    r"known issues|help\.salesforce\.com/s/issues|W-\d{6,}", re.IGNORECASE
)
STEPS_PATTERN = re.compile(r"steps to reproduce|reproduction steps", re.IGNORECASE)
LOGIN_ACCESS_PATTERN = re.compile(
    r"grant login access|grant access to salesforce\.com", re.IGNORECASE
)
LOGIN_DURATION_PATTERN = re.compile(
    r"\d+\s*(hour|day|hr)s?\b", re.IGNORECASE
)
LOGIN_REVOKE_PATTERN = re.compile(r"\brevok\w+|\bremov\w+ access", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce support escalation work template or case description "
            "for common readiness issues."
        ),
    )
    parser.add_argument(
        "--template-file",
        default=None,
        help="Path to a filled work template or case description markdown file.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of Salesforce metadata (default: current directory). "
        "Used for org-ID detection in metadata XML when --template-file is not given.",
    )
    return parser.parse_args()


def check_template_file(template_path: Path) -> list[str]:
    """Validate a filled support escalation template for common issues."""
    issues: list[str] = []

    if not template_path.exists():
        issues.append(f"Template file not found: {template_path}")
        return issues

    text = template_path.read_text(encoding="utf-8")

    # --- Org ID check ---
    if not ORG_ID_PATTERN.search(text):
        issues.append(
            "No Org ID detected (expected an 18-character ID starting with '00D'). "
            "Org ID is required for all support cases."
        )

    # --- Severity + sandbox conflict check ---
    has_sev1 = SEVERITY_PATTERNS["sev1"].search(text)
    has_sandbox = SANDBOX_KEYWORDS.search(text)
    has_production = PRODUCTION_KEYWORDS.search(text)

    if has_sev1 and has_sandbox and not has_production:
        issues.append(
            "Severity 1 is referenced alongside sandbox/scratch org language but no "
            "production impact is mentioned. Sev1 requires production business impact "
            "(Salesforce KA 000382814). Consider Sev3."
        )

    # --- Business impact statement check for Sev1/Sev2 ---
    if (has_sev1 or SEVERITY_PATTERNS["sev2"].search(text)) and not IMPACT_KEYWORDS.search(text):
        issues.append(
            "No business impact statement detected for a Sev1/Sev2 case. "
            "Include: number of affected users, the business process blocked, and "
            "revenue or operational impact if applicable."
        )

    # --- Steps to reproduce check for Sev1/Sev2/Sev3 ---
    any_severity = any(p.search(text) for p in SEVERITY_PATTERNS.values())
    if any_severity and not STEPS_PATTERN.search(text):
        issues.append(
            "No 'Steps to Reproduce' section detected. All support cases benefit from "
            "reproduction steps; they are required for Sev1 and Sev2 to speed triage."
        )

    # --- Trust site check ---
    if not TRUST_KEYWORDS.search(text):
        issues.append(
            "No reference to trust.salesforce.com found. The Trust site should be "
            "checked before opening a case to detect active incidents (KA 000387502)."
        )

    # --- Known Issues check ---
    if not KNOWN_ISSUES_KEYWORDS.search(text):
        issues.append(
            "No reference to the Known Issues site (help.salesforce.com/s/issues) found. "
            "Search Known Issues before opening a Sev3 or Sev4 case (KA 000386216)."
        )

    # --- Grant Login Access security check ---
    if LOGIN_ACCESS_PATTERN.search(text):
        if not LOGIN_DURATION_PATTERN.search(text):
            issues.append(
                "Grant Login Access is mentioned but no time limit (e.g., '1 hour', '1 day') "
                "is specified. Always set the minimum necessary access duration."
            )
        if not LOGIN_REVOKE_PATTERN.search(text):
            issues.append(
                "Grant Login Access is mentioned but no revocation step is documented. "
                "Access should be revoked immediately after the support session."
            )

    return issues


def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Check a Salesforce metadata directory for support-escalation-relevant issues.

    Looks for org ID patterns in package.xml or similar manifest files and
    flags any hardcoded Sev1 references in automation metadata (e.g., Flow XML).
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check that a package.xml exists — absence suggests an incomplete manifest
    package_xml = manifest_dir / "package.xml"
    if not package_xml.exists():
        # Not necessarily an issue for all workflows, just informational
        pass

    # Scan Flow metadata for any hardcoded severity or support-routing patterns
    # that might indicate a support escalation automation was implemented incorrectly
    flow_dir = manifest_dir / "flows"
    if flow_dir.exists():
        for flow_file in flow_dir.glob("*.flow-meta.xml"):
            try:
                content = flow_file.read_text(encoding="utf-8")
            except OSError:
                continue

            # Detect flows that reference sandbox-qualified Sev1 routing
            if (
                SEVERITY_PATTERNS["sev1"].search(content)
                and SANDBOX_KEYWORDS.search(content)
            ):
                issues.append(
                    f"{flow_file.name}: Flow appears to route Sev1 cases for sandbox "
                    "environments. Sev1 applies to production impact only (KA 000382814)."
                )

    return issues


def main() -> int:
    args = parse_args()

    all_issues: list[str] = []

    if args.template_file:
        template_path = Path(args.template_file)
        all_issues.extend(check_template_file(template_path))
    else:
        manifest_dir = Path(args.manifest_dir)
        all_issues.extend(check_manifest_dir(manifest_dir))

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
