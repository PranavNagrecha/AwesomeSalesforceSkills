#!/usr/bin/env python3
"""Audit an Apex source tree for layering, sharing, and dynamic-factory mistakes.

Stdlib only. Regex-based static inspection of `.cls` and `.trigger` files, plus
XML parsing of Custom Metadata records, under --manifest-dir. This script never
compiles Apex and never contacts an org.

Checks implemented
------------------
1.  Trigger body carries logic. A `.trigger` whose body contains SOQL, DML, or a
    loop is not an adapter. The canonical body is one line:
    `new <Object>TriggerHandler().run();` (templates/apex/TriggerHandler.cls).
2.  Layer class with no sharing declaration. A class named `*Service` /
    `*Selector` / `*Domain` / `*TriggerHandler` / `*Factory` with no
    `with sharing`, `without sharing`, or `inherited sharing` keyword. From API
    version 67.0 an undeclared class runs `with sharing` (Apex Developer Guide
    L4961), so the same source means different things at different API versions.
    Inner classes are checked too: they do not adopt the container's sharing
    mode (L4931-4932).
3.  SOQL outside a selector class. Inline `[SELECT ...]`, `Database.query`,
    `Database.queryWithBinds`, or `Database.getQueryLocator*` in a non-test class
    whose name does not end in `Selector` — the heuristic form of "the selector
    layer owns every query".
4.  `Type.forName('Literal')` naming a class that no Custom Metadata record in
    this manifest mentions. A hardcoded literal is a `new` in disguise; a literal
    that no `.md-meta.xml` names is a strategy nobody can reconfigure.
    Also flags `newInstance()` chained onto `Type.forName(...)` with no
    intervening null check (Apex Reference Guide L241920-241922, L242303).
5.  `abstract` or `override` method with no access modifier. From API version
    65.0 this is the compile error "Abstract methods require at least one of the
    following: global, public, protected" (Apex Developer Guide L3359-3364).
6.  Static mutable collection with no reset hook. A rollback does not revert
    static variables (L8692-8693) and Bulk API chunks share them (L3789-3791),
    so every static Map/List/Set needs a `reset()`/`clear()` path.

Carried over from the previous revision: `Test.isRunningTest()` in production
code, god-class mixing (SOQL + DML + HTTP), and utility classes holding data
access.

Usage:
    python3 check_apex_design_patterns.py --manifest-dir force-app/main/default
    python3 check_apex_design_patterns.py --manifest-dir .
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

MD_NS = "{http://soap.sforce.com/2006/04/metadata}"

# --- shapes --------------------------------------------------------------------
TRIGGER_HEADER_RE = re.compile(r"trigger\s+(\w+)\s+on\s+(\w+)\s*\(", re.IGNORECASE)
SOQL_RE = re.compile(r"\[\s*SELECT\b", re.IGNORECASE)
INLINE_SOQL_BODY_RE = re.compile(r"\[\s*SELECT\b[^\]]*\]", re.IGNORECASE | re.DOTALL)
CMDT_SOURCE_RE = re.compile(r"\b\w+__mdt\b", re.IGNORECASE)
DYNAMIC_SOQL_RE = re.compile(
    r"\bDatabase\s*\.\s*(query|queryWithBinds|countQuery|countQueryWithBinds"
    r"|getQueryLocator|getQueryLocatorWithBinds)\s*\(",
    re.IGNORECASE,
)
DML_RE = re.compile(
    r"(?:^|[;{}\s])(insert|update|upsert|delete|undelete|merge)\s+[A-Za-z_(]"
    r"|\bDatabase\s*\.\s*(insert|update|upsert|delete|undelete|merge)\s*\(",
    re.IGNORECASE,
)
LOOP_RE = re.compile(r"\b(for|while)\s*\(")
HTTP_RE = re.compile(r"\bHttp(Request|Response)?\b")
TEST_RUNNING_RE = re.compile(r"Test\.isRunningTest\s*\(", re.IGNORECASE)
UTIL_CLASS_RE = re.compile(r"\bclass\s+\w*Util\w*\b")
TEST_CLASS_RE = re.compile(r"@\s*isTest\b|\btestMethod\b", re.IGNORECASE)

CLASS_DECL_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<mods>(?:(?:global|public|private|protected|abstract|virtual"
    r"|with\s+sharing|without\s+sharing|inherited\s+sharing)\s+)*)"
    r"class\s+(?P<name>\w+)",
    re.IGNORECASE | re.MULTILINE,
)
SHARING_RE = re.compile(r"\b(with\s+sharing|without\s+sharing|inherited\s+sharing)\b", re.IGNORECASE)
LAYER_SUFFIXES = ("Service", "Selector", "Domain", "TriggerHandler")

# `abstract`/`override` on a METHOD (not a class/interface) with no access modifier.
ABSTRACT_METHOD_RE = re.compile(
    r"^\s*(?!.*\b(?:class|interface|enum)\b)"
    r"(?P<mods>(?:\w+\s+)*?)(?P<kw>abstract|override)\s+[\w<>\[\],\s.]+\s+\w+\s*\(",
    re.MULTILINE,
)
ACCESS_RE = re.compile(r"\b(global|public|protected|private)\b")

FORNAME_LITERAL_RE = re.compile(r"Type\s*\.\s*forName\s*\(\s*'([^']*)'", re.IGNORECASE)
FORNAME_ANY_RE = re.compile(r"Type\s*\.\s*forName\s*\(", re.IGNORECASE)
FORNAME_CHAINED_RE = re.compile(
    r"Type\s*\.\s*forName\s*\([^)]*\)\s*\.\s*newInstance\s*\(", re.IGNORECASE
)

STATIC_COLLECTION_RE = re.compile(
    r"^\s*(?P<mods>(?:(?:global|public|private|protected|static|final|transient|@\w+)\s+)*)"
    r"(?P<type>Map|List|Set)\s*<[^>;=]*>\s+(?P<name>\w+)\s*(?P<tail>[=;])",
    re.MULTILINE,
)
RESET_HOOK_RE = re.compile(
    r"\bvoid\s+(reset|clearCache|clear|flushCache)\s*\(\s*\)", re.IGNORECASE
)

BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT_RE = re.compile(r"//[^\n]*")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check an Apex source tree for layering, sharing, and dynamic-factory defects."
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for Apex classes, triggers, and Custom Metadata records.",
    )
    return parser.parse_args()


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(item) for item in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


def strip_comments(text: str) -> str:
    """Blank out comments while preserving line numbering."""
    def blank(match: re.Match) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    return LINE_COMMENT_RE.sub(blank, BLOCK_COMMENT_RE.sub(blank, text))


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def iter_apex(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".cls", ".trigger"}
    )


def iter_custom_metadata(root: Path) -> list[Path]:
    """Custom Metadata records: `.md` (Metadata API) or `.md-meta.xml` (SFDX source)."""
    out: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        if name.endswith(".md-meta.xml") or name.endswith(".md"):
            out.append(path)
    return sorted(out)


def _child(element, tag: str):
    """Return a child Element or None. Never rely on Element truthiness: an
    Element with no children is falsy, so `a.find(x) or a.find(y)` is a bug."""
    found = element.find(tag)
    if found is None:
        found = element.find(MD_NS + tag)
    return found


def custom_metadata_values(paths: list[Path]) -> set[str]:
    """Every scalar <value> text across every Custom Metadata record found."""
    values: set[str] = set()
    for path in paths:
        try:
            root = ET.parse(path).getroot()
        except (ET.ParseError, OSError):
            continue
        entries = root.findall(MD_NS + "values") + root.findall("values")
        for entry in entries:
            node = _child(entry, "value")
            if node is not None and node.text:
                values.add(node.text.strip())
    return values


# --- individual checks ---------------------------------------------------------


def audit_trigger(path: Path, code: str) -> list[str]:
    findings: list[str] = []
    header = TRIGGER_HEADER_RE.search(code)
    if not header:
        return findings
    body = code[header.end():]

    if SOQL_RE.search(body) or DYNAMIC_SOQL_RE.search(body):
        findings.append(
            f"HIGH {path}: trigger body contains SOQL; move the query into a selector called "
            f"by the handler (templates/apex/BaseSelector.cls)"
        )
    if DML_RE.search(body):
        findings.append(
            f"HIGH {path}: trigger body contains DML; the trigger must delegate to a handler "
            f"that calls a service (templates/apex/TriggerHandler.cls)"
        )
    if LOOP_RE.search(body):
        findings.append(
            f"HIGH {path}: trigger body contains a loop; per-record logic belongs in a domain "
            f"class extending templates/apex/BaseDomain.cls"
        )

    statements = [
        line.strip()
        for line in body.splitlines()
        if line.strip() and line.strip() not in {"{", "}"}
    ]
    delegates = re.search(r"\b\w*(Handler|Service)\b", body) is not None
    if len(statements) > 6 and not delegates:
        findings.append(
            f"MEDIUM {path}: trigger body has {len(statements)} statements and names no "
            f"Handler or Service class; it is not an adapter"
        )
    return findings


def audit_sharing(path: Path, code: str) -> list[str]:
    findings: list[str] = []
    for match in CLASS_DECL_RE.finditer(code):
        name = match.group("name")
        mods = match.group("mods") or ""
        if not name.endswith(LAYER_SUFFIXES):
            continue
        if SHARING_RE.search(mods):
            continue
        is_inner = bool(match.group("indent"))
        is_base = re.search(r"\b(abstract|virtual)\b", mods, re.IGNORECASE) is not None
        inner = " (inner class — inner classes do not adopt the outer sharing mode)" if is_inner else ""
        if is_base:
            severity = "LOW"
            inner += " — a virtual/abstract base sets the default its subclasses inherit"
        elif name.endswith("Service"):
            severity = "HIGH"
        else:
            severity = "MEDIUM"
        findings.append(
            f"{severity} {path}:{line_of(code, match.start())}: class {name} declares no sharing "
            f"keyword{inner}; add with sharing / without sharing / inherited sharing"
        )
    return findings


def audit_query_placement(path: Path, code: str, is_test: bool) -> list[str]:
    if is_test:
        return []
    stem = path.stem
    if stem.endswith("Selector") or stem.endswith("Selectors"):
        return []
    findings: list[str] = []
    # Custom metadata reads are exempt: they carry no SOQL query limit in a
    # transaction (Apex Developer Guide L19614-19615) and belong with the class
    # that owns the setting, not in an sObject selector.
    hits = [
        m.start() for m in INLINE_SOQL_BODY_RE.finditer(code)
        if not CMDT_SOURCE_RE.search(m.group(0))
    ] + [m.start() for m in DYNAMIC_SOQL_RE.finditer(code)]
    if hits:
        first = min(hits)
        findings.append(
            f"MEDIUM {path}:{line_of(code, first)}: {len(hits)} query site(s) in a class that is "
            f"not a selector; centralise them in a *Selector extending templates/apex/BaseSelector.cls"
        )
    return findings


def audit_dynamic_factory(path: Path, code: str, cmdt_values: set[str], has_cmdt: bool) -> list[str]:
    findings: list[str] = []
    for match in FORNAME_LITERAL_RE.finditer(code):
        literal = match.group(1)
        if literal in cmdt_values:
            continue
        detail = (
            "no Custom Metadata record in this manifest names it"
            if has_cmdt
            else "this manifest contains no Custom Metadata records at all"
        )
        findings.append(
            f"MEDIUM {path}:{line_of(code, match.start())}: Type.forName('{literal}') is a "
            f"hardcoded class name and {detail}; either use `new {literal}()` or drive it from a "
            f"__mdt row so the strategy is configurable"
        )
    for match in FORNAME_CHAINED_RE.finditer(code):
        findings.append(
            f"HIGH {path}:{line_of(code, match.start())}: newInstance() is chained straight onto "
            f"Type.forName(); forName returns null for an inner, private, or renamed class "
            f"(Apex Reference Guide L241920-241922) — null-check the Type first"
        )
    return findings


def audit_access_modifiers(path: Path, code: str) -> list[str]:
    findings: list[str] = []
    for match in ABSTRACT_METHOD_RE.finditer(code):
        mods = match.group("mods") or ""
        if ACCESS_RE.search(mods):
            continue
        findings.append(
            f"HIGH {path}:{line_of(code, match.start())}: `{match.group('kw')}` method with no "
            f"access modifier; API 65.0+ requires protected, public, or global "
            f"(Apex Developer Guide L3359-3364)"
        )
    return findings


def audit_static_state(path: Path, code: str, is_test: bool) -> list[str]:
    if is_test:
        return []
    findings: list[str] = []
    has_reset = RESET_HOOK_RE.search(code) is not None
    for match in STATIC_COLLECTION_RE.finditer(code):
        mods = match.group("mods") or ""
        if "static" not in mods.lower():
            continue
        name = match.group("name")
        # A `static final` ALL_CAPS collection is a declared constant, not mutable state.
        if "final" in mods.lower() and name.isupper():
            continue
        if has_reset:
            continue
        severity = "LOW" if "@testvisible" in mods.lower() else "MEDIUM"
        findings.append(
            f"{severity} {path}:{line_of(code, match.start())}: static {match.group('type')} "
            f"`{name}` has no reset hook; a rollback does not revert statics and Bulk API "
            f"chunks share them (Apex Developer Guide L8692-8693, L3789-3791) — add a "
            f"@TestVisible private static void reset()"
        )
    return findings


def audit_legacy(path: Path, code: str, line_count: int) -> list[str]:
    findings: list[str] = []
    concerns = sum(
        bool(pattern.search(code))
        for pattern in (SOQL_RE, DML_RE, HTTP_RE)
    )
    if concerns >= 3 and line_count > 80:
        findings.append(
            f"REVIEW {path}: class mixes query, DML, and HTTP concerns; possible god-class"
        )
    if TEST_RUNNING_RE.search(code):
        findings.append(
            f"MEDIUM {path}: `Test.isRunningTest()` found; use an interface seam and constructor "
            f"injection instead (see skills/apex/apex-mocking-and-stubs)"
        )
    if UTIL_CLASS_RE.search(code) and (SOQL_RE.search(code) or DML_RE.search(code)):
        findings.append(
            f"REVIEW {path}: utility-style class contains data access or DML; verify responsibility "
            f"is clear"
        )
    return findings


def audit_file(path: Path, cmdt_values: set[str], has_cmdt: bool) -> list[str]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    code = strip_comments(raw)
    is_test = TEST_CLASS_RE.search(code) is not None
    line_count = raw.count("\n") + 1

    if path.suffix.lower() == ".trigger":
        return audit_trigger(path, code)

    findings: list[str] = []
    findings += audit_sharing(path, code)
    findings += audit_query_placement(path, code, is_test)
    findings += audit_dynamic_factory(path, code, cmdt_values, has_cmdt)
    findings += audit_access_modifiers(path, code)
    findings += audit_static_state(path, code, is_test)
    if not is_test:
        findings += audit_legacy(path, code, line_count)
    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result(
            [f"HIGH {root}: manifest directory not found"],
            "Scanned 0 Apex files; manifest directory was missing.",
        )

    files = iter_apex(root)
    if not files:
        return emit_result(
            [f"HIGH {root}: no Apex files found"],
            "Scanned 0 Apex files; no .cls or .trigger files were found.",
        )

    cmdt_files = iter_custom_metadata(root)
    cmdt_values = custom_metadata_values(cmdt_files)

    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path, cmdt_values, bool(cmdt_files)))

    summary = (
        f"Scanned {len(files)} Apex file(s) and {len(cmdt_files)} Custom Metadata record(s); "
        f"{len(findings)} design-pattern finding(s) detected."
    )
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
