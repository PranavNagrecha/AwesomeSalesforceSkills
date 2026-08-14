#!/usr/bin/env python3
"""Audit OmniStudio-related assets for common security smells."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


OMNI_RE = re.compile(r"omnistudio|omniscript|dataraptor|integration procedure|flexcard", re.IGNORECASE)
HTTP_URL_RE = re.compile(r"https?://", re.IGNORECASE)
NAMED_CRED_RE = re.compile(r"namedCredential|Named Credential", re.IGNORECASE)
TOKEN_RE = re.compile(r"bearer\s+[A-Za-z0-9._-]+|api[_-]?key|client[_-]?secret", re.IGNORECASE)
AURA_ENABLED_RE = re.compile(r"@AuraEnabled", re.IGNORECASE)
WITHOUT_SHARING_RE = re.compile(r"\bwithout\s+sharing\b", re.IGNORECASE)
SECURITY_RE = re.compile(r"with\s+sharing|inherited\s+sharing|WITH\s+USER_MODE|stripInaccessible", re.IGNORECASE)
# WITH SECURITY_ENFORCED is deliberately NOT enforcement evidence: it was removed
# in API 67.0 and is the weaker construct below it. See agents/_shared/AGENT_CONTRACT.md,
# "Apex security idiom by API version" -- the gate is the class's own apiVersion,
# not the org's release.
SECURITY_ENFORCED_RE = re.compile(r"WITH\s+SECURITY_ENFORCED", re.IGNORECASE)
API_VERSION_RE = re.compile(r"<apiVersion>\s*([0-9]+(?:\.[0-9]+)?)\s*</apiVersion>")
PUBLIC_GUEST_RE = re.compile(r"guest|public", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check OmniStudio-adjacent assets for security and exposure issues.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan for OmniStudio, Apex, and LWC assets.")
    return parser.parse_args()


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(item) for item in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


def iter_files(root: Path) -> list[Path]:
    allowed = {".json", ".txt", ".xml", ".js", ".cls", ".yaml", ".yml"}
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in allowed)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def class_api_version(path: Path) -> float | None:
    """Return the apiVersion pinned in the class's sibling .cls-meta.xml, if readable."""
    meta = path.with_name(path.name + "-meta.xml")
    if not meta.is_file():
        return None
    match = API_VERSION_RE.search(read_text(meta))
    return float(match.group(1)) if match else None


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    text = read_text(path)

    if HTTP_URL_RE.search(text) and not NAMED_CRED_RE.search(text):
        findings.append(f"HIGH {path}: hardcoded HTTP URL found without an obvious Named Credential reference; review outbound security design")
    if TOKEN_RE.search(text):
        findings.append(f"CRITICAL {path}: possible hardcoded credential or token material found")
    if path.suffix.lower() == ".cls" and AURA_ENABLED_RE.search(text):
        api_version = class_api_version(path)
        # 67.0+ (Summer '26): SOQL/SOSL/DML default to user mode and a bare class runs
        # `with sharing`. Below that, both default the other way. When no .cls-meta.xml
        # is readable the scan falls back to the 66.0-and-below row and says so in the
        # finding, per AGENT_CONTRACT: state which row you assumed rather than imply
        # the pin was known.
        user_mode_default = api_version is not None and api_version >= 67.0
        unknown_pin = api_version is None
        pin = f"apiVersion {api_version:.1f}" if api_version is not None else "an unreadable apiVersion"
        if WITHOUT_SHARING_RE.search(text):
            findings.append(f"HIGH {path}: @AuraEnabled Apex uses without sharing; verify OmniStudio exposure is intentionally elevated")
        if SECURITY_ENFORCED_RE.search(text):
            if user_mode_default:
                findings.append(f"HIGH {path}: WITH SECURITY_ENFORCED at {pin}; removed in 67.0 and no longer compiles - use WITH USER_MODE")
            elif unknown_pin:
                findings.append(f"MEDIUM {path}: WITH SECURITY_ENFORCED, and no sibling .cls-meta.xml to read the apiVersion from; scored on the 66.0-and-below row, where it is legacy and is not evidence of a secure query - at 67.0+ it does not compile at all. Migrate to WITH USER_MODE and confirm the pin")
            else:
                findings.append(f"MEDIUM {path}: WITH SECURITY_ENFORCED at {pin} is legacy and is not evidence of a secure query; migrate to WITH USER_MODE")
        elif not SECURITY_RE.search(text):
            if user_mode_default:
                findings.append(f"REVIEW {path}: @AuraEnabled Apex at {pin} declares no access mode, so database operations default to user mode; confirm that is intended and that writes built from OmniScript input use Security.stripInaccessible")
            elif unknown_pin:
                findings.append(f"REVIEW {path}: @AuraEnabled Apex found without obvious sharing or CRUD/FLS enforcement markers, and no sibling .cls-meta.xml to read the apiVersion from; scored on the 66.0-and-below row, where that means system mode - confirm the pin, because at 67.0+ the default is user mode instead")
            else:
                findings.append(f"REVIEW {path}: @AuraEnabled Apex at {pin} found without obvious sharing or CRUD/FLS enforcement markers; below 67.0 that means system mode")
    if PUBLIC_GUEST_RE.search(text) and re.search(r"\b(create|update|delete|upsert)\b", text, re.IGNORECASE):
        findings.append(f"REVIEW {path}: guest/public markers appear near write-oriented behavior; confirm the external contract is intentionally narrow")

    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 files; manifest directory was missing.")

    files = iter_files(root)
    findings: list[str] = []
    omni_hits = 0
    for path in files:
        text = read_text(path)
        if OMNI_RE.search(path.name) or OMNI_RE.search(text):
            omni_hits += 1
            findings.extend(audit_file(path))

    if omni_hits == 0:
        return emit_result([f"HIGH {root}: no OmniStudio-related assets found"], "Scanned 0 OmniStudio-related files.")

    summary = f"Observed {omni_hits} OmniStudio-related file(s); {len(findings)} security finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
