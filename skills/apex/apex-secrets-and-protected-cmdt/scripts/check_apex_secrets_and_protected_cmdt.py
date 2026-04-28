#!/usr/bin/env python3
"""Checker for Apex Secrets and Protected CMDT skill.

Scans a Salesforce DX project for secret-storage anti-patterns:

  P0 — Hardcoded secret literal in .cls
       Regex: (api_?key|secret|token|password)\\s*=\\s*'[A-Za-z0-9\\-_+/=]{16,}'

  P0 — customMetadata/*.md-meta.xml records containing fields named like a
       secret (Api_Key__c, Secret__c, Token__c, Password__c, Signing_Key__c)
       with a non-placeholder value populated.

  P1 — System.debug(...) call whose argument references a variable named
       like a secret (key, secret, token, password, credential).

Actual secret values are NEVER printed — only the file path, line number,
and a short redacted marker. Exit 1 if any P0 or P1 issues are found.

Usage:
    python3 check_apex_secrets_and_protected_cmdt.py [--manifest-dir PATH]

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable


HARDCODED_SECRET = re.compile(
    r"\b(api_?key|secret|token|password)\b\s*=\s*'([A-Za-z0-9\-_+/=]{16,})'",
    re.IGNORECASE,
)

DEBUG_OF_SECRET = re.compile(
    r"System\.debug\s*\([^)]*\b(api_?key|secret|token|password|credential)\b[^)]*\)",
    re.IGNORECASE,
)

SECRET_FIELD_NAMES = {
    "api_key__c",
    "apikey__c",
    "secret__c",
    "token__c",
    "password__c",
    "signing_key__c",
    "shared_secret__c",
    "client_secret__c",
}

PLACEHOLDER_VALUES = {
    "",
    "todo",
    "replace_me",
    "replace-me",
    "changeme",
    "change_me",
    "xxx",
    "xxxxxxxx",
    "placeholder",
}

CMDT_NS = "http://soap.sforce.com/2006/04/metadata"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex Secrets and Protected CMDT anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def redact(value: str) -> str:
    """Return a length-only marker so secret values never appear in output."""
    if not value:
        return "[REDACTED:empty]"
    return f"[REDACTED:len={len(value)}]"


def scan_apex_files(root: Path) -> list[tuple[str, str, int, str]]:
    """Walk .cls/.trigger files and return (severity, path, line, message) tuples."""
    findings: list[tuple[str, str, int, str]] = []
    apex_paths: Iterable[Path] = list(root.rglob("*.cls")) + list(root.rglob("*.trigger"))
    for path in apex_paths:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            print(f"WARN: cannot read {path}: {exc}", file=sys.stderr)
            continue

        for match in HARDCODED_SECRET.finditer(text):
            line_no = text[: match.start()].count("\n") + 1
            var_name = match.group(1)
            findings.append(
                (
                    "P0",
                    str(path),
                    line_no,
                    f"Hardcoded secret literal: variable '{var_name}' assigned {redact(match.group(2))}",
                )
            )

        for match in DEBUG_OF_SECRET.finditer(text):
            line_no = text[: match.start()].count("\n") + 1
            findings.append(
                (
                    "P1",
                    str(path),
                    line_no,
                    f"System.debug of secret-named variable '{match.group(1)}' (debug logs leak secrets)",
                )
            )
    return findings


def scan_custom_metadata(root: Path) -> list[tuple[str, str, int, str]]:
    """Scan customMetadata/*.md-meta.xml for secret-named fields with values."""
    findings: list[tuple[str, str, int, str]] = []
    cmdt_paths = list(root.rglob("customMetadata/*.md-meta.xml"))
    for path in cmdt_paths:
        try:
            tree = ET.parse(path)
        except (ET.ParseError, OSError) as exc:
            print(f"WARN: cannot parse {path}: {exc}", file=sys.stderr)
            continue

        root_el = tree.getroot()
        for values_el in root_el.findall(f"{{{CMDT_NS}}}values"):
            field_el = values_el.find(f"{{{CMDT_NS}}}field")
            value_el = values_el.find(f"{{{CMDT_NS}}}value")
            if field_el is None or field_el.text is None:
                continue
            field_name = field_el.text.strip().lower()
            if field_name not in SECRET_FIELD_NAMES:
                continue
            raw_value = (value_el.text or "").strip() if value_el is not None else ""
            if raw_value.lower() in PLACEHOLDER_VALUES:
                continue
            findings.append(
                (
                    "P0",
                    str(path),
                    0,
                    f"customMetadata record has secret-named field '{field_el.text}' populated with {redact(raw_value)} — value committed to source control",
                )
            )
    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    findings = scan_apex_files(root) + scan_custom_metadata(root)

    if not findings:
        print("No secret-storage anti-patterns detected.")
        return 0

    findings.sort(key=lambda item: (item[0], item[1], item[2]))
    has_blocking = False
    for severity, path, line_no, message in findings:
        if severity in {"P0", "P1"}:
            has_blocking = True
        location = f"{path}:{line_no}" if line_no else path
        print(f"{severity}: {location}: {message}", file=sys.stderr)

    return 1 if has_blocking else 0


if __name__ == "__main__":
    sys.exit(main())
