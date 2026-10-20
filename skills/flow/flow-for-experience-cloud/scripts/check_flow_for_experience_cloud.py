#!/usr/bin/env python3
"""Checker script for Flow For Experience Cloud skill.

Heuristic review of a metadata directory:
- LWR markers in site files next to screen flows that place a custom Lightning component on a screen.
  A custom component sits in FlowScreenField `extensionName` ("the name of the Lightning component to
  display", api_meta 264 L74393-74395); the old rule looked for a <componentName> element that
  FlowScreenField does not have. Standard `flowruntime:` components are skipped (that prefix is
  UNVERIFIED, 2026-10-20: not in either corpus), as is LWR incompatibility itself.
- Guest profiles that grant Apex class or object access (guest access is a public-surface decision;
  guest org-wide defaults are Private and fixed, secguide 262 L2868-2869).
- Flows whose runInMode is SystemModeWithoutSharing ("can access all data", api_meta 264 L70919-70921).

Severity contract: a missing directory is an ERROR (exit 1 always). Every other finding is REVIEW and
exits 0 unless --strict. A directory with no files is one WARN, exit 0.

Uses stdlib only. Usage:
    python3 check_flow_for_experience_cloud.py --manifest-dir path/to/metadata [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SITE_SUFFIXES = (".xml", ".json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Flow For Experience Cloud configuration and metadata for common issues.",
    )
    parser.add_argument("--manifest-dir", default=".", help="Root directory of the Salesforce metadata (default: .).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on REVIEW/WARN findings too.")
    return parser.parse_args()


def custom_component_flows(manifest_dir: Path) -> list[Path]:
    found = []
    for flow_path in sorted(manifest_dir.rglob("*.flow-meta.xml")):
        text = flow_path.read_text(encoding="utf-8", errors="ignore")
        names = re.findall(r"<extensionName>([^<]+)</extensionName>", text)
        if any(not n.strip().lower().startswith("flowruntime:") for n in names):
            found.append(flow_path)
    return found


def has_lwr_marker(manifest_dir: Path) -> bool:
    for candidate in manifest_dir.rglob("*"):
        if not candidate.is_file() or candidate.suffix not in SITE_SUFFIXES:
            continue
        path_text = str(candidate).lower()
        if "experience" not in path_text and "site" not in path_text:
            continue
        if re.search(r"\blwr\b", candidate.read_text(encoding="utf-8", errors="ignore").lower()):
            return True
    return False


def scan(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    custom = custom_component_flows(manifest_dir)
    if custom and has_lwr_marker(manifest_dir):
        issues.append(
            "REVIEW: LWR site markers were found alongside screen flows with custom components "
            f"({', '.join(p.name for p in custom)}); review `lightning-flow` compatibility before exposing them (LWR limits UNVERIFIED, 2026-10-20)."
        )
    for profile_path in sorted(manifest_dir.rglob("*Guest*.profile-meta.xml")):
        text = profile_path.read_text(encoding="utf-8", errors="ignore")
        if "<classAccesses>" in text or "<objectPermissions>" in text:
            issues.append(
                f"REVIEW: {profile_path}: guest profile grants Apex or object access; treat every Experience Cloud flow that depends on it as a public-surface security decision."
            )
    for flow_path in sorted(manifest_dir.rglob("*.flow-meta.xml")):
        text = flow_path.read_text(encoding="utf-8", errors="ignore")
        if "<runInMode>SystemModeWithoutSharing</runInMode>" in text:
            issues.append(
                f"REVIEW: {flow_path}: runInMode SystemModeWithoutSharing can access all data; confirm it is intended for any guest or external audience."
            )
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.is_dir():
        print(f"ERROR: manifest directory not found: {manifest_dir}")
        sys.exit(1)
    if not any(manifest_dir.iterdir()):
        print(f"WARN: {manifest_dir} is empty; nothing to check.")
        return 1 if args.strict else 0

    issues = scan(manifest_dir)
    if not issues:
        print("No issues found.")
        return 0
    for issue in issues:
        print(issue)
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
