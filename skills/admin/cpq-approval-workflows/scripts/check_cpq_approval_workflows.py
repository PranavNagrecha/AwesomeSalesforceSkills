#!/usr/bin/env python3
"""Checker script for CPQ Approval Workflows skill.

Scans a local SFDX / Metadata API tree for CPQ Advanced Approvals configuration issues.
The Advanced Approvals package (SBAA__) is not in the corpus, and of CPQ it holds only the
managed package and its SBQQ__ prefix (sfdx_dev 264 L6306-6307; object_reference 264
L71334-71339), so every package-specific rule is REVIEW, never ERROR.

  ERROR   an approvalProcess file that does not parse, or one missing a Required field
          (active, allowedSubmitters, label — api_meta 264 L25132, L25141, L25215)
  REVIEW  AP-001 a standard approval process on SBQQ__Quote__c (file SBQQ__Quote__c.*):
          entryCriteria evaluates the submitted record (L25183-25185), so line values
          reach it only through a quote field
  REVIEW  AP-002 SBQQ__ object folders present but no SBAA__ ones
  REVIEW  AP-003 a flow with a submit action (actionType submit, api_meta 264 L103531)
          that names SBQQ__Quote__c and no SBAA__ element
  REVIEW  AP-004 a permission set naming SBQQ__ but not SBAA__
  WARN    AP-005 a hard-coded 005 user ID in a flow

Stdlib only. Exit 1 on ERROR; WARN/REVIEW exit 0 unless --strict; empty dir one WARN;
missing dir ERROR exit 1.

Usage:
    python3 check_cpq_approval_workflows.py --manifest-dir force-app/main/default [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

QUOTE = "SBQQ__Quote__c"
REQUIRED_AP_FIELDS = ("active", "allowedSubmitters", "label")
USER_ID = re.compile(r"\b005[A-Za-z0-9]{12}(?:[A-Za-z0-9]{3})?\b")
SUBMIT_ACTION = re.compile(r"<actionType>\s*submit\s*</actionType>")


def local(tag: str) -> str:
    return tag.split("}", 1)[-1]


def files(root: Path, *suffixes: str) -> list[Path]:
    return [p for p in root.rglob("*") if p.is_file() and p.name.endswith(suffixes)]


def scan(root: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for f in files(root, ".approvalProcess-meta.xml", ".approvalProcess"):
        try:
            r = ET.parse(f).getroot()
        except ET.ParseError as exc:
            out.append(("ERROR", f"{f}: does not parse: {exc}"))
            continue
        present = {local(c.tag) for c in r}
        for req in REQUIRED_AP_FIELDS:
            if req not in present:
                out.append(("ERROR", f"{f}: ApprovalProcess missing Required <{req}>"))
        if f.name.startswith(QUOTE + "."):
            out.append(("REVIEW", f"AP-001 {f}: standard approval process on {QUOTE} sees line values only through a quote field — confirm one carries the aggregate, or use Advanced Approvals"))
    obj_dirs = [p for p in root.rglob("objects") if p.is_dir()]
    names = {c.name for d in obj_dirs for c in d.iterdir() if c.is_dir()}
    if any(n.startswith("SBQQ__") for n in names) and not any(n.startswith("SBAA__") for n in names):
        out.append(("REVIEW", "AP-002 SBQQ__ objects present but no SBAA__ object metadata — confirm Advanced Approvals is installed and retrieved"))
    for f in files(root, ".flow-meta.xml"):
        text = f.read_text(encoding="utf-8", errors="replace")
        if SUBMIT_ACTION.search(text) and QUOTE in text and "SBAA__" not in text:
            out.append(("REVIEW", f"AP-003 {f}: submits {QUOTE} through a standard approval submit action"))
        ids = sorted(set(USER_ID.findall(text)))
        if ids:
            out.append(("WARN", f"AP-005 {f}: hard-coded user ID(s) {', '.join(ids[:3])} — use an approver field instead"))
    for f in files(root, ".permissionset-meta.xml"):
        text = f.read_text(encoding="utf-8", errors="replace")
        if "SBQQ__" in text and "SBAA__" not in text:
            out.append(("REVIEW", f"AP-004 {f}: grants SBQQ__ access with no SBAA__ access — confirm the Advanced Approvals permission set is assigned separately"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest-dir", default=".", help="Root of the metadata, e.g. force-app/main/default.")
    ap.add_argument("--strict", action="store_true", help="Exit 1 on WARN/REVIEW findings too.")
    args = ap.parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest dir not found: {root}")
        sys.exit(1)
    if not any(root.rglob("*")):
        print(f"WARN: {root} is empty — nothing to check")
        return 0
    findings = scan(root)
    for sev, msg in findings:
        print(f"{sev}: {msg}")
    if not findings:
        print("OK: no CPQ approval workflow issues found")
    if any(s == "ERROR" for s, _ in findings):
        return 1
    return 1 if (args.strict and findings) else 0


if __name__ == "__main__":
    sys.exit(main())
