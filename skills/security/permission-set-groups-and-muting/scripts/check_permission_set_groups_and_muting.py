#!/usr/bin/env python3
"""Audit metadata for profile-heavy access models and weak PSG adoption."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check metadata for permission-set-group and muting design smells.")
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


def count_matching(root: Path, pattern: str) -> int:
    return sum(1 for _ in root.rglob(pattern))


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 metadata files; manifest directory was missing.")

    profile_count = count_matching(root, "*.profile-meta.xml")
    psg_count = count_matching(root, "*.permissionsetgroup-meta.xml") + count_matching(root, "*PermissionSetGroup*")
    muting_count = count_matching(root, "*muting*") + count_matching(root, "*Muting*")

    findings: list[str] = []
    if profile_count > 10 and psg_count == 0:
        findings.append(f"REVIEW {root}: {profile_count} profile metadata files found with no obvious permission-set-group metadata; verify access is not still profile-heavy")
    if psg_count > 0 and muting_count == 0:
        findings.append(f"REVIEW {root}: permission-set-group metadata found without obvious muting assets; verify subtractive bundle scenarios were evaluated intentionally")

    scanned = profile_count + psg_count + muting_count
    if scanned == 0:
        return emit_result([f"HIGH {root}: no relevant security metadata found"], "Scanned 0 metadata files; no profile, PSG, or muting files were found.")
    summary = f"Observed {profile_count} profile file(s), {psg_count} PSG artifact(s), and {muting_count} muting-related artifact(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
