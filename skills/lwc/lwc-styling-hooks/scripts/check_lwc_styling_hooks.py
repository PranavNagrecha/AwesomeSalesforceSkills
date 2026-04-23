#!/usr/bin/env python3
"""Checker script for the lwc-styling-hooks skill.

Scans LWC CSS files for styling-hook anti-patterns that break on SLDS
upgrades or fail silently under the shadow DOM. Uses stdlib only — no
pip dependencies.

Checks performed (each finding is line-numbered):

1. Selectors that target internal SLDS class names as direct overrides
   (pattern: ``\\.slds-[a-z_-]+\\s*\\{``). Those classes are not a
   public API and upgrade-break.
2. Raw hex color literals (``#[0-9a-fA-F]{3,8}``) that are NOT the
   value of a ``var(...)`` reference — those should usually be
   replaced by a styling hook or SLDS semantic token.
3. ``!important`` applied to a styling-hook declaration
   (pattern: ``--slds-.*!important`` or ``--sds-.*!important``) —
   this fights the cascade and blocks legitimate downstream overrides.

Usage::

    python3 check_lwc_styling_hooks.py [--root PATH]

    # Defaults to scanning ./force-app, ./src, and . in order of
    # whichever exists first.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

# --- Patterns -----------------------------------------------------------------

# `.slds-foo {` or `.slds-foo_bar {` used as a direct override selector.
SLDS_CLASS_SELECTOR = re.compile(r"(\.slds-[a-z0-9][a-z0-9_-]*)\s*(?:[,\{]|\s)")

# Hex color literal. We filter hits that are arguments to `var(...)`
# by looking at the surrounding context on the same line.
HEX_LITERAL = re.compile(r"#[0-9a-fA-F]{3,8}\b")

# `--slds-...!important` or `--sds-...!important` on the same declaration line.
HOOK_IMPORTANT = re.compile(r"(--(?:slds|sds)-[a-z0-9-]+)\s*:[^;]*!important")

# Comment stripping (line-level). CSS block comments that fit on one line.
LINE_COMMENT = re.compile(r"/\*.*?\*/")


# --- File discovery -----------------------------------------------------------


def discover_css_files(root: Path) -> list[Path]:
    """Return all `.css` files under any `lwc/` directory rooted at ``root``.

    Matches common project layouts: ``force-app/main/default/lwc/**/*.css``,
    ``src/lwc/**/*.css``, or a raw ``lwc/**/*.css`` tree.
    """
    files: list[Path] = []
    if not root.exists():
        return files
    for css in root.rglob("*.css"):
        parts_lower = {p.lower() for p in css.parts}
        if "lwc" in parts_lower:
            files.append(css)
    return sorted(files)


def resolve_default_root(cwd: Path) -> Path:
    for candidate in ("force-app", "src"):
        p = cwd / candidate
        if p.is_dir():
            return p
    return cwd


# --- Scanners -----------------------------------------------------------------


def _strip_inline_comments(line: str) -> str:
    return LINE_COMMENT.sub("", line)


def scan_slds_class_selectors(path: Path, lines: list[str]) -> list[str]:
    findings: list[str] = []
    in_block_comment = False
    for idx, raw in enumerate(lines, start=1):
        line = raw
        # Crude multi-line comment tracking.
        if in_block_comment:
            end = line.find("*/")
            if end == -1:
                continue
            line = line[end + 2 :]
            in_block_comment = False
        start = line.find("/*")
        if start != -1 and line.find("*/", start) == -1:
            in_block_comment = True
            line = line[:start]
        line = _strip_inline_comments(line)
        match = SLDS_CLASS_SELECTOR.search(line)
        if not match:
            continue
        # Ignore usage inside `@apply`-like contexts or string literals —
        # CSS string literals with `.slds-` are rare, so a raw hit is
        # nearly always a selector.
        findings.append(
            f"{path}:{idx}: targets SLDS internal class `{match.group(1)}` — "
            f"use an --slds-c-* styling hook instead; SLDS class names "
            f"are not a public API and break on upgrade."
        )
    return findings


def scan_raw_hex_literals(path: Path, lines: list[str]) -> list[str]:
    findings: list[str] = []
    in_block_comment = False
    for idx, raw in enumerate(lines, start=1):
        line = raw
        if in_block_comment:
            end = line.find("*/")
            if end == -1:
                continue
            line = line[end + 2 :]
            in_block_comment = False
        start = line.find("/*")
        if start != -1 and line.find("*/", start) == -1:
            in_block_comment = True
            line = line[:start]
        line = _strip_inline_comments(line)
        for m in HEX_LITERAL.finditer(line):
            # Skip hex values that sit inside a `var(... #abc ...)` — rare
            # but possible as a fallback, e.g. `var(--x, #abcdef)`.
            before = line[: m.start()]
            if before.rstrip().endswith(",") and "var(" in before:
                continue
            # Skip when the hit is within `url(#...)` — SVG references
            # like `url(#grad)` are hex-looking but not colors.
            ctx_start = max(0, m.start() - 6)
            if "url(" in line[ctx_start : m.start()]:
                continue
            findings.append(
                f"{path}:{idx}: raw hex literal `{m.group(0)}` — prefer "
                f"an --slds-g-* semantic token or an --slds-c-* component hook "
                f"so the value travels with the theme."
            )
    return findings


def scan_hook_important(path: Path, lines: list[str]) -> list[str]:
    findings: list[str] = []
    for idx, line in enumerate(lines, start=1):
        m = HOOK_IMPORTANT.search(line)
        if not m:
            continue
        findings.append(
            f"{path}:{idx}: `{m.group(1)}` declared with !important — "
            f"prefer scope specificity over !important; !important blocks "
            f"legitimate downstream overrides."
        )
    return findings


# --- Orchestration ------------------------------------------------------------


def scan_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:  # pragma: no cover - defensive
        return [f"{path}: could not read ({exc})"]
    lines = text.splitlines()
    findings: list[str] = []
    findings.extend(scan_slds_class_selectors(path, lines))
    findings.extend(scan_raw_hex_literals(path, lines))
    findings.extend(scan_hook_important(path, lines))
    return findings


def run(files: Iterable[Path]) -> list[str]:
    all_findings: list[str] = []
    for f in files:
        all_findings.extend(scan_file(f))
    return all_findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan LWC CSS files for SLDS Styling Hooks anti-patterns: "
            "raw .slds-* class overrides, hardcoded hex color literals, "
            "and !important on styling-hook declarations."
        ),
    )
    parser.add_argument(
        "--root",
        default=None,
        help=(
            "Root directory to scan. Defaults to ./force-app if present, "
            "else ./src if present, else the current directory."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root) if args.root else resolve_default_root(Path.cwd())
    files = discover_css_files(root)

    if not files:
        print(f"No LWC CSS files found under {root}")
        return 0

    findings = run(files)

    if not findings:
        print(f"OK: scanned {len(files)} LWC CSS file(s); no styling-hook anti-patterns found.")
        return 0

    print(
        f"Scanned {len(files)} LWC CSS file(s); found {len(findings)} "
        f"styling-hook issue(s):",
        file=sys.stderr,
    )
    for item in findings:
        print(f"WARN: {item}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
