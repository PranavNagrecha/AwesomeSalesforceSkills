#!/usr/bin/env python3
"""Checker for the scratch-org-snapshots skill.

Scratch org definition files (JSON with a "snapshot" key):
  ERROR  snapshot name longer than 15 characters or not alphanumeric
  ERROR  "snapshot" together with edition, features, hasSampleData, release, or sourceOrg
CI / shell files (.yml, .yaml, .sh, .bash, Jenkinsfile):
  ERROR  `sf org create snapshot --name <x>` with an invalid name
  WARN   `org create snapshot` with no status check (`org get snapshot` or an OrgSnapshot
         query) in the same file before scratch orgs are created from it
  WARN   a scratch org created from a snapshot with no fallback `org create scratch`
         path in the same file

Exit 1 on ERROR (or WARN with --strict) and when --manifest-dir is missing. Stdlib only.

Usage:
    python3 check_scratch_org_snapshots.py --manifest-dir .
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[A-Za-z0-9]{1,15}$")
FORBIDDEN = ("edition", "features", "hasSampleData", "release", "sourceOrg")
CI_SUFFIXES = {".yml", ".yaml", ".sh", ".bash"}
CREATE_SNAP_RE = re.compile(r"org\s+create\s+snapshot\b(?P<rest>(?:[^\n]|\\\n)*)", re.I)
NAME_FLAG_RE = re.compile(r"(?:--name|-n)[ =]+[\"']?([^\s\"'\\]+)")
CREATE_SCRATCH_RE = re.compile(r"org\s+create\s+scratch\b(?P<rest>(?:[^\n]|\\\n)*)", re.I)


def check_defs(root: Path, out: list[tuple[str, str]]) -> tuple[int, set[str]]:
    n, snap_defs = 0, set()
    for path in sorted(root.rglob("*.json")):
        if "node_modules" in path.parts:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict) or "snapshot" not in data:
            continue
        n += 1
        snap_defs.add(path.name)
        name = data.get("snapshot")
        if not isinstance(name, str) or not NAME_RE.match(name):
            out.append(("ERROR", f"{path}: snapshot name '{name}' must be 1-15 alphanumeric characters"))
        bad = [k for k in FORBIDDEN if k in data]
        if bad:
            out.append(("ERROR", f"{path}: don't combine 'snapshot' with {bad} in a scratch org definition file"))
    return n, snap_defs


def check_ci(root: Path, snap_defs: set[str], out: list[tuple[str, str]]) -> int:
    n = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "node_modules" in path.parts:
            continue
        if path.suffix not in CI_SUFFIXES and path.name != "Jenkinsfile":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        creates = list(CREATE_SNAP_RE.finditer(text))
        scratches = list(CREATE_SCRATCH_RE.finditer(text))
        if not creates and not scratches:
            continue
        n += 1
        for m in creates:
            nm = NAME_FLAG_RE.search(m.group("rest"))
            if nm and "$" not in nm.group(1) and not NAME_RE.match(nm.group(1)):
                line = text.count("\n", 0, m.start()) + 1
                out.append(("ERROR", f"{path}:{line}: snapshot name '{nm.group(1)}' must be 1-15 alphanumeric characters"))
        if creates and not re.search(r"org\s+get\s+snapshot|FROM\s+OrgSnapshot", text, re.I):
            out.append(("WARN", f"{path}: creates a snapshot but never checks it reached Active (org get snapshot / OrgSnapshot query)"))
        from_snap = [s for s in scratches if "--snapshot" in s.group("rest") or any(d in s.group("rest") for d in snap_defs)]
        if from_snap and len(scratches) == len(from_snap):
            out.append(("WARN", f"{path}: every scratch org here comes from a snapshot; add a definition-file fallback"))
    return n


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check scratch org snapshot definitions and CI usage.")
    parser.add_argument("--manifest-dir", required=True, type=Path, help="Project directory to scan.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN as well as ERROR.")
    args = parser.parse_args(argv)
    root = args.manifest_dir
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    out: list[tuple[str, str]] = []
    defs, snap_defs = check_defs(root, out)
    ci = check_ci(root, snap_defs, out)
    if not defs and not ci:
        print(f"WARN: no snapshot definition files or CI files using snapshots under {root}; nothing to check")
        return 0
    for level, msg in out:
        print(f"{level}: {msg}")
    errors = sum(1 for lvl, _ in out if lvl == "ERROR")
    warns = len(out) - errors
    print(f"Checked {defs} definition file(s) and {ci} CI file(s): {errors} error(s), {warns} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
