#!/usr/bin/env python3
"""Checker script for Apex Trigger Bypass And Killswitch Patterns skill.

Scans .cls and .trigger files for missing or unsafe bypass / kill-switch
patterns. Stdlib only.

Severity:
    P0 — must fix (e.g. hardcoded user-id bypass)
    P1 — handler missing kill-switch wiring
    P2 — code smell (commented-out trigger logic)

Exit codes:
    0  no P0/P1 findings (P2 only or none)
    1  one or more P0/P1 findings
    2  bad invocation / IO error

Usage:
    python3 check_apex_trigger_bypass_and_killswitch_patterns.py [--manifest-dir DIR]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

# (severity, message)
Finding = Tuple[str, str]

# Hardcoded user-id equality check used as a bypass — wrong, brittle, no audit.
HARDCODED_USERID_RE = re.compile(
    r"UserInfo\.getUserId\(\)\s*==\s*['\"]005[A-Za-z0-9]{12,15}['\"]"
)

# Signals that the handler has SOME kill-switch wiring.
KILLSWITCH_SIGNALS = (
    "Trigger_Setting__mdt",
    "FeatureManagement.checkPermission",
    "TriggerControl.isActive",
    "TriggerControl.isBypassed",
)

# A class that extends TriggerHandler is in scope for the kill-switch check.
HANDLER_DECL_RE = re.compile(
    r"\bclass\s+\w+\s+extends\s+TriggerHandler\b", re.IGNORECASE
)

# Commented-out handler invocation inside a trigger file.
COMMENTED_HANDLER_RE = re.compile(
    r"^\s*//.*new\s+\w+TriggerHandler\s*\(\s*\)\s*\.\s*run\s*\(",
    re.MULTILINE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Apex .cls and .trigger files for missing / unsafe trigger "
            "bypass and kill-switch patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: cwd).",
    )
    return parser.parse_args()


def scan_apex_file(path: Path) -> List[Finding]:
    findings: List[Finding] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [("P0", f"Could not read {path}: {exc}")]

    # P0 — hardcoded user-id bypass.
    for match in HARDCODED_USERID_RE.finditer(text):
        findings.append(
            (
                "P0",
                f"{path}: hardcoded UserInfo.getUserId() == '005...' bypass at "
                f"offset {match.start()}. Use Custom Permission + "
                f"FeatureManagement.checkPermission instead.",
            )
        )

    # P1 — TriggerHandler subclass with no kill-switch signal.
    if path.suffix == ".cls" and HANDLER_DECL_RE.search(text):
        if not any(signal in text for signal in KILLSWITCH_SIGNALS):
            findings.append(
                (
                    "P1",
                    f"{path}: TriggerHandler subclass has no kill-switch check "
                    f"(expected one of: Trigger_Setting__mdt, "
                    f"FeatureManagement.checkPermission, TriggerControl.isActive).",
                )
            )

    # P2 — commented-out trigger handler invocation inside .trigger files.
    if path.suffix == ".trigger":
        for match in COMMENTED_HANDLER_RE.finditer(text):
            line_num = text.count("\n", 0, match.start()) + 1
            findings.append(
                (
                    "P2",
                    f"{path}:{line_num}: commented-out handler invocation. "
                    f"Use a kill switch (Trigger_Setting__mdt.Is_Active__c) "
                    f"instead of commenting code out.",
                )
            )

    return findings


def collect_apex_files(root: Path) -> List[Path]:
    if not root.exists():
        raise FileNotFoundError(f"Manifest directory not found: {root}")
    files: List[Path] = []
    files.extend(root.rglob("*.cls"))
    files.extend(root.rglob("*.trigger"))
    return files


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)

    try:
        files = collect_apex_files(root)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not files:
        print(f"No .cls or .trigger files found under {root}.")
        return 0

    all_findings: List[Finding] = []
    for path in files:
        all_findings.extend(scan_apex_file(path))

    if not all_findings:
        print(f"OK: scanned {len(files)} Apex file(s); no bypass/kill-switch issues.")
        return 0

    severity_counts = {"P0": 0, "P1": 0, "P2": 0}
    for severity, message in all_findings:
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        stream = sys.stderr if severity in ("P0", "P1") else sys.stdout
        print(f"{severity}: {message}", file=stream)

    print(
        "\nSummary: "
        f"P0={severity_counts['P0']} "
        f"P1={severity_counts['P1']} "
        f"P2={severity_counts['P2']} "
        f"(scanned {len(files)} file(s))"
    )

    if severity_counts["P0"] > 0 or severity_counts["P1"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
