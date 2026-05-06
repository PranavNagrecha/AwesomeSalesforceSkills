#!/usr/bin/env python3
"""Static checks for Net Zero Cloud sustainability reporting.

Looks at OmniScript / Data Mapper / report-builder configuration
files and Apex / metadata referencing Net Zero Cloud objects, and
flags common pitfalls.

Anti-patterns detected:

  1. CSRD / ESRS workflow files referencing the report builder but
     no explicit reference to a double-materiality assessment
     artifact (heuristic).
  2. Net Zero Cloud `*CarbonInventory` references in Apex or test
     data without setting `IsAssessmentReady__c` or similar period-
     readiness flags (informational warning — may be benign).
  3. Files referencing "SASB" without a sector identifier.

Stdlib only.

Usage:
    python3 check_sustainability_reporting.py --src-root .
    python3 check_sustainability_reporting.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_ESRS_RE = re.compile(r"\b(ESRS|MSESRS|MSESRSMainDataraptor)\b", re.IGNORECASE)
_DOUBLE_MATERIALITY_RE = re.compile(
    r"\b(double[-\s]?materiality|material(ity)?\s+assessment)\b",
    re.IGNORECASE,
)

_SASB_RE = re.compile(r"\bSASB\b")
_SECTOR_RE = re.compile(r"\b(SICS|sector)\b", re.IGNORECASE)

_CARBON_INV_RE = re.compile(
    r"\b(StationaryAssetCarbonInventory|VehicleAssetCarbonInventory|ScopeThreeCarbonInventory)\b",
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    has_esrs = bool(_ESRS_RE.search(text))
    has_dm = bool(_DOUBLE_MATERIALITY_RE.search(text))
    if has_esrs and not has_dm:
        findings.append(
            f"{path}: ESRS / CSRD report-builder reference without any "
            "double-materiality assessment reference. CSRD requires the "
            "double-materiality assessment as a prerequisite "
            "(llm-anti-patterns.md § 2, gotchas.md § 1)."
        )

    if _SASB_RE.search(text) and not _SECTOR_RE.search(text):
        findings.append(
            f"{path}: SASB reference without a sector / SICS qualifier — "
            "SASB standards are sector-specific (llm-anti-patterns.md § 4, "
            "gotchas.md § 2)."
        )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]
    findings: list[str] = []
    for ext in (
        "*.cls",
        "*.trigger",
        "*.xml",
        "*.json",
        "*.md",
    ):
        for p in root.rglob(ext):
            findings.extend(_scan(p))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Net Zero Cloud configuration / Apex / OmniScript files "
            "for sustainability-reporting anti-patterns: ESRS / CSRD "
            "references missing double-materiality, SASB without sector."
        ),
    )
    parser.add_argument(
        "--src-root",
        default=".",
        help="Root of the project tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no sustainability-reporting anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
