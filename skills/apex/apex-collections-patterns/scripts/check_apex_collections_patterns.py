#!/usr/bin/env python3
"""Audit Apex source for the collection defects this skill covers.

Static, stdlib-only, regex + bracket matching. It never compiles Apex and never
contacts an org: every finding is a place to look, not a proven defect.

Checks implemented
------------------
1. `List.contains(...)` evaluated inside a loop body               (WARN)
   O(n x m). "Apex uses a hash structure for all sets" (apexdev L1640) but no
   such structure is documented for List, so membership testing belongs on a Set.
2. A user-defined class used as a `Map` key or `Set` element while the same
   source tree never gives that class both `equals` and `hashCode`   (ERROR)
   "Uniqueness of map keys of user-defined types is determined by the equals and
   hashCode methods, which you provide in your classes" (apexdev L1700-L1701).
3. `remove(...)` called on the very collection a `for` loop is walking (ERROR)
   "Modifying a collection's elements while iterating through that collection is
   not supported and causes an error" (apexdev L3182-L3183).
4. A single-argument `new Map<K, V>(...)` whose key type is not `Id`  (ERROR)
   The only list-populating Map constructor is `Map<ID,sObject>(recordList)`
   (apexrefguide L222322-L222330).
5. Nested loops over two collections that compare `.Id` in the body   (WARN)
   The Map lookup this skill exists to teach.
6. `Set<String>` / `Map<String, ...>` keyed on record Ids, or a file mixing
   15-character and 18-character Id literals                     (ADVISORY)
   `Id` normalizes 15 to 18 (apexdev L1255); `String` does not, and set/map
   String elements are case-sensitive (apexrefguide L230262, apexdev L1697).
7. A bare `List.sort()` next to a comment implying a multi-field order (ADVISORY)
   Default sObject sort order is type label, Name, then standard then custom
   fields alphabetically (apexdev L10245-L10258) — rarely the business order.

Severity and exit code
----------------------
    ERROR     -> exit 1
    WARN      -> exit 0, unless --strict promotes it to ERROR
    ADVISORY  -> never affects the exit code
A missing --manifest-dir is always exit 1. A directory with no Apex files is a
WARN.

Usage:
    python3 check_apex_collections_patterns.py --manifest-dir force-app/main/default/classes
    python3 check_apex_collections_patterns.py --manifest-dir force-app --strict
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

APEX_SUFFIXES = (".cls", ".trigger")

DECL_RE = re.compile(r"\b(List|Set|Map)\s*<", re.IGNORECASE)
LOOP_RE = re.compile(r"\b(for|while)\s*\(", re.IGNORECASE)
FOREACH_RE = re.compile(
    r"\bfor\s*\(\s*(?:final\s+)?[A-Za-z_][\w<>,\s\[\]\.]*?\s+([A-Za-z_]\w*)\s*:\s*([^)]+?)\s*\)"
)
CLASSIC_FOR_RE = re.compile(
    r"\bfor\s*\(\s*Integer\s+(\w+)\s*=[^;]*;[^;]*?\b(\w+)\s*\.\s*size\s*\(\s*\)", re.IGNORECASE
)
CLASS_DECL_RE = re.compile(
    r"\b(?:global|public|private|protected)?\s*(?:virtual\s+|abstract\s+|with\s+sharing\s+|"
    r"without\s+sharing\s+|inherited\s+sharing\s+|static\s+)*class\s+([A-Za-z_]\w*)",
    re.IGNORECASE,
)
EQUALS_RE = re.compile(r"\bBoolean\s+equals\s*\(\s*Object\s+\w+\s*\)", re.IGNORECASE)
HASHCODE_RE = re.compile(r"\bInteger\s+hashCode\s*\(\s*\)", re.IGNORECASE)
SORT_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\.\s*sort\s*\(\s*\)")
ID_18_LITERAL_RE = re.compile(r"'([a-zA-Z0-9]{18})'")
ID_15_LITERAL_RE = re.compile(r"'([a-zA-Z0-9]{15})'")
ID_PREFIXED = re.compile(r"^[a-zA-Z0-9]{3}[0-9A-Za-z]")
MULTI_KEY_COMMENT_RE = re.compile(
    r"(?:then\s+by|,\s*then|sort(?:ed)?\s+by\s+[\w\.]+\s*(?:,|and|then)|order\s+by\s+[\w\.]+\s*,)",
    re.IGNORECASE,
)
STRING_SET_FEED_RE = re.compile(r"\.\s*add\s*\(\s*([^;()]*?\.\s*Id)\s*\)")
STRING_VALUEOF_ID_RE = re.compile(r"String\s*\.\s*valueOf\s*\(\s*[^;()]*?\.\s*Id\s*\)", re.IGNORECASE)

BUILTIN_TYPES = {
    "id", "string", "integer", "long", "decimal", "double", "boolean", "date",
    "datetime", "time", "blob", "object", "sobject", "type", "schema.sobjecttype",
    "schema.sobjectfield", "sobjectfield", "sobjecttype",
}


# ---------------------------------------------------------------- source prep

def sanitize(src: str) -> str:
    """Blank string literals and comments, preserving length and newlines so
    that every offset in the result maps to the same offset in the original."""
    out = list(src)
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "'":
            j = i + 1
            while j < n and src[j] != "'":
                if src[j] == "\\":
                    out[j] = " "
                    j += 1
                if j < n:
                    out[j] = " " if src[j] != "\n" else "\n"
                j += 1
            out[i] = " "
            if j < n:
                out[j] = " "
            i = j + 1
            continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            for k in range(i, j):
                out[k] = " "
            i = j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            for k in range(i, j):
                if src[k] != "\n":
                    out[k] = " "
            i = j
            continue
        i += 1
    return "".join(out)


def match_bracket(text: str, start: int, opener: str, closer: str) -> int:
    """Index just past the closer matching the opener at `start`, or -1."""
    if start < 0 or start >= len(text) or text[start] != opener:
        return -1
    depth = 0
    for idx in range(start, len(text)):
        if text[idx] == opener:
            depth += 1
        elif text[idx] == closer:
            depth -= 1
            if depth == 0:
                return idx + 1
    return -1


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def collection_declarations(clean: str) -> dict[str, str]:
    """variable name -> 'list' | 'set' | 'map', from `List<...> name` style
    declarations. Generic arguments are bracket-matched so nesting is safe."""
    found: dict[str, str] = {}
    for m in DECL_RE.finditer(clean):
        kind = m.group(1).lower()
        open_angle = clean.find("<", m.start())
        close = match_bracket(clean, open_angle, "<", ">")
        if close == -1:
            continue
        tail = clean[close:close + 80]
        name = re.match(r"\s*([A-Za-z_]\w*)\s*(?==|;|\)|,|:)", tail)
        if name:
            found.setdefault(name.group(1), kind)
    for m in re.finditer(r"\b([A-Za-z_][\w\.]*)\s*\[\s*\]\s+([A-Za-z_]\w*)", clean):
        found.setdefault(m.group(2), "list")
    return found


def loop_bodies(clean: str) -> list[tuple[int, int, str]]:
    """(body_start, body_end, header_text) for every for/while in the source."""
    bodies: list[tuple[int, int, str]] = []
    for m in LOOP_RE.finditer(clean):
        paren = clean.find("(", m.start())
        header_end = match_bracket(clean, paren, "(", ")")
        if header_end == -1:
            continue
        header = clean[m.start():header_end]
        rest = clean[header_end:]
        brace_offset = len(rest) - len(rest.lstrip())
        if header_end + brace_offset < len(clean) and clean[header_end + brace_offset] == "{":
            body_start = header_end + brace_offset
            body_end = match_bracket(clean, body_start, "{", "}")
            if body_end == -1:
                continue
        else:  # single-statement loop body
            semi = clean.find(";", header_end)
            body_start, body_end = header_end, (len(clean) if semi < 0 else semi + 1)
        bodies.append((body_start, body_end, header))
    return bodies


# ------------------------------------------------------------------- checks

def check_list_contains_in_loop(path, clean, decls, bodies) -> list[tuple[str, str]]:
    out = []
    for body_start, body_end, _header in bodies:
        body = clean[body_start:body_end]
        for m in re.finditer(r"\b([A-Za-z_]\w*)\s*\.\s*contains\s*\(", body):
            var = m.group(1)
            if decls.get(var) == "list":
                out.append((
                    "WARN",
                    f"{path}:{line_of(clean, body_start + m.start())}: "
                    f"List.contains() on '{var}' inside a loop is a linear scan per iteration "
                    f"(O(n x m)); build a Set once outside the loop and test membership on it",
                ))
    return out


def check_remove_while_iterating(path, clean, bodies) -> list[tuple[str, str]]:
    out = []
    for body_start, body_end, header in bodies:
        targets: set[str] = set()
        fe = FOREACH_RE.search(header)
        if fe:
            expr = fe.group(2).strip()
            base = re.match(r"^([A-Za-z_]\w*)", expr)
            if base:
                targets.add(base.group(1))
        cf = CLASSIC_FOR_RE.search(header)
        if cf:
            targets.add(cf.group(2))
        if not targets:
            continue
        body = clean[body_start:body_end]
        for m in re.finditer(r"\b([A-Za-z_]\w*)\s*\.\s*(remove|add|addAll|clear)\s*\(", body):
            if m.group(1) in targets:
                out.append((
                    "ERROR",
                    f"{path}:{line_of(clean, body_start + m.start())}: "
                    f"'{m.group(1)}.{m.group(2)}()' mutates the collection this loop is iterating; "
                    f"collect the elements in a temporary collection and apply the change after the loop",
                ))
    return out


def check_nested_loop_id_compare(path, clean, bodies) -> list[tuple[str, str]]:
    out = []
    for outer_start, outer_end, outer_header in bodies:
        outer_fe = FOREACH_RE.search(outer_header)
        if not outer_fe:
            continue
        outer_var = outer_fe.group(1)
        for inner_start, inner_end, inner_header in bodies:
            if not (outer_start < inner_start and inner_end <= outer_end):
                continue
            inner_fe = FOREACH_RE.search(inner_header)
            if not inner_fe or inner_fe.group(1) == outer_var:
                continue
            inner_var = inner_fe.group(1)
            body = clean[inner_start:inner_end]
            pattern = re.compile(
                rf"\b(?:{re.escape(outer_var)}|{re.escape(inner_var)})\s*\.\s*\w*Id\w*\s*"
                rf"(?:==|!=)\s*\b(?:{re.escape(outer_var)}|{re.escape(inner_var)})\s*\.",
                re.IGNORECASE,
            )
            hit = pattern.search(body)
            if hit:
                out.append((
                    "WARN",
                    f"{path}:{line_of(clean, inner_start + hit.start())}: "
                    f"nested loops over '{outer_var}' and '{inner_var}' matched by Id; "
                    f"index the inner collection into a Map once and look up in O(1)",
                ))
    return out


def check_map_constructor_key_type(path, clean) -> list[tuple[str, str]]:
    out = []
    for m in re.finditer(r"\bnew\s+Map\s*<", clean):
        open_angle = clean.find("<", m.start())
        close = match_bracket(clean, open_angle, "<", ">")
        if close == -1:
            continue
        params = clean[open_angle + 1:close - 1]
        key_type = params.split(",", 1)[0].strip().lower()
        rest = clean[close:]
        offset = len(rest) - len(rest.lstrip())
        if close + offset >= len(clean) or clean[close + offset] != "(":
            continue  # `new Map<..>{...}` literal, not the constructor
        arg_end = match_bracket(clean, close + offset, "(", ")")
        if arg_end == -1:
            continue
        arg = clean[close + offset + 1:arg_end - 1].strip()
        if not arg:
            continue
        if key_type in ("id",):
            continue
        # A copy constructor `new Map<String,X>(otherMap)` is legal; only the
        # list-populating form is Id-only. Treat a SOQL literal or a name that
        # reads like a list as the list form.
        looks_like_list = arg.startswith("[") or re.search(r"(list|records|rows|scope|s)$", arg, re.IGNORECASE)
        if looks_like_list and not re.search(r"map", arg, re.IGNORECASE):
            out.append((
                "ERROR",
                f"{path}:{line_of(clean, m.start())}: "
                f"new Map<{params.strip()}>({arg}) — the only list-populating Map constructor is "
                f"Map<ID,sObject>(recordList); key on Id, or build the map in an explicit loop",
            ))
    return out


def check_id_string_keys(path, raw, clean) -> list[tuple[str, str]]:
    out = []
    string_keyed = re.search(r"\b(?:Set\s*<\s*String\s*>|Map\s*<\s*String\s*,)", clean, re.IGNORECASE)
    if string_keyed:
        fed = STRING_SET_FEED_RE.search(clean) or STRING_VALUEOF_ID_RE.search(clean)
        if fed:
            out.append((
                "ADVISORY",
                f"{path}:{line_of(clean, fed.start())}: "
                f"a String-keyed collection is being fed record Ids; String keys are case-sensitive "
                f"and are not normalized from 15 to 18 characters — use Set<Id>/Map<Id, ...>",
            ))
    # literals live in the raw source; sanitize() blanks string bodies
    fifteens = [v for v in ID_15_LITERAL_RE.findall(raw) if ID_PREFIXED.match(v)]
    eighteens = [v for v in ID_18_LITERAL_RE.findall(raw) if ID_PREFIXED.match(v)]
    if fifteens and eighteens:
        out.append((
            "ADVISORY",
            f"{path}: file mixes 15-character and 18-character Id-shaped literals "
            f"({len(fifteens)} and {len(eighteens)}); the two forms are distinct String values "
            f"even when they name the same record",
        ))
    return out


def check_bare_sort(path, raw, clean, decls) -> list[tuple[str, str]]:
    out = []
    lines = raw.splitlines()
    for m in SORT_RE.finditer(clean):
        var = m.group(1)
        if decls.get(var) != "list":
            continue
        line_no = line_of(clean, m.start())
        window = "\n".join(lines[max(0, line_no - 4):line_no])
        comment = "\n".join(
            ln for ln in window.splitlines()
            if ln.strip().startswith("//") or ln.strip().startswith("*")
        )
        if comment and MULTI_KEY_COMMENT_RE.search(comment):
            out.append((
                "ADVISORY",
                f"{path}:{line_no}: bare '{var}.sort()' next to a comment implying a multi-field "
                f"order; List.sort() with no argument uses the platform default sequence — pass a "
                f"Comparator, or wrap the record in a Comparable class",
            ))
    return out


def check_custom_keys(files: list[tuple[Path, str]]) -> list[tuple[str, str]]:
    """Cross-file: a user class used as a Map key or Set element must define
    both equals(Object) and hashCode()."""
    classes: dict[str, dict] = {}
    for path, clean in files:
        for m in CLASS_DECL_RE.finditer(clean):
            name = m.group(1)
            brace = clean.find("{", m.end())
            if brace == -1:
                continue
            end = match_bracket(clean, brace, "{", "}")
            body = clean[brace:end] if end != -1 else clean[brace:]
            classes[name] = {
                "equals": bool(EQUALS_RE.search(body)),
                "hashCode": bool(HASHCODE_RE.search(body)),
                "path": path,
            }
    out = []
    seen: set[tuple[str, str]] = set()
    for path, clean in files:
        for m in re.finditer(
            r"\b(?:Set\s*<\s*([A-Za-z_]\w*)\s*>|Map\s*<\s*([A-Za-z_]\w*)\s*,)", clean
        ):
            name = m.group(1) or m.group(2)
            if name.lower() in BUILTIN_TYPES or name not in classes:
                continue
            info = classes[name]
            missing = [k for k in ("equals", "hashCode") if not info[k]]
            if not missing:
                continue
            key = (str(path), name)
            if key in seen:
                continue
            seen.add(key)
            out.append((
                "ERROR",
                f"{path}:{line_of(clean, m.start())}: "
                f"'{name}' is used as a Map key or Set element but defines no "
                f"{' and no '.join(missing)} (declared in {info['path'].name}); without both, "
                f"user-defined types compare by reference and every instance is a distinct entry",
            ))
    return out


# --------------------------------------------------------------------- main

def audit_file(path: Path, raw: str, clean: str) -> list[tuple[str, str]]:
    decls = collection_declarations(clean)
    bodies = loop_bodies(clean)
    findings: list[tuple[str, str]] = []
    findings += check_list_contains_in_loop(path, clean, decls, bodies)
    findings += check_remove_while_iterating(path, clean, bodies)
    findings += check_nested_loop_id_compare(path, clean, bodies)
    findings += check_map_constructor_key_type(path, clean)
    findings += check_id_string_keys(path, raw, clean)
    findings += check_bare_sort(path, raw, clean, decls)
    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex source for List/Set/Map defects: linear membership tests in "
                    "loops, custom Map keys without equals/hashCode, mutation while iterating, "
                    "misuse of the Map constructor, nested-loop Id matching, and Id-as-String keys."
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Apex source tree to scan (e.g. force-app/main/default/classes).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote WARN findings to ERROR so they affect the exit code.",
    )
    return parser.parse_args()


def emit(findings: list[tuple[str, str]], summary: str, strict: bool) -> int:
    order = {"ERROR": 0, "WARN": 1, "ADVISORY": 2}
    findings = sorted(dict.fromkeys(findings), key=lambda f: (order.get(f[0], 3), f[1]))
    for severity, message in findings:
        effective = "ERROR" if (strict and severity == "WARN") else severity
        stream = sys.stderr if effective == "ERROR" else sys.stdout
        print(f"{effective}: {message}", file=stream)
    print(summary)
    fatal = any(
        s == "ERROR" or (strict and s == "WARN") for s, _ in findings
    )
    return 1 if fatal else 0


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: manifest directory not found: {root}", file=sys.stderr)
        return 1
    paths = sorted(
        p for p in root.rglob("*") if p.is_file() and p.suffix in APEX_SUFFIXES
    )
    if not paths:
        print(f"WARN: no .cls or .trigger files under {root}", file=sys.stdout)
        print("Scanned 0 Apex files.")
        return 1 if args.strict else 0

    parsed: list[tuple[Path, str]] = []
    findings: list[tuple[str, str]] = []
    for path in paths:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        clean = sanitize(raw)
        parsed.append((path, clean))
        findings += audit_file(path, raw, clean)
    findings += check_custom_keys(parsed)

    summary = f"Scanned {len(paths)} Apex file(s); {len(findings)} collection finding(s)."
    return emit(findings, summary, args.strict)


if __name__ == "__main__":
    sys.exit(main())
