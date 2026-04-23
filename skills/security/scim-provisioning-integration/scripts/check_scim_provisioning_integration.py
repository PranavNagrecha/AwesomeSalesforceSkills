#!/usr/bin/env python3
"""Check a SCIM mapping document for deprovisioning completeness.

Reads a SCIM mapping YAML or markdown doc and flags missing concerns:
- No OAuth token revoke step.
- No record ownership reassignment step.
- IdP groups mapped directly to Profiles.
- No monitoring / SLA section.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_MARKERS = {
    "oauth token": "No OAuth token revoke step found in the deprovisioning runbook",
    "reassign": "No record ownership reassignment step found",
    "freeze": "No freeze step found — freeze-first is the common safe default",
    "monitor": "No monitoring/SLA section found",
    "permission set": "No Permission Set mapping discussed",
}

PROFILE_MAPPING_MARKERS = (
    "group to profile",
    "group-to-profile",
    "maps to profile",
    "-> profile",
    "→ profile",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect SCIM mapping / runbook docs for completeness.",
    )
    parser.add_argument(
        "--doc",
        required=True,
        help="Path to the SCIM mapping doc (markdown or yaml).",
    )
    return parser.parse_args()


def check_doc(path: Path) -> list[str]:
    issues: list[str] = []
    if not path.exists():
        return [f"Doc not found: {path}"]

    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for marker, message in REQUIRED_MARKERS.items():
        if marker not in text:
            issues.append(f"{path}: {message}")

    for marker in PROFILE_MAPPING_MARKERS:
        if marker in text:
            issues.append(
                f"{path}: appears to map IdP groups to Profiles — prefer Permission Sets / PSGs"
            )
            break

    return issues


def main() -> int:
    args = parse_args()
    issues = check_doc(Path(args.doc))

    if not issues:
        print("No SCIM provisioning gaps found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
