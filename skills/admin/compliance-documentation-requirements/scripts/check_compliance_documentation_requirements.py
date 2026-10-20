#!/usr/bin/env python3
"""Checker script for Compliance Documentation Requirements skill.

Scans retrieved Salesforce metadata for compliance-documentation anti-patterns:

- ERROR: a NamedCredential / ExternalCredential / object / field file that does not parse
- REVIEW: a per-user credential — legacy NamedCredential principalType PerUser, or an
  ExternalCredential parameter of type PerUserPrincipal (api_meta 264 L66350, L92943).
  NamedUser is Named Principal (L92832) and is never flagged. Whether per-user
  credentials fail in batch or scheduled runs is UNVERIFIED (2026-10-20).
- WARN: a credential-looking literal in a NamedCredential file, or an AML vendor host
  or API key literal in Apex (use named credentials for secrets, apexdev 264 L13709-13713)
- WARN: a corpus-confirmed KYC picklist field declared without trackHistory=true
  (PartyProfileRisk.RiskCategory, PartyIdentityVerification.Status,
  PartyScreeningSummary.Status — api_meta 264 L146588, L146637, L146690).
  Fields not present in the retrieved metadata are not judged.

Stdlib only. Exit 1 on ERROR; WARN/REVIEW exit 0 unless --strict; empty dir one WARN;
missing dir ERROR exit 1.

Usage:
    python3 check_compliance_documentation_requirements.py --manifest-dir path/to/metadata [--strict]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

KYC_TRACKED = {
    "PartyProfileRisk": {"RiskCategory"},
    "PartyIdentityVerification": {"Status"},
    "PartyScreeningSummary": {"Status"},
}
CREDENTIAL_PATTERNS = ["apikey=", "api_key=", "token=", "secret=", "password=", "authorization: basic"]
VENDOR_STRINGS = ["onfido.com", "refinitiv.com", "lexisnexis.com", "worldcheck", "complyadvantage.com",
                  "apikey", "api_key", "authorization: token"]


def local(tag: str) -> str:
    return tag.split("}", 1)[-1]


def child(el: ET.Element, name: str) -> ET.Element | None:
    for c in el:
        if local(c.tag) == name:
            return c
    return None


def text_of(el: ET.Element, name: str) -> str:
    c = child(el, name)
    return (c.text or "").strip() if c is not None else ""


def files(root: Path, *patterns: str) -> list[Path]:
    out: list[Path] = []
    for pat in patterns:
        out += [p for p in root.rglob(pat) if p.is_file()]
    return out


def parse(path: Path, out: list) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        out.append(("ERROR", f"{path}: does not parse: {exc}"))
        return None


def scan(root: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for f in files(root, "*.namedCredential", "*.namedCredential-meta.xml"):
        r = parse(f, out)
        if r is None:
            continue
        if text_of(r, "principalType") == "PerUser":
            out.append(("REVIEW", f"{f}: legacy principalType PerUser — confirm no batch/scheduled caller (headless failure UNVERIFIED)"))
        body = f.read_text(encoding="utf-8", errors="ignore").lower()
        hit = next((p for p in CREDENTIAL_PATTERNS if p in body), None)
        if hit:
            out.append(("WARN", f"{f}: possible hard-coded credential ('{hit}') — keep secrets in the External Credential"))
    for f in files(root, "*.externalCredential", "*.externalCredential-meta.xml"):
        r = parse(f, out)
        if r is None:
            continue
        for el in r.iter():
            if local(el.tag) == "externalCredentialParameters" and text_of(el, "parameterType") == "PerUserPrincipal":
                out.append(("REVIEW", f"{f}: PerUserPrincipal parameter '{text_of(el, 'parameterName')}' — confirm no batch/scheduled caller"))
    for f in files(root, "*.cls"):
        low = f.read_text(encoding="utf-8", errors="ignore").lower()
        hit = next((p for p in VENDOR_STRINGS if p in low), None)
        if hit:
            out.append(("WARN", f"{f}: possible hard-coded AML vendor endpoint or key ('{hit}') — use a named credential"))
    # Field history on corpus-confirmed KYC picklists: object files (<fields>) and source-format field files.
    declared: list[tuple[str, str, bool, Path]] = []
    for f in files(root, "*.object", "*.object-meta.xml"):
        obj = f.name.split(".")[0]
        if obj not in KYC_TRACKED:
            continue
        r = parse(f, out)
        if r is None:
            continue
        for fl in r:
            if local(fl.tag) == "fields":
                declared.append((obj, text_of(fl, "fullName"), text_of(fl, "trackHistory") == "true", f))
    for f in files(root, "*.field-meta.xml"):
        obj = f.parent.parent.name
        if obj not in KYC_TRACKED:
            continue
        r = parse(f, out)
        if r is None:
            continue
        declared.append((obj, text_of(r, "fullName") or f.name.split(".")[0], text_of(r, "trackHistory") == "true", f))
    for obj, field, tracked, f in declared:
        if field in KYC_TRACKED[obj] and not tracked:
            out.append(("WARN", f"{f}: {obj}.{field} has no trackHistory=true — field history is the audit trail for this value"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest-dir", default=".", help="Root of the retrieved metadata.")
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
        print("OK: no compliance documentation issues found")
    if any(s == "ERROR" for s, _ in findings):
        return 1
    return 1 if (args.strict and findings) else 0


if __name__ == "__main__":
    sys.exit(main())
