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


def has_permissioned_runas(text: str) -> bool:
    """True when at least one `System.runAs` block runs as somebody other than the
    user executing the test.

    Two overloads do not count. `System.runAs(new User(Id = UserInfo.getUserId()))`
    is the mixed-DML idiom (apexdev L8931-L8942) — it re-enters the *same* user's
    context and grants no permission. `System.runAs(System.Version)` switches the
    managed-package version, not the user (apexdev L41417)."""
    stripped = strip_literals(text)
    self_users = {m.group(1) for m in SELF_USER_VAR_RE.finditer(stripped)}
    for arg in runas_arguments(stripped):
        flat = re.sub(r"\s+", "", arg)
        if not flat:
            continue
        if "UserInfo.getUserId()" in flat:
            continue
        if flat in self_users:
            continue
        if VERSION_ARG_RE.match(flat):
            continue
        return True
    return False


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
