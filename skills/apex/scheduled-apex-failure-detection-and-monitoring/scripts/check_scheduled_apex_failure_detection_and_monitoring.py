#!/usr/bin/env python3
"""Detect gaps in scheduled-Apex failure detection across an SFDX project.

Walks an SFDX-style metadata tree (force-app/) and reports:

1. Schedulable classes whose ``execute(SchedulableContext ...)`` body is not
   wrapped in a try-catch — the most common silent-failure source.
2. Database.Batchable classes that do NOT implement
   ``Database.RaisesPlatformEvents`` (so uncaught exceptions in their
   ``execute()`` produce no ``BatchApexErrorEvent``).
3. Whether the project contains at least one trigger on
   ``BatchApexErrorEvent`` — without it, even classes that DO implement
   ``RaisesPlatformEvents`` deliver to nowhere.
4. Whether the project contains a Schedulable class whose body queries
   ``AsyncApexJob`` — a heuristic for "is there a failure watcher".

Stdlib only — no pip dependencies.

Usage:
    python3 check_scheduled_apex_failure_detection_and_monitoring.py [--root force-app/main/default]

Exit codes:
    0  no findings
    1  findings present (informational, non-blocking)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# --- Pattern definitions ----------------------------------------------------

SCHEDULABLE_IMPL_RE = re.compile(
    r"\bimplements\b[^{]*\bSchedulable\b", re.IGNORECASE
)
BATCHABLE_IMPL_RE = re.compile(
    r"\bimplements\b[^{]*\bDatabase\.Batchable\b", re.IGNORECASE
)
RAISES_PE_RE = re.compile(
    r"\bDatabase\.RaisesPlatformEvents\b", re.IGNORECASE
)
SCHEDULABLE_EXECUTE_RE = re.compile(
    r"\bexecute\s*\(\s*SchedulableContext\s+\w+\s*\)\s*\{",
    re.IGNORECASE,
)
TRY_CATCH_RE = re.compile(r"\btry\b\s*\{", re.IGNORECASE)
ASYNC_APEX_JOB_QUERY_RE = re.compile(
    r"\bFROM\s+AsyncApexJob\b", re.IGNORECASE
)
TRIGGER_HEADER_RE = re.compile(
    r"\btrigger\s+\w+\s+on\s+BatchApexErrorEvent\b", re.IGNORECASE
)


# --- Helpers ----------------------------------------------------------------


def _read(fp: Path) -> str:
    try:
        return fp.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _strip_comments(text: str) -> str:
    """Crudely strip Apex // and /* */ comments so regexes don't match commented code."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", "", text)
    return text


