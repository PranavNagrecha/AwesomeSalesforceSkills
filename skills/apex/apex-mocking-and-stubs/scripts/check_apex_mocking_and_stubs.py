#!/usr/bin/env python3
"""Audit an Apex source tree for mocking-seam and Stub API mistakes.

Stdlib only. Regex-based static inspection of `.cls` files under --manifest-dir.
This script never compiles Apex and never contacts an org; it flags shapes that
the Apex Developer Guide documents as unsupported or that hide a missing seam.

Checks implemented
------------------
1. handleMethodCall signature drift — a StubProvider implementation whose
   handleMethodCall does not declare the six documented parameters in order
   (Apex Reference Guide L238486-238488). Apex will not compile it, but the
   drift is easy to miss in review and in generated code.
2. Test.createStub on a type the Stub API refuses — an inner class
   (`Outer.Inner.class`), a class whose only constructor is private, or a class
   declaring `implements Database.Batchable` (Apex Developer Guide L42209-42219).
3. Test.isRunningTest() in production code — a test-only branch standing in for
   a real seam.
4. Test class exercising the HTTP transport with no Test.setMock, and the
   startTest/setMock ordering rule for tests that do their own DML
   (Apex Developer Guide L35384-35385, L35675-35681).
5. StubProvider implementations whose handleMethodCall can throw for a void
   method — a fallback `throw` with no null path for methods with no return
   value.

Usage:
    python3 check_apex_mocking_and_stubs.py --manifest-dir force-app/main/default/classes
    python3 check_apex_mocking_and_stubs.py --manifest-dir . --fail-on HIGH
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}
SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "REVIEW"]

# --- file-level classification -------------------------------------------------
TEST_CLASS_RE = re.compile(r"@\s*isTest\b|\btestMethod\b", re.IGNORECASE)
STUB_PROVIDER_RE = re.compile(r"implements\s+(?:System\.)?StubProvider\b", re.IGNORECASE)
BATCHABLE_RE = re.compile(r"implements\s+[^{;]*Database\.Batchable\b", re.IGNORECASE)

# --- transport / stub API call sites -------------------------------------------
SETMOCK_RE = re.compile(r"Test\.setMock\s*\(", re.IGNORECASE)
START_TEST_RE = re.compile(r"Test\.startTest\s*\(\s*\)", re.IGNORECASE)
CREATE_STUB_RE = re.compile(r"Test\.createStub\s*\(\s*([A-Za-z0-9_.]+)\s*\.class", re.IGNORECASE)
HTTP_SEND_RE = re.compile(r"\bnew\s+Http\s*\(\s*\)|\bHttp\s+\w+\s*=|\.\s*send\s*\(")
MOCK_IMPL_RE = re.compile(
    r"implements\s+[^{;]*\b(?:HttpCalloutMock|WebServiceMock|StubProvider)\b", re.IGNORECASE
)
TEST_RUNNING_RE = re.compile(r"Test\.isRunningTest\s*\(", re.IGNORECASE)
TESTSETUP_RE = re.compile(r"@\s*TestSetup\b", re.IGNORECASE)
INLINE_DML_RE = re.compile(r"^\s*(?:insert|update|upsert|delete)\s+(?:as\s+\w+\s+)?[A-Za-z_]", re.IGNORECASE)

# --- handleMethodCall signature ------------------------------------------------
HANDLE_CALL_RE = re.compile(
    r"\bObject\s+handleMethodCall\s*\((?P<params>[^)]*)\)", re.IGNORECASE | re.DOTALL
)
EXPECTED_PARAM_TYPES = [
    r"object",
    r"string",
    r"(?:system\.)?type",
    r"list<\s*(?:system\.)?type\s*>",
    r"list<\s*string\s*>",
    r"list<\s*object\s*>",
]

# --- class declarations, for the private-constructor / inner-class checks -------
CLASS_DECL_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<mods>(?:(?:global|public|private|protected|virtual|abstract|with sharing|"
    r"without sharing|inherited sharing|static)\s+)*)class\s+(?P<name>\w+)",
    re.IGNORECASE | re.MULTILINE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check an Apex source tree for weak mocking seams and Stub API misuse."
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for Apex classes (e.g. force-app/main/default/classes).",
    )
    parser.add_argument(
        "--fail-on",
        default="MEDIUM",
        choices=SEVERITY_ORDER,
        help="Lowest severity that makes the run exit non-zero (default MEDIUM).",
    )
    return parser.parse_args()


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str, fail_on: str) -> int:
    normalized = [normalize_finding(item) for item in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    threshold = SEVERITY_ORDER.index(fail_on)
    blocking = [
        item
        for item in normalized
        if item["severity"] in SEVERITY_ORDER
        and SEVERITY_ORDER.index(item["severity"]) <= threshold
    ]
    return 1 if blocking else 0


def iter_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.cls")
        if path.is_file() and "__pycache__" not in path.parts
    )


def strip_comments(text: str) -> str:
    """Blank out comments while preserving line count, so reported line numbers
    still match the file on disk."""

    def blank(match: re.Match) -> str:
        return "\n" * match.group(0).count("\n")

    text = re.sub(r"/\*.*?\*/", blank, text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", "", text)
    return text


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


# --- check 1 -------------------------------------------------------------------
def check_handle_method_call_signature(path: Path, code: str) -> list[str]:
    findings: list[str] = []
    if not STUB_PROVIDER_RE.search(code):
        return findings
    matches = list(HANDLE_CALL_RE.finditer(code))
    if not matches:
        findings.append(
            f"HIGH {path}: class declares `implements StubProvider` but no "
            f"`Object handleMethodCall(...)` was found; the interface requires exactly one"
        )
        return findings
    for match in matches:
        raw = " ".join(match.group("params").split())
        params = [p.strip() for p in raw.split(",") if p.strip()]
        line = line_of(code, match.start())
        if len(params) != 6:
            findings.append(
                f"HIGH {path}:{line}: handleMethodCall declares {len(params)} parameter(s); "
                f"the StubProvider interface fixes it at 6 "
                f"(Object, String, System.Type, List<System.Type>, List<String>, List<Object>)"
            )
            continue
        for position, (declared, expected) in enumerate(zip(params, EXPECTED_PARAM_TYPES)):
            declared_type = declared.rsplit(" ", 1)[0].strip().lower().replace(" ", "")
            if not re.fullmatch(expected.replace(r"\s*", ""), declared_type):
                findings.append(
                    f"HIGH {path}:{line}: handleMethodCall parameter {position + 1} is "
                    f"`{declared.strip()}`; the interface signature requires "
                    f"`{EXPECTED_PARAM_TYPES[position]}` in that position"
                )
    return findings


# --- check 2 -------------------------------------------------------------------
def index_class_declarations(code: str) -> dict[str, dict]:
    """Map class name -> {inner: bool, private_ctor_only: bool, batchable: bool}."""
    declarations: dict[str, dict] = {}
    decls = list(CLASS_DECL_RE.finditer(code))
    for position, match in enumerate(decls):
        name = match.group("name")
        # An inner class is any class declaration after the first in the file, or one
        # that is indented (Apex allows only one top-level type per file).
        inner = position > 0 or bool(match.group("indent").strip("\n"))
        body_start = match.end()
        body_end = decls[position + 1].start() if position + 1 < len(decls) else len(code)
        body = code[body_start:body_end]
        ctors = re.findall(
            r"(?:^|[{};])\s*(global|public|private|protected)\s+"
            + re.escape(name)
            + r"\s*\(",
            body,
            re.MULTILINE,
        )
        declarations[name] = {
            "inner": inner,
            "private_ctor_only": bool(ctors) and all(c.lower() == "private" for c in ctors),
            "batchable": bool(BATCHABLE_RE.search(code[match.start():body_end])),
            "line": line_of(code, match.start()),
        }
    return declarations


def check_create_stub_targets(
    path: Path,
    code: str,
    declarations: dict[str, dict],
    global_index: dict[str, dict],
) -> list[str]:
    findings: list[str] = []
    for match in CREATE_STUB_RE.finditer(code):
        target = match.group(1)
        line = line_of(code, match.start())
        if "." in target:
            findings.append(
                f"CRITICAL {path}:{line}: `Test.createStub({target}.class, ...)` names a nested "
                f"type; inner classes cannot be mocked and this fails at runtime, not compile time "
                f"(Apex Developer Guide L42214)"
            )
            continue
        local = declarations.get(target)
        info = local if local else global_index.get(target)
        if not info:
            continue
        # Only a declaration in THIS file can be trusted as an inner class; a
        # same-named top-level class in another file is the more likely referent.
        if local and local["inner"]:
            findings.append(
                f"CRITICAL {path}:{line}: `{target}` is declared as an inner class at line "
                f"{info['line']} of this file; inner classes cannot be mocked "
                f"(Apex Developer Guide L42214)"
            )
        if info["private_ctor_only"]:
            findings.append(
                f"CRITICAL {path}:{line}: `{target}` has only private constructor(s); classes with "
                f"only private constructors cannot be mocked (Apex Developer Guide L42217)"
            )
        if info["batchable"]:
            findings.append(
                f"CRITICAL {path}:{line}: `{target}` implements Database.Batchable; Batchable "
                f"classes cannot be mocked (Apex Developer Guide L42216) — extract an injectable "
                f"service the batch calls instead"
            )
    return findings


# --- check 3 -------------------------------------------------------------------
def check_is_running_test(path: Path, code: str, is_test: bool) -> list[str]:
    if is_test:
        return []
    findings: list[str] = []
    for match in TEST_RUNNING_RE.finditer(code):
        line = line_of(code, match.start())
        window = code[match.end(): match.end() + 250]
        # A context guard's branch body is a bare `return;` or a `throw` — it changes
        # nothing about which collaborator runs. A `return <value>;` or an assignment
        # means the branch is substituting a dependency, which is the real smell.
        guard_only = bool(re.match(r"[^{;]{0,80}\{\s*(?:throw\b|return\s*;)", window, re.DOTALL))
        if guard_only:
            findings.append(
                f"REVIEW {path}:{line}: `Test.isRunningTest()` guards a bare return or throw "
                f"rather than selecting a dependency; that is a context assertion, not a missing "
                f"seam — confirm no collaborator is being swapped here"
            )
        else:
            findings.append(
                f"HIGH {path}:{line}: `Test.isRunningTest()` in production code selects a "
                f"different value or return path under test; that is a test-only branch standing "
                f"in for a missing seam — inject the collaborator instead"
            )
    return findings


# --- check 4 -------------------------------------------------------------------
def check_transport_mocking(path: Path, code: str, is_test: bool) -> list[str]:
    findings: list[str] = []
    if not is_test or MOCK_IMPL_RE.search(code):
        # A class that IS the test double builds HttpResponse objects by design and
        # is registered by whoever calls Test.setMock, not by itself.
        return findings
    touches_http = bool(HTTP_SEND_RE.search(code))
    has_setmock = bool(SETMOCK_RE.search(code))
    if touches_http and not has_setmock:
        findings.append(
            f"HIGH {path}: test class reaches the HTTP transport with no `Test.setMock(...)`; "
            f"tests that perform a real callout fail rather than skip it "
            f"(Apex Developer Guide L35384-35385)"
        )
    if has_setmock and not TESTSETUP_RE.search(code):
        setmock_pos = SETMOCK_RE.search(code).start()
        start_match = START_TEST_RE.search(code)
        has_inline_dml = any(
            INLINE_DML_RE.match(raw_line) for raw_line in code.splitlines()
        )
        if has_inline_dml and (start_match is None or start_match.start() > setmock_pos):
            findings.append(
                f"MEDIUM {path}:{line_of(code, setmock_pos)}: `Test.setMock` appears before "
                f"`Test.startTest()` in a class that performs its own DML; the guide requires "
                f"DML -> startTest -> setMock or the callout hits pending uncommitted work "
                f"(Apex Developer Guide L35675-35681)"
            )
    return findings


# --- check 5 -------------------------------------------------------------------
def check_void_return_path(path: Path, code: str) -> list[str]:
    findings: list[str] = []
    if not STUB_PROVIDER_RE.search(code):
        return findings
    match = HANDLE_CALL_RE.search(code)
    if not match:
        return findings
    body = code[match.end():]
    # Take the body up to the next top-level method or class, best effort.
    body = body[: body.find("\n    }") + 6] if "\n    }" in body else body
    throws_on_fallback = re.search(r"\bthrow\s+new\b", body)
    returns_null = re.search(r"\breturn\s+null\s*;", body)
    if throws_on_fallback and not returns_null:
        findings.append(
            f"MEDIUM {path}:{line_of(code, match.start())}: handleMethodCall throws for unhandled "
            f"methods but never returns null; a stubbed void method still routes through this "
            f"method and must receive null, or the stub explodes on a command it was never asked "
            f"to verify"
        )
    return findings


def build_global_index(sources: dict[Path, str]) -> dict[str, dict]:
    """Top-level class declarations across the tree, so `Test.createStub(Foo.class)`
    in one file resolves against Foo.cls in another."""
    index: dict[str, dict] = {}
    for path, code in sources.items():
        declarations = index_class_declarations(code)
        for name, info in declarations.items():
            if not info["inner"]:
                enriched = dict(info)
                enriched["file"] = str(path)
                index[name] = enriched
    return index


def audit_file(path: Path, code: str, global_index: dict[str, dict]) -> list[str]:
    is_test = bool(TEST_CLASS_RE.search(code))
    declarations = index_class_declarations(code)

    findings: list[str] = []
    findings += check_handle_method_call_signature(path, code)
    findings += check_create_stub_targets(path, code, declarations, global_index)
    findings += check_is_running_test(path, code, is_test)
    findings += check_transport_mocking(path, code, is_test)
    findings += check_void_return_path(path, code)
    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result(
            [f"HIGH {root}: manifest directory not found"],
            "Scanned 0 Apex classes; manifest directory was missing.",
            args.fail_on,
        )
    files = iter_files(root)
    if not files:
        return emit_result(
            [f"HIGH {root}: no Apex classes found"],
            "Scanned 0 Apex classes; no .cls files were found.",
            args.fail_on,
        )
    sources = {
        path: strip_comments(path.read_text(encoding="utf-8", errors="ignore"))
        for path in files
    }
    global_index = build_global_index(sources)
    findings: list[str] = []
    for path, code in sources.items():
        findings.extend(audit_file(path, code, global_index))
    summary = (
        f"Scanned {len(files)} Apex class file(s); {len(findings)} mocking/stub finding(s) detected."
    )
    return emit_result(findings, summary, args.fail_on)


if __name__ == "__main__":
    sys.exit(main())
