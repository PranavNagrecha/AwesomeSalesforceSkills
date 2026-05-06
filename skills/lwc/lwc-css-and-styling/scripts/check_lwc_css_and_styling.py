#!/usr/bin/env python3
"""Static checks for LWC CSS / styling anti-patterns.

Scans LWC source for the high-confidence anti-patterns documented in
`references/llm-anti-patterns.md`:

  1. Selector targeting an internal `.slds-*` class from outside a
     base component (selector starts with a `lightning-*` tag and
     contains a `.slds-` class).
  2. `!important` directly attached to a `.slds-*` rule.
  3. Hardcoded 6-character hex colors in LWC CSS files.
  4. Deprecated `/deep/`, `::shadow`, or `>>>` selectors.

Stdlib only.

Usage:
    python3 check_lwc_css_and_styling.py --src-root .
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


_PIERCING_SELECTOR_RE = re.compile(
    r"^\s*lightning-[\w-]+\s+[^{]*\.slds-[^\{,]+\{",
    re.MULTILINE | re.IGNORECASE,
)
_BANG_IMPORTANT_SLDS_RE = re.compile(
    r"\.slds-[\w-]+[^{]*\{[^}]*!important",
    re.IGNORECASE | re.DOTALL,
)
_HEX_COLOR_RE = re.compile(r"#[0-9a-fA-F]{6}\b")
_DEEP_DEPRECATED_RE = re.compile(r"/deep/|::shadow|>>>")
_COMMENT_BLOCK_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _strip_comments(text: str) -> str:
    return _COMMENT_BLOCK_RE.sub(lambda m: " " * (m.end() - m.start()), text)


def _scan_css(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]
    text = _strip_comments(raw)

    for m in _PIERCING_SELECTOR_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: selector targets a "
            "base-component internal `.slds-*` class — does not "
            "pierce shadow DOM, brittle across SLDS versions "
            "(references/llm-anti-patterns.md § 1)"
        )

    for m in _BANG_IMPORTANT_SLDS_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: `!important` on a "
            "`.slds-*` rule — fighting specificity, not solving the "
            "shadow-DOM boundary (references/llm-anti-patterns.md § 2)"
        )

    for m in _HEX_COLOR_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: hardcoded hex color "
            f"`{m.group(0)}` — use a design token "
            "(--slds-g-color-*) for theme/contrast support "
            "(references/llm-anti-patterns.md § 3)"
        )

    for m in _DEEP_DEPRECATED_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: deprecated piercing "
            f"selector `{m.group(0)}` — removed from modern browsers; "
            "use a styling hook or ::part() "
            "(references/llm-anti-patterns.md § 6)"
        )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]
    findings: list[str] = []
    for css in root.rglob("*.css"):
        # Skip third-party / generated CSS
        parts = css.parts
        if "node_modules" in parts or "staticresources" in parts:
            continue
        findings.extend(_scan_css(css))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan LWC CSS for styling anti-patterns "
            "(piercing selectors, !important on .slds-*, hardcoded "
            "hex colors, deprecated /deep/)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the LWC source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no LWC styling anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
