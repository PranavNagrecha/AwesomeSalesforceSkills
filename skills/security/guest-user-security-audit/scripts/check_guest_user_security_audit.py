#!/usr/bin/env python3
"""Static checks for Experience Cloud guest-user exposure anti-patterns.

Anti-patterns detected:

  1. Apex class with `@AuraEnabled` annotation declared `without
     sharing` — guest-reachable + bypasses sharing.
  2. Apex class with `@RestResource(urlMapping=...)` annotation
     declared `without sharing` — same risk via REST.
  3. Profile XML granting `viewAllData` or `modifyAllData` to a
     Guest profile (file name containing `Guest` heuristic).
  4. Concatenated user input in `Database.query(...)` — SOQL
     injection vector when guest-reachable.

Stdlib only.

Usage:
    python3 check_guest_user_security_audit.py --src-root .
    python3 check_guest_user_security_audit.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_CLASS_HEADER_RE = re.compile(
    r"\b(public|global)\s+(without\s+sharing|with\s+sharing|inherited\s+sharing)?\s*class\s+(\w+)",
    re.IGNORECASE,
)
_AURAENABLED_RE = re.compile(r"@AuraEnabled\b", re.IGNORECASE)
_RESTRESOURCE_RE = re.compile(r"@RestResource\b", re.IGNORECASE)
_WITHOUT_SHARING_RE = re.compile(r"\bwithout\s+sharing\b", re.IGNORECASE)

_PROFILE_VIEW_ALL_RE = re.compile(
    r"<name>(viewAllData|modifyAllData|manageUsers)</name>\s*<enabled>true</enabled>",
    re.IGNORECASE | re.DOTALL,
)

_DYNAMIC_QUERY_CONCAT_RE = re.compile(
    r"Database\.query\s*\(\s*['\"][^'\"]*['\"]\s*\+\s*\w+",
    re.IGNORECASE,
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan_apex(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    has_auraenabled = bool(_AURAENABLED_RE.search(text))
    has_restresource = bool(_RESTRESOURCE_RE.search(text))
    is_without = bool(_WITHOUT_SHARING_RE.search(text))

    if has_auraenabled and is_without:
        findings.append(
            f"{path}: class with `@AuraEnabled` declared `without sharing` — "
            "guest-reachable from LWC / Aura and bypasses sharing. Default "
            "to `with sharing` for guest surfaces (llm-anti-patterns.md "
            "§ 1)."
        )
    if has_restresource and is_without:
        findings.append(
            f"{path}: class with `@RestResource` declared `without sharing` "
            "— public-site reachable and bypasses sharing (llm-anti-"
            "patterns.md § 2)."
        )

    for m in _DYNAMIC_QUERY_CONCAT_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: Database.query(...) with "
            "string concatenation — SOQL injection risk if reachable from "
            "guest. Use bind variables or escapeSingleQuotes "
            "(llm-anti-patterns.md § 6)."
        )

    return findings


def _scan_profile(path: Path) -> list[str]:
    findings: list[str] = []
    name = path.name.lower()
    is_guest = "guest" in name
    if not is_guest:
        return findings
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]
    for m in _PROFILE_VIEW_ALL_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: Guest profile grants "
            f"{m.group(1)}=true — secure-by-default removes these grants; "
            "remove from the guest profile (llm-anti-patterns.md § 4)."
        )
    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]
    findings: list[str] = []
    for apex in list(root.rglob("*.cls")) + list(root.rglob("*.trigger")):
        findings.extend(_scan_apex(apex))
    for prof in list(root.rglob("*.profile-meta.xml")) + list(
        root.rglob("*.permissionset-meta.xml")
    ):
        findings.extend(_scan_profile(prof))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Salesforce Apex and metadata for Experience Cloud "
            "guest-user exposure anti-patterns: @AuraEnabled / @RestResource "
            "Apex with `without sharing`, guest profile XML granting view-all "
            "/ modify-all, and string-concatenated dynamic SOQL."
        ),
    )
    parser.add_argument(
        "--src-root",
        default=".",
        help="Root of the Salesforce source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no guest-user exposure anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
