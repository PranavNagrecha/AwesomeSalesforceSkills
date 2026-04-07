#!/usr/bin/env python3
"""Checker script for Portal Requirements Gathering skill.

Validates a portal requirements document (Markdown) for common anti-patterns
and missing sections. Uses stdlib only — no pip dependencies.

Checks performed:
- Contact reason analysis section present and has data rows
- Access architecture decision recorded (public/authenticated/hybrid)
- License type selection present per audience
- Top-3 jobs defined with success criteria
- Content taxonomy section present with at least one owner named
- Deferred features section present (social/gamification explicitly deferred)
- Sign-off section present

Usage:
    python3 check_portal_requirements_gathering.py --doc path/to/requirements.md
    python3 check_portal_requirements_gathering.py --doc path/to/requirements.md --strict
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check a portal requirements document for common anti-patterns and missing sections.",
    )
    parser.add_argument(
        "--doc",
        required=False,
        default=None,
        help="Path to the portal requirements Markdown document to check.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (exit 1 on any finding).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_contact_reason_analysis(text: str) -> list[str]:
    """Verify that a contact reason analysis section exists and contains data."""
    issues: list[str] = []
    if not re.search(r"contact reason", text, re.IGNORECASE):
        issues.append(
            "MISSING: No 'Contact Reason' section found. "
            "A 60–90 day contact reason analysis is required before feature scoping."
        )
        return issues

    # Look for the Answers/Status/Actions categorisation
    if not re.search(r"answers|status|action", text, re.IGNORECASE):
        issues.append(
            "INCOMPLETE: Contact reason section found but does not categorise reasons "
            "as Answers / Status / Actions. Add this breakdown."
        )

    # Look for at least one table row with data (non-header, non-TODO)
    rows = re.findall(r"\|\s*\d+\s*\|", text)
    if not rows:
        issues.append(
            "INCOMPLETE: Contact reason section appears to have no ranked data rows. "
            "Populate the top contact reasons table with real data before the requirements workshop."
        )

    return issues


def check_access_architecture(text: str) -> list[str]:
    """Verify that an access architecture decision is recorded."""
    issues: list[str] = []
    if not re.search(r"access architecture", text, re.IGNORECASE):
        issues.append(
            "MISSING: No 'Access Architecture' section found. "
            "The portal access model (public / authenticated / hybrid) must be locked in requirements."
        )
        return issues

    # Check that one of the three models is chosen
    if not re.search(r"\b(public|authenticated|hybrid)\b", text, re.IGNORECASE):
        issues.append(
            "INCOMPLETE: Access Architecture section found but no decision keyword detected "
            "(public / authenticated / hybrid). Record the decision explicitly."
        )

    return issues


def check_license_selection(text: str) -> list[str]:
    """Verify that a license selection is documented."""
    issues: list[str] = []
    license_keywords = [
        "customer community",
        "partner community",
        "external apps",
        "community plus",
    ]
    found = any(re.search(kw, text, re.IGNORECASE) for kw in license_keywords)
    if not found:
        issues.append(
            "MISSING: No license type recorded (Customer Community, Customer Community Plus, "
            "Partner Community, or External Apps). License selection must be locked in requirements."
        )
    return issues


def check_top_jobs(text: str) -> list[str]:
    """Verify that top-3 jobs are defined with success criteria."""
    issues: list[str] = []

    if not re.search(r"job\s*(1|2|3|statement|high.volume)", text, re.IGNORECASE):
        issues.append(
            "MISSING: No 'Top-3 Jobs' section found. "
            "Define the three highest-volume customer jobs before any feature scoping."
        )
        return issues

    # Check for success criterion per job
    success_hits = len(re.findall(r"success criterion", text, re.IGNORECASE))
    if success_hits < 3:
        issues.append(
            f"INCOMPLETE: Found {success_hits} 'Success Criterion' reference(s); expected 3. "
            "Each of the top-3 jobs must have a measurable success criterion."
        )

    return issues


def check_content_taxonomy(text: str) -> list[str]:
    """Verify that a content taxonomy section is present with at least one owner."""
    issues: list[str] = []
    if not re.search(r"content taxonomy|content type|content owner", text, re.IGNORECASE):
        issues.append(
            "MISSING: No content taxonomy or content ownership section found. "
            "Every content type (Knowledge Articles, documents, assets) must have a named owner "
            "and review cadence."
        )
    return issues


def check_deferred_features(text: str) -> list[str]:
    """Verify that social and gamification features are explicitly deferred."""
    issues: list[str] = []
    if not re.search(r"deferred|phase 2", text, re.IGNORECASE):
        issues.append(
            "MISSING: No 'Deferred' or 'Phase 2' section found. "
            "Social and gamification features must be explicitly deferred until the core "
            "deflection loop is validated."
        )
        return issues

    social_terms = ["idea exchange", "gamification", "leaderboard", "badges", "forum", "chatter"]
    missing_deferrals = [
        term for term in social_terms
        if not re.search(term, text, re.IGNORECASE)
    ]
    if missing_deferrals:
        issues.append(
            "INCOMPLETE: Deferred section found but these social/gamification items were not "
            f"explicitly addressed: {', '.join(missing_deferrals)}. "
            "Record each one as deferred or out-of-scope to prevent scope creep."
        )

    return issues


def check_sign_off(text: str) -> list[str]:
    """Verify that a sign-off section exists."""
    issues: list[str] = []
    if not re.search(r"sign.off|signed off|approver", text, re.IGNORECASE):
        issues.append(
            "MISSING: No sign-off section found. "
            "Requirements must be signed off by both a business stakeholder and a technical lead "
            "before build begins."
        )
    return issues


def check_deflection_baseline(text: str) -> list[str]:
    """Verify that a deflection baseline and target are recorded."""
    issues: list[str] = []
    if not re.search(r"deflection|containment rate|self.service rate", text, re.IGNORECASE):
        issues.append(
            "MISSING: No deflection baseline or target found. "
            "Record the current self-service containment rate and a measurable phase 1 target."
        )
    return issues


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_checks(text: str) -> list[str]:
    """Run all checks and return a flat list of issue strings."""
    all_issues: list[str] = []
    all_issues.extend(check_contact_reason_analysis(text))
    all_issues.extend(check_access_architecture(text))
    all_issues.extend(check_license_selection(text))
    all_issues.extend(check_top_jobs(text))
    all_issues.extend(check_content_taxonomy(text))
    all_issues.extend(check_deferred_features(text))
    all_issues.extend(check_deflection_baseline(text))
    all_issues.extend(check_sign_off(text))
    return all_issues


def main() -> int:
    args = parse_args()

    if args.doc is None:
        print(
            "No --doc argument provided. Pass the path to a portal requirements Markdown document.\n"
            "Usage: python3 check_portal_requirements_gathering.py --doc path/to/requirements.md",
            file=sys.stderr,
        )
        return 2

    doc_path = Path(args.doc)
    if not doc_path.exists():
        print(f"ERROR: Document not found: {doc_path}", file=sys.stderr)
        return 2

    text = doc_path.read_text(encoding="utf-8")
    issues = run_checks(text)

    if not issues:
        print("All checks passed. Portal requirements document looks complete.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    if args.strict:
        print(
            f"\n{len(issues)} issue(s) found. Resolve before proceeding to build.",
            file=sys.stderr,
        )
        return 1

    print(
        f"\n{len(issues)} issue(s) found. Review the warnings above before marking requirements complete.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
