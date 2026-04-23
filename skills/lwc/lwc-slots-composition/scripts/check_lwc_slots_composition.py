#!/usr/bin/env python3
"""Checker script for the lwc-slots-composition skill.

Scans LWC component bundles under --manifest-dir and flags common slot-
composition mistakes:

    1. ``::slotted(`` in a component CSS file whose bundle is NOT declared as
       light DOM in the ``.js-meta.xml``. LWC shadow DOM does not support the
       ``::slotted`` pseudo-element — the rule is silently dead.
    2. More than one default (unnamed) ``<slot>`` in the same template. Slot
       assignment becomes ambiguous and the template is invalid.
    3. ``slot="..."`` used on an element whose parent tag is a plain HTML tag
       rather than a custom element (``<c-*>``, ``<lightning-*>``,
       ``<lwc-*>``, or another kebab-cased custom element). Slot assignment
       must be a direct child of the receiving custom element.

Stdlib only. Usage:

    python3 check_lwc_slots_composition.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Any tag containing a hyphen is a custom element (HTML custom-element rule).
# Plain HTML tags never contain a hyphen.
_HTML_TAG_RE = re.compile(r"<\s*([a-zA-Z][a-zA-Z0-9:-]*)\b([^>]*)>")
_SLOT_TAG_RE = re.compile(r"<\s*slot\b([^>]*)>", re.IGNORECASE)
_NAME_ATTR_RE = re.compile(r"""\bname\s*=\s*["']([^"']*)["']""", re.IGNORECASE)
_SLOT_ATTR_ON_CHILD_RE = re.compile(
    r"""<\s*([a-zA-Z][a-zA-Z0-9:-]*)\b([^>]*?)\bslot\s*=\s*["']([^"']+)["']([^>]*)>""",
    re.IGNORECASE,
)
_LIGHT_DOM_META_RE = re.compile(
    r"<\s*lwc:renderMode\s*>\s*light\s*</\s*lwc:renderMode\s*>",
    re.IGNORECASE,
)


@dataclass
class Finding:
    path: Path
    line: int
    message: str

    def format(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check LWC slot composition for common mistakes: "
            "::slotted() in shadow-DOM CSS, multiple default slots, "
            "and misplaced slot='...' assignment."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _bundle_is_light_dom(html_file: Path) -> bool:
    """Return True if the component bundle declares light DOM via renderMode.

    LWC light DOM is opted in via ``<lwc:renderMode>light</lwc:renderMode>`` in
    the component's ``.js-meta.xml``. We also treat a JS file containing
    ``static renderMode = 'light'`` as light DOM.
    """
    bundle_dir = html_file.parent
    for meta in bundle_dir.glob("*.js-meta.xml"):
        try:
            content = meta.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if _LIGHT_DOM_META_RE.search(content):
            return True
    for js in bundle_dir.glob("*.js"):
        try:
            content = js.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if re.search(r"""static\s+renderMode\s*=\s*['"]light['"]""", content):
            return True
    return False


def _check_slotted_in_shadow_css(
    manifest_dir: Path, findings: list[Finding]
) -> None:
    """Flag ``::slotted(`` inside a shadow-DOM component's CSS."""
    for css_file in manifest_dir.rglob("lwc/**/*.css"):
        try:
            content = css_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Pair CSS with the matching template to check light-DOM status.
        html_siblings = list(css_file.parent.glob("*.html"))
        if not html_siblings:
            continue
        if _bundle_is_light_dom(html_siblings[0]):
            continue
        for match in re.finditer(r"::slotted\s*\(", content):
            line = _line_of(content, match.start())
            findings.append(
                Finding(
                    path=css_file,
                    line=line,
                    message=(
                        "::slotted() is not supported in LWC shadow DOM. "
                        "Style slotted content from the parent's CSS, or "
                        "opt the child into light DOM via "
                        "<lwc:renderMode>light</lwc:renderMode>."
                    ),
                )
            )


