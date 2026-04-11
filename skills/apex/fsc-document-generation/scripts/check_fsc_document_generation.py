#!/usr/bin/env python3
"""Checker script for FSC Document Generation skill.

Validates org metadata for common FSC document generation anti-patterns:
- DocGen callout code missing rate-limit (429/503) handling
- AuthorizationFormConsent writes absent from disclosure workflows
- Document Builder usage in contexts where OmniStudio DocGen is required
- OmniScript invocation patterns used in batch/scheduled Apex contexts
- Batch Apex missing Database.AllowsCallouts for DocGen callout methods

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsc_document_generation.py [--manifest-dir path/to/metadata]
    python3 check_fsc_document_generation.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ── Pattern definitions ────────────────────────────────────────────────────────

# Apex files that call DocGen API but lack 429/503 response handling
DOCGEN_CALLOUT_PATTERN = re.compile(
    r"http\.send\s*\(", re.IGNORECASE
)
RATE_LIMIT_HANDLING_PATTERN = re.compile(
    r"getStatusCode\(\)\s*==\s*['\"]?(429|503)", re.IGNORECASE
)

# Batch/Schedulable Apex without Database.AllowsCallouts
BATCHABLE_PATTERN = re.compile(
    r"implements\s+.*Database\.Batchable", re.IGNORECASE
)
ALLOWS_CALLOUTS_PATTERN = re.compile(
    r"Database\.AllowsCallouts", re.IGNORECASE
)

# OmniScript invocation in Apex (wrong pattern for batch doc generation)
OMNISCRIPT_BATCH_PATTERN = re.compile(
    r"OmniScriptController|OmniScriptSaveAction|omniscript.*controller",
    re.IGNORECASE,
)

# Document Builder usage (PCI-excluded tool)
DOCUMENT_BUILDER_PATTERN = re.compile(
    r"ConnectApi\.DocumentBuilder|DocumentBuilderController|document_builder",
    re.IGNORECASE,
)

# AuthorizationFormConsent — should be present in disclosure workflows
# Heuristic: if DocGen API is called and AuthorizationFormConsent insert is absent
DOCGEN_API_PATTERN = re.compile(
    r"docgen|DocGenDocument|vlocity_ins__DocGenDocument",
    re.IGNORECASE,
)
CONSENT_INSERT_PATTERN = re.compile(
    r"AuthorizationFormConsent", re.IGNORECASE
)


# ── File collection ────────────────────────────────────────────────────────────

def collect_apex_files(manifest_dir: Path) -> list[Path]:
    """Return all .cls and .trigger files under manifest_dir."""
    apex_files: list[Path] = []
    for ext in ("*.cls", "*.trigger"):
        apex_files.extend(manifest_dir.rglob(ext))
    return apex_files


# ── Individual checks ──────────────────────────────────────────────────────────

def check_docgen_rate_limit_handling(apex_files: list[Path]) -> list[str]:
    """Warn if any file calls http.send but lacks 429/503 status code handling."""
    issues: list[str] = []
    for f in apex_files:
        content = f.read_text(encoding="utf-8", errors="replace")
        if DOCGEN_CALLOUT_PATTERN.search(content) and DOCGEN_API_PATTERN.search(content):
            if not RATE_LIMIT_HANDLING_PATTERN.search(content):
                issues.append(
                    f"{f.name}: DocGen API callout found but no 429/503 rate-limit "
                    f"response handling detected. Add explicit getStatusCode() == 429 "
                    f"handling with retry logic. (See gotchas.md Gotcha 3)"
                )
    return issues


def check_batch_allows_callouts(apex_files: list[Path]) -> list[str]:
    """Warn if a Batchable class calls DocGen but does not implement AllowsCallouts."""
    issues: list[str] = []
    for f in apex_files:
        content = f.read_text(encoding="utf-8", errors="replace")
        if BATCHABLE_PATTERN.search(content) and DOCGEN_API_PATTERN.search(content):
            if not ALLOWS_CALLOUTS_PATTERN.search(content):
                issues.append(
                    f"{f.name}: Batchable class with DocGen API usage does not implement "
                    f"Database.AllowsCallouts. Callouts from batch execute() require this "
                    f"interface. Add ', Database.AllowsCallouts' to the implements clause."
                )
    return issues


def check_omniscript_in_batch_context(apex_files: list[Path]) -> list[str]:
    """Warn if OmniScript controller patterns appear inside Batchable or Schedulable classes."""
    issues: list[str] = []
    for f in apex_files:
        content = f.read_text(encoding="utf-8", errors="replace")
        is_batch_or_scheduled = (
            re.search(r"implements\s+.*Database\.Batchable", content, re.IGNORECASE)
            or re.search(r"implements\s+.*Schedulable", content, re.IGNORECASE)
        )
        if is_batch_or_scheduled and OMNISCRIPT_BATCH_PATTERN.search(content):
            issues.append(
                f"{f.name}: OmniScript controller reference found inside a Batchable or "
                f"Schedulable class. OmniScript requires a user session and is not suitable "
                f"for headless batch document generation. Use the DocGen REST API directly. "
                f"(See llm-anti-patterns.md Anti-Pattern 5)"
            )
    return issues


def check_document_builder_usage(apex_files: list[Path]) -> list[str]:
    """Warn if Document Builder API patterns are found — PCI-excluded tool."""
    issues: list[str] = []
    for f in apex_files:
        content = f.read_text(encoding="utf-8", errors="replace")
        if DOCUMENT_BUILDER_PATTERN.search(content):
            issues.append(
                f"{f.name}: Document Builder API usage detected. Document Builder is "
                f"excluded from Salesforce's PCI DSS compliance attestation (Winter '25+). "
                f"Use OmniStudio DocGen for FSC compliance documents. "
                f"(See llm-anti-patterns.md Anti-Pattern 2)"
            )
    return issues


def check_docgen_without_consent_record(apex_files: list[Path]) -> list[str]:
    """Warn if a file invokes DocGen API but has no AuthorizationFormConsent reference."""
    issues: list[str] = []
    for f in apex_files:
        content = f.read_text(encoding="utf-8", errors="replace")
        if DOCGEN_API_PATTERN.search(content) and DOCGEN_CALLOUT_PATTERN.search(content):
            # Only flag if it looks like a disclosure/compliance context
            # (heuristic: file name or content mentions disclosure/consent/compliance)
            compliance_hint = re.search(
                r"disclosure|consent|finra|gdpr|compliance|authorization",
                content,
                re.IGNORECASE,
            )
            if compliance_hint and not CONSENT_INSERT_PATTERN.search(content):
                issues.append(
                    f"{f.name}: DocGen API callout in a compliance context but no "
                    f"AuthorizationFormConsent insert detected. Compliance document workflows "
                    f"must write an AuthorizationFormConsent record as proof of delivery. "
                    f"(See gotchas.md Gotcha 2)"
                )
    return issues


# ── Orchestrator ───────────────────────────────────────────────────────────────

def check_fsc_document_generation(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = collect_apex_files(manifest_dir)

    if not apex_files:
        # No Apex found — not necessarily an error, but note it
        return issues

    issues.extend(check_docgen_rate_limit_handling(apex_files))
    issues.extend(check_batch_allows_callouts(apex_files))
    issues.extend(check_omniscript_in_batch_context(apex_files))
    issues.extend(check_document_builder_usage(apex_files))
    issues.extend(check_docgen_without_consent_record(apex_files))

    return issues


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for FSC Document Generation anti-patterns. "
            "Detects missing rate-limit handling, absent consent records, Document Builder "
            "misuse, and OmniScript batch anti-patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsc_document_generation(manifest_dir)

    if not issues:
        print("No FSC document generation issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
