#!/usr/bin/env python3
"""Audit metadata for baseline org-hardening signals."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check metadata for missing baseline hardening assets and exception sprawl signals.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan for Salesforce metadata.")
    return parser.parse_args()


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(item) for item in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


def count_matches(root: Path, pattern: str) -> int:
    return sum(1 for _ in root.rglob(pattern))


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 metadata files; manifest directory was missing.")

    settings_count = count_matches(root, "*.settings-meta.xml")
    csp_count = count_matches(root, "*CspTrustedSite*")
    cors_count = count_matches(root, "*CorsWhitelistOrigin*")
    network_count = count_matches(root, "*NetworkAccess*")

    findings: list[str] = []
    if settings_count == 0:
        findings.append(f"REVIEW {root}: no settings metadata files found; verify baseline security settings are tracked as metadata")
    if csp_count + cors_count + network_count == 0:
        findings.append(f"REVIEW {root}: no obvious CSP, CORS, or network-control metadata found; verify baseline trust controls are managed intentionally")
    if csp_count > 25:
        findings.append(f"REVIEW {root}: {csp_count} CSP-related artifacts found; verify trusted-site sprawl has active governance")

    scanned = settings_count + csp_count + cors_count + network_count
    if scanned == 0:
        return emit_result([f"HIGH {root}: no relevant hardening metadata found"], "Scanned 0 metadata files; no settings or trust-control metadata artifacts were found.")
    summary = f"Observed {settings_count} settings file(s), {csp_count} CSP artifact(s), {cors_count} CORS artifact(s), and {network_count} network-control artifact(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
