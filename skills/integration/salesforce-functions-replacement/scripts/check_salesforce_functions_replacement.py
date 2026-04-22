#!/usr/bin/env python3
"""Checker script for Salesforce Functions Replacement skill.

Scans a repo for Functions residue that should be migrated off:
- project.toml / functions.yaml manifests
- Apex calls to `Function.get(...).invoke(...)`
- Auth Provider references in Named Credentials (legacy pattern)

Usage:
    python3 check_salesforce_functions_replacement.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


FUNCTION_INVOKE_PAT = re.compile(
    r"(?i)functions\.Function\.get\s*\(|Function\.get\s*\(\s*['\"][^'\"]+['\"]\s*\)\s*\.invoke"
)
PROJECT_TOML_HINT = re.compile(r"(?im)^\s*\[com\.salesforce\]|functions-project")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check for Salesforce Functions residue.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of the repo.")
    return parser.parse_args()


def check_functions_manifests(root: Path) -> list[str]:
    issues: list[str] = []
    for name in ("project.toml", "functions.yaml", "functions.yml"):
        for path in root.rglob(name):
            if "node_modules" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if PROJECT_TOML_HINT.search(text) or name.startswith("functions"):
                issues.append(
                    f"{path.relative_to(root)}: Salesforce Functions manifest present; Functions is retired"
                )
    return issues


def check_invoke_calls(root: Path) -> list[str]:
    issues: list[str] = []
    classes_dir = root / "classes"
    if not classes_dir.exists():
        return issues
    for path in classes_dir.rglob("*.cls"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if FUNCTION_INVOKE_PAT.search(text):
            issues.append(
                f"{path.relative_to(root)}: Function.get(...).invoke(...) call; replace with Heroku/External callout"
            )
    return issues


def check_auth_provider_usage(root: Path) -> list[str]:
    issues: list[str] = []
    nc_dir = root / "namedCredentials"
    if not nc_dir.exists():
        return issues
    for path in nc_dir.glob("*.namedCredential-meta.xml"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "<authProvider>" in text and "<externalClientApp>" not in text:
            issues.append(
                f"{path.relative_to(root)}: Named Credential on legacy Auth Provider; migrate to External Client App"
            )
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    issues: list[str] = []
    issues.extend(check_functions_manifests(root))
    issues.extend(check_invoke_calls(root))
    issues.extend(check_auth_provider_usage(root))

    if not issues:
        print("No Salesforce Functions residue detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
