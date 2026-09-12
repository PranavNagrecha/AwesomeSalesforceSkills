#!/usr/bin/env python3
"""check_platform_events_apex.py — audit an Apex platform-event publish/subscribe slice.

Stdlib only. Point --manifest-dir at a source tree (for example
force-app/main/default) and it walks every .cls, .trigger and *.object-meta.xml
under it.

Rules (each maps to a gotcha in ../references/gotchas.md):

  R1  EventBus.publish(...) result is discarded
      -> apexrefguide L214561-214565: publish never throws for a rejected event;
         the SaveResult is the only failure signal.
  R2  EventBus.publish(...) called inside a loop
      -> apexdev L19598 / L19635: 150 publish-immediately calls, or one DML
         statement per publish-after-commit call, per transaction.
  R3  __e trigger declared with any event other than `after insert`
      -> a platform event subscriber has exactly one context.
  R4  DML or SOQL directly inside a for-each loop over an __e collection
      -> apexdev L19862: the platform-event trigger batch size is 2,000.
  R5  EventBus.RetryableException thrown with no read of
      EventBus.TriggerContext.currentContext().retries in the same file
      -> object_reference L131382-131390: exceeding the retry budget puts the
         subscription into Status = Error, where it stops receiving events.
  R6  A *__e.object-meta.xml with no <publishBehavior> element
      -> api_meta L42228-42229: the default is PublishImmediately, which fires
         even when the transaction rolls back.
  R7  A test method that publishes an event but never calls
      Test.getEventBus().deliver() or Test.getEventBus().fail()
      -> apexrefguide L157686-157712: stopTest() does not flush the event bus.
  R8  setResumeCheckpoint(...) called before the work for that event completes
      (advisory heuristic: the checkpoint is the first statement in the loop
      body, or precedes the only DML in the loop)
      -> apexrefguide L157866-157874: the trigger resumes AFTER the checkpoint,
         so checkpointing early silently skips unprocessed events.
  R9  EventBus.publish(...) of a <Name>__e with no *.permissionset-meta.xml or
      *.profile-meta.xml under the scanned tree granting <allowCreate>true
      on that <Name>__e via <objectPermissions>
      -> apexdev L11735-11737, L11760-11763: Apex enforces the running user's
         object permissions by default; at API 67.0 that includes Create on a
         published platform event (apexrefguide L214529-214531, cited on the
         same gotcha). WARN only, not ERROR: a build may grant the permission
         from a permission set or profile outside the scanned tree. Pass
         --strict to fail the run on this rule too.

Exit codes: 0 clean, 1 on any finding other than a bare WARN (WARN alone does
not fail unless --strict is passed), or a missing --manifest-dir.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

APEX_SUFFIXES = {".cls", ".trigger"}
OBJECT_SUFFIX = ".object-meta.xml"
PERMSET_SUFFIX = ".permissionset-meta.xml"
PROFILE_SUFFIX = ".profile-meta.xml"
MDAPI_NS = "http://soap.sforce.com/2006/04/metadata"

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0, "WARN": 3}

PUBLISH_RE = re.compile(r"\bEventBus\s*\.\s*publish(?:WithAccessLevel)?\s*\(")
INLINE_EVENT_RE = re.compile(r"EventBus\s*\.\s*publish(?:WithAccessLevel)?\s*\(\s*new\s+(\w+__e)\b")
EVENT_TYPE_TOKEN_RE = re.compile(r"\b(\w+__e)\b")
ASSIGNED_PUBLISH_RE = re.compile(
    r"(?:List\s*<\s*Database\.SaveResult\s*>|Database\.SaveResult|\w+)\s*(?:\w+\s*)?=\s*EventBus\s*\.\s*publish"
)
RETURN_PUBLISH_RE = re.compile(r"\breturn\s+EventBus\s*\.\s*publish")
EVENT_TRIGGER_RE = re.compile(
    r"\btrigger\s+(\w+)\s+on\s+(\w+__e)\s*\(([^)]*)\)", re.IGNORECASE
)
LOOP_HEAD_RE = re.compile(r"\b(?:for|while|do)\b\s*[({]")
EVENT_FOREACH_RE = re.compile(r"\bfor\s*\(\s*(\w+__e)\s+(\w+)\s*:", re.IGNORECASE)
DML_RE = re.compile(r"\b(?:insert|update|upsert|delete|undelete|merge)\s+[\w(\[]")
DATABASE_DML_RE = re.compile(r"\bDatabase\s*\.\s*(?:insert|update|upsert|delete|undelete|convertLead)\s*\(")
SOQL_RE = re.compile(r"\[\s*SELECT\b", re.IGNORECASE)
RETRYABLE_THROW_RE = re.compile(r"\bthrow\s+new\s+EventBus\s*\.\s*RetryableException\b")
RETRIES_READ_RE = re.compile(r"\bTriggerContext\s*\.\s*currentContext\s*\(\s*\)\s*\.\s*retries\b|\.\s*retries\b")
CHECKPOINT_RE = re.compile(r"\bsetResumeCheckpoint\s*\(")
DELIVER_RE = re.compile(r"\bTest\s*\.\s*getEventBus\s*\(\s*\)\s*\.\s*(?:deliver|fail)\s*\(")
TESTMETHOD_RE = re.compile(
    r"@IsTest[^\n]*\n(?:\s*(?:static|private|public|global|void|\w+)\s+)*?\s*(?:static\s+)?void\s+(\w+)\s*\(",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check an Apex platform-event publish/subscribe slice.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the source tree to scan (e.g. force-app/main/default).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also fail (exit 1) on WARN-level findings, such as R9's missing "
        "permission-set Create grant on a published platform event.",
    )
    return parser.parse_args()


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location, message = "", remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str, exit_code: int) -> int:
    normalized = [normalize_finding(item) for item in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(f["severity"], 0) for f in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return exit_code


def strip_noise(src: str) -> str:
    """Blank comments and string literals, preserving line count and offsets."""
    out = list(src)
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "'":
            j = i + 1
            while j < n and src[j] != "'":
                j += 2 if src[j] == "\\" else 1
            for k in range(i, min(j + 1, n)):
                if out[k] != "\n":
                    out[k] = " "
            i = j + 1
            continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            for k in range(i, j):
                out[k] = " "
            i = j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            for k in range(i, min(j, n)):
                if out[k] != "\n":
                    out[k] = " "
            i = j
            continue
        i += 1
    return "".join(out)


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def block_end(text: str, open_brace: int) -> int:
    """Index just past the matching close brace for the '{' at open_brace."""
    depth = 0
    for i in range(open_brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    return len(text)


def loop_bodies(code: str) -> list[tuple[int, int, str]]:
    """(start, end, header) for each loop body, brace-delimited only."""
    bodies = []
    for m in LOOP_HEAD_RE.finditer(code):
        brace = code.find("{", m.start())
        if brace == -1:
            continue
        # a '{' more than a header away is a single-statement loop; skip it
        if "\n" in code[m.end() : brace] and code[m.end() : brace].count(";") > 2:
            continue
        bodies.append((brace, block_end(code, brace), code[m.start() : brace]))
    return bodies


def audit_apex(path: Path, rel: str) -> list[str]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    code = strip_noise(raw)
    findings: list[str] = []
    # A test class deliberately drives the publish path; a discarded result there
    # is a weaker signal than in production code, so it is reported at REVIEW.
    is_test = bool(re.search(r"@IsTest\b", raw, re.IGNORECASE))

    # R1 — publish result discarded
    for m in PUBLISH_RE.finditer(code):
        # the statement may wrap across lines, so scan back to the previous
        # statement or block boundary rather than to the previous newline
        stmt_start = max(code.rfind(ch, 0, m.start()) for ch in ";{}") + 1
        stmt = code[stmt_start : code.find(";", m.start()) + 1]
        if not (ASSIGNED_PUBLISH_RE.search(stmt) or RETURN_PUBLISH_RE.search(stmt)):
            findings.append(
                f"{'REVIEW' if is_test else 'HIGH'} {rel}:{line_of(code, m.start())}: EventBus.publish result is "
                "discarded; publish does not throw for a rejected event, so the SaveResult is the only failure signal (R1)"
            )

    # R2 — publish inside a loop
    for start, end, _ in loop_bodies(code):
        for m in PUBLISH_RE.finditer(code, start, end):
            findings.append(
                f"HIGH {rel}:{line_of(code, m.start())}: EventBus.publish inside a loop; "
                "collect the events and publish the list once (R2)"
            )

    # R3 — __e trigger context
    for m in EVENT_TRIGGER_RE.finditer(code):
        name, event, events = m.group(1), m.group(2), m.group(3)
        declared = {e.strip().lower() for e in events.split(",") if e.strip()}
        if declared != {"after insert"}:
            findings.append(
                f"CRITICAL {rel}:{line_of(code, m.start())}: trigger {name} on {event} declares "
                f"({', '.join(sorted(declared)) or 'nothing'}); a platform event subscriber runs only in after insert (R3)"
            )

    # R4 — DML/SOQL inside a for-each over an __e collection
    for m in EVENT_FOREACH_RE.finditer(code):
        brace = code.find("{", m.start())
        if brace == -1:
            continue
        end = block_end(code, brace)
        body = code[brace:end]
        # nested loop bodies are still inside this loop, so scan the whole body
        for pattern, label in ((DML_RE, "DML"), (DATABASE_DML_RE, "Database DML"), (SOQL_RE, "SOQL")):
            hit = pattern.search(body)
            if hit:
                findings.append(
                    f"HIGH {rel}:{line_of(code, brace + hit.start())}: {label} inside the loop over "
                    f"{m.group(1)} records; the default platform-event trigger batch is 2,000 events (R4)"
                )
                break

    # R5 — RetryableException without a retry-count guard
    throws = list(RETRYABLE_THROW_RE.finditer(code))
    if throws and not RETRIES_READ_RE.search(code):
        findings.append(
            f"CRITICAL {rel}:{line_of(code, throws[0].start())}: EventBus.RetryableException is thrown with no read "
            "of EventBus.TriggerContext.currentContext().retries; exceeding the budget puts the subscription into "
            "Status = Error and it later resumes from the tip, skipping the backlog (R5)"
        )

    # R7 — test method publishes without driving the bus
    if "@IsTest" in raw or "@isTest" in raw:
        for m in TESTMETHOD_RE.finditer(code):
            brace = code.find("{", m.end())
            if brace == -1:
                continue
            body = code[brace : block_end(code, brace)]
            if PUBLISH_RE.search(body) and not DELIVER_RE.search(body):
                findings.append(
                    f"HIGH {rel}:{line_of(code, m.start())}: test method {m.group(1)} publishes an event but never "
                    "calls Test.getEventBus().deliver() or .fail(); stopTest() does not flush the event bus (R7)"
                )

    # R8 — checkpoint set before the work (advisory)
    for start, end, header in loop_bodies(code):
        body = code[start:end]
        cp = CHECKPOINT_RE.search(body)
        if not cp:
            continue
        work = None
        for pattern in (DML_RE, DATABASE_DML_RE, SOQL_RE):
            hit = pattern.search(body)
            if hit and (work is None or hit.start() < work):
                work = hit.start()
        first_stmt = body.find(";")
        if work is not None and cp.start() < work:
            findings.append(
                f"REVIEW {rel}:{line_of(code, start + cp.start())}: setResumeCheckpoint appears before the "
                "SOQL/DML for that event; the trigger resumes AFTER the checkpoint, so an early checkpoint "
                "silently skips unprocessed events (R8)"
            )
        elif work is None and first_stmt != -1 and cp.start() <= first_stmt:
            findings.append(
                f"REVIEW {rel}:{line_of(code, start + cp.start())}: setResumeCheckpoint is the first statement in "
                "the loop body; confirm the work for that event has completed before checkpointing (R8)"
            )

    return findings


def audit_object(path: Path, rel: str) -> list[str]:
    if not path.name.endswith(OBJECT_SUFFIX):
        return []
    if not path.name[: -len(OBJECT_SUFFIX)].endswith("__e"):
        return []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"HIGH {rel}: platform event object file does not parse — {exc}"]

    def child(tag: str):
        node = root.find(f"{{{MDAPI_NS}}}{tag}")
        if node is None:
            node = root.find(tag)
        return node

    findings: list[str] = []
    behavior = child("publishBehavior")
    if behavior is None:
        findings.append(
            f"HIGH {rel}: platform event definition has no <publishBehavior>; the default is "
            "PublishImmediately, which publishes even when the transaction rolls back (R6)"
        )
    elif (behavior.text or "").strip() not in ("PublishAfterCommit", "PublishImmediately"):
        findings.append(
            f"HIGH {rel}: <publishBehavior> is '{(behavior.text or '').strip()}'; valid values are "
            "PublishAfterCommit and PublishImmediately (R6)"
        )

    event_type = child("eventType")
    if event_type is not None and (event_type.text or "").strip() == "StandardVolume":
        findings.append(
            f"MEDIUM {rel}: <eventType>StandardVolume</eventType> is deprecated; new events use HighVolume "
            "and existing ones migrate with PlatformEventMigration (R6)"
        )
    return findings


def published_events_in_file(code: str) -> set[str]:
    """Best-effort set of <Name>__e types published via EventBus in this file.

    Prefers the inline-construction shape (`EventBus.publish(new Foo__e(...))`).
    Falls back to the nearest preceding `__e` type token in the file for the
    common case of publishing a variable or a pre-built list — a heuristic,
    not a type resolver, matching the rest of this checker's approach (R8).
    """
    events: set[str] = set()
    for m in INLINE_EVENT_RE.finditer(code):
        events.add(m.group(1))
    if events:
        return events
    for m in PUBLISH_RE.finditer(code):
        preceding = list(EVENT_TYPE_TOKEN_RE.finditer(code, 0, m.start()))
        if preceding:
            events.add(preceding[-1].group(1))
    return events


def collect_granted_create_objects(root: Path) -> set[str]:
    """<Name>__e object names with <allowCreate>true in any permission set or
    profile under root, so R9 can check a publisher against the whole tree
    rather than just the object file's own folder."""
    granted: set[str] = set()
    files = sorted(root.rglob(f"*{PERMSET_SUFFIX}")) + sorted(root.rglob(f"*{PROFILE_SUFFIX}"))
    for path in files:
        try:
            root_el = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        for node in root_el.iter():
            tag = node.tag.rsplit("}", 1)[-1]
            if tag != "objectPermissions":
                continue
            obj_name = None
            allow_create = False
            for child in node:
                child_tag = child.tag.rsplit("}", 1)[-1]
                if child_tag == "object":
                    obj_name = (child.text or "").strip()
                elif child_tag == "allowCreate":
                    allow_create = (child.text or "").strip().lower() == "true"
            if obj_name and obj_name.endswith("__e") and allow_create:
                granted.add(obj_name)
    return granted


