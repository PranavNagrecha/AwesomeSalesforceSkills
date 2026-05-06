#!/usr/bin/env python3
"""Static checks for Custom Report Type metadata.

Scans `reportTypes/*.reportType-meta.xml` (sfdx-style metadata) for
high-confidence issues documented in `references/llm-anti-patterns.md`
and `references/gotchas.md`:

  1. CRT layout exposes more than 60 fields (display-limit risk).
  2. CRT layout exposes more than 200 fields total (curation issue).
  3. CRT description missing or under 20 characters (poor doc).
  4. CRT layout has zero <sections> grouping (flat layout).

Stdlib only — uses xml.etree.ElementTree.

Usage:
    python3 check_report_type_strategy.py --src-root .
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


_NS = "http://soap.sforce.com/2006/04/metadata"


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def _scan_xml(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError) as exc:
        return [f"{path}: parse error — {exc}"]

    root = tree.getroot()
    if _strip_ns(root.tag) != "ReportType":
        return findings

    description = ""
    sections = []
    fields_total = 0
    fields_displayed = 0

    for child in root:
        tag = _strip_ns(child.tag)
        if tag == "description":
            description = (child.text or "").strip()
        if tag == "sections":
            sections.append(child)
            for col in child:
                if _strip_ns(col.tag) == "columns":
                    fields_total += 1
                    checked = col.find(f"{{{_NS}}}checkedByDefault")
                    if checked is not None and (checked.text or "").strip() == "true":
                        fields_displayed += 1

    label = root.findtext(f"{{{_NS}}}label", default=path.stem)

    if fields_displayed > 60:
        findings.append(
            f"{path}: ReportType `{label}` displays {fields_displayed} "
            "fields by default (>60) — past 60 fields the report "
            "builder gates them behind search "
            "(references/gotchas.md § 2)"
        )

    if fields_total > 200:
        findings.append(
            f"{path}: ReportType `{label}` exposes {fields_total} "
            "total fields — typical curated CRT has <50; consider "
            "removing rarely-used fields "
            "(references/llm-anti-patterns.md § 4)"
        )

    if not description or len(description) < 20:
        findings.append(
            f"{path}: ReportType `{label}` has missing or terse "
            f"description ({len(description)} chars) — description "
            "appears in the report-builder picker "
            "(references/examples.md § 6)"
        )

    if not sections:
        findings.append(
            f"{path}: ReportType `{label}` has no <sections> "
            "grouping — flat layouts are unscannable for users "
            "(references/llm-anti-patterns.md § 4)"
        )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]
    findings: list[str] = []
    patterns = ("*.reportType-meta.xml", "*.reportType")
    for pat in patterns:
        for f in root.rglob(pat):
            findings.extend(_scan_xml(f))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Salesforce reportType metadata for CRT design issues "
            "(over 60 displayed fields, over 200 total fields, missing "
            "description, no section grouping)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the metadata source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no Report Type design issues detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