def _execute_body_has_try(text: str, header_re: re.Pattern[str]) -> bool:
    """Return True if the first method matched by header_re contains a `try { ... }`.

    Brace-balance scan from the opening { of the matched header.
    """
    m = header_re.search(text)
    if not m:
        return False
    open_idx = text.find("{", m.end() - 1)
    if open_idx < 0:
        return False
    depth = 0
    body_start = open_idx
    body_end = open_idx
    for i in range(open_idx, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                body_end = i
                break
    body = text[body_start : body_end + 1]
    return bool(TRY_CATCH_RE.search(body))


# --- Detectors --------------------------------------------------------------


def find_schedulable_without_try(classes_dir: Path) -> list[tuple[Path, str]]:
    """Return (path, class_name) for each Schedulable class whose
    `execute(SchedulableContext ...)` body has no try-catch."""
    findings: list[tuple[Path, str]] = []
    if not classes_dir.exists():
        return findings
    for fp in classes_dir.rglob("*.cls"):
        raw = _read(fp)
        text = _strip_comments(raw)
        if not SCHEDULABLE_IMPL_RE.search(text):
            continue
        if not _execute_body_has_try(text, SCHEDULABLE_EXECUTE_RE):
            findings.append((fp, fp.stem))
    return findings


def find_batchable_without_raises(classes_dir: Path) -> list[tuple[Path, str]]:
    """Return (path, class_name) for each Database.Batchable class that does NOT
    implement Database.RaisesPlatformEvents."""
    findings: list[tuple[Path, str]] = []
    if not classes_dir.exists():
        return findings
    for fp in classes_dir.rglob("*.cls"):
        raw = _read(fp)
        text = _strip_comments(raw)
        if not BATCHABLE_IMPL_RE.search(text):
            continue
        if not RAISES_PE_RE.search(text):
            findings.append((fp, fp.stem))
    return findings


def has_batch_apex_error_event_trigger(triggers_dir: Path) -> tuple[bool, list[Path]]:
    """Return (present, paths). present is True iff at least one *.trigger
    file in the tree has a trigger declared on BatchApexErrorEvent."""
    paths: list[Path] = []
    if not triggers_dir.exists():
        return False, paths
    for fp in triggers_dir.rglob("*.trigger"):
        text = _strip_comments(_read(fp))
        if TRIGGER_HEADER_RE.search(text):
            paths.append(fp)
    return (bool(paths), paths)


def has_async_apex_job_watcher(classes_dir: Path) -> tuple[bool, list[Path]]:
    """Return (present, paths) for classes implementing Schedulable that
    contain a SOQL query on AsyncApexJob — a heuristic for a watcher."""
    paths: list[Path] = []
    if not classes_dir.exists():
        return False, paths
    for fp in classes_dir.rglob("*.cls"):
        text = _strip_comments(_read(fp))
        if SCHEDULABLE_IMPL_RE.search(text) and ASYNC_APEX_JOB_QUERY_RE.search(text):
            paths.append(fp)
    return (bool(paths), paths)


# --- CLI --------------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser(
        description=(
            "Audit an SFDX metadata tree for gaps in scheduled-Apex failure "
            "detection. Reports Schedulable classes without try-catch, "
            "Batchable classes without Database.RaisesPlatformEvents, "
            "missing BatchApexErrorEvent subscriber, and missing AsyncApexJob "
            "watcher."
        )
    )
    p.add_argument("--root", default="force-app/main/default")
    args = p.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"metadata root not found: {root}", file=sys.stderr)
        return 0

    classes_dir = root / "classes"
    triggers_dir = root / "triggers"

    findings_count = 0

    sched_no_try = find_schedulable_without_try(classes_dir)
    if sched_no_try:
        print(
            "\n## Schedulable classes whose execute(SchedulableContext) lacks try-catch"
        )
        print(
            "   Uncaught exceptions in async execute() do NOT email anyone — "
            "they only land in the debug log + ExtendedStatus."
        )
        for fp, name in sched_no_try:
            print(f"  - {fp.relative_to(root)}: class {name}")
        findings_count += len(sched_no_try)

    batch_no_raises = find_batchable_without_raises(classes_dir)
    if batch_no_raises:
        print(
            "\n## Database.Batchable classes WITHOUT Database.RaisesPlatformEvents"
        )
        print(
            "   Without this marker interface, the platform does not publish "
            "BatchApexErrorEvent on uncaught failures, so a subscriber trigger "
            "cannot detect them."
        )
        for fp, name in batch_no_raises:
            print(f"  - {fp.relative_to(root)}: class {name}")
        findings_count += len(batch_no_raises)

    has_subscriber, subscriber_paths = has_batch_apex_error_event_trigger(
        triggers_dir
    )
    if not has_subscriber:
        print(
            "\n## Missing BatchApexErrorEvent subscriber trigger"
        )
        print(
            "   No *.trigger file in the project subscribes to "
            "BatchApexErrorEvent. Even Batch classes that publish the event "
            "have nowhere to deliver to. Add one trigger that logs + notifies."
        )
        findings_count += 1
    else:
        print(
            "\nNote: BatchApexErrorEvent subscriber present at "
            + ", ".join(str(p.relative_to(root)) for p in subscriber_paths)
        )

    has_watcher, watcher_paths = has_async_apex_job_watcher(classes_dir)
    if not has_watcher:
        print(
            "\n## No AsyncApexJob watcher schedule detected"
        )
        print(
            "   No Schedulable class queries AsyncApexJob. Without a watcher, "
            "stuck-queued jobs, completed-with-errors batches, and Queueable "
            "failures are invisible. See the skill workflow step 4."
        )
        findings_count += 1
    else:
        print(
            "\nNote: AsyncApexJob watcher candidate(s): "
            + ", ".join(str(p.relative_to(root)) for p in watcher_paths)
        )

    if findings_count == 0:
        print(
            "\nAll three failure-detection layers appear to be in place "
            "(no gaps detected)."
        )
        return 0

    print(f"\nTotal findings: {findings_count}")
    print(
        "Refer to skills/apex/scheduled-apex-failure-detection-and-monitoring/SKILL.md "
        "for the recommended workflow."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
