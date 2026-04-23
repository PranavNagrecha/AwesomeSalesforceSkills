#!/usr/bin/env python3
"""Checker script for lwc-custom-datatable-types skill.

Scans LWC bundles that subclass `LightningDatatable` and flags:
- missing `customTypes` static property
- entries missing `typeAttributes` list
- `template:` / `editTemplate:` names that do not resolve to sibling .html files

Stdlib only.

Usage:
    python3 check_lwc_custom_datatable_types.py --manifest-dir path/to/force-app
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXTENDS_RE = re.compile(r'class\s+\w+\s+extends\s+LightningDatatable\b')
CUSTOM_TYPES_HEAD_RE = re.compile(r'static\s+customTypes\s*=\s*\{')
ENTRY_HEAD_RE = re.compile(r'([A-Za-z_$][\w$]*)\s*:\s*\{')
TEMPLATE_NAME_RE = re.compile(
    r'(template|editTemplate)\s*:\s*([A-Za-z_$][\w$]*)'
)


def _extract_braced(text: str, open_idx: int) -> tuple[int, int] | None:
    """Return (start, end_exclusive) for the braced block whose `{` is at open_idx.

    Naive brace counter — does not attempt to skip braces inside string
    literals. LWC source in this position rarely contains string braces and the
    worst-case failure mode is a benign miss on an exotic entry.
    """
    if open_idx >= len(text) or text[open_idx] != "{":
        return None
    depth = 0
    i = open_idx
    while i < len(text):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return open_idx, i + 1
        i += 1
    return None


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _iter_top_level_entries(inner: str):
    """Yield (name, entry_body_incl_braces, start_offset_in_inner) at depth 0."""
    depth = 0
    i = 0
    while i < len(inner):
        ch = inner[i]
        if ch == "{":
            depth += 1
            i += 1
            continue
        if ch == "}":
            depth -= 1
            i += 1
            continue
        if depth == 0:
            m = ENTRY_HEAD_RE.match(inner, i)
            if m:
                name = m.group(1)
                brace_rel = m.end() - 1
                span = _extract_braced(inner, brace_rel)
                if span is None:
                    return
                yield name, inner[span[0]:span[1]], m.start()
                i = span[1]
                continue
        i += 1


def iter_datatable_js(root: Path):
    for path in root.rglob("*.js"):
        parts = {p.lower() for p in path.parts}
        if "lwc" not in parts or "__tests__" in parts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if EXTENDS_RE.search(text):
            yield path, text


def collect_imports(text: str) -> dict[str, Path]:
    imports: dict[str, Path] = {}
    for match in re.finditer(
        r'import\s+(\w+)\s+from\s+[\'"]\./([\w\-]+)\.html[\'"]',
        text,
    ):
        alias = match.group(1)
        filename = match.group(2) + ".html"
        imports[alias] = Path(filename)
    return imports


def scan_file(path: Path, text: str) -> list[str]:
    findings: list[str] = []
    head = CUSTOM_TYPES_HEAD_RE.search(text)
    if not head:
        findings.append(
            f"{path}:1: subclasses LightningDatatable but no `customTypes` static property"
        )
        return findings

    brace_idx = head.end() - 1
    span = _extract_braced(text, brace_idx)
    if span is None:
        findings.append(
            f"{path}:{_line_of(text, brace_idx)}: unbalanced braces in customTypes block"
        )
        return findings

    block = text[span[0]:span[1]]
    inner = block[1:-1]
    imports = collect_imports(text)
    bundle_dir = path.parent

    entries = list(_iter_top_level_entries(inner))
    if not entries:
        findings.append(
            f"{path}:{_line_of(text, brace_idx)}: customTypes is declared but empty"
        )

    for name, body, rel_offset in entries:
        abs_offset = span[0] + 1 + rel_offset
        line_no = _line_of(text, abs_offset)

        if "typeAttributes" not in body:
            findings.append(
                f"{path}:{line_no}: customType `{name}` missing `typeAttributes` — "
                f"datatable will drop attribute values silently"
            )
        else:
            arr_match = re.search(r"typeAttributes\s*:\s*(\[[^\]]*\])", body)
            if not arr_match:
                findings.append(
                    f"{path}:{line_no}: customType `{name}` typeAttributes must be "
                    f"an array literal, e.g. typeAttributes: ['variant', 'label']"
                )

        template_seen = False
        for ref in TEMPLATE_NAME_RE.finditer(body):
            kind = ref.group(1)
            alias = ref.group(2)
            if kind == "template":
                template_seen = True
            target = imports.get(alias)
            if target is None:
                findings.append(
                    f"{path}:{line_no}: customType `{name}` {kind} `{alias}` "
                    f"has no matching `import {alias} from './<file>.html'`"
                )
                continue
            if not (bundle_dir / target).exists():
                findings.append(
                    f"{path}:{line_no}: customType `{name}` {kind} -> {target} "
                    f"not found next to {path.name}"
                )

        if not template_seen:
            findings.append(
                f"{path}:{line_no}: customType `{name}` is missing a `template:` reference"
            )

    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit custom lightning-datatable subclasses for common authoring mistakes.",
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
    for path, text in iter_datatable_js(root):
        findings.extend(scan_file(path, text))

    if not findings:
        print("No custom-datatable-type issues found.")
        return 0

    for item in findings:
        print(f"WARN: {item}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