def audit_publish_permissions(apex_files: list[Path], root: Path) -> list[str]:
    """R9 — a publisher with no permission-set/profile Create grant anywhere
    in the scanned tree. WARN, not ERROR: a build may grant the permission
    from a permission set that lives outside --manifest-dir."""
    granted = collect_granted_create_objects(root)
    publishers: dict[str, set[str]] = {}
    for path in apex_files:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        code = strip_noise(raw)
        for event in published_events_in_file(code):
            publishers.setdefault(event, set()).add(str(path))

    findings: list[str] = []
    for event in sorted(publishers):
        if event in granted:
            continue
        for rel in sorted(publishers[event]):
            findings.append(
                f"WARN {rel}: publishes {event} but no *{PERMSET_SUFFIX} or *{PROFILE_SUFFIX} under "
                f"{root} grants <allowCreate>true on {event}; at the API 67.0 user-mode default this "
                "rejects the publish for any running user without it (R9)"
            )
    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists() or not root.is_dir():
        return emit_result(
            [f"HIGH {root}: manifest directory not found"],
            "Scanned nothing; --manifest-dir does not point at a directory.",
            1,
        )

    apex_files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in APEX_SUFFIXES)
    object_files = sorted(p for p in root.rglob(f"*{OBJECT_SUFFIX}") if p.is_file())
    if not apex_files and not object_files:
        return emit_result(
            [],
            f"WARN: no .cls, .trigger or *{OBJECT_SUFFIX} files found under {root}; nothing to check.",
            0,
        )

    findings: list[str] = []
    for path in apex_files:
        findings.extend(audit_apex(path, str(path)))
    for path in object_files:
        findings.extend(audit_object(path, str(path)))
    findings.extend(audit_publish_permissions(apex_files, root))

    summary = (
        f"Scanned {len(apex_files)} Apex file(s) and {len(object_files)} object file(s); "
        f"{len(findings)} platform-event finding(s)."
    )
    blocking = findings if args.strict else [f for f in findings if not f.startswith("WARN ")]
    return emit_result(findings, summary, 1 if blocking else 0)


if __name__ == "__main__":
    sys.exit(main())
