#!/usr/bin/env python3
"""check_invocable_methods.py — audit Apex invocable-action classes against the
documented @InvocableMethod / @InvocableVariable contract.

Stdlib only. Regex-based: this script reads source text and never claims to
compile Apex. It reports the defects that the compiler does not catch and that a
one-input Flow test does not surface.

Rules, each grounded in the Apex Developer Guide v67.0 (Summer '26):

  IM001  CRITICAL  more than one @InvocableMethod in a class
                   "Only one method in a class can have the InvocableMethod
                   annotation." (apexdev L5422)
  IM002  CRITICAL  the annotated method is not `static`, or is not public/global
                   "The invocable method must be static and public or global, and
                   its class must be an outer class." (apexdev L5421)
  IM003  CRITICAL  the annotated method's parameter is not a single List<...>
                   "There can be at most one input parameter and its data type
                   must be one of the following: A list of ..." (apexdev L5432)
  IM004  CRITICAL  the annotated method's return type is neither List<...> nor void
                   (apexdev L5443-5454)
  IM005  HIGH      SOQL or DML inside a for/while/do loop anywhere in the class
                   The action is called once per batch of interviews, so per-input
                   queries and DML burn the 100 SOQL / 150 DML transaction budget
                   (apexdev L19544, L19554).
  IM006  MEDIUM    @InvocableMethod without a `label`
                   "The default is the method name, though we recommend that you
                   provide a label." (apexdev L5404-5405)
  IM007  CRITICAL  @InvocableVariable on a static, final, protected or private
                   member, or on a property
                   "Only global and public variables can be invocable variables."
                   / "The invocable variable can't be any of these: A non-member
                   variable such as a static or local variable. A property. A final
                   variable. Protected or private." (apexdev L5718-5723)
  IM008  HIGH      an HTTP callout in an invocable class whose annotation does not
                   declare callout=true  (apexdev L5407-5408)
  IM009  MEDIUM    @InvocableVariable combines required with defaultValue
                   "The defaultValue modifier throws an error when used with
                   required." (apexdev L5693)
  IM010  HIGH      the annotated method returns a list built only on a success path
                   (results.add( appears only inside an if/else block and never
                   once per input) — heuristic for the size-and-order rule
                   (apexdev L5456-5457)

Usage:
    python3 check_invocable_methods.py --manifest-dir force-app
    python3 check_invocable_methods.py --manifest-dir force-app --fail-on HIGH

Exit codes:
    0  no findings (or only findings below --fail-on)
    1  findings at or above --fail-on, or the manifest directory is missing
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}
SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "REVIEW"]

INVOCABLE_METHOD_RE = re.compile(r"@InvocableMethod\b", re.IGNORECASE)
INVOCABLE_VARIABLE_RE = re.compile(r"@InvocableVariable\b", re.IGNORECASE)

# @InvocableMethod ( ...optional modifiers... ) <modifiers> <return> <name> ( <params> )
ANNOTATED_METHOD_RE = re.compile(
    r"@InvocableMethod\b\s*(?P<modifiers>\([^)]*\))?\s*"
    r"(?P<signature>(?:[\w<>,\[\]\s\.]+?)\s*\([^)]*\))\s*\{",
    re.IGNORECASE | re.DOTALL,
)

# @InvocableVariable ( ... ) <field declaration up to ; or {>
ANNOTATED_FIELD_RE = re.compile(
    r"@InvocableVariable\b\s*(?P<modifiers>\([^)]*\))?\s*(?P<decl>[^;{}]+?)\s*(?P<terminator>[;{])",
    re.IGNORECASE | re.DOTALL,
)

LOOP_RE = re.compile(r"\b(for|while|do)\b\s*[\(\{]")
SOQL_RE = re.compile(r"\[\s*(SELECT|FIND)\b", re.IGNORECASE)
DML_RE = re.compile(
    r"(^|[^\w.])(insert|update|upsert|delete|undelete|merge)\s+(?![\w]*\s*\()"
    r"|Database\s*\.\s*(insert|update|upsert|delete|undelete|merge|query)\s*\(",
    re.IGNORECASE,
)
CALLOUT_RE = re.compile(
    r"\bnew\s+Http\s*\(\s*\)|\bHttpRequest\b|\bHttp\s*\.\s*send\b|\bHttpClient\b"
    r"|\bWebServiceCallout\b|\bnew\s+HttpClient\b",
    re.IGNORECASE,
)

VOID_RETURN_RE = re.compile(r"\bvoid\s+\w+\s*\($")
LIST_RETURN_RE = re.compile(r"\bList\s*<", re.IGNORECASE)
STATIC_RE = re.compile(r"\bstatic\b", re.IGNORECASE)
PUBLIC_GLOBAL_RE = re.compile(r"\b(public|global)\b", re.IGNORECASE)
LIST_PARAM_RE = re.compile(r"\(\s*(final\s+)?List\s*<", re.IGNORECASE)

BAD_FIELD_MODIFIER_RE = re.compile(r"\b(static|final|protected|private)\b", re.IGNORECASE)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit @InvocableMethod / @InvocableVariable classes against the documented contract."
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the source tree to scan for .cls files (e.g. force-app).",
    )
    parser.add_argument(
        "--fail-on",
        default="MEDIUM",
        choices=SEVERITY_ORDER,
        help="Lowest severity that makes the run exit non-zero. Default: MEDIUM.",
    )
    return parser.parse_args(argv)


def strip_comments_and_strings(src: str) -> str:
    """Blank out string literals and comments in one left-to-right pass, preserving
    line count so line numbers stay usable. A quote inside a comment must not open a
    phantom string, and a '/*' inside a string must not open a phantom comment."""
    out: list[str] = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "'":
            j = i + 1
            while j < n and src[j] != "'":
                j += 2 if src[j] == "\\" else 1
            chunk = src[i : min(j + 1, n)]
            out.append(" " * len(chunk.replace("\n", "")) + "\n" * chunk.count("\n"))
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
            chunk = src[i:j]
            out.append(" " * len(chunk.replace("\n", "")) + "\n" * chunk.count("\n"))
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def is_test_class(src: str) -> bool:
    return re.search(r"@IsTest\b", src, re.IGNORECASE) is not None


def loop_body_spans(code: str) -> list[tuple[int, int]]:
    """Return (start, end) offsets of each loop body, matched by brace depth.
    Loops written without braces (single statement) are approximated by taking the
    remainder of the line, which is enough to catch `for (...) insert x;`."""
    spans: list[tuple[int, int]] = []
    for m in LOOP_RE.finditer(code):
        # Walk forward to the first '{' or ';' after the loop header's parentheses.
        i = m.end() - 1
        depth = 0
        while i < len(code):
            if code[i] == "(":
                depth += 1
            elif code[i] == ")":
                depth -= 1
                if depth == 0:
                    i += 1
                    break
            elif code[i] == "{" and depth == 0:
                break
            i += 1
        while i < len(code) and code[i] in " \t\r\n":
            i += 1
        if i >= len(code):
            continue
        if code[i] == "{":
            depth = 0
            j = i
            while j < len(code):
                if code[j] == "{":
                    depth += 1
                elif code[j] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            spans.append((i, min(j + 1, len(code))))
        else:
            j = code.find(";", i)
            spans.append((i, len(code) if j < 0 else j + 1))
    return spans


def audit_file(path: Path, rel: str) -> list[dict]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    if not INVOCABLE_METHOD_RE.search(raw) and not INVOCABLE_VARIABLE_RE.search(raw):
        return []
    code = strip_comments_and_strings(raw)
    findings: list[dict] = []

    def add(rule: str, severity: str, offset: int, message: str) -> None:
        findings.append(
            {
                "severity": severity,
                "rule": rule,
                "location": f"{rel}:{line_of(code, offset)}",
                "message": message,
            }
        )

    annotations = list(INVOCABLE_METHOD_RE.finditer(code))

    # IM001 — one annotated method per class (apexdev L5422)
    if len(annotations) > 1:
        add(
            "IM001",
            "CRITICAL",
            annotations[1].start(),
            f"{len(annotations)} @InvocableMethod annotations in one class; only one method in a class "
            "can carry it (apexdev L5422). Split into one outer class per action.",
        )

    methods = list(ANNOTATED_METHOD_RE.finditer(code))
    for m in methods:
        modifiers = (m.group("modifiers") or "")
        signature = " ".join(m.group("signature").split())
        header = signature[: signature.find("(")] if "(" in signature else signature
        params = signature[signature.find("(") :] if "(" in signature else "()"

        # IM002 — static + public/global (apexdev L5421)
        if not STATIC_RE.search(header) or not PUBLIC_GLOBAL_RE.search(header):
            add(
                "IM002",
                "CRITICAL",
                m.start(),
                f"Invocable method `{signature}` must be declared `static` and `public` or `global` "
                "(apexdev L5421).",
            )

        # IM003 — exactly one List<...> parameter (apexdev L5432)
        inner = params[1:-1].strip() if params.startswith("(") and params.endswith(")") else params
        if not inner:
            add(
                "IM003",
                "CRITICAL",
                m.start(),
                f"Invocable method `{signature}` takes no parameter; the contract is one "
                "`List<...>` input (apexdev L5432).",
            )
        else:
            depth = 0
            top_level_commas = 0
            for ch in inner:
                if ch == "<":
                    depth += 1
                elif ch == ">":
                    depth -= 1
                elif ch == "," and depth == 0:
                    top_level_commas += 1
            if top_level_commas:
                add(
                    "IM003",
                    "CRITICAL",
                    m.start(),
                    f"Invocable method `{signature}` declares {top_level_commas + 1} parameters; "
                    "there can be at most one, and it must be a List (apexdev L5432).",
                )
            elif not LIST_PARAM_RE.search(params):
                add(
                    "IM003",
                    "CRITICAL",
                    m.start(),
                    f"Invocable method `{signature}` does not take a `List<...>` parameter "
                    "(apexdev L5432). Flow passes one element per interview in the batch.",
                )

        # IM004 — return type must be List<...> or void (apexdev L5443-5454)
        if not LIST_RETURN_RE.search(header) and not re.search(r"\bvoid\b", header, re.IGNORECASE):
            add(
                "IM004",
                "CRITICAL",
                m.start(),
                f"Invocable method `{signature}` returns neither a `List<...>` nor `void` "
                "(apexdev L5443-5454).",
            )

        # IM006 — label modifier (apexdev L5404-5405)
        if "label" not in modifiers.lower():
            add(
                "IM006",
                "MEDIUM",
                m.start(),
                "@InvocableMethod has no `label`; the action then shows the raw method name on the "
                "Flow canvas (apexdev L5404-5405). Agentforce also reasons over label/description "
                "(apexdev L43664-43666).",
            )

    # IM005 — SOQL / DML inside a loop (apexdev L19544, L19554)
    for start, end in loop_body_spans(code):
        body = code[start:end]
        soql = SOQL_RE.search(body)
        if soql:
            add(
                "IM005",
                "HIGH",
                start + soql.start(),
                "SOQL inside a loop in an invocable class. The action receives the whole batch of "
                "interviews in one list, so this scales with input count against a 100-query "
                "transaction budget (apexdev L19544). Collect ids, then query once.",
            )
        dml = DML_RE.search(body)
        if dml:
            add(
                "IM005",
                "HIGH",
                start + dml.start(),
                "DML inside a loop in an invocable class. Same reasoning: 150 DML statements per "
                "transaction (apexdev L19554). Build the list, then run one DML.",
            )

    # IM007 / IM009 — invocable variable rules (apexdev L5691-5723)
    for f in ANNOTATED_FIELD_RE.finditer(code):
        decl = " ".join(f.group("decl").split())
        modifiers = (f.group("modifiers") or "")
        bad = BAD_FIELD_MODIFIER_RE.search(decl)
        if bad:
            add(
                "IM007",
                "CRITICAL",
                f.start(),
                f"@InvocableVariable on `{decl}` uses `{bad.group(1)}`. An invocable variable cannot "
                "be static, final, protected or private; only public and global instance members "
                "qualify (apexdev L5718-5723).",
            )
        if f.group("terminator") == "{":
            add(
                "IM007",
                "CRITICAL",
                f.start(),
                f"@InvocableVariable on `{decl}` looks like a property. A property cannot be an "
                "invocable variable (apexdev L5719-5723) — use a plain instance field.",
            )
        low = modifiers.lower()
        if "required" in low and "defaultvalue" in low:
            add(
                "IM009",
                "MEDIUM",
                f.start(),
                "@InvocableVariable combines `required` with `defaultValue`; the defaultValue "
                "modifier throws an error when used with required (apexdev L5693).",
            )

    # IM008 — callout without callout=true (apexdev L5407-5408)
    if annotations and not is_test_class(raw):
        callout = CALLOUT_RE.search(code)
        declares_callout = any(
            "callout" in (m.group("modifiers") or "").lower() and "callout=false" not in
            (m.group("modifiers") or "").lower().replace(" ", "")
            for m in methods
        )
        if callout and not declares_callout:
            add(
                "IM008",
                "HIGH",
                callout.start(),
                "This invocable class makes an HTTP callout but its @InvocableMethod does not declare "
                "`callout=true` (apexdev L5407-5408). In a screen flow that modifier is one of the "
                "three conditions for committing and starting a new transaction (apexdev L26872-26876).",
            )

    # IM010 — results built only on a success path (heuristic for apexdev L5456-5457)
    if methods and not is_test_class(raw):
        adds = list(re.finditer(r"\b\w*[Rr]esults?\s*\.\s*add\s*\(", code))
        if adds:
            conditional_spans = []
            for m in re.finditer(r"\bif\b\s*\(", code):
                i = code.find("{", m.end())
                if i < 0:
                    continue
                depth, j = 0, i
                while j < len(code):
                    if code[j] == "{":
                        depth += 1
                    elif code[j] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                conditional_spans.append((i, min(j + 1, len(code))))
            def in_conditional(off: int) -> bool:
                return any(s <= off < e for s, e in conditional_spans)
            if all(in_conditional(a.start()) for a in adds):
                add(
                    "IM010",
                    "HIGH",
                    adds[0].start(),
                    "Every `results.add(...)` sits inside an `if` block, so the output list can be "
                    "shorter than the input list. The i-th output must correspond to the i-th input "
                    "(apexdev L5456-5457) — seed one result per input before the work starts.",
                )

    return findings


def iter_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.cls") if p.is_file())


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.manifest_dir)

    if not root.exists() or not root.is_dir():
        print(
            json.dumps(
                {
                    "score": 0,
                    "findings": [
                        {
                            "severity": "CRITICAL",
                            "rule": "IM000",
                            "location": str(root),
                            "message": "manifest directory not found",
                        }
                    ],
                    "summary": f"Manifest directory {root} does not exist.",
                },
                indent=2,
            )
        )
        print(f"ERROR: manifest directory not found: {root}", file=sys.stderr)
        return 1

    files = iter_files(root)
    if not files:
        print(
            json.dumps(
                {"score": 100, "findings": [], "summary": f"No .cls files found under {root}."},
                indent=2,
            )
        )
        print(f"WARN: no Apex classes found under {root}", file=sys.stderr)
        return 0

    findings: list[dict] = []
    invocable_files = 0
    for path in files:
        try:
            rel = str(path.relative_to(root))
        except ValueError:
            rel = str(path)
        file_findings = audit_file(path, rel)
        if file_findings:
            invocable_files += 1
        findings.extend(file_findings)

    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(f["severity"], 0) for f in findings))
    summary = (
        f"Scanned {len(files)} Apex class file(s) under {root}; "
        f"{len(findings)} invocable-contract finding(s) in {invocable_files} file(s)."
    )
    print(json.dumps({"score": score, "findings": findings, "summary": summary}, indent=2))

    threshold = SEVERITY_ORDER.index(args.fail_on)
    blocking = [f for f in findings if SEVERITY_ORDER.index(f["severity"]) <= threshold]
    if blocking:
        print(
            f"FAIL: {len(blocking)} finding(s) at or above {args.fail_on}",
            file=sys.stderr,
        )
        return 1
    if findings:
        print(f"WARN: {len(findings)} finding(s) below {args.fail_on}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
