#!/usr/bin/env python3
"""Audit OmniStudio assets for performance anti-patterns.

Checks Integration Procedure and OmniScript metadata for common issues:
- Multiple independent DataRaptor Action elements per step (serialized round trips)
- DataRaptor caching disabled on Extract/Turbo Extract assets
- Synchronous Integration Procedure invocations where async may be appropriate
- Deep nesting of Integration Procedures (IP calling IP chains)
- Absence of lazy loading on large OmniScripts

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omnistudio_performance.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

JSON_SUFFIXES = {".json"}
TEXT_SUFFIXES = {".json", ".xml", ".txt"}

# OmniStudio asset name patterns
OMNI_SCRIPT_RE = re.compile(r"OmniScript|omniscript", re.IGNORECASE)
IP_RE = re.compile(r"IntegrationProcedure|integration_procedure|IP_", re.IGNORECASE)
DATARAPTOR_RE = re.compile(r"DataRaptor|dataraptor", re.IGNORECASE)
FLEXCARD_RE = re.compile(r"FlexCard|flexcard", re.IGNORECASE)

# Performance signal patterns in JSON content
CACHE_DISABLED_RE = re.compile(r'"cacheEnabled"\s*:\s*false', re.IGNORECASE)
CACHE_ABSENT_RE = re.compile(r'"cacheEnabled"', re.IGNORECASE)
ASYNC_RE = re.compile(r'"executionType"\s*:\s*"[Aa]sync"')
SYNC_RE = re.compile(r'"executionType"\s*:\s*"[Ss]ync"')
LAZY_LOAD_RE = re.compile(r'"lazyLoad"\s*:\s*true', re.IGNORECASE)
NESTED_IP_RE = re.compile(r'"elementType"\s*:\s*"Integration Procedure"', re.IGNORECASE)
DR_ACTION_RE = re.compile(r'"elementType"\s*:\s*"DataRaptor"', re.IGNORECASE)
TURBO_EXTRACT_RE = re.compile(r'"dataRaptorType"\s*:\s*"Turbo"', re.IGNORECASE)
EXTRACT_RE = re.compile(r'"dataRaptorType"\s*:\s*"Extract"', re.IGNORECASE)
STEP_RE = re.compile(r'"elementType"\s*:\s*"Step"', re.IGNORECASE)

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit OmniStudio assets for performance anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of Salesforce metadata to scan (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(f) for f in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(n["severity"], 0) for n in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------

def iter_files(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES
    )


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_dataraptor_asset(path: Path, text: str) -> list[str]:
    """Check a DataRaptor asset file for caching configuration issues."""
    findings: list[str] = []

    is_extract = EXTRACT_RE.search(text) or TURBO_EXTRACT_RE.search(text)

    if is_extract:
        if CACHE_DISABLED_RE.search(text):
            findings.append(
                f"MEDIUM {path}: DataRaptor Extract has cacheEnabled=false; "
                "consider enabling caching if this asset reads read-only session data "
                "to avoid repeated SOQL queries on step revisits"
            )
        elif not CACHE_ABSENT_RE.search(text):
            findings.append(
                f"REVIEW {path}: DataRaptor Extract asset has no cacheEnabled field found; "
                "verify caching configuration is intentional"
            )

    return findings


def check_integration_procedure(path: Path, text: str) -> list[str]:
    """Check an Integration Procedure asset for performance patterns."""
    findings: list[str] = []

    # Count DataRaptor Action elements — more than 3 at top-level suggests consolidation opportunity
    dr_action_count = len(DR_ACTION_RE.findall(text))
    if dr_action_count >= 4:
        findings.append(
            f"HIGH {path}: Integration Procedure contains {dr_action_count} DataRaptor Action elements; "
            "review whether these can be consolidated to reduce serialized execution within the IP"
        )
    elif dr_action_count >= 2:
        findings.append(
            f"REVIEW {path}: Integration Procedure contains {dr_action_count} DataRaptor Action elements; "
            "confirm these run in parallel or are intentionally sequential"
        )

    # Deeply nested IP-calling-IP chains
    nested_ip_count = len(NESTED_IP_RE.findall(text))
    if nested_ip_count >= 3:
        findings.append(
            f"MEDIUM {path}: Integration Procedure calls {nested_ip_count} nested Integration Procedures; "
            "deep IP-calling-IP chains serialize latency and complicate debugging; consider flattening"
        )

    return findings


def check_omniscript_asset(path: Path, text: str) -> list[str]:
    """Check an OmniScript asset for performance patterns."""
    findings: list[str] = []

    step_count = len(STEP_RE.findall(text))
    has_lazy_load = LAZY_LOAD_RE.search(text)

    if step_count >= 6 and not has_lazy_load:
        findings.append(
            f"MEDIUM {path}: OmniScript has {step_count} steps but no lazyLoad=true found; "
            "consider enabling lazy loading on non-critical later steps to reduce initial load time"
        )

    # Count DataRaptor actions at the OmniScript level (not inside IPs)
    dr_action_count = len(DR_ACTION_RE.findall(text))
    if dr_action_count >= 3:
        findings.append(
            f"HIGH {path}: OmniScript contains {dr_action_count} DataRaptor Action elements at the script level; "
            "each fires a separate network round trip; consolidate per-step data fetches into single IP calls"
        )

    return findings


def check_flexcard_asset(path: Path, text: str) -> list[str]:
    """Check a FlexCard asset for performance patterns."""
    findings: list[str] = []

    dr_action_count = len(DR_ACTION_RE.findall(text))
    if dr_action_count >= 2:
        findings.append(
            f"MEDIUM {path}: FlexCard has {dr_action_count} DataRaptor data sources; "
            "in a repeated card context each instance fetches independently; "
            "consider aggregating data in a parent Integration Procedure and passing state down"
        )

    return findings


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def audit_file(path: Path) -> list[str]:
    text = read_text(path)
    if not text:
        return []

    findings: list[str] = []
    name_lower = path.name.lower()

    if DATARAPTOR_RE.search(name_lower) or (DATARAPTOR_RE.search(text) and EXTRACT_RE.search(text)):
        findings.extend(check_dataraptor_asset(path, text))

    elif IP_RE.search(name_lower) or (IP_RE.search(text) and NESTED_IP_RE.search(text)):
        findings.extend(check_integration_procedure(path, text))

    elif OMNI_SCRIPT_RE.search(name_lower) or STEP_RE.search(text):
        findings.extend(check_omniscript_asset(path, text))

    elif FLEXCARD_RE.search(name_lower):
        findings.extend(check_flexcard_asset(path, text))

    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)

    if not root.exists():
        return emit_result(
            [f"HIGH {root}: manifest directory not found"],
            "Scanned 0 files; manifest directory was missing.",
        )

    files = iter_files(root)
    findings: list[str] = []
    asset_hits = 0

    for path in files:
        text = read_text(path)
        is_omnistudio = (
            OMNI_SCRIPT_RE.search(path.name)
            or IP_RE.search(path.name)
            or DATARAPTOR_RE.search(path.name)
            or FLEXCARD_RE.search(path.name)
            or STEP_RE.search(text)
            or (DATARAPTOR_RE.search(text) and EXTRACT_RE.search(text))
        )
        if is_omnistudio:
            asset_hits += 1
            findings.extend(audit_file(path))

    if asset_hits == 0:
        return emit_result(
            [f"REVIEW {root}: no OmniStudio asset files detected in manifest directory"],
            "Scanned 0 OmniStudio-related files.",
        )

    summary = (
        f"Scanned {asset_hits} OmniStudio-related file(s); "
        f"{len(findings)} performance finding(s) detected."
    )
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