def _check_multiple_default_slots(
    html_file: Path, content: str, findings: list[Finding]
) -> None:
    """Flag more than one default (unnamed) <slot> in the same template."""
    default_slots: list[int] = []
    for match in _SLOT_TAG_RE.finditer(content):
        attrs = match.group(1)
        if not _NAME_ATTR_RE.search(attrs):
            default_slots.append(match.start())
    if len(default_slots) > 1:
        for idx in default_slots:
            findings.append(
                Finding(
                    path=html_file,
                    line=_line_of(content, idx),
                    message=(
                        f"Template contains {len(default_slots)} default "
                        "(unnamed) <slot> elements. Only one default slot is "
                        "allowed per template — name the extras via "
                        '<slot name="...">.'
                    ),
                )
            )


def _find_enclosing_parent_tag(content: str, position: int) -> str | None:
    """Walk backwards from ``position`` and return the nearest open tag name.

    Returns ``None`` if no open tag is found before ``position`` (i.e. the
    element is at template root, which in an LWC template is itself inside
    ``<template>``). For our purposes, "template root" counts as a valid
    parent only if it is ``<template>`` — we treat that as "inside the child's
    own template," which is still a misuse because assignment must happen in
    the parent component's template referencing a custom element.
    """
    depth = 0
    # Scan tags before `position` in reverse.
    tags = list(_HTML_TAG_RE.finditer(content, 0, position))
    for match in reversed(tags):
        tag_text = match.group(0)
        tag_name = match.group(1).lower()
        if tag_text.startswith("</"):
            # Closing tag increases depth (we skip past its block).
            depth += 1
            continue
        if tag_text.endswith("/>"):
            # Self-closing tag — doesn't affect containment.
            continue
        if tag_name in {"br", "hr", "img", "input", "meta", "link"}:
            continue
        if depth > 0:
            depth -= 1
            continue
        return tag_name
    return None


def _check_slot_assignment_parent(
    html_file: Path, content: str, findings: list[Finding]
) -> None:
    """Flag ``slot="..."`` placed on a child of a plain HTML element.

    Slot assignment only makes sense when the element is a direct child of
    the custom element that owns the slots. A custom element tag contains a
    hyphen (``<c-card>``, ``<lightning-button>``, ``<c-ui-modal>``).
    """
    for match in _SLOT_ATTR_ON_CHILD_RE.finditer(content):
        element_tag = match.group(1).lower()
        # Skip <slot> itself — having slot="..." on <slot> is a different
        # (also incorrect) pattern covered implicitly by the "name" attr check.
        if element_tag == "slot":
            continue
        parent = _find_enclosing_parent_tag(content, match.start())
        # Template root: parent is implicit <template>, not a custom element.
        is_custom_element_parent = parent is not None and "-" in parent
        if is_custom_element_parent:
            continue
        line = _line_of(content, match.start())
        parent_label = parent if parent else "<template root>"
        findings.append(
            Finding(
                path=html_file,
                line=line,
                message=(
                    f'slot="{match.group(3)}" is on <{element_tag}> whose '
                    f"parent is <{parent_label}>, which is not a custom "
                    "element. Slot assignment must happen on a direct child "
                    "of the custom element that declares the slot."
                ),
            )
        )


def check_lwc_slots_composition(manifest_dir: Path) -> list[Finding]:
    findings: list[Finding] = []

    if not manifest_dir.exists():
        findings.append(
            Finding(
                path=manifest_dir,
                line=0,
                message=f"Manifest directory not found: {manifest_dir}",
            )
        )
        return findings

    for html_file in manifest_dir.rglob("lwc/**/*.html"):
        try:
            content = html_file.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            findings.append(
                Finding(
                    path=html_file,
                    line=0,
                    message=f"Could not read file: {exc}",
                )
            )
            continue
        _check_multiple_default_slots(html_file, content, findings)
        _check_slot_assignment_parent(html_file, content, findings)

    _check_slotted_in_shadow_css(manifest_dir, findings)

    return findings


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    findings = check_lwc_slots_composition(manifest_dir)

    if not findings:
        print("No slot-composition issues found.")
        return 0

    for finding in findings:
        print(f"WARN: {finding.format()}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
