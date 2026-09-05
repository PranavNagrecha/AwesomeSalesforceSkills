#!/usr/bin/env python3
"""check_recursive_trigger_prevention.py — audit an Apex source tree for the recursion-guard
shapes that break under bulk, partial success, and Apex<->Flow re-entry.

Stdlib only. Regex-based: this reads Apex as text and never claims to compile it. Every rule
below maps to a documented platform behaviour cited in ../references/gotchas.md.

Rules
  ERROR    static Boolean guard named like hasRun / isExecuting / alreadyRan / firstRun that is
           never assigned false anywhere in the tree. A static "persists across these trigger
           invocations" (apexdev L3738-3740) and a DML over 200 rows invokes the trigger once
           per batch (apexdev L15029-15033), so a never-reset flag silences batches 2..N.
  WARN     more than one .trigger file on the same sObject. "If more than one trigger is defined
           on an object for the same event, the order of trigger execution isn't guaranteed"
           (apexdev L15502-15504), so guard state set by one may not be visible to the other.
  WARN     a .trigger body containing logic rather than a one-line handler dispatch. A static
           declared in a trigger "doesn't retain its value between different trigger contexts"
           (apexdev L3761-3763).
  WARN     a handler performing DML on the same sObject as its trigger with no processed-set
           guard in the file.
  ADVISORY a static Set/Map guard with no @TestVisible reset hook.
  ADVISORY a trigger whose handler never consults the framework bypass (TriggerControl /
           isActive / bypass), so a data load has no switch.

Exit codes
  0  no ERROR findings (WARN/ADVISORY may be present), or --strict not set
  1  any ERROR finding; or, with --strict, any ERROR or WARN finding
  1  --manifest-dir does not exist
  0  --manifest-dir exists but holds no Apex (a WARN is emitted)

Usage
  python3 check_recursive_trigger_prevention.py --manifest-dir force-app
  python3 check_recursive_trigger_prevention.py --manifest-dir force-app --strict
  python3 check_recursive_trigger_prevention.py --manifest-dir force-app --format json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ERROR, WARN, ADVISORY = "ERROR", "WARN", "ADVISORY"
SEVERITY_WEIGHTS = {ERROR: 20, WARN: 8, ADVISORY: 2}

BOOL_GUARD_NAMES = r"(?:has[_]?Run|is[_]?Executing|is[_]?Running|already[_]?Ran|already[_]?Run|first[_]?Run|hasFired|isFirstTime)"
STATIC_BOOL_RE = re.compile(
    r"\bstatic\s+(?:final\s+)?Boolean\s+(" + BOOL_GUARD_NAMES + r"\w*)\b", re.IGNORECASE
)
STATIC_SET_RE = re.compile(
    r"\bstatic\s+(?:final\s+)?(?:Set\s*<\s*Id\s*>|Map\s*<[^>]*>)\s+(\w+)", re.IGNORECASE
)
TRIGGER_DECL_RE = re.compile(
    r"\btrigger\s+(\w+)\s+on\s+(\w+)\s*\(([^)]*)\)", re.IGNORECASE | re.DOTALL
)
DML_RE = re.compile(r"^\s*(insert|update|upsert|delete|undelete)\s+[\w\[]", re.IGNORECASE | re.MULTILINE)
DATABASE_DML_RE = re.compile(r"\bDatabase\.(insert|update|upsert|delete|undelete)\s*\(", re.IGNORECASE)
NEW_SOBJECT_RE = re.compile(r"\bnew\s+(\w+)\s*\(\s*Id\s*=", re.IGNORECASE)
TESTVISIBLE_RESET_RE = re.compile(
    r"@TestVisible[^;{]{0,200}?\b(?:void\s+)?(\w*(?:reset|clear)\w*)\s*\(", re.IGNORECASE | re.DOTALL
)
BYPASS_RE = re.compile(r"TriggerControl|isActive\s*\(|bypass|skipOnce|kill[_]?switch", re.IGNORECASE)
HANDLER_DISPATCH_RE = re.compile(r"\bnew\s+\w+\s*\([^)]*\)\s*\.\s*\w+\s*\(", re.IGNORECASE)
GUARD_LOOKUP_RE = re.compile(
    r"\.contains\s*\(|\.containsKey\s*\(|isProcessed\s*\(|isAlreadyProcessed\s*\(|hasBeenProcessed\s*\(",
    re.IGNORECASE,
)
SKIP_DIR_NAMES = {".git", "node_modules", ".sfdx", ".sf", "__pycache__"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Audit Apex triggers and handlers for recursion-guard anti-patterns.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Apex source tree to scan (e.g. force-app).",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Promote WARN findings to failures (exit 1). ADVISORY never fails the run.",
    )
    p.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format. json (default) is machine-readable; text is one line per finding.",
    )
    return p.parse_args()


def strip_apex(src: str) -> str:
    """Blank string literals and comments in one left-to-right pass, preserving line count so
    reported line numbers stay accurate. An apostrophe inside a comment must not open a string,
    and a '/*' inside a string must not open a comment — order of checks matters."""
    out: list[str] = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "'":
            j = i + 1
            while j < n and src[j] != "'":
                j += 2 if src[j] == "\\" else 1
            out.append(" " * (min(j, n - 1) - i + 1))
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
            out.append("".join(c if c == "\n" else " " for c in src[i:j]))
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def iter_apex(root: Path) -> list[Path]:
    found: list[Path] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in {".cls", ".trigger"}:
            found.append(path)
    return sorted(found)


DECLARATION_TAIL_RE = re.compile(r"\bBoolean\s+$", re.IGNORECASE)


def has_real_reset(name: str, tree: str) -> bool:
    """True when `name = false` appears somewhere that is not its own declaration.

    `public static Boolean hasRun = false;` is a declaration, not a reset — the initializer
    runs once per transaction and says nothing about whether the guard is ever cleared again.
    """
    pattern = re.compile(r"\b" + re.escape(name) + r"\s*=\s*false\b", re.IGNORECASE)
    for m in pattern.finditer(tree):
        preceding = tree[max(0, m.start() - 40) : m.start()]
        if DECLARATION_TAIL_RE.search(preceding):
            continue
        return True
    return False


def finding(severity: str, path: Path, line: int, rule: str, message: str) -> dict:
    return {
        "severity": severity,
        "location": f"{path}:{line}",
        "rule": rule,
        "message": message,
    }


def trigger_body(code: str, match: re.Match) -> str:
    """Return the text between the trigger's outermost braces."""
    start = code.find("{", match.end())
    if start < 0:
        return ""
    depth, i, n = 0, start, len(code)
    while i < n:
        if code[i] == "{":
            depth += 1
        elif code[i] == "}":
            depth -= 1
            if depth == 0:
                return code[start + 1 : i]
        i += 1
    return code[start + 1 :]


