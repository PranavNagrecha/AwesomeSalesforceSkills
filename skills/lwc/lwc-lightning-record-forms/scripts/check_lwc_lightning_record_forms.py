#!/usr/bin/env python3
"""Static checks for LWC Lightning Record Forms anti-patterns.

Scans LWC source for the high-confidence anti-patterns documented in
`references/llm-anti-patterns.md`:

  1. lightning-record-form with both layout-type and fields set.
  2. String-literal field-name (lightning-input-field field-name="X")
     — loses compile-time validation and FLS protection.
  3. lightning-record-edit-form with a type="submit" button but no
     lightning-messages slot — validation errors won't render.

Stdlib only.

Usage:
    python3 check_lwc_lightning_record_forms.py --src-root .
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


_RECORD_FORM_TAG_RE = re.compile(
    r"<lightning-record-form\b([^>]*)>", re.IGNORECASE | re.DOTALL
)
_LAYOUT_TYPE_RE = re.compile(r"\blayout-type\s*=", re.IGNORECASE)
_FIELDS_ATTR_RE = re.compile(r"\bfields\s*=", re.IGNORECASE)
_LITERAL_FIELD_NAME_RE = re.compile(
    r'<lightning-(?:input|output)-field\b[^>]*\bfield-name\s*=\s*"([^"{}]+)"',
    re.IGNORECASE | re.DOTALL,
)
_RECORD_EDIT_FORM_RE = re.compile(
    r"<lightning-record-edit-form\b[^>]*>(.*?)</lightning-record-edit-form>",
    re.IGNORECASE | re.DOTALL,
)
_SUBMIT_BTN_RE = re.compile(r'type\s*=\s*"submit"', re.IGNORECASE)
_LIGHTNING_MESSAGES_RE = re.compile(r"<lightning-messages\b", re.IGNORECASE)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan_html(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    for m in _RECORD_FORM_TAG_RE.finditer(text):
        attrs = m.group(1)
        if _LAYOUT_TYPE_RE.search(attrs) and _FIELDS_ATTR_RE.search(attrs):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: "
                "lightning-record-form has both layout-type and fields "
                "— mutually exclusive (references/llm-anti-patterns.md § 3)"
            )

    for m in _LITERAL_FIELD_NAME_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: "
            f'field-name="{m.group(1)}" is a string literal — import via '
            "@salesforce/schema for FLS-safe binding "
            "(references/llm-anti-patterns.md § 2)"
        )

    for m in _RECORD_EDIT_FORM_RE.finditer(text):
        body = m.group(1)
        if _SUBMIT_BTN_RE.search(body) and not _LIGHTNING_MESSAGES_RE.search(body):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: "
                "lightning-record-edit-form has a type=\"submit\" button "
                "but no <lightning-messages> child — validation errors "
                "will not render (references/llm-anti-patterns.md § 7)"
            )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]
    findings: list[str] = []
    for html in root.rglob("*.html"):
        findings.extend(_scan_html(html))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan LWC HTML templates for record-form anti-patterns "
            "(layout+fields together, literal field-name, missing "
            "lightning-messages)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the LWC source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no LWC record-form anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
