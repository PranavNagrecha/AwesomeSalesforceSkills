#!/usr/bin/env python3
"""Audit Apex source for the CPU- and heap-heavy patterns this skill covers.

Static, stdlib-only, regex + brace-matching. It never compiles Apex and never
contacts an org: treat every finding as a place to look, not a proven defect.

Checks implemented
------------------
1. SOQL or DML inside a loop body                              (CRITICAL)
2. Nested loops over two collections with no Map/Set lookup    (HIGH)
3. String `+=` accumulation inside a loop                      (HIGH)
4. `Schema.getGlobalDescribe()` in a loop or in a per-record   (HIGH / MEDIUM)
   method signature
5. Test classes with no 200-record bulk case                   (MEDIUM)
6. Test classes that never assert on `Limits.*` headroom, and  (MEDIUM / HIGH)
   `Limits.*` reads placed after `Test.stopTest()`
Plus topical extras: JSON serialize/deserialize in a loop, `Pattern.compile`
in a loop, deep `clone()` in a loop, unthrottled `Limits.getCpuTime()` inside a
loop, and `SeeAllData=true`.

Usage:
    python3 check_apex_cpu_and_heap_optimization.py --manifest-dir force-app
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

LOOP_HEADER_RE = re.compile(r"\b(for|while)\s*\(")
SOQL_RE = re.compile(r"\[\s*SELECT\b", re.IGNORECASE)
DML_RE = re.compile(r"\b(?:insert|update|upsert|delete|undelete)\s+(?!new\s+Map\b)[A-Za-z_]", re.IGNORECASE)
DATABASE_DML_RE = re.compile(
    r"\bDatabase\.(?:insert|update|upsert|delete|undelete|query|queryWithBinds|countQuery|getQueryLocator)\s*\(",
    re.IGNORECASE,
)
JSON_RE = re.compile(r"\bJSON\.(?:serialize|serializePretty|deserialize|deserializeUntyped|deserializeStrict)\s*\(", re.IGNORECASE)
PATTERN_RE = re.compile(r"\bPattern\.compile\s*\(", re.IGNORECASE)
CLONE_RE = re.compile(r"\.clone\s*\(\s*true", re.IGNORECASE)
GLOBAL_DESCRIBE_RE = re.compile(r"\bSchema\.getGlobalDescribe\s*\(", re.IGNORECASE)
CPU_PROBE_RE = re.compile(r"\bLimits\.getCpuTime\s*\(", re.IGNORECASE)
THROTTLE_RE = re.compile(r"\bMath\.mod\s*\(|%\s*\d+\s*==|\bmodulo\b", re.IGNORECASE)
MAP_LOOKUP_RE = re.compile(r"\.(?:get|containsKey|contains)\s*\(")
STRING_DECL_RE = re.compile(r"\bString\s+([A-Za-z_]\w*)\s*(?:=|;)")
FOREACH_RE = re.compile(r"\bfor\s*\(\s*(?:final\s+)?[A-Za-z_][\w<>,\s\[\]\.]*?\s+([A-Za-z_]\w*)\s*:\s*([^)]+)\)")
IS_TEST_RE = re.compile(r"@IsTest\b", re.IGNORECASE)
SEE_ALL_DATA_RE = re.compile(r"SeeAllData\s*=\s*true", re.IGNORECASE)
STOP_TEST_RE = re.compile(r"\bTest\.stopTest\s*\(", re.IGNORECASE)
LIMITS_READ_RE = re.compile(r"\bLimits\.get(?:CpuTime|HeapSize)\s*\(", re.IGNORECASE)
ASSERT_RE = re.compile(r"\b(?:Assert\.\w+|System\.assert\w*)\s*\(", re.IGNORECASE)
# a record count reads as "200 or more" only in a count-ish position: a loop bound,
# a LIMIT clause, a factory argument, or a constant assignment. Numbers on a line
# that also mentions Limits.* are governor ceilings, not record counts.
BULK_COUNT_RE = re.compile(r"(?:<=?\s*|LIMIT\s+|\(\s*|,\s*|=\s*)(\d{3,})\b", re.IGNORECASE)
PER_RECORD_SIG_RE = re.compile(
    r"\b(?:public|private|protected|global)\s+(?:static\s+)?[\w<>,\s\[\]\.]+?\s+(\w+)\s*\(\s*(?!List<|Set<|Map<)[A-Z]\w*(?:__c)?\s+\w+\s*\)"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex classes and triggers for CPU-time and heap-size anti-patterns."
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Apex source tree to scan (e.g. force-app/main/default/classes).",
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


def iter_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".cls", ".trigger"}
    )


def sanitize(text: str) -> str:
    """Blank out comments and string literals while preserving offsets and newlines."""
    def blank(match: re.Match) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    text = re.sub(r"//[^\n]*", blank, text)
    text = re.sub(r"/\*.*?\*/", blank, text, flags=re.S)
    text = re.sub(r"'(?:\\.|[^'\\\n])*'", lambda m: "'" + " " * (len(m.group(0)) - 2) + "'", text)
    return text


def match_bracket(text: str, start: int, opener: str, closer: str) -> int:
    """Index just past the bracket that matches the one at `start`, or -1."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == opener:
            depth += 1
        elif text[i] == closer:
            depth -= 1
            if depth == 0:
                return i + 1
    return -1


