#!/usr/bin/env python3
"""Audit Agentforce action assets and invocable Apex for contract smells."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


INVOKABLE_RE = re.compile(r"@InvocableMethod", re.IGNORECASE)
LIST_SIGNATURE_RE = re.compile(r"\(\s*List<", re.IGNORECASE)
GENERIC_NAME_RE = re.compile(r"\b(doAction|execute|runProcess|handleRequest)\b", re.IGNORECASE)
OBJECT_PARAM_RE = re.compile(r"\bObject\b|\bMap<", re.IGNORECASE)
REQUIRED_VAR_RE = re.compile(r"@InvocableVariable\s*\([^)]*required\s*=\s*true", re.IGNORECASE)
ACTION_RE = re.compile(r"\baction\b", re.IGNORECASE)
CONFIRM_RE = re.compile(r"confirm|confirmation|are you sure", re.IGNORECASE)
WRITE_RE = re.compile(r"\b(create|update|delete|cancel|submit|send)\b", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check agent action assets and invocable Apex for naming and contract issues.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan for agent assets and Apex classes.")
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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def iter_files(root: Path) -> list[Path]:
    allowed = {".cls", ".json", ".yaml", ".yml", ".md", ".txt"}
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in allowed)


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 files; manifest directory was missing.")

    files = iter_files(root)
    findings: list[str] = []
    action_files = 0

    for path in files:
        text = read_text(path)
        lower_path = path.as_posix().lower()

        if path.suffix.lower() == ".cls" and INVOKABLE_RE.search(text):
            action_files += 1
            if not LIST_SIGNATURE_RE.search(text):
                findings.append(f"HIGH {path}: invocable method does not appear to accept a List input; verify it is safe for agent use")
            if OBJECT_PARAM_RE.search(text):
                findings.append(f"REVIEW {path}: generic Object or Map types found in invocable contract; prefer narrower agent-friendly schemas")
            if GENERIC_NAME_RE.search(text):
                findings.append(f"REVIEW {path}: generic action naming found in Apex; use a business-capability name instead")
            if len(REQUIRED_VAR_RE.findall(text)) >= 7:
                findings.append(f"REVIEW {path}: many required invocable variables found; verify the action contract is not overloaded")

        if "agent" in lower_path and ACTION_RE.search(text):
            action_files += 1
            action_count = len(ACTION_RE.findall(text))
            if action_count >= 15:
                findings.append(f"REVIEW {path}: {action_count} action markers found; confirm the agent action set is still intentionally small")
            if GENERIC_NAME_RE.search(text):
                findings.append(f"REVIEW {path}: generic action naming found in agent asset; improve labels and descriptions")
            if WRITE_RE.search(text) and not CONFIRM_RE.search(text):
                findings.append(f"REVIEW {path}: write-oriented action markers found without obvious confirmation language; verify side effects are gated intentionally")

    if action_files == 0:
        return emit_result([f"HIGH {root}: no agent-action-like assets found"], "Scanned 0 action-related files.")

    summary = f"Observed {action_files} action-related file(s); {len(findings)} agent-action finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
