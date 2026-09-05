#!/usr/bin/env python3
"""Audit an SFDX source tree for Custom Metadata Type mistakes in Apex and metadata.

Stdlib only. Regex-based static inspection of `.cls` / `.trigger` files plus
ElementTree parsing of `__mdt` object definitions, their `fields/` files, and
`CustomMetadata` records under --manifest-dir. This script never compiles Apex
and never contacts an org.

Checks implemented
------------------
1.  DML on a `__mdt` sObject. `insert` / `update` / `upsert` / `delete` (statement
    or `Database.*` form) applied to a variable declared as a custom metadata type,
    or applied inline to a `__mdt` expression. "Apex code can deploy custom metadata
    records, but not via a DML operation." (Metadata API Developer Guide
    L41317-41322.) The supported calls on a `Custom Metadata Type__mdt` object are
    only describeSObjects(), describeLayout(), query() and retrieve()
    (Object Reference L5671-5672).
2.  SOQL against a `__mdt` inside a loop. Custom metadata carries no SOQL query
    limit (Apex Developer Guide L19616-19619), so this is not a governor problem —
    it is a design one: `getAll()` hoisted out of the loop reads the same
    application cache once.
3.  `LongTextArea` field on a `__mdt` type. Advisory. `getAll()` and `getInstance()`
    return "only the first 255 characters… so longer text fields get truncated"
    (Apex Reference Guide L204569-204572), and the CustomMetadataValue `xsi:type`
    table does not list LongTextArea (Metadata API Developer Guide L41716-41749).
    See references/gotchas.md Gotcha 11 and its UNVERIFIED note.
4.  `CustomMetadata` record with no `<protected>` element where the type is
    packaged. Advisory. Triggered when the record's own `__mdt` object definition
    declares `<visibility>Protected</visibility>` or `PackageProtected`
    (Metadata API Developer Guide L41363-41377), or when sfdx-project.json declares
    a non-empty namespace. `protected` defaults to false, so an omitted element
    ships a readable record out of a package that meant to hide it.
5.  Test class using `SeeAllData=true` while referencing `__mdt`. Metadata objects
    stay visible to tests without it (Apex Developer Guide L40707-40709); custom
    *settings* are the ones that need it (L13515-13516).
6.  `Metadata.Operations.enqueueDeployment` in a test class, or in a production
    class with no `Test.isRunningTest()` guard anywhere in the file. The guide's
    own instruction is to assert the DeployContainer and call the callback
    directly rather than enqueue from a test (Apex Developer Guide L28248-28254).

Exit codes
----------
    1  --manifest-dir does not exist, or at least one finding was reported
    0  clean, or nothing to scan (reported as a WARN finding)

Usage:
    python3 check_custom_metadata_in_apex.py --manifest-dir force-app/main/default
    python3 check_custom_metadata_in_apex.py --manifest-dir .
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = "{http://soap.sforce.com/2006/04/metadata}"
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0, "WARN": 0}

APEX_SUFFIXES = {".cls", ".trigger"}
CMDT_TYPE_RE = re.compile(r"\b([A-Za-z][A-Za-z0-9_]*__mdt)\b")
TEST_ANNOTATION_RE = re.compile(r"@\s*is\s*test", re.IGNORECASE)
SEEALLDATA_RE = re.compile(r"SeeAllData\s*=\s*'?\s*true", re.IGNORECASE)
IS_RUNNING_TEST_RE = re.compile(r"\bTest\s*\.\s*isRunningTest\s*\(", re.IGNORECASE)
ENQUEUE_RE = re.compile(r"\bMetadata\s*\.\s*Operations\s*\.\s*enqueueDeployment\s*\(", re.IGNORECASE)
SOQL_MDT_RE = re.compile(r"\[\s*SELECT\b[^\]]*?\bFROM\s+[A-Za-z0-9_]*__mdt\b", re.IGNORECASE | re.DOTALL)
SOQL_OPEN_RE = re.compile(r"\[\s*SELECT\b", re.IGNORECASE)
LOOP_RE = re.compile(r"\b(for|while)\s*\(")
DML_VERBS = "insert|update|upsert|delete|undelete"
DML_INLINE_RE = re.compile(
    rf"\b({DML_VERBS})\s+(?:new\s+)?[A-Za-z0-9_<>,.\s]*__mdt\b", re.IGNORECASE
)
DATABASE_DML_RE = re.compile(
    rf"\bDatabase\s*\.\s*({DML_VERBS})\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE
)
# variable declarations whose type is (or contains) a __mdt
DECL_RES = [
    re.compile(r"\b([A-Za-z][A-Za-z0-9_]*__mdt)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?==|;|:)"),
    re.compile(r"\bList\s*<\s*[A-Za-z][A-Za-z0-9_]*__mdt\s*>\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?==|;|:)"),
    re.compile(r"\bSet\s*<\s*[A-Za-z][A-Za-z0-9_]*__mdt\s*>\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?==|;|:)"),
]


# --------------------------------------------------------------------------- io


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check an SFDX source tree for Custom Metadata Type mistakes.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for Apex classes, __mdt definitions and records.",
    )
    return parser.parse_args()


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str, exit_code: int | None = None) -> int:
    normalized = [normalize_finding(item) for item in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    if exit_code is not None:
        return exit_code
    return 1 if normalized else 0


# ------------------------------------------------------------------ xml helpers


def child(element, tag: str):
    """Return the first child with `tag` (namespaced or not), or None.

    NEVER write `element.find(a) or element.find(b)` — an ElementTree element with
    no children is falsy, so a real match with an empty body would be discarded.
    """
    found = element.find(MD_NS + tag)
    if found is not None:
        return found
    return element.find(tag)


def child_text(element, tag: str) -> str:
    found = child(element, tag)
    if found is None:
        return ""
    return (found.text or "").strip()


def children(element, tag: str) -> list:
    found = element.findall(MD_NS + tag)
    if found:
        return found
    return element.findall(tag)


def parse_xml(path: Path):
    try:
        return ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None


def local_name(tag: str) -> str:
    return tag.split("}")[-1]


# ------------------------------------------------------------------- discovery


def iter_apex(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in APEX_SUFFIXES)


def iter_xml(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.xml") if p.is_file())


def object_type_name(path: Path) -> str:
    """`Retry_Policy__mdt.object-meta.xml` -> `Retry_Policy__mdt`."""
    name = path.name
    for suffix in (".object-meta.xml", ".object"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return ""


def namespace_from_project(root: Path) -> str:
    for candidate in (root / "sfdx-project.json", root.parent / "sfdx-project.json"):
        if not candidate.is_file():
            continue
        try:
            data = json.loads(candidate.read_text(encoding="utf-8", errors="ignore"))
        except (ValueError, OSError):
            continue
        value = data.get("namespace")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


# ------------------------------------------------------------- metadata audits


def audit_object_definitions(paths: list[Path]) -> tuple[list[str], dict[str, str]]:
    """Check 3, and collect {type name -> visibility} for check 4."""
    findings: list[str] = []
    visibility: dict[str, str] = {}

    for path in paths:
        type_name = object_type_name(path)
        if not type_name.endswith("__mdt"):
            continue
        root = parse_xml(path)
        if root is None or local_name(root.tag) != "CustomObject":
            continue
        visibility[type_name] = child_text(root, "visibility") or "Public"

        for field in children(root, "fields"):
            field_name = child_text(field, "fullName")
            if child_text(field, "type") == "LongTextArea":
                findings.append(
                    f"MEDIUM {path}: field `{field_name or '(unnamed)'}` on {type_name} is a "
                    f"LongTextArea; getAll()/getInstance() truncate every field at 255 characters, "
                    f"so this field has no safe cache read path — see references/gotchas.md Gotcha 11"
                )
    return findings, visibility


def audit_field_files(paths: list[Path]) -> list[str]:
    """Check 3 for decomposed source format: objects/<Type>__mdt/fields/*.field-meta.xml."""
    findings: list[str] = []
    for path in paths:
        if not path.name.endswith(".field-meta.xml"):
            continue
        owner = path.parent.parent.name if path.parent.name == "fields" else ""
        if not owner.endswith("__mdt"):
            continue
        root = parse_xml(path)
        if root is None or local_name(root.tag) != "CustomField":
            continue
        if child_text(root, "type") == "LongTextArea":
            field_name = child_text(root, "fullName") or path.name
            findings.append(
                f"MEDIUM {path}: field `{field_name}` on {owner} is a LongTextArea; "
                f"getAll()/getInstance() truncate every field at 255 characters, so this field "
                f"has no safe cache read path — see references/gotchas.md Gotcha 11"
            )
    return findings


def audit_records(paths: list[Path], visibility: dict[str, str], namespace: str) -> list[str]:
    """Check 4: a CustomMetadata record with no <protected> where the type is packaged."""
    findings: list[str] = []
    for path in paths:
        name = path.name
        if not (name.endswith(".md-meta.xml") or name.endswith(".md")):
            continue
        root = parse_xml(path)
        if root is None or local_name(root.tag) != "CustomMetadata":
            continue

        stem = name[: -len(".md-meta.xml")] if name.endswith(".md-meta.xml") else name[: -len(".md")]
        type_stem = stem.split(".", 1)[0]
        type_visibility = visibility.get(type_stem + "__mdt", "")
        packaged = type_visibility in ("Protected", "PackageProtected") or bool(namespace)
        if not packaged:
            continue
        if child(root, "protected") is not None:
            continue

        reason = (
            f"its type declares visibility {type_visibility}"
            if type_visibility
            else f"sfdx-project.json declares namespace '{namespace}'"
        )
        findings.append(
            f"REVIEW {path}: CustomMetadata record declares no <protected> element and {reason}; "
            f"protected defaults to false, so this record ships readable to the subscriber"
        )
    return findings


# ----------------------------------------------------------------- apex audits


def strip_apex(src: str) -> str:
    """Blank string literals and comments in one left-to-right pass, preserving newlines
    so that line numbers still line up."""
    out: list[str] = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "'":
            j = i + 1
            while j < n and src[j] != "'":
                j += 2 if src[j] == "\\" else 1
            end = min(j + 1, n)
            out.append(" " * (end - i))
            i = end
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
            out.append("".join(c if c == "\n" else " " for c in src[i:j]))
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def declared_mdt_variables(code: str) -> set[str]:
    names: set[str] = set()
    for pattern in DECL_RES:
        for match in pattern.finditer(code):
            names.add(match.group(match.lastindex))
    return names


def audit_dml(path: Path, code: str) -> list[str]:
    findings: list[str] = []
    variables = declared_mdt_variables(code)

    for line_no, line in enumerate(code.splitlines(), start=1):
        if DML_INLINE_RE.search(line):
            findings.append(
                f"HIGH {path}:{line_no}: DML statement on a custom metadata type; custom metadata "
                f"records cannot be inserted, updated or deleted with DML — use "
                f"Metadata.Operations.enqueueDeployment (references/code-examples.md § 6)"
            )
            continue
        for match in re.finditer(rf"\b({DML_VERBS})\s+([A-Za-z_][A-Za-z0-9_]*)\s*;", line, re.IGNORECASE):
            if match.group(2) in variables:
                findings.append(
                    f"HIGH {path}:{line_no}: `{match.group(1)} {match.group(2)}` applies DML to a "
                    f"variable declared as a custom metadata type; the write path is a metadata "
                    f"deployment, not DML"
                )
        for match in DATABASE_DML_RE.finditer(line):
            if match.group(2) in variables:
                findings.append(
                    f"HIGH {path}:{line_no}: `Database.{match.group(1)}` applied to the custom "
                    f"metadata variable `{match.group(2)}`; Database DML is DML"
                )
    return findings


def audit_soql_in_loop(path: Path, code: str) -> list[str]:
    """Check 2. Tracks brace depth and the depths at which loops opened."""
    findings: list[str] = []
    depth = 0
    loop_depths: list[int] = []
    pending_loop = False

    for line_no, line in enumerate(code.splitlines(), start=1):
        in_loop_at_line_start = bool(loop_depths)

        if LOOP_RE.search(line):
            pending_loop = True

        if in_loop_at_line_start and SOQL_MDT_RE.search(line):
            findings.append(
                f"MEDIUM {path}:{line_no}: SOQL against a custom metadata type inside a loop; "
                f"hoist it out — `<Type>__mdt.getAll()` reads the same application cache once, "
                f"and the query costs nothing either way"
            )
        elif in_loop_at_line_start and SOQL_OPEN_RE.search(line) and CMDT_TYPE_RE.search(line):
            findings.append(
                f"MEDIUM {path}:{line_no}: SOQL against a custom metadata type inside a loop; "
                f"hoist it out — `<Type>__mdt.getAll()` reads the same application cache once, "
                f"and the query costs nothing either way"
            )

        for ch in line:
            if ch == "{":
                depth += 1
                if pending_loop:
                    loop_depths.append(depth)
                    pending_loop = False
            elif ch == "}":
                while loop_depths and loop_depths[-1] >= depth:
                    loop_depths.pop()
                depth = max(0, depth - 1)
        if ";" in line:
            pending_loop = False
    return findings


def audit_test_visibility(path: Path, code: str, is_test: bool) -> list[str]:
    if not is_test:
        return []
    if not SEEALLDATA_RE.search(code) or not CMDT_TYPE_RE.search(code):
        return []
    return [
        f"MEDIUM {path}: test uses SeeAllData=true while reading a custom metadata type; "
        f"metadata objects are already visible to tests without it, and the annotation drags "
        f"every other org record into the test with it — inject rows through a @TestVisible "
        f"static instead (references/code-examples.md § 4)"
    ]


def audit_enqueue(path: Path, code: str, is_test: bool) -> list[str]:
    if not ENQUEUE_RE.search(code):
        return []
    guarded = IS_RUNNING_TEST_RE.search(code) is not None
    if is_test:
        return [
            f"HIGH {path}: Metadata.Operations.enqueueDeployment is called from a test class; "
            f"assert the DeployContainer and invoke the DeployCallback directly instead "
            f"(references/code-examples.md § 7)"
        ]
    if not guarded:
        return [
            f"MEDIUM {path}: Metadata.Operations.enqueueDeployment has no Test.isRunningTest() "
            f"guard in this class; a test that reaches this line enqueues a real asynchronous "
            f"deployment"
        ]
    return []


def audit_apex(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    code = strip_apex(raw)
    if not CMDT_TYPE_RE.search(code) and not ENQUEUE_RE.search(code):
        return []
    is_test = TEST_ANNOTATION_RE.search(code) is not None

    findings: list[str] = []
    findings += audit_dml(path, code)
    findings += audit_soql_in_loop(path, code)
    findings += audit_test_visibility(path, code, is_test)
    findings += audit_enqueue(path, code, is_test)
    return findings


# ------------------------------------------------------------------------ main


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result(
            [f"HIGH {root}: manifest directory not found"],
            "Scanned nothing; --manifest-dir does not exist.",
            exit_code=1,
        )

    apex_files = iter_apex(root)
    xml_files = iter_xml(root)
    if not apex_files and not xml_files:
        return emit_result(
            [f"WARN {root}: no Apex or metadata XML files found under this directory"],
            "Scanned 0 files; nothing to audit.",
            exit_code=0,
        )

    findings: list[str] = []
    object_findings, visibility = audit_object_definitions(xml_files)
    findings += object_findings
    findings += audit_field_files(xml_files)
    findings += audit_records(xml_files, visibility, namespace_from_project(root))
    for path in apex_files:
        findings += audit_apex(path)

    summary = (
        f"Scanned {len(apex_files)} Apex file(s) and {len(xml_files)} metadata XML file(s) "
        f"across {len(visibility)} custom metadata type definition(s); "
        f"{len(findings)} finding(s) detected."
    )
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
