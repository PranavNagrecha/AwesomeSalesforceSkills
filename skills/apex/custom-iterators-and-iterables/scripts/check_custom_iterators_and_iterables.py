#!/usr/bin/env python3
"""Checker script for Custom Iterators and Iterables skill.

Scans Apex source files in a metadata directory for common anti-patterns
related to custom Iterator<T> and Iterable<T> implementations.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_custom_iterators_and_iterables.py [--help]
    python3 check_custom_iterators_and_iterables.py --manifest-dir path/to/force-app
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
            "Check Apex classes for common custom Iterator/Iterable anti-patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def _find_apex_files(root: Path) -> list[Path]:
    """Return all .cls files under root."""
    return list(root.rglob("*.cls"))


def check_offset_pagination(apex_files: list[Path]) -> list[str]:
    """Warn when SOQL OFFSET is used inside a class that also implements Iterator."""
    issues: list[str] = []
    offset_re = re.compile(r"\bOFFSET\b", re.IGNORECASE)
    iterator_re = re.compile(r"\bimplements\b.*\bIterator\b", re.IGNORECASE)

    for path in apex_files:
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if iterator_re.search(source) and offset_re.search(source):
            issues.append(
                f"{path}: Iterator class uses SOQL OFFSET — "
                "prefer keyset pagination (WHERE Id > :lastId) to avoid scan degradation."
            )
    return issues


def check_iterator_returns_this(apex_files: list[Path]) -> list[str]:
    """Warn when iterator() method returns 'this' — shared cursor anti-pattern."""
    issues: list[str] = []
    # Match: public Iterator<...> iterator() { ... return this; }
    # Simplified: look for both implements Iterable and a line with `return this`
    iterable_re = re.compile(r"\bimplements\b.*\bIterable\b", re.IGNORECASE)
    return_this_re = re.compile(r"\breturn\s+this\s*;")

    for path in apex_files:
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if iterable_re.search(source) and return_this_re.search(source):
            issues.append(
                f"{path}: Iterable class may return 'this' from iterator() — "
                "this creates a shared cursor. iterator() should return a new Iterator instance."
            )
    return issues


def check_missing_hasnext_guard_in_next(apex_files: list[Path]) -> list[str]:
    """Warn when next() method body does not call hasNext() or check a bound."""
    issues: list[str] = []
    iterator_re = re.compile(r"\bimplements\b.*\bIterator\b", re.IGNORECASE)
    # Heuristic: look for a method named next() that lacks a hasNext() call or an index comparison
    next_method_re = re.compile(
        r"public\s+\w[\w<>, ]*\s+next\s*\(\s*\)\s*\{([^}]*)\}", re.DOTALL
    )
    guard_re = re.compile(r"hasNext\s*\(\s*\)|NoSuchElementException|idx\s*[<>=]|index\s*[<>=]|bufferIdx\s*[<>=]")

    for path in apex_files:
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not iterator_re.search(source):
            continue
        for match in next_method_re.finditer(source):
            body = match.group(1)
            if not guard_re.search(body):
                issues.append(
                    f"{path}: next() method body appears to lack a hasNext() guard or "
                    "NoSuchElementException throw — callers past end will produce undefined behavior."
                )
                break  # one issue per file is enough
    return issues


def check_batch_start_returns_list(apex_files: list[Path]) -> list[str]:
    """Warn when a Batchable class start() explicitly returns a List that could be an Iterable."""
    issues: list[str] = []
    batchable_re = re.compile(r"\bimplements\b.*\bDatabase\.Batchable\b", re.IGNORECASE)
    start_returns_list_re = re.compile(
        r"public\s+List\s*<\s*\w+\s*>\s+start\s*\(", re.IGNORECASE
    )

    for path in apex_files:
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if batchable_re.search(source) and start_returns_list_re.search(source):
            issues.append(
                f"{path}: Batchable start() returns List<T> — "
                "consider returning Iterable<SObject> to allow lazy evaluation "
                "and avoid materializing the full collection before first execute()."
            )
    return issues


def check_no_iterable_wrapper_when_iterator_only(apex_files: list[Path]) -> list[str]:
    """Warn when a class implements Iterator but not Iterable, and is used in a for-each context."""
    issues: list[str] = []
    iterator_only_re = re.compile(
        r"\bimplements\b(?!.*\bIterable\b).*\bIterator\b", re.IGNORECASE
    )
    foreach_re = re.compile(r"\bfor\s*\(.*:.*\b\w+\s*\)", re.DOTALL)

    for path in apex_files:
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if iterator_only_re.search(source) and foreach_re.search(source):
            issues.append(
                f"{path}: Class implements Iterator<T> but not Iterable<T>, "
                "yet appears in a for-each pattern. For-each loops require Iterable<T>."
            )
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_custom_iterators_and_iterables(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found under manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = _find_apex_files(manifest_dir)
    if not apex_files:
        # No Apex files — nothing to check, not an error
        return issues

    issues.extend(check_offset_pagination(apex_files))
    issues.extend(check_iterator_returns_this(apex_files))
    issues.extend(check_missing_hasnext_guard_in_next(apex_files))
    issues.extend(check_batch_start_returns_list(apex_files))
    issues.extend(check_no_iterable_wrapper_when_iterator_only(apex_files))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_custom_iterators_and_iterables(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
