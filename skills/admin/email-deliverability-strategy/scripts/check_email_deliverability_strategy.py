#!/usr/bin/env python3
"""Checker script for Email Deliverability Strategy skill.

Checks org metadata or configuration relevant to email deliverability.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_email_deliverability_strategy.py [--help]
    python3 check_email_deliverability_strategy.py --manifest-dir path/to/metadata
    python3 check_email_deliverability_strategy.py --dns-spec path/to/dns-spec.txt
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check email deliverability configuration and metadata for common issues. "
            "Validates DNS record specifications, suppression policy documents, and "
            "DMARC policy settings."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata or project (default: current directory).",
    )
    parser.add_argument(
        "--dns-spec",
        default=None,
        help="Path to a text file containing DNS record specifications to validate.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# DNS record spec checks
# ---------------------------------------------------------------------------

def check_dns_spec(spec_path: Path) -> list[str]:
    """Validate a DNS record specification file for common deliverability misconfigurations."""
    issues: list[str] = []

    if not spec_path.exists():
        issues.append(f"DNS spec file not found: {spec_path}")
        return issues

    text = spec_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    # Check for duplicate SPF records (multiple lines starting with v=spf1)
    spf_lines = [ln for ln in lines if "v=spf1" in ln]
    if len(spf_lines) > 1:
        issues.append(
            "DUPLICATE SPF RECORDS DETECTED: Found multiple lines containing 'v=spf1'. "
            "RFC 7208 requires exactly one SPF TXT record per domain. "
            "Merge all include: directives into a single record."
        )

    # Check that Marketing Cloud SPF include is present
    mc_spf_includes = [
        "_spf.exacttarget.com",
        "_spf.sfmc.exacttarget.com",
    ]
    has_mc_spf = any(inc in text for inc in mc_spf_includes)
    if spf_lines and not has_mc_spf:
        issues.append(
            "Marketing Cloud SPF include not found. "
            "Expected 'include:_spf.exacttarget.com' in the SPF TXT record. "
            "Obtain the correct include directive from Marketing Cloud Setup > Private Domains."
        )

    # Check for DKIM CNAME records
    dkim_pattern = re.compile(r"_domainkey\.", re.IGNORECASE)
    dkim_cname_pattern = re.compile(r"CNAME", re.IGNORECASE)
    dkim_lines = [ln for ln in lines if dkim_pattern.search(ln)]
    if not dkim_lines:
        issues.append(
            "No DKIM records found in DNS spec. "
            "Marketing Cloud requires at least two CNAME records for DKIM signing "
            "(e.g., s1._domainkey.<domain> and s2._domainkey.<domain>). "
            "Retrieve these from Marketing Cloud Setup > Private Domains."
        )
    else:
        cname_dkim = [ln for ln in dkim_lines if dkim_cname_pattern.search(ln)]
        if not cname_dkim:
            issues.append(
                "DKIM records found but none appear to be CNAME type. "
                "Marketing Cloud uses CNAME-based DKIM records (not raw TXT public keys). "
                "Verify the record type is CNAME pointing to Marketing Cloud's key servers."
            )

    # Check for DMARC record
    dmarc_pattern = re.compile(r"_dmarc\.", re.IGNORECASE)
    dmarc_lines = [ln for ln in lines if dmarc_pattern.search(ln)]
    if not dmarc_lines:
        issues.append(
            "No DMARC record found in DNS spec. "
            "A DMARC TXT record at _dmarc.<sending-domain> is required by Google and Yahoo "
            "for bulk senders (>5,000/day) since February 2024."
        )
    else:
        dmarc_text = " ".join(dmarc_lines)
        # Check for rua destination
        if "rua=" not in dmarc_text.lower():
            issues.append(
                "DMARC record is missing rua= (aggregate report URI). "
                "Add 'rua=mailto:<your-report-address>' so receiving servers can send "
                "alignment reports. Without reports, authentication failures go undetected."
            )
        # Check for p= policy
        p_reject = re.search(r"p=reject", dmarc_text, re.IGNORECASE)
        p_quarantine = re.search(r"p=quarantine", dmarc_text, re.IGNORECASE)
        p_none = re.search(r"p=none", dmarc_text, re.IGNORECASE)
        if not (p_reject or p_quarantine or p_none):
            issues.append(
                "DMARC record is missing the p= policy tag. "
                "Valid values: p=none (monitor), p=quarantine, p=reject. "
                "Start with p=none when first deploying DMARC."
            )
        # Warn if starting at p=reject directly (common over-aggressive setup)
        if p_reject and not p_none and not p_quarantine:
            issues.append(
                "DMARC policy is p=reject. Confirm that aggregate reports (rua=) have been "
                "reviewed for at least 30 days and that 95%+ of legitimate sends show DMARC pass "
                "before enforcing p=reject. Premature enforcement blocks legitimate email."
            )

    return issues


# ---------------------------------------------------------------------------
# Manifest directory checks
# ---------------------------------------------------------------------------

def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Check project metadata directory for deliverability-relevant configurations."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Look for any DNS spec or deliverability planning files
    dns_files = list(manifest_dir.rglob("*.txt")) + list(manifest_dir.rglob("*.md"))
    deliverability_files = [
        f for f in dns_files
        if any(kw in f.name.lower() for kw in ["dns", "spf", "dkim", "dmarc", "deliverability"])
    ]

    if not deliverability_files:
        issues.append(
            "No DNS specification or deliverability planning files found in manifest directory. "
            "Expected at least one file documenting SPF, DKIM, and DMARC record specifications. "
            "Use the email-deliverability-strategy template to create a planning document."
        )
    else:
        # Run DNS spec checks on any found files that look like DNS specs
        for dns_file in deliverability_files:
            file_issues = check_dns_spec(dns_file)
            for issue in file_issues:
                issues.append(f"[{dns_file.name}] {issue}")

    # Check for evidence of a warm-up plan
    warmup_files = [
        f for f in dns_files
        if any(kw in f.name.lower() for kw in ["warmup", "warm-up", "warm_up", "ramp"])
    ]
    if not warmup_files:
        issues.append(
            "No dedicated IP warm-up plan found. "
            "If using a dedicated IP, document the week-by-week volume schedule and "
            "engagement-segment criteria before the first send."
        )

    # Check for suppression or hygiene policy document
    hygiene_files = [
        f for f in dns_files
        if any(kw in f.name.lower() for kw in ["hygiene", "suppression", "sunset", "inactive"])
    ]
    if not hygiene_files:
        issues.append(
            "No list hygiene or suppression policy document found. "
            "Document the hard bounce suppression confirmation, soft bounce threshold, "
            "and inactive subscriber sunset criteria (typically 6–12 months)."
        )

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    issues: list[str] = []

    if args.dns_spec:
        dns_path = Path(args.dns_spec)
        issues.extend(check_dns_spec(dns_path))
    else:
        manifest_dir = Path(args.manifest_dir)
        issues.extend(check_manifest_dir(manifest_dir))

    if not issues:
        print("No deliverability configuration issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
