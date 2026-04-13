#!/usr/bin/env python3
"""Checker script for Banking Lending Architecture skill.

Checks org metadata or configuration relevant to Banking Lending Architecture.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_banking_lending_architecture.py [--help]
    python3 check_banking_lending_architecture.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Banking Lending Architecture configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_files_recursive(root: Path, pattern: str) -> list[Path]:
    """Return all files matching a glob pattern under root."""
    return list(root.rglob(pattern))


def check_residential_loan_application(manifest_dir: Path, issues: list[str]) -> None:
    """Check for ResidentialLoanApplication object metadata in the manifest."""
    rla_files = find_files_recursive(manifest_dir, "ResidentialLoanApplication*.object-meta.xml")
    if not rla_files:
        issues.append(
            "No ResidentialLoanApplication*.object-meta.xml found in manifest. "
            "ResidentialLoanApplication is the anchor object for FSC Digital Lending and custom "
            "loan origination workflows. Its absence indicates the FSC Digital Lending module may "
            "not be provisioned, or loan origination has not yet been designed. "
            "Confirm FSC license includes the Digital Lending add-on before designing loan workflows."
        )
    else:
        print(f"  OK: Found ResidentialLoanApplication metadata: {[f.name for f in rla_files]}")


def check_omnistudio_metadata(manifest_dir: Path, issues: list[str]) -> None:
    """Check for OmniStudio metadata (OmniScript, IntegrationProcedure) required for Digital Lending."""
    omniscript_files = find_files_recursive(manifest_dir, "OmniScript*.xml")
    ip_files = find_files_recursive(manifest_dir, "IntegrationProcedure*.xml")
    # Also check for vlocity/omnistudio component files
    vlocity_files = find_files_recursive(manifest_dir, "*.OmniScript-meta.xml")
    vlocity_ip_files = find_files_recursive(manifest_dir, "*.IntegrationProcedure-meta.xml")

    has_omniscript = bool(omniscript_files or vlocity_files)
    has_ip = bool(ip_files or vlocity_ip_files)

    if not has_omniscript:
        issues.append(
            "No OmniScript metadata found in manifest. "
            "FSC Digital Lending requires OmniStudio (OmniScripts for guided loan intake, "
            "FlexCards for loan officer workspace). Without OmniStudio provisioning and deployed "
            "OmniScripts, the Digital Lending guided origination experience will not render. "
            "If OmniStudio is not licensed, document the decision to use custom Screen Flow + "
            "ResidentialLoanApplication instead."
        )
    else:
        print(f"  OK: Found OmniScript metadata ({len(omniscript_files + vlocity_files)} file(s)).")

    if not has_ip:
        issues.append(
            "No IntegrationProcedure metadata found in manifest. "
            "FSC Digital Lending uses Integration Procedures for credit bureau callouts, income "
            "verification, and async payment initiation. Missing Integration Procedures indicate "
            "external service integrations may not be designed or that synchronous Apex callouts "
            "are being used instead — which violates the 100-callout-per-transaction governor limit."
        )
    else:
        print(f"  OK: Found IntegrationProcedure metadata ({len(ip_files + vlocity_ip_files)} file(s)).")


def check_industries_settings_flags(manifest_dir: Path, issues: list[str]) -> None:
    """Warn if loanApplicantAutoCreation IndustriesSettings flag is not visible in metadata."""
    settings_files = find_files_recursive(manifest_dir, "IndustriesSettings.settings-meta.xml")
    # Also check in Settings directory
    settings_files += find_files_recursive(manifest_dir, "Industries.settings-meta.xml")

    found_auto_creation = False
    found_digital_lending = False

    for sf in settings_files:
        content = sf.read_text(encoding="utf-8", errors="replace")
        if "loanApplicantAutoCreation" in content:
            found_auto_creation = True
            # Check if it's explicitly set to true
            if re.search(r"<loanApplicantAutoCreation>true</loanApplicantAutoCreation>", content):
                print("  OK: loanApplicantAutoCreation is explicitly enabled in IndustriesSettings.")
            else:
                issues.append(
                    "loanApplicantAutoCreation is present in IndustriesSettings but NOT set to true. "
                    "Without this flag enabled, creating a LoanApplicant via API or OmniScript does not "
                    "auto-create the associated Person Account, producing orphan applicant records."
                )
        if "enableDigitalLending" in content:
            found_digital_lending = True
            if re.search(r"<enableDigitalLending>true</enableDigitalLending>", content):
                print("  OK: enableDigitalLending is explicitly enabled in IndustriesSettings.")
            else:
                issues.append(
                    "enableDigitalLending is present in IndustriesSettings but NOT set to true. "
                    "The Digital Lending platform will not be active without this flag."
                )

    if not settings_files:
        issues.append(
            "No IndustriesSettings.settings-meta.xml or Industries.settings-meta.xml found in manifest. "
            "The loanApplicantAutoCreation and enableDigitalLending flags must be explicitly configured. "
            "Without loanApplicantAutoCreation=true, LoanApplicant records created via API will not "
            "auto-create the associated Person Account, producing orphan applicants on bulk load."
        )
    elif not found_auto_creation:
        issues.append(
            "loanApplicantAutoCreation flag not found in IndustriesSettings. "
            "This flag defaults to off — without it, LoanApplicant records do not auto-create the "
            "associated Person Account. Confirm this is intentional or add the flag with value true."
        )
    elif not found_digital_lending:
        issues.append(
            "enableDigitalLending flag not found in IndustriesSettings. "
            "Without enableDigitalLending=true, the FSC Digital Lending platform features are inactive."
        )


def check_sync_apex_callouts_loan_processing(manifest_dir: Path, issues: list[str]) -> None:
    """Check for synchronous Apex callout patterns in classes related to loan processing."""
    apex_files = find_files_recursive(manifest_dir, "*.cls")

    # Keywords that suggest loan processing context
    loan_keywords = re.compile(
        r"ResidentialLoanApplication|LoanApplicant|loanApplicant|payment.*process|paymentProcess|"
        r"creditBureau|credit.*bureau|Experian|Equifax|Plaid|Finicity|industriesdigitallending",
        re.IGNORECASE,
    )
    callout_pattern = re.compile(r"\bHttpRequest\b|\bHttpResponse\b|\bnew\s+Http\(\)")
    async_pattern = re.compile(
        r"@future\s*\(\s*callout\s*=\s*true\s*\)|implements\s+Queueable|implements\s+Schedulable|"
        r"Database\.executeBatch|System\.enqueueJob"
    )

    flagged: list[str] = []
    for apex_file in apex_files:
        content = apex_file.read_text(encoding="utf-8", errors="replace")
        if not loan_keywords.search(content):
            continue
        if callout_pattern.search(content) and not async_pattern.search(content):
            flagged.append(apex_file.name)

    if flagged:
        issues.append(
            f"Apex class(es) {flagged} appear to contain synchronous HTTP callouts related to loan "
            "processing but do not use @future(callout=true), Queueable, or Schedulable patterns. "
            "Synchronous callouts for payment initiation, credit checks, or core banking integrations "
            "violate the 100-callout-per-transaction governor limit and will fail when multiple records "
            "are processed simultaneously. Use Integration Procedures or async Apex patterns instead."
        )


def check_banking_lending_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    print(f"Checking Banking Lending Architecture in: {manifest_dir.resolve()}")

    check_residential_loan_application(manifest_dir, issues)
    check_omnistudio_metadata(manifest_dir, issues)
    check_industries_settings_flags(manifest_dir, issues)
    check_sync_apex_callouts_loan_processing(manifest_dir, issues)

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_banking_lending_architecture(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    print(f"\n{len(issues)} issue(s) found:", file=sys.stderr)
    for issue in issues:
        print(f"\nWARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
