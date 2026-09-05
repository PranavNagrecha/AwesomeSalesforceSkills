#!/usr/bin/env python3
"""Audit Apex source for the SOQL relationship-query defects this skill covers.

Static, stdlib-only, regex over sanitized source. It never compiles Apex, never
parses SOQL properly, and never contacts an org: every finding is a place to
look, not a proven defect.

Checks implemented
------------------
1. A `__c` custom-field token used where a relationship traversal was intended,
   i.e. `Something__c.Field` inside a SOQL string                        (ERROR)
   The parent pointer and the relationship name are different tokens: for a
   relationship field `MyRel`, "the parent object pointer becomes MyRel__c, and
   the relationship name is MyRel__r" (object_reference L3030-L3032). Dotting
   into the `__c` pointer does not traverse. The same rule catches a subquery
   whose FROM names an object API name (`FROM My_Child__c`) instead of a child
   relationship name.
2. A child-to-parent traversal chain deeper than five dots                (ERROR)
   The five-level relationship-depth cap is stated in the SOQL and SOSL
   Reference, which is not in this repo's offline corpus; the rule is retained
   because exceeding it is a parse error in the org, but the threshold itself
   carries an UNVERIFIED marker in SKILL.md.
3. More than 20 subqueries in a single SELECT                            (ERROR)
   Same provenance caveat as #2. The grounded companion constraint is that each
   parent-child relationship "counts as an extra query" against a pool of three
   times the top-level limit, read from `Limits.getLimitAggregateQueries()`
   (apexdev L19613-L19616) - a query with this many subqueries is a limits
   problem regardless of the parse-time cap.
4. A subquery nested inside a subquery, `(SELECT ... (SELECT`            (ERROR)
   Parent-to-child nesting is one level only. Every subquery example in the
   Apex guide is single-level (apexdev L11704, L12160, L17801, L20249).
5. Iterating `parent.Children__r` / `parent.Contacts` without a null or isEmpty
   guard, where the query filtered the subquery with a WHERE            (ADVISORY)
   A filtered subquery is the case most likely to yield no children for some
   parent. The Apex guide's dynamic sample guards the same shape under the
   comment "Prevent a null relationship from being accessed"
   (apexdev L11719-L11721).
6. SOQL inside a `for` loop body                                          (WARN)
   Deliberately one rule, not a family: bulkification and selector-layer
   checkers own this. Kept here because the relationship subquery is the
   documented fix - the guide's own `LimitExample` / `EnhancedLimitExample`
   pair (apexdev L20228-L20255).
7. `WITH SECURITY_ENFORCED` in a class whose meta.xml apiVersion is >= 67.0
                                                                         (ERROR)
   "In API version 67.0 and later, you can't use the WITH SECURITY_ENFORCED
   clause in SOQL SELECT queries in Apex code. Instead, use the WITH USER_MODE
   clause." (apexdev L11742-L11743, restated L44500-L44502). This does not
   compile; it is a hard blocker, not a style note.

Severity and exit code
----------------------
    ERROR     -> exit 1
    WARN      -> exit 0, unless --strict promotes it to ERROR
    ADVISORY  -> never affects the exit code
A missing --manifest-dir is always exit 1. A directory with no Apex files is a
WARN (exit 1 only under --strict).

Usage:
    python3 check_apex_soql_relationship_queries.py --manifest-dir force-app/main/default/classes
    python3 check_apex_soql_relationship_queries.py --manifest-dir force-app --strict
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

APEX_SUFFIXES = (".cls", ".trigger")

MAX_TRAVERSAL_DOTS = 5
MAX_SUBQUERIES = 20
SECURITY_ENFORCED_FLOOR = 67.0

SELECT_RE = re.compile(r"\bSELECT\b", re.IGNORECASE)
FROM_RE = re.compile(r"\bFROM\s+([A-Za-z_][\w.]*)", re.IGNORECASE)
NESTED_SUBQUERY_RE = re.compile(r"\(\s*SELECT\b[^()]*\(\s*SELECT\b", re.IGNORECASE | re.DOTALL)
SECURITY_ENFORCED_RE = re.compile(r"\bWITH\s+SECURITY_ENFORCED\b", re.IGNORECASE)
API_VERSION_RE = re.compile(r"<apiVersion>\s*([0-9]+(?:\.[0-9]+)?)\s*</apiVersion>")
FOR_RE = re.compile(r"\bfor\s*\(", re.IGNORECASE)

# `Something__c.Field` — dotting into a parent pointer instead of the __r name.
# Excludes `Schema.Something__c.Field` style describe access and the common
# `Trigger.new` shapes by requiring the token before `__c` to not follow `Schema.`.
CUSTOM_PTR_DOT_RE = re.compile(r"(?<!Schema\.)\b([A-Za-z_]\w*__c)\.([A-Za-z_]\w*)")

# A dotted traversal chain: Identifier(.Identifier){n}
DOT_CHAIN_RE = re.compile(r"\b([A-Za-z_]\w*(?:\.[A-Za-z_]\w*){%d,})" % MAX_TRAVERSAL_DOTS)

# Iterating a relationship collection.
REL_ITER_RE = re.compile(
    r"\bfor\s*\(\s*(?:final\s+)?[A-Za-z_][\w<>,\s\[\]]*\s+\w+\s*:\s*"
    r"([A-Za-z_]\w*)\s*\.\s*([A-Za-z_]\w*__r|[A-Z][A-Za-z]*s)\s*\)"
)
GETSOBJECTS_ITER_RE = re.compile(
    r"\bfor\s*\(\s*(?:final\s+)?[A-Za-z_][\w<>,\s\[\]]*\s+\w+\s*:\s*"
    r"([A-Za-z_]\w*)\s*\.\s*getSObjects\s*\("
)

# SOQL literal forms: inline [ SELECT ... ] and Database.query('SELECT ...').
INLINE_SOQL_RE = re.compile(r"\[\s*(SELECT\b.*?)\]", re.IGNORECASE | re.DOTALL)

# Words that legitimately end in a lowercase-plural but are not relationships.
NON_RELATIONSHIP_PLURALS = {
    "values", "keySet", "Values", "Keys", "Options", "Results",
}


def sanitize(src: str) -> str:
    """Blank string literals and comments in one left-to-right pass so that a
    quote inside a comment never opens a phantom string, and a '/*' inside a
    string never opens a phantom comment. Length is preserved so that character
    offsets still map back to line numbers."""
    out = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "'":
            j = i + 1
            while j < n and src[j] != "'":
                j += 2 if src[j] == "\\" else 1
            j = min(j, n - 1) if j < n else n
            out.append(" " * (min(j, n) - i + 1))
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


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def soql_blocks(raw: str, clean: str) -> list[tuple[int, str]]:
    """Return (line, soql_text) for every SOQL literal we can find.

    Inline `[SELECT ...]` is read from the *sanitized* text so that a bracket in
    a comment does not open a block. Dynamic strings are read from the *raw*
    text, because sanitizing blanks exactly the content we need; they are found
    by locating quoted runs that begin with SELECT.
    """
    found: list[tuple[int, str]] = []
    for m in INLINE_SOQL_RE.finditer(clean):
        found.append((line_of(clean, m.start()), m.group(1)))
    for m in re.finditer(r"'([^']*)'", raw, re.DOTALL):
        body = m.group(1)
        if SELECT_RE.match(body.strip()) or " FROM " in body.upper():
            if "SELECT" in body.upper():
                found.append((line_of(raw, m.start()), body))
    return found


def brace_depth_ranges(clean: str) -> list[tuple[int, int]]:
    """Return (start_offset, end_offset) for every `for (...) { ... }` body."""
    ranges: list[tuple[int, int]] = []
    for m in FOR_RE.finditer(clean):
        # walk to the matching ')' of the for header
        i, depth = m.end() - 1, 0
        while i < len(clean):
            if clean[i] == "(":
                depth += 1
            elif clean[i] == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        j = i + 1
        while j < len(clean) and clean[j] in " \t\r\n":
            j += 1
        if j >= len(clean):
            continue
        if clean[j] != "{":
            # single-statement body: to the next ';'
            k = clean.find(";", j)
            if k != -1:
                ranges.append((j, k))
            continue
        depth = 0
        k = j
        while k < len(clean):
            if clean[k] == "{":
                depth += 1
            elif clean[k] == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        ranges.append((j, k))
    return ranges


def count_subqueries(soql: str) -> int:
    """Count `(SELECT` occurrences — each is one parent-to-child subquery or a
    semi-join. Semi-joins appear after IN/NOT IN, so those are excluded."""
    count = 0
    for m in re.finditer(r"\(\s*SELECT\b", soql, re.IGNORECASE):
        before = soql[max(0, m.start() - 12): m.start()].upper()
        if re.search(r"\b(IN|NOT\s+IN)\s*$", before):
            continue
        count += 1
    return count


def read_api_version(cls_path: Path) -> float | None:
    meta = cls_path.with_name(cls_path.name + "-meta.xml")
    if not meta.exists():
        return None
    try:
        m = API_VERSION_RE.search(meta.read_text(encoding="utf-8", errors="ignore"))
    except OSError:
        return None
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def audit_file(path: Path, raw: str, clean: str) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    rel = str(path)

    api_version = read_api_version(path)

    # ---- rule 7: WITH SECURITY_ENFORCED at API 67.0+ ----
    for m in SECURITY_ENFORCED_RE.finditer(clean):
        ln = line_of(clean, m.start())
        if api_version is not None and api_version >= SECURITY_ENFORCED_FLOOR:
            findings.append((
                "ERROR",
                f"{rel}:{ln}: WITH SECURITY_ENFORCED in a class at apiVersion {api_version:g}. "
                f"It cannot be used at {SECURITY_ENFORCED_FLOOR:g} or later (apexdev L11742-L11743); "
                "use WITH USER_MODE.",
            ))
        elif api_version is None:
            findings.append((
                "ADVISORY",
                f"{rel}:{ln}: WITH SECURITY_ENFORCED found but no -meta.xml apiVersion could be read. "
                f"Confirm the class is below {SECURITY_ENFORCED_FLOOR:g}.",
            ))
        else:
            findings.append((
                "WARN",
                f"{rel}:{ln}: WITH SECURITY_ENFORCED at apiVersion {api_version:g}. Still legal, but it "
                "does not process the WHERE clause or polymorphic fields; migrate to WITH USER_MODE "
                f"before upgrading past {SECURITY_ENFORCED_FLOOR:g}.",
            ))

    # ---- rules 1-4: per SOQL literal ----
    for ln, soql in soql_blocks(raw, clean):
        upper = soql.upper()

        # rule 1a: dotting into a __c parent pointer inside SOQL
        for m in CUSTOM_PTR_DOT_RE.finditer(soql):
            findings.append((
                "ERROR",
                f"{rel}:{ln}: SOQL traverses `{m.group(1)}.{m.group(2)}`. `__c` is the parent-object "
                f"pointer; the relationship name is `{m.group(1)[:-3]}__r` "
                "(object_reference L3030-L3032). Use the __r form to traverse.",
            ))

        # rule 1b: a subquery FROM naming an object API name
        for m in re.finditer(r"\(\s*SELECT\b(.*?)(?:\)|$)", soql, re.IGNORECASE | re.DOTALL):
            fm = FROM_RE.search(m.group(1))
            if fm and fm.group(1).endswith("__c"):
                findings.append((
                    "ERROR",
                    f"{rel}:{ln}: subquery FROM `{fm.group(1)}` uses an object API name. A subquery "
                    "FROM takes the child relationship name (`__r` for custom, the registered "
                    "plural for standard) — resolve it with "
                    "ChildRelationship.getRelationshipName() (apexrefguide L189843-L189876).",
                ))

        # rule 2: traversal depth
        for m in DOT_CHAIN_RE.finditer(soql):
            chain = m.group(1)
            parts = chain.split(".")
            # a bind variable or a namespace prefix is not a traversal
            if chain.startswith(("Trigger.", "Schema.", "System.", "Database.", "Limits.")):
                continue
            if len(parts) - 1 > MAX_TRAVERSAL_DOTS:
                findings.append((
                    "ERROR",
                    f"{rel}:{ln}: child-to-parent chain `{chain}` traverses {len(parts) - 1} levels; "
                    f"the documented maximum is {MAX_TRAVERSAL_DOTS}. Split the query or denormalize.",
                ))

        # rule 3: subquery count
        n_sub = count_subqueries(soql)
        if n_sub > MAX_SUBQUERIES:
            findings.append((
                "ERROR",
                f"{rel}:{ln}: {n_sub} parent-to-child subqueries in one SELECT; the documented maximum "
                f"is {MAX_SUBQUERIES}. Each also charges the aggregate-query pool "
                "(apexdev L19613-L19616).",
            ))

        # rule 4: nested subquery
        if NESTED_SUBQUERY_RE.search(soql):
            findings.append((
                "ERROR",
                f"{rel}:{ln}: a subquery contains another subquery. Parent-to-child nesting is one "
                "level only; query the grandchildren separately and join in Apex.",
            ))

        # note the filtered-subquery fact for rule 5
        if "(SELECT" in upper.replace(" ", "") and re.search(
            r"\(\s*SELECT\b[^)]*\bWHERE\b", soql, re.IGNORECASE | re.DOTALL
        ):
            findings.append(("__filtered__", rel))

    has_filtered_subquery = any(s == "__filtered__" for s, _ in findings)
    findings = [f for f in findings if f[0] != "__filtered__"]

    # ---- rule 5: unguarded relationship iteration ----
    if has_filtered_subquery:
        for m in list(REL_ITER_RE.finditer(clean)) + list(GETSOBJECTS_ITER_RE.finditer(clean)):
            ln = line_of(clean, m.start())
            receiver = m.group(1)
            member = m.group(2) if m.re is REL_ITER_RE else "getSObjects(...)"
            if member in NON_RELATIONSHIP_PLURALS:
                continue
            # Blank any SOQL literal in the lookback window first: a `WHERE
            # Email != null` inside the query is not a guard on the collection.
            window = INLINE_SOQL_RE.sub(
                lambda mm: " " * (mm.end() - mm.start()),
                clean[max(0, m.start() - 400): m.start()],
            )
            guarded = re.search(
                r"(?:!=\s*null|==\s*null|isEmpty\s*\(\s*\)|\bnull\s*!=)", window
            )
            if not guarded:
                findings.append((
                    "ADVISORY",
                    f"{rel}:{ln}: iterating `{receiver}.{member}` with no null/isEmpty guard in the "
                    "preceding lines, and this file's subquery carries a WHERE — the filter can "
                    "leave a parent with no children. The Apex guide guards the same shape "
                    "(apexdev L11719-L11721).",
                ))

    # ---- rule 6: SOQL inside a for loop ----
    for start, end in brace_depth_ranges(clean):
        body = clean[start:end]
        for m in INLINE_SOQL_RE.finditer(body):
            findings.append((
                "WARN",
                f"{rel}:{line_of(clean, start + m.start())}: SOQL inside a for loop. A parent-to-child "
                "subquery outside the loop is the documented fix (apexdev L20228-L20255). "
                "Bulkification and selector checkers own the general case.",
            ))
        for m in re.finditer(r"\bDatabase\s*\.\s*(query|queryWithBinds|getQueryLocator)\s*\(", body):
            findings.append((
                "WARN",
                f"{rel}:{line_of(clean, start + m.start())}: Database.{m.group(1)} inside a for loop. "
                "It counts against the SOQL statement limit (apexdev L19617-L19620).",
            ))

    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex source for SOQL relationship-query defects: __c used where a "
                    "traversal was intended, over-deep dot chains, too many or nested subqueries, "
                    "unguarded child iteration, SOQL in loops, and WITH SECURITY_ENFORCED at "
                    "API 67.0+.",
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
    fatal = any(s == "ERROR" or (strict and s == "WARN") for s, _ in findings)
    return 1 if fatal else 0


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: manifest directory not found: {root}", file=sys.stderr)
        return 1

    paths = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix in APEX_SUFFIXES)
    if not paths:
        print(f"WARN: no .cls or .trigger files under {root}")
        print("Scanned 0 Apex files.")
        return 1 if args.strict else 0

    findings: list[tuple[str, str]] = []
    for path in paths:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        findings += audit_file(path, raw, sanitize(raw))

    summary = f"Scanned {len(paths)} Apex file(s); {len(findings)} relationship-query finding(s)."
    return emit(findings, summary, args.strict)


if __name__ == "__main__":
    sys.exit(main())
