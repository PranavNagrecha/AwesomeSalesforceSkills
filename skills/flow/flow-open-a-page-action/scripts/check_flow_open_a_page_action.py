#!/usr/bin/env python3
"""Checker for the Flow "Open a Page" action (Summer '26) and its navigation alternatives.

Scans a source-format metadata tree of Flow definitions (`*.flow-meta.xml`) and reports:

  WARN  An Open a Page navigation action in a flow that has NO screens. The action is a
        Screen Flow capability; a background flow (record-triggered / autolaunched /
        scheduled / platform-event) has no interactive UI to navigate, so it silently
        does nothing where the user expects it.

  INFO  A legacy redirect (custom navigateToUrl / force:navigateToURL local action, or a
        retURL URL hack) inside a Screen Flow — a candidate to replace with the native
        Open a Page action.

Detection is HEURISTIC and name-based: the exact `actionName` string of the native action
is set by the platform and is intentionally NOT hard-coded here (do not invent one). Matching
keys off recognizable substrings in element/action names, so treat the output as leads to
verify in Flow Builder, not a proof.

Stdlib only — no pip dependencies. Exit code 0 = no WARN-level issues, 1 = at least one WARN.

Usage:
    python3 check_flow_open_a_page_action.py [--manifest-dir path] [--strict]

    --strict  Treat INFO migration candidates as failures too (exit 1 if any are found).
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Substrings (lowercased, non-alphanumerics stripped) that identify the native action.
NATIVE_ACTION_KEYS = ("openapage", "openpage")
# Substrings that identify a legacy/custom redirect the native action can replace.
LEGACY_REDIRECT_KEYS = (
    "navigatetourl",
    "forcenavigatetourl",
    "navigateurl",
    "openurl",
    "redirecturl",
)
# Raw-text markers of the finish-URL / retURL hack.
RETURL_MARKERS = ("returl", "returl=")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Heuristically check Flow metadata for Open a Page action misuse and "
        "legacy redirect migration candidates.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source metadata (searched recursively for *.flow-meta.xml).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also fail (exit 1) when INFO-level migration candidates are found.",
    )
    return parser.parse_args()


def _localname(tag: str) -> str:
    """Strip the XML namespace from a tag, e.g. '{...}actionCalls' -> 'actionCalls'."""
    return tag.rsplit("}", 1)[-1]


def _norm(text: str | None) -> str:
    """Lowercase and strip everything but a-z/0-9 for tolerant substring matching."""
    if not text:
        return ""
    return "".join(ch for ch in text.lower() if ch.isalnum())


def _names_in(element: ET.Element) -> list[str]:
    """Collect the name/label/actionName text of an actionCalls element."""
    names: list[str] = []
    for child in element:
        if _localname(child.tag) in ("name", "label", "actionName") and child.text:
            names.append(child.text)
    return names


def check_flow(path: Path) -> tuple[list[str], list[str]]:
    """Return (warnings, infos) for a single flow file."""
    warnings: list[str] = []
    infos: list[str] = []
    try:
        raw = path.read_text(encoding="utf-8")
        root = ET.fromstring(raw)
    except (OSError, ET.ParseError) as exc:
        return [f"{path}: could not parse Flow XML ({exc})"], []

    elements = list(root.iter())
    has_screens = any(_localname(e.tag) == "screens" for e in elements)

    native_hits: list[str] = []
    legacy_hits: list[str] = []
    for element in elements:
        if _localname(element.tag) != "actionCalls":
            continue
        raw_names = _names_in(element)
        normed = [_norm(n) for n in raw_names]
        label = raw_names[0] if raw_names else "(unnamed action)"
        if any(key in n for n in normed for key in NATIVE_ACTION_KEYS):
            native_hits.append(label)
        elif any(key in n for n in normed for key in LEGACY_REDIRECT_KEYS):
            legacy_hits.append(label)

    if native_hits and not has_screens:
        warnings.append(
            f"{path}: Open a Page action(s) {native_hits} found in a flow with NO screens. "
            f"Open a Page is a Screen Flow action — a background flow can't navigate the user."
        )

    if has_screens:
        for hit in legacy_hits:
            infos.append(
                f"{path}: legacy redirect action '{hit}' in a Screen Flow — candidate to "
                f"replace with the native Open a Page action."
            )
        if any(marker in _norm(raw) for marker in RETURL_MARKERS):
            infos.append(
                f"{path}: a retURL / finish-URL marker appears in this Screen Flow — candidate "
                f"to replace with the native Open a Page action."
            )

    return warnings, infos


def check(manifest_dir: Path) -> tuple[list[str], list[str]]:
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"], []
    flow_files = sorted(manifest_dir.rglob("*.flow-meta.xml"))
    if not flow_files:
        return [], [f"No *.flow-meta.xml files found under {manifest_dir} — nothing to check."]
    all_warnings: list[str] = []
    all_infos: list[str] = []
    for flow in flow_files:
        warnings, infos = check_flow(flow)
        all_warnings.extend(warnings)
        all_infos.extend(infos)
    return all_warnings, all_infos


def main() -> int:
    args = parse_args()
    warnings, infos = check(Path(args.manifest_dir))

    for info in infos:
        print(f"INFO: {info}")
    for warning in warnings:
        print(f"WARN: {warning}", file=sys.stderr)

    if not warnings and not infos:
        print("No issues found.")
        return 0
    if warnings:
        return 1
    if args.strict and infos:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
