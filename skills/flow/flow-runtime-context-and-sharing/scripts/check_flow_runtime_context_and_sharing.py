#!/usr/bin/env python3
"""Static checker for flow-runtime-context-and-sharing.

Parses *.flow-meta.xml under --manifest-dir and audits the flow-level runInMode.
Stdlib only; reads metadata, never runs a flow. Grounding is the Metadata API
Developer Guide 264 ("api_meta"); line numbers come from `grep -n`.

ERROR (exit 1 always)
  * A file that does not parse.
  * runInMode is not one of DefaultMode, SystemModeWithSharing,
    SystemModeWithoutSharing, UserMode (api_meta 264 L70907-70927).
  * runInMode UserMode in a flow with apiVersion below 68.0 (L70926-70927), or
    SystemModeWithoutSharing below 49.0 (L70921-70922).
  * runInMode appears inside an element rather than as a child of Flow. The guide
    documents it only on the Flow (L70907; sample L76526-76533).
WARN (exit 0 unless --strict)
  * No runInMode: the flow relies on DefaultMode, which depends on how the flow is
    launched (api_meta 264 L70908-70909). SKILL.md Review Checklist asks for an
    explicit value.
  * No apiVersion pinned (Review Checklist).
  * SystemModeWithoutSharing with no <description> (Review Checklist asks for a
    justification block).
  * A screen flow (processType Flow) with SystemModeWithoutSharing (Decision Guidance).

An empty tree prints one WARN and exits 0 (1 with --strict). A missing path prints an
ERROR and exits 1.

Usage:
    python3 check_flow_runtime_context_and_sharing.py --manifest-dir force-app/main/default [--strict]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MODES = {"DefaultMode", "SystemModeWithSharing", "SystemModeWithoutSharing", "UserMode"}


def local(el: ET.Element) -> str:
    return el.tag.split("}")[-1]


def text(parent: ET.Element, name: str) -> str:
    for c in parent:
        if local(c) == name:
            return (c.text or "").strip()
    return ""


def check_flow(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warns: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"{path}: XML does not parse ({exc})"], warns
    for child in root:
        if local(child) == "runInMode":
            continue
        for el in child.iter():
            if el is not child and local(el) == "runInMode":
                errors.append(f"{path}: runInMode inside element {local(child)}; the guide documents it only on the Flow (api_meta 264 L70907)")
    mode = text(root, "runInMode")
    api = text(root, "apiVersion")
    try:
        version = float(api) if api else None
    except ValueError:
        version = None
        errors.append(f"{path}: apiVersion {api!r} is not a number")
    if mode and mode not in MODES:
        errors.append(f"{path}: runInMode {mode!r} is not a documented value (api_meta 264 L70907-70927)")
    if mode == "UserMode" and version is not None and version < 68.0:
        errors.append(f"{path}: UserMode needs API version 68.0 or later, found {api} (api_meta 264 L70926-70927)")
    if mode == "SystemModeWithoutSharing" and version is not None and version < 49.0:
        errors.append(f"{path}: SystemModeWithoutSharing needs API version 49.0 or later, found {api} (api_meta 264 L70921-70922)")
    if not mode:
        warns.append(f"{path}: no runInMode; DefaultMode depends on how the flow is launched (api_meta 264 L70908-70909)")
    if not api:
        warns.append(f"{path}: no apiVersion pinned")
    if mode == "SystemModeWithoutSharing":
        if not text(root, "description"):
            warns.append(f"{path}: SystemModeWithoutSharing with no description; add the justification block")
        if text(root, "processType") == "Flow":
            warns.append(f"{path}: screen flow in SystemModeWithoutSharing; keep screens in user context and escalate in a subflow")
    return errors, warns


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the flow-level runInMode of Flow metadata.")
    parser.add_argument("--manifest-dir", default=".", help="Root of the metadata tree (default: current directory).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings too.")
    args = parser.parse_args()
    root_dir = Path(args.manifest_dir)
    if not root_dir.is_dir():
        print(f"ERROR: manifest directory not found: {root_dir}")
        sys.exit(1)
    files = sorted(root_dir.rglob("*.flow-meta.xml"))
    if not files:
        print(f"WARN: no *.flow-meta.xml files found under {root_dir}")
        return 1 if args.strict else 0
    errors: list[str] = []
    warns: list[str] = []
    for f in files:
        e, w = check_flow(f)
        errors += e
        warns += w
    for e in errors:
        print(f"ERROR: {e}")
    for w in warns:
        print(f"WARN: {w}")
    if not errors and not warns:
        print("No issues found.")
    if errors:
        sys.exit(1)
    return 1 if (warns and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