def audit_tree(files: list[Path]) -> list[dict]:
    findings: list[dict] = []
    sources: dict[Path, str] = {}
    for path in files:
        sources[path] = strip_apex(path.read_text(encoding="utf-8", errors="ignore"))

    whole_tree = "\n".join(sources.values())

    triggers_by_object: dict[str, list[tuple[Path, str]]] = defaultdict(list)

    for path, code in sources.items():
        is_trigger = path.suffix.lower() == ".trigger"

        # --- ERROR: never-reset static Boolean guard -------------------------------------
        for m in STATIC_BOOL_RE.finditer(code):
            name = m.group(1)
            if has_real_reset(name, whole_tree):
                continue
            findings.append(
                finding(
                    ERROR,
                    path,
                    line_of(code, m.start()),
                    "never-reset-boolean-guard",
                    f"static Boolean '{name}' is used as a recursion guard and is never assigned "
                    "false anywhere in the tree. Statics persist across every trigger invocation in "
                    "a transaction (apexdev L3738-3740) and a DML over 200 rows invokes the trigger "
                    "once per batch (apexdev L15029-15033), so records 201+ are silently skipped. "
                    "Key the guard by record Id instead.",
                )
            )

        # --- ADVISORY: static Set/Map guard without a @TestVisible reset -------------------
        if STATIC_SET_RE.search(code) and GUARD_LOOKUP_RE.search(code):
            if not TESTVISIBLE_RESET_RE.search(code):
                m = STATIC_SET_RE.search(code)
                findings.append(
                    finding(
                        ADVISORY,
                        path,
                        line_of(code, m.start()),
                        "guard-without-testvisible-reset",
                        "a static Set/Map recursion guard has no @TestVisible reset hook. Statics are "
                        "reinitialised between test METHODS (apexdev L41032-41035) but not between two "
                        "DML statements inside one method — which is the case a recursion test must "
                        "drive. Add '@TestVisible static void reset()'.",
                    )
                )

        if not is_trigger:
            continue

        for m in TRIGGER_DECL_RE.finditer(code):
            trigger_name, sobject, _events = m.group(1), m.group(2), m.group(3)
            triggers_by_object[sobject.lower()].append((path, trigger_name))
            body = trigger_body(code, m)

            # --- WARN: logic in the trigger body ------------------------------------------
            statements = [s.strip() for s in body.split(";") if s.strip()]
            has_control_flow = re.search(r"\b(if|for|while|switch\s+on)\b", body) is not None
            if has_control_flow or len(statements) > 1 or not HANDLER_DISPATCH_RE.search(body):
                findings.append(
                    finding(
                        WARN,
                        path,
                        line_of(code, m.start()),
                        "logic-in-trigger-body",
                        f"trigger '{trigger_name}' contains logic rather than a single handler "
                        "dispatch line. Guard state declared in a .trigger file does not survive "
                        "between trigger contexts in the same transaction (apexdev L3761-3763); move "
                        "the body into a TriggerHandler subclass.",
                    )
                )

            # --- ADVISORY: no bypass reachable -------------------------------------------
            if not BYPASS_RE.search(body) and not any(
                BYPASS_RE.search(other) for p, other in sources.items() if p.suffix.lower() == ".cls"
            ):
                findings.append(
                    finding(
                        ADVISORY,
                        path,
                        line_of(code, m.start()),
                        "no-framework-bypass",
                        f"trigger '{trigger_name}' has no reachable bypass check (TriggerControl / "
                        "isActive / bypass). A data load then has no switch other than editing code. "
                        "See templates/apex/TriggerControl.cls.",
                    )
                )

            # --- WARN: same-object DML in the handler with no guard ------------------------
            handler = re.search(r"\bnew\s+(\w+)\s*\(", body)
            if not handler:
                continue
            handler_name = handler.group(1)
            for hpath, hcode in sources.items():
                if hpath.suffix.lower() != ".cls" or hpath.stem != handler_name:
                    continue
                writes_same_object = any(
                    sobject.lower() in hcode[max(0, dm.start() - 400) : dm.end() + 200].lower()
                    for dm in list(DML_RE.finditer(hcode)) + list(DATABASE_DML_RE.finditer(hcode))
                ) or any(
                    sm.group(1).lower() == sobject.lower() for sm in NEW_SOBJECT_RE.finditer(hcode)
                )
                if writes_same_object and not GUARD_LOOKUP_RE.search(hcode):
                    findings.append(
                        finding(
                            WARN,
                            hpath,
                            1,
                            "self-dml-without-guard",
                            f"handler '{handler_name}' issues DML that appears to touch {sobject}, "
                            f"the same sObject as trigger '{trigger_name}', with no processed-set "
                            "lookup (contains / containsKey / isProcessed) anywhere in the class. "
                            "That is the classic self-DML re-entry loop; the ceiling is a stack depth "
                            "of 16 (apexdev L19559).",
                        )
                    )

    # --- WARN: more than one trigger on the same sObject ---------------------------------
    for sobject, entries in sorted(triggers_by_object.items()):
        if len(entries) < 2:
            continue
        names = ", ".join(f"{name} ({path})" for path, name in entries)
        findings.append(
            finding(
                WARN,
                entries[0][0],
                1,
                "multiple-triggers-one-sobject",
                f"{len(entries)} triggers found on '{sobject}': {names}. "
                "\"If more than one trigger is defined on an object for the same event, the order of "
                "trigger execution isn't guaranteed\" (apexdev L15502-15504), so guard state set by "
                "one may or may not be visible to the other. Consolidate to one trigger.",
            )
        )

    return findings


