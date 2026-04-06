#!/usr/bin/env python3
"""Audit Agentforce topic assets for scope and boundary smells."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TOPIC_RE = re.compile(r"\btopic\b", re.IGNORECASE)
AGENT_RE = re.compile(r"agentforce|agent", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"Topic\s+\d+|topic_\d+|General Help|Support", re.IGNORECASE)
BOUNDARY_RE = re.compile(r"out of scope|handoff|escalat|transfer|not for", re.IGNORECASE)
ACTION_RE = re.compile(r"\baction\b", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Agentforce topic assets for weak naming and missing boundaries.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan for agent configuration files.")
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
    allowed = {".json", ".yaml", ".yml", ".md", ".txt"}
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in allowed)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 files; manifest directory was missing.")

    files = iter_files(root)
    findings: list[str] = []
    topic_files: list[Path] = []

    for path in files:
        text = read_text(path)
        if not ((TOPIC_RE.search(path.name) or TOPIC_RE.search(text)) and (AGENT_RE.search(path.as_posix()) or AGENT_RE.search(text))):
            continue
        topic_files.append(path)

        if PLACEHOLDER_RE.search(text) or PLACEHOLDER_RE.search(path.name):
            findings.append(f"REVIEW {path}: placeholder or overly broad topic naming found; use capability-specific topic names")
        if not BOUNDARY_RE.search(text):
            findings.append(f"REVIEW {path}: topic-like asset found without obvious out-of-scope or handoff wording")
        action_count = len(ACTION_RE.findall(text))
        if action_count >= 15:
            findings.append(f"REVIEW {path}: topic asset references {action_count} action markers; verify the topic is not too broad for one capability boundary")

    if len(topic_files) > 10:
        findings.append(f"REVIEW {root}: {len(topic_files)} topic-like files found; verify the agent should not be narrowed with a topic selector")

    if not topic_files:
        return emit_result([f"HIGH {root}: no topic-like agent assets found"], "Scanned 0 topic-related files.")

    summary = f"Observed {len(topic_files)} topic-like file(s); {len(findings)} topic-design finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
