#!/usr/bin/env python3
"""Checker for the `apex/entitlement-apex-hooks` skill.

Scans Apex source (`.cls`, `.trigger`) in a retrieved/deployable metadata tree for
the mistakes that this skill exists to prevent when Apex reads or writes
`CaseMilestone`.

Every rule is grounded in the Object Reference / Apex Developer Guide facts cited
in `references/gotchas.md`:

  * `CaseMilestone` supports only describeLayout(), describeSObjects(), query(),
    retrieve(), update() — no create(), no delete().
  * Only `CompletionDate` and `StartDate` carry the `Update` property.
    `IsCompleted`, `IsViolated` and `TargetDate` do not.
  * `SlaExitDate` is NOT a `CaseMilestone` field.
  * SOQL/DML inside a loop over `Trigger.new` burns one query per record.
  * A `CaseMilestone` query with no `CompletionDate = NULL` filter re-stamps
    already-completed milestones when the trigger fires a second time.
  * `WITH SECURITY_ENFORCED` does not compile at `apiVersion` 67.0+.
  * A class calling `TestDataFactory` (or another `templates/apex/**` class) with no copy
    of that class shipped in the same manifest fails deploy with
    `Variable does not exist: <Name>` (rule EAH009, WARN — see references/code-examples.md
    § Deploy prerequisites).
  * A `SeeAllData` test class that selects its `SlaProcess` with no `Name` filter proves
    nothing against a target org that already runs its own active process (rule EAH010,
    WARN — see Gotcha 13 in references/gotchas.md).

stdlib only — no pip dependencies.

Exit codes
    0   no ERROR findings (WARN findings alone still exit 0, unless --strict)
    1   at least one ERROR finding, or --manifest-dir does not exist,
        or --strict and at least one WARN finding
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ERROR = "ERROR"
WARN = "WARN"

# --------------------------------------------------------------------------
# Source normalisation
# --------------------------------------------------------------------------

_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_LINE_COMMENT = re.compile(r"//[^\n]*")
_STRING = re.compile(r"'(?:\\.|[^'\\])*'")


def _blank_out(match: re.Match) -> str:
    """Replace a matched span with spaces, preserving newlines and offsets."""
    return "".join("\n" if ch == "\n" else " " for ch in match.group(0))


def strip_noise(source: str) -> str:
    """Blank comments and string literals so regexes never match inside them.

    Offsets and line numbers are preserved, so a hit in the stripped text maps
    back to the same line in the original file.
    """
    stripped = _BLOCK_COMMENT.sub(_blank_out, source)
    stripped = _LINE_COMMENT.sub(_blank_out, stripped)
    stripped = _STRING.sub(_blank_out, stripped)
    return stripped


def line_of(source: str, offset: int) -> int:
    return source.count("\n", 0, offset) + 1


def line_text(source: str, offset: int) -> str:
    start = source.rfind("\n", 0, offset) + 1
    end = source.find("\n", offset)
    if end == -1:
        end = len(source)
    return source[start:end].strip()


# --------------------------------------------------------------------------
# Finding
# --------------------------------------------------------------------------

class Finding:
    def __init__(self, severity: str, path: Path, line: int, rule: str, message: str):
        self.severity = severity
        self.path = path
        self.line = line
        self.rule = rule
        self.message = message

    def render(self) -> str:
        where = f"{self.path}:{self.line}" if self.line else str(self.path)
        return f"{self.severity} {self.rule} {where}: {self.message}"


# --------------------------------------------------------------------------
# Loop-body index (rule EAH001)
# --------------------------------------------------------------------------

_LOOP_KEYWORD = re.compile(r"\b(for|while)\s*\(")


def loop_body_spans(stripped: str) -> list[tuple[int, int, str]]:
    """Return (body_start, body_end, loop_header) for every brace-delimited loop.

    Walks the brace structure once. A loop header is the text between the
    keyword's `(` and its matching `)`, which is what lets the message name
    `Trigger.new` when that is what is being iterated.
    """
    spans: list[tuple[int, int, str]] = []
    for match in _LOOP_KEYWORD.finditer(stripped):
        open_paren = stripped.index("(", match.start())
        depth = 0
        close_paren = -1
        for i in range(open_paren, len(stripped)):
            if stripped[i] == "(":
                depth += 1
            elif stripped[i] == ")":
                depth -= 1
                if depth == 0:
                    close_paren = i
                    break
        if close_paren == -1:
            continue
        header = " ".join(stripped[open_paren + 1:close_paren].split())

        # Find the loop body: the next `{` before any `;` (a `;` first means a
        # single-statement loop with no braces, which we do not index).
        body_open = -1
        for i in range(close_paren + 1, len(stripped)):
            if stripped[i] == "{":
                body_open = i
                break
            if stripped[i] == ";":
                break
            if not stripped[i].isspace():
                break
        if body_open == -1:
            continue

        depth = 0
        body_close = len(stripped)
        for i in range(body_open, len(stripped)):
            if stripped[i] == "{":
                depth += 1
            elif stripped[i] == "}":
                depth -= 1
                if depth == 0:
                    body_close = i
                    break
        spans.append((body_open, body_close, header))
    return spans


def enclosing_loop(spans: list[tuple[int, int, str]], offset: int) -> str | None:
    """Return the innermost loop header containing offset, or None."""
    best: tuple[int, str] | None = None
    for start, end, header in spans:
        if start < offset < end:
            width = end - start
            if best is None or width < best[0]:
                best = (width, header)
    return None if best is None else best[1]


_SOQL = re.compile(r"\[\s*SELECT\b", re.I)
_DML = re.compile(
    r"\b(?:insert|update|delete|upsert|undelete)\s+(?:as\s+(?:user|system)\s+)?[A-Za-z_]"
    r"|\bDatabase\.(?:insert|update|delete|upsert|undelete)\s*\(",
    re.I,
)


def rule_query_or_dml_in_loop(path: Path, source: str, stripped: str) -> list[Finding]:
    """EAH001 — SOQL or DML inside a loop. The classic bulk-safety failure."""
    findings: list[Finding] = []
    spans = loop_body_spans(stripped)
    if not spans:
        return findings
    for pattern, kind in ((_SOQL, "SOQL query"), (_DML, "DML statement")):
        for match in pattern.finditer(stripped):
            header = enclosing_loop(spans, match.start())
            if header is None:
                continue
            over_trigger_new = bool(re.search(r"Trigger\.(new|old)\b", header))
            detail = (
                "a loop over Trigger.new" if over_trigger_new else f"a loop ({header})"
            )
            findings.append(
                Finding(
                    ERROR,
                    path,
                    line_of(source, match.start()),
                    "EAH001",
                    f"{kind} inside {detail} — it runs once per record and hits the "
                    "per-transaction limit. Collect Ids into a Set<Id> first, then run "
                    "one query and one DML outside the loop. "
                    f"Line: {line_text(source, match.start())}",
                )
            )
    return findings


# --------------------------------------------------------------------------
# Field-level rules
# --------------------------------------------------------------------------

_ASSIGN = r"\s*=(?!=)"

_NON_UPDATEABLE = {
    "IsCompleted": (
        "IsCompleted is not an updateable CaseMilestone field (Object Reference lists "
        "its properties as 'Defaulted on create, Filter' — no Update). Write "
        "CompletionDate instead; it is one of only two fields on the object that carry "
        "the Update property."
    ),
    "IsViolated": (
        "IsViolated is not an updateable CaseMilestone field (properties: 'Defaulted on "
        "create, Filter'). Violation state is set by the platform, not by your DML."
    ),
    "TargetDate": (
        "TargetDate is not an updateable CaseMilestone field (properties: 'Filter' only). "
        "Milestone deadlines come from the entitlement process definition, not from Apex."
    ),
}


def rule_non_updateable_writes(path: Path, source: str, stripped: str) -> list[Finding]:
    """EAH002 — assignment to a CaseMilestone field that has no Update property."""
    findings: list[Finding] = []
    for field, message in _NON_UPDATEABLE.items():
        pattern = re.compile(r"\.(" + field + r")\b" + _ASSIGN)
        for match in pattern.finditer(stripped):
            findings.append(
                Finding(
                    ERROR,
                    path,
                    line_of(source, match.start()),
                    "EAH002",
                    f"{message} Line: {line_text(source, match.start())}",
                )
            )
    return findings


_SLA_EXIT_DATE = re.compile(r"\bSlaExitDate\b")


def rule_sla_exit_date(path: Path, source: str, stripped: str) -> list[Finding]:
    """EAH003 — SlaExitDate referenced in CaseMilestone code.

    SlaExitDate is not a CaseMilestone field at all. Referencing it on a
    CaseMilestone variable or in a CaseMilestone SOQL SELECT list is a compile
    error, not a silently-ignored write.
    """
    findings: list[Finding] = []
    if "CaseMilestone" not in stripped:
        return findings
    for match in _SLA_EXIT_DATE.finditer(stripped):
        findings.append(
            Finding(
                ERROR,
                path,
                line_of(source, match.start()),
                "EAH003",
                "SlaExitDate is not a field on CaseMilestone — the Object Reference "
                "CaseMilestone field list has no SlaExitDate (the field of that name "
                "belongs to WorkOrder). On Case the entitlement-clock fields are "
                "SlaStartDate and StopStartDate. "
                f"Line: {line_text(source, match.start())}",
            )
        )
    return findings


_UNSUPPORTED_DML = re.compile(
    r"\b(insert|delete|upsert|undelete)\s+(?:as\s+(?:user|system)\s+)?([A-Za-z_][A-Za-z0-9_]*)",
    re.I,
)


def _case_milestone_variables(stripped: str) -> set[str]:
    """Names of local variables declared as CaseMilestone or List<CaseMilestone>."""
    names: set[str] = set()
    decl = re.compile(
        r"\b(?:List|Set)\s*<\s*CaseMilestone\s*>\s+([A-Za-z_][A-Za-z0-9_]*)"
        r"|\bCaseMilestone\s+([A-Za-z_][A-Za-z0-9_]*)\s*[=;]",
    )
    for match in decl.finditer(stripped):
        names.add(match.group(1) or match.group(2))
    return names


def rule_unsupported_call(path: Path, source: str, stripped: str) -> list[Finding]:
    """EAH004 — insert/delete/upsert against CaseMilestone. Only update() is supported."""
    findings: list[Finding] = []
    variables = _case_milestone_variables(stripped)
    if not variables:
        return findings
    for match in _UNSUPPORTED_DML.finditer(stripped):
        verb, target = match.group(1).lower(), match.group(2)
        if target not in variables:
            continue
        findings.append(
            Finding(
                ERROR,
                path,
                line_of(source, match.start()),
                "EAH004",
                f"`{verb}` on a CaseMilestone variable. The Object Reference lists "
                "CaseMilestone's supported calls as describeLayout(), describeSObjects(), "
                "query(), retrieve(), update() — the platform creates and deletes these "
                "rows, your code can only update them. "
                f"Line: {line_text(source, match.start())}",
            )
        )
    return findings


_SECURITY_ENFORCED = re.compile(r"\bWITH\s+SECURITY_ENFORCED\b", re.I)
_API_VERSION = re.compile(r"<apiVersion>\s*([\d.]+)\s*</apiVersion>")


def _api_version_of(path: Path) -> float | None:
    meta = path.with_name(path.name + "-meta.xml")
    if not meta.is_file():
        return None
    match = _API_VERSION.search(meta.read_text(encoding="utf-8", errors="replace"))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def rule_security_enforced(path: Path, source: str, stripped: str) -> list[Finding]:
    """EAH005 — WITH SECURITY_ENFORCED. ERROR at apiVersion 67.0+, WARN below."""
    findings: list[Finding] = []
    matches = list(_SECURITY_ENFORCED.finditer(stripped))
    if not matches:
        return findings
    api_version = _api_version_of(path)
    if api_version is not None and api_version >= 67.0:
        severity = ERROR
        detail = (
            f"apiVersion {api_version:.1f} — WITH SECURITY_ENFORCED was removed in 67.0 "
            "and does not compile. Use WITH USER_MODE (it is the default access mode at "
            "this version anyway)."
        )
    else:
        version_note = f"apiVersion {api_version:.1f}" if api_version is not None else "apiVersion unknown (no -meta.xml found)"
        severity = WARN
        detail = (
            f"{version_note} — WITH SECURITY_ENFORCED is the weaker legacy construct and "
            "is removed at 67.0. Migrate to WITH USER_MODE."
        )
    for match in matches:
        findings.append(
            Finding(severity, path, line_of(source, match.start()), "EAH005", detail)
        )
    return findings


_CASE_MILESTONE_QUERY = re.compile(
    r"\[\s*SELECT\b(?:[^\[\]]|\[[^\]]*\])*?\bFROM\s+CaseMilestone\b(?:[^\[\]]|\[[^\]]*\])*?\]",
    re.I | re.S,
)
_OPEN_FILTER = re.compile(r"CompletionDate\s*=\s*(?:NULL|:\s*[A-Za-z_])", re.I)
# A query pinned to specific milestone Ids is a read-back of rows you already hold, not
# the completion-set query the open-milestone filter exists to constrain. Exempt it.
_ID_PINNED = re.compile(r"\bWHERE\b[^\]]*?\bId\s+(?:=|IN)\s*:", re.I | re.S)


def rule_missing_open_filter(path: Path, source: str, stripped: str) -> list[Finding]:
    """EAH006 — a CaseMilestone query with no `CompletionDate = NULL` filter.

    Without it the query returns already-completed milestones too, and the
    completion write re-stamps them. That matters because a workflow field
    update re-fires before/after update triggers one more time on the same save
    (Apex Developer Guide, order of execution step 11c), so the trigger body
    genuinely runs twice.
    """
    findings: list[Finding] = []
    for match in _CASE_MILESTONE_QUERY.finditer(stripped):
        if _OPEN_FILTER.search(match.group(0)):
            continue
        if _ID_PINNED.search(match.group(0)):
            continue
        findings.append(
            Finding(
                WARN,
                path,
                line_of(source, match.start()),
                "EAH006",
                "SOQL on CaseMilestone with no `CompletionDate = NULL` filter — the "
                "query returns already-completed milestones, and a completion write "
                "re-stamps them on the second trigger pass a workflow field update "
                "causes. Add `AND CompletionDate = NULL` to the WHERE clause.",
            )
        )
    return findings


_TIME_REMAINING_COMPARE = re.compile(
    r"\bTimeRemainingIn(?:Mins|Hrs)\s*(?:<=|>=|<|>)\s*[-\d]"
)


def rule_time_remaining_numeric(path: Path, source: str, stripped: str) -> list[Finding]:
    """EAH007 — numeric comparison against a text field."""
    findings: list[Finding] = []
    for match in _TIME_REMAINING_COMPARE.finditer(stripped):
        findings.append(
            Finding(
                WARN,
                path,
                line_of(source, match.start()),
                "EAH007",
                "TimeRemainingInMins and TimeRemainingInHrs are typed `text` on "
                "CaseMilestone (TimeRemainingInMins is documented as 'minutes and "
                "seconds'), so a numeric comparison does not mean what it looks like. "
                "Compare TargetDate against System.now(), or use the `double` field "
                "TimeRemainingInDays. "
                f"Line: {line_text(source, match.start())}",
            )
        )
    return findings


_MILESTONE_TRIGGER = re.compile(r"\btrigger\s+\w+\s+on\s+CaseMilestone\b", re.I)
_BEFORE_TRIGGER = re.compile(r"\btrigger\s+\w+\s+on\s+\w+\s*\([^)]*\bbefore\s+(?:insert|update)\b", re.I)


def rule_trigger_shape(path: Path, source: str, stripped: str) -> list[Finding]:
    """EAH008 — trigger-context mistakes specific to milestone automation."""
    findings: list[Finding] = []
    if path.suffix.lower() != ".trigger":
        return findings

    milestone_trigger = _MILESTONE_TRIGGER.search(stripped)
    if milestone_trigger and re.search(r"\bIsViolated\b", stripped):
        findings.append(
            Finding(
                WARN,
                path,
                line_of(source, milestone_trigger.start()),
                "EAH008",
                "A trigger on CaseMilestone that inspects IsViolated will not see the "
                "platform's violation transition — nothing in the Apex Developer Guide "
                "describes a DML event for it. Poll with Scheduled Apex, or use the "
                "entitlement process's native milestone violation actions.",
            )
        )

    before_trigger = _BEFORE_TRIGGER.search(stripped)
    if before_trigger and "CaseMilestone" in stripped:
        findings.append(
            Finding(
                WARN,
                path,
                line_of(source, before_trigger.start()),
                "EAH008",
                "A `before insert`/`before update` trigger that touches CaseMilestone. "
                "Entitlement rules run at step 15 of the order of execution, after all "
                "before triggers (step 4) and all after triggers (step 8), so the "
                "milestone rows for a case entering the process do not exist yet. Use "
                "`after update` on a later save.",
            )
        )
    return findings


_IS_TEST_CLASS = re.compile(r"@[Ii]s[Tt]est\b|@[Tt]est[Ss]etup\b", re.I)
_SLA_PROCESS_QUERY = re.compile(
    r"\[\s*SELECT\b(?:[^\[\]]|\[[^\]]*\])*?\bFROM\s+SlaProcess\b(?:[^\[\]]|\[[^\]]*\])*?\]",
    re.I | re.S,
)
_NAME_FILTER = re.compile(r"\bName\s*(?:=|IN)\s*[:(]", re.I)


def rule_slaprocess_missing_name_filter(path: Path, source: str, stripped: str) -> list[Finding]:
    """EAH010 — a SeeAllData test selects SlaProcess with no Name filter.

    A test class needs `@IsTest(SeeAllData=true)` to reach a real SlaProcess at all
    (Gotcha 6 — SlaProcess has no create()). `WHERE IsActive = true LIMIT 1` with no name
    filter returns whichever active SlaProcess the target org already has, not necessarily
    the one the test was written to exercise — if the org carries its own process with a
    different milestone shape, the test silently enters the wrong process and proves
    nothing (F-61, case-onboarding MOCK-DEPLOY-M5.md run 6; deploy-order.md § 10). WARN,
    not ERROR: this is a test-grounding defect that only an org dry run surfaces, and a
    query that happens to filter Name on a different clause shape than this regex expects
    is a false negative this checker will miss, not a false positive it will raise.
    """
    findings: list[Finding] = []
    if not _IS_TEST_CLASS.search(stripped):
        return findings
    for match in _SLA_PROCESS_QUERY.finditer(stripped):
        if _NAME_FILTER.search(match.group(0)):
            continue
        findings.append(
            Finding(
                WARN,
                path,
                line_of(source, match.start()),
                "EAH010",
                "SOQL on SlaProcess in a test class with no Name filter — "
                "`WHERE IsActive = true LIMIT 1` (or similar) takes whichever active "
                "entitlement process the target org already has, not necessarily the one "
                "this test was written against. Select by name, assert exactly one match, "
                "and name the process in the failure message. See Gotcha 13 in "
                "references/gotchas.md.",
            )
        )
    return findings


_RULES = (
    rule_query_or_dml_in_loop,
    rule_non_updateable_writes,
    rule_sla_exit_date,
    rule_unsupported_call,
    rule_security_enforced,
    rule_missing_open_filter,
    rule_time_remaining_numeric,
    rule_trigger_shape,
    rule_slaprocess_missing_name_filter,
)


# --------------------------------------------------------------------------
# Template-class provenance (rule EAH009)
# --------------------------------------------------------------------------

# The canonical cross-skill building blocks under templates/apex/ (see
# templates/README.md). A class in this manifest that calls one of these by name, with no
# .cls of that name anywhere under the same --manifest-dir, is a class that will fail
# deploy with "Variable does not exist: <Name>" unless some other step ships the template
# (F-37, case-onboarding M4-S05, org dry run 2026-09-12).
_TEMPLATE_CLASS_NAMES = (
    "TriggerHandler",
    "TriggerControl",
    "ApplicationLogger",
    "SecurityUtils",
    "HttpClient",
    "BaseDomain",
    "BaseService",
    "BaseSelector",
    "TestDataFactory",
    "TestRecordBuilder",
    "MockHttpResponseGenerator",
    "TestUserFactory",
    "BulkTestPattern",
)
_TEMPLATE_CLASS_PATTERNS = {
    name: re.compile(r"\b" + re.escape(name) + r"\b") for name in _TEMPLATE_CLASS_NAMES
}


def rule_missing_template_class(
    path: Path, source: str, stripped: str, class_stems: set[str]
) -> list[Finding]:
    """EAH009 — a referenced template class has no .cls of that name in this manifest.

    WARN, not ERROR: this checker sees one manifest directory at a time, not the whole
    build plan, so it cannot know a template class ships from an earlier step. `--strict`
    promotes it to a failing exit code, which is the CI posture recommended in
    references/code-examples.md § Verification.
    """
    findings: list[Finding] = []
    own_stem = path.stem
    for name, pattern in _TEMPLATE_CLASS_PATTERNS.items():
        if name == own_stem or name in class_stems:
            continue
        match = pattern.search(stripped)
        if match is None:
            continue
        findings.append(
            Finding(
                WARN,
                path,
                line_of(source, match.start()),
                "EAH009",
                f"References `{name}` but no `{name}.cls` exists under this "
                f"--manifest-dir. {name} ships from templates/apex/ (see "
                "templates/README.md) and must be copied into the deployable set by this "
                "step or an earlier one — otherwise this fails deploy with "
                f"`Variable does not exist: {name}`. "
                f"Line: {line_text(source, match.start())}",
            )
        )
    return findings


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

def find_apex_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for ext in ("*.cls", "*.trigger"):
        files.extend(p for p in root.rglob(ext) if p.is_file())
    return sorted(files)


def scan(manifest_dir: Path) -> tuple[list[Finding], int]:
    """Return (findings, apex_file_count)."""
    findings: list[Finding] = []
    apex_files = find_apex_files(manifest_dir)
    class_stems = {p.stem for p in apex_files if p.suffix.lower() == ".cls"}
    for path in apex_files:
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            findings.append(Finding(WARN, path, 0, "EAH000", f"unreadable: {exc}"))
            continue
        stripped = strip_noise(source)
        for rule in _RULES:
            findings.extend(rule(path, source, stripped))
        if path.suffix.lower() == ".cls":
            findings.extend(rule_missing_template_class(path, source, stripped, class_stems))
    return findings, len(apex_files)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="check_entitlement_apex_hooks.py",
        description=(
            "Scan Apex source for CaseMilestone / entitlement-hook mistakes: writes to "
            "non-updateable fields, SlaExitDate on the wrong object, unsupported "
            "insert/delete calls, SOQL or DML inside a loop over Trigger.new, missing "
            "open-milestone filters, and WITH SECURITY_ENFORCED at apiVersion 67.0+."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        required=True,
        help="Root of the retrieved or deployable Salesforce metadata tree to scan.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on WARN findings as well as ERROR findings.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.is_dir():
        detail = "--manifest-dir does not exist or is not a directory."
        print(f"ERROR EAH000 {manifest_dir}: {detail}", file=sys.stderr)
        return 1

    findings, apex_count = scan(manifest_dir)

    if apex_count == 0:
        detail = (
            "no .cls or .trigger files found — nothing to check. Point --manifest-dir at "
            "the force-app (or retrieved metadata) tree that contains the classes."
        )
        print(f"WARN EAH000 {manifest_dir}: {detail}", file=sys.stderr)
        return 1 if args.strict else 0

    errors = [f for f in findings if f.severity == ERROR]
    warns = [f for f in findings if f.severity == WARN]

    for finding in findings:
        print(finding.render(), file=sys.stderr)

    print(
        f"scanned {apex_count} Apex file(s) under {manifest_dir}: "
        f"{len(errors)} ERROR, {len(warns)} WARN"
    )

    if errors:
        return 1
    if warns and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
