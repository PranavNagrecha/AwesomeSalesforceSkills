#!/usr/bin/env python3
"""Heuristic checker that flags likely mis-matched OmniStudio / Flow choices.

Examines a project directory for patterns that typically indicate a
better-fit tool was available:
- Screen Flows with 6+ screens and branching (OmniScript may fit better).
- Short (1-3 screen) OmniScripts owned by admins (Screen Flow likely cheaper).
- Flow XML containing large string-concatenation chains for JSON payloads
  (Integration Procedure likely better).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check a project for OmniStudio / Flow tool mismatch signals.",
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Directory containing flow and omnistudio metadata.",
    )
    return parser.parse_args()


def count_elements(xml_text: str, tag: str) -> int:
    return len(re.findall(rf"<{tag}[\s>]", xml_text))


def check_flow(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    screens = count_elements(text, "screens")
    decisions = count_elements(text, "decisions")

    if screens >= 6 and decisions >= 3:
        issues.append(
            f"{path}: Screen Flow has {screens} screens and {decisions} decisions — OmniScript may be a better fit"
        )

    concat_markers = text.count("&amp;") + text.lower().count('"concat"')
    if concat_markers >= 10 and "<actionCalls>" in text:
        issues.append(
            f"{path}: Flow contains heavy string concatenation with action calls — Integration Procedure likely fits better"
        )
    return issues


def check_omniscript(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    steps = text.lower().count('"type":"step"')
    if 0 < steps <= 3:
        issues.append(
            f"{path}: OmniScript has only {steps} step(s) — Screen Flow likely cheaper to operate"
        )
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.project_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    flow_files = list(root.rglob("*.flow-meta.xml"))
    omniscript_files = list(root.rglob("*OmniScript*.json"))

    all_issues: list[str] = []
    for path in flow_files:
        all_issues.extend(check_flow(path))
    for path in omniscript_files:
        all_issues.extend(check_omniscript(path))

    if not all_issues:
        print("No obvious OmniStudio/Flow mismatches detected.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
