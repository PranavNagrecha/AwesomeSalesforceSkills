#!/usr/bin/env python3
"""Static checks for Apex Platform Event subscriber triggers.

Catches four high-confidence anti-patterns documented in this skill:

  1. `EventBus.subscribe(...)` calls (the API doesn't exist).
  2. Platform Event trigger (`on <Name>__e (after insert)`) with no
     `setResumeCheckpoint` call in the body — silent re-processing on
     retry.
  3. Trigger that BOTH calls `setResumeCheckpoint` AND throws
     `EventBus.RetryableException` — contradictory retry strategy.
  4. Bare `catch (Exception ...)` followed by `throw new
     EventBus.RetryableException(...)` — mistreats permanent failures
     as transient, burns the 9-retry budget.

Stdlib only. Conservative regexes; signal tool, not a parser.

Usage:
    python3 check_apex_event_bus_subscriber.py --src-root .
    python3 check_apex_event_bus_subscriber.py --src-root force-app/main/default
    python3 check_apex_event_bus_subscriber.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Smell 1: fictional EventBus.subscribe API
_EVENTBUS_SUBSCRIBE_RE = re.compile(r"\bEventBus\.subscribe\s*\(", re.IGNORECASE)

# Trigger header on a Platform Event SObject (`__e` suffix), `after insert`.
_PE_TRIGGER_HEADER_RE = re.compile(
    r"\btrigger\s+(\w+)\s+on\s+(\w+__e)\s*\(\s*after\s+insert\b",
    re.IGNORECASE,
)

# Body markers we look for inside the trigger.
_SETRESUMECHECKPOINT_RE = re.compile(r"\bsetResumeCheckpoint\s*\(", re.IGNORECASE)
_RETRYABLE_THROW_RE = re.compile(
    r"\bthrow\s+new\s+EventBus\.RetryableException\s*\(", re.IGNORECASE
)
_BARE_CATCH_EXCEPTION_RE = re.compile(
    r"\bcatch\s*\(\s*Exception\s+\w+\s*\)\s*\{",
    re.IGNORECASE,
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _find_matching_brace(text: str, open_pos: int) -> int:
    depth = 0
    i = open_pos
    in_string = False
    in_line_comment = False
    in_block_comment = False
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
        elif in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 1
        elif in_string:
            if ch == "\\":
                i += 1
            elif ch == "'":
                in_string = False
        else:
            if ch == "/" and nxt == "/":
                in_line_comment = True
                i += 1
            elif ch == "/" and nxt == "*":
                in_block_comment = True
                i += 1
            elif ch == "'":
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    return len(text)


def _scan_apex_file(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    # Smell 1: EventBus.subscribe — anywhere in any Apex file
    for m in _EVENTBUS_SUBSCRIBE_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: `EventBus.subscribe(...)` does not exist "
            "in Apex. The only subscriber is an `after insert` trigger on the Platform "
            "Event SObject. (references/llm-anti-patterns.md § 1)"
        )

    # Trigger-specific smells (only fire inside .trigger files matching the PE header)
    if path.suffix.lower() == ".trigger":
        for header in _PE_TRIGGER_HEADER_RE.finditer(text):
            trigger_name = header.group(1)
            event_name = header.group(2)
            # Find body open brace after the header.
            after_header = text.find("{", header.end())
            if after_header == -1:
                continue
            body_end = _find_matching_brace(text, after_header)
            body = text[after_header : body_end + 1]
            line_no = _line_no(text, header.start())

            has_checkpoint = bool(_SETRESUMECHECKPOINT_RE.search(body))
            has_retryable = bool(_RETRYABLE_THROW_RE.search(body))
            has_bare_catch = bool(_BARE_CATCH_EXCEPTION_RE.search(body))

            # Smell 2: no checkpoint
            if not has_checkpoint and not has_retryable:
                findings.append(
                    f"{path}:{line_no}: trigger `{trigger_name}` on `{event_name}` has no "
                    "`setResumeCheckpoint(e.ReplayId)` and no `RetryableException` — "
                    "any uncaught exception will re-process already-handled events "
                    "on retry. (references/gotchas.md § 1, llm-anti-patterns.md § 2)"
                )

            # Smell 3: contradictory checkpoint + RetryableException
            if has_checkpoint and has_retryable:
                findings.append(
                    f"{path}:{line_no}: trigger `{trigger_name}` mixes `setResumeCheckpoint` "
                    "with `EventBus.RetryableException` — the two retry strategies "
                    "contradict (RetryableException re-fires the WHOLE batch, ignoring "
                    "checkpoints). (references/gotchas.md § 3, llm-anti-patterns.md § 4)"
                )

            # Smell 4: bare catch Exception → RetryableException
            if has_bare_catch and has_retryable:
                findings.append(
                    f"{path}:{line_no}: trigger `{trigger_name}` catches `Exception` and "
                    "throws `RetryableException` — permanent failures (bad payload, "
                    "validation errors) burn the 9-retry budget without succeeding. "
                    "Catch typed exceptions and split transient vs permanent. "
                    "(references/llm-anti-patterns.md § 5)"
                )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]
    apex_files = list(root.rglob("*.cls")) + list(root.rglob("*.trigger"))
    findings: list[str] = []
    for apex in apex_files:
        findings.extend(_scan_apex_file(apex))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Apex sources for Platform Event subscriber anti-patterns "
            "(fictional EventBus.subscribe, missing setResumeCheckpoint, "
            "contradictory retry strategies, bare-Exception → RetryableException)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the Apex source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no Platform Event subscriber anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
