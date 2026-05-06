#!/usr/bin/env python3
"""Static checks for LWC drag-and-drop anti-patterns.

Scans LWC source for the high-confidence anti-patterns documented in
`references/llm-anti-patterns.md`:

  1. ondragover handler missing event.preventDefault().
  2. dataTransfer.getData(...) inside ondragover/ondragenter/
     ondragleave handlers.
  3. draggable="true" elements with no companion onkeydown handler
     anywhere in the same template (heuristic for missing keyboard
     alternative).
  4. DOM-mutation calls (classList, style.) inside ondragover handlers.

Stdlib only.

Usage:
    python3 check_lwc_drag_and_drop.py --src-root .
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


_HANDLER_FN_RE = re.compile(
    r"\b(\w+)\s*\(\s*(\w+)[^)]*\)\s*\{", re.IGNORECASE
)
_PREVENT_DEFAULT_RE = re.compile(r"\bpreventDefault\s*\(")
_GET_DATA_RE = re.compile(r"\bdataTransfer\.getData\s*\(")
_DOM_MUTATE_RE = re.compile(r"\bclassList\.(add|remove|toggle)\s*\(|\bstyle\.\w+\s*=")
_ONDRAGOVER_BIND_RE = re.compile(r"ondragover\s*=\s*\{(\w+)\}", re.IGNORECASE)
_ONDRAG_HOVER_BIND_RE = re.compile(
    r"on(dragover|dragenter|dragleave)\s*=\s*\{(\w+)\}", re.IGNORECASE
)
_DRAGGABLE_TRUE_RE = re.compile(r'draggable\s*=\s*"true"', re.IGNORECASE)
_ONKEYDOWN_RE = re.compile(r"onkeydown\s*=\s*\{", re.IGNORECASE)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _function_body(text: str, fn_name: str) -> tuple[int, str] | None:
    pat = re.compile(
        rf"\b{re.escape(fn_name)}\s*\([^)]*\)\s*\{{", re.IGNORECASE
    )
    m = pat.search(text)
    if not m:
        return None
    depth = 1
    i = m.end()
    while i < len(text) and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return m.start(), text[m.end(): i - 1]


def _scan_js(path: Path, html_handlers: dict[str, set[str]]) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    component_dir = path.parent.name
    over_handlers = html_handlers.get(component_dir + ":dragover", set())
    hover_handlers = html_handlers.get(component_dir + ":hover", set())

    # 1. ondragover handler missing preventDefault
    for fn in over_handlers:
        body = _function_body(text, fn)
        if body is None:
            continue
        start, content = body
        if not _PREVENT_DEFAULT_RE.search(content):
            findings.append(
                f"{path}:{_line_no(text, start)}: ondragover handler "
                f"`{fn}` missing event.preventDefault() — drop won't "
                "fire (references/llm-anti-patterns.md § 1)"
            )
        # 4. DOM mutation in ondragover
        if _DOM_MUTATE_RE.search(content):
            findings.append(
                f"{path}:{_line_no(text, start)}: ondragover handler "
                f"`{fn}` performs DOM mutation — fires every ~50ms; use "
                "dragenter/dragleave for visual state "
                "(references/llm-anti-patterns.md § 6)"
            )

    # 2. getData in any hover handler
    for fn in hover_handlers:
        body = _function_body(text, fn)
        if body is None:
            continue
        start, content = body
        if _GET_DATA_RE.search(content):
            findings.append(
                f"{path}:{_line_no(text, start)}: `{fn}` calls "
                "dataTransfer.getData() in a hover-phase handler — "
                "returns empty for security; use component state "
                "(references/llm-anti-patterns.md § 2)"
            )

    return findings


def _scan_html(path: Path) -> tuple[list[str], dict[str, set[str]]]:
    findings: list[str] = []
    handlers: dict[str, set[str]] = {}
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"], handlers

    component_dir = path.parent.name

    # Collect handler names by phase
    over_set = set()
    hover_set = set()
    for m in _ONDRAG_HOVER_BIND_RE.finditer(text):
        phase = m.group(1).lower()
        fn = m.group(2)
        hover_set.add(fn)
        if phase == "dragover":
            over_set.add(fn)
    handlers[component_dir + ":dragover"] = over_set
    handlers[component_dir + ":hover"] = hover_set

    # 3. draggable="true" without onkeydown anywhere in the template
    if _DRAGGABLE_TRUE_RE.search(text) and not _ONKEYDOWN_RE.search(text):
        findings.append(
            f"{path}: template has draggable=\"true\" elements but no "
            "onkeydown handler — keyboard alternative missing "
            "(references/llm-anti-patterns.md § 3)"
        )

    return findings, handlers


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]
    findings: list[str] = []
    handler_index: dict[str, set[str]] = {}
    for html in root.rglob("*.html"):
        f, h = _scan_html(html)
        findings.extend(f)
        for k, v in h.items():
            handler_index.setdefault(k, set()).update(v)
    for js in root.rglob("*.js"):
        findings.extend(_scan_js(js, handler_index))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan LWC sources for drag-and-drop anti-patterns "
            "(missing preventDefault, getData in hover, missing "
            "keyboard handler, DOM mutation in dragover)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the LWC source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no LWC drag-and-drop anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
