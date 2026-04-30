#!/usr/bin/env python3
"""Static checker for metadata-diff pipeline configurations.

Validates a diff-pipeline config (YAML or shell script) for known smells:

- two `sf project retrieve` calls with different `-x` manifests (asymmetric scope)
- diff target containing `*.profile-meta.xml` without a corresponding ignore entry
- destructive-changes generation step lacking a manual approval gate

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RETRIEVE = re.compile(r"sf\s+project\s+retrieve\s+start[^\n]*?(?:-x|--manifest)\s+(\S+)")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Lint metadata-diff pipeline scripts.")
    p.add_argument("--manifest-dir", default=".", help="Repository root.")
    p.add_argument(
        "--ignore",
        default="diff-ignore.txt",
        help="Diff-ignore file path (default: diff-ignore.txt).",
    )
    return p.parse_args()


def candidate_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for ext in ("*.sh", "*.yml", "*.yaml"):
        out.extend(root.rglob(ext))
    return [p for p in out if "node_modules" not in p.parts and ".git" not in p.parts]


def check_file(path: Path, ignore_text: str) -> list[str]:
    issues: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return issues

    manifests = RETRIEVE.findall(text)
    if len(manifests) >= 2 and len(set(manifests)) > 1:
        issues.append(
            f"{path}: asymmetric retrieve manifests detected ({sorted(set(manifests))})"
        )

    if "*.profile-meta.xml" in text and "profile" not in ignore_text.lower():
        issues.append(
            f"{path}: profile XML in diff scope without an ignore entry — expect noise"
        )

    if "destructiveChanges" in text and "approval" not in text.lower() and "manual" not in text.lower():
        issues.append(
            f"{path}: destructiveChanges step found with no obvious approval/manual gate"
        )

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: manifest dir not found: {root}", file=sys.stderr)
        return 1

    ignore_path = root / args.ignore
    ignore_text = ignore_path.read_text(encoding="utf-8") if ignore_path.exists() else ""

    issues: list[str] = []
    for f in candidate_files(root):
        issues.extend(check_file(f, ignore_text))

    if not issues:
        print("[metadata-diff-between-sandboxes] no issues found")
        return 0
    for i in issues:
        print(f"WARN: {i}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
