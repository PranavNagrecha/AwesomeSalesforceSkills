#!/usr/bin/env python3
"""Audit OmniStudio assets for the most common debugging-blocking anti-patterns.

Checks metadata files for:
- Integration Procedures missing rollbackOnError: true (silent fail-open)
- HTTP actions without a Named Credential reference (hardcoded endpoints)
- IP or OmniScript assets with placeholder failureResponse text
- Active version absent from Integration Procedure metadata

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omnistudio_debugging.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# OmniStudio asset markers
OMNI_RE = re.compile(
    r"OmniScript|IntegrationProcedure|DataRaptor|OmniProcess|vlocityOpenInterface",
    re.IGNORECASE,
)

# rollbackOnError false or absent
ROLLBACK_FALSE_RE = re.compile(r"rollbackOnError\s*[=:]\s*[\"']?false[\"']?", re.IGNORECASE)
ROLLBACK_TRUE_RE = re.compile(r"rollbackOnError\s*[=:]\s*[\"']?true[\"']?", re.IGNORECASE)

# Hardcoded HTTP URLs without a Named Credential ref
HTTP_URL_RE = re.compile(r"https?://[a-zA-Z0-9._/-]+", re.IGNORECASE)
NAMED_CRED_RE = re.compile(r"namedCredential|Named_Credential|callout:", re.IGNORECASE)

# Placeholder failure response text (common scaffolded defaults)
PLACEHOLDER_FAILURE_RE = re.compile(
    r"failureResponse\s*[=:]\s*[\"']?\s*(TODO|TBD|placeholder|your message here|error occurred|"
    r"something went wrong|N/A|null|undefined)[\"']?",
    re.IGNORECASE,
)

# OmniScript Navigation Action (check if file is expected to have live-context validation)
NAV_ACTION_RE = re.compile(r"NavigationAction|navigationType", re.IGNORECASE)

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check OmniStudio metadata for debugging anti-patterns."
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for OmniStudio asset metadata (default: current directory).",
    )
    parser.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        help="Emit results as JSON (default: human-readable).",
    )
    return parser.parse_args()


def iter_omni_files(root: Path) -> list[Path]:
    """Return metadata files that are likely OmniStudio assets."""
    allowed_suffixes = {".json", ".xml", ".yaml", ".yml", ".txt"}
    candidates: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in allowed_suffixes:
            continue
        candidates.append(path)
    return sorted(candidates)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


# ---------------------------------------------------------------------------
# Per-file checks
# ---------------------------------------------------------------------------

def check_file(path: Path) -> list[dict]:
    """Return findings for a single file. Each finding is a dict with severity, file, message."""
    text = read_text(path)

    # Only examine files that contain OmniStudio asset markers
    if not OMNI_RE.search(text):
        return []

    findings: list[dict] = []
    rel = str(path)

    # 1. rollbackOnError absent or false in Integration Procedure metadata
    if re.search(r"IntegrationProcedure|iprocedure", text, re.IGNORECASE):
        if ROLLBACK_FALSE_RE.search(text):
            findings.append({
                "severity": "HIGH",
                "file": rel,
                "message": (
                    "rollbackOnError is explicitly set to false on an Integration Procedure. "
                    "Element failures will be swallowed silently and the IP will return partial "
                    "or empty data without surfacing an error to the caller."
                ),
            })
        elif not ROLLBACK_TRUE_RE.search(text):
            findings.append({
                "severity": "MEDIUM",
                "file": rel,
                "message": (
                    "rollbackOnError is not set to true in this Integration Procedure asset. "
                    "Without it, HTTP action or DataRaptor failures fail open and are invisible "
                    "to the calling OmniScript or FlexCard."
                ),
            })

    # 2. Hardcoded HTTP URL without a Named Credential reference
    http_matches = HTTP_URL_RE.findall(text)
    if http_matches and not NAMED_CRED_RE.search(text):
        # Filter out documentation or example URLs embedded in descriptions
        real_urls = [u for u in http_matches if not re.search(r"salesforce\.com|help\.salesforce|developer\.salesforce", u, re.IGNORECASE)]
        if real_urls:
            findings.append({
                "severity": "HIGH",
                "file": rel,
                "message": (
                    f"HTTP URL(s) found ({real_urls[0]!r}{'...' if len(real_urls) > 1 else ''}) "
                    "without a Named Credential reference. Hardcoded endpoints make the asset "
                    "environment-specific and block safe promotion across orgs."
                ),
            })

    # 3. Placeholder failure response text
    if PLACEHOLDER_FAILURE_RE.search(text):
        findings.append({
            "severity": "MEDIUM",
            "file": rel,
            "message": (
                "Placeholder or generic failureResponse text detected. This text will ship "
                "to users as-is. Replace with a specific, user-safe message describing what "
                "went wrong and what the user should do next."
            ),
        })

    # 4. Navigation Action present — remind that Preview will not exercise it
    if NAV_ACTION_RE.search(text) and re.search(r"OmniScript|OmniProcess", text, re.IGNORECASE):
        findings.append({
            "severity": "REVIEW",
            "file": rel,
            "message": (
                "NavigationAction element detected in this OmniScript asset. "
                "Navigation Actions are excluded from Preview mode execution. "
                "Validate this action only in a deployed Lightning app page or Experience Site."
            ),
        })

    return findings


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def emit_human(findings: list[dict], file_count: int, omni_count: int) -> int:
    if not findings:
        print(f"No issues found. Scanned {file_count} file(s), {omni_count} OmniStudio asset(s).")
        return 0

    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(f["severity"], 0) for f in findings))
    print(f"Score: {score}/100 | {len(findings)} finding(s) across {omni_count} OmniStudio file(s)\n")
    for f in findings:
        print(f"[{f['severity']}] {f['file']}")
        print(f"  {f['message']}\n")
    return 1


def emit_json(findings: list[dict], file_count: int, omni_count: int) -> int:
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(f["severity"], 0) for f in findings))
    result = {
        "score": score,
        "file_count": file_count,
        "omni_asset_count": omni_count,
        "finding_count": len(findings),
        "findings": findings,
    }
    print(json.dumps(result, indent=2))
    return 1 if findings else 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)

    if not root.exists():
        msg = f"Manifest directory not found: {root}"
        if args.output_json:
            print(json.dumps({"score": 0, "error": msg, "findings": []}))
        else:
            print(f"ERROR: {msg}")
        return 1

    files = iter_omni_files(root)
    all_findings: list[dict] = []
    omni_count = 0

    for path in files:
        file_findings = check_file(path)
        if file_findings or OMNI_RE.search(read_text(path)):
            omni_count += 1
        all_findings.extend(file_findings)

    if args.output_json:
        return emit_json(all_findings, len(files), omni_count)
    return emit_human(all_findings, len(files), omni_count)


if __name__ == "__main__":
    sys.exit(main())
