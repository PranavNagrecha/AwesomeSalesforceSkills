#!/usr/bin/env python3
"""Checker script for Long-Running Process Orchestration skill.

Scans Apex source files for common anti-patterns in multi-step async orchestration:
  - Queueable chains missing AsyncOptions on enqueueJob calls
  - attachFinalizer called after risky code (SOQL/DML/callout) in execute()
  - Multiple System.enqueueJob() calls within a single execute() method
  - Static fields used for inter-step state in Queueable classes
  - Queueable execute() doing DML/callouts with no Finalizer attached

Note: calling a @future method from a Queueable's execute() is NOT checked here,
because it is legal. The Apex per-transaction limits table allocates "0 in batch
and future contexts; 50 in queueable context" for methods with the future
annotation, so @future-from-Queueable is explicitly permitted.
See https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_long_running_process_orchestration.py [--help]
    python3 check_long_running_process_orchestration.py --manifest-dir path/to/metadata
    python3 check_long_running_process_orchestration.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Apex metadata for common long-running process orchestration anti-patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_apex_classes(manifest_dir: Path) -> list[Path]:
    """Return all .cls files under manifest_dir."""
    return list(manifest_dir.rglob("*.cls"))


def extract_execute_body(source: str) -> str:
    """
    Naively extract the body of the execute() method from an Apex class source.
    Returns the content between the opening and closing brace of the first
    execute( method found, or empty string if none found.
    """
    # Find the start of any execute( method
    match = re.search(r'\bpublic\s+void\s+execute\s*\(', source)
    if not match:
        return ""

    start = match.start()
    brace_count = 0
    body_start = source.find("{", start)
    if body_start == -1:
        return ""

    for i in range(body_start, len(source)):
        if source[i] == "{":
            brace_count += 1
        elif source[i] == "}":
            brace_count -= 1
            if brace_count == 0:
                return source[body_start : i + 1]
    return ""


def extract_call_args(source: str, open_paren_idx: int) -> str | None:
    """
    Given the index of a '(' in source, return the text between it and its
    matching ')', honouring nesting. Returns None if unbalanced.
    """
    if open_paren_idx >= len(source) or source[open_paren_idx] != "(":
        return None
    depth = 0
    for i in range(open_paren_idx, len(source)):
        char = source[i]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return source[open_paren_idx + 1 : i]
    return None


def count_top_level_args(args: str) -> int:
    """
    Count comma-separated arguments at nesting depth 0, so that commas inside
    nested calls or generic type parameters (Map<Id, Account>) are not counted.
    """
    if not args.strip():
        return 0
    depth = 0
    count = 1
    for char in args:
        if char in "(<[":
            depth += 1
        elif char in ")>]":
            depth -= 1
        elif char == "," and depth == 0:
            count += 1
    return count


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_enqueue_without_options(path: Path, source: str) -> list[str]:
    """
    Warn when System.enqueueJob() is called without an AsyncOptions argument
    inside what looks like a Queueable class (contains 'implements Queueable').
    """
    issues: list[str] = []
    if "implements Queueable" not in source and "implements Queueable," not in source:
        return issues

    # Find all enqueueJob calls and count TOP-LEVEL arguments. A naive
    # r'\(([^)]*)\)' match stops at the first inner ')', so
    # System.enqueueJob(new Foo(a, b), opts) would be read as "new Foo(a, b"
    # and misjudged. Walk the parentheses instead.
    for match in re.finditer(r'System\.enqueueJob\s*\(', source):
        args = extract_call_args(source, match.end() - 1)
        if args is None:
            continue
        if count_top_level_args(args) < 2:
            issues.append(
                f"{path.name}: System.enqueueJob() called without AsyncOptions — "
                "the chain runs with the org's default queueable stack-depth behavior. "
                "Pass AsyncOptions with MaximumQueueableStackDepth to bound the chain "
                "explicitly."
            )
    return issues


def check_finalizer_placement(path: Path, source: str) -> list[str]:
    """
    Warn when attachFinalizer appears after the first SOQL, DML, or callout
    in the execute() body of a Queueable.
    """
    issues: list[str] = []
    if "implements Queueable" not in source and "implements Queueable," not in source:
        return issues

    execute_body = extract_execute_body(source)
    if not execute_body:
        return issues

    finalizer_pos = execute_body.find("attachFinalizer")
    if finalizer_pos == -1:
        # No Finalizer attached at all — this is a separate concern, not flagged here
        return issues

    # Look for risky operations that appear BEFORE attachFinalizer
    risky_patterns = [
        (r'\[SELECT\b', "SOQL query"),
        (r'\binsert\b', "DML insert"),
        (r'\bupdate\b', "DML update"),
        (r'\bdelete\b', "DML delete"),
        (r'\bupsert\b', "DML upsert"),
        (r'new\s+Http\(\)', "HTTP callout"),
        (r'\.send\s*\(', "callout send"),
    ]
    before_finalizer = execute_body[:finalizer_pos]
    for pattern, label in risky_patterns:
        if re.search(pattern, before_finalizer, re.IGNORECASE):
            issues.append(
                f"{path.name}: System.attachFinalizer() appears after a {label} in execute() — "
                "move it to the first line to guarantee Finalizer runs on all failure modes."
            )
            break  # Report once per file to avoid noise
    return issues


def check_multiple_enqueues_in_execute(path: Path, source: str) -> list[str]:
    """
    Warn when execute() contains more than one System.enqueueJob() call,
    which violates the single-child Queueable rule.
    """
    issues: list[str] = []
    if "implements Queueable" not in source and "implements Queueable," not in source:
        return issues

    execute_body = extract_execute_body(source)
    if not execute_body:
        return issues

    count = len(re.findall(r'System\.enqueueJob\s*\(', execute_body))
    if count > 1:
        issues.append(
            f"{path.name}: execute() contains {count} System.enqueueJob() calls — "
            "only one child Queueable may be enqueued per execute(); the second call will "
            "throw System.LimitException at runtime."
        )
    return issues


def check_static_state_fields(path: Path, source: str) -> list[str]:
    """
    Warn when a Queueable class declares static instance fields that look like
    they are used for inter-step state passing (Map, List, String, Id, Integer).
    """
    issues: list[str] = []
    if "implements Queueable" not in source and "implements Queueable," not in source:
        return issues

    # Static fields that are not final constants (all-caps name) are suspicious.
    # Capture the declared name so the ALL_CAPS constant test can run in Python —
    # a variable-width lookbehind such as (?<![A-Z_]{3,}) is not a legal regex.
    static_field_pattern = re.compile(
        r'\b(?:public|private|protected|global)\s+static\s+(?!final\b)'
        r'(?:Map|List|Set|String|Id|Integer|Boolean|Object|Decimal|Long|Double)\b'
        r'(?:\s*<[^>]*>)?\s+'
        r'(\w+)\s*(?:=|;)',
        re.IGNORECASE,
    )
    for match in static_field_pattern.finditer(source):
        field_name = match.group(1)
        # ALL_CAPS names are conventional constants, not inter-step state.
        if field_name.isupper():
            continue
        issues.append(
            f"{path.name}: Queueable class declares non-constant static field "
            f"'{field_name}' — "
            "static variables do not survive between async transactions; "
            "pass state through constructor fields instead."
        )
    return issues


def check_missing_finalizer_on_queueable(path: Path, source: str) -> list[str]:
    """
    Warn when a Queueable class has DML or callouts in execute() but no attachFinalizer.
    This is advisory — many simple Queueables legitimately skip Finalizers.
    Only flag when there are outbound callouts or DML and no Finalizer is present.
    """
    issues: list[str] = []
    if "implements Queueable" not in source and "implements Queueable," not in source:
        return issues

    execute_body = extract_execute_body(source)
    if not execute_body:
        return issues

    has_callout = bool(re.search(r'new\s+Http\(\)|\.send\s*\(', execute_body))
    has_dml = bool(re.search(r'\b(insert|update|delete|upsert)\b', execute_body, re.IGNORECASE))
    has_finalizer = "attachFinalizer" in execute_body

    if (has_callout or has_dml) and not has_finalizer:
        issues.append(
            f"{path.name}: Queueable execute() performs DML or callouts but has no "
            "System.attachFinalizer() — failures will leave process state ambiguous. "
            "Add a Finalizer for production-safe error handling."
        )
    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_long_running_process_orchestration(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = find_apex_classes(manifest_dir)
    if not apex_files:
        # Not an error — the directory may be a non-Apex project
        return issues

    check_fns = [
        check_enqueue_without_options,
        check_finalizer_placement,
        check_multiple_enqueues_in_execute,
        check_static_state_fields,
        check_missing_finalizer_on_queueable,
    ]

    for cls_path in sorted(apex_files):
        try:
            source = cls_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            issues.append(f"Could not read file: {cls_path}")
            continue

        for fn in check_fns:
            issues.extend(fn(cls_path, source))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_long_running_process_orchestration(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
