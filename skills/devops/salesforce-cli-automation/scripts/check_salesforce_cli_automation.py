#!/usr/bin/env python3
"""Checker script for Salesforce CLI Automation skill.

Scans CI configuration and shell scripts for common Salesforce CLI automation issues:
legacy sfdx force commands, interactive login in headless contexts, missing explicit
org targeting on mutating sf commands, and missing machine-readable flags where
pipelines typically need them.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_salesforce_cli_automation.py [--help]
    python3 check_salesforce_cli_automation.py --manifest-dir path/to/project
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Salesforce CLI automation patterns in scripts and CI configs.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce project (default: current directory).",
    )
    return parser.parse_args()


def find_automation_files(root: Path) -> list[Path]:
    """Collect CI configs and shell scripts likely to contain sf/sfdx invocations."""
    patterns = [
        ".github/workflows/*.yml",
        ".github/workflows/*.yaml",
        ".gitlab-ci.yml",
        "Jenkinsfile",
        "azure-pipelines.yml",
        "bitbucket-pipelines.yml",
        ".circleci/config.yml",
        "Makefile",
    ]
    found: list[Path] = []
    for pattern in patterns:
        found.extend(root.glob(pattern))
    # Shell scripts at repo root and under scripts/ (shallow)
    found.extend(root.glob("*.sh"))
    scripts_dir = root / "scripts"
    if scripts_dir.is_dir():
        found.extend(scripts_dir.glob("*.sh"))
    # De-duplicate while preserving order
    seen: set[str] = set()
    unique: list[Path] = []
    for p in found:
        key = str(p.resolve())
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def check_legacy_sfdx_force(content: str, filepath: str) -> list[str]:
    issues: list[str] = []
    pat = re.compile(r"\bsfdx\s+force:", re.IGNORECASE)
    for i, line in enumerate(content.splitlines(), 1):
        if pat.search(line):
            issues.append(
                f"{filepath}:{i} — legacy `sfdx force:` usage. "
                "Migrate to `sf` CLI v2 commands per Salesforce CLI Reference."
            )
    return issues


def check_interactive_login_in_automation(content: str, filepath: str) -> list[str]:
    issues: list[str] = []
    pat = re.compile(r"\bsf\s+org\s+login\s+web\b", re.IGNORECASE)
    for i, line in enumerate(content.splitlines(), 1):
        if pat.search(line):
            issues.append(
                f"{filepath}:{i} — `sf org login web` is interactive and unsuitable "
                "for headless automation; use JWT or another non-interactive flow."
            )
    return issues


def check_deprecated_npm_sfdx_cli(content: str, filepath: str) -> list[str]:
    issues: list[str] = []
    if re.search(r"npm\s+install\s+(-g\s+)?sfdx-cli\b", content, re.IGNORECASE):
        issues.append(
            f"{filepath} — installs deprecated `sfdx-cli` npm package. "
            "Prefer supported Salesforce CLI installation or `@salesforce/cli`."
        )
    return issues


def check_mutating_sf_without_target_org(content: str, filepath: str) -> list[str]:
    """Warn when mutating sf topics run without --target-org in automation files."""
    issues: list[str] = []
    mutating = re.compile(
        r"\bsf\s+(project\s+deploy|project\s+delete|data\s+(create|upsert|delete|import|export)|apex\s+run|org\s+delete)",
        re.IGNORECASE,
    )
    lines = content.splitlines()
    for i, line in enumerate(lines, 1):
        if not mutating.search(line):
            continue
        window = "\n".join(lines[max(0, i - 2) : min(len(lines), i + 6)])
        if not re.search(r"--target-org\b", window, re.IGNORECASE) and not re.search(
            r"SF_TARGET_ORG", window
        ):
            issues.append(
                f"{filepath}:{i} — mutating `sf` command without `--target-org` "
                "or SF_TARGET_ORG in nearby lines; default org may be wrong on runners."
            )
    return issues


def check_deploy_missing_json_when_parsed(content: str, filepath: str) -> list[str]:
    """If file uses jq on sf output, ensure sf deploy uses --json."""
    issues: list[str] = []
    if "jq" not in content:
        return issues
    for i, line in enumerate(content.splitlines(), 1):
        if re.search(r"\bsf\s+project\s+deploy\s+(start|validate)\b", line, re.IGNORECASE):
            window_start = max(0, i - 1)
            window_end = min(len(content.splitlines()), i + 8)
            block = "\n".join(content.splitlines()[window_start:window_end])
            if "jq" in block and "--json" not in block:
                issues.append(
                    f"{filepath}:{i} — `jq` appears near `sf project deploy` but no "
                    "`--json` flag found in the command block; human output will not parse."
                )
    return issues


def check_apex_test_missing_result_format_in_ci(content: str, filepath: str) -> list[str]:
    issues: list[str] = []
    for i, line in enumerate(content.splitlines(), 1):
        if not re.search(r"\bsf\s+apex\s+run\s+test\b", line, re.IGNORECASE):
            continue
        window_start = max(0, i - 1)
        window_end = min(len(content.splitlines()), i + 10)
        block = "\n".join(content.splitlines()[window_start:window_end])
        if not re.search(r"--result-format\b", block, re.IGNORECASE):
            issues.append(
                f"{filepath}:{i} — `sf apex run test` without `--result-format` "
                "nearby; CI should emit junit or json for dashboards and archives."
            )
    return issues


def check_salesforce_cli_automation(manifest_dir: Path) -> tuple[list[str], bool]:
    """Return (issues, scanned_any_files)."""
    issues: list[str] = []

    if not manifest_dir.exists():
        return ([f"Project directory not found: {manifest_dir}"], False)

    files = find_automation_files(manifest_dir)
    if not files:
        # Not an error: many metadata-only repos have no checked-in CI at this path.
        return ([], False)

    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            issues.append(f"{path}: could not read file ({exc})")
            continue
        rel = str(path.relative_to(manifest_dir))
        issues.extend(check_legacy_sfdx_force(text, rel))
        issues.extend(check_interactive_login_in_automation(text, rel))
        issues.extend(check_deprecated_npm_sfdx_cli(text, rel))
        issues.extend(check_mutating_sf_without_target_org(text, rel))
        issues.extend(check_deploy_missing_json_when_parsed(text, rel))
        issues.extend(check_apex_test_missing_result_format_in_ci(text, rel))

    return (issues, True)


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()
    issues, scanned = check_salesforce_cli_automation(manifest_dir)

    if not issues and not scanned:
        print(
            "No CI or shell automation files matched search paths; nothing to check.",
            file=sys.stdout,
        )
        return 0

    if not issues:
        print("No issues found.", file=sys.stdout)
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
