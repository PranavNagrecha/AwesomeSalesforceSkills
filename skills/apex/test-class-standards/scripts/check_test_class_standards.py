#!/usr/bin/env python3
"""check_test_class_standards.py — audit Apex test classes in a deploy manifest.

Stdlib only. Reads a directory of Apex source (`--manifest-dir`) and reports the
test-hygiene defects that make a suite pass in one org and fail in the next.

Rules
-----
ERROR  no-assertions          a test class whose test methods contain no assertion
ERROR  seealldata-unjustified `SeeAllData=true` with no adjacent comment explaining why
ERROR  callout-without-mock   a test that exercises a callout without `Test.setMock(...)`
ERROR  user-mode-test-without-runas  a test class with no permissioned `System.runAs` block
                                  while a non-test class in the same tree enforces the running
                                  user's FLS (`WITH USER_MODE`, `AccessLevel.USER_MODE`,
                                  `WITH SECURITY_ENFORCED`, `stripInaccessible`)
WARN   eventbus-result-discarded  `EventBus.publish(...)` called as a bare statement in a test
WARN   bulk-insert-no-starttest   a test method building more than 200 records outside
                                  a `Test.startTest()` / `Test.stopTest()` boundary
WARN   template-class-not-shipped a referenced `templates/apex/tests` class with no `.cls`
                                  in the manifest directory (the deploy would fail)
WARN   hardcoded-id           a 15/18-character Salesforce-style Id literal in a test
WARN   coverage-only-assert   `System.assert(true)` / `System.assertEquals(true, true)`
WARN   fixture-seeded-as-persona  plain fixture DML inside a permissioned `System.runAs`
                                  (Gotcha 15: seed in system mode; act as the persona)

Exit codes
----------
0  no ERROR findings (WARN findings still print)
1  at least one ERROR finding, or `--manifest-dir` does not exist
1  any finding at all when `--strict` is passed

Usage
-----
    python3 check_test_class_standards.py --manifest-dir force-app/main/default/classes
    python3 check_test_class_standards.py --manifest-dir path/to/classes --strict
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- detection

TEST_ARTIFACT_RE = re.compile(r"@isTest\b|\btestMethod\b", re.IGNORECASE)
ANNOTATION_RE = re.compile(r"^\s*@isTest\b", re.IGNORECASE)
CLASS_DECL_RE = re.compile(r"\bclass\s+\w+", re.IGNORECASE)
TEST_SETUP_RE = re.compile(r"^\s*@testSetup\b", re.IGNORECASE)
METHOD_DECL_RE = re.compile(r"\bstatic\s+(?:testMethod\s+)?void\s+(\w+)\s*\(", re.IGNORECASE)
ASSERT_RE = re.compile(r"\bAssert\.\w+\s*\(|\bSystem\.assert\w*\s*\(|(?<![.\w])assertEquals\s*\(", re.IGNORECASE)
SEE_ALL_DATA_RE = re.compile(r"SeeAllData\s*=\s*'?true'?", re.IGNORECASE)
SET_MOCK_RE = re.compile(r"Test\.setMock\s*\(", re.IGNORECASE)
START_TEST_RE = re.compile(r"Test\.startTest\s*\(", re.IGNORECASE)
STOP_TEST_RE = re.compile(r"Test\.stopTest\s*\(", re.IGNORECASE)
EVENTBUS_STATEMENT_RE = re.compile(r"^\s*EventBus\.publish\s*\(", re.IGNORECASE)
HARD_CODED_ID_RE = re.compile(r"'(?:[a-zA-Z0-9]{15}|[a-zA-Z0-9]{18})'")
COMMENT_RE = re.compile(r"//|/\*")
COUNT_ARG_RE = re.compile(
    r"(?:create\w*|build\w*|buildMany|newRecords)\s*\(\s*(\d+)|for\s*\(\s*Integer\s+\w+\s*=\s*0\s*;\s*\w+\s*<\s*(\d+)",
    re.IGNORECASE,
)

# Callout evidence inside a class body.
CALLOUT_MARKERS = (
    re.compile(r"\bnew\s+Http\s*\(\s*\)", re.IGNORECASE),
    re.compile(r"\bHttpRequest\b", re.IGNORECASE),
    re.compile(r"\bHttp\w*\.send\s*\(", re.IGNORECASE),
    re.compile(r"@future\s*\(\s*callout\s*=\s*true", re.IGNORECASE),
    re.compile(r"\bWebServiceCallout\.invoke\b", re.IGNORECASE),
)

# User-mode / FLS evidence inside a non-test class body. Code carrying any of
# these evaluates the RUNNING USER's object permissions and field-level security
# ("In user mode, the object permissions, field-level security, and sharing rules
# of the current user are enforced", apexdev L11437; L11955-L11967). A test that
# never leaves the deploying user's context therefore proves nothing about FLS —
# and when the custom fields ship in the same deployment, it does not merely prove
# nothing, it fails outright at validation time.
USER_MODE_MARKERS = (
    re.compile(r"\bWITH\s+USER_MODE\b", re.IGNORECASE),
    re.compile(r"\bAccessLevel\.USER_MODE\b", re.IGNORECASE),
    re.compile(r"\bWITH\s+SECURITY_ENFORCED\b", re.IGNORECASE),
    re.compile(r"\bstripInaccessible\s*\(", re.IGNORECASE),
)

RUNAS_CALL_RE = re.compile(r"\bSystem\.runAs\s*\(", re.IGNORECASE)
SELF_USER_VAR_RE = re.compile(
    r"(\w+)\s*=\s*new\s+User\s*\(\s*Id\s*=\s*UserInfo\.getUserId\s*\(\s*\)",
    re.IGNORECASE,
)
VERSION_ARG_RE = re.compile(r"^new(?:System\.)?Version\(", re.IGNORECASE)
KEYWORD_DML_RE = re.compile(r"\b(insert|update|upsert)\s+", re.IGNORECASE)
DATABASE_DML_RE = re.compile(r"\bDatabase\.(insert|update|upsert)\s*\(", re.IGNORECASE)
SYSTEM_MODE_ARG_RE = re.compile(r"AccessLevel\s*\.\s*SYSTEM_MODE", re.IGNORECASE)
NEW_EXPR_RE = re.compile(r"\bnew\s+[A-Za-z_]\w*", re.IGNORECASE)
CREATE_CALL_ASSIGN_RE = re.compile(
    r"\b(\w+)\s*=\s*(?:[\w.]+\.)?(create\w+)\s*\(",
    re.IGNORECASE,
)
FACTORY_CALL_ASSIGN_RE = re.compile(
    r"\b(\w+)\s*=\s*(?:[\w.]*Factory[\w.]*)\s*\(",
    re.IGNORECASE,
)
NEW_ASSIGN_RE = re.compile(r"\b(\w+)\s*=\s*new\s+[A-Za-z_]\w*", re.IGNORECASE)
LEADING_IDENT_RE = re.compile(r"^(\w+)\b")
CALL_NAME_RE = re.compile(r"(?:[\w.]+\.)?(\w+)\s*\(")

# Canonical shared test classes (templates/apex/tests). A test that names one of
# these must ship it — see agents/apex-builder/AGENT.md Step 6 provenance check.
TEMPLATE_TEST_CLASSES = (
    "TestDataFactory",
    "TestRecordBuilder",
    "TestUserFactory",
    "MockHttpResponseGenerator",
    "BulkTestPattern",
)

SEVERITY_WEIGHTS = {"ERROR": 15, "WARN": 5, "INFO": 0}
BULK_THRESHOLD = 200


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Apex test classes for assertion, isolation, callout-mock and bulk defects."
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Directory of Apex source (.cls) to scan. Must exist.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on any finding, not only on ERROR findings.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------- utilities


def strip_literals(src: str) -> str:
    """Blank single-quoted literals so an apostrophe or brace inside a string
    never confuses brace matching. One left-to-right pass, comments preserved."""
    out = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "'":
            j = i + 1
            while j < n and src[j] != "'":
                j += 2 if src[j] == "\\" else 1
            out.append("''")
            i = j + 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def strip_comments(src: str) -> str:
    """Blank `//` line and `/* … */` block comments to spaces, preserving length.

    Newlines inside block comments stay newlines so structure is unchanged. Single-quoted
    string literals are copied through so a `//` or `/*` inside a string is not treated as
    a comment. Offsets of non-comment code therefore match `src` — required by the
    startTest/stopTest span logic in `fixture-seeded-as-persona`.
    """
    out: list[str] = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "'":
            j = i + 1
            while j < n and src[j] != "'":
                j += 2 if src[j] == "\\" else 1
            if j < n:
                j += 1
            out.append(src[i:j])
            i = j
            continue
        if ch == "/" and i + 1 < n and src[i + 1] == "/":
            j = i
            while j < n and src[j] != "\n":
                out.append(" ")
                j += 1
            i = j
            continue
        if ch == "/" and i + 1 < n and src[i + 1] == "*":
            out.append(" ")
            out.append(" ")
            j = i + 2
            while j + 1 < n and not (src[j] == "*" and src[j + 1] == "/"):
                out.append("\n" if src[j] == "\n" else " ")
                j += 1
            if j + 1 < n:
                out.append(" ")
                out.append(" ")
                j += 2
            elif j < n:
                out.append(" ")
                j += 1
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def method_bodies(text: str) -> list[tuple[str, int, str]]:
    """Return (method_name, 1-based start line, body) for every @IsTest method."""
    lines = text.splitlines()
    bodies: list[tuple[str, int, str]] = []
    pending = False
    for idx, line in enumerate(lines):
        if ANNOTATION_RE.match(line):
            pending = True
            if CLASS_DECL_RE.search(line):
                pending = False
            continue
        if not line.strip():
            continue
        if CLASS_DECL_RE.search(line):
            pending = False
            continue
        match = METHOD_DECL_RE.search(line)
        is_legacy = re.search(r"\btestMethod\b", line, re.IGNORECASE) is not None
        if match and (pending or is_legacy):
            body = extract_block(lines, idx)
            bodies.append((match.group(1), idx + 1, body))
        pending = False
    return bodies


def extract_block(lines: list[str], start_idx: int) -> str:
    """Brace-match the block that opens at or after `start_idx`."""
    depth = 0
    started = False
    collected: list[str] = []
    for line in lines[start_idx:]:
        cleaned = strip_literals(line)
        collected.append(line)
        for ch in cleaned:
            if ch == "{":
                depth += 1
                started = True
            elif ch == "}":
                depth -= 1
        if started and depth <= 0:
            break
    return "\n".join(collected)


def testsetup_bodies(text: str) -> list[str]:
    """Bodies of `@TestSetup` methods. A mock registered there does not carry into
    a test method: every test method is its own transaction (apexdev L41033)."""
    lines = text.splitlines()
    out: list[str] = []
    for idx, line in enumerate(lines):
        if TEST_SETUP_RE.match(line):
            out.append(extract_block(lines, idx))
    return out


def has_callout(text: str) -> bool:
    return any(marker.search(text) for marker in CALLOUT_MARKERS)


def has_user_mode(text: str) -> bool:
    return any(marker.search(text) for marker in USER_MODE_MARKERS)


def runas_arguments(text: str) -> list[str]:
    """The argument expression of every `System.runAs(...)` call, parens balanced."""
    args: list[str] = []
    for match in RUNAS_CALL_RE.finditer(text):
        depth = 1
        i = match.end()
        n = len(text)
        while i < n and depth:
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
            i += 1
        args.append(text[match.end(): max(match.end(), i - 1)])
    return args


def self_user_names(text: str) -> set[str]:
    """Variable names bound to `new User(Id = UserInfo.getUserId())`."""
    return {m.group(1) for m in SELF_USER_VAR_RE.finditer(strip_literals(text))}


def is_permissioned_runas_arg(arg: str, self_users: set[str]) -> bool:
    """True when a `System.runAs` argument is a real persona, not a self-user or Version."""
    flat = re.sub(r"\s+", "", arg)
    if not flat:
        return False
    if "UserInfo.getUserId()" in flat:
        return False
    if flat in self_users:
        return False
    if VERSION_ARG_RE.match(flat):
        return False
    return True


def has_permissioned_runas(text: str) -> bool:
    """True when at least one `System.runAs` block runs as somebody other than the
    user executing the test.

    Two overloads do not count. `System.runAs(new User(Id = UserInfo.getUserId()))`
    is the mixed-DML idiom (apexdev L8931-L8942) — it re-enters the *same* user's
    context and grants no permission. `System.runAs(System.Version)` switches the
    managed-package version, not the user (apexdev L41417)."""
    stripped = strip_literals(strip_comments(text))  # comments first: prose runAs and apostrophes must not count
    self_users = self_user_names(stripped)
    return any(is_permissioned_runas_arg(arg, self_users) for arg in runas_arguments(stripped))


def runas_blocks(text: str) -> list[tuple[str, str]]:
    """Return `(arg, body)` for every `System.runAs(...) { ... }` in `text`."""
    stripped = strip_literals(strip_comments(text))
    blocks: list[tuple[str, str]] = []
    for match in RUNAS_CALL_RE.finditer(stripped):
        depth = 1
        i = match.end()
        n = len(stripped)
        while i < n and depth:
            if stripped[i] == "(":
                depth += 1
            elif stripped[i] == ")":
                depth -= 1
            i += 1
        arg = stripped[match.end() : max(match.end(), i - 1)]
        j = i
        while j < n and stripped[j] in " \t\r\n":
            j += 1
        if j >= n or stripped[j] != "{":
            continue
        depth = 0
        body_start = j + 1
        k = j
        while k < n:
            if stripped[k] == "{":
                depth += 1
            elif stripped[k] == "}":
                depth -= 1
                if depth == 0:
                    blocks.append((arg, stripped[body_start:k]))
                    break
            k += 1
    return blocks


def read_expr_to_semicolon(text: str, start: int) -> tuple[str, int]:
    """Read from `start` through the next top-level `;`, tracking paren/bracket/brace depth."""
    depth_paren = depth_bracket = depth_brace = 0
    i = start
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "(":
            depth_paren += 1
        elif ch == ")":
            depth_paren -= 1
        elif ch == "[":
            depth_bracket += 1
        elif ch == "]":
            depth_bracket -= 1
        elif ch == "{":
            depth_brace += 1
        elif ch == "}":
            depth_brace -= 1
        elif ch == ";" and depth_paren == depth_bracket == depth_brace == 0:
            return text[start:i].strip(), i + 1
        i += 1
    return text[start:].strip(), n


def read_paren_contents(text: str, open_idx: int) -> tuple[str, int]:
    """Given the index of `(`, return the inside text and the index after the matching `)`."""
    depth = 0
    i = open_idx
    n = len(text)
    while i < n:
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[open_idx + 1 : i], i + 1
        i += 1
    return text[open_idx + 1 :], n


def first_top_level_arg(args: str) -> str:
    depth = 0
    for idx, ch in enumerate(args):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            return args[:idx].strip()
    return args.strip()


def start_stop_spans(body: str) -> list[tuple[int, int]]:
    """Byte spans covering each `Test.startTest()` … `Test.stopTest()` pair in `body`.

    Matches only outside comments (`strip_comments`), so a mention of `Test.startTest()`
    in a `//` or `/* … */` comment never opens a span. Length is preserved, so offsets
    still line up with DML matches on the same comment-stripped text.
    """
    code = strip_comments(body)
    spans: list[tuple[int, int]] = []
    for start_m in START_TEST_RE.finditer(code):
        stop_m = STOP_TEST_RE.search(code, start_m.end())
        if stop_m:
            spans.append((start_m.start(), stop_m.end()))
    return spans


def in_spans(pos: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= pos < end for start, end in spans)


def fixture_vars_in(scope: str) -> set[str]:
    """Names assigned from `new Type(...)` or a create*/Factory call in this method/setup."""
    names: set[str] = set()
    for match in NEW_ASSIGN_RE.finditer(scope):
        names.add(match.group(1))
    for match in CREATE_CALL_ASSIGN_RE.finditer(scope):
        names.add(match.group(1))
    for match in FACTORY_CALL_ASSIGN_RE.finditer(scope):
        names.add(match.group(1))
    return names


def call_is_fixture_builder(name: str) -> bool:
    lower = name.lower()
    return lower.startswith("create") or "factory" in lower


def is_fixture_operand(operand: str, fixture_vars: set[str]) -> bool:
    """True when the DML target was built by `new Type(` or a create*/Factory call."""
    op = operand.strip()
    if not op:
        return False
    if NEW_EXPR_RE.search(op):
        return True
    call = CALL_NAME_RE.search(op)
    if call and call_is_fixture_builder(call.group(1)):
        return True
    leading = LEADING_IDENT_RE.match(op)
    if leading and leading.group(1) in fixture_vars:
        return True
    return False


def plain_fixture_dml_in_runas(runas_body: str, fixture_vars: set[str]) -> bool:
    """True when `runas_body` has plain fixture DML outside any startTest/stopTest span."""
    # Comment-stripped copy keeps offsets aligned with `runas_body` non-comment code, so
    # start/stop spans and DML matches share one coordinate space and ignore comment text.
    code = strip_comments(runas_body)
    spans = start_stop_spans(code)

    for match in KEYWORD_DML_RE.finditer(code):
        if in_spans(match.start(), spans):
            continue
        operand, _ = read_expr_to_semicolon(code, match.end())
        if is_fixture_operand(operand, fixture_vars):
            return True

    for match in DATABASE_DML_RE.finditer(code):
        if in_spans(match.start(), spans):
            continue
        # match ends at the character after `(`, so open paren is match.end() - 1
        args, _ = read_paren_contents(code, match.end() - 1)
        if SYSTEM_MODE_ARG_RE.search(args):
            continue
        operand = first_top_level_arg(args)
        if is_fixture_operand(operand, fixture_vars):
            return True

    return False


def find_fixture_seeded_as_persona(text: str) -> str | None:
    """Return the permissioned `runAs` arg when the class seeds fixtures as the persona.

    Heuristic (WARN): a permissioned `System.runAs` body performs plain insert/update/upsert
    (or `Database.*` without `AccessLevel.SYSTEM_MODE`) on a factory/`new Type` operand
    outside `Test.startTest()`/`Test.stopTest()`, and the class also calls `Test.startTest()`
    somewhere. `insertAsSystem(...)` is not keyword DML and never matches. Mentions of
    `Test.startTest()` inside comments do not satisfy the class-level gate.
    """
    stripped = strip_literals(strip_comments(text))
    if not START_TEST_RE.search(stripped):
        return None

    self_users = self_user_names(stripped)
    scopes = [body for _, _, body in method_bodies(text)] + testsetup_bodies(text)
    for scope in scopes:
        scope_s = strip_literals(strip_comments(scope))
        vars_ = fixture_vars_in(scope_s)
        for arg, body in runas_blocks(scope_s):
            if not is_permissioned_runas_arg(arg, self_users):
                continue
            if plain_fixture_dml_in_runas(body, vars_):
                return re.sub(r"\s+", " ", arg.strip())
    return None


def seealldata_is_justified(lines: list[str], idx: int) -> bool:
    """True when a comment sits on, or within the two lines above, the annotation."""
    window = lines[max(0, idx - 2): idx + 1]
    return any(COMMENT_RE.search(line) for line in window)


def max_record_count(body: str) -> int:
    biggest = 0
    for match in COUNT_ARG_RE.finditer(body):
        value = match.group(1) or match.group(2)
        if value and int(value) > biggest:
            biggest = int(value)
    return biggest


# ---------------------------------------------------------------- audit


def audit_class(
    path: Path,
    text: str,
    callout_classes: set[str],
    shipped: set[str],
    user_mode_classes: set[str],
) -> list[dict]:
    findings: list[dict] = []

    def add(severity: str, rule: str, message: str, line: int = 0) -> None:
        location = f"{path}:{line}" if line else str(path)
        findings.append({"severity": severity, "rule": rule, "location": location, "message": message})

    if not TEST_ARTIFACT_RE.search(text):
        return findings

    lines = text.splitlines()
    methods = method_bodies(text)
    is_test_class = bool(methods)

    for idx, line in enumerate(lines):
        if SEE_ALL_DATA_RE.search(line) and not seealldata_is_justified(lines, idx):
            add(
                "ERROR",
                "seealldata-unjustified",
                "`SeeAllData=true` with no adjacent comment justifying the org-data dependency",
                idx + 1,
            )

    for name in TEMPLATE_TEST_CLASSES:
        if re.search(rf"\b{name}\s*[.(]", text) and name not in shipped and path.stem != name:
            add(
                "WARN",
                "template-class-not-shipped",
                f"references shared test class `{name}` but `{name}.cls` is not in the manifest directory",
            )

    if not is_test_class:
        return findings

    for idx, line in enumerate(lines):
        if EVENTBUS_STATEMENT_RE.match(line):
            add(
                "WARN",
                "eventbus-result-discarded",
                "`EventBus.publish(...)` result is discarded; capture the result and assert on it, "
                "then call `Test.getEventBus().deliver()`",
                idx + 1,
            )
        if HARD_CODED_ID_RE.search(line):
            add("WARN", "hardcoded-id", "hard-coded Salesforce-style Id literal in a test", idx + 1)

    if user_mode_classes and not has_permissioned_runas(text):
        named = sorted(user_mode_classes)
        shown = ", ".join(f"`{name}`" for name in named[:3])
        if len(named) > 3:
            shown += f" (+{len(named) - 3} more)"
        add(
            "ERROR",
            "user-mode-test-without-runas",
            f"test class `{path.stem}` has no `System.runAs` block for a permissioned user, but "
            f"{shown} in the same tree enforce(s) the running user's FLS. A validation deploy runs "
            "these tests as the deploying user, whose profile carries no field permissions for "
            "custom fields shipped in the same request, so the suite fails with "
            "\"No such column 'X__c' on entity 'Y'\" or \"Operation failed due to fields being "
            "inaccessible on Sobject Y\". Put the assertions inside `System.runAs` of a user built "
            "by `templates/apex/tests/TestUserFactory.cls` holding the permission set(s) this "
            "deployment ships.",
        )

    squashed = re.sub(r"\s+", "", text)
    if "System.assert(true" in squashed or "System.assertEquals(true,true" in squashed:
        add("WARN", "coverage-only-assert", "assertion asserts a constant; it proves nothing about the code under test")

    # A mock registered in @TestSetup does not survive into a test method, so the
    # class-level fallback deliberately excludes @TestSetup bodies.
    mock_scope = text
    for setup_body in testsetup_bodies(text):
        mock_scope = mock_scope.replace(setup_body, "")

    other_callout_classes = [name for name in callout_classes if name != path.stem]

    for name, line_no, body in methods:
        if not ASSERT_RE.search(body):
            add("ERROR", "no-assertions", f"test method `{name}` contains no assertion", line_no)
        method_does_callout = has_callout(body) or any(
            re.search(rf"\b{re.escape(other)}\b", body) for other in other_callout_classes
        )
        if method_does_callout and not SET_MOCK_RE.search(body) and not SET_MOCK_RE.search(mock_scope):
            add(
                "ERROR",
                "callout-without-mock",
                f"test method `{name}` exercises callout code with no `Test.setMock(...)` registered",
                line_no,
            )
        count = max_record_count(body)
        if count > BULK_THRESHOLD and not (START_TEST_RE.search(body) and STOP_TEST_RE.search(body)):
            add(
                "WARN",
                "bulk-insert-no-starttest",
                f"test method `{name}` builds {count} records (> {BULK_THRESHOLD}) without a "
                "`Test.startTest()` / `Test.stopTest()` boundary",
                line_no,
            )

    seeded_arg = find_fixture_seeded_as_persona(text)
    if seeded_arg is not None:
        add(
            "WARN",
            "fixture-seeded-as-persona",
            f"{path.stem} seeds records with plain DML inside System.runAs({seeded_arg}) — at API 67.0 "
            "that insert runs in the persona's user context and needs Create FLS on every populated "
            "field (Gotcha 15: seed with Database.insert(records, AccessLevel.SYSTEM_MODE) or "
            "TestDataFactory.insertAsSystem outside runAs; keep only the action under test inside it)",
        )

    return findings


def emit(findings: list[dict], summary: str, strict: bool) -> int:
    errors = sum(1 for f in findings if f["severity"] == "ERROR")
    warns = sum(1 for f in findings if f["severity"] == "WARN")
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(f["severity"], 0) for f in findings))
    print(json.dumps({"score": score, "findings": findings, "summary": summary}, indent=2))
    print(f"{summary} ERROR={errors} WARN={warns}", file=sys.stderr)
    if errors:
        return 1
    if strict and findings:
        return 1
    return 0


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)

    if not root.is_dir():
        summary = f"manifest directory not found: {root}"
        finding = {
            "severity": "ERROR",
            "rule": "manifest-dir-missing",
            "location": str(root),
            "message": "manifest directory does not exist; nothing was scanned",
        }
        print(json.dumps({"score": 0, "findings": [finding], "summary": summary}, indent=2))
        print(f"{summary} ERROR=1 WARN=0", file=sys.stderr)
        return 1

    files = sorted(p for p in root.rglob("*.cls") if p.is_file())
    if not files:
        summary = f"no Apex classes found under {root}"
        finding = {
            "severity": "WARN",
            "rule": "manifest-dir-empty",
            "location": str(root),
            "message": "manifest directory contains no .cls files; nothing to audit",
        }
        return emit([finding], summary, args.strict)

    texts = {p: p.read_text(encoding="utf-8", errors="ignore") for p in files}
    shipped = {p.stem for p in files}
    callout_classes = {p.stem for p, t in texts.items() if has_callout(t) and not TEST_ARTIFACT_RE.search(t)}
    user_mode_classes = {p.stem for p, t in texts.items() if has_user_mode(t) and not TEST_ARTIFACT_RE.search(t)}

    findings: list[dict] = []
    audited = 0
    for path in files:
        text = texts[path]
        if TEST_ARTIFACT_RE.search(text):
            audited += 1
        findings.extend(audit_class(path, text, callout_classes, shipped, user_mode_classes))

    if audited == 0:
        findings.append(
            {
                "severity": "WARN",
                "rule": "no-test-classes",
                "location": str(root),
                "message": "no `@IsTest` artifacts found in the scanned tree",
            }
        )

    summary = f"Scanned {len(files)} Apex class file(s); audited {audited} @IsTest artifact(s); {len(findings)} finding(s)."
    return emit(findings, summary, args.strict)


if __name__ == "__main__":
    sys.exit(main())
