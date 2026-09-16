#!/usr/bin/env python3
"""Checker script for the apex/trigger-framework skill.

Scans a Salesforce DX metadata tree (``.trigger``, ``.cls`` and their
``-meta.xml`` companions) and reports, by severity:

  ERROR  TF-ONE-01   -- more than one ``.trigger`` file declared on the same
                        SObject. "If more than one trigger is defined on an
                        object for the same event, the order of trigger
                        execution isn't guaranteed" (Apex Developer Guide,
                        trigger considerations, apexdev L15503-15505). Undefined
                        ordering is a design failure, not a style preference.
  ERROR  TF-BODY-01  -- the trigger body contains logic beyond handler dispatch:
                        a SOQL query against anything other than the activation
                        settings object, a DML statement, a loop, an
                        ``addError()``, a field assignment, or an async enqueue.
                        A trigger's code block cannot contain the ``static``
                        keyword (apexdev L14989), so it cannot hold a recursion
                        guard either -- logic there is untestable in isolation
                        and cannot be guarded.
  ERROR  TF-RECUR-01 -- an after-update handler method performs DML on its own
                        SObject with no recursion guard anywhere in the class.
                        "Triggers can also modify other records of the same type
                        as the records that initially fired the trigger ...
                        because these changes can, in turn, fire more triggers"
                        (apexdev L14869-14872).
  ERROR  TF-PROV-01  -- a class or trigger in the tree references a canonical
                        ``templates/apex/**`` class that is not in the tree.
                        The deploy fails with ``Invalid type: <name>``. The rule
                        has no exceptions: ship the template verbatim in the
                        same deployment, or have an earlier plan step declare it.
  ERROR  TF-META-01  -- an ``ApexClass`` ``-meta.xml`` carries
                        ``<status>Inactive</status>``. ``ApexCodeUnitStatus``
                        "includes an Inactive option, but it's only supported
                        for ApexTrigger; it isn't supported for ApexClass"
                        (Metadata API Developer Guide, api_meta L22277-22278).
  ERROR  TF-OVER-01   -- a hook is declared with a bare ``override`` and no
                        access modifier, in a class pinned at ``apiVersion``
                        65.0 or later. "In API version 65.0 and later, an
                        abstract or override method requires a protected,
                        public, or global access modifier" (apexdev L3360).
  WARN   TF-SHARE-01 -- a per-object trigger handler declares no sharing
                        keyword. The ``.trigger`` file always runs in system
                        mode and cannot carry one, so the handler class is the
                        only place the decision is expressible.
  WARN   TF-BYPASS-01 -- nothing in the tree provides an activation bypass
                        (no ``TriggerControl``, ``Trigger_Setting__mdt`` or
                        ``TriggerSettings__c`` reference). Disabling a trigger
                        then requires a deployment.
  WARN   TF-META-02  -- a ``.cls`` or ``.trigger`` has no ``-meta.xml``
                        companion. The Metadata API requires one
                        (api_meta L22726).
  WARN   TF-EMPTY-01 -- the manifest directory contains no ``.trigger`` and no
                        ``.cls`` file. Advisory: a tree with no Apex in it is
                        not a failure.
  INFO   TF-DELTA-01 -- an after-update handler method never reads the old-state
                        map. Often fine; sometimes the reason a side effect
                        fires on every save.

Exit codes:
  0 -- no ERROR (and no WARN when --strict is passed)
  1 -- at least one ERROR, at least one WARN under --strict, or the
       --manifest-dir does not exist

Uses stdlib only -- no pip dependencies.

Usage:
    python3 check_trigger_framework.py --manifest-dir force-app/main/default
    python3 check_trigger_framework.py --manifest-dir force-app/main/default --strict
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Canonical templates/apex/** classes. A class that names one of these must
# ship it (agents/apex-builder/AGENT.md Step 6, template-class provenance).
CANONICAL_TEMPLATE_CLASSES = {
    "TriggerHandler",
    "TriggerControl",
    "ApplicationLogger",
    "TestDataFactory",
    "TestRecordBuilder",
    "MockHttpResponseGenerator",
    "SecurityUtils",
    "TestUserFactory",
    "BulkTestPattern",
    "BaseDomain",
    "BaseService",
    "BaseSelector",
    "HttpClient",
}

# Objects that legitimately appear in a trigger body: the activation-bypass
# lookup is the one query the body is allowed to run.
ACTIVATION_OBJECTS = ("Trigger_Setting__mdt", "TriggerSettings__c", "TriggerSetting__c")
ACTIVATION_SIGNALS = ACTIVATION_OBJECTS + ("TriggerControl", "isActive(")

# Any of these inside a class means somebody thought about re-entry.
RECURSION_GUARD_SIGNALS = (
    "skipOnce",
    "processedIds",
    "depthByHandler",
    "alreadyProcessed",
    "hasRun",
    "isRunning",
    "recursion",
    "reentr",
)

# A method *declaration*, not a call: `void afterUpdate(` / `void onAfterUpdate(`.
AFTER_UPDATE_METHOD_RE = re.compile(r"\bvoid\s+(?:on)?afterUpdate\s*\(", re.IGNORECASE)
TRIGGER_DECL_RE = re.compile(
    r"\btrigger\s+(\w+)\s+on\s+(\w+)\s*\(([^)]*)\)", re.IGNORECASE | re.DOTALL
)
CLASS_DECL_RE = re.compile(
    r"\b(?:public|global|private)\s+(?:(with|without|inherited)\s+sharing\s+)?"
    r"(?:virtual\s+|abstract\s+)?class\s+(\w+)",
    re.IGNORECASE,
)
SHARING_DECL_RE = re.compile(r"\b(?:with|without|inherited)\s+sharing\b", re.IGNORECASE)
BARE_OVERRIDE_RE = re.compile(r"^\s*(?:(?:static|virtual)\s+)*override\b", re.MULTILINE)
SOQL_FROM_RE = re.compile(r"\[\s*SELECT\b.*?\bFROM\s+(\w+)", re.IGNORECASE | re.DOTALL)
DML_RE = re.compile(
    r"(?<![\w.])(insert|update|upsert|delete|undelete)\s+(?!\s)([A-Za-z_]\w*)\s*;"
)
LOOP_RE = re.compile(r"\b(for|while)\s*\(")
FIELD_ASSIGN_RE = re.compile(r"\b\w+\.\w+\s*=(?!=)")
ASYNC_RE = re.compile(
    r"System\.enqueueJob\s*\(|Database\.executeBatch\s*\(|Messaging\.sendEmail\s*\("
)
LIST_DECL_RE = re.compile(r"\b(?:List|Set)\s*<\s*(\w+)\s*>\s+(\w+)\s*(?:=|;)")
SCALAR_DECL_RE = re.compile(r"^\s*(\w+)\s+(\w+)\s*=\s*new\s+\1\s*\(", re.MULTILINE)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def tag(local: str) -> str:
    """Return a Clark-notation tag for the Salesforce metadata namespace."""
    return f"{{{_SF_NS}}}{local}"


def child_text(parent, local: str) -> str | None:
    """Return the stripped text of a direct child element, or None.

    A leaf ``Element`` is falsy, so ``parent.find(a) or parent.find(b)`` is a
    trap that silently drops empty elements. Compare against None explicitly.
    """
    node = parent.find(tag(local))
    if node is None:
        return None
    if node.text is None:
        return ""
    return node.text.strip()


def strip_apex(src: str) -> str:
    """Blank `//` line comments, `/* … */` block comments, and `'…'` literals to spaces.

    Comments first so a possessive apostrophe inside a comment never opens a string.
    Replaces rather than deletes so character offsets are preserved and a match can
    still be turned back into a line number.
    """
    out: list[str] = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
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
                out.append("\n" if src[j] == "\n" else " ")
                j += 1
            i = j
            continue
        if ch == "'":
            out.append(" ")
            i += 1
            while i < n:
                if src[i] == "\n":
                    out.append("\n")
                    i += 1
                    break
                if src[i] == "\\" and i + 1 < n:
                    out.append(" ")
                    out.append(" ")
                    i += 2
                    continue
                if src[i] == "'":
                    if i + 1 < n and src[i + 1] == "'":
                        out.append(" ")
                        out.append(" ")
                        i += 2
                        continue
                    out.append(" ")
                    i += 1
                    break
                out.append(" ")
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def brace_block(text: str, open_index: int) -> str:
    """Return the source between the brace at/after open_index and its match."""
    start = text.find("{", open_index)
    if start < 0:
        return ""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : i]
    return text[start + 1 :]


def sobject_from_handler_name(name: str) -> str | None:
    """WorkOrderTriggerHandler -> WorkOrder. None when the name says nothing."""
    for suffix in ("TriggerHandler", "Handler"):
        if name.endswith(suffix) and len(name) > len(suffix):
            return name[: -len(suffix)]
    return None


def meta_api_version(source_file: Path) -> float | None:
    """Read apiVersion from the -meta.xml companion, or None if unreadable."""
    meta = source_file.with_name(source_file.name + "-meta.xml")
    if not meta.is_file():
        return None
    try:
        root = ET.fromstring(meta.read_bytes())
    except ET.ParseError:
        return None
    raw = child_text(root, "apiVersion")
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Collection
# ---------------------------------------------------------------------------


class Finding:
    def __init__(self, severity: str, rule: str, location: str, message: str):
        self.severity = severity
        self.rule = rule
        self.location = location
        self.message = message

    def render(self) -> str:
        return f"{self.rule} {self.location}: {self.message}"


def collect_sources(root: Path) -> tuple[list[Path], list[Path]]:
    triggers = sorted(p for p in root.rglob("*.trigger") if p.is_file())
    classes = sorted(p for p in root.rglob("*.cls") if p.is_file())
    return triggers, classes


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------


def check_trigger_body(path: Path, raw: str, rel: str) -> list[Finding]:
    """TF-BODY-01 -- anything in the body beyond handler dispatch."""
    findings: list[Finding] = []
    code = strip_apex(raw)
    decl = TRIGGER_DECL_RE.search(code)
    if decl is None:
        return findings
    body = brace_block(code, decl.end())

    offenders: list[str] = []

    for m in SOQL_FROM_RE.finditer(body):
        queried = m.group(1)
        if queried not in ACTIVATION_OBJECTS:
            offenders.append(f"SOQL against {queried}")

    for m in DML_RE.finditer(body):
        offenders.append(f"`{m.group(1)} {m.group(2)};` DML statement")

    for m in LOOP_RE.finditer(body):
        offenders.append(f"`{m.group(1)}` loop")

    if "addError(" in body:
        offenders.append("addError() call")

    if ASYNC_RE.search(body):
        offenders.append("async enqueue")

    # Field assignment, ignoring the activation-bypass local and the handler
    # local that the dispatch pattern legitimately declares.
    for m in FIELD_ASSIGN_RE.finditer(body):
        snippet = m.group(0).strip()
        if any(sig in snippet for sig in ACTIVATION_SIGNALS):
            continue
        offenders.append(f"field assignment `{snippet}`")

    if offenders:
        unique = sorted(set(offenders))
        findings.append(
            Finding(
                "ERROR",
                "TF-BODY-01",
                rel,
                "trigger body holds logic beyond handler dispatch: "
                + "; ".join(unique)
                + ". Move it to the handler class -- a trigger body cannot "
                "declare a static, so it cannot carry a recursion guard.",
            )
        )
    return findings


def check_recursion_guard(path: Path, raw: str, rel: str) -> list[Finding]:
    """TF-RECUR-01 / TF-DELTA-01 -- after-update self-DML without a guard."""
    findings: list[Finding] = []
    if path.stem in CANONICAL_TEMPLATE_CLASSES or not path.stem.endswith("TriggerHandler"):
        return findings  # base classes dispatch; they own no SObject of their own
    code = strip_apex(raw)
    decl = CLASS_DECL_RE.search(code)
    if decl is None:
        return findings
    class_name = decl.group(2)
    own_sobject = sobject_from_handler_name(class_name)
    if own_sobject is None:
        return findings

    method = AFTER_UPDATE_METHOD_RE.search(code)
    if method is None:
        return findings
    body = brace_block(code, method.end())
    if not body:
        return findings

    # Which locals in this method hold records of the handler's own SObject?
    own_locals = {
        var
        for typ, var in LIST_DECL_RE.findall(body)
        if typ.lower() == own_sobject.lower()
    }
    own_locals.update(
        var for typ, var in SCALAR_DECL_RE.findall(body) if typ.lower() == own_sobject.lower()
    )

    self_dml = [
        m.group(0).strip()
        for m in DML_RE.finditer(body)
        if m.group(2) in own_locals
    ]
    if self_dml:
        guarded = any(sig.lower() in code.lower() for sig in RECURSION_GUARD_SIGNALS)
        if not guarded:
            findings.append(
                Finding(
                    "ERROR",
                    "TF-RECUR-01",
                    rel,
                    f"after-update handler for {own_sobject} runs `{self_dml[0]}` on its "
                    f"own object with no recursion guard in {class_name}. The update "
                    "re-enters the same trigger. Call TriggerHandler.skipOnce() "
                    "immediately before the DML, or filter on a static Set<Id>.",
                )
            )

    if "oldmap" not in body.lower():
        findings.append(
            Finding(
                "INFO",
                "TF-DELTA-01",
                rel,
                f"the after-update path in {class_name} never reads the old-state map, "
                "so it cannot tell a real field change from any other save. Confirm "
                "that is intended before a workflow field update doubles the work.",
            )
        )
    return findings


def check_sharing(path: Path, raw: str, rel: str) -> list[Finding]:
    """TF-SHARE-01 -- per-object handler with no explicit sharing keyword."""
    findings: list[Finding] = []
    if path.stem in CANONICAL_TEMPLATE_CLASSES:
        return findings  # shipped verbatim; its posture belongs to the template
    if not path.stem.endswith("TriggerHandler"):
        return findings
    code = strip_apex(raw)
    decl = CLASS_DECL_RE.search(code)
    if decl is None:
        return findings
    if SHARING_DECL_RE.search(code[: decl.end()]) is None:
        findings.append(
            Finding(
                "WARN",
                "TF-SHARE-01",
                rel,
                f"{decl.group(2)} declares no sharing keyword. The .trigger file always "
                "runs in system mode and cannot carry one, so this class is the only "
                "place the decision exists -- and an absent keyword means opposite "
                "things below and above apiVersion 67.0. Write it out.",
            )
        )
    return findings


def check_bare_override(path: Path, raw: str, rel: str) -> list[Finding]:
    """TF-OVER-01 -- bare `override` at apiVersion 65.0 or later."""
    findings: list[Finding] = []
    code = strip_apex(raw)
    version = meta_api_version(path)
    for m in BARE_OVERRIDE_RE.finditer(code):
        if version is not None and version < 65.0:
            continue
        shown = "unknown" if version is None else f"{version:g}"
        findings.append(
            Finding(
                "ERROR",
                "TF-OVER-01",
                f"{rel}:{line_of(code, m.start())}",
                "hook declared with a bare `override` and no access modifier "
                f"(apiVersion {shown}). From API 65.0 an override method requires "
                "protected, public, or global -- without one it defaults to private "
                "and cannot override the base hook, so the class stops compiling.",
            )
        )
    return findings


def check_provenance(
    sources: list[tuple[Path, str, str]], present_classes: set[str]
) -> list[Finding]:
    """TF-PROV-01 -- referenced canonical template class not shipped."""
    findings: list[Finding] = []
    for path, raw, rel in sources:
        code = strip_apex(raw)
        for name in sorted(CANONICAL_TEMPLATE_CLASSES):
            if path.stem == name:
                continue
            if name in present_classes:
                continue
            if re.search(rf"\b{name}\b", code) is None:
                continue
            findings.append(
                Finding(
                    "ERROR",
                    "TF-PROV-01",
                    rel,
                    f"references the canonical template class `{name}`, which is not in "
                    "this tree. Deploy fails with `Invalid type: " + name + "`. Ship "
                    f"templates/apex/{name}.cls verbatim with its -meta.xml in this "
                    "deployment, or have an earlier plan step declare it.",
                )
            )
    return findings


def check_meta_files(sources: list[tuple[Path, str, str]]) -> list[Finding]:
    """TF-META-01 / TF-META-02 -- companion metadata files."""
    findings: list[Finding] = []
    for path, _raw, rel in sources:
        meta = path.with_name(path.name + "-meta.xml")
        if not meta.is_file():
            findings.append(
                Finding(
                    "WARN",
                    "TF-META-02",
                    rel,
                    f"has no {meta.name} companion. The Metadata API requires one "
                    "alongside every .cls and .trigger file.",
                )
            )
            continue
        try:
            root = ET.fromstring(meta.read_bytes())
        except ET.ParseError as exc:
            findings.append(
                Finding("ERROR", "TF-META-01", str(meta), f"malformed metadata XML -- {exc}")
            )
            continue
        local = root.tag.split("}")[-1]
        status = child_text(root, "status")
        if local == "ApexClass" and status == "Inactive":
            findings.append(
                Finding(
                    "ERROR",
                    "TF-META-01",
                    str(meta),
                    "ApexClass status is `Inactive`. ApexCodeUnitStatus includes an "
                    "Inactive option, but it is only supported for ApexTrigger -- it "
                    "is not supported for ApexClass. Use Active or Deleted.",
                )
            )
    return findings


def check_one_trigger_per_object(
    triggers: list[tuple[Path, str, str]]
) -> tuple[list[Finding], dict[str, list[str]]]:
    """TF-ONE-01 -- more than one trigger declared on the same SObject."""
    findings: list[Finding] = []
    by_object: dict[str, list[str]] = {}
    for path, raw, rel in triggers:
        decl = TRIGGER_DECL_RE.search(strip_apex(raw))
        if decl is None:
            continue
        by_object.setdefault(decl.group(2), []).append(rel)
    for sobject, paths in sorted(by_object.items()):
        if len(paths) > 1:
            findings.append(
                Finding(
                    "ERROR",
                    "TF-ONE-01",
                    sobject,
                    f"{len(paths)} triggers declared on this object ({', '.join(sorted(paths))}). "
                    "When more than one trigger is defined on an object for the same event "
                    "the firing order is not guaranteed. Consolidate into one trigger and "
                    "dispatch from the handler.",
                )
            )
    return findings, by_object


def check_bypass(all_sources: list[tuple[Path, str, str]]) -> list[Finding]:
    """TF-BYPASS-01 -- tree-level activation bypass reachable?"""
    if not all_sources:
        return []
    joined = "\n".join(strip_apex(raw) for _p, raw, _r in all_sources)
    if any(sig in joined for sig in ACTIVATION_SIGNALS):
        return []
    return [
        Finding(
            "WARN",
            "TF-BYPASS-01",
            "(tree)",
            "no activation bypass found anywhere in this tree -- no TriggerControl, "
            "Trigger_Setting__mdt or TriggerSettings__c reference. Disabling a trigger "
            "for a data load or an incident then requires a deployment.",
        )
    ]


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def print_block(title: str, findings: list[Finding]) -> None:
    if not findings:
        return
    print(title)
    for f in findings:
        print(f"  {f.render()}")
    print()


def print_inventory(by_object: dict[str, list[str]], handler_count: int) -> None:
    print("Trigger inventory (SObject -> trigger files):")
    if not by_object:
        print("  (no trigger declarations found)")
    else:
        width = max(len(name) for name in by_object)
        width = max(width, len("SObject"))
        print(f"  {'SObject':<{width}}  Triggers")
        print("  " + "-" * (width + 12))
        for sobject in sorted(by_object):
            print(f"  {sobject:<{width}}  {', '.join(sorted(by_object[sobject]))}")
    print(f"  handler classes seen: {handler_count}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit an Apex trigger package for framework and operability defects: "
            "one trigger per object, no logic in the trigger body, a recursion guard "
            "on same-object after-update DML, template-class provenance, explicit "
            "sharing, and companion metadata."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on warnings as well as errors.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.is_dir():
        print(f"ERROR: manifest directory not found: {manifest_dir}")
        return 1

    print(f"Scanning: {manifest_dir.resolve()}")
    print()

    trigger_paths, class_paths = collect_sources(manifest_dir)
    triggers = [(p, p.read_text(encoding="utf-8", errors="ignore"), str(p)) for p in trigger_paths]
    classes = [(p, p.read_text(encoding="utf-8", errors="ignore"), str(p)) for p in class_paths]
    all_sources = triggers + classes

    print(f"Trigger files: {len(triggers)}")
    print(f"Apex classes:  {len(classes)}")
    print()

    if not all_sources:
        print("WARN:")
        print(
            "  TF-EMPTY-01 "
            f"{manifest_dir}: no .trigger or .cls files found under this directory. "
            "Nothing to audit."
        )
        print()
        print("Summary: 0 error(s), 1 warning(s), 0 info.")
        if args.strict:
            print("--strict: failing on warnings.")
            return 1
        return 0

    present_classes = {p.stem for p, _r, _rel in classes}
    handler_count = sum(1 for p, _r, _rel in classes if p.stem.endswith("Handler"))

    findings: list[Finding] = []
    one_per_object, by_object = check_one_trigger_per_object(triggers)
    findings.extend(one_per_object)

    for path, raw, rel in triggers:
        findings.extend(check_trigger_body(path, raw, rel))

    for path, raw, rel in classes:
        findings.extend(check_recursion_guard(path, raw, rel))
        findings.extend(check_sharing(path, raw, rel))
        findings.extend(check_bare_override(path, raw, rel))

    findings.extend(check_provenance(all_sources, present_classes))
    findings.extend(check_meta_files(all_sources))
    findings.extend(check_bypass(all_sources))

    print_inventory(by_object, handler_count)

    errors = [f for f in findings if f.severity == "ERROR"]
    warnings = [f for f in findings if f.severity == "WARN"]
    infos = [f for f in findings if f.severity == "INFO"]

    print_block("ERROR:", errors)
    print_block("WARN:", warnings)
    print_block("INFO:", infos)

    print(
        f"Summary: {len(errors)} error(s), {len(warnings)} warning(s), {len(infos)} info."
    )

    if errors:
        return 1
    if args.strict and warnings:
        print("--strict: failing on warnings.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
