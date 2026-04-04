#!/usr/bin/env python3
"""Checker script for Bitbucket Pipelines for Salesforce skill.

Validates a bitbucket-pipelines.yml file for the most common Salesforce CI
anti-patterns: missing after-script cleanup, unquoted branch globs, missing
--test-level flags, hardcoded credentials, and deprecated sfdx commands.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_bitbucket_pipelines_for_salesforce.py [--help]
    python3 check_bitbucket_pipelines_for_salesforce.py --pipeline-file path/to/bitbucket-pipelines.yml
    python3 check_bitbucket_pipelines_for_salesforce.py  # searches current dir
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_file(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _find_pipeline_file(root: Path) -> Path | None:
    candidates = [
        root / "bitbucket-pipelines.yml",
        root / "bitbucket-pipelines.yaml",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_server_key_in_after_script(content: str) -> list[str]:
    """Warn if server.key is written in script: but not cleaned up in after-script:."""
    issues: list[str] = []
    # Detect any step that writes a key file
    writes_key = re.search(r'echo.*server\.key|>\s*/tmp/server\.key', content)
    if not writes_key:
        return issues

    # Look for after-script with rm of server.key
    has_after_cleanup = re.search(r'after-script\s*:', content) and re.search(
        r'rm\s+-f?\s+/tmp/server\.key', content
    )
    if not has_after_cleanup:
        issues.append(
            "SECURITY: Private key file (/tmp/server.key) is written but 'after-script:' "
            "cleanup (rm -f /tmp/server.key) was not detected. If the deploy step fails, "
            "the key file persists on the runner. Move 'rm -f /tmp/server.key' to "
            "an 'after-script:' block so it runs even on step failure."
        )
    return issues


def check_unquoted_branch_globs(content: str) -> list[str]:
    """Warn if branch patterns containing * are not quoted in YAML."""
    issues: list[str] = []
    # Match lines under 'branches:' that look like glob patterns without surrounding quotes
    # Pattern: a line that starts with whitespace, has a key containing * but no quotes
    unquoted = re.findall(
        r'^\s{4,}([^\'"\s][^:]*\*[^:]*):',
        content,
        flags=re.MULTILINE,
    )
    for pattern in unquoted:
        stripped = pattern.strip()
        # Skip if it looks like a YAML value not a branch key
        if stripped and not stripped.startswith('-'):
            issues.append(
                f"YAML: Branch pattern '{stripped}' contains a glob wildcard (*) but "
                "is not quoted. Unquoted glob patterns can be misinterpreted by some "
                "YAML parsers and silently never match. Wrap it in single quotes: "
                f"'{stripped}':"
            )
    return issues


def check_missing_test_level(content: str) -> list[str]:
    """Warn if sf project deploy start is used without --test-level."""
    issues: list[str] = []
    # Find all deploy start invocations
    deploy_invocations = re.finditer(
        r'sf\s+project\s+deploy\s+start([^\n]*(?:\n\s+--[^\n]*)*)',
        content,
        flags=re.MULTILINE,
    )
    for match in deploy_invocations:
        block = match.group(0)
        if '--test-level' not in block:
            # Extract a snippet for context
            snippet = block[:80].replace('\n', ' ').strip()
            issues.append(
                f"TEST GATE: 'sf project deploy start' invocation found without "
                f"'--test-level' flag: [{snippet}...]. Omitting --test-level defaults "
                "to NoTestRun on sandbox targets, silently skipping all Apex tests. "
                "Always specify --test-level explicitly (RunLocalTests for production, "
                "NoTestRun only if a prior test step enforces coverage)."
            )
    return issues


def check_deprecated_sfdx_commands(content: str) -> list[str]:
    """Warn if deprecated sfdx force:* commands are used."""
    issues: list[str] = []
    deprecated_patterns = [
        (r'sfdx\s+force:source:deploy', 'sfdx force:source:deploy', 'sf project deploy start'),
        (r'sfdx\s+force:source:retrieve', 'sfdx force:source:retrieve', 'sf project retrieve start'),
        (r'sfdx\s+force:apex:test:run', 'sfdx force:apex:test:run', 'sf apex run test'),
        (r'sfdx\s+auth:jwt:grant', 'sfdx auth:jwt:grant', 'sf org login jwt'),
        (r'sfdx\s+auth:sfdxurl:store', 'sfdx auth:sfdxurl:store', 'sf org login sfdx-url'),
        (r'sfdx\s+force:org:create', 'sfdx force:org:create', 'sf org create scratch'),
    ]
    for pattern, old_cmd, new_cmd in deprecated_patterns:
        if re.search(pattern, content):
            issues.append(
                f"DEPRECATED: '{old_cmd}' is a deprecated Salesforce CLI command "
                f"(sfdx force:* namespace). Replace with '{new_cmd}' (sf CLI v2). "
                "Deprecated commands will be removed in a future CLI release."
            )
    return issues


def check_hardcoded_credentials(content: str) -> list[str]:
    """Warn if credentials appear to be hardcoded rather than from variables."""
    issues: list[str] = []
    # Look for --client-id or --jwt-key-file with a literal value (not a $VARIABLE reference)
    hardcoded_patterns = [
        (r'--client-id\s+[^\$\s\'"][^\s]+', '--client-id'),
        (r'--username\s+[^\$\s\'"][^\s@]*@[^\s]+', '--username with literal email'),
    ]
    for pattern, label in hardcoded_patterns:
        match = re.search(pattern, content)
        if match:
            snippet = match.group(0)[:60]
            issues.append(
                f"SECURITY: Possible hardcoded value for '{label}': [{snippet}]. "
                "Credentials and usernames should be stored as secured (masked) "
                "Bitbucket repository variables and referenced via $VARIABLE_NAME, "
                "not hardcoded in bitbucket-pipelines.yml."
            )
    return issues


def check_sfdx_project_json(root: Path) -> list[str]:
    """Check that sfdx-project.json exists — required for sf CLI commands."""
    issues: list[str] = []
    sfdx_json = root / "sfdx-project.json"
    if not sfdx_json.exists():
        issues.append(
            "PROJECT STRUCTURE: 'sfdx-project.json' not found in the project root. "
            "This file is required for 'sf project deploy start' and other sf CLI "
            "commands to locate the source directory and package directories. "
            "Run 'sf project generate' to create a Salesforce DX project structure."
        )
    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_checks(pipeline_file: Path) -> list[str]:
    """Run all checks against the given pipeline file. Returns list of issue strings."""
    issues: list[str] = []
    root = pipeline_file.parent

    content = _read_file(pipeline_file)
    if content is None:
        issues.append(f"Cannot read pipeline file: {pipeline_file}")
        return issues

    issues.extend(check_server_key_in_after_script(content))
    issues.extend(check_unquoted_branch_globs(content))
    issues.extend(check_missing_test_level(content))
    issues.extend(check_deprecated_sfdx_commands(content))
    issues.extend(check_hardcoded_credentials(content))
    issues.extend(check_sfdx_project_json(root))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a bitbucket-pipelines.yml file for common Salesforce CI anti-patterns: "
            "missing after-script key cleanup, unquoted branch globs, missing --test-level, "
            "deprecated sfdx commands, and hardcoded credentials."
        ),
    )
    parser.add_argument(
        "--pipeline-file",
        default=None,
        help=(
            "Path to bitbucket-pipelines.yml (default: search current directory). "
            "Also accepts a project root directory."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.pipeline_file:
        p = Path(args.pipeline_file)
        if p.is_dir():
            pipeline_file = _find_pipeline_file(p)
            if pipeline_file is None:
                print(f"ERROR: No bitbucket-pipelines.yml found in {p}")
                return 2
        else:
            pipeline_file = p
            if not pipeline_file.exists():
                print(f"ERROR: File not found: {pipeline_file}")
                return 2
    else:
        pipeline_file = _find_pipeline_file(Path("."))
        if pipeline_file is None:
            print(
                "INFO: No bitbucket-pipelines.yml found in the current directory. "
                "Pass --pipeline-file to specify a path."
            )
            return 0

    print(f"Checking: {pipeline_file}")
    issues = run_checks(pipeline_file)

    if not issues:
        print("OK: No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")
        print()

    print(f"Found {len(issues)} issue(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
