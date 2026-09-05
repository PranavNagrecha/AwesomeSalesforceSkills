#!/usr/bin/env python3
"""Checker script for the Standard Object Quirks skill.

Scans an SFDX source tree for the standard-object quirks this skill documents.
Every rule below traces to a sentence in an official guide, cited in the message
it emits, so a finding can be argued with rather than merely obeyed.

Rules
-----
1. Contact triggers/handlers that reference IsPersonAccount.
   "Inserts, updates, and deletes on person accounts fire Account triggers, not
   Contact triggers" (Apex Developer Guide, Operations That Don't Invoke
   Triggers). A person-account guard inside a Contact trigger defends against an
   event that never fires, and usually means the Account-side logic is missing.

2. Event DML with neither DurationInMinutes nor EndDateTime.
   "If IsAllDayEvent is false, a value must be supplied for either
   DurationInMinutes or EndDateTime" (Object Reference, Event). Only the
   neither-field case fails, so this checker flags exactly that -- it does NOT
   flag duration-only inserts, which are valid.

3. merge / Database.merge with more than two losing records.
   "You can pass a main record and up to two additional sObject records to a
   single merge method" (Apex Developer Guide, Merge Considerations). Flags list
   literals of 3+ elements, and unguarded list variables as a weaker warning.

4. MasterRecordId read in a `before delete` context.
   "The MasterRecordId field is only set in after delete trigger events"
   (Apex Developer Guide, Triggers and Merge Statements).

5. TaskStatus standard value set with no value flagged closed.
   Task.CompletedDateTime is "the date and time the task was saved with a Closed
   status" (Object Reference, Task). A value set with no <closed>true</closed>
   leaves the field permanently null.

6. Task completion filters that hard-code Status = 'Completed', or that use
   ActivityDate ("the due date") as a completion date.

7. Polymorphic dot-notation on Who./What. for type-specific fields, and bare
   Email in an Account SOQL SELECT (Account has no Email field; person account
   email is PersonEmail, whose UI label is "Email").

Uses stdlib only -- no pip dependencies. Reads source; never contacts an org.

Usage:
    python3 check_standard_object_quirks.py --manifest-dir force-app/main/default
    python3 check_standard_object_quirks.py --manifest-dir . --format json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = "{http://soap.sforce.com/2006/04/metadata}"

# Fields that resolve on the generic Name/parent polymorphic relationship.
POLY_SAFE_FIELDS = {"Name", "Type", "Id"}

APEX_SUFFIXES = (".cls", ".trigger")


class Issue:
    """One finding, carrying the source sentence that justifies it."""

    __slots__ = ("path", "line", "rule", "message", "severity")

    def __init__(
        self,
        path: str,
        line: int,
        rule: str,
        message: str,
        severity: str = "ERROR",
    ) -> None:
        self.path = path
        self.line = line
        self.rule = rule
        self.message = message
        self.severity = severity

    def as_dict(self) -> dict:
        return {
            "path": self.path,
            "line": self.line,
            "rule": self.rule,
            "severity": self.severity,
            "message": self.message,
        }

    def __str__(self) -> str:
        return f"{self.severity} [{self.rule}] {self.path}:{self.line} — {self.message}"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check an SFDX source tree for Salesforce standard-object quirks "
            "(person-account triggers, Event duration contract, merge caps, "
            "Task closed-status handling, polymorphic lookups)."
        )
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the source tree to scan (default: current directory).",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Exit non-zero on WARN findings as well as ERROR findings.",
    )
    return parser.parse_args(argv)


def _read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _strip_apex_comments(content: str) -> str:
    """Blank out // and /* */ comments, preserving line structure.

    Comments are where the folklore lives, so a few rules deliberately run over
    the *raw* text instead. Rules that reason about code run over this.
    """
    out = re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), content, flags=re.S)
    out = re.sub(r"//[^\n]*", lambda m: " " * len(m.group(0)), out)
    return out


def _find_child(element, tag: str):
    """Namespace-tolerant single-child lookup.

    A leaf Element is falsy, so `a.find(x) or a.find(y)` silently discards a real
    match. Every lookup here tests `is not None` explicitly.
    """
    child = element.find(MD_NS + tag)
    if child is None:
        child = element.find(tag)
    return child


def _find_children(element, tag: str) -> list:
    found = element.findall(MD_NS + tag)
    if not found:
        found = element.findall(tag)
    return found


def _child_text(element, tag: str) -> str:
    child = _find_child(element, tag)
    if child is None:
        return ""
    return (child.text or "").strip()


def _line_of(content: str, index: int) -> int:
    return content.count("\n", 0, index) + 1


def _trigger_sobject(content: str) -> str:
    """Return the sObject a .trigger file is declared on, or ''."""
    m = re.search(r"\btrigger\s+\w+\s+on\s+(\w+)\s*\(", content, re.IGNORECASE)
    return m.group(1) if m else ""


# --------------------------------------------------------------------------- #
# rule 1 — person-account logic on the Contact side
# --------------------------------------------------------------------------- #


def check_contact_person_account_guard(content: str, path: str) -> list[Issue]:
    issues: list[Issue] = []
    lowered_path = path.lower()
    sobject = _trigger_sobject(content)

    is_contact_context = (
        sobject.lower() == "contact"
        or "contacttrigger" in lowered_path.replace("_", "")
        or bool(re.search(r"\bclass\s+Contact\w*Handler\b", content))
    )
    if not is_contact_context:
        return issues

    for m in re.finditer(r"\bIsPersonAccount\b", content):
        issues.append(
            Issue(
                path,
                _line_of(content, m.start()),
                "person-account-on-contact",
                "IsPersonAccount referenced in a Contact trigger context. Person-account "
                "inserts, updates and deletes fire Account triggers, NOT Contact triggers "
                "(Apex Developer Guide, 'Operations That Don't Invoke Triggers'). This code "
                "never runs for person accounts — move the logic to an Account handler.",
            )
        )
    return issues


# --------------------------------------------------------------------------- #
# rule 2 — Event DML with neither duration form
# --------------------------------------------------------------------------- #


def check_event_duration_contract(content: str, path: str) -> list[Issue]:
    """Flag Event construction that supplies NEITHER duration form.

    Duration-only is valid and is deliberately not flagged: "a value must be
    supplied for either DurationInMinutes or EndDateTime" (Object Reference).
    """
    issues: list[Issue] = []
    code = _strip_apex_comments(content)

    # Constructor form: new Event(a = b, c = d)
    for m in re.finditer(r"\bnew\s+Event\s*\((?P<args>[^;]*?)\)\s*;", code, re.S):
        args = m.group("args")
        if _event_args_ok(args):
            continue
        issues.append(
            Issue(
                path,
                _line_of(code, m.start()),
                "event-duration-contract",
                "Event constructed with neither DurationInMinutes nor EndDateTime. When "
                "IsAllDayEvent is false the API requires ONE of the two (Object Reference, "
                "Event.DurationInMinutes / Event.EndDateTime). Supplying only "
                "DurationInMinutes is valid — supplying neither is not.",
            )
        )

    # Assignment form: Event e = new Event(); e.Subject = ...; insert e;
    for m in re.finditer(
        r"\bnew\s+Event\s*\(\s*\)\s*;(?P<body>.*?)\b(?:insert|upsert|Database\.insert)\b",
        code,
        re.S,
    ):
        body = m.group("body")
        if _event_args_ok(body):
            continue
        if "IsAllDayEvent" in body:
            continue
        issues.append(
            Issue(
                path,
                _line_of(code, m.start()),
                "event-duration-contract",
                "Event inserted with neither DurationInMinutes nor EndDateTime assigned. "
                "One of the two is required when IsAllDayEvent is false (Object Reference, "
                "Event).",
            )
        )
    return issues


def _event_args_ok(fragment: str) -> bool:
    has_duration = re.search(r"\bDurationInMinutes\b", fragment) is not None
    has_end = re.search(r"\bEndDateTime\b", fragment) is not None
    all_day = re.search(r"\bIsAllDayEvent\s*=\s*true\b", fragment, re.IGNORECASE) is not None
    return has_duration or has_end or all_day


# --------------------------------------------------------------------------- #
# rule 3 — merge record cap
# --------------------------------------------------------------------------- #


def check_merge_record_cap(content: str, path: str) -> list[Issue]:
    """Flag merges passing more than two losing records."""
    issues: list[Issue] = []
    code = _strip_apex_comments(content)

    pattern = re.compile(
        r"\b(?:Database\.merge|merge)\s*\(?\s*(?P<rest>[^;]{0,400});",
        re.S,
    )
    for m in pattern.finditer(code):
        rest = m.group("rest")
        line = _line_of(code, m.start())

        literal = re.search(r"new\s+List<\w+>\s*\{(?P<items>[^}]*)\}", rest, re.S)
        if literal is not None:
            items = [i for i in literal.group("items").split(",") if i.strip()]
            if len(items) > 2:
                issues.append(
                    Issue(
                        path,
                        line,
                        "merge-record-cap",
                        f"merge called with {len(items)} losing records in a list literal. "
                        "A single merge takes a main record and AT MOST TWO additional "
                        "records (Apex Developer Guide, 'Merge Considerations'; App Limits "
                        "cheat sheet: three per request including the master). Split into "
                        "successive merges.",
                    )
                )
            continue

        # Bare list variable with no visible slicing/size guard nearby.
        if re.search(r",\s*[A-Za-z_]\w*(?:List|s)\b", rest) and not re.search(
            r"\bMath\.min\b|\bsize\(\)\b|\bsublist\b|\bslice\b", code, re.IGNORECASE
        ):
            issues.append(
                Issue(
                    path,
                    line,
                    "merge-record-cap",
                    "merge called with an unbounded list variable and no size guard found "
                    "in this file. The cap is a main record plus two others (Apex Developer "
                    "Guide, 'Merge Considerations'). Confirm the list can never exceed two.",
                    severity="WARN",
                )
            )
    return issues


# --------------------------------------------------------------------------- #
# rule 4 — MasterRecordId in before delete
# --------------------------------------------------------------------------- #


def check_master_record_id_context(content: str, path: str) -> list[Issue]:
    issues: list[Issue] = []
    code = _strip_apex_comments(content)
    if "MasterRecordId" not in code:
        return issues

    declares_before_delete = re.search(r"\bbefore\s+delete\b", code, re.IGNORECASE) is not None
    declares_after_delete = re.search(r"\bafter\s+delete\b", code, re.IGNORECASE) is not None
    guarded = re.search(r"Trigger\.isAfter", code) is not None

    if declares_before_delete and not (declares_after_delete or guarded):
        m = re.search(r"\bMasterRecordId\b", code)
        issues.append(
            Issue(
                path,
                _line_of(code, m.start()) if m else 1,
                "masterrecordid-context",
                "MasterRecordId read in a file whose only delete context is 'before delete'. "
                "The field 'is only set in after delete trigger events' (Apex Developer "
                "Guide, 'Triggers and Merge Statements'), so this reads null on every row.",
            )
        )
    return issues


# --------------------------------------------------------------------------- #
# rule 5 — TaskStatus value set with no closed value
# --------------------------------------------------------------------------- #


def check_task_status_value_set(path: Path, rel_path: str) -> list[Issue]:
    issues: list[Issue] = []
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        return [
            Issue(
                rel_path,
                1,
                "value-set-unparseable",
                f"Could not parse StandardValueSet XML: {exc}",
                severity="WARN",
            )
        ]

    values = _find_children(root, "standardValue")
    if not values:
        return [
            Issue(
                rel_path,
                1,
                "value-set-empty",
                "StandardValueSet has no <standardValue> entries. A deployed value set "
                "'must contain at least one picklist value. Otherwise, you receive an "
                "error' (Metadata API Developer Guide, StandardValueSet).",
            )
        ]

    closed_values = []
    for value in values:
        if _child_text(value, "closed").lower() == "true":
            closed_values.append(_child_text(value, "fullName"))

    if not closed_values:
        issues.append(
            Issue(
                rel_path,
                1,
                "task-status-no-closed",
                f"TaskStatus value set defines {len(values)} value(s) but none is flagged "
                "<closed>true</closed>. Task.CompletedDateTime is 'the date and time the "
                "task was saved with a Closed status' (Object Reference, Task), so it will "
                "never populate and IsClosed will never be true.",
            )
        )
    elif len(closed_values) > 1:
        issues.append(
            Issue(
                rel_path,
                1,
                "task-status-multiple-closed",
                "TaskStatus flags more than one value as closed ("
                + ", ".join(closed_values)
                + "). This is legitimate, but any query filtering on "
                "Status = 'Completed' will undercount — filter on "
                "CompletedDateTime != null instead.",
                severity="WARN",
            )
        )
    return issues


# --------------------------------------------------------------------------- #
# rule 6 — Task completion filters
# --------------------------------------------------------------------------- #


def check_task_completion_filters(content: str, path: str) -> list[Issue]:
    issues: list[Issue] = []
    lines = content.splitlines()

    for i in range(len(lines)):
        window = " ".join(lines[max(0, i - 3) : i + 4])
        lowered = window.lower()
        if "from task" not in lowered:
            continue

        if "activitydate" in lowered and "completeddatetime" not in lowered:
            if re.search(r"completed|isclosed", lowered):
                issues.append(
                    Issue(
                        path,
                        i + 1,
                        "task-activitydate-as-completion",
                        "Task query treats ActivityDate as a completion date. ActivityDate "
                        "'represents the due date of the task' and is labelled Due Date "
                        "(Object Reference, Task). Use CompletedDateTime.",
                    )
                )
                break

    for m in re.finditer(r"Status\s*=\s*'Completed'", content):
        line = _line_of(content, m.start())
        context = "\n".join(
            content.splitlines()[max(0, line - 6) : line + 5]
        ).lower()
        if "task" not in context:
            continue
        issues.append(
            Issue(
                path,
                line,
                "task-completed-literal",
                "Task filtered on the literal Status = 'Completed'. CompletedDateTime "
                "follows the Closed status CATEGORY, not that value (Object Reference, "
                "Task). An org with a second closed status (e.g. 'Closed - No Action') "
                "will be undercounted. Prefer CompletedDateTime != null.",
                severity="WARN",
            )
        )
    return issues


# --------------------------------------------------------------------------- #
# rule 7 — polymorphic dot-notation and bare Account.Email
# --------------------------------------------------------------------------- #


def check_polymorphic_dot_notation(content: str, path: str) -> list[Issue]:
    issues: list[Issue] = []
    pattern = re.compile(r"\b(Who|What)\.(\w+)")
    for i, line in enumerate(content.splitlines(), 1):
        for match in pattern.finditer(line):
            field = match.group(2)
            if field in POLY_SAFE_FIELDS:
                continue
            issues.append(
                Issue(
                    path,
                    i,
                    "polymorphic-dot-notation",
                    f"Polymorphic dot-notation '{match.group(0)}'. WhoId and WhatId are "
                    "polymorphic (Object Reference, Task.WhoId / Task.WhatId); only Name, "
                    "Type and Id resolve on the parent. Use TYPEOF or an explicit type "
                    "filter.",
                )
            )
    return issues


def check_account_bare_email(content: str, path: str) -> list[Issue]:
    issues: list[Issue] = []
    for match in re.finditer(
        r"SELECT\s+(?P<fields>.+?)\s+FROM\s+Account\b", content, re.IGNORECASE | re.DOTALL
    ):
        select_clause = match.group("fields")
        if re.search(r"(?<![A-Za-z])Email\b", select_clause) and not re.search(
            r"Person\s*Email", select_clause, re.IGNORECASE
        ):
            issues.append(
                Issue(
                    path,
                    _line_of(content, match.start()),
                    "account-bare-email",
                    "Account SOQL selects a bare 'Email' field. Account has no such field; "
                    "person account email is PersonEmail, whose UI label is 'Email' "
                    "(Object Reference, Account.PersonEmail).",
                )
            )
    return issues


def check_person_account_schema_token(content: str, path: str) -> list[Issue]:
    issues: list[Issue] = []
    # Comments legitimately quote the forbidden token when explaining the rule,
    # so this rule reads code only.
    code = _strip_apex_comments(content)
    for m in re.finditer(r"Schema\.Account\.(?:fields\.)?(Person\w+)", code):
        issues.append(
            Issue(
                path,
                _line_of(code, m.start()),
                "person-account-schema-token",
                f"Schema field token used for a person account field ('{m.group(1)}'). "
                "'Field tokens aren't available for person accounts. If you access "
                "Schema.Account.fieldname, you get an exception error. Instead, specify "
                "the field name as a string' (Apex Developer Guide).",
            )
        )
    return issues


def check_person_account_name_write(content: str, path: str) -> list[Issue]:
    issues: list[Issue] = []
    code = _strip_apex_comments(content)
    if "IsPersonAccount" not in code:
        return issues
    for m in re.finditer(r"\b(\w+)\.Name\s*=\s*", code):
        var = m.group(1)
        if var in {"this", "e", "ex"}:
            continue
        # A write guarded by an explicit business-account branch is correct, not
        # suspect. Look back a few lines for `else` or a negated IsPersonAccount.
        preceding = code[max(0, m.start() - 400) : m.start()]
        tail = "\n".join(preceding.splitlines()[-8:])
        if re.search(r"\belse\b|!\s*\w+\.IsPersonAccount", tail):
            continue
        issues.append(
            Issue(
                path,
                _line_of(code, m.start()),
                "person-account-name-write",
                f"Assignment to {var}.Name in a file that also branches on IsPersonAccount. "
                "'If an Account record has a record type of Person Account, the Name field "
                "can't be modified with DML operations' (Apex Developer Guide). Confirm "
                "this path is business-account only, or write FirstName/LastName.",
                severity="WARN",
            )
        )
    return issues


# --------------------------------------------------------------------------- #
# driver
# --------------------------------------------------------------------------- #


def check_standard_object_quirks(manifest_dir: Path) -> list[Issue]:
    issues: list[Issue] = []

    if not manifest_dir.exists():
        return [
            Issue(
                str(manifest_dir),
                1,
                "manifest-dir-missing",
                f"Manifest directory not found: {manifest_dir}",
            )
        ]

    apex_files = sorted(
        p
        for suffix in APEX_SUFFIXES
        for p in manifest_dir.rglob(f"*{suffix}")
        if "__pycache__" not in p.parts
    )

    for apex_file in apex_files:
        rel = str(apex_file.relative_to(manifest_dir))
        content = _read_text_safe(apex_file)
        if not content:
            continue

        issues.extend(check_contact_person_account_guard(content, rel))
        issues.extend(check_event_duration_contract(content, rel))
        issues.extend(check_merge_record_cap(content, rel))
        issues.extend(check_master_record_id_context(content, rel))
        issues.extend(check_task_completion_filters(content, rel))
        issues.extend(check_polymorphic_dot_notation(content, rel))
        issues.extend(check_account_bare_email(content, rel))
        issues.extend(check_person_account_schema_token(content, rel))
        issues.extend(check_person_account_name_write(content, rel))

    for value_set in sorted(manifest_dir.rglob("TaskStatus.standardValueSet-meta.xml")):
        issues.extend(
            check_task_status_value_set(value_set, str(value_set.relative_to(manifest_dir)))
        )

    return issues


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_dir = Path(args.manifest_dir)
    issues = check_standard_object_quirks(manifest_dir)

    errors = [i for i in issues if i.severity == "ERROR"]
    warnings = [i for i in issues if i.severity != "ERROR"]

    if args.format == "json":
        print(
            json.dumps(
                {
                    "manifest_dir": str(manifest_dir),
                    "error_count": len(errors),
                    "warning_count": len(warnings),
                    "issues": [i.as_dict() for i in issues],
                },
                indent=2,
            )
        )
    else:
        if not issues:
            print("No standard-object quirk issues found.")
        else:
            for issue in issues:
                print(issue)
            print(f"\n{len(errors)} error(s), {len(warnings)} warning(s).")

    if errors:
        return 1
    if warnings and args.warnings_as_errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
