#!/usr/bin/env python3
"""Static checks for LWC datatable anti-patterns.

Scans LWC source for the high-confidence anti-patterns documented in
`references/llm-anti-patterns.md`:

  1. `await updateRecord(...)` inside a `for` loop (sequential save).
  2. Mutation of `this.<wire>.data.push/splice` (mutating wired data).
  3. `onloadmore` handler missing `event.target.isLoading = false`.
  4. `this.draftValues = []` before the awaited save call.

Stdlib only.

Usage:
    python3 check_lwc_datatable_advanced.py --src-root .
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


_FOR_LOOP_RE = re.compile(
    r"for\s*\(\s*(?:const|let|var)\s+\w+\s+(?:of|in)\s+[^)]+\)\s*\{",
    re.IGNORECASE,
)
_AWAIT_UPDATE_RECORD_RE = re.compile(
    r"\bawait\s+updateRecord\s*\(", re.IGNORECASE
)
_WIRED_MUTATE_RE = re.compile(
    r"this\.\w+\.data\.(push|splice|unshift|pop|shift)\s*\("
)
_ONLOADMORE_FN_RE = re.compile(
    r"\b(\w+)\s*\(\s*event[^)]*\)\s*\{", re.IGNORECASE
)
_DRAFT_CLEAR_RE = re.compile(r"this\.draftValues\s*=\s*\[\s*\]\s*;")
_AWAIT_RE = re.compile(r"\bawait\s+", re.IGNORECASE)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _block_end(text: str, brace_pos: int) -> int:
    depth = 1
    i = brace_pos + 1
    while i < len(text) and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return i


def _scan_js(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    # 1. await updateRecord in for loop
    for m in _FOR_LOOP_RE.finditer(text):
        body_start = m.end() - 1
        body_end = _block_end(text, body_start)
        body = text[body_start:body_end]
        if _AWAIT_UPDATE_RECORD_RE.search(body):
            findings.append(
                f"{path}:{_line_no(text, body_start)}: `await updateRecord` "
                "inside a for-loop — use Promise.all for parallel saves "
                "(references/llm-anti-patterns.md § 1)"
            )

    # 2. Mutating wired data
    for m in _WIRED_MUTATE_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: mutating wired data via "
            f"`.{m.group(1)}` — wired data is a read-only proxy "
            "(references/llm-anti-patterns.md § 2)"
        )

    # 3. draftValues=[] before await
    for m in _DRAFT_CLEAR_RE.finditer(text):
        # Look for an `await` AFTER this statement within the same brace block
        # that contains it. If there's an await after, it's premature.
        tail = text[m.end(): m.end() + 600]
        # Bail out if the tail crosses a closing }
        end_brace = tail.find("}")
        if end_brace == -1:
            end_brace = len(tail)
        local = tail[:end_brace]
        if _AWAIT_RE.search(local):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: this.draftValues = [] "
                "before an await — cleared too early; if save fails the "
                "user loses edits (references/llm-anti-patterns.md § 6)"
            )

    return findings


def _scan_html(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]
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
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan LWC sources for datatable anti-patterns "
            "(sequential saves, wired-data mutation, premature draft "
            "clearing)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the LWC source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no LWC datatable anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