def emit(findings: list[dict], summary: str, fmt: str) -> None:
    if fmt == "text":
        for f in findings:
            print(f"{f['severity']} {f['location']} [{f['rule']}] {f['message']}")
        print(summary)
        return
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(f["severity"], 0) for f in findings))
    print(json.dumps({"score": score, "findings": findings, "summary": summary}, indent=2))


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)

    if not root.exists() or not root.is_dir():
        print(f"ERROR: --manifest-dir '{root}' does not exist or is not a directory", file=sys.stderr)
        return 1

    files = iter_apex(root)
    if not files:
        summary = f"Scanned 0 Apex files under {root}; nothing to check."
        emit(
            [
                finding(
                    WARN,
                    root,
                    1,
                    "no-apex-found",
                    "no .cls or .trigger files under --manifest-dir. Point it at the source tree "
                    "root (e.g. force-app), not at the manifest folder.",
                )
            ],
            summary,
            args.format,
        )
        return 1 if args.strict else 0

    findings = audit_tree(files)
    counts = {s: sum(1 for f in findings if f["severity"] == s) for s in (ERROR, WARN, ADVISORY)}
    summary = (
        f"Scanned {len(files)} Apex file(s) under {root}; "
        f"{counts[ERROR]} ERROR, {counts[WARN]} WARN, {counts[ADVISORY]} ADVISORY."
    )
    emit(findings, summary, args.format)

    if counts[ERROR]:
        return 1
    if args.strict and counts[WARN]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
