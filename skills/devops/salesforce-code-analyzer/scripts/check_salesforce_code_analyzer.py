#!/usr/bin/env python3
"""Checker script for Salesforce Code Analyzer skill.

Validates that a Salesforce DX project is correctly configured for
Salesforce Code Analyzer v5 usage in CI and AppExchange contexts.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_salesforce_code_analyzer.py [--help]
    python3 check_salesforce_code_analyzer.py --manifest-dir path/to/project
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce DX project for Salesforce Code Analyzer v5 "
            "configuration issues and common anti-patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce DX project (default: current directory).",
    )
    return parser.parse_args()


# The v4 retirement (August 2025) removed the whole 'scanner' CLI topic, not just
# 'scanner run', and in both the 'sf scanner ...' and older 'sfdx scanner:...'
# spellings. Match the topic, then map the specific command.
LEGACY_TOPIC_PATTERN = re.compile(r"\b(?:sf|sfdx)\s+scanner\b[:\s]", re.IGNORECASE)

# (label, pattern, v5 equivalent) per the official v4-to-v5 migration guide.
# Ordered longest-match-first: 'scanner run dfa' must win over 'scanner run'.
LEGACY_COMMAND_MAP: list[tuple[str, re.Pattern[str], str]] = [
    ("scanner run dfa", re.compile(r"\bscanner[:\s]run\s+dfa\b", re.IGNORECASE),
     "'code-analyzer run --rule-selector sfge'"),
    ("scanner rule list", re.compile(r"\bscanner[:\s]rule[:\s]list\b", re.IGNORECASE),
     "'code-analyzer rules'"),
    ("scanner rule describe", re.compile(r"\bscanner[:\s]rule[:\s]describe\b", re.IGNORECASE),
     "'code-analyzer rules --view detail'"),
    ("scanner rule add/remove", re.compile(r"\bscanner[:\s]rule[:\s](?:add|remove)\b", re.IGNORECASE),
     "no equivalent command — add or remove custom rules in code-analyzer.yml"),
    ("scanner run", re.compile(r"\bscanner[:\s]run\b(?!\s+dfa\b)", re.IGNORECASE),
     "'code-analyzer run'"),
]

# Flags removed in v5. --pmdconfig/--eslintconfig have no flag replacement at all.
# These are checked separately from the command map because the common LLM error
# is a v5 command name carrying v4 flags ('code-analyzer run --category Security').
LEGACY_FLAG_MAP: list[tuple[str, str]] = [
    ("--category", "--rule-selector"),
    ("--engine", "--rule-selector"),
    ("--projectdir", "--workspace"),
    ("--pmdconfig", "engines.pmd.custom_rulesets in code-analyzer.yml (no flag equivalent)"),
    ("--eslintconfig", "engines.eslint.eslint_config_file in code-analyzer.yml (no flag equivalent)"),
]

# '--engine' and '--category' are generic enough that unrelated tooling uses them
# (docker, linters). Only attribute a flag to Code Analyzer when the invocation it
# belongs to actually names the tool, looking back a few lines so that backslash
# continuations and YAML block scalars still resolve to their command.
TOOL_MENTION_PATTERN = re.compile(r"\b(?:scanner|code-analyzer)\b", re.IGNORECASE)
_FLAG_CONTEXT_LINES = 3


def _flag_is_code_analyzer_scoped(lines: list[str], index: int) -> bool:
    """True when the command the flag on `lines[index]` belongs to names the tool."""
    start = max(0, index - _FLAG_CONTEXT_LINES)
    return any(TOOL_MENTION_PATTERN.search(line) for line in lines[start : index + 1])


def _legacy_hits(content: str) -> list[str]:
    """Return migration advice for every retired v4 command or flag in `content`."""
    hits: list[str] = []
    if LEGACY_TOPIC_PATTERN.search(content):
        for label, pattern, replacement in LEGACY_COMMAND_MAP:
            if pattern.search(content):
                hits.append(f"{label} -> {replacement}")
        if not hits:
            hits.append("'scanner' CLI topic -> 'code-analyzer'")

    lines = content.splitlines()
    for flag, replacement in LEGACY_FLAG_MAP:
        flag_pattern = re.compile(rf"(?<![\w-]){re.escape(flag)}(?![\w-])")
        for index, line in enumerate(lines):
            if flag_pattern.search(line) and _flag_is_code_analyzer_scoped(lines, index):
                hits.append(f"{flag} -> {replacement}")
                break
    return hits


def check_legacy_scanner_commands(manifest_dir: Path) -> list[str]:
    """Detect retired v4 'scanner' topic commands and flags in CI files and scripts."""
    issues: list[str] = []

    candidates: list[Path] = []

    # Check GitHub Actions workflows (.yml and .yaml)
    github_dir = manifest_dir / ".github" / "workflows"
    if github_dir.exists():
        candidates.extend(github_dir.glob("*.yml"))
        candidates.extend(github_dir.glob("*.yaml"))

    # Check shell scripts and Makefiles at project root
    for script_glob in ("*.sh", "Makefile", "Jenkinsfile", "*.groovy"):
        candidates.extend(manifest_dir.glob(script_glob))

    for path in candidates:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        hits = _legacy_hits(content)
        if hits:
            try:
                label = path.relative_to(manifest_dir)
            except ValueError:
                label = path.name
            issues.append(
                f"[v4-legacy] {label} uses Code Analyzer v4 syntax "
                f"(v4 retired August 2025): " + "; ".join(hits)
            )

    return issues


def check_code_analyzer_yml(manifest_dir: Path) -> list[str]:
    """Check for presence and basic validity of code-analyzer.yml config file."""
    issues: list[str] = []
    config_file = manifest_dir / "code-analyzer.yml"

    if not config_file.exists():
        issues.append(
            "[config-missing] No code-analyzer.yml found at project root. "
            "Create this file to enforce consistent scan settings across "
            "developers and CI. Without it, every invocation depends on "
            "manually-specified CLI flags."
        )
        return issues

    try:
        content = config_file.read_text(encoding="utf-8")
    except OSError:
        issues.append(f"[config-unreadable] Cannot read {config_file}.")
        return issues

    # Warn if node_modules is not excluded. The v5 top-level property is
    # 'ignores'; there is no 'global' / 'global.exclude' property in v5.
    if "node_modules" not in content:
        issues.append(
            "[config-exclusion] code-analyzer.yml does not appear to exclude "
            "'node_modules'. Add it under the top-level 'ignores' section to "
            "prevent RetireJS from scanning development dependencies that are "
            "not deployed."
        )

    # The Graph Engine's v5 engine name is 'sfge'; a 'graph-engine' key is not
    # a documented engine name and its settings would not apply.
    if re.search(r"^\s*graph-engine\s*:", content, re.MULTILINE):
        issues.append(
            "[config-graph-engine] code-analyzer.yml contains a 'graph-engine' "
            "engine key. Code Analyzer v5 names the Graph Engine 'sfge', so "
            "settings under 'graph-engine' do not apply. Use "
            "'engines.sfge.disable_engine: true' to turn the engine off in "
            "fast pipeline stages."
        )

    return issues


def check_suppress_warnings_patterns(manifest_dir: Path) -> list[str]:
    """Detect overly-broad @SuppressWarnings('PMD') without rule names in Apex."""
    issues: list[str] = []
    # Match @SuppressWarnings('PMD') or @SuppressWarnings("PMD") without a dot
    blanket_pattern = re.compile(
        r"@SuppressWarnings\s*\(\s*['\"]PMD['\"]\s*\)",
        re.IGNORECASE,
    )

    apex_dirs = [
        manifest_dir / "force-app" / "main" / "default" / "classes",
        manifest_dir / "force-app" / "main" / "default" / "triggers",
    ]

    for apex_dir in apex_dirs:
        if not apex_dir.exists():
            continue
        for apex_file in apex_dir.rglob("*.cls"):
            try:
                content = apex_file.read_text(encoding="utf-8")
                matches = blanket_pattern.findall(content)
                if matches:
                    issues.append(
                        f"[blanket-suppress] {apex_file.relative_to(manifest_dir)} "
                        f"uses @SuppressWarnings('PMD') without a specific rule name "
                        f"({len(matches)} occurrence(s)). Replace with the specific "
                        f"rule name, e.g. @SuppressWarnings('PMD.ApexCRUDViolation'), "
                        f"and add a justification comment."
                    )
            except OSError:
                pass

    return issues


def check_ci_severity_threshold(manifest_dir: Path) -> list[str]:
    """Warn if GitHub Actions workflows run Code Analyzer without --severity-threshold."""
    issues: list[str] = []
    github_dir = manifest_dir / ".github" / "workflows"

    if not github_dir.exists():
        return issues

    code_analyzer_pattern = re.compile(r"sf\s+code-analyzer\s+run", re.IGNORECASE)
    threshold_pattern = re.compile(r"--severity-threshold", re.IGNORECASE)

    for yml_file in github_dir.glob("*.yml"):
        try:
            content = yml_file.read_text(encoding="utf-8")
            if code_analyzer_pattern.search(content) and not threshold_pattern.search(content):
                issues.append(
                    f"[no-threshold] {yml_file.relative_to(manifest_dir)} runs "
                    f"'sf code-analyzer run' without '--severity-threshold'. "
                    f"Without this flag the command always exits 0 and never "
                    f"fails the build. Add '--severity-threshold 2' for a "
                    f"Critical/High gate."
                )
        except OSError:
            pass

    return issues


def check_salesforce_code_analyzer(manifest_dir: Path) -> list[str]:
    """Run all checks and return a consolidated list of issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_legacy_scanner_commands(manifest_dir))
    issues.extend(check_code_analyzer_yml(manifest_dir))
    issues.extend(check_suppress_warnings_patterns(manifest_dir))
    issues.extend(check_ci_severity_threshold(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()
    issues = check_salesforce_code_analyzer(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
