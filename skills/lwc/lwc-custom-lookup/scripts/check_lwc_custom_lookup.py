#!/usr/bin/env python3
"""Static checks for LWC custom-lookup anti-patterns.

Scans LWC source for the high-confidence anti-patterns documented in
`references/llm-anti-patterns.md`:

  1. oninput handler calling an Apex import directly with no
     setTimeout/debounce.
  2. onclick on a child of role="listbox" (should be onmousedown).
  3. @AuraEnabled search method missing cacheable=true.
  4. ArrowDown/ArrowUp branch missing preventDefault.

Stdlib only.

Usage:
    python3 check_lwc_custom_lookup.py --src-root .
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


_ONINPUT_HANDLER_RE = re.compile(
    r"\boninput\s*=\s*\{(\w+)\}", re.IGNORECASE
)
_LISTBOX_BLOCK_RE = re.compile(
    r'role\s*=\s*"listbox"[^>]*>(.*?)</(?:ul|ol|div)>',
    re.IGNORECASE | re.DOTALL,
)
_ONCLICK_INSIDE_LISTBOX_RE = re.compile(r"\bonclick\s*=", re.IGNORECASE)
_AURA_ENABLED_RE = re.compile(
    r"@AuraEnabled\s*(?:\([^)]*\))?\s*\n\s*public\s+static\s+\S+\s+(search\w+)",
    re.IGNORECASE,
)
_CACHEABLE_RE = re.compile(r"cacheable\s*=\s*true", re.IGNORECASE)
_ARROW_KEY_CASE_RE = re.compile(
    r"case\s+'(ArrowDown|ArrowUp)'\s*:\s*([^;]*?;[^;]*?;)", re.DOTALL
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan_js(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    # 1. oninput handler that calls the apex import without a setTimeout.
    # Heuristic: read the handler body from the JS file.
    for m in _ONINPUT_HANDLER_RE.finditer(text):
        handler = m.group(1)
        # Look for a method definition `<handler>(...)` body in the same file.
        body_re = re.compile(
            rf"\b{re.escape(handler)}\s*\([^)]*\)\s*\{{(.*?)\n\s*\}}",
            re.DOTALL,
        )
        body_m = body_re.search(text)
        if body_m:
            body = body_m.group(1)
            if "setTimeout" not in body and "debounce" not in body.lower():
                findings.append(
                    f"{path}:{_line_no(text, body_m.start())}: oninput "
                    f"handler `{handler}` does not appear to debounce — "
                    "wrap the search call in setTimeout/clearTimeout "
                    "(references/llm-anti-patterns.md § 1)"
                )

    # 3. @AuraEnabled search method missing cacheable=true
    for m in _AURA_ENABLED_RE.finditer(text):
        head = text[max(0, m.start() - 200): m.end()]
        if not _CACHEABLE_RE.search(head):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: @AuraEnabled "
                f"method `{m.group(1)}` is missing cacheable=true — "
                "wire layer cannot dedupe repeated keystrokes "
                "(references/llm-anti-patterns.md § 4)"
            )

    # 4. ArrowDown/ArrowUp case without preventDefault
    for m in _ARROW_KEY_CASE_RE.finditer(text):
        block = m.group(2)
        if "preventDefault" not in block:
            findings.append(
                f"{path}:{_line_no(text, m.start())}: case '{m.group(1)}' "
                "missing event.preventDefault() — page scrolls during "
                "keyboard nav (references/llm-anti-patterns.md § 6)"
            )

    return findings


def _scan_html(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    # 2. onclick inside role="listbox"
    for m in _LISTBOX_BLOCK_RE.finditer(text):
        block = m.group(1)
        if _ONCLICK_INSIDE_LISTBOX_RE.search(block):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: onclick inside "
                "role=\"listbox\" — use onmousedown so selection fires "
                "before input blur "
                "(references/llm-anti-patterns.md § 2)"
            )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]
    findings: list[str] = []
    for js in root.rglob("*.js"):
        findings.extend(_scan_js(js))
    for html in root.rglob("*.html"):
        findings.extend(_scan_html(html))
    for cls in root.rglob("*.cls"):
        findings.extend(_scan_js(cls))  # AuraEnabled scan also works on .cls
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan LWC + Apex sources for custom-lookup anti-patterns "
            "(no debounce, onclick in listbox, missing cacheable=true, "
            "missing preventDefault)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no LWC custom-lookup anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
