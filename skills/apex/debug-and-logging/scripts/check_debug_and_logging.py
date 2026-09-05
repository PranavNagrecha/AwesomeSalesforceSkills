#!/usr/bin/env python3
"""check_debug_and_logging.py — audit an Apex source tree for logging defects.

Stdlib only. Scans .cls, .trigger and .object-meta.xml files under --manifest-dir
and applies the rules this skill's gotchas are about:

  R1  System.debug() in a non-test class with no LoggingLevel argument   (advisory)
  R2  System.debug() inside a for/while loop                             (heap + 20 MB truncation)
  R3  catch block whose only statement is a System.debug (swallow)       (invisible to coverage)
  R4  logger/debug call concatenating an sObject collection in a loop    (heap)
  R5  __e object used for logging with no publishBehavior element        (rollback loses the log)
  R6  test that publishes an event and asserts, with no
      Test.getEventBus().deliver()                                       (asserts on an empty table)

Exit codes: 0 clean, 1 findings or a hard error (missing --manifest-dir).
An empty directory is a WARN with exit 0 — nothing to judge is not a failure.

Usage:
    python3 check_debug_and_logging.py --manifest-dir force-app/main/default
    python3 check_debug_and_logging.py --manifest-dir . --format text
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MDAPI_NS = "{http://soap.sforce.com/2006/04/metadata}"

TEST_CLASS_RE = re.compile(r"@is\s*test|\btestMethod\b", re.IGNORECASE)
SYSTEM_DEBUG_RE = re.compile(r"\bSystem\s*\.\s*debug\s*\(", re.IGNORECASE)
DEBUG_WITH_LEVEL_RE = re.compile(r"\bSystem\s*\.\s*debug\s*\(\s*(System\s*\.\s*)?LoggingLevel\s*\.", re.IGNORECASE)
LOOP_HEAD_RE = re.compile(r"\b(for|while)\s*\(")
CATCH_HEAD_RE = re.compile(r"\bcatch\s*\(\s*[\w.]+\s+\w+\s*\)\s*\{")
LOGGER_CALL_RE = re.compile(
    r"\b(System\s*\.\s*debug|LogService\s*\.\s*\w+|ApplicationLogger\s*\.\s*\w+|Logger\s*\.\s*\w+)\s*\(",
    re.IGNORECASE,
)
COLLECTION_CONCAT_RE = re.compile(
    r"\+\s*(JSON\s*\.\s*serialize(Pretty)?\s*\(|String\s*\.\s*valueOf\s*\(\s*\w*(list|set|map|records|rows|scope|new)\w*\b|"
    r"\w*(List|Set|Map|Records|Rows|Scope)\b\s*[),])",
    re.IGNORECASE,
)
EVENT_PUBLISH_RE = re.compile(r"\bEventBus\s*\.\s*publish\s*\(|\bLogService\s*\.\s*flush\s*\(", re.IGNORECASE)
DELIVER_RE = re.compile(r"\bTest\s*\.\s*getEventBus\s*\(\s*\)\s*\.\s*deliver\s*\(", re.IGNORECASE)
ASSERT_RE = re.compile(r"\b(System\s*\.\s*assert\w*|Assert\s*\.\s*\w+)\s*\(", re.IGNORECASE)
TEST_METHOD_SPLIT_RE = re.compile(r"@is\s*test\b", re.IGNORECASE)
LOG_EVENT_NAME_RE = re.compile(r"(log|error|audit|trace|telemetry|diagnostic)", re.IGNORECASE)

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest-dir", required=True, help="Root of the source tree to scan.")
    parser.add_argument("--format", choices=("json", "text"), default="json", help="Output format.")
    return parser.parse_args()


def child(parent, tag):
    """Return the first child element with `tag`, or None.

    Never use `a.find(x) or a.find(y)`: an Element with no children is falsy.
    """
    found = parent.find(MDAPI_NS + tag)
    if found is None:
        found = parent.find(tag)
    return found


def strip_apex(src: str) -> str:
    """Blank out string literals and comments so regexes do not match inside them.
    Newlines are preserved so line numbers stay accurate."""
    out = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "'":
            j = i + 1
            while j < n and src[j] != "'":
                j += 2 if src[j] == "\\" else 1
            out.append(" " * (min(j, n - 1) + 1 - i))
            i = j + 1
            continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("".join(c if c == "\n" else " " for c in src[i:j]))
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def block_end(text: str, open_brace: int) -> int:
    """Index just past the matching '}' for the '{' at open_brace, or len(text)."""
    depth = 0
    for i in range(open_brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    return len(text)


def loop_body_spans(clean: str) -> list[tuple[int, int]]:
    """(start, end) index spans of for/while bodies, including nested ones."""
    spans = []
    for m in LOOP_HEAD_RE.finditer(clean):
        brace = clean.find("{", m.end())
        if brace == -1 or brace - m.end() > 400:
            continue
        spans.append((brace, block_end(clean, brace)))
    return spans


def in_any_span(index: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= index < end for start, end in spans)


def audit_apex(path: Path, findings: list[str]) -> None:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    clean = strip_apex(raw)
    is_test = bool(TEST_CLASS_RE.search(clean))
    loops = loop_body_spans(clean)

    if not is_test:
        # R1 — advisory: a debug call with no explicit level uses DEBUG.
        for m in SYSTEM_DEBUG_RE.finditer(clean):
            if not DEBUG_WITH_LEVEL_RE.match(clean, m.start()):
                findings.append(
                    f"REVIEW {path}:{line_of(clean, m.start())}: `System.debug` with no LoggingLevel "
                    "argument defaults to DEBUG; give it a level or route it through LogService"
                )

        # R2 — debug inside a loop.
        for m in SYSTEM_DEBUG_RE.finditer(clean):
            if in_any_span(m.start(), loops):
                findings.append(
                    f"MEDIUM {path}:{line_of(clean, m.start())}: `System.debug` inside a loop; "
                    "per-record log lines are the usual cause of 20 MB log truncation"
                )

        # R3 — catch block whose only statement is a System.debug.
        for m in CATCH_HEAD_RE.finditer(clean):
            brace = clean.index("{", m.start())
            body = clean[brace + 1: block_end(clean, brace) - 1]
            statements = [s.strip() for s in body.split(";") if s.strip()]
            if statements and all(SYSTEM_DEBUG_RE.search(s) for s in statements):
                findings.append(
                    f"HIGH {path}:{line_of(clean, m.start())}: catch block only calls `System.debug` "
                    "and swallows the exception; rethrow or call LogService.error(...) then rethrow"
                )

    # R4 — logger call concatenating a collection, inside a loop.
    for m in LOGGER_CALL_RE.finditer(clean):
        if not in_any_span(m.start(), loops):
            continue
        close = clean.find(")", m.end())
        arg = clean[m.end(): close if close != -1 else m.end() + 200]
        if COLLECTION_CONCAT_RE.search(arg):
            findings.append(
                f"HIGH {path}:{line_of(clean, m.start())}: log call concatenates a collection or "
                "serialized object inside a loop; the string is built before the level filter applies"
            )

    # R6 — test publishes an event and asserts, but never delivers.
    if is_test:
        chunks = TEST_METHOD_SPLIT_RE.split(clean)
        for chunk in chunks[1:]:
            if EVENT_PUBLISH_RE.search(chunk) and ASSERT_RE.search(chunk) and not DELIVER_RE.search(chunk):
                idx = EVENT_PUBLISH_RE.search(chunk).start()
                approx = clean.index(chunk[idx: idx + 40]) if chunk[idx: idx + 40] in clean else 0
                findings.append(
                    f"HIGH {path}:{line_of(clean, approx)}: test publishes an event and asserts without "
                    "`Test.getEventBus().deliver()`; the subscriber never runs and the assertion sees an empty table"
                )


def audit_object(path: Path, findings: list[str]) -> None:
    name = path.name.split(".")[0]
    if not name.endswith("__e"):
        return
    if not LOG_EVENT_NAME_RE.search(name):
        return
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        findings.append(f"HIGH {path}:1: platform event XML does not parse ({exc})")
        return
    behavior = child(root, "publishBehavior")
    if behavior is None:
        findings.append(
            f"HIGH {path}:1: logging platform event `{name}` declares no <publishBehavior>; "
            "state PublishImmediately so ERROR records survive a rollback"
        )
    elif (behavior.text or "").strip() != "PublishImmediately":
        findings.append(
            f"CRITICAL {path}:1: logging platform event `{name}` uses publishBehavior "
            f"`{(behavior.text or '').strip()}`; the log is discarded when the transaction fails"
        )
    event_type = child(root, "eventType")
    if event_type is not None and (event_type.text or "").strip() == "StandardVolume":
        findings.append(
            f"HIGH {path}:1: `{name}` uses the deprecated StandardVolume eventType; use HighVolume"
        )


def normalize(finding: str) -> dict:
    severity, _, remainder = finding.partition(" ")
    location, _, message = remainder.partition(": ")
    return {"severity": severity or "REVIEW", "location": location, "message": message or remainder}


def emit(findings: list[str], summary: str, fmt: str, exit_code: int) -> int:
    rows = [normalize(f) for f in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(r["severity"], 0) for r in rows))
    if fmt == "text":
        for r in rows:
            print(f"{r['severity']:9} {r['location']}  {r['message']}")
        print(summary)
    else:
        print(json.dumps({"score": score, "findings": rows, "summary": summary}, indent=2))
    if rows:
        print(f"WARN: {len(rows)} finding(s) detected", file=sys.stderr)
    return exit_code


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        return emit(
            [f"CRITICAL {root}:0: manifest directory not found"],
            f"Manifest directory {root} does not exist.",
            args.format,
            1,
        )

    apex_files = sorted(p for p in root.rglob("*") if p.suffix in (".cls", ".trigger") and p.is_file())
    object_files = sorted(root.rglob("*.object-meta.xml"))
    if not apex_files and not object_files:
        print(f"WARN: no .cls, .trigger or .object-meta.xml files under {root}", file=sys.stderr)
        return emit([], f"Scanned 0 files under {root}; nothing to check.", args.format, 0)

    findings: list[str] = []
    for path in apex_files:
        audit_apex(path, findings)
    for path in object_files:
        audit_object(path, findings)

    summary = (
        f"Scanned {len(apex_files)} Apex file(s) and {len(object_files)} object file(s); "
        f"{len(findings)} logging finding(s)."
    )
    return emit(findings, summary, args.format, 1 if findings else 0)


if __name__ == "__main__":
    sys.exit(main())
