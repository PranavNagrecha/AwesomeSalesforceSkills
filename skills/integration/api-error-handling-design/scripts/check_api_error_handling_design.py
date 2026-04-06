#!/usr/bin/env python3
"""Checker script for API Error Handling Design skill.

Scans Apex source files in a Salesforce metadata deployment directory for
common API error handling anti-patterns documented in
skills/integration/api-error-handling-design/references/llm-anti-patterns.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_api_error_handling_design.py [--help]
    python3 check_api_error_handling_design.py --manifest-dir path/to/sfdx/force-app
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Issue dataclass (stdlib-only replacement)
# ---------------------------------------------------------------------------

class Issue:
    def __init__(self, file: Path, line: int, rule: str, detail: str) -> None:
        self.file = file
        self.line = line
        self.rule = rule
        self.detail = detail

    def __str__(self) -> str:
        return f"{self.file}:{self.line} [{self.rule}] {self.detail}"


# ---------------------------------------------------------------------------
# Per-rule check functions
# ---------------------------------------------------------------------------

def check_salesforce_error_deserialized_as_map(apex_lines: list[str], file: Path) -> list[Issue]:
    """Detect: (Map<String,Object>) JSON.deserializeUntyped(... on a Salesforce REST callout response.

    Salesforce REST API errors are a JSON array. Casting to Map raises TypeException.
    """
    issues: list[Issue] = []
    pattern = re.compile(
        r'\(Map<String\s*,\s*Object>\)\s*JSON\.deserializeUntyped',
        re.IGNORECASE,
    )
    for lineno, line in enumerate(apex_lines, start=1):
        if pattern.search(line):
            issues.append(Issue(
                file=file,
                line=lineno,
                rule="SF-ERR-001",
                detail=(
                    "JSON.deserializeUntyped() cast to Map<String,Object> — "
                    "Salesforce REST API errors are a JSON array (List<Object>), not a Map. "
                    "This will throw System.TypeException at runtime."
                ),
            ))
    return issues


def check_throw_from_rest_resource_after_status_set(apex_lines: list[str], file: Path) -> list[Issue]:
    """Detect: setting RestContext.response.statusCode followed by a throw in the same method.

    Throwing from a @RestResource method overrides any pre-set statusCode with 500.
    """
    issues: list[Issue] = []
    status_set_pattern = re.compile(r'RestContext\.response\.statusCode\s*=')
    throw_pattern = re.compile(r'\bthrow\s+new\b')

    in_rest_resource_method = False
    status_set_lineno: int | None = None

    # Heuristic: look for @HttpPost/@HttpPut/@HttpPatch/@HttpDelete annotation
    http_method_annotation = re.compile(r'@(HttpPost|HttpPut|HttpPatch|HttpDelete|HttpGet)\b')

    for lineno, line in enumerate(apex_lines, start=1):
        if http_method_annotation.search(line):
            in_rest_resource_method = True
            status_set_lineno = None
            continue

        # Reset on new method boundary (naive: any 'global static' or 'public static' after annotation)
        if in_rest_resource_method and re.search(r'\b(global|public)\s+(static\s+)?\w+', line) and '{' in line:
            # We're inside the method now — wait until closing brace heuristic (good enough for linting)
            pass

        if in_rest_resource_method and status_set_pattern.search(line):
            status_set_lineno = lineno

        if in_rest_resource_method and status_set_lineno and throw_pattern.search(line):
            issues.append(Issue(
                file=file,
                line=lineno,
                rule="SF-ERR-002",
                detail=(
                    f"'throw' statement after RestContext.response.statusCode set on line {status_set_lineno}. "
                    "The platform overrides the status code with 500 when an exception escapes a @RestResource method. "
                    "Catch all exceptions and return normally instead of throwing."
                ),
            ))

    return issues


def check_stack_trace_in_rest_response(apex_lines: list[str], file: Path) -> list[Issue]:
    """Detect: e.getStackTraceString() included in RestContext.response.responseBody."""
    issues: list[Issue] = []
    pattern = re.compile(r'getStackTraceString\s*\(\s*\)')

    in_catch_block = False
    for lineno, line in enumerate(apex_lines, start=1):
        if re.search(r'\bcatch\s*\(', line):
            in_catch_block = True
        if in_catch_block and pattern.search(line):
            issues.append(Issue(
                file=file,
                line=lineno,
                rule="SF-ERR-003",
                detail=(
                    "getStackTraceString() found in a catch block. "
                    "Never include stack traces in external API responses — "
                    "log them server-side (System.debug or custom object) and return a sanitized message."
                ),
            ))

    return issues


def check_retry_on_all_non_200(apex_lines: list[str], file: Path) -> list[Issue]:
    """Detect: retry/enqueue logic triggered on any non-200 or >=400 without 4xx dead-letter carve-out."""
    issues: list[Issue] = []
    # Pattern: an if condition matching status >= 400 or != 200 or >= 300
    # followed by something that looks like a retry enqueue
    broad_condition = re.compile(
        r'if\s*\(.*(?:getStatusCode\s*\(\s*\)|statusCode)\s*'
        r'(?:!=\s*200|>=\s*(?:300|400))\b'
    )
    enqueue_pattern = re.compile(r'enqueueJob|enqueueRetry|System\.enqueueJob')

    for lineno, line in enumerate(apex_lines, start=1):
        if broad_condition.search(line) and enqueue_pattern.search(line):
            issues.append(Issue(
                file=file,
                line=lineno,
                rule="SF-ERR-004",
                detail=(
                    "Possible retry on all non-2xx status codes without 4xx dead-letter carve-out. "
                    "HTTP 400/401/403/404/422 are permanent errors — retrying wastes async Apex quota. "
                    "Only retry 429, 5xx (except 501), and timeout exceptions."
                ),
            ))

    return issues


def check_no_set_timeout(apex_lines: list[str], file: Path) -> list[Issue]:
    """Detect: HttpRequest usage without an explicit setTimeout() call in the same method block."""
    issues: list[Issue] = []
    has_http_request = False
    has_set_timeout = False
    http_request_lineno: int | None = None

    for lineno, line in enumerate(apex_lines, start=1):
        if re.search(r'\bnew\s+HttpRequest\s*\(\s*\)', line):
            # If we saw a prior HttpRequest without setTimeout, flag it
            if has_http_request and not has_set_timeout and http_request_lineno:
                issues.append(Issue(
                    file=file,
                    line=http_request_lineno,
                    rule="SF-ERR-005",
                    detail=(
                        "HttpRequest instantiated without a subsequent setTimeout() call. "
                        "Always set an explicit timeout — platform defaults vary by Named Credential type "
                        "and can change between releases."
                    ),
                ))
            has_http_request = True
            has_set_timeout = False
            http_request_lineno = lineno

        if has_http_request and re.search(r'\.setTimeout\s*\(', line):
            has_set_timeout = True

    # Check the last HttpRequest in file
    if has_http_request and not has_set_timeout and http_request_lineno:
        issues.append(Issue(
            file=file,
            line=http_request_lineno,
            rule="SF-ERR-005",
            detail=(
                "HttpRequest instantiated without a subsequent setTimeout() call. "
                "Always set an explicit timeout — platform defaults vary by Named Credential type "
                "and can change between releases."
            ),
        ))

    return issues


def check_message_string_matching_for_error_code(apex_lines: list[str], file: Path) -> list[Issue]:
    """Detect: .contains() or .startsWith() on a Salesforce REST response body string for error routing."""
    issues: list[Issue] = []
    # Look for patterns like body.contains('Required fields') or responseBody.contains('INSUFFICIENT')
    # near callout response parsing logic
    pattern = re.compile(
        r'(?:getBody|responseBody|resBody)\s*\(\s*\)\s*\.'
        r'(?:contains|startsWith|equalsIgnoreCase)\s*\(\s*[\'"]',
        re.IGNORECASE,
    )
    for lineno, line in enumerate(apex_lines, start=1):
        if pattern.search(line):
            issues.append(Issue(
                file=file,
                line=lineno,
                rule="SF-ERR-006",
                detail=(
                    "String matching on HTTP response body for error classification. "
                    "For Salesforce REST API errors, use the 'errorCode' field rather than 'message' text — "
                    "errorCode is release-stable; message text can change."
                ),
            ))

    return issues


# ---------------------------------------------------------------------------
# Apex file discovery and runner
# ---------------------------------------------------------------------------

CHECKS = [
    check_salesforce_error_deserialized_as_map,
    check_throw_from_rest_resource_after_status_set,
    check_stack_trace_in_rest_response,
    check_retry_on_all_non_200,
    check_no_set_timeout,
    check_message_string_matching_for_error_code,
]


def find_apex_files(root: Path) -> list[Path]:
    """Return all .cls files under root."""
    return sorted(root.rglob("*.cls"))


def check_api_error_handling_design(manifest_dir: Path) -> list[Issue]:
    """Return a list of issues found across all Apex files in manifest_dir."""
    all_issues: list[Issue] = []

    if not manifest_dir.exists():
        # Return a single structural issue rather than crashing
        return [Issue(
            file=manifest_dir,
            line=0,
            rule="SETUP",
            detail=f"Manifest directory not found: {manifest_dir}",
        )]

    apex_files = find_apex_files(manifest_dir)
    if not apex_files:
        # No Apex files is not an error — report nothing
        return []

    for apex_file in apex_files:
        try:
            lines = apex_file.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            all_issues.append(Issue(
                file=apex_file,
                line=0,
                rule="SETUP",
                detail=f"Could not read file: {exc}",
            ))
            continue

        for check_fn in CHECKS:
            all_issues.extend(check_fn(lines, apex_file))

    return all_issues


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Apex classes for API error handling anti-patterns. "
            "Scans .cls files under --manifest-dir for patterns documented in "
            "skills/integration/api-error-handling-design/references/llm-anti-patterns.md."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a summary count per rule instead of full issue list.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_api_error_handling_design(manifest_dir)

    if not issues:
        print("No API error handling issues found.")
        return 0

    if args.summary:
        rule_counts: dict[str, int] = {}
        for issue in issues:
            rule_counts[issue.rule] = rule_counts.get(issue.rule, 0) + 1
        print(f"Found {len(issues)} issue(s) across {len(rule_counts)} rule(s):")
        for rule, count in sorted(rule_counts.items()):
            print(f"  {rule}: {count}")
    else:
        for issue in issues:
            print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
