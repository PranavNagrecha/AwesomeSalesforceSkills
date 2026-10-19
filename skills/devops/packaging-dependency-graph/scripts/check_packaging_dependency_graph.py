#!/usr/bin/env python3
"""Checker for the packaging-dependency-graph skill.

Reads every sfdx-project.json under --manifest-dir and checks the package graph:

  ERROR  sfdx-project.json is not valid JSON
  ERROR  a dependency `package` value that is neither a packageAliases key, a
         package directory name, nor a 0Ho/04t ID
  ERROR  a dependency versionNumber using NEXT (NEXT is for your own version)
  ERROR  a package's own versionNumber using LATEST or RELEASED
  ERROR  a dependency cycle between packages in this project
  WARN   a dependency on LATEST (switch to RELEASED before creating a version you will promote)
  WARN   without calculateTransitiveDependencies: an indirect dependency missing from
         the list, or the list not in install order
  WARN   ancestorVersion / ancestorId set to NONE (existing customers can't upgrade)

Prints the base-first install/promotion order for local packages when there is no cycle.
Exit 1 on ERROR (or WARN with --strict) and when --manifest-dir is missing. Stdlib only.

Usage:
    python3 check_packaging_dependency_graph.py --manifest-dir .
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ID_RE = re.compile(r"^(0Ho|04t)[A-Za-z0-9]{12,15}$")


def _dep_name(dep: dict, aliases: dict, local: set[str]) -> str | None:
    """Return the local package a dependency points at, if any."""
    pkg = str(dep.get("package", ""))
    if pkg in local:
        return pkg
    target = aliases.get(pkg)
    for name in local:
        if target is not None and aliases.get(name) == target:
            return name
        if pkg.startswith(name + "@"):
            return name
    return None


def _resolves(pkg: str, aliases: dict, local: set[str]) -> bool:
    return pkg in aliases or pkg in local or bool(ID_RE.match(pkg))


def check_project(path: Path, out: list[tuple[str, str]]) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        out.append(("ERROR", f"{path}: not valid JSON ({exc})"))
        return
    dirs = [d for d in data.get("packageDirectories", []) if isinstance(d, dict) and d.get("package")]
    aliases = data.get("packageAliases", {}) or {}
    local = {d["package"] for d in dirs}
    graph: dict[str, list[str]] = {}

    for d in dirs:
        name = d["package"]
        own = str(d.get("versionNumber", ""))
        if own.endswith(".LATEST") or own.endswith(".RELEASED"):
            out.append(("ERROR", f"{path}: {name} versionNumber {own} uses a dependency keyword; use NEXT or a literal build"))
        for key in ("ancestorVersion", "ancestorId"):
            if str(d.get(key, "")).upper() == "NONE":
                out.append(("WARN", f"{path}: {name} {key} is NONE; existing customers can't upgrade to this version"))
        edges: list[str] = []
        deps = d.get("dependencies", []) or []
        if not isinstance(deps, list):
            out.append(("ERROR", f"{path}: {name} dependencies must be an array of {{\"package\": ...}} objects"))
            deps = []
        for dep in deps:
            if not isinstance(dep, dict):
                out.append(("ERROR", f"{path}: {name} has a dependency entry that is not an object: {dep!r}"))
                continue
            pkg = str(dep.get("package", ""))
            ver = str(dep.get("versionNumber", ""))
            if not _resolves(pkg, aliases, local):
                out.append(("ERROR", f"{path}: {name} depends on '{pkg}', which is not a packageAliases key, package, or 0Ho/04t ID"))
            if ver.endswith(".NEXT"):
                out.append(("ERROR", f"{path}: {name} dependency {pkg} uses NEXT; NEXT is only for a package's own versionNumber"))
            elif ver.endswith(".LATEST"):
                out.append(("WARN", f"{path}: {name} depends on {pkg} with LATEST; switch to RELEASED before creating the version you will promote"))
            target = _dep_name(dep, aliases, local)
            if target and target != name:
                edges.append(target)
        graph[name] = edges

    # cycle detection + topological order (dependencies first)
    order: list[str] = []
    state: dict[str, int] = {}
    cycle: list[str] = []

    def visit(n: str, stack: list[str]) -> None:
        if cycle:
            return
        if state.get(n) == 1:
            cycle.extend(stack[stack.index(n):] + [n])
            return
        if state.get(n) == 2:
            return
        state[n] = 1
        for m in graph.get(n, []):
            visit(m, stack + [n])
        state[n] = 2
        order.append(n)

    for n in graph:
        visit(n, [])
    if cycle:
        out.append(("ERROR", f"{path}: dependency cycle: {' -> '.join(cycle)}; extract the shared code into a third package"))
        return

    # transitive completeness and install order of each list
    def closure(n: str) -> set[str]:
        seen: set[str] = set()
        todo = list(graph.get(n, []))
        while todo:
            m = todo.pop()
            if m not in seen:
                seen.add(m)
                todo.extend(graph.get(m, []))
        return seen

    for d in dirs:
        name = d["package"]
        if d.get("calculateTransitiveDependencies") is True:
            continue
        missing = closure(name) - set(graph[name])
        if missing:
            out.append(("WARN", f"{path}: {name} omits indirect dependencies {sorted(missing)}; list them or set calculateTransitiveDependencies"))
        listed = graph[name]
        pos = {p: i for i, p in enumerate(order)}
        if listed != sorted(listed, key=lambda p: pos.get(p, 0)):
            out.append(("WARN", f"{path}: {name} dependencies are not in install order; expected {sorted(listed, key=lambda p: pos.get(p, 0))}"))

    if order:
        print(f"INFO: {path}: install/promote order: {' -> '.join(order)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check unlocked package dependencies in sfdx-project.json.")
    parser.add_argument("--manifest-dir", required=True, type=Path, help="Project directory containing sfdx-project.json.")
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
        check_project(proj, out)
    for level, msg in out:
        print(f"{level}: {msg}")
    errors = sum(1 for lvl, _ in out if lvl == "ERROR")
    warns = len(out) - errors
    print(f"Checked {len(projects)} project file(s): {errors} error(s), {warns} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
