#!/usr/bin/env python3
"""Static checks for Salesforce deployment-related anti-patterns.

Scans the project tree for the high-confidence patterns documented
in this skill:

  1. CI / pipeline files (`.github/workflows/*.yml`, `Jenkinsfile`,
     `*.gitlab-ci.yml`, etc.) using `--ignore-errors` on `sf project
     deploy`.
  2. `package.xml` mixing `<members>*</members>` AND explicit
     `<members>X</members>` for the same `<name>type</name>`.
  3. Flow XML with `<status>Draft</status>` (deploy will fail —
     should be Active or Obsolete).
  4. Apex class metadata with `<status>Inactive</status>` (likely
     unintended; should match runtime intent).

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_NS = "http://soap.sforce.com/2006/04/metadata"
_NS_TAG = f"{{{_NS}}}"


def _strip_ns(tag: str) -> str:
    return tag[len(_NS_TAG):] if tag.startswith(_NS_TAG) else tag


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan_pipeline(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings
    for m in re.finditer(r"sf\s+project\s+deploy[^\n]*--ignore-errors", text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: deploy command uses "
            "`--ignore-errors` — masks real failures and produces half-deployed "
            "targets. Triage errors instead "
            "(references/llm-anti-patterns.md § 1)"
        )
    return findings


def _scan_package_xml(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError):
        return findings
    root = tree.getroot()
    if _strip_ns(root.tag) != "Package":
        return findings

    for types_el in root.findall(f"{_NS_TAG}types"):
        name_el = types_el.find(f"{_NS_TAG}name")
        members = types_el.findall(f"{_NS_TAG}members")
        member_values = [m.text for m in members if m.text is not None]
        has_wildcard = "*" in member_values
        has_explicit = any(v != "*" for v in member_values)
        if has_wildcard and has_explicit and name_el is not None and name_el.text:
            findings.append(
                f"{path}: <types> for `{name_el.text}` mixes <members>*</members> "
                "with explicit <members> entries — implementation-defined behavior. "
                "Pick one (references/llm-anti-patterns.md § 7)"
            )
    return findings


def _scan_flow(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError):
        return findings
    root = tree.getroot()
    if _strip_ns(root.tag) != "Flow":
        return findings
    status_el = root.find(f"{_NS_TAG}status")
    if status_el is not None and status_el.text and status_el.text.strip() == "Draft":
        findings.append(
            f"{path}: flow has <status>Draft</status> — deploy will fail. Set "
            "`Active` (in-use) or `Obsolete` (retiring) before deploying "
            "(references/llm-anti-patterns.md § 3)"
        )
    return findings


def _scan_apex_meta(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings
    if "<status>Inactive</status>" in text:
        findings.append(
            f"{path}: Apex class metadata has <status>Inactive</status> — verify "
            "this is intended; deploys with this state can break runtime behavior "
            "(references/gotchas.md § 10)"
        )
    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]

    findings: list[str] = []

    pipeline_globs = [
        "**/.github/workflows/*.yml",
        "**/.github/workflows/*.yaml",
        "**/Jenkinsfile",
        "**/.gitlab-ci.yml",
        "**/azure-pipelines.yml",
        "**/.circleci/config.yml",
    ]
    for pattern in pipeline_globs:
        for f in root.glob(pattern):
            findings.extend(_scan_pipeline(f))

    for f in list(root.rglob("package.xml")):
        findings.extend(_scan_package_xml(f))

    for f in root.rglob("*.flow-meta.xml"):
        findings.extend(_scan_flow(f))

    for f in root.rglob("*.cls-meta.xml"):
        findings.extend(_scan_apex_meta(f))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan a Salesforce project for deployment anti-patterns "
            "(--ignore-errors in CI, mixed wildcard+explicit package.xml, "
            "Draft flows, Inactive Apex classes)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the project (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no deployment anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
