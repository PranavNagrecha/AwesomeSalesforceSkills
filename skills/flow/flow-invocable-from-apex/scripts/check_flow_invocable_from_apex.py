#!/usr/bin/env python3
"""Static checker for flow-invocable-from-apex.

Scans Apex classes (*.cls) under --manifest-dir that carry @InvocableMethod or
@InvocableVariable. Stdlib only; regex based, so it reads declarations, not a full
Apex grammar. Grounding is the Apex Developer Guide 264 ("apexdev") and the Apex
Reference Guide 262 ("apexref"); line numbers come from `grep -n`.

ERROR (exit 1 always)
  * @InvocableMethod takes more than one parameter or a non-List parameter, or returns
    neither void nor a List. The guide allows "at most one input parameter" (zero is
    valid) and lists only list types for it (apexdev L5486-5490, L5498-5504).
  * @InvocableVariable on a property, static, final, protected or private member
    (apexdev L5773-5778).
  * @InvocableVariable carries both defaultValue and required (apexdev L5748).
  * WITH SECURITY_ENFORCED in a class whose .cls-meta.xml apiVersion is 67.0 or
    later (apexdev L11926).
WARN (exit 0 unless --strict)
  * Method body makes an HTTP callout but the annotation lacks callout=true
    (apexdev L5461-5462).
  * SOQL or DML inside a for loop over the input list (gotcha 1; apexdev L19747,
    L19757 for the 100 SOQL / 150 DML limits).
  * Flow.Interview.createInterview called with a literal containing a space; the
    parameter is the flow API name (apexref L158101).
  * A class-level static Map in a class that holds an @InvocableMethod; a static
    persists for the whole transaction (apexdev L3746-3748).

An empty tree prints one WARN and exits 0 (1 with --strict). A missing path prints an
ERROR and exits 1.

Usage:
    python3 check_flow_invocable_from_apex.py --manifest-dir force-app/main/default [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

METHOD_RE = re.compile(
    r"@InvocableMethod\s*(\((?:[^()]|\([^()]*\))*\))?\s*"
    r"(?:(?:public|global|static|private)\s+)*"
    r"([\w<>,.\s]+?)\s+(\w+)\s*\(([^)]*)\)\s*\{",
    re.S | re.I,
)
VAR_RE = re.compile(
    r"@InvocableVariable\s*(\((?:[^()]|\([^()]*\))*\))?\s*"
    r"((?:\w+\s+)*?)([\w<>.,]+)\s+(\w+)\s*([;{=])",
    re.S | re.I,
)


def strip_noise(src: str) -> str:
    """Blank comments and string literals so braces and keywords inside them do not count."""
    src = re.sub(r"/\*.*?\*/", lambda m: " " * len(m.group(0)), src, flags=re.S)
    src = re.sub(r"//[^\n]*", "", src)
    return re.sub(r"'(?:\\.|[^'\\])*'", "''", src)


def split_top(params: str) -> list[str]:
    """Split a parameter list on commas that are not inside <...> generics."""
    out, depth, cur = [], 0, ""
    for ch in params:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return out


def block_after(src: str, open_idx: int) -> str:
    """Text between the brace at open_idx and its match."""
    depth = 0
    for i in range(open_idx, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return src[open_idx + 1 : i]
    return src[open_idx + 1 :]


def api_version(cls: Path) -> float | None:
    meta = cls.with_name(cls.name + "-meta.xml")
    if not meta.exists():
        return None
    m = re.search(r"<apiVersion>\s*([\d.]+)\s*</apiVersion>", meta.read_text(encoding="utf-8"))
    return float(m.group(1)) if m else None


def check_file(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warns: list[str] = []
    raw = path.read_text(encoding="utf-8")
    src = strip_noise(raw)
    has_method = False
    for m in METHOD_RE.finditer(src):
        has_method = True
        args, ret, name, params = m.group(1) or "", " ".join(m.group(2).split()), m.group(3), m.group(4).strip()
        ret = ret.split()[-1] if ret.split() else ret
        plist = [p for p in split_top(params) if p.strip()]
        if len(plist) > 1 or (plist and not params.lower().startswith("list<")):
            errors.append(f"{path}: {name} takes at most one input parameter and it must be a List (apexdev 264 L5486-5490), found ({params})")
        if ret.lower() != "void" and not ret.lower().startswith("list<"):
            errors.append(f"{path}: {name} must return void or a List (apexdev 264 L5498-5504), found {ret}")
        body = block_after(src, m.end() - 1)
        calls_out = re.search(r"new\s+Http\s*\(|\bHttpRequest\b|callout:|\.send\s*\(", body)
        if calls_out and not re.search(r"callout\s*=\s*true", args, re.I):
            warns.append(f"{path}: {name} makes a callout but the annotation lacks callout=true (apexdev 264 L5461-5462)")
        pname = re.findall(r"(\w+)\s*$", params)
        if pname:
            for lm in re.finditer(r"for\s*\(\s*[\w<>.]+\s+\w+\s*:\s*%s\s*\)\s*\{" % re.escape(pname[0]), body):
                loop = block_after(body, lm.end() - 1)
                if re.search(r"\[\s*SELECT\b|\b(insert|update|delete|upsert|undelete)\s+[\w(]|\bDatabase\.(insert|update|delete|upsert)\b", loop, re.I):
                    warns.append(f"{path}: {name} runs SOQL or DML inside a loop over {pname[0]} (apexdev 264 L19747, L19757)")
    for m in VAR_RE.finditer(src):
        args, mods, _typ, vname, term = m.group(1) or "", m.group(2).lower().split(), m.group(3), m.group(4), m.group(5)
        bad = [x for x in mods if x in ("private", "protected", "static", "final")]
        if bad or term == "{" or not any(x in ("public", "global") for x in mods):
            errors.append(f"{path}: @InvocableVariable {vname} must be a public or global member variable, not a property/static/final/private (apexdev 264 L5773-5778)")
        if re.search(r"defaultValue", args, re.I) and re.search(r"required", args, re.I):
            errors.append(f"{path}: @InvocableVariable {vname} combines defaultValue and required (apexdev 264 L5748)")
    if has_method:
        for sm in re.finditer(r"^\s*(?:(?:private|public|global)\s+)?static\s+(?:final\s+)?Map\s*<[^;(]*>\s*\w+\s*(?:=|;)", src, re.M):
            warns.append(f"{path}: class-level static Map in an invocable class persists for the transaction (apexdev 264 L3746-3748)")
            break
        ver = api_version(path)
        if ver is not None and ver >= 67.0 and re.search(r"WITH\s+SECURITY_ENFORCED", src, re.I):
            errors.append(f"{path}: WITH SECURITY_ENFORCED cannot be used at API 67.0 and later (apexdev 264 L11926)")
    if re.search(r"createInterview\s*\(\s*(?:'[^']*',\s*)?'[^']* [^']*'\s*,", raw):
        warns.append(f"{path}: createInterview called with a literal containing a space; pass the flow API name (apexref 262 L158101)")
    return errors, warns


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Apex invocable actions against the documented contract.")
    parser.add_argument("--manifest-dir", default=".", help="Root of the Apex source (default: current directory).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings too.")
    args = parser.parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    errors: list[str] = []
    warns: list[str] = []
    seen = 0
    for cls in sorted(root.rglob("*.cls")):
        text = cls.read_text(encoding="utf-8")
        if "@Invocable" not in text and "createInterview" not in text:
            continue
        seen += 1
        e, w = check_file(cls)
        errors += e
        warns += w
    if seen == 0:
        print(f"WARN: no Apex classes with invocable annotations found under {root}")
        return 1 if args.strict else 0
    for e in errors:
        print(f"ERROR: {e}")
    for w in warns:
        print(f"WARN: {w}")
    if not errors and not warns:
        print("No issues found.")
    if errors:
        sys.exit(1)
    return 1 if (warns and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
