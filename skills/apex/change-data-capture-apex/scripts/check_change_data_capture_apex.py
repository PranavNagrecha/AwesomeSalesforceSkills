#!/usr/bin/env python3
"""check_change_data_capture_apex.py — audit an Apex Change Data Capture subscriber slice.

Stdlib only. Point --manifest-dir at a source tree (for example force-app/main/default)
and it walks every .trigger, .cls, *.platformEventChannelMember-meta.xml and
*.field-meta.xml under it.

Severities
    ERROR     the slice is wrong and will misbehave in production
    WARN      likely wrong; suppressible only by a deliberate decision
    ADVISORY  worth a human look, too heuristic to gate on

Exit codes
    0  no ERROR findings (WARN/ADVISORY may be present), or nothing to scan
    1  at least one ERROR, or --manifest-dir does not exist
With --strict, WARN findings are promoted to ERROR and also cause exit 1.
ADVISORY findings never change the exit code.

Rules (each maps to a gotcha in ../references/gotchas.md or a section of SKILL.md):

  R1  ERROR     A trigger on a *ChangeEvent type declared with any event other than
                exactly `after insert`.
                -> apexdev L29634: the change event trigger sample is `after insert`;
                   the event is published after the transaction committed, so there is
                   no before phase to intercept.

  R2  ADVISORY  A change event body field is read (event.SomeField__c) without the same
                file testing changedFields / nulledFields / diffFields or changeType.
                -> apexrefguide L157381-157385: unchanged fields arrive null, which is
                   why nulledFields exists. The event is not a record snapshot.

  R3  WARN      recordIds treated as a single value: `recordIds[0]`, `getRecordIds()[0]`,
                or an (Id) cast of the whole list, with no iteration in the file.
                -> apexrefguide L157393-157397: Salesforce merges notifications, so one
                   event can carry every id that took the same change in one second.
                   apexrefguide L157413-157417: an entry can be a wildcard ('001*').

  R4  WARN      No branch for GAP_* / GAP_OVERFLOW in a file that routes on changeType.
                -> apexrefguide L157298-157304: GAP_CREATE, GAP_UPDATE, GAP_DELETE,
                   GAP_UNDELETE and GAP_OVERFLOW are real changeType values. A chain
                   without them drops the platform's own "I could not tell you what
                   changed" signal.

  R5  ERROR     SOQL, DML or System.enqueueJob inside a for-each loop over Trigger.new
                or over a *ChangeEvent collection.
                -> apexdev L19862: the batch is 2,000, against 100 SOQL / 150 DML
                   (apexdev L19542, L19553) and enqueueJob at 1 in an async context
                   (apexdev L19571). Bulkification detail lives in the skill, not here.

  R6  ERROR     A *ChangeEvent trigger exists in the tree but no test file calls
                Test.enableChangeDataCapture().
                -> apexrefguide L240419-240435: without it, change event notifications
                   are not generated for the test regardless of Setup, so a green test
                   asserts on an event that never arrived.

  R7  ADVISORY  A PlatformEventChannelMember names an enrichedFields field that has no
                matching *.field-meta.xml for the selected entity's object in the tree.
                Only raised when that object's folder is present.
                -> api_meta L96047-96050: enriched fields are named by field API name;
                   a typo deploys and then silently enriches nothing.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MDAPI_NS = "http://soap.sforce.com/2006/04/metadata"
MEMBER_SUFFIX = ".platformEventChannelMember-meta.xml"
FIELD_SUFFIX = ".field-meta.xml"

CHANGE_EVENT_TRIGGER_RE = re.compile(
    r"\btrigger\s+(\w+)\s+on\s+(\w*ChangeEvent)\s*\(([^)]*)\)", re.IGNORECASE
)
CHANGE_EVENT_TYPE_RE = re.compile(r"\b(\w*ChangeEvent)\b")
HEADER_VAR_RE = re.compile(r"EventBus\s*\.\s*ChangeEventHeader\s+(\w+)")
FOREACH_RE = re.compile(
    r"\bfor\s*\(\s*(\w[\w<>,\s]*?)\s+(\w+)\s*:\s*([^)]+?)\)\s*\{", re.IGNORECASE
)
SOQL_RE = re.compile(r"\[\s*SELECT\b|\bDatabase\s*\.\s*query\s*\(", re.IGNORECASE)
DML_RE = re.compile(
    r"\b(?:insert|update|upsert|delete|undelete)\s+[\w\[(]|\bDatabase\s*\.\s*(?:insert|update|upsert|delete|undelete)\s*\(",
    re.IGNORECASE,
)
ENQUEUE_RE = re.compile(r"\bSystem\s*\.\s*enqueueJob\s*\(", re.IGNORECASE)
GAP_RE = re.compile(r"GAP_", re.IGNORECASE)
CHANGETYPE_RE = re.compile(r"\bchangeType\b", re.IGNORECASE)
CHANGED_FIELDS_RE = re.compile(r"\b(?:changedFields|nulledFields|diffFields)\b", re.IGNORECASE)
ENABLE_CDC_RE = re.compile(r"\bTest\s*\.\s*enableChangeDataCapture\s*\(", re.IGNORECASE)
IS_TEST_RE = re.compile(r"@IsTest\b|\btestMethod\b", re.IGNORECASE)
SINGLE_RECORD_ID_RE = re.compile(
    r"(?:\.\s*recordIds\s*\[\s*0\s*\]|getRecordIds\s*\(\s*\)\s*\[\s*0\s*\]"
    r"|\(\s*Id\s*\)\s*\w+\s*\.\s*recordIds\b(?!\s*\[)"
    r"|\(\s*Id\s*\)\s*\w+\s*\.\s*getRecordIds\s*\(\s*\)(?!\s*\[))",
    re.IGNORECASE,
)
ITERATES_IDS_RE = re.compile(
    r"for\s*\([^)]*:\s*[^)]*(?:recordIds|getRecordIds\s*\(\s*\))[^)]*\)"
    r"|addAll\s*\(\s*[^)]*(?:recordIds|getRecordIds\s*\(\s*\))",
    re.IGNORECASE,
)
# a header field read that is NOT the header itself: event.Foo__c / evt.BillingCity
BODY_FIELD_READ_RE = re.compile(
    r"\b(\w+)\s*\.\s*(?!ChangeEventHeader\b|get\w|addAll\b|size\b|isEmpty\b|clone\b|put\b|get\b)"
    r"([A-Z][A-Za-z0-9]*(?:__c)?)\b"
)

APEX_SUFFIXES = {".cls", ".trigger"}


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Audit an Apex Change Data Capture subscriber slice (7 rules).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument(
        "--manifest-dir",
        required=True,
        help="Root of the Salesforce source tree to scan, e.g. force-app/main/default",
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Promote WARN findings to ERROR so they fail the run.",
    )
    return ap.parse_args()


def strip_apex(src: str, keep_strings: bool = False) -> str:
    """Blank comments and (unless keep_strings) string literals in one left-to-right pass,
    keeping length so that reported line numbers and brace matching stay meaningful.

    keep_strings=True is used for the GAP_ scan: `changeType.startsWith('GAP_')` puts the
    only evidence of a gap branch inside a string literal, so blanking strings would make
    every correct handler look like it has no gap branch.
    """
    out = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "'":
            j = i + 1
            while j < n and src[j] != "'":
                j += 2 if src[j] == "\\" else 1
            j = min(j, n - 1) if j < n else n
            out.append(src[i : j + 1] if keep_strings else " " * (j + 1 - i))
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
            out.append(" " * (j - i))
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def block_after(code: str, open_brace_index: int) -> str:
    """Return the text of the braced block that starts at open_brace_index."""
    depth = 0
    for i in range(open_brace_index, len(code)):
        if code[i] == "{":
            depth += 1
        elif code[i] == "}":
            depth -= 1
            if depth == 0:
                return code[open_brace_index + 1 : i]
    return code[open_brace_index + 1 :]


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def audit_apex(path: Path, rel: str) -> tuple[list[tuple[str, str]], dict]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    code = strip_apex(raw)
    # comments blanked, strings kept: the gap branch lives in a string literal
    code_with_strings = strip_apex(raw, keep_strings=True)
    findings: list[tuple[str, str]] = []
    facts = {
        "is_change_event_trigger": False,
        "mentions_change_event": bool(CHANGE_EVENT_TYPE_RE.search(code)),
        "is_test": bool(IS_TEST_RE.search(raw)),
        "enables_cdc": bool(ENABLE_CDC_RE.search(code)),
    }

    # ---- R1: trigger events -------------------------------------------------------------
    for m in CHANGE_EVENT_TRIGGER_RE.finditer(code):
        facts["is_change_event_trigger"] = True
        name, event_type, events = m.group(1), m.group(2), m.group(3)
        normalised = re.sub(r"\s+", " ", events.strip().lower())
        if normalised != "after insert":
            findings.append((
                "ERROR",
                f"{rel}:{line_of(code, m.start())}: trigger {name} on {event_type} is declared "
                f"({events.strip()}); a change event trigger supports exactly `after insert` (R1)",
            ))

    if not facts["mentions_change_event"] and not facts["enables_cdc"]:
        return findings, facts

    header_vars = set(HEADER_VAR_RE.findall(code))
    checks_fields = bool(CHANGED_FIELDS_RE.search(code))
    routes_on_change_type = bool(CHANGETYPE_RE.search(code))

    # ---- R2: body field read without a changedFields/changeType guard --------------------
    if facts["is_change_event_trigger"] or (facts["mentions_change_event"] and header_vars):
        event_vars = set()
        for m in FOREACH_RE.finditer(code):
            if CHANGE_EVENT_TYPE_RE.search(m.group(1)) or "Trigger.new" in m.group(3):
                event_vars.add(m.group(2))
        for m in BODY_FIELD_READ_RE.finditer(code):
            var, field = m.group(1), m.group(2)
            if var not in event_vars or var in header_vars:
                continue
            if not checks_fields and not routes_on_change_type:
                findings.append((
                    "ADVISORY",
                    f"{rel}:{line_of(code, m.start())}: reads {var}.{field} off the change event "
                    "without any changedFields / nulledFields / diffFields / changeType check in "
                    "this file; unchanged fields arrive null (R2)",
                ))
                break

    # ---- R3: recordIds treated as one id --------------------------------------------------
    if SINGLE_RECORD_ID_RE.search(code) and not ITERATES_IDS_RE.search(code):
        m = SINGLE_RECORD_ID_RE.search(code)
        findings.append((
            "WARN",
            f"{rel}:{line_of(code, m.start())}: recordIds is used as a single Id; one event can "
            "carry many ids (merged notifications) and an entry can be a wildcard like '001*' (R3)",
        ))

    # ---- R4: no GAP branch ----------------------------------------------------------------
    if routes_on_change_type and not GAP_RE.search(code_with_strings) and not facts["is_test"]:
        m = CHANGETYPE_RE.search(code)
        findings.append((
            "WARN",
            f"{rel}:{line_of(code, m.start())}: routes on changeType but has no GAP_ branch; "
            "GAP_CREATE/UPDATE/DELETE/UNDELETE and GAP_OVERFLOW are real values (R4)",
        ))

    # ---- R5: SOQL / DML / enqueueJob inside the event loop ---------------------------------
    if not facts["is_test"]:
        for m in FOREACH_RE.finditer(code):
            loop_type, _var, source = m.group(1), m.group(2), m.group(3)
            over_events = "Trigger.new" in source or bool(CHANGE_EVENT_TYPE_RE.search(loop_type))
            if not over_events:
                continue
            body = block_after(code, m.end() - 1)
            for rx, label in ((SOQL_RE, "SOQL"), (DML_RE, "DML"), (ENQUEUE_RE, "System.enqueueJob")):
                hit = rx.search(body)
                if hit:
                    findings.append((
                        "ERROR",
                        f"{rel}:{line_of(code, m.start())}: {label} inside the loop over the change "
                        "event collection; the batch is up to 2,000 events (R5)",
                    ))
                    break

    return findings, facts


def audit_channel_members(members: list[Path], field_names: dict[str, set], root: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for path in members:
        rel = str(path.relative_to(root))
        try:
            tree = ET.parse(path)
        except ET.ParseError as exc:
            findings.append(("ERROR", f"{rel}: malformed PlatformEventChannelMember XML — {exc}"))
            continue
        root_el = tree.getroot()

        def child_text(tag: str) -> str | None:
            node = root_el.find(f"{{{MDAPI_NS}}}{tag}")
            if node is None:
                node = root_el.find(tag)
            if node is None:
                return None
            return (node.text or "").strip()

        selected = child_text("selectedEntity")
        if not selected:
            findings.append(("ERROR", f"{rel}: PlatformEventChannelMember has no <selectedEntity> (R7)"))
            continue

        # AccountChangeEvent -> Account ; MyObject__ChangeEvent -> MyObject__c
        if selected.endswith("__ChangeEvent"):
            obj = selected[: -len("__ChangeEvent")] + "__c"
        elif selected.endswith("ChangeEvent"):
            obj = selected[: -len("ChangeEvent")]
        else:
            obj = None

        known = field_names.get(obj) if obj else None
        if known is None:
            continue  # object folder not in this tree; nothing to compare against

        enriched = []
        for node in root_el.findall(f"{{{MDAPI_NS}}}enrichedFields") + root_el.findall("enrichedFields"):
            name_node = node.find(f"{{{MDAPI_NS}}}name")
            if name_node is None:
                name_node = node.find("name")
            if name_node is not None and (name_node.text or "").strip():
                enriched.append((name_node.text or "").strip())

        for field in enriched:
            if field.endswith("__c") and field not in known:
                findings.append((
                    "ADVISORY",
                    f"{rel}: <enrichedFields><name>{field}</name> is not a field of {obj} in this "
                    "source tree; a typo deploys and then enriches nothing (R7)",
                ))
    return findings


def collect_object_fields(root: Path) -> dict[str, set]:
    """Map object API name -> set of custom field API names found under objects/<Obj>/fields/."""
    out: dict[str, set] = {}
    for path in root.rglob(f"*{FIELD_SUFFIX}"):
        parts = path.parts
        if "fields" not in parts:
            continue
        idx = parts.index("fields")
        if idx == 0:
            continue
        obj = parts[idx - 1]
        out.setdefault(obj, set()).add(path.name[: -len(FIELD_SUFFIX)])
    return out


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists() or not root.is_dir():
        print(f"ERROR {root}: --manifest-dir does not point at an existing directory")
        return 1

    apex_files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in APEX_SUFFIXES)
    members = sorted(p for p in root.rglob(f"*{MEMBER_SUFFIX}") if p.is_file())

    if not apex_files and not members:
        print(f"WARN: no .cls, .trigger or *{MEMBER_SUFFIX} files found under {root}; nothing to check.")
        return 0

    findings: list[tuple[str, str]] = []
    trigger_files: list[str] = []
    any_test_enables_cdc = False

    for path in apex_files:
        rel = str(path.relative_to(root))
        f, facts = audit_apex(path, rel)
        findings.extend(f)
        if facts["is_change_event_trigger"]:
            trigger_files.append(rel)
        if facts["enables_cdc"]:
            any_test_enables_cdc = True

    # ---- R6: a change event trigger in the tree with no test that enables CDC --------------
    if trigger_files and not any_test_enables_cdc:
        findings.append((
            "ERROR",
            f"{', '.join(trigger_files)}: a change event trigger is present but no file in the tree "
            "calls Test.enableChangeDataCapture(); without it a test's DML generates no change "
            "event and the assertions pass vacuously (R6)",
        ))

    findings.extend(audit_channel_members(members, collect_object_fields(root), root))

    if args.strict:
        findings = [("ERROR", msg) if sev == "WARN" else (sev, msg) for sev, msg in findings]

    order = {"ERROR": 0, "WARN": 1, "ADVISORY": 2}
    findings.sort(key=lambda f: (order[f[0]], f[1]))
    for sev, msg in findings:
        print(f"{sev} {msg}")

    errors = sum(1 for sev, _ in findings if sev == "ERROR")
    warns = sum(1 for sev, _ in findings if sev == "WARN")
    advisories = sum(1 for sev, _ in findings if sev == "ADVISORY")
    print(
        f"\nScanned {len(apex_files)} Apex file(s) and {len(members)} channel member(s) under {root}: "
        f"{errors} ERROR, {warns} WARN, {advisories} ADVISORY."
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