def loop_regions(text: str) -> list[tuple[int, int, int]]:
    """(header_start, body_start, body_end) for every loop body in `text`."""
    regions: list[tuple[int, int, int]] = []
    for match in LOOP_HEADER_RE.finditer(text):
        paren_open = text.index("(", match.start())
        paren_end = match_bracket(text, paren_open, "(", ")")
        if paren_end == -1:
            continue
        cursor = paren_end
        while cursor < len(text) and text[cursor] in " \t\r\n":
            cursor += 1
        if cursor < len(text) and text[cursor] == "{":
            body_end = match_bracket(text, cursor, "{", "}")
            if body_end == -1:
                continue
            regions.append((match.start(), cursor, body_end))
        else:
            semi = text.find(";", cursor)
            regions.append((match.start(), cursor, semi + 1 if semi != -1 else len(text)))
    return regions


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def scan_loops(path: Path, raw: str, clean: str) -> list[str]:
    findings: list[str] = []
    regions = loop_regions(clean)
    string_vars = set(STRING_DECL_RE.findall(clean))

    for header_start, body_start, body_end in regions:
        body = clean[body_start:body_end]
        offset = body_start
        line = line_of(clean, header_start)

        for pattern, severity, message in (
            (SOQL_RE, "CRITICAL", "SOQL query inside a loop body"),
            (DATABASE_DML_RE, "CRITICAL", "Database.* DML or query call inside a loop body"),
            (DML_RE, "CRITICAL", "DML statement inside a loop body"),
            (JSON_RE, "HIGH", "JSON serialize/deserialize inside a loop body (CPU and heap)"),
            (PATTERN_RE, "HIGH", "Pattern.compile inside a loop body; hoist the compiled Pattern out"),
            (CLONE_RE, "MEDIUM", "deep clone() inside a loop body doubles heap for the collection"),
            (GLOBAL_DESCRIBE_RE, "HIGH", "Schema.getGlobalDescribe() inside a loop body; the map is built at runtime over every sObject in the org"),
        ):
            hit = pattern.search(body)
            if hit:
                findings.append(
                    f"{severity} {path}:{line_of(clean, offset + hit.start())}: {message}"
                )

        cpu_hit = CPU_PROBE_RE.search(body)
        if cpu_hit and not THROTTLE_RE.search(body):
            findings.append(
                f"MEDIUM {path}:{line_of(clean, offset + cpu_hit.start())}: "
                "Limits.getCpuTime() called on every iteration; measure a block or throttle with Math.mod"
            )

        for var in string_vars:
            concat = re.search(rf"\b{re.escape(var)}\s*\+=", body)
            if concat:
                findings.append(
                    f"HIGH {path}:{line_of(clean, offset + concat.start())}: "
                    f"String '{var}' accumulated with += inside a loop; build a List<String> and String.join once"
                )

        # nested loop over a second collection with no Map/Set lookup in the outer body
        outer_header = clean[header_start:body_start]
        outer_iter = FOREACH_RE.search(outer_header)
        for inner_start, inner_body_start, inner_body_end in regions:
            if not (body_start < inner_start < body_end):
                continue
            inner_header = clean[inner_start:inner_body_start]
            inner_iter = FOREACH_RE.search(inner_header)
            if not (outer_iter and inner_iter):
                continue
            outer_var = outer_iter.group(1)
            inner_source = inner_iter.group(2)
            if outer_var in inner_source:
                continue  # iterating the outer record's own children — not a cross product
            if MAP_LOOKUP_RE.search(body):
                continue  # already indexed
            findings.append(
                f"HIGH {path}:{line_of(clean, inner_start)}: "
                f"nested loop iterates '{inner_source.strip()}' for every '{outer_var}' with no Map/Set lookup; "
                "index one collection into a Map before the outer loop"
            )
            break
    return findings


