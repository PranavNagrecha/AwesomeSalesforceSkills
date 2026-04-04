#!/usr/bin/env python3
"""
check_integration_framework.py — stdlib-only static analysis for Apex integration framework patterns.

Scans .cls files for:
  1. HttpRequest usage without try/catch around http.send() — callout not protected
  2. Direct callout usage that does not route through a dispatcher or service class name
  3. Hard-coded URL strings inside callout-related code (http:// or https:// literals)

Usage:
    python3 scripts/check_integration_framework.py [--path <directory>]

Exit code:
    0 — no issues found
    1 — one or more issues found
"""

import os
import re
import sys
import argparse


# Patterns to detect
PATTERN_HTTP_REQUEST = re.compile(r'\bHttpRequest\b')
PATTERN_HTTP_SEND = re.compile(r'\bhttp\.send\s*\(')
PATTERN_TRY_CATCH = re.compile(r'\btry\s*\{', re.IGNORECASE)
PATTERN_CATCH_CALLOUT = re.compile(r'\bcatch\s*\(\s*\w*CalloutException\b', re.IGNORECASE)
PATTERN_CATCH_ANY = re.compile(r'\bcatch\s*\(\s*\w*Exception\b', re.IGNORECASE)
PATTERN_HARDCODED_URL = re.compile(r'''['"]https?://[^'"]{5,}['"]''')
PATTERN_DISPATCHER_CALL = re.compile(r'\bHttpCalloutDispatcher\b|\bCalloutDispatcher\b|\bdispatch\s*\(', re.IGNORECASE)
PATTERN_SERVICE_INTERFACE = re.compile(r'\bIIntegrationService\b|\bIntegrationService\b', re.IGNORECASE)
PATTERN_TRIGGER_CONTEXT = re.compile(r'Trigger\.(isInsert|isUpdate|isDelete|isBefore|isAfter|new|old)\b', re.IGNORECASE)


def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except OSError:
        return None


def check_file(filepath, content):
    issues = []
    lines = content.splitlines()

    has_http_request = bool(PATTERN_HTTP_REQUEST.search(content))
    has_http_send = bool(PATTERN_HTTP_SEND.search(content))

    if not has_http_request and not has_http_send:
        return issues  # Not a callout file — skip

    # Issue 1: HttpRequest used but no try/catch guarding http.send()
    has_try = bool(PATTERN_TRY_CATCH.search(content))
    has_catch = bool(PATTERN_CATCH_CALLOUT.search(content)) or bool(PATTERN_CATCH_ANY.search(content))
    if has_http_send and not (has_try and has_catch):
        issues.append({
            'file': filepath,
            'severity': 'ERROR',
            'message': 'http.send() found without enclosing try/catch block. '
                       'CalloutExceptions will be unhandled and surface as uncontrolled errors.',
        })

    # Issue 2: Direct http.send() not routed through a dispatcher or service class
    has_dispatcher = bool(PATTERN_DISPATCHER_CALL.search(content))
    has_service = bool(PATTERN_SERVICE_INTERFACE.search(content))
    if has_http_send and not has_dispatcher and not has_service:
        issues.append({
            'file': filepath,
            'severity': 'WARNING',
            'message': 'http.send() called without a dispatcher or IIntegrationService reference. '
                       'Consider routing through HttpCalloutDispatcher for centralized logging, retry, and auth.',
        })

    # Issue 3: Hard-coded URL strings in callout code
    for i, line in enumerate(lines, start=1):
        if PATTERN_HARDCODED_URL.search(line):
            # Ignore lines that are comments or unit test mock setups
            stripped = line.strip()
            if stripped.startswith('//') or stripped.startswith('*'):
                continue
            issues.append({
                'file': filepath,
                'severity': 'ERROR',
                'message': f'Line {i}: Hard-coded URL string detected. '
                           f'Endpoints should be stored in Integration_Service__mdt.Endpoint__c '
                           f'or a Named Credential, not as string literals in Apex.',
                'line': i,
                'content': stripped[:120],
            })

    # Issue 4: Callout file appears to be a trigger handler
    is_trigger_handler = bool(PATTERN_TRIGGER_CONTEXT.search(content))
    if has_http_send and is_trigger_handler:
        issues.append({
            'file': filepath,
            'severity': 'ERROR',
            'message': 'Callout logic detected in a trigger handler context. '
                       'Salesforce does not allow synchronous callouts with uncommitted DML work pending. '
                       'Move callouts to a Queueable or enqueue via Platform Event.',
        })

    return issues


def scan_directory(root_path):
    all_issues = []
    for dirpath, _dirnames, filenames in os.walk(root_path):
        for filename in filenames:
            if not filename.endswith('.cls'):
                continue
            filepath = os.path.join(dirpath, filename)
            content = read_file(filepath)
            if content is None:
                continue
            issues = check_file(filepath, content)
            all_issues.extend(issues)
    return all_issues


def format_issue(issue):
    lines = [f"  [{issue['severity']}] {issue['file']}"]
    lines.append(f"    {issue['message']}")
    if 'content' in issue:
        lines.append(f"    Code: {issue['content']}")
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Check Apex files for integration framework anti-patterns.'
    )
    parser.add_argument(
        '--path',
        default='.',
        help='Root directory to scan for .cls files (default: current directory)',
    )
    args = parser.parse_args()

    scan_root = os.path.abspath(args.path)
    if not os.path.isdir(scan_root):
        print(f'ERROR: Path does not exist or is not a directory: {scan_root}', file=sys.stderr)
        sys.exit(1)

    print(f'Scanning {scan_root} for integration framework issues...\n')
    issues = scan_directory(scan_root)

    if not issues:
        print('OK — No integration framework issues found.')
        sys.exit(0)

    errors = [i for i in issues if i['severity'] == 'ERROR']
    warnings = [i for i in issues if i['severity'] == 'WARNING']

    print(f'Found {len(issues)} issue(s): {len(errors)} error(s), {len(warnings)} warning(s)\n')
    for issue in issues:
        print(format_issue(issue))
        print()

    sys.exit(1)


if __name__ == '__main__':
    main()
