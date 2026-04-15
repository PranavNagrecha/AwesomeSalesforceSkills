#!/usr/bin/env python3
"""Checker script for Industries Cloud Selection skill.

Validates that a selection decision document or requirements file contains
the minimum required content to constitute a defensible vertical cloud
selection recommendation.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_industries_cloud_selection.py [--help]
    python3 check_industries_cloud_selection.py --doc path/to/decision.md
    python3 check_industries_cloud_selection.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Known industry standard objects and their license requirements.
# If a document references these objects, it must also confirm licensing.
# ---------------------------------------------------------------------------
LICENSED_OBJECTS: dict[str, str] = {
    "InsurancePolicy": "Insurance Cloud (+ FSC base)",
    "InsurancePolicyCoverage": "Insurance Cloud (+ FSC base)",
    "InsurancePolicyParticipant": "Insurance Cloud (+ FSC base)",
    "ServicePoint": "Energy & Utilities Cloud",
    "UtilityAccount": "Energy & Utilities Cloud",
    "RatePlan": "Energy & Utilities Cloud",
    "ServicePointReading": "Energy & Utilities Cloud",
    "BillingAccount": "Communications Cloud",
    "EnterpriseProduct": "Communications Cloud",
    "ProductCatalog": "Communications Cloud",
    "FinancialAccount": "Financial Services Cloud",
    "FinancialHolding": "Financial Services Cloud",
    "AssetsAndLiabilities": "Financial Services Cloud",
    "ClinicalEncounter": "Health Cloud",
    "CarePlan": "Health Cloud",
    "MemberPlan": "Health Cloud",
    "BusinessLicense": "Public Sector Solutions",
    "BusinessRegulatoryAuthorization": "Public Sector Solutions",
    "Vehicle": "Automotive Cloud",
    "Fleet": "Automotive Cloud",
    "SalesAgreement": "Manufacturing Cloud",
    "AccountProductForecast": "Manufacturing Cloud",
    "RetailStore": "Consumer Goods Cloud",
    "AssortmentProduct": "Consumer Goods Cloud",
    "CourseOffering": "Education Cloud",
    "ProgramEnrollment": "Education Cloud",
}

# ---------------------------------------------------------------------------
# Phrases that indicate a document is discussing license confirmation.
# A passing document should contain at least one of these near object mentions.
# ---------------------------------------------------------------------------
LICENSE_CONFIRMATION_PHRASES = [
    "license",
    "licensed",
    "licensing",
    "license psl",
    "psl",
    "entitlement",
    "order form",
    "sku",
]

# ---------------------------------------------------------------------------
# Phrases that indicate the one-way OmniStudio migration risk has been noted.
# ---------------------------------------------------------------------------
OMNISTUDIO_IRREVERSIBILITY_PHRASES = [
    "irreversible",
    "one-way",
    "one way",
    "cannot be reverted",
    "cannot be rolled back",
    "permanent",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate an Industries Cloud selection decision document or "
            "metadata directory for common issues."
        ),
    )
    parser.add_argument(
        "--doc",
        default=None,
        help="Path to a selection decision document (.md or .txt) to validate.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of the Salesforce metadata to scan for issues.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Document-level checks
# ---------------------------------------------------------------------------

def check_object_license_confirmation(text: str) -> list[str]:
    """Warn if a licensed object is mentioned without any license language nearby."""
    issues: list[str] = []
    lower_text = text.lower()

    has_license_language = any(
        phrase in lower_text for phrase in LICENSE_CONFIRMATION_PHRASES
    )

    for obj_name, required_license in LICENSED_OBJECTS.items():
        if obj_name in text and not has_license_language:
            issues.append(
                f"Document references '{obj_name}' (requires: {required_license}) "
                f"but contains no license confirmation language. "
                f"Add a statement confirming the license is in scope."
            )
    return issues


def check_insurance_fsc_dependency(text: str) -> list[str]:
    """Warn if Insurance Cloud is mentioned without FSC dependency note."""
    issues: list[str] = []
    lower = text.lower()
    if "insurance cloud" in lower:
        fsc_mentioned = "fsc" in lower or "financial services cloud" in lower
        if not fsc_mentioned:
            issues.append(
                "Document mentions 'Insurance Cloud' but does not reference "
                "'FSC' or 'Financial Services Cloud'. "
                "Insurance Cloud requires FSC as a base license — "
                "confirm FSC is included in the license scope."
            )
    return issues


def check_omnistudio_migration_risk(text: str) -> list[str]:
    """Warn if OmniStudio migration is discussed without noting irreversibility."""
    issues: list[str] = []
    lower = text.lower()
    migration_mentioned = (
        "standard designer" in lower
        or ("omnistudio" in lower and "migrat" in lower)
        or ("omnistudio" in lower and "platform-native" in lower)
    )
    if migration_mentioned:
        irreversibility_noted = any(
            phrase in lower for phrase in OMNISTUDIO_IRREVERSIBILITY_PHRASES
        )
        if not irreversibility_noted:
            issues.append(
                "Document discusses OmniStudio migration or platform-native "
                "adoption but does not note the one-way/irreversible nature "
                "of Standard Designer migration. "
                "Add a statement that opening a managed-package component in "
                "the Standard Designer cannot be undone."
            )
    return issues


def check_required_sections(text: str) -> list[str]:
    """Check that a decision document has minimum required sections."""
    issues: list[str] = []
    lower = text.lower()

    required_keywords = {
        "required objects / data model": [
            "standard object", "required object", "data model", "object landscape"
        ],
        "license scope": [
            "license", "licensed", "sku", "order form", "entitlement"
        ],
        "open questions or risks": [
            "open question", "risk", "assumption", "outstanding", "tbd", "to be confirmed"
        ],
    }

    for section_name, keywords in required_keywords.items():
        if not any(kw in lower for kw in keywords):
            issues.append(
                f"Decision document appears to be missing a '{section_name}' section. "
                f"A complete vertical cloud selection document must address: "
                f"{', '.join(keywords[:2])}."
            )

    return issues


def check_document(doc_path: Path) -> list[str]:
    """Run all document-level checks on a selection decision document."""
    issues: list[str] = []
    if not doc_path.exists():
        issues.append(f"Document not found: {doc_path}")
        return issues

    text = doc_path.read_text(encoding="utf-8", errors="replace")

    issues.extend(check_object_license_confirmation(text))
    issues.extend(check_insurance_fsc_dependency(text))
    issues.extend(check_omnistudio_migration_risk(text))
    issues.extend(check_required_sections(text))

    return issues


# ---------------------------------------------------------------------------
# Metadata directory checks
# ---------------------------------------------------------------------------

def check_manifest_for_industries_objects(manifest_dir: Path) -> list[str]:
    """
    Scan metadata files for references to industry standard objects without
    corresponding license confirmation patterns.
    """
    issues: list[str] = []
    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Scan common metadata file types for object references
    extensions = {".xml", ".json", ".cls", ".trigger", ".flow"}
    scanned = 0

    for filepath in manifest_dir.rglob("*"):
        if filepath.suffix not in extensions:
            continue
        scanned += 1
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for obj_name, required_license in LICENSED_OBJECTS.items():
            if obj_name in content:
                # Check if any license confirmation language is in the same file
                lower_content = content.lower()
                has_license_lang = any(
                    phrase in lower_content for phrase in LICENSE_CONFIRMATION_PHRASES
                )
                if not has_license_lang:
                    issues.append(
                        f"{filepath.relative_to(manifest_dir)}: "
                        f"references '{obj_name}' (requires: {required_license}) — "
                        f"confirm the org holds the required Industries license."
                    )
                    # Report once per file, not once per object
                    break

    if scanned == 0:
        issues.append(
            f"No metadata files ({', '.join(sorted(extensions))}) found in "
            f"{manifest_dir}. Ensure the manifest directory is correct."
        )

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    issues: list[str] = []

    if args.doc:
        issues.extend(check_document(Path(args.doc)))
    elif args.manifest_dir:
        issues.extend(check_manifest_for_industries_objects(Path(args.manifest_dir)))
    else:
        # Default: look for any .md files in the current directory
        cwd = Path(".")
        md_files = list(cwd.glob("*.md"))
        if md_files:
            for md in md_files:
                issues.extend(check_document(md))
        else:
            print(
                "No --doc or --manifest-dir provided and no .md files in current "
                "directory. Run with --help for usage.",
                file=sys.stderr,
            )
            return 1

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
