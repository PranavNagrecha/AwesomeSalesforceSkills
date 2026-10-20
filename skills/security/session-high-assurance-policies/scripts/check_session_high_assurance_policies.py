#!/usr/bin/env python3
"""Checker for session-high-assurance-policies (stdlib only).

Reads ProfileSessionSetting files (*.profileSessionSetting, and -meta.xml
variants; api_meta 264 L101448-101530) and Apex classes under --manifest-dir:

  ERROR  a ProfileSessionSetting that does not parse, misses the Required
         <profile> or <sessionTimeout> (api_meta 264 L101469, L101478), or has a
         requiredSessionLevel outside HIGH_ASSURANCE / STANDARD / LOW
         (L101502-101520)
  INFO   requiredSessionLevel HIGH_ASSURANCE (valid; the guide's own sample) — every login for that profile must
         reach High Assurance; exclude integration users and async-job owners
  WARN   requiredSessionLevel LOW — "unpredictable and reduced functionality"
         (L101518-101520)
  WARN   an Apex gate written as "not STANDARD", which passes a LOW session
         (Auth.SessionLevel LOW: apexref 262 L11901-11906)
  WARN   a UserInfo.getSession* call other than getSessionId() (apexref 262 L243284)

Exit 1 on any ERROR, or on WARN with --strict; otherwise 0. A missing
--manifest-dir is an ERROR; a tree with nothing to check is one WARN, exit 0.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"
LEVELS = {"HIGH_ASSURANCE", "STANDARD", "LOW"}
NOT_STANDARD = re.compile(r"!\s*'STANDARD'\s*\.\s*equalsIgnoreCase\s*\(", re.IGNORECASE)
FAKE_USERINFO = re.compile(r"UserInfo\s*\.\s*getSession(?!Id\b)\w*\s*\(")


def text(el: ET.Element, tag: str) -> str:
    found = el.find(NS + tag)
    if found is None:
        found = el.find(tag)
    return (found.text or "").strip() if found is not None else ""


def run(settings: list[Path], classes: list[Path]) -> list:
    out: list = []
    for path in settings:
        try:
            el = ET.parse(path).getroot()
        except ET.ParseError as exc:
            out.append(("ERROR", f"{path}: XML does not parse ({exc})"))
            continue
        for req in ("profile", "sessionTimeout"):
            if not text(el, req):
                out.append(("ERROR", f"{path}: missing Required <{req}> (api_meta 264 L101469-101478)"))
        level = text(el, "requiredSessionLevel")
        if level and level not in LEVELS:
            out.append(("ERROR", f"{path}: requiredSessionLevel '{level}' is not HIGH_ASSURANCE, STANDARD or LOW"))
        elif level == "HIGH_ASSURANCE":
            out.append(("INFO", f"{path}: profile '{text(el, 'profile')}' requires High Assurance at login — exclude integration users and async-job owners (gotchas.md 1 and 5)"))
        elif level == "LOW":
            out.append(("WARN", f"{path}: LOW session level gives unpredictable and reduced functionality (api_meta 264 L101518-101520)"))
    for path in classes:
        body = path.read_text(encoding="utf-8", errors="replace")
        for n, line in enumerate(body.splitlines(), 1):
            if NOT_STANDARD.search(line):
                out.append(("WARN", f"{path}:{n}: session gate written as 'not STANDARD' passes a LOW session — compare to 'HIGH_ASSURANCE' instead"))
            if FAKE_USERINFO.search(line):
                out.append(("WARN", f"{path}:{n}: UserInfo has no session-level accessor; use Auth.SessionManagement.getCurrentSession()"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Check ProfileSessionSetting metadata and Apex step-up gates.")
    ap.add_argument("--manifest-dir", default=".", help="Root of the source-format metadata tree.")
    ap.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings as well as ERROR.")
    args = ap.parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    settings = sorted(set(root.rglob("*.profileSessionSetting")) | set(root.rglob("*.profileSessionSetting-meta.xml")))
    classes = sorted(root.rglob("*.cls"))
    if not settings and not classes:
        print(f"WARN: no ProfileSessionSetting or Apex class files under {root}; nothing to check")
        return 0
    findings = run(settings, classes)
    for sev, msg in findings:
        print(f"{sev}: {msg}")
    errors = sum(1 for s, _ in findings if s == "ERROR")
    warns = sum(1 for s, _ in findings if s == "WARN")
    print(f"Summary: {errors} error(s), {warns} warning(s)")
    if errors or (args.strict and warns):
        sys.exit(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
