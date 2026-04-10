#!/usr/bin/env python3
"""Checker script for Marketing Cloud vs. MCAE Selection skill.

Validates that a platform selection decision document or requirements file
contains the minimum required content to constitute a defensible recommendation.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_marketing_cloud_vs_mcae_selection.py [--help]
    python3 check_marketing_cloud_vs_mcae_selection.py --doc path/to/selection-doc.md
    python3 check_marketing_cloud_vs_mcae_selection.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Keywords that indicate MCAE-only scope — flag if SMS/push also mentioned.
MCAE_KEYWORDS = re.compile(
    r"\b(account.engagement|pardot|mcae|engagement.studio|lead.scor|lead.grad)\b",
    re.IGNORECASE,
)

# Keywords that indicate MCE scope.
MCE_KEYWORDS = re.compile(
    r"\b(marketing.cloud.engagement|mce|journey.builder|email.studio|data.extension|mobileconnect|mobilepush)\b",
    re.IGNORECASE,
)

# Channels that require MCE — flag if mentioned alongside MCAE-only recommendation.
MCE_REQUIRED_CHANNELS = re.compile(
    r"\b(sms|push.notification|mobile.push|mobileconnect|advertising.studio|in.app)\b",
    re.IGNORECASE,
)

# Dangerous claims that indicate the shared-data-store anti-pattern.
# These patterns match positive claims of data unification, not educational disclaimers.
# Look for affirmative statements like "MC Connect shares data" or "unified contact record",
# but skip sentences that contain negation words (not, does not, no, without, etc.).
SHARED_DATA_STORE_CLAIMS = re.compile(
    r"(?<!not\s)(?<!does not\s)(?<!no\s)(?<!without\s)"
    r"(mc.connect\s+(provides?|gives?|creates?|enables?|allows?)\s+.{0,40}(shared|unified|merged)\s+(data|database|record|contact|prospect)"
    r"|unified\s+contact\s+record\s+.{0,60}mc.connect"
    r"|mc.connect\s+.{0,30}unified\s+contact)",
    re.IGNORECASE,
)

# Claim that features transfer between platforms.
# Match affirmative "you can use scoring in MCE" style claims,
# not educational "scoring is not available in MCE" corrections.
FEATURE_TRANSFER_CLAIMS = re.compile(
    r"(enable\s+scoring\s+in\s+mce"
    r"|use\s+scoring\s+in\s+mce"
    r"|enable\s+grading\s+in\s+mce"
    r"|journey.builder\s+(is\s+)?available\s+in\s+mcae"
    r"|sms\s+(is\s+)?available\s+in\s+mcae"
    r"|push\s+(is\s+)?available\s+in\s+mcae"
    r"|sms\s+(is\s+)?supported\s+in\s+mcae"
    r"|push\s+notification\s+(is\s+)?available\s+in\s+mcae"
    r"|mobile\s*push\s+(is\s+)?available\s+in\s+mcae)",
    re.IGNORECASE,
)

# Required structural elements in a selection document.
REQUIRED_AUDIENCE_TYPE = re.compile(r"\b(B2C|B2B|consumer|prospect|subscriber)\b", re.IGNORECASE)
REQUIRED_VOLUME = re.compile(r"\b(\d[\d,]+\s*(subscriber|prospect|record|contact)|volume|list.size)\b", re.IGNORECASE)
REQUIRED_RECOMMENDATION = re.compile(r"\b(recommend|select|platform.is|we.recommend|decision)\b", re.IGNORECASE)
REQUIRED_GAP_REGISTER = re.compile(r"\b(gap|not.covered|out.of.scope|limitation|does.not|cannot)\b", re.IGNORECASE)

# MCAE edition limits for volume validation.
MCAE_PREMIUM_LIMIT = 75_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Marketing Cloud vs. MCAE platform selection document "
            "for common anti-patterns and required decision elements."
        ),
    )
    parser.add_argument(
        "--doc",
        default=None,
        help="Path to a selection recommendation document (Markdown or text) to validate.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of Salesforce metadata (optional; scans for marketing-related metadata).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Document-level checks
# ---------------------------------------------------------------------------

def check_document(doc_path: Path) -> list[str]:
    """Validate a platform selection document for required content and anti-patterns."""
    issues: list[str] = []

    if not doc_path.exists():
        issues.append(f"Document not found: {doc_path}")
        return issues

    text = doc_path.read_text(encoding="utf-8", errors="replace")

    # Required structural elements
    if not REQUIRED_AUDIENCE_TYPE.search(text):
        issues.append(
            "Selection document does not mention audience type (B2C/B2B/consumer/prospect). "
            "Audience characterization is required before a defensible recommendation can be made."
        )

    if not REQUIRED_VOLUME.search(text):
        issues.append(
            "Selection document does not mention subscriber or prospect volume. "
            "Volume is required to validate against MCAE edition limits."
        )

    if not REQUIRED_RECOMMENDATION.search(text):
        issues.append(
            "Selection document does not contain a clear recommendation statement. "
            "The document must state which platform is recommended and why."
        )

    if not REQUIRED_GAP_REGISTER.search(text):
        issues.append(
            "Selection document does not document capability gaps. "
            "A capability gap register is required to confirm the customer has accepted "
            "what the selected platform does not cover."
        )

    # Anti-pattern: MCAE recommended but MCE-required channels mentioned
    has_mcae = bool(MCAE_KEYWORDS.search(text))
    has_mce = bool(MCE_KEYWORDS.search(text))
    channel_match = MCE_REQUIRED_CHANNELS.search(text)

    if has_mcae and not has_mce and channel_match:
        issues.append(
            f"Document references MCAE but also mentions '{channel_match.group()}' — "
            f"a channel that requires MCE (Marketing Cloud Engagement). "
            f"MCE must be included in the platform recommendation when SMS, push, or "
            f"advertising audiences are in scope. MCAE does not support these channels."
        )

    # Anti-pattern: MC Connect shared data store claim
    shared_match = SHARED_DATA_STORE_CLAIMS.search(text)
    if shared_match:
        issues.append(
            "Document may contain the anti-pattern that MC Connect creates a shared data store. "
            f"Matched text near: '{shared_match.group()[:120]}'. "
            "MC Connect does not merge the MCE and MCAE data stores. Each platform retains "
            "its own data layer. Verify this claim is not present in the recommendation."
        )

    # Anti-pattern: feature transfer claims
    feature_match = FEATURE_TRANSFER_CLAIMS.search(text)
    if feature_match:
        issues.append(
            f"Document may claim that a platform-specific feature is available on the other platform. "
            f"Matched: '{feature_match.group()}'. "
            "Scoring and grading are MCAE-exclusive. SMS, push, and Journey Builder are MCE-exclusive. "
            "Features do not transfer between platforms."
        )

    # Volume extraction heuristic — warn if number > MCAE limit in an MCAE-only doc
    if has_mcae and not has_mce:
        for match in re.finditer(r"[\d,]{4,}", text):
            try:
                num = int(match.group().replace(",", ""))
                if num > MCAE_PREMIUM_LIMIT:
                    issues.append(
                        f"Found a number ({num:,}) that exceeds the MCAE Premium edition prospect limit "
                        f"({MCAE_PREMIUM_LIMIT:,}). If this represents subscriber/prospect volume, "
                        f"MCAE is not suitable for this audience at this scale. MCE is required."
                    )
                    break  # Report once
            except ValueError:
                continue

    return issues


# ---------------------------------------------------------------------------
# Metadata directory checks
# ---------------------------------------------------------------------------

def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Scan a Salesforce metadata directory for marketing-related configuration signals."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Look for Pardot/MCAE connected app or remote site setting references
    pardot_refs: list[Path] = []
    mce_refs: list[Path] = []

    for xml_file in manifest_dir.rglob("*.xml"):
        try:
            content = xml_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if re.search(r"(pardot|account.engagement|b2bma)", content, re.IGNORECASE):
            pardot_refs.append(xml_file)
        if re.search(r"(exacttarget|marketing.cloud|marketingcloud)", content, re.IGNORECASE):
            mce_refs.append(xml_file)

    if pardot_refs and not mce_refs:
        issues.append(
            f"Metadata contains MCAE/Pardot references ({len(pardot_refs)} file(s)) but no MCE references. "
            "If the implementation requires SMS, push notifications, or advertising audiences, "
            "MCE must also be part of the implementation."
        )

    if mce_refs and not pardot_refs:
        issues.append(
            f"Metadata contains MCE references ({len(mce_refs)} file(s)) but no MCAE references. "
            "If lead scoring, grading, or native CRM lead/contact sync is required, "
            "MCAE must also be part of the implementation."
        )

    # Check for Marketing Cloud Connect remote site settings — both platforms must be licensed
    connect_refs = [
        f for f in manifest_dir.rglob("*.xml")
        if re.search(r"(MarketingCloudConnect|mc_connect|mc\.connect)", f.name, re.IGNORECASE)
        or (f.exists() and re.search(r"MarketingCloudConnect", f.read_text(encoding="utf-8", errors="replace"), re.IGNORECASE))
    ]

    if connect_refs:
        issues.append(
            "Marketing Cloud Connect configuration detected. "
            "Confirm that BOTH an MCE license and an MCAE license are in place — "
            "MC Connect requires separate licenses for each platform. "
            "Also confirm that the implementation team understands MC Connect does not "
            "create a shared data store between MCE and MCAE."
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    all_issues: list[str] = []

    if args.doc:
        all_issues.extend(check_document(Path(args.doc)))

    if args.manifest_dir:
        all_issues.extend(check_manifest_dir(Path(args.manifest_dir)))

    if args.doc is None and args.manifest_dir is None:
        print(
            "No input provided. Use --doc to validate a selection document "
            "or --manifest-dir to scan a Salesforce metadata directory.\n"
            "Run with --help for usage.",
            file=sys.stderr,
        )
        return 2

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
