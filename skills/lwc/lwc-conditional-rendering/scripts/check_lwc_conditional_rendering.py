#!/usr/bin/env python3
"""Checker script for lwc-conditional-rendering skill.

Scans LWC HTML templates for stale `if:true` / `if:false` directives, malformed
`lwc:elseif` / `lwc:else` usage, expression complexity inside `lwc:if`, and
invalid values on `lwc:else`.

Stdlib only.

Usage:
    python3 check_lwc_conditional_rendering.py --manifest-dir path/to/force-app
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

LEGACY_DIRECTIVE_RE = re.compile(r'\b(if:true|if:false)\s*=', re.IGNORECASE)
LWC_IF_EXPR_RE = re.compile(r'lwc:if\s*=\s*"?\{([^}]+)\}"?')
LWC_ELSEIF_RE = re.compile(r'<template\b[^>]*\blwc:elseif\b', re.IGNORECASE)
LWC_ELSE_WITH_VALUE_RE = re.compile(r'\blwc:else\s*=\s*[\'"{]')
LWC_IF_OR_ELSEIF_SIBLING_RE = re.compile(
    r'<template\b[^>]*\b(lwc:if|lwc:elseif)\b', re.IGNORECASE
)
CLOSE_TEMPLATE_RE = re.compile(r'</template\s*>')


def iter_lwc_html_files(root: Path):
    for path in root.rglob("*.html"):
        parts = {p.lower() for p in path.parts}
        if "lwc" in parts and path.parent.name == path.stem:
            yield path
        elif "lwc" in parts and "__tests__" not in parts:
            yield path


def scan_file(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    for lineno, line in enumerate(lines, start=1):
        if LEGACY_DIRECTIVE_RE.search(line):
            findings.append(
                f"{path}:{lineno}: legacy `if:true` / `if:false` — use `lwc:if` + `lwc:elseif` + `lwc:else`"
            )
        if LWC_ELSE_WITH_VALUE_RE.search(line):
            findings.append(
                f"{path}:{lineno}: `lwc:else` takes no value — remove the expression"
            )
        for match in LWC_IF_EXPR_RE.finditer(line):
            expr = match.group(1)
            if re.search(r'(&&|\|\||!==|===|[<>!]=|\?.*:|\.length\b)', expr):
                findings.append(
                    f"{path}:{lineno}: complex expression in `lwc:if` — move to a getter ({expr!r})"
                )

    # lwc:elseif / lwc:else must follow an IMMEDIATE SIBLING lwc:if / lwc:elseif.
    # Track one "last closed sibling directive" per nesting depth: each frame
    # on `depth_stack` holds the directive of the most recently CLOSED child
    # at that level (None if the last closed child was not a conditional).
    depth_stack: list[str | None] = [None]  # root frame
    for lineno, line in enumerate(lines, start=1):
        for token in re.finditer(r'<template\b[^>]*/?>|</template\s*>', line, re.IGNORECASE):
            tag = token.group(0)
            if tag.startswith("</"):
                # Closing a <template> — pop its own frame and record its
                # directive as the "last closed sibling" of the parent frame.
                if len(depth_stack) > 1:
                    closed_directive_frame = depth_stack.pop()
                    # The parent's "last closed sibling" becomes whatever
                    # directive the just-closed child carried on its OPEN tag.
                    # We stashed it under a sentinel key in the child frame.
                    # Here we stored it as the frame value itself when opening.
                    depth_stack[-1] = closed_directive_frame
                continue

            directive = None
            if re.search(r'\blwc:if\b', tag):
                directive = "if"
            elif re.search(r'\blwc:elseif\b', tag):
                directive = "elseif"
            elif re.search(r'\blwc:else\b', tag):
                directive = "else"

            prev_sibling = depth_stack[-1]
            if directive == "elseif" and prev_sibling not in ("if", "elseif"):
                findings.append(
                    f"{path}:{lineno}: `lwc:elseif` not preceded by `lwc:if` / `lwc:elseif`"
                )
            if directive == "else" and prev_sibling not in ("if", "elseif"):
                findings.append(
                    f"{path}:{lineno}: `lwc:else` not preceded by `lwc:if` / `lwc:elseif`"
                )

            # Self-closing <template ... /> does not push a child frame.
            if tag.rstrip(">").rstrip().endswith("/"):
                depth_stack[-1] = directive
            else:
                # Opening tag: push a new frame that stores this element's
                # directive; it becomes the parent's "last closed sibling"
                # when it closes.
                depth_stack.append(directive)

    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan LWC HTML templates for legacy conditional directives and misuses "
            "of the lwc:if / lwc:elseif / lwc:else family."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)

    if not root.exists():
        print(f"Manifest directory not found: {root}", file=sys.stderr)
        return 1

    findings: list[str] = []
    for html in iter_lwc_html_files(root):
        findings.extend(scan_file(html))

    if not findings:
        print("No conditional-rendering issues found.")
        return 0

    for item in findings:
        print(f"WARN: {item}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
