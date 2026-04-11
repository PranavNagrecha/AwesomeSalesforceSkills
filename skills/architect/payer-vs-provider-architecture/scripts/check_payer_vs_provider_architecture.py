#!/usr/bin/env python3
"""Checker script for Payer vs Provider Architecture skill.

Validates that a Health Cloud architecture document or metadata directory
contains the expected deployment-type classification artifacts, object model
references, PSL requirements, and provider/payer disambiguation.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_payer_vs_provider_architecture.py [--help]
    python3 check_payer_vs_provider_architecture.py --doc path/to/architecture.md
    python3 check_payer_vs_provider_architecture.py --manifest-dir path/to/metadata
    python3 check_payer_vs_provider_architecture.py --doc arch.md --manifest-dir metadata/
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Object model constants
# ---------------------------------------------------------------------------

PAYER_OBJECTS = {
    "MemberPlan",
    "PurchaserPlan",
    "CoverageBenefit",
    "CoverageBenefitItem",
    "ClaimHeader",
    "ClaimLine",
    "AuthorizationForm",
    "AuthorizationFormConsent",
}

PROVIDER_OBJECTS = {
    "ClinicalEncounter",
    "HealthCondition",
    "Medication",
    "CareObservation",
}

PAYER_PSLS = {
    "Health Cloud for Payers",
    "Utilization Management",
    "Provider Network Management",
}

REQUIRED_PAYER_PSL = "Health Cloud for Payers"
FHIR_KEYWORD = "FHIR R4 Support Settings"

# Phrases that must appear when "provider" is discussed, to ensure disambiguation
DISAMBIGUATION_PHRASES = [
    "network provider",
    "clinical provider",
    "Provider Relationship Management",
    "payer.*provider",
    "provider.*payer",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _contains_any(text: str, keywords: set[str] | list[str]) -> list[str]:
    """Return which keywords from the set appear in text (case-sensitive)."""
    return [kw for kw in keywords if kw in text]


def _contains_pattern(text: str, pattern: str) -> bool:
    return bool(re.search(pattern, text, re.IGNORECASE))


# ---------------------------------------------------------------------------
# Document-level checks (architecture doc / SKILL.md)
# ---------------------------------------------------------------------------


def check_document(doc_path: Path) -> list[str]:
    """Check an architecture document for required payer/provider content."""
    issues: list[str] = []

    if not doc_path.exists():
        issues.append(f"Document not found: {doc_path}")
        return issues

    text = _read_text(doc_path)
    if not text.strip():
        issues.append(f"Document is empty: {doc_path}")
        return issues

    # 1. Deployment type must be identified
    deployment_patterns = [
        r"payer.only",
        r"provider.only",
        r"dual.sector",
        r"dual.deployment",
        r"deployment type",
        r"payer deployment",
        r"provider deployment",
    ]
    if not any(_contains_pattern(text, p) for p in deployment_patterns):
        issues.append(
            "DEPLOYMENT TYPE: No deployment type classification found "
            "(payer-only, provider-only, or dual-sector). "
            "Deployment type must be explicitly stated."
        )

    # 2. At least one canonical object from the relevant object model must appear
    payer_refs = _contains_any(text, PAYER_OBJECTS)
    provider_refs = _contains_any(text, PROVIDER_OBJECTS)
    if not payer_refs and not provider_refs:
        issues.append(
            "OBJECT MODEL: No Health Cloud canonical objects referenced. "
            "Expected at least one of: "
            + ", ".join(sorted(PAYER_OBJECTS | PROVIDER_OBJECTS))
        )

    # 3. Cross-sector object contamination: warn if payer objects appear alongside
    #    provider-only language (or vice versa) without dual-sector acknowledgment.
    is_dual = _contains_pattern(text, r"dual.sector|dual.deployment|both payer and provider")
    has_payer = bool(payer_refs)
    has_provider = bool(provider_refs)

    if has_payer and has_provider and not is_dual:
        issues.append(
            "OBJECT MODEL CONTAMINATION: Both payer objects "
            f"({', '.join(payer_refs)}) and provider objects "
            f"({', '.join(provider_refs)}) are referenced, but no dual-sector "
            "deployment acknowledgment found. If this is intentional, explicitly "
            "document the dual-sector architecture."
        )

    # 4. PSL requirements must be documented
    psl_keyword_present = _contains_pattern(
        text,
        r"PSL|Permission Set License|Health Cloud for Payers|Utilization Management PSL|payer.*license|license.*payer",
    )
    if not psl_keyword_present:
        issues.append(
            "PSL REQUIREMENTS: No PSL (Permission Set License) requirements documented. "
            "Payer deployments require Health Cloud for Payers PSL at minimum. "
            "Provider deployments require base Health Cloud PSL. Document the PSL matrix."
        )

    # 5. If payer objects are referenced, Health Cloud for Payers PSL must be mentioned
    if has_payer and REQUIRED_PAYER_PSL not in text:
        issues.append(
            f"PAYER PSL MISSING: Payer objects ({', '.join(payer_refs)}) are referenced "
            f"but '{REQUIRED_PAYER_PSL}' PSL is not mentioned. "
            "Payer features require this PSL — omitting it causes silent feature gaps."
        )

    # 6. Provider/payer disambiguation must be present if "provider" appears
    if re.search(r"\bprovider\b", text, re.IGNORECASE):
        disambiguated = any(
            _contains_pattern(text, p) for p in DISAMBIGUATION_PHRASES
        )
        if not disambiguated:
            issues.append(
                "PROVIDER DISAMBIGUATION: The term 'provider' appears in the document "
                "but no disambiguation between 'network provider' (payer-side) and "
                "'clinical provider' (care delivery) is present. "
                "This ambiguity is the most common architecture mistake in Health Cloud."
            )

    # 7. If provider objects referenced, check for FHIR activation note (when FHIR context present)
    if has_provider and _contains_pattern(text, r"FHIR|interoperab"):
        if FHIR_KEYWORD not in text:
            issues.append(
                "FHIR ACTIVATION: Provider objects and FHIR are mentioned but "
                f"'{FHIR_KEYWORD}' is not referenced. "
                "FHIR R4 is not active by default — it must be enabled in "
                "Setup > Health > Health Cloud Settings."
            )

    return issues


# ---------------------------------------------------------------------------
# Metadata directory checks
# ---------------------------------------------------------------------------


def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Check Salesforce metadata for payer/provider architecture issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Collect all text from XML metadata files
    xml_files = list(manifest_dir.rglob("*.xml"))
    if not xml_files:
        issues.append(
            f"No XML metadata files found in {manifest_dir}. "
            "Pass the root directory of an SFDX project or metadata package."
        )
        return issues

    all_text = "\n".join(_read_text(f) for f in xml_files)

    # Check for AuthorizationForm usage in non-payer context
    if "AuthorizationForm" in all_text:
        payer_context = any(
            _contains_pattern(_read_text(f), r"MemberPlan|ClaimHeader|PurchaserPlan")
            for f in xml_files
        )
        if not payer_context:
            issues.append(
                "AUTHORIZATION FORM IN NON-PAYER CONTEXT: AuthorizationForm metadata found "
                "but no payer enrollment objects (MemberPlan, ClaimHeader, PurchaserPlan) "
                "detected. AuthorizationForm is a Utilization Management object for payer orgs — "
                "confirm this is not being misused for clinical consent in a provider org."
            )

    # Check for mixed payer/provider object references without documentation
    payer_obj_in_metadata = [obj for obj in PAYER_OBJECTS if obj in all_text]
    provider_obj_in_metadata = [obj for obj in PROVIDER_OBJECTS if obj in all_text]

    if payer_obj_in_metadata and provider_obj_in_metadata:
        issues.append(
            "DUAL-SECTOR METADATA DETECTED: Both payer objects "
            f"({', '.join(payer_obj_in_metadata)}) and provider objects "
            f"({', '.join(provider_obj_in_metadata)}) found in metadata. "
            "If this is a dual-sector org, verify that object-level permission sets "
            "enforce sector separation. If this is a single-sector org, "
            "remove objects from the wrong sector."
        )

    # Check for permission sets referencing payer objects
    perm_set_files = [f for f in xml_files if "permissionsets" in str(f).lower()]
    for pf in perm_set_files:
        content = _read_text(pf)
        has_payer_obj = any(obj in content for obj in PAYER_OBJECTS)
        has_provider_obj = any(obj in content for obj in PROVIDER_OBJECTS)
        if has_payer_obj and has_provider_obj:
            issues.append(
                f"MIXED PERMISSION SET: {pf.name} grants access to both payer objects "
                f"({[o for o in PAYER_OBJECTS if o in content]}) and provider objects "
                f"({[o for o in PROVIDER_OBJECTS if o in content]}). "
                "In a dual-sector org, payer and provider permissions should be in "
                "separate permission sets to enforce sector access boundaries."
            )

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Health Cloud architecture documents and metadata for "
            "payer vs provider deployment type classification issues."
        ),
    )
    parser.add_argument(
        "--doc",
        metavar="PATH",
        help="Path to an architecture document (Markdown) to validate.",
    )
    parser.add_argument(
        "--manifest-dir",
        metavar="PATH",
        help="Root directory of Salesforce metadata to inspect.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.doc and not args.manifest_dir:
        print(
            "Usage: check_payer_vs_provider_architecture.py [--doc PATH] [--manifest-dir PATH]",
            file=sys.stderr,
        )
        print(
            "At least one of --doc or --manifest-dir must be provided.",
            file=sys.stderr,
        )
        return 2

    all_issues: list[str] = []

    if args.doc:
        doc_issues = check_document(Path(args.doc))
        all_issues.extend(doc_issues)

    if args.manifest_dir:
        manifest_issues = check_manifest_dir(Path(args.manifest_dir))
        all_issues.extend(manifest_issues)

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
