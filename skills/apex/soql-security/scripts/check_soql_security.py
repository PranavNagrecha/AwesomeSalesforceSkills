#!/usr/bin/env python3
"""Scan Apex files for SOQL injection and CRUD/FLS risk patterns.

Stdlib only. Pass class or trigger files, or folders that contain them. The
severity of version-gated findings comes from the sibling -meta.xml apiVersion.

Corrections (2026-10-03), grounded on the Apex Developer Guide v67.0:
  * AccessLevel.USER_MODE (Database.query, Database.queryWithBinds, DML methods)
    and `as user` DML are user-mode idioms. The check used to recognize only the
    WITH USER_MODE clause, so a 66.0 class using AccessLevel.USER_MODE got a
    false "no CRUD/FLS enforcement" finding.
  * Concatenation is now also detected in Database.queryWithBinds,
    Database.countQuery, and Database.getQueryLocator calls, the other dynamic
    entry points listed under "Set an Access Mode for Database Operations".
  * Triggers saved at 67.0+ run their SOQL and DML in user mode unless system
    mode is stated. The guide recommends an explicit access mode on every
    database operation in triggers, so an unqualified trigger query is LOW.

A dynamic ORDER BY line that carries an `allowlist` comment is treated as
acknowledged and not reported.

Usage:
    python3 check_soql_security.py force-app/main/default/classes
    python3 check_soql_security.py --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".cls", ".trigger"}
DATABASE_QUERY_RE = re.compile(
    r"Database\.(query|queryWithBinds|countQuery|countQueryWithBinds|getQueryLocator|getQueryLocatorWithBinds)\s*\(",
    re.IGNORECASE,
)
STRING_CONCAT_RE = re.compile(r"\+\s*\w+|\w+\s*\+")
WITHOUT_SHARING_RE = re.compile(r"\bwithout\s+sharing\b", re.IGNORECASE)
AURA_OR_REST_RE = re.compile(r"@AuraEnabled|@RestResource|global\s+static|public\s+static", re.IGNORECASE)
USER_MODE_RE = re.compile(r"WITH\s+USER_MODE|AccessLevel\.USER_MODE|\b(insert|update|upsert|delete|undelete|merge)\s+as\s+user\b", re.IGNORECASE)
EXPLICIT_MODE_RE = re.compile(r"(WITH\s+|AccessLevel\.)(USER|SYSTEM)_MODE|\bas\s+(user|system)\b", re.IGNORECASE)
DB_OP_RE = re.compile(r"\[\s*SELECT\b|\bDatabase\.|\b(insert|update|upsert|delete|undelete|merge)\s+\w", re.IGNORECASE)
ALLOWLIST_NOTE_RE = re.compile(r"//.*allow-?list", re.IGNORECASE)
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
                f"and later the Apex Developer Guide says the clause can't be used in Apex SOQL "
                f"(expect a compile failure); below that it is legacy. Determine the version, "
                f"then migrate to WITH USER_MODE"
            )
        elif api_version >= SECURITY_ENFORCED_REMOVED_IN:
            findings.append(
                f"CRITICAL {path}: uses WITH SECURITY_ENFORCED at apiVersion {api_version:g}. "
                f"From {SECURITY_ENFORCED_REMOVED_IN:g} the clause can't be used in Apex SOQL "
                f"(Apex Developer Guide, Versioned Behavior Changes); expect a compile failure. "
                f"Replace it with WITH USER_MODE"
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

    if (path.suffix.lower() == ".trigger" and api_version is not None
            and api_version >= SECURITY_ENFORCED_REMOVED_IN
            and DB_OP_RE.search(text) and not EXPLICIT_MODE_RE.search(text)):
        findings.append(
            f"LOW {path}: trigger saved at apiVersion {api_version:g} has database operations with no explicit "
            f"access mode. At 67.0+ they run in user mode (sharing applies in the trigger body); the Apex "
            f"Developer Guide recommends stating WITH USER_MODE or WITH SYSTEM_MODE on every operation"
        )

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if DATABASE_QUERY_RE.search(line) and STRING_CONCAT_RE.search(line):
            findings.append(f"CRITICAL {path}:{line_number}: dynamic SOQL call appears to use string concatenation")
        if ("ORDER BY" in line.upper() and STRING_CONCAT_RE.search(line)
                and not ALLOWLIST_NOTE_RE.search(raw_line)):
            findings.append(f"HIGH {path}:{line_number}: dynamic ORDER BY detected; confirm allowlist protection")

    return findings


def self_test() -> int:
    here = Path(__file__).resolve().parent / "fixtures"
    good = [f for p in iter_files([str(here / "good")]) for f in audit_file(p)]
    bad_files = iter_files([str(here / "bad")])
    bad = [f for p in bad_files for f in audit_file(p)]
    expected = {
        "InjectableSearch.cls": ["CRITICAL", "HIGH"],
        "RemovedClause.cls": ["CRITICAL"],
        "AccountContactSync.trigger": ["LOW"],
        "UnenforcedController.cls": ["MEDIUM"],
    }
    missing = []
    for name, sevs in expected.items():
        hits = [f for f in bad if f"{name}" in f]
        for sev in sevs:
            if not any(h.startswith(sev + " ") for h in hits):
                missing.append(f"{name}: expected a {sev} finding")
    print(f"good fixtures: {len(good)} finding(s) (expected 0)")
    for f in good:
        print(f"  unexpected: {f}")
    print(f"bad fixtures: {len(bad)} finding(s); missing: {missing or 'none'}")
    return 0 if not good and not missing else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Apex files for dynamic SOQL and CRUD/FLS risk patterns."
    )
    parser.add_argument("paths", nargs="*", help="Files or directories to inspect")
    parser.add_argument("--self-test", action="store_true", help="Run the bundled fixtures and exit.")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.paths:
        parser.error("pass at least one file or directory, or --self-test")

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
