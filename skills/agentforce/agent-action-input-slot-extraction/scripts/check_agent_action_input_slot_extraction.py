#!/usr/bin/env python3
"""Static checker for Apex InvocableVariable descriptions used by Agentforce.

Scans `force-app/.../classes/*.cls` for:

- @InvocableVariable lines whose `description` is empty, missing, or one-word
- @InvocableVariable typed `Id` (any case) — flag as risky for LLM-driven calls

Stdlib only. The checker uses a permissive regex; treat output as candidates.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

INVOCABLE = re.compile(
    r"@InvocableVariable\s*\(([^)]*)\)\s*\n\s*(?:public|global|private)\s+(\w+)\s+(\w+)",
    re.MULTILINE,
)
DESC = re.compile(r"description\s*=\s*['\"]([^'\"]*)['\"]")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Lint Apex invocable variable descriptions.")
    p.add_argument("--manifest-dir", default=".", help="Project root.")
    return p.parse_args()


def cls_files(root: Path) -> list[Path]:
    return list((root / "force-app").rglob("*.cls"))


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return issues

    for m in INVOCABLE.finditer(text):
        attrs = m.group(1)
        type_name = m.group(2)
        var_name = m.group(3)

        d = DESC.search(attrs)
        desc = d.group(1) if d else ""
        if not desc.strip():
            issues.append(f"{path}: invocable {var_name} has no description")
        elif len(desc.split()) <= 2:
            issues.append(
                f"{path}: invocable {var_name} description '{desc}' is too short — add format/example/reject clauses"
            )

        if type_name.lower() == "id":
            issues.append(
                f"{path}: invocable {var_name} typed Id — LLMs hallucinate IDs; take a String name and resolve in Apex"
            )

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not (root / "force-app").exists():
        print(f"ERROR: no force-app/ directory under {root}", file=sys.stderr)
        return 1

    issues: list[str] = []
    for f in cls_files(root):
        issues.extend(check_file(f))

    if not issues:
        print("[agent-action-input-slot-extraction] no issues found")
        return 0
    for i in issues:
        print(f"WARN: {i}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
