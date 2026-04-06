#!/usr/bin/env python3
"""Audit Apex exception-handling patterns for common reliability failures."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".cls", ".trigger"}
CATCH_RE = re.compile(r"catch\s*\(\s*([A-Za-z0-9_.]+)\s+([A-Za-z0-9_]+)\s*\)")
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}
LOGGER_HINTS = ("logger.", "log.", "eventbus.publish", "platformevent", "error_log__c", "publish(")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex files for swallowed exceptions and weak catch-block patterns."
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


def extract_catch_block(lines: list[str], start_index: int) -> tuple[list[str], int]:
    body: list[str] = []
    depth = 0
    seen_open = False
    i = start_index
    while i < len(lines):
        line = lines[i]
        if not seen_open and "{" in line:
            seen_open = True
            depth += line.count("{")
            depth -= line.count("}")
            body.append(line.split("{", 1)[1])
            if seen_open and depth <= 0:
                return body[:-1], i
        elif seen_open:
            body.append(line)
            depth += line.count("{")
            depth -= line.count("}")
            if depth <= 0:
                return body[:-1], i
        i += 1
    return body, i


def body_has_meaningful_code(body: list[str]) -> bool:
    for line in body:
        stripped = line.strip()
        if not stripped or stripped.startswith("//") or stripped in {"}", "};"}:
            continue
        return True
    return False


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()

    for index, line in enumerate(lines):
        match = CATCH_RE.search(line)
        if not match:
            continue

        exception_type = match.group(1)
        body, end_index = extract_catch_block(lines, index)
        body_text = "\n".join(body)
        lowered = body_text.lower()
        location = f"{path}:{index + 1}"

        if not body_has_meaningful_code(body):
            findings.append(f"CRITICAL {location}: empty catch block for `{exception_type}`")
            continue

        if "system.debug" in lowered and not any(token in lowered for token in LOGGER_HINTS) and "throw " not in lowered:
            findings.append(f"HIGH {location}: catch block only debugs `{exception_type}` without durable logging or rethrow")

        if exception_type == "Exception" and "throw " not in lowered and "adderror" not in lowered and not any(
            token in lowered for token in LOGGER_HINTS
        ):
            findings.append(f"HIGH {location}: generic `catch (Exception ...)` has no clear rethrow or logging strategy")

        if any(token in lowered for token in ("return null", "return false", "return new list", "return new map", "return;")) and "throw " not in lowered:
            findings.append(f"MEDIUM {location}: catch block appears to suppress `{exception_type}` and continue")

        if exception_type == "DmlException" and "database." not in lowered and "getdml" not in lowered and "geterrors" not in lowered:
            findings.append(f"REVIEW {location}: `DmlException` caught without obvious row-level error inspection")

        if path.suffix.lower() == ".trigger" and "adderror" not in lowered and "throw " not in lowered:
            findings.append(f"REVIEW {location}: trigger catch block neither rethrows nor uses `addError`; verify intended transaction behavior")

        if end_index == index:
            findings.append(f"LOW {location}: could not confidently parse catch-block braces; review manually")

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

    summary = f"Scanned {len(files)} Apex file(s); {len(findings)} exception-handling finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