def scan_test_class(path: Path, clean: str) -> list[str]:
    findings: list[str] = []
    see_all = SEE_ALL_DATA_RE.search(clean)
    if see_all:
        findings.append(
            f"HIGH {path}:{line_of(clean, see_all.start())}: SeeAllData=true makes the run depend on org data; limits measured this way are not reproducible"
        )

    bulk = None
    for match in BULK_COUNT_RE.finditer(clean):
        line_start = clean.rfind("\n", 0, match.start()) + 1
        line_end = clean.find("\n", match.start())
        line_text = clean[line_start: line_end if line_end != -1 else len(clean)]
        if "limits." in line_text.lower():
            continue
        if int(match.group(1)) >= 200:
            bulk = match
            break
    if not bulk:
        findings.append(
            f"MEDIUM {path}: test class has no 200-or-more record case; CPU and heap defects only appear at bulk volume"
        )

    if not LIMITS_READ_RE.search(clean):
        findings.append(
            f"MEDIUM {path}: test class never reads Limits.getCpuTime()/getHeapSize(); add a headroom assertion so a regression fails the build"
        )
    else:
        stop = STOP_TEST_RE.search(clean)
        if stop:
            after = clean[stop.end():]
            late = LIMITS_READ_RE.search(after)
            if late:
                findings.append(
                    f"HIGH {path}:{line_of(clean, stop.end() + late.start())}: "
                    "Limits.getCpuTime()/getHeapSize() read after Test.stopTest(); that reverts to the limits in effect before startTest, so it measures the setup block"
                )
        if not ASSERT_RE.search(clean):
            findings.append(
                f"MEDIUM {path}: test class reads Limits.* but contains no assertion; a measurement nobody asserts on is not a gate"
            )
    return findings


def scan_describe_signatures(path: Path, clean: str) -> list[str]:
    findings: list[str] = []
    if not GLOBAL_DESCRIBE_RE.search(clean):
        return findings
    for match in PER_RECORD_SIG_RE.finditer(clean):
        body_open = clean.find("{", match.end() - 1)
        if body_open == -1:
            continue
        body_end = match_bracket(clean, body_open, "{", "}")
        if body_end == -1:
            continue
        hit = GLOBAL_DESCRIBE_RE.search(clean[body_open:body_end])
        if hit:
            findings.append(
                f"MEDIUM {path}:{line_of(clean, body_open + hit.start())}: "
                f"Schema.getGlobalDescribe() inside '{match.group(1)}', which takes a single record and is therefore called per record; "
                "resolve the describe once and pass it in"
            )
    return findings


def audit_file(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    clean = sanitize(raw)
    findings = scan_loops(path, raw, clean)
    findings.extend(scan_describe_signatures(path, clean))
    if IS_TEST_RE.search(clean):
        findings.extend(scan_test_class(path, clean))
    return findings


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
            "Scanned 0 Apex files; no .cls or .trigger files were found.",
        )
    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))
    findings = list(dict.fromkeys(findings))  # a hit inside nested loops reports once
    summary = f"Scanned {len(files)} Apex file(s); {len(findings)} CPU/heap finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
