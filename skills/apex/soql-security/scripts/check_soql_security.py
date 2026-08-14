#!/usr/bin/env python3
"""Scan Apex files for SOQL injection and CRUD/FLS risk patterns."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".cls", ".trigger"}
DATABASE_QUERY_RE = re.compile(r"Database\.query\s*\(", re.IGNORECASE)
STRING_CONCAT_RE = re.compile(r"\+\s*\w+|\w+\s*\+")
WITHOUT_SHARING_RE = re.compile(r"\bwithout\s+sharing\b", re.IGNORECASE)
AURA_OR_REST_RE = re.compile(r"@AuraEnabled|@RestResource|global\s+static|public\s+static", re.IGNORECASE)
USER_MODE_RE = re.compile(r"WITH\s+USER_MODE", re.IGNORECASE)
SECURITY_ENFORCED_RE = re.compile(r"WITH\s+SECURITY_ENFORCED", re.IGNORECASE)
STRIP_RE = re.compile(r"stripInaccessible\s*\(", re.IGNORECASE)
API_VERSION_RE = re.compile(r"<apiVersion>\s*([0-9.]+)\s*</apiVersion>")
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

# Salesforce removed the WITH SECURITY_ENFORCED clause in API 67.0 (Summer '26).
# See agents/_shared/AGENT_CONTRACT.md, "Apex security idiom by API version".
SECURITY_ENFORCED_REMOVED_IN = 67.0
USER_MODE_GA_IN = 57.0


def class_api_version(path: Path) -> float | None:
    """apiVersion from the sibling `<Class>.cls-meta.xml`, or None.

    The controlling fact for every Apex security idiom is the version the CLASS
    is pinned to, not the org's release: a Summer '26 org runs a class pinned to
    58.0 quite happily, and that class still compiles the old clause. So the
    severity of a `WITH SECURITY_ENFORCED` hit is undecidable from the .cls
    alone — but the meta XML sits right next to it, so it is decidable here.
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


def iter_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(candidate for candidate in path.rglob("*") if candidate.is_file())
    return sorted(set(files))


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


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return findings

    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    if WITHOUT_SHARING_RE.search(text):
        findings.append(f"HIGH {path}: class uses without sharing; verify and document intentional system context")

    # `WITH SECURITY_ENFORCED` is a FINDING, never a pass. Treating its presence
    # as evidence of a secure query is the polarity bug this check used to have:
    # it silenced the enforcement warning for a clause that, from API 67.0, does
    # not compile at all. Severity is decided by the class's pinned apiVersion.
    api_version = class_api_version(path)
    if SECURITY_ENFORCED_RE.search(text):
        if api_version is None:
            findings.append(
                f"MEDIUM {path}: uses WITH SECURITY_ENFORCED and no sibling .cls-meta.xml "
                f"was found, so the apiVersion is unknown. At {SECURITY_ENFORCED_REMOVED_IN} "
                f"and later this does not compile "
                f"(\"WITH SECURITY_ENFORCED is no longer supported, use WITH USER_MODE instead\"); "
                f"below that it is legacy. Determine the version, then migrate to WITH USER_MODE"
            )
        elif api_version >= SECURITY_ENFORCED_REMOVED_IN:
            findings.append(
                f"CRITICAL {path}: uses WITH SECURITY_ENFORCED at apiVersion {api_version:g}. "
                f"The clause was removed in {SECURITY_ENFORCED_REMOVED_IN:g} and this class will "
                f"not compile: \"WITH SECURITY_ENFORCED is no longer supported, use WITH USER_MODE "
                f"instead\". This is a build failure, not a style note"
            )
        else:
            findings.append(
                f"LOW {path}: uses WITH SECURITY_ENFORCED at apiVersion {api_version:g}. It still "
                f"compiles below {SECURITY_ENFORCED_REMOVED_IN:g}, but it is the weaker construct — "
                f"it checks only the SELECT list, mishandles polymorphic fields, and reports one "
                f"violation rather than all. Migrate to WITH USER_MODE (GA at "
                f"{USER_MODE_GA_IN:g}) before raising the apiVersion"
            )

    # Below 67.0, WITH SECURITY_ENFORCED is legacy but it DOES enforce FLS, so a
    # class carrying it has already been reported above and must not also be
    # told it has no enforcement at all. At 67.0+ the clause does not compile,
    # so it counts for nothing — but there user mode is the default anyway.
    enforces_below_67 = (
        USER_MODE_RE.search(text)
        or STRIP_RE.search(text)
        or (SECURITY_ENFORCED_RE.search(text)
            and (api_version is None or api_version < SECURITY_ENFORCED_REMOVED_IN))
    )
    if AURA_OR_REST_RE.search(text) and not enforces_below_67:
        # At 67.0+ user mode is the default, so an unqualified query is already
        # enforced and the absence of a keyword is not itself a defect.
        if api_version is None or api_version < SECURITY_ENFORCED_REMOVED_IN:
            findings.append(f"MEDIUM {path}: public or API-facing Apex found without obvious CRUD/FLS enforcement pattern")

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if DATABASE_QUERY_RE.search(line) and STRING_CONCAT_RE.search(line):
            findings.append(f"CRITICAL {path}:{line_number}: Database.query appears to use string concatenation")
        if "ORDER BY" in line.upper() and STRING_CONCAT_RE.search(line):
            findings.append(f"HIGH {path}:{line_number}: dynamic ORDER BY detected; confirm allowlist protection")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Apex files for dynamic SOQL and CRUD/FLS risk patterns."
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to inspect")
    args = parser.parse_args()

    files = iter_files(args.paths)
    if not files:
        return emit_result(
            ["HIGH no Apex files matched the provided paths"],
            "Scanned 0 Apex files; no matching .cls or .trigger files were found.",
        )

    findings: list[str] = []
    scanned = 0
    for path in files:
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        scanned += 1
        findings.extend(audit_file(path))

    if scanned == 0:
        findings.append("HIGH no Apex files matched the provided paths")
    summary = f"Scanned {scanned} Apex file(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
