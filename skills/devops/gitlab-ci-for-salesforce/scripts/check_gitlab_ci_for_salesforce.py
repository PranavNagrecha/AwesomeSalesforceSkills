#!/usr/bin/env python3
"""Checker script for GitLab CI for Salesforce skill.

Analyzes a .gitlab-ci.yml file for common security and best-practice issues
specific to Salesforce CI/CD pipelines.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_gitlab_ci_for_salesforce.py [--help]
    python3 check_gitlab_ci_for_salesforce.py --gitlab-ci-file .gitlab-ci.yml
    python3 check_gitlab_ci_for_salesforce.py --manifest-dir path/to/repo
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a .gitlab-ci.yml file for common issues in Salesforce CI/CD pipelines."
        ),
    )
    parser.add_argument(
        "--gitlab-ci-file",
        default=".gitlab-ci.yml",
        help="Path to the .gitlab-ci.yml file to check (default: .gitlab-ci.yml).",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help=(
            "Root directory to search for .gitlab-ci.yml if --gitlab-ci-file is not given "
            "(default: current directory)."
        ),
    )
    return parser.parse_args()


def _find_gitlab_ci(manifest_dir: Path, gitlab_ci_file: str) -> Path | None:
    """Return the path to .gitlab-ci.yml, searching manifest_dir if needed."""
    explicit = Path(gitlab_ci_file)
    if explicit.exists():
        return explicit
    candidate = manifest_dir / ".gitlab-ci.yml"
    if candidate.exists():
        return candidate
    return None


def check_no_base64_decode_for_key(content: str) -> list[str]:
    """Check that private key variables are decoded via base64 before use."""
    issues: list[str] = []
    # Detect patterns like: echo "$SF_JWT.*KEY.*" > /tmp/  without base64 -d
    raw_write_pattern = re.compile(
        r'echo\s+"?\$(?:SF_JWT[A-Z_]*KEY[A-Z_]*)"?\s*>\s*/tmp/',
        re.IGNORECASE,
    )
    base64_decode_pattern = re.compile(
        r'echo\s+"?\$(?:SF_JWT[A-Z_]*KEY[A-Z_]*)"?\s*\|\s*base64\s+-d',
        re.IGNORECASE,
    )
    raw_matches = raw_write_pattern.findall(content)
    decode_matches = base64_decode_pattern.findall(content)
    if raw_matches and not decode_matches:
        issues.append(
            "SECURITY: Private key written to /tmp without base64 decoding. "
            "GitLab cannot mask multi-line PEM values. "
            "Store key as base64 -w 0 encoded value and decode with: "
            "echo \"$SF_JWT_SERVER_KEY\" | base64 -d > /tmp/server.key"
        )
    return issues


def check_after_script_cleanup(content: str) -> list[str]:
    """Check that key file cleanup is in after_script, not only in script."""
    issues: list[str] = []
    has_key_write = bool(re.search(r"/tmp/server\.key", content, re.IGNORECASE))
    if not has_key_write:
        return issues
    has_after_script_rm = bool(
        re.search(r"after_script\s*:.*?rm\s+-f\s+/tmp/server\.key", content, re.DOTALL)
    )
    if not has_after_script_rm:
        issues.append(
            "SECURITY: /tmp/server.key is written but not removed in after_script:. "
            "Key file cleanup must be in after_script: to run even if the job fails. "
            "Add: after_script:\\n  - rm -f /tmp/server.key"
        )
    return issues


def check_no_only_except(content: str) -> list[str]:
    """Check for deprecated only: / except: branch conditions."""
    issues: list[str] = []
    # Match 'only:' or 'except:' at the start of a line (job-level key)
    only_pattern = re.compile(r"^\s{0,4}(only|except)\s*:", re.MULTILINE)
    matches = only_pattern.findall(content)
    if matches:
        issues.append(
            f"STYLE: Deprecated '{matches[0]}:' branch condition found. "
            "Migrate to 'rules:' for reliable branch matching and support for "
            "$CI_PIPELINE_SOURCE, when: manual, and complex conditions."
        )
    return issues


def check_test_level_on_deploy(content: str) -> list[str]:
    """Check that sf project deploy start includes --test-level."""
    issues: list[str] = []
    # Find all sf project deploy start calls
    deploy_calls = re.findall(
        r"sf\s+project\s+deploy\s+start[^\n]*", content
    )
    for call in deploy_calls:
        if "--test-level" not in call and "test-level" not in call:
            issues.append(
                f"CONFIG: 'sf project deploy start' found without --test-level: "
                f"  {call.strip()[:100]}\n"
                "  Omitting --test-level on sandbox deploys defaults to NoTestRun "
                "(zero tests run). Always specify --test-level explicitly."
            )
    return issues


def check_no_github_actions_syntax(content: str) -> list[str]:
    """Check for GitHub Actions syntax bleed in a GitLab CI file."""
    issues: list[str] = []
    ga_patterns = {
        r"^\s+uses\s*:": "uses: (GitHub Actions step syntax)",
        r"^\s+with\s*:": "with: (GitHub Actions input syntax)",
        r"if:\s*github\.": "if: github. (GitHub Actions condition syntax)",
        r"actions/checkout": "actions/checkout (GitHub Actions step reference)",
    }
    for pattern, description in ga_patterns.items():
        if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
            issues.append(
                f"SYNTAX: GitHub Actions syntax detected — '{description}'. "
                "GitLab CI uses script:, rules:, before_script:, after_script: — "
                "not uses:, with:, or GitHub-specific condition variables."
            )
    return issues


def check_instance_url_for_sandbox(content: str) -> list[str]:
    """Warn if login.salesforce.com is used as instance URL in a sandbox-named job."""
    issues: list[str] = []
    # Find job blocks that reference "sandbox" and check their instance-url
    sandbox_blocks = re.findall(
        r"((?:sandbox|develop)[^\n]*\n(?:.*\n){0,30}?)",
        content,
        re.IGNORECASE,
    )
    for block in sandbox_blocks:
        if "login.salesforce.com" in block and "test.salesforce.com" not in block:
            issues.append(
                "CONFIG: A sandbox-related job appears to use 'login.salesforce.com' "
                "instead of 'test.salesforce.com'. Sandboxes must authenticate via "
                "https://test.salesforce.com — using the production URL causes auth failures."
            )
            break  # Report once
    return issues


def check_sfdx_legacy_commands(content: str) -> list[str]:
    """Check for deprecated sfdx force:* command namespace."""
    issues: list[str] = []
    legacy_pattern = re.compile(r"\bsfdx\s+force:", re.IGNORECASE)
    matches = legacy_pattern.findall(content)
    if matches:
        issues.append(
            f"DEPRECATION: Legacy 'sfdx force:*' command found ({len(matches)} occurrence(s)). "
            "Migrate to 'sf' CLI v2 commands: "
            "'sf project deploy start', 'sf apex run test', 'sf org login jwt'."
        )
    return issues


def check_gitlab_ci_for_salesforce(gitlab_ci_path: Path) -> list[str]:
    """Run all checks against the .gitlab-ci.yml content. Return list of issues."""
    issues: list[str] = []

    if not gitlab_ci_path.exists():
        issues.append(f"FILE NOT FOUND: {gitlab_ci_path} — no .gitlab-ci.yml to check.")
        return issues

    content = gitlab_ci_path.read_text(encoding="utf-8")

    issues.extend(check_no_github_actions_syntax(content))
    issues.extend(check_no_base64_decode_for_key(content))
    issues.extend(check_after_script_cleanup(content))
    issues.extend(check_no_only_except(content))
    issues.extend(check_test_level_on_deploy(content))
    issues.extend(check_instance_url_for_sandbox(content))
    issues.extend(check_sfdx_legacy_commands(content))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    gitlab_ci_path = _find_gitlab_ci(manifest_dir, args.gitlab_ci_file)

    if gitlab_ci_path is None:
        print(
            f"ISSUE: No .gitlab-ci.yml found at '{args.gitlab_ci_file}' "
            f"or in '{manifest_dir}'."
        )
        return 1

    print(f"Checking: {gitlab_ci_path}")
    issues = check_gitlab_ci_for_salesforce(gitlab_ci_path)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
