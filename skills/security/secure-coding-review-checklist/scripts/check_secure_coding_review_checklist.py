#!/usr/bin/env python3
"""Checker for the Secure Coding Review Checklist skill (stdlib only).

Scans Apex classes, triggers and Visualforce pages/components under
--manifest-dir. Every Apex finding is scored against the file's own
<apiVersion> (sibling *-meta.xml), never the org's release.

  ERROR  WITH SECURITY_ENFORCED in a file at API 67.0+ — "you can't use the
         WITH SECURITY_ENFORCED clause" there (apexdev 264 L11926), so the file
         does not save
  WARN   a SOQL query with no WITH USER_MODE / WITH SYSTEM_MODE in a file below
         67.0, where system mode is the default (apexdev 264 L45133-45135)
  WARN   WITH SECURITY_ENFORCED below 67.0 — prefer WITH USER_MODE
  WARN   Database.query / countQuery built with string concatenation
         (bind values instead — apexdev 264 L11623-11656)
  WARN   a class with no sharing keyword below 67.0 — its mode depends on
         inheritance, entry-point type and caller (apexdev 264 L11931-11937)
  WARN   HTMLENCODE inside a <script> block — JSENCODE is the JavaScript
         encoder (apexdev 264 L13504-13507)
  INFO   a bare SOQL query or bare class at 67.0+ — user mode and with sharing
         are the defaults (L11928-11930); state the intent explicitly

A trigger has a fixed implicit `without sharing` context, but database
operations in its body "run in user mode unless system mode is explicitly
specified", and user mode "overrides the trigger's without sharing context"
(apexdev 264 L4905-4909) — so .trigger files are scored like classes for
access mode and skipped for the sharing-keyword rule.

Exit 1 on any ERROR, or on WARN with --strict; otherwise 0. A missing
--manifest-dir is an ERROR; a tree with no Apex or Visualforce files is one
WARN, exit 0.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SOQL = re.compile(r"\[\s*SELECT\s+.+?\s+FROM\s+\w+.*?\]", re.IGNORECASE | re.DOTALL)
MODE = re.compile(r"WITH\s+(USER_MODE|SYSTEM_MODE)", re.IGNORECASE)
ENFORCED = re.compile(r"WITH\s+SECURITY_ENFORCED", re.IGNORECASE)
DYNAMIC = re.compile(r"Database\.(query|countQuery)\s*\(", re.IGNORECASE)
CLASS = re.compile(r"^\s*(?:public|global|private)\s+(?:(?:virtual|abstract)\s+)?class\s+(\w+)", re.MULTILINE)
SHARING = re.compile(r"(with\s+sharing|without\s+sharing|inherited\s+sharing)", re.IGNORECASE)
# Tempered: never crosses a </script>, so HTMLENCODE in the HTML body between two script
# blocks (the documented use, apexdev 264 L13504-13505) is not flagged; \b skips JSINHTMLENCODE.
HTML_IN_SCRIPT = re.compile(r"<script[^>]*>(?:(?!</script>)[\s\S])*?\bHTMLENCODE\s*\(", re.IGNORECASE)


def api_version(path: Path) -> float | None:
    try:
        meta = Path(str(path) + "-meta.xml").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.search(r"<apiVersion>\s*(\d+(?:\.\d+)?)\s*</apiVersion>", meta)
    return float(m.group(1)) if m else None


def line_of(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def check_apex(path: Path, out: list) -> None:
    body = path.read_text(encoding="utf-8", errors="replace")
    api = api_version(path)
    seen = f"apiVersion {api:.1f}" if api is not None else "apiVersion unknown (scored as below 67.0)"
    modern = api is not None and api >= 67.0
    for m in SOQL.finditer(body):
        q, n = m.group(0), line_of(body, m.start())
        if ENFORCED.search(q):
            if modern:
                out.append(("ERROR", f"{path}:{n}: WITH SECURITY_ENFORCED can't be used at {seen} (apexdev 264 L11926); use WITH USER_MODE"))
            else:
                out.append(("WARN", f"{path}:{n}: WITH SECURITY_ENFORCED at {seen}; prefer WITH USER_MODE, which enforces object permissions, FLS and sharing (apexdev 264 L11612-11613)"))
        elif not MODE.search(q):
            if modern:
                out.append(("INFO", f"{path}:{n}: bare SOQL at {seen} runs in user mode by default; add WITH USER_MODE to state intent"))
            else:
                out.append(("WARN", f"{path}:{n}: SOQL without WITH USER_MODE/SYSTEM_MODE at {seen} runs in system mode, no CRUD/FLS enforcement"))
    for n, line in enumerate(body.splitlines(), 1):
        if DYNAMIC.search(line) and "+" in line:
            out.append(("WARN", f"{path}:{n}: dynamic query built with concatenation; bind values with :var or Database.queryWithBinds"))
    if path.suffix == ".cls":
        for m in CLASS.finditer(body):
            start = body.rfind("\n", 0, m.start()) + 1
            if SHARING.search(body[start:m.end()]):
                continue
            n = line_of(body, m.start())
            if modern:
                out.append(("INFO", f"{path}:{n}: class '{m.group(1)}' has no sharing keyword; runs with sharing at {seen} (apexdev 264 L11930)"))
            else:
                out.append(("WARN", f"{path}:{n}: class '{m.group(1)}' has no sharing keyword at {seen}; mode depends on inheritance, entry point and caller (apexdev 264 L11931-11937) — declare it"))


def check_vf(path: Path, out: list) -> None:
    body = path.read_text(encoding="utf-8", errors="replace")
    for m in HTML_IN_SCRIPT.finditer(body):
        out.append(("WARN", f"{path}:{line_of(body, m.start())}: HTMLENCODE inside <script>; use JSENCODE (apexdev 264 L13504-13507)"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Check Apex and Visualforce code for security review findings, scored by apiVersion.")
    ap.add_argument("--manifest-dir", default=".", help="Root of the Salesforce metadata (default: current directory).")
    ap.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings as well as ERROR.")
    args = ap.parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    apex = sorted(set(root.rglob("*.cls")) | set(root.rglob("*.trigger")))
    vf = sorted(set(root.rglob("*.page")) | set(root.rglob("*.component")))
    if not apex and not vf:
        print(f"WARN: no Apex or Visualforce files under {root}; nothing to check")
        return 0
    out: list = []
    for path in apex:
        check_apex(path, out)
    for path in vf:
        check_vf(path, out)
    for sev, msg in out:
        print(f"{sev}: {msg}")
    errors = sum(1 for s, _ in out if s == "ERROR")
    warns = sum(1 for s, _ in out if s == "WARN")
    print(f"Summary: {errors} error(s), {warns} warning(s)")
    if errors or (args.strict and warns):
        sys.exit(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
