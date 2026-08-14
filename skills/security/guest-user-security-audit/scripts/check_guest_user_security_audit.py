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
  5. `@RestResource` Apex class with NO sharing declaration, where
     the sibling `.cls-meta.xml` pins `apiVersion` <= 66.0 (or is
     missing). An omitted declaration is not `inherited sharing`:
     at API 67.0+ a bare class runs `with sharing`, but at <= 66.0
     only Aura controllers, `@AuraEnabled` methods called from an
     LWC, and classes with a 67.0+ ancestor resolve that way — a
     standalone bare `@RestResource` class falls through to
     `without sharing`. Scoped to `@RestResource` on purpose: a bare
     `@AuraEnabled` class resolves to `with sharing` at every
     version, so flagging it would be a false positive. Triggers are
     exempt too — they can't carry a sharing declaration at any
     version.

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

# An omitted sharing declaration is version-gated on the class's
# .cls-meta.xml apiVersion, not the org's release. Full resolution order:
# references/gotchas.md, gotcha 3.
_SHARING_FLIP_VERSION = 67.0

_SHARING_DECL_RE = re.compile(
    r"\b(?:with|without|inherited)\s+sharing\b", re.IGNORECASE
)
_OUTER_CLASS_DECL_RE = re.compile(
    r"^(?:global|public|private)\b[^\n{]*\bclass\s+\w+", re.IGNORECASE | re.MULTILINE
)
_API_VERSION_RE = re.compile(
    r"<apiVersion>\s*([0-9]+(?:\.[0-9]+)?)\s*</apiVersion>", re.IGNORECASE
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _api_version(cls_path: Path) -> float | None:
    """Read apiVersion from the sibling `<Name>.cls-meta.xml`, if present."""
    meta = cls_path.with_name(cls_path.name + "-meta.xml")
    try:
        m = _API_VERSION_RE.search(meta.read_text(encoding="utf-8", errors="ignore"))
    except OSError:
        return None
    return float(m.group(1)) if m else None


def _outer_class_declaration(text: str) -> str | None:
    """Return the outer (column-0) class declaration, ignoring inner classes."""
    m = _OUTER_CLASS_DECL_RE.search(text)
    return m.group(0) if m else None


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

    # Scoped to `.cls` + `@RestResource`: triggers can't carry a sharing
    # declaration at any API version, and a bare `@AuraEnabled` class resolves
    # to `with sharing` at every version. Flagging either would be a
    # guaranteed false positive.
    if path.suffix.lower() == ".cls" and has_restresource:
        decl = _outer_class_declaration(text)
        if decl and not _SHARING_DECL_RE.search(decl):
            version = _api_version(path)
            if version is None:
                findings.append(
                    f"{path}: `@RestResource` class with no sharing declaration "
                    "and no readable `.cls-meta.xml` — the mode is decided by an "
                    "apiVersion this scan can't see. Declare it explicitly "
                    "(gotchas.md § 3)."
                )
            elif version < _SHARING_FLIP_VERSION:
                findings.append(
                    f"{path}: `@RestResource` class with no sharing declaration "
                    f"pinned to apiVersion {version:g} — below "
                    f"{_SHARING_FLIP_VERSION:g} it is not an Aura/LWC entry point, "
                    "so unless a 67.0+ class sits in its inheritance chain it "
                    "runs `without sharing` and bypasses sharing on a public "
                    "endpoint. Declare `with sharing` (gotchas.md § 3)."
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
            "Apex with `without sharing`, guest-reachable classes whose "
            "omitted sharing declaration resolves to `without sharing` at the "
            "apiVersion their .cls-meta.xml pins, guest profile XML granting "
            "view-all / modify-all, and string-concatenated dynamic SOQL."
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
