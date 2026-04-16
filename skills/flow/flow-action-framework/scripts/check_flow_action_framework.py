#!/usr/bin/env python3
"""Checker script for Flow Action Framework skill.

Scans Apex classes for @InvocableMethod declarations that violate the common
Flow-facing contract (static method, list-typed input parameter). Uses stdlib
only — no pip dependencies.

Usage:
    python3 check_flow_action_framework.py [--help]
    python3 check_flow_action_framework.py --manifest-dir path/to/sfdx/project
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex invocable methods for Flow compatibility heuristics.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce project (searched recursively for *.cls).",
    )
    return parser.parse_args()


def _strip_trailing_line_comments(line: str) -> str:
    in_sq = in_dq = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "'" and not in_dq:
            in_sq = not in_sq
        elif ch == '"' and not in_sq:
            in_dq = not in_dq
        elif ch == "/" and i + 1 < len(line) and line[i + 1] == "/" and not in_sq and not in_dq:
            return line[:i].rstrip()
        i += 1
    return line


def _roughly_strip_comments(source: str) -> str:
    """Remove // comments per line; good enough for annotation scanning."""
    return "\n".join(_strip_trailing_line_comments(ln) for ln in source.splitlines())


def _iter_cls_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.cls") if p.is_file())


def check_flow_action_framework(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found under manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    cls_files = _iter_cls_files(manifest_dir)
    if not cls_files:
        return issues

    invocable_re = re.compile(r"@InvocableMethod\b")

    for cls_path in cls_files:
        try:
            raw = cls_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            issues.append(f"{cls_path}: could not read file ({exc})")
            continue

        text = _roughly_strip_comments(raw)
        if "@InvocableMethod" not in text:
            continue

        pos = 0
        while True:
            m = invocable_re.search(text, pos)
            if not m:
                break
            start = m.start()
            brace = text.find("{", start)
            if brace == -1:
                issues.append(
                    f"{cls_path}: @InvocableMethod has no following '{{' — incomplete class?"
                )
                break
            header = text[start:brace]
            try:
                rel = cls_path.relative_to(manifest_dir)
            except ValueError:
                rel = cls_path

            if re.search(r"\bstatic\b", header) is None:
                issues.append(
                    f"{rel}: @InvocableMethod must annotate a static method for Flow invocable use"
                )

            open_paren = header.rfind("(")
            close_paren = header.rfind(")")
            if open_paren == -1 or close_paren <= open_paren:
                issues.append(f"{rel}: could not parse parameter list after @InvocableMethod")
                pos = brace + 1
                continue

            params = header[open_paren + 1 : close_paren]
            if "List<" not in params:
                issues.append(
                    f"{rel}: @InvocableMethod parameter list should use List<...> input for Flow "
                    f"(got: {params.strip()[:80]!r})"
                )

            static_match = re.search(r"\bstatic\b", header)
            if static_match:
                ret_segment = header[static_match.end() : open_paren]
                has_void = re.search(r"\bvoid\b", ret_segment) is not None
                has_list_return = "List<" in ret_segment
                if not has_void and not has_list_return:
                    snippet = re.sub(r"\s+", " ", ret_segment).strip()[:120]
                    issues.append(
                        f"{rel}: @InvocableMethod return should be void or List<...> for Flow outputs "
                        f"(parsed return segment: {snippet!r})"
                    )

            pos = brace + 1

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()
    issues = check_flow_action_framework(manifest_dir)

    cls_count = len(_iter_cls_files(manifest_dir)) if manifest_dir.exists() else 0
    if cls_count == 0:
        print(f"No *.cls files found under {manifest_dir}")
    elif not issues:
        print(f"Scanned {cls_count} Apex class file(s); no invocable contract issues detected.")

    if not issues:
        if cls_count:
            print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
