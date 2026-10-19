#!/usr/bin/env python3
"""Checker for the sandbox-refresh-and-templates skill.

Scans a project for sandbox definition files and SandboxPostCopy Apex.

Sandbox definition files (*sandbox-def.json, or any JSON with sandboxName):
  ERROR  licenseType Partial without templateId (required for Partial sandboxes)
  ERROR  templateId with licenseType Developer or Developer_Pro (not available)
  ERROR  more than one of licenseType / sourceSandboxName / sourceId
  ERROR  both apexClassId and apexClassName
  ERROR  sandboxName missing, not alphanumeric, or longer than 10 characters
  ERROR  licenseType not one of Developer, Developer_Pro, Partial, Full
  WARN   no apexClassName / apexClassId (no post-copy automation)
  WARN   features ['SandboxStorage'] on Partial or Full (Developer types only)
SandboxPostCopy Apex (comments and strings ignored):
  ERROR  a class implementing SandboxPostCopy with no runApexClass(...) method
  ERROR  constructors declared but none is a no-arg constructor
  WARN   System.abortJob in the class (scheduled jobs aren't copied on refresh)
  WARN   no test calls Test.testSandboxPostCopyScript(... , true) for the class
Any Apex (comments ignored, string literals scanned):
  WARN   a literal org ID (00D...) in code

Exit 1 on ERROR (or WARN with --strict) and when --manifest-dir is missing. Stdlib only.

Usage:
    python3 check_sandbox_refresh.py --manifest-dir .
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ORG_ID_RE = re.compile(r"\b00D[A-Za-z0-9]{12}(?:[A-Za-z0-9]{3})?\b")
IMPL_RE = re.compile(r"\bclass\s+(\w+)[^{]*\bimplements\b[^{]*\b(?:System\.)?SandboxPostCopy\b", re.I)
RUN_RE = re.compile(r"\bvoid\s+runApexClass\s*\(", re.I)
ABORT_RE = re.compile(r"\bSystem\.abortJob\s*\(", re.I)
TEST_CALL_RE = re.compile(r"testSandboxPostCopyScript\s*\(\s*new\s+(\w+)\s*\(\s*\)(.*?)\)\s*;", re.I | re.S)
LICENSES = {"Developer", "Developer_Pro", "Partial", "Full"}


def strip_comments(src: str) -> str:
    """Blank comments only, skipping over string literals so a '//' inside a URL survives."""
    out, i, n = [], 0, len(src)
    while i < n:
        if src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(re.sub(r"[^\n]", " ", src[i:j]))
            i = j
        elif src[i] == "'":
            m = re.compile(r"'(?:\\.|[^'\\])*'").match(src, i)
            j = m.end() if m else n
            out.append(src[i:j])
            i = j
        else:
            out.append(src[i])
            i += 1
    return "".join(out)


def strip_code(src: str) -> str:
    return re.sub(r"'(?:\\.|[^'\\])*'", "''", strip_comments(src))


def check_definition(path: Path, data: dict, out: list[tuple[str, str]]) -> None:
    lic = data.get("licenseType")
    sources = [k for k in ("licenseType", "sourceSandboxName", "sourceId") if data.get(k)]
    if len(sources) > 1:
        out.append(("ERROR", f"{path}: specify only one of licenseType / sourceSandboxName / sourceId (found {sources})"))
    if lic is not None and lic not in LICENSES:
        out.append(("ERROR", f"{path}: licenseType '{lic}' is not one of {sorted(LICENSES)}"))
    if lic == "Partial" and not data.get("templateId"):
        out.append(("ERROR", f"{path}: Partial sandbox without templateId (required for Partial sandboxes)"))
    if lic in ("Developer", "Developer_Pro") and data.get("templateId"):
        out.append(("ERROR", f"{path}: templateId isn't available for {lic} sandboxes"))
    if data.get("apexClassId") and data.get("apexClassName"):
        out.append(("ERROR", f"{path}: specify apexClassId or apexClassName, not both"))
    name = data.get("sandboxName")
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9]{1,10}", name):
        out.append(("ERROR", f"{path}: sandboxName '{name}' must be alphanumeric and 10 characters or fewer"))
    if not data.get("apexClassName") and not data.get("apexClassId"):
        out.append(("WARN", f"{path}: no apexClassName/apexClassId; post-refresh setup is entirely manual"))
    if "SandboxStorage" in str(data.get("features", "")) and lic in ("Partial", "Full"):
        out.append(("WARN", f"{path}: features SandboxStorage can't be used with Partial or Full sandboxes"))


def check_apex(root: Path, out: list[tuple[str, str]]) -> int:
    files = sorted(root.rglob("*.cls"))
    raws = {p: p.read_text(encoding="utf-8", errors="ignore") for p in files}
    codes = {p: strip_code(t) for p, t in raws.items()}
    tested: dict[str, bool] = {}
    for code in codes.values():
        for m in TEST_CALL_RE.finditer(code):
            as_auto = re.search(r",\s*true\s*$", m.group(2).strip()) is not None
            tested[m.group(1).lower()] = tested.get(m.group(1).lower(), False) or as_auto
    for path, code in codes.items():
        # org IDs are written as string literals, so search with strings kept (comments still ignored)
        with_strings = strip_comments(raws[path])
        m = ORG_ID_RE.search(with_strings)
        if m:
            out.append(("WARN", f"{path}:{with_strings.count(chr(10), 0, m.start()) + 1}: literal org ID; read it at runtime with UserInfo.getOrganizationId()"))
        impl = IMPL_RE.search(code)
        if not impl:
            continue
        cls = impl.group(1)
        if not RUN_RE.search(code):
            out.append(("ERROR", f"{path}: {cls} implements SandboxPostCopy but has no runApexClass(SandboxContext) method"))
        ctors = re.findall(rf"\b{re.escape(cls)}\s*\(([^)]*)\)\s*\{{", code)
        if ctors and not any(not c.strip() for c in ctors):
            out.append(("ERROR", f"{path}: {cls} declares constructors but no no-arg constructor; the copy process uses the no-arg one"))
        if ABORT_RE.search(code):
            out.append(("WARN", f"{path}: {cls} calls System.abortJob; scheduled jobs aren't copied on refresh, reschedule what you need instead"))
        if not tested.get(cls.lower()):
            out.append(("WARN", f"{path}: no test calls Test.testSandboxPostCopyScript(new {cls}(), ..., true)"))
    return len(files)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check sandbox definition files and SandboxPostCopy Apex.")
    parser.add_argument("--manifest-dir", required=True, type=Path, help="Project directory to scan.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN as well as ERROR.")
    args = parser.parse_args(argv)

    root = args.manifest_dir
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)

    out: list[tuple[str, str]] = []
    defs = 0
    for path in sorted(root.rglob("*.json")):
        if "node_modules" in path.parts:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            if path.name.endswith("sandbox-def.json"):
                out.append(("ERROR", f"{path}: not valid JSON"))
            continue
        if isinstance(data, dict) and ("sandboxName" in data or path.name.endswith("sandbox-def.json")):
            defs += 1
            check_definition(path, data, out)
    apex = check_apex(root, out)
    if not defs and not apex:
        print(f"WARN: no sandbox definition files or Apex classes under {root}; nothing to check")
        return 0
    for level, msg in out:
        print(f"{level}: {msg}")
    errors = sum(1 for lvl, _ in out if lvl == "ERROR")
    warns = len(out) - errors
    print(f"Checked {defs} definition file(s) and {apex} Apex file(s): {errors} error(s), {warns} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
