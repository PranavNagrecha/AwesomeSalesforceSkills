#!/usr/bin/env python3
"""Audit Apex files for sharing-model and CRUD/FLS enforcement risks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".cls", ".trigger"}
CLASS_RE = re.compile(r"\b(public|global)\s+(virtual\s+|abstract\s+)?(with|without|inherited)?\s*sharing?\s*class\b", re.IGNORECASE)
PUBLIC_CLASS_RE = re.compile(r"\b(public|global)\s+(virtual\s+|abstract\s+)?class\b", re.IGNORECASE)
WITHOUT_SHARING_RE = re.compile(r"\bwithout\s+sharing\b", re.IGNORECASE)
WITH_OR_INHERITED_RE = re.compile(r"\b(with|inherited)\s+sharing\b", re.IGNORECASE)
ENTRY_POINT_RE = re.compile(r"@AuraEnabled|@InvocableMethod|@RestResource", re.IGNORECASE)
# `WITH SECURITY_ENFORCED` is deliberately NOT read enforcement: it is the weaker
# clause below API 67.0 and does not compile at 67.0 and later. See SECURITY_ENFORCED_RE.
READ_ENFORCEMENT_RE = re.compile(
    r"WITH\s+USER_MODE|AccessLevel\.USER_MODE|isAccessible\s*\(", re.IGNORECASE
)
WRITE_ENFORCEMENT_RE = re.compile(
    r"stripInaccessible\s*\(|AccessLevel\.USER_MODE|\bas\s+user\b|isCreateable\s*\(|isUpdateable\s*\(",
    re.IGNORECASE,
)
SECURITY_ENFORCED_RE = re.compile(r"WITH\s+SECURITY_ENFORCED", re.IGNORECASE)
SYSTEM_MODE_RE = re.compile(r"WITH\s+SYSTEM_MODE|AccessLevel\.SYSTEM_MODE|\bas\s+system\b", re.IGNORECASE)
API_VERSION_RE = re.compile(r"<apiVersion>\s*([0-9]+(?:\.[0-9]+)?)\s*</apiVersion>")
# API 67.0 (Summer '26) flipped the default access mode for SOQL/SOSL/DML/Database
# methods from system mode to user mode, and removed WITH SECURITY_ENFORCED.
USER_MODE_DEFAULT_API = 67.0
DML_RE = re.compile(r"\b(insert|update|upsert|delete|undelete|merge)\b", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex files for ambiguous sharing declarations and missing CRUD/FLS protections."
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for Apex classes and triggers.",
    )
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


def iter_apex_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
    )


def read_api_version(path: Path) -> float | None:
    """Return the apiVersion from the sibling .cls-meta.xml / .trigger-meta.xml, if present.

    The default access mode is gated on this value, not on the org's release: a
    Summer '26 org runs a class pinned to 58.0 with the old system-mode default.
    """
    meta = path.with_name(path.name + "-meta.xml")
    if not meta.is_file():
        return None
    match = API_VERSION_RE.search(meta.read_text(encoding="utf-8", errors="ignore"))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    api_version = read_api_version(path)
    version_label = f"apiVersion {api_version:.1f}" if api_version is not None else "apiVersion unknown"

    if SECURITY_ENFORCED_RE.search(text):
        if api_version is not None and api_version >= USER_MODE_DEFAULT_API:
            findings.append(
                f"CRITICAL {path}: `WITH SECURITY_ENFORCED` at {version_label}; "
                "the clause was removed in API 67.0 and no longer compiles — use `WITH USER_MODE`"
            )
        else:
            findings.append(
                f"MEDIUM {path}: `WITH SECURITY_ENFORCED` found ({version_label}); it checks only the "
                "SELECT list and stops compiling at API 67.0 — migrate to `WITH USER_MODE`"
            )

    # NOTE: do not flag a trigger for carrying `WITH USER_MODE` / `WITH SYSTEM_MODE`.
    # A trigger cannot declare a *sharing* keyword, but operations inside the body do
    # take an explicit access mode, and the Apex Developer Guide documents that exact
    # pattern. Flagging it would penalise correct code.
    if path.suffix.lower() == ".trigger" and SYSTEM_MODE_RE.search(text):
        findings.append(
            f"REVIEW {path}: trigger-body operation opts out to system mode; confirm the elevation is "
            "intended and carries a `// reason:` comment (record visibility is already unrestricted here)"
        )

    if path.suffix.lower() == ".cls" and PUBLIC_CLASS_RE.search(text) and not (
        WITH_OR_INHERITED_RE.search(text) or WITHOUT_SHARING_RE.search(text)
    ):
        # At API 67.0+ an undeclared class defaults to `with sharing`, so this is an
        # explicitness defect rather than an open door. Below 67.0 it is still a real risk.
        severity = "MEDIUM" if api_version is not None and api_version >= USER_MODE_DEFAULT_API else "HIGH"
        findings.append(
            f"{severity} {path}: public/global Apex class has no explicit sharing declaration ({version_label})"
        )

    if SYSTEM_MODE_RE.search(text) and ENTRY_POINT_RE.search(text):
        findings.append(
            f"HIGH {path}: user-facing entry point opts out to system mode; justify the elevation with a "
            "`// reason:` comment or drop it"
        )

    if WITHOUT_SHARING_RE.search(text):
        findings.append(f"HIGH {path}: `without sharing` found; verify and document intentional privilege elevation")

    if ENTRY_POINT_RE.search(text) and not (WITH_OR_INHERITED_RE.search(text) or WITHOUT_SHARING_RE.search(text)):
        findings.append(f"HIGH {path}: user-facing entry point has no explicit sharing declaration")

    if ENTRY_POINT_RE.search(text) and not READ_ENFORCEMENT_RE.search(text):
        findings.append(f"HIGH {path}: user-facing entry point lacks obvious read-access enforcement (`WITH USER_MODE`, `AccessLevel.USER_MODE`, or describe checks)")

    if ENTRY_POINT_RE.search(text) and DML_RE.search(text) and not WRITE_ENFORCEMENT_RE.search(text):
        findings.append(f"HIGH {path}: user-facing entry point performs DML without obvious write-access enforcement")

    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 Apex files; manifest directory was missing.")

    files = iter_apex_files(root)
    if not files:
        return emit_result([f"HIGH {root}: no Apex files found"], "Scanned 0 Apex files; no .cls or .trigger files were found.")

    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))

    summary = f"Scanned {len(files)} Apex file(s); {len(findings)} security-pattern finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
