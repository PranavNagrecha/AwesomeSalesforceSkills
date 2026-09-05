#!/usr/bin/env python3
"""Lint Apex that drives approval processes, against the processes actually deployed.

Stdlib only. Reads a DX metadata tree and reports findings as JSON on
stdout, in the same shape as the other checkers in this repo
(``{"score": int, "findings": [...], "summary": str}``).

Two halves, and the second is why ``--manifest-dir`` exists: the Apex
checks cross-reference the ``approvalProcesses/`` metadata in the same
tree, so a process name that appears only in a string literal is
detectable.

Metadata checks (``approvalProcesses/*.approvalProcess-meta.xml``)
-----------------------------------------------------------------
HIGH      ``active`` missing or not ``true`` while Apex in the tree
          names the process - submissions naming an inactive process
          fail (Object Reference, ``ProcessDefinition.State``).
HIGH      No ``approvalStep`` element at all.
MEDIUM    No ``recordEditability`` - the deployed process falls back to
          whatever the target org has rather than a declared value
          (Metadata API Developer Guide, ``ApprovalProcess``).
MEDIUM    ``allowRecall`` false while Apex in the tree calls
          ``setAction('Removed')`` - recall is administrator-only.
REVIEW    ``allowedSubmitters`` narrower than ``owner`` /
          ``allInternalUsers`` while Apex calls ``setSubmitterId`` -
          "the user must be one of the allowed submitters"
          (Apex Reference Guide, ``setSubmitterId``).

Apex checks (``*.cls`` / ``*.trigger``)
---------------------------------------
CRITICAL  A loop body that both constructs an
          ``Approval.Process*Request`` and calls ``Approval.process`` -
          one DML statement per record against a 150-statement
          transaction budget. The canonical chunking loop, which builds
          the request list in an earlier loop and calls
          ``Approval.process(chunk, false)`` once per chunk, is not
          flagged.
HIGH      ``setProcessDefinitionNameOrId`` with a literal record Id
          (``300...``) - not portable across orgs.
HIGH      ``setAction`` with a wrong-case or past-tense value; only
          ``Approve``, ``Reject`` and ``Removed`` are valid.
HIGH      A process developer name passed to
          ``setProcessDefinitionNameOrId`` that no approval process in
          the manifest defines.
MEDIUM    ``Approval.process(list)`` with no ``allOrNone`` argument -
          defaults to true, so one bad row rolls the batch back.
MEDIUM    ``Actor.IsActive`` / ``Actor.Username`` dereferenced without
          ``TYPEOF`` - ``ActorId`` is polymorphic over Group and User.
LOW       ``ProcessInstanceWorkitem`` or ``ProcessInstanceStep``
          filtered or ordered on ``CreatedDate``; the Object Reference
          field tables document ``ElapsedTimeInDays`` instead.

Usage
-----
    python3 check_approval_process_apex_patterns.py --manifest-dir force-app/main/default
    python3 check_approval_process_apex_patterns.py path/to/classes path/to/approvalProcesses
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PROCESS_SUFFIX = ".approvalProcess-meta.xml"
APEX_SUFFIXES = (".cls", ".trigger")
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}
SEVERITIES = tuple(SEVERITY_WEIGHTS)

WIDE_SUBMITTER_TYPES = {"owner", "creator", "allInternalUsers"}
VALID_ACTIONS = ("Approve", "Reject", "Removed")

# --- Apex patterns ---------------------------------------------------------

RE_PROCESS_NAME = re.compile(
    r"setProcessDefinitionNameOrId\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
)
RE_HARDCODED_ID = re.compile(r"^300[a-zA-Z0-9]{12,15}$")
RE_SET_ACTION = re.compile(r"setAction\s*\(\s*['\"]([^'\"]*)['\"]\s*\)")
RE_SET_SUBMITTER = re.compile(r"setSubmitterId\s*\(")
RE_PROCESS_CALL = re.compile(r"Approval\s*\.\s*process\s*\(")
RE_NEW_REQUEST = re.compile(
    r"new\s+Approval\s*\.\s*Process(Submit|Workitem)Request\s*\(", re.IGNORECASE
)
RE_ACTOR_FIELD = re.compile(r"\bActor\s*\.\s*(IsActive|Username|Name|Email)\b")
RE_TYPEOF = re.compile(r"\bTYPEOF\b", re.IGNORECASE)
RE_WORKITEM_SOQL = re.compile(
    r"FROM\s+(ProcessInstanceWorkitem|ProcessInstanceStep)\b", re.IGNORECASE
)
RE_CREATEDDATE = re.compile(r"\bCreatedDate\b")
RE_LOOP_OPEN = re.compile(r"\b(for|while)\s*\(")
RE_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
RE_LINE_COMMENT = re.compile(r"//[^\n]*")


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def child(element: ET.Element | None, name: str) -> ET.Element | None:
    """First direct child named ``name``.

    A leaf ``Element`` is falsy, so every caller must compare against
    None. Never write ``el.find(a) or el.find(b)``.
    """
    if element is None:
        return None
    for candidate in element:
        if local_name(candidate.tag) == name:
            return candidate
    return None


def children(element: ET.Element | None, name: str) -> list[ET.Element]:
    if element is None:
        return []
    return [c for c in element if local_name(c.tag) == name]


def text_of(element: ET.Element | None, name: str) -> str:
    found = child(element, name)
    if found is None or found.text is None:
        return ""
    return found.text.strip()


def strip_comments(text: str) -> str:
    """Blank out comments while preserving line numbering."""

    def blank(match: re.Match[str]) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    return RE_LINE_COMMENT.sub(blank, RE_BLOCK_COMMENT.sub(blank, text))


def line_no(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def process_name_of(path: Path) -> str:
    """``Expense__c.Expense_Approval.approvalProcess-meta.xml`` -> Expense_Approval."""
    stem = path.name[: -len(PROCESS_SUFFIX)]
    return stem.split(".", 1)[1] if "." in stem else stem


# --- collection ------------------------------------------------------------


def iter_files(paths: list[Path], suffixes: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            for suffix in suffixes:
                files.extend(c for c in path.rglob(f"*{suffix}") if c.is_file())
        elif path.is_file() and path.name.endswith(suffixes):
            files.append(path)
    return sorted(set(files))


def load_processes(files: list[Path]) -> tuple[dict[str, dict], list[str]]:
    """Parse each approval process into a small summary dict."""
    processes: dict[str, dict] = {}
    findings: list[str] = []
    for path in files:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            findings.append(f"HIGH {path}: not well-formed XML ({exc})")
            continue

        submitter_types = {
            text_of(node, "type")
            for node in children(root, "allowedSubmitters")
            if text_of(node, "type")
        }
        processes[process_name_of(path)] = {
            "path": path,
            "active": text_of(root, "active").lower() == "true",
            "has_active_element": child(root, "active") is not None,
            "allow_recall": text_of(root, "allowRecall").lower() == "true",
            "has_allow_recall": child(root, "allowRecall") is not None,
            "steps": len(children(root, "approvalStep")),
            "record_editability": text_of(root, "recordEditability"),
            "submitter_types": submitter_types,
        }
    return processes, findings


# --- Apex scanning ---------------------------------------------------------


def match_close(text: str, open_pos: int, opener: str, closer: str) -> int:
    """Index just past the ``closer`` matching the ``opener`` at ``open_pos``."""
    depth = 0
    for i in range(open_pos, len(text)):
        if text[i] == opener:
            depth += 1
        elif text[i] == closer:
            depth -= 1
            if depth == 0:
                return i + 1
    return len(text)


def loop_body_spans(text: str) -> list[tuple[int, int]]:
    """``(start, end)`` offsets of every ``for`` / ``while`` body in ``text``.

    Spans nest: an inner loop yields its own span as well as being
    contained in the outer one. Callers therefore see the innermost
    enclosing body for any offset, which is what the per-record DML check
    wants.
    """
    spans: list[tuple[int, int]] = []
    for match in RE_LOOP_OPEN.finditer(text):
        header_end = match_close(text, match.end() - 1, "(", ")")
        cursor = header_end
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor >= len(text):
            continue
        if text[cursor] == "{":
            spans.append((cursor, match_close(text, cursor, "{", "}")))
        else:
            # single-statement body, up to and including the semicolon
            end = text.find(";", cursor)
            spans.append((cursor, len(text) if end == -1 else end + 1))
    return spans


def per_record_dml_loops(text: str) -> list[int]:
    """Offsets of ``Approval.process`` calls that run once per record.

    A loop body that constructs a request *and* processes it does one DML
    statement per iteration. A chunking loop - request list built earlier,
    ``Approval.process(chunk, false)`` called once per slice - does not
    construct requests inside the processing loop and is not reported.
    """
    offsets: list[int] = []
    for start, end in loop_body_spans(text):
        body = text[start:end]
        if not RE_NEW_REQUEST.search(body):
            continue
        for call in RE_PROCESS_CALL.finditer(body):
            offsets.append(start + call.start())
    return sorted(set(offsets))


def balanced_call_args(text: str, open_paren: int) -> str:
    """Return the argument text of a call whose '(' is at ``open_paren``."""
    depth = 0
    for i in range(open_paren, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[open_paren + 1 : i]
    return ""


def scan_apex(path: Path, processes: dict[str, dict], resolve: bool) -> tuple[list[str], set[str], set[str]]:
    findings: list[str] = []
    named: set[str] = set()
    actions: set[str] = set()
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"HIGH could not read {path}: {exc}"], named, actions
    text = strip_comments(raw)

    for match in RE_PROCESS_NAME.finditer(text):
        name = match.group(1).strip()
        named.add(name)
        where = f"{path}:{line_no(text, match.start())}"
        if RE_HARDCODED_ID.match(name):
            findings.append(
                f"HIGH {where}: setProcessDefinitionNameOrId uses the literal record Id "
                f"`{name}`. Approval-process record Ids differ per org and per sandbox "
                "refresh; pass the developer name instead (gotchas.md gotcha 1)"
            )
        elif resolve and name not in processes:
            known = ", ".join(sorted(processes)) or "none"
            findings.append(
                f"HIGH {where}: setProcessDefinitionNameOrId('{name}') names a process "
                f"that no approvalProcess metadata in this tree defines (found: {known}). "
                "A submission naming a process that is absent or inactive fails "
                "(gotchas.md gotcha 14)"
            )

    for match in RE_SET_ACTION.finditer(text):
        value = match.group(1)
        actions.add(value)
        if value not in VALID_ACTIONS:
            findings.append(
                f"HIGH {path}:{line_no(text, match.start())}: setAction('{value}') is not "
                "a valid action. The Apex Reference lists exactly Approve, Reject and "
                "Removed, and only system administrators can specify Removed "
                "(gotchas.md gotchas 4 and 5)"
            )

    for offset in per_record_dml_loops(text):
        findings.append(
            f"CRITICAL {path}:{line_no(text, offset)}: this loop body both constructs an "
            "Approval request and calls Approval.process, so it issues one DML statement "
            "per record against a 150-statement transaction budget. Build the request "
            "list in one loop, then call Approval.process(chunk, false) per chunk "
            "(gotchas.md gotcha 7)"
        )

    for match in RE_PROCESS_CALL.finditer(text):
        where = f"{path}:{line_no(text, match.start())}"
        open_paren = match.end() - 1
        args = balanced_call_args(text, open_paren)
        top_level_commas = 0
        depth = 0
        for ch in args:
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            elif ch == "," and depth == 0:
                top_level_commas += 1

        if top_level_commas == 0 and args.strip():
            findings.append(
                f"MEDIUM {where}: Approval.process(...) called without an allOrNone "
                "argument, which defaults to true - one failing row rolls the whole call "
                "back. Pass false and read the per-row ProcessResults "
                "(gotchas.md gotcha 2)"
            )

    if RE_WORKITEM_SOQL.search(text):
        for match in RE_ACTOR_FIELD.finditer(text):
            # TYPEOF anywhere in the file is treated as handled; the point
            # is to catch code that has never heard of the polymorphism.
            if not RE_TYPEOF.search(text):
                findings.append(
                    f"MEDIUM {path}:{line_no(text, match.start())}: Actor.{match.group(1)} "
                    "dereferenced with no TYPEOF in the file. ActorId on "
                    "ProcessInstanceWorkitem and ProcessInstanceStep is polymorphic over "
                    "Group and User, so a queue-assigned request has no user at all "
                    "(gotchas.md gotcha 13)"
                )
                break
        if RE_CREATEDDATE.search(text):
            match = RE_CREATEDDATE.search(text)
            assert match is not None
            findings.append(
                f"LOW {path}:{line_no(text, match.start())}: CreatedDate used alongside a "
                "ProcessInstanceWorkitem / ProcessInstanceStep query. The Object Reference "
                "field tables for these objects document ElapsedTimeInDays / InHours / "
                "InMinutes as the filterable, sortable aging fields "
                "(gotchas.md gotcha 13)"
            )

    return findings, named, actions


# --- metadata auditing -----------------------------------------------------


def audit_processes(
    processes: dict[str, dict],
    named_in_apex: set[str],
    actions_in_apex: set[str],
    submitter_set_in_apex: bool,
) -> list[str]:
    findings: list[str] = []
    for name, info in sorted(processes.items()):
        path = info["path"]
        referenced = name in named_in_apex

        if not info["has_active_element"]:
            findings.append(
                f"HIGH {path}: no <active> element. It is a required field on "
                "ApprovalProcess and the deploy will not set a value"
            )
        elif not info["active"] and referenced:
            findings.append(
                f"HIGH {path}: <active>false</active> while Apex in this tree submits to "
                f"'{name}'. ProcessDefinition.State must be Active for the submission to "
                "resolve (gotchas.md gotcha 14)"
            )

        if info["steps"] == 0:
            findings.append(
                f"HIGH {path}: no <approvalStep> defined, so nothing can be approved. "
                "Each process supports up to 30 steps"
            )

        if not info["record_editability"]:
            findings.append(
                f"MEDIUM {path}: no <recordEditability>. Declare AdminOnly or "
                "AdminOrCurrentApprover explicitly rather than inheriting whatever the "
                "target org already has"
            )

        if "Removed" in actions_in_apex and info["has_allow_recall"] and not info["allow_recall"]:
            findings.append(
                f"MEDIUM {path}: <allowRecall>false</allowRecall> while Apex in this tree "
                "calls setAction('Removed'). Recall is administrator-only in that "
                "configuration (gotchas.md gotcha 5)"
            )

        if submitter_set_in_apex and not (info["submitter_types"] & WIDE_SUBMITTER_TYPES):
            listed = ", ".join(sorted(info["submitter_types"])) or "none"
            findings.append(
                f"REVIEW {path}: Apex in this tree calls setSubmitterId, but "
                f"allowedSubmitters is limited to [{listed}] with no owner / creator / "
                "allInternalUsers entry. Any submitter outside that list fails its row "
                "(gotchas.md gotcha 11)"
            )
    return findings


# --- output ----------------------------------------------------------------


def normalize_finding(finding: str) -> dict:
    severity, _, message = finding.partition(" ")
    if severity not in SEVERITIES:
        severity, message = "REVIEW", finding
    return {"severity": severity, "message": message.strip()}


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(f) for f in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(i["severity"], 0) for i in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Lint approval-process Apex against the approval processes deployed "
            "alongside it in a DX metadata tree."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or directories to scan (alternative to --manifest-dir)",
    )
    parser.add_argument(
        "--manifest-dir",
        help="DX metadata root, e.g. force-app/main/default; scans approvalProcesses/ "
        "and every .cls / .trigger under it, and resolves Apex process names against "
        "the deployed metadata",
    )
    args = parser.parse_args()

    root_dir: Path | None = None
    targets: list[Path] = [Path(p) for p in args.paths]
    if args.manifest_dir:
        root_dir = Path(args.manifest_dir)
        if not root_dir.exists():
            return emit_result(
                [f"HIGH --manifest-dir does not exist: {root_dir}"],
                f"Could not read {root_dir}.",
            )
        targets.append(root_dir)
    if not targets:
        parser.error("provide one or more paths, or --manifest-dir")

    process_files = iter_files(targets, (PROCESS_SUFFIX,))
    apex_files = iter_files(targets, APEX_SUFFIXES)

    if not process_files and not apex_files:
        return emit_result(
            ["HIGH no approval-process metadata and no Apex files found"],
            "Scanned 0 files; nothing matched the provided paths.",
        )

    processes, findings = load_processes(process_files)
    resolve = bool(process_files)

    named_in_apex: set[str] = set()
    actions_in_apex: set[str] = set()
    submitter_set = False
    for path in apex_files:
        apex_findings, named, actions = scan_apex(path, processes, resolve)
        findings.extend(apex_findings)
        named_in_apex |= named
        actions_in_apex |= actions
        try:
            if RE_SET_SUBMITTER.search(strip_comments(path.read_text(encoding="utf-8", errors="ignore"))):
                submitter_set = True
        except OSError:
            pass

    findings.extend(audit_processes(processes, named_in_apex, actions_in_apex, submitter_set))

    notes: list[str] = []
    if not resolve:
        notes.append(
            "no approvalProcess metadata in scope, so Apex process names were not resolved"
        )
    if not apex_files:
        notes.append("no Apex files in scope, so only the metadata was audited")
    suffix = f" Note: {'; '.join(notes)}." if notes else ""

    summary = (
        f"Scanned {len(process_files)} approval-process file(s) and {len(apex_files)} "
        f"Apex file(s); {len(findings)} finding(s) detected.{suffix}"
    )
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
