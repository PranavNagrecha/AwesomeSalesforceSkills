#!/usr/bin/env python3
"""Audit Apex SOSL for silent search-result-limit risks.

Flags the result-limiting behaviors documented in "SOSL Limits on Search Results":

  * Single-object SOSL whose RETURNING object has no WHERE/ORDER BY/LIMIT — capped at
    250 records, not the 2,000 most developers assume.
  * Multi-object SOSL with 9+ objects — each object is capped at min(2000/n, 250),
    which drops below 250 once n > 8.
  * Dynamic Search.query(...) calls — the SearchQuery string silently drops logical
    operators over 4,000 chars and returns zero rows over 10,000 chars, so callers
    should length-bound the string before the call.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_sosl_search_result_limits.py [--help]
    python3 check_sosl_search_result_limits.py --manifest-dir path/to/apex
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# A static SOSL statement: [ ... FIND ... ]. RETURNING field lists use parentheses,
# not square brackets, so excluding [ and ] safely bounds one statement.
SOSL_STATEMENT_RE = re.compile(r"\[\s*FIND\b[^\[\]]*\]", re.IGNORECASE | re.DOTALL)
RETURNING_RE = re.compile(r"\bRETURNING\b", re.IGNORECASE)
# One RETURNING object clause: Name( ...fields... ). Inner text has no nested parens.
OBJECT_CLAUSE_RE = re.compile(r"([A-Za-z_]\w*)\s*\(([^()]*)\)")
CAP_RAISER_RE = re.compile(r"\bWHERE\b|\bORDER\s+BY\b|\bLIMIT\b", re.IGNORECASE)
DYNAMIC_SOSL_RE = re.compile(r"Search\.query\s*\(", re.IGNORECASE)

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex files for SOSL search-result-limit risks.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for Apex classes (default: current directory).",
    )
    return parser.parse_args()


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def audit_static_sosl(path: Path, text: str) -> list[str]:
    findings: list[str] = []
    for stmt in SOSL_STATEMENT_RE.finditer(text):
        body = stmt.group(0)
        line = line_of(text, stmt.start())
        ret = RETURNING_RE.search(body)
        if not ret:
            # A FIND with no RETURNING returns Ids grouped by object; the caps still
            # apply but there is no clause to tune, so nothing actionable to flag here.
            continue
        clauses = OBJECT_CLAUSE_RE.findall(body[ret.end():])
        n = len(clauses)
        if n == 0:
            continue
        if n == 1:
            _, inner = clauses[0]
            if not CAP_RAISER_RE.search(inner):
                findings.append(
                    f"MEDIUM {path}:{line}: single-object SOSL with no WHERE/ORDER BY/LIMIT "
                    f"inside RETURNING is capped at 250 records; add a WHERE or ORDER BY to "
                    f"raise the cap to 2,000"
                )
        elif n >= 9:
            per_object = 2000 // n
            objects = ", ".join(name for name, _ in clauses)
            findings.append(
                f"MEDIUM {path}:{line}: SOSL RETURNING {n} objects ({objects}); each object "
                f"is capped at min(2000/{n}, 250) = {per_object} records — below 250; reduce "
                f"the object count or split into per-object searches"
            )
    return findings


def audit_dynamic_sosl(path: Path, text: str) -> list[str]:
    findings: list[str] = []
    for call in DYNAMIC_SOSL_RE.finditer(text):
        line = line_of(text, call.start())
        findings.append(
            f"REVIEW {path}:{line}: dynamic Search.query() — length-bound the SearchQuery "
            f"string (>4,000 chars silently removes logical operators; >10,000 chars returns "
            f"zero rows; statement limit is 100,000 chars by default)"
        )
    return findings


def audit_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    findings: list[str] = []
    findings.extend(audit_static_sosl(path, text))
    findings.extend(audit_dynamic_sosl(path, text))
    return findings


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location, sep, message = remainder.partition(": ")
    if not sep:
        location, message = "", remainder
    return {"severity": severity or "INFO", "location": location, "message": message}


def iter_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.cls") if path.is_file())


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(item) for item in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(f["severity"], 0) for f in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result(
            [f"HIGH {root}: manifest directory not found"],
            "Scanned 0 Apex files; manifest directory was missing.",
        )
    files = iter_files(root)
    if not files:
        return emit_result(
            [f"HIGH {root}: no Apex files found"],
            "Scanned 0 Apex files; no .cls files were found.",
        )
    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))
    summary = f"Scanned {len(files)} Apex file(s); {len(findings)} SOSL limit finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
