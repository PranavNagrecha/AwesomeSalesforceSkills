#!/usr/bin/env python3
"""Audit Apex REST resources for common contract and security issues."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REST_RE = re.compile(r"@RestResource", re.IGNORECASE)
METHOD_RE = re.compile(r"@Http(Get|Post|Patch|Put|Delete)", re.IGNORECASE)
SHARING_RE = re.compile(r"\b(with|without|inherited)\s+sharing\b", re.IGNORECASE)
STATUS_RE = re.compile(r"statusCode\s*=", re.IGNORECASE)
RESTCONTEXT_RE = re.compile(r"RestContext\.(request|response)", re.IGNORECASE)
API_VERSION_RE = re.compile(r"<apiVersion>\s*([0-9.]+)\s*</apiVersion>")
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

# A class with no sharing keyword runs `with sharing` from API 67.0 (Summer '26);
# below that it runs without sharing. See agents/_shared/AGENT_CONTRACT.md,
# "Apex security idiom by API version".
DEFAULT_WITH_SHARING_IN = 67.0


def class_api_version(path: Path) -> float | None:
    """apiVersion from the sibling `<Class>.cls-meta.xml`, or None.

    The missing sharing keyword is undecidable from the .cls alone — the class's
    own version pin decides it, not the org's release — but the meta XML sits
    right next to it, so it is decidable here.
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Apex REST resource classes for weak contract patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan for Apex classes.")
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
    return sorted(path for path in root.rglob("*.cls") if path.is_file())


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not REST_RE.search(text):
        return findings

    if not METHOD_RE.search(text):
        findings.append(f"HIGH {path}: `@RestResource` class has no HTTP method annotations")
    if not SHARING_RE.search(text):
        api = class_api_version(path)
        if api is not None and api >= DEFAULT_WITH_SHARING_IN:
            findings.append(
                f"LOW {path}: Apex REST class has no explicit sharing declaration; at apiVersion "
                f"{api:.1f} it runs `with sharing`, so declare it rather than leave the posture to the version pin"
            )
        elif api is None:
            findings.append(
                f"HIGH {path}: Apex REST class has no explicit sharing declaration and has no sibling "
                f".cls-meta.xml to read; graded as pre-{DEFAULT_WITH_SHARING_IN:.1f} (runs without sharing)"
            )
        else:
            findings.append(
                f"HIGH {path}: Apex REST class has no explicit sharing declaration; at apiVersion "
                f"{api:.1f} it runs without sharing and exposes records the caller cannot otherwise see"
            )
    if not STATUS_RE.search(text):
        findings.append(f"REVIEW {path}: REST resource has no explicit response status-code handling")
    if "requestBody" in text and "JSON.deserialize" not in text and "JSON.deserializeUntyped" not in text:
        findings.append(f"MEDIUM {path}: request body access found without obvious JSON parsing")
    if not RESTCONTEXT_RE.search(text):
        findings.append(f"REVIEW {path}: REST resource does not reference `RestContext`; verify response handling is explicit")

    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 Apex classes; manifest directory was missing.")
    files = iter_files(root)
    if not files:
        return emit_result([f"HIGH {root}: no Apex classes found"], "Scanned 0 Apex classes; no .cls files were found.")
    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))
    summary = f"Scanned {len(files)} Apex class file(s); {len(findings)} Apex-REST finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
