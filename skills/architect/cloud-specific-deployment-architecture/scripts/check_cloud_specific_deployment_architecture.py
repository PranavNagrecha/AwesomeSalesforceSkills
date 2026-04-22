#!/usr/bin/env python3
"""Checker script for Cloud-Specific Deployment Architecture skill.

Scans a repo for multi-cloud deploy hygiene issues:
- Agentforce Topic metadata that references Action classes missing from the repo
- Single-step sfdx deploy expected to cover Marketing Cloud or Commerce Cloud assets
- OmniStudio components present without migration-tool ordering hints

Usage:
    python3 check_cloud_specific_deployment_architecture.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ACTION_REF_PAT = re.compile(r"<actionName>([^<]+)</actionName>")
MC_HINT_PAT = re.compile(r"(?i)(marketingcloud|data\s*extension|mc[-_]?devtools)")
COMMERCE_HINT_PAT = re.compile(r"(?i)(sfcc|commerce\s*cloud|cartridge)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check cloud-specific deployment hygiene.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of Salesforce metadata.")
    return parser.parse_args()


def list_apex_classes(root: Path) -> set[str]:
    classes_dir = root / "classes"
    if not classes_dir.exists():
        return set()
    return {p.stem.replace(".cls-meta", "") for p in classes_dir.glob("*.cls")}


def check_agent_action_refs(root: Path) -> list[str]:
    issues: list[str] = []
    bot_dir = root / "bots"
    if not bot_dir.exists():
        return issues
    known = list_apex_classes(root)
    for path in bot_dir.rglob("*.xml"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        actions = ACTION_REF_PAT.findall(text)
        for action in actions:
            if action and action not in known:
                issues.append(
                    f"{path.relative_to(root)}: references action '{action}' not present in classes/"
                )
    return issues


def check_omnistudio_ordering(root: Path) -> list[str]:
    issues: list[str] = []
    omni_dir = root / "omniscripts"
    dr_dir = root / "dataraptors"
    ip_dir = root / "integrationprocedures"
    if omni_dir.exists() and not (dr_dir.exists() or ip_dir.exists()):
        issues.append(
            "OmniScripts present but no DataRaptors/IntegrationProcedures siblings; confirm ordered deploy"
        )
    return issues


def check_pipeline_coverage(root: Path) -> list[str]:
    issues: list[str] = []
    candidates = []
    for name in (".github/workflows", "ci", "pipelines"):
        candidate = root / name
        if candidate.exists():
            candidates.extend(candidate.rglob("*.yml"))
            candidates.extend(candidate.rglob("*.yaml"))
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        has_mc = MC_HINT_PAT.search(text)
        has_commerce = COMMERCE_HINT_PAT.search(text)
        has_sfdx = re.search(r"(?i)sfdx|sf\s+project\s+deploy", text)
        if has_sfdx and (has_mc or has_commerce):
            if not re.search(r"(?i)(mcdev|sfcc-ci|build\s*api)", text):
                issues.append(
                    f"{path.relative_to(root)}: mentions Marketing/Commerce Cloud with sfdx-only deploy step"
                )
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.exists():
        print(f"ERROR: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    issues: list[str] = []
    issues.extend(check_agent_action_refs(manifest_dir))
    issues.extend(check_omnistudio_ordering(manifest_dir))
    issues.extend(check_pipeline_coverage(manifest_dir))

    if not issues:
        print("No cloud-specific deployment issues detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
