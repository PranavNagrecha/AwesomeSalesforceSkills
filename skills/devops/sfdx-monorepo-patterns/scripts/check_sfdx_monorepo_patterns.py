#!/usr/bin/env python3
"""Checker for the sfdx-monorepo-patterns skill.

Reads sfdx-project.json under --manifest-dir and the package directories it lists.

ERROR  sfdx-project.json not valid JSON
ERROR  more than one packageDirectories entry with "default": true, or none when
       there are several directories
ERROR  a package directory path that doesn't exist, or two paths that overlap
ERROR  the same custom object definition (*.object-meta.xml) in two package directories
WARN   field files for a custom object whose definition lives in another directory that
       this directory's package doesn't depend on (directly or transitively)
WARN   a per-package .forceignore that omits patterns from the root .forceignore
       (the CLI uses the nearest .forceignore and stops looking)
WARN   Apex classes named like seed/demo/sample-data tooling inside a package path

Exit 1 on ERROR (or WARN with --strict) and when --manifest-dir is missing. Stdlib only.

Usage:
    python3 check_sfdx_monorepo_patterns.py --manifest-dir .
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TOOLING_RE = re.compile(r"(seed|seeder|demodata|demo_data|sampledata|sample_data|dataload)", re.I)


def _patterns(path: Path) -> set[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return set()
    return {ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")}


def check(root: Path, project: Path, out: list[tuple[str, str]]) -> None:
    base = project.parent
    try:
        data = json.loads(project.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        out.append(("ERROR", f"{project}: not valid JSON ({exc})"))
        return
    dirs = [d for d in data.get("packageDirectories", []) if isinstance(d, dict) and d.get("path")]
    defaults = [d["path"] for d in dirs if d.get("default") is True]
    if len(defaults) > 1:
        out.append(("ERROR", f"{project}: {len(defaults)} package directories have default true ({defaults}); only one can"))
    elif len(dirs) > 1 and not defaults:
        out.append(("ERROR", f"{project}: several package directories but none has default true; nominate one"))

    paths = {d["path"].rstrip("/"): d for d in dirs}
    for p in paths:
        if not (base / p).is_dir():
            out.append(("ERROR", f"{project}: package directory '{p}' does not exist"))
    plist = sorted(paths)
    for i, a in enumerate(plist):
        for b in plist[i + 1:]:
            if b.startswith(a + "/"):
                out.append(("ERROR", f"{project}: package directories overlap: '{a}' contains '{b}'"))

    # dependency closure by package name
    deps = {d.get("package"): [x.get("package", "").split("@")[0] for x in d.get("dependencies", []) or [] if isinstance(x, dict)]
            for d in dirs if d.get("package")}

    def closure(pkg: str | None) -> set[str]:
        seen: set[str] = set()
        todo = list(deps.get(pkg, []))
        while todo:
            m = todo.pop()
            if m and m not in seen:
                seen.add(m)
                todo.extend(deps.get(m, []))
        return seen

    owners: dict[str, list[str]] = {}
    fields: dict[str, set[str]] = {}
    for p in paths:
        pdir = base / p
        if not pdir.is_dir():
            continue
        for f in pdir.rglob("*.object-meta.xml"):
            obj = f.name[: -len(".object-meta.xml")]
            if obj.endswith("__c") or obj.endswith("__mdt") or obj.endswith("__e"):
                owners.setdefault(obj, []).append(p)
        for f in pdir.rglob("*.field-meta.xml"):
            if f.parent.name == "fields":
                fields.setdefault(f.parent.parent.name, set()).add(p)
        for f in pdir.rglob("*.cls"):
            if TOOLING_RE.search(f.stem) and not f.stem.lower().endswith("test"):
                out.append(("WARN", f"{f}: looks like seed/demo tooling inside package directory '{p}'; keep it outside packageDirectories"))
    for obj, own in owners.items():
        if len(own) > 1:
            out.append(("ERROR", f"{project}: custom object {obj} is defined in {len(own)} directories: {own}"))
    for obj, holders in fields.items():
        own = owners.get(obj, [])
        if len(own) != 1:
            continue
        owner_pkg = paths[own[0]].get("package")
        for h in sorted(holders - {own[0]}):
            pkg = paths[h].get("package")
            if not owner_pkg or not pkg or owner_pkg not in closure(pkg):
                out.append(("WARN", f"{project}: '{h}' has fields on {obj}, whose definition is in '{own[0]}', but its package doesn't depend on {owner_pkg or 'that directory'}"))

    root_ignore = base / ".forceignore"
    root_pats = _patterns(root_ignore) if root_ignore.is_file() else set()
    for p in paths:
        local = base / p / ".forceignore"
        if local.is_file() and local != root_ignore:
            missing = sorted(root_pats - _patterns(local))
            out.append(("WARN", f"{local}: per-package .forceignore replaces the root file for '{p}'"
                        + (f"; root patterns not repeated: {missing}" if missing else "")))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a Salesforce DX monorepo layout.")
    parser.add_argument("--manifest-dir", required=True, type=Path, help="Repository root (contains sfdx-project.json).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN as well as ERROR.")
    args = parser.parse_args(argv)
    root = args.manifest_dir
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    projects = sorted(p for p in root.rglob("sfdx-project.json") if "node_modules" not in p.parts)
    if not projects:
        print(f"WARN: no sfdx-project.json under {root}; nothing to check")
        return 0
    out: list[tuple[str, str]] = []
    for proj in projects:
        check(root, proj, out)
    for level, msg in out:
        print(f"{level}: {msg}")
    errors = sum(1 for lvl, _ in out if lvl == "ERROR")
    warns = len(out) - errors
    print(f"Checked {len(projects)} project(s): {errors} error(s), {warns} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
