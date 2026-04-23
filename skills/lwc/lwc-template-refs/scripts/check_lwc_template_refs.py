#!/usr/bin/env python3
"""Checker script for the LWC Template Refs skill.

Scans an LWC source tree for the three most common `lwc:ref` mistakes:

  1. `lwc:ref=` declarations nested inside a `<template for:each=...>` or
     `<template iterator:...>` block. Refs are explicitly unsupported inside
     iterators and the name would collide per iteration.
  2. Usage of `this.refs.` inside a `connectedCallback` method body. Refs are
     only populated after the first render pass, so this always throws.
  3. Duplicate `lwc:ref="<name>"` values within the same `.html` template.
     Within a single template root, ref names must be unique.

Stdlib-only. No pip dependencies.

Usage:
    python3 check_lwc_template_refs.py [--manifest-dir path/to/lwc]
    python3 check_lwc_template_refs.py --help

Typical invocations from a SFDX project root:
    python3 check_lwc_template_refs.py --manifest-dir force-app/main/default/lwc
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable


REF_DECL_RE = re.compile(r'lwc:ref\s*=\s*"([^"]+)"')
FOR_EACH_OPEN_RE = re.compile(r'<template\b[^>]*\b(for:each|iterator:)\b', re.IGNORECASE)
TEMPLATE_OPEN_RE = re.compile(r'<template\b', re.IGNORECASE)
TEMPLATE_CLOSE_RE = re.compile(r'</template\s*>', re.IGNORECASE)

# Naive JS method detector: matches `connectedCallback()` or
# `connectedCallback( ... )` at the start of a line (ignoring leading whitespace).
CONNECTED_CALLBACK_RE = re.compile(r'^\s*connectedCallback\s*\([^)]*\)\s*\{')
METHOD_HEAD_RE = re.compile(r'^\s*(?:async\s+)?[A-Za-z_$][\w$]*\s*\([^)]*\)\s*\{')
REFS_USE_RE = re.compile(r'\bthis\.refs\b')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Check LWC components for common lwc:ref mistakes.',
    )
    parser.add_argument(
        '--manifest-dir',
        default='.',
        help='Root directory to scan. Typically force-app/main/default/lwc '
             '(default: current directory).',
    )
    return parser.parse_args()


def iter_lwc_files(root: Path) -> Iterable[Path]:
    """Yield all .html and .js files below `root`."""
    if not root.exists():
        return
    for ext in ('*.html', '*.js'):
        yield from root.rglob(ext)


def check_refs_in_for_each(html_path: Path) -> list[str]:
    """Flag lwc:ref declarations that appear inside a for:each/iterator block.

    The scan is line-based with a depth counter for `<template>` tags. Entering a
    template tag that contains `for:each=` or `iterator:` increments an "inside
    iterator" depth; the matching `</template>` closes it. Any ref declaration
    encountered while that depth is > 0 is flagged.
    """
    findings: list[str] = []
    try:
        text = html_path.read_text(encoding='utf-8', errors='replace')
    except OSError as exc:
        return [f'{html_path}: could not read file ({exc})']

    # Stack of booleans: True if this template is an iterator template.
    template_stack: list[bool] = []
    iterator_depth = 0

    for line_no, line in enumerate(text.splitlines(), start=1):
        # Process openings and closings in order. A single line can contain
        # both, but in real LWC templates they almost never do — scan
        # sequentially across the line for correctness anyway.
        cursor = 0
        while cursor < len(line):
            open_match = TEMPLATE_OPEN_RE.search(line, cursor)
            close_match = TEMPLATE_CLOSE_RE.search(line, cursor)
            ref_match = REF_DECL_RE.search(line, cursor)

            # Pick the earliest match on this line.
            candidates = [
                (m.start(), kind, m)
                for kind, m in (('open', open_match),
                                ('close', close_match),
                                ('ref', ref_match))
                if m is not None
            ]
            if not candidates:
                break
            candidates.sort(key=lambda t: t[0])
            _, kind, m = candidates[0]

            if kind == 'open':
                is_iterator = bool(FOR_EACH_OPEN_RE.search(
                    line, m.start(), min(len(line), m.start() + 400)
                ))
                template_stack.append(is_iterator)
                if is_iterator:
                    iterator_depth += 1
                cursor = m.end()
            elif kind == 'close':
                if template_stack:
                    was_iterator = template_stack.pop()
                    if was_iterator and iterator_depth > 0:
                        iterator_depth -= 1
                cursor = m.end()
            else:  # ref
                if iterator_depth > 0:
                    findings.append(
                        f'{html_path}:{line_no}: lwc:ref="{m.group(1)}" '
                        f'declared inside a for:each/iterator template — refs '
                        f'are not supported inside iterators; use data-* + '
                        f'event delegation instead.'
                    )
                cursor = m.end()

    return findings


def check_duplicate_ref_names(html_path: Path) -> list[str]:
    """Flag duplicate lwc:ref="<name>" values within the same .html file."""
    try:
        text = html_path.read_text(encoding='utf-8', errors='replace')
    except OSError as exc:
        return [f'{html_path}: could not read file ({exc})']

    seen: dict[str, int] = {}
    findings: list[str] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for m in REF_DECL_RE.finditer(line):
            name = m.group(1)
            if name in seen:
                findings.append(
                    f'{html_path}:{line_no}: duplicate lwc:ref="{name}" '
                    f'(first seen at line {seen[name]}) — ref names must be '
                    f'unique within a template root.'
                )
            else:
                seen[name] = line_no
    return findings


def check_refs_in_connected_callback(js_path: Path) -> list[str]:
    """Flag `this.refs` usage inside a `connectedCallback` method body.

    Uses a naive brace counter. Good enough for conventional LWC component
    formatting; does not attempt to parse JS.
    """
    try:
        text = js_path.read_text(encoding='utf-8', errors='replace')
    except OSError as exc:
        return [f'{js_path}: could not read file ({exc})']

    findings: list[str] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if CONNECTED_CALLBACK_RE.search(line):
            # Enter connectedCallback body. Track braces from this line forward.
            depth = line.count('{') - line.count('}')
            start_line = i + 1
            j = i
            while j < len(lines) and depth > 0:
                j += 1
                if j >= len(lines):
                    break
                inner = lines[j]
                if REFS_USE_RE.search(inner):
                    findings.append(
                        f'{js_path}:{j + 1}: this.refs used inside '
                        f'connectedCallback (defined at line {start_line}) — '
                        f'refs are undefined before the first render; move '
                        f'this work to renderedCallback.'
                    )
                depth += inner.count('{') - inner.count('}')
            i = j + 1
        else:
            i += 1
    return findings


def run_checks(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    if not manifest_dir.exists():
        return [f'Manifest directory not found: {manifest_dir}']

    for path in iter_lwc_files(manifest_dir):
        if path.suffix == '.html':
            issues.extend(check_refs_in_for_each(path))
            issues.extend(check_duplicate_ref_names(path))
        elif path.suffix == '.js':
            issues.extend(check_refs_in_connected_callback(path))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = run_checks(manifest_dir)

    if not issues:
        print('No issues found.')
        return 0

    for issue in issues:
        print(f'WARN: {issue}', file=sys.stderr)

    return 1


if __name__ == '__main__':
    sys.exit(main())
