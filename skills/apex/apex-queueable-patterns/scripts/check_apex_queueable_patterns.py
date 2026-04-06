#!/usr/bin/env python3
"""Checker script for Apex Queueable Patterns skill.

Audits Apex source files for common Queueable implementation anti-patterns:
  - Queueable with callouts missing Database.AllowsCallouts
  - Multiple System.enqueueJob() calls inside a single execute() body (single-child rule violation)
  - Queueable execute() bodies with no System.attachFinalizer() call
  - System.enqueueJob() calls without AsyncOptions (unbounded chaining risk)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_apex_queueable_patterns.py [--manifest-dir path/to/metadata]
    python3 check_apex_queueable_patterns.py --manifest-dir force-app/main/default/classes
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

APEX_SUFFIXES = {".cls", ".trigger"}

QUEUEABLE_CLASS_RE = re.compile(
    r"\bimplements\b[^{;]*\bQueueable\b", re.IGNORECASE
)
ALLOWS_CALLOUTS_RE = re.compile(
    r"\bDatabase\.AllowsCallouts\b", re.IGNORECASE
)
HTTP_CALLOUT_RE = re.compile(
    r"\b(HttpRequest|Http\b|WebServiceCallout\.invoke)\b"
)
EXECUTE_QUEUEABLE_START_RE = re.compile(
    r"void\s+execute\s*\(\s*QueueableContext", re.IGNORECASE
)
ENQUEUE_JOB_RE = re.compile(
    r"\bSystem\.enqueueJob\s*\(", re.IGNORECASE
)
ATTACH_FINALIZER_RE = re.compile(
    r"\bSystem\.attachFinalizer\s*\(", re.IGNORECASE
)
ASYNC_OPTIONS_RE = re.compile(
    r"\bAsyncOptions\b", re.IGNORECASE
)
LOOP_RE = re.compile(r"\b(for|while)\s*\(")

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def iter_apex_files(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in APEX_SUFFIXES
    )


def extract_execute_body(lines: list[str], start_index: int) -> list[str]:
    """Return lines inside the first { } block starting at or after start_index."""
    body: list[str] = []
    depth = 0
    started = False
    for i in range(start_index, len(lines)):
        line = lines[i]
        opens = line.count("{")
        closes = line.count("}")
        if not started and opens > 0:
            started = True
        if started:
            body.append(line)
            depth += opens - closes
            if depth <= 0 and started:
                break
    return body


def normalize_finding(finding: str) -> dict[str, str]:
    parts = finding.split(" ", 1)
    severity = parts[0] if len(parts) > 1 else "INFO"
    remainder = parts[1] if len(parts) > 1 else finding
    location = ""
    message = remainder
    if ": " in remainder:
        location, _, message = remainder.partition(": ")
    return {"severity": severity, "location": location, "message": message}


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(f) for f in findings]
    penalty = sum(SEVERITY_WEIGHTS.get(n["severity"], 0) for n in normalized)
    score = max(0, 100 - penalty)
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


# ---------------------------------------------------------------------------
# Per-file audit
# ---------------------------------------------------------------------------

def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return [f"HIGH {path}: could not read file"]

    lines = text.splitlines()

    is_queueable = bool(QUEUEABLE_CLASS_RE.search(text))
    if not is_queueable:
        return findings  # Not a Queueable class — nothing to check

    has_allows_callouts = bool(ALLOWS_CALLOUTS_RE.search(text))
    has_http_callout = bool(HTTP_CALLOUT_RE.search(text))

    # Check 1: Callout without AllowsCallouts
    if has_http_callout and not has_allows_callouts:
        findings.append(
            f"HIGH {path}: Queueable makes HTTP callouts but does not implement "
            f"Database.AllowsCallouts — will throw CalloutException at runtime"
        )

    # Find execute(QueueableContext) method body
    execute_start_line = -1
    for idx, line in enumerate(lines):
        if EXECUTE_QUEUEABLE_START_RE.search(line):
            execute_start_line = idx
            break

    if execute_start_line == -1:
        # No execute() found — likely an abstract or interface; skip body checks
        return findings

    execute_body_lines = extract_execute_body(lines, execute_start_line)
    execute_body_text = "\n".join(execute_body_lines)

    # Check 2: Multiple enqueueJob calls inside execute body (single-child rule)
    enqueue_count = len(ENQUEUE_JOB_RE.findall(execute_body_text))
    if enqueue_count > 1:
        findings.append(
            f"CRITICAL {path}: execute(QueueableContext) contains {enqueue_count} "
            f"System.enqueueJob() calls — only one child Queueable may be enqueued per execution; "
            f"the second call throws LimitException at runtime"
        )

    # Check 3: No attachFinalizer in execute body (missing error recovery)
    if not ATTACH_FINALIZER_RE.search(execute_body_text):
        findings.append(
            f"MEDIUM {path}: execute(QueueableContext) does not call System.attachFinalizer() — "
            f"uncaught exceptions and platform-termination events will have no cleanup path"
        )

    # Check 4: enqueueJob calls without AsyncOptions (unbounded chaining)
    if enqueue_count >= 1 and not ASYNC_OPTIONS_RE.search(execute_body_text):
        findings.append(
            f"MEDIUM {path}: System.enqueueJob() is called without AsyncOptions — "
            f"consider setting MaximumQueueableStackDepth to prevent unbounded chaining"
        )

    # Check 5: enqueueJob inside a loop body
    loop_depth = 0
    for line_number, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()
        if LOOP_RE.search(stripped):
            loop_depth += stripped.count("{") or 1
        if loop_depth > 0 and ENQUEUE_JOB_RE.search(stripped):
            findings.append(
                f"CRITICAL {path}:{line_number}: System.enqueueJob() inside a loop — "
                f"this will throw LimitException on the second iteration"
            )
        if "}" in stripped and loop_depth > 0:
            loop_depth = max(0, loop_depth - stripped.count("}"))

    return findings


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit Apex files for Queueable anti-patterns: missing AllowsCallouts, "
            "multiple-child enqueue (single-child rule), missing Finalizer, and unbounded chaining."
        )
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for Apex classes and triggers (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)

    if not root.exists():
        return emit_result(
            [f"HIGH {root}: manifest directory not found"],
            "Scanned 0 Apex files; manifest directory was missing.",
        )

    files = iter_apex_files(root)
    if not files:
        return emit_result(
            [f"REVIEW {root}: no Apex files found"],
            "Scanned 0 Apex files; no .cls or .trigger files found.",
        )

    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))

    queueable_count = sum(
        1 for f in files
        if QUEUEABLE_CLASS_RE.search(f.read_text(encoding="utf-8", errors="ignore"))
    )
    summary = (
        f"Scanned {len(files)} Apex file(s); "
        f"{queueable_count} Queueable class(es) found; "
        f"{len(findings)} Queueable pattern finding(s) detected."
    )
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
