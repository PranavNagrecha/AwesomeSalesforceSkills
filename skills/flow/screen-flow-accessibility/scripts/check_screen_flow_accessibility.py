#!/usr/bin/env python3
"""Heuristic checker for Screen Flow accessibility audit documents.

Scans markdown audit docs under ``--manifest-dir`` (alias ``--docs-dir``) for the
minimum sections (per-screen checklist, keyboard test, screen reader test,
contrast, WCAG mapping) and a few omissions from `references/llm-anti-patterns.md`.
All findings are WARN: they exit 0 unless ``--strict``. A missing directory is an
ERROR (exit 1); a directory with no markdown prints one WARN and exits 0.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "per-screen checklist",
    "keyboard test",
    "screen reader test",
    "contrast",
    "wcag",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect Screen Flow accessibility audit documents.",
    )
    parser.add_argument(
        "--manifest-dir",
        "--docs-dir",
        dest="manifest_dir",
        default=".",
        help="Directory containing audit markdown files.",
    )
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings too.")
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    if "nvda" not in text and "voiceover" not in text and "jaws" not in text:
        issues.append(f"{path}: no specific screen reader named (audit untested)")

    if "placeholder" in text and "label" not in text:
        issues.append(f"{path}: placeholder used without label — WCAG 1.3.1 risk")

    if "color" in text and "4.5" not in text:
        issues.append(f"{path}: contrast ratio target (4.5:1) not documented")

    if "wcag 2.1" in text and "2.2" not in text:
        issues.append(f"{path}: audits against WCAG 2.1 only; the skill targets WCAG 2.2 AA")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: directory not found: {root}")
        sys.exit(1)

    targets = sorted(root.rglob("*.md"))
    if not targets:
        print(f"WARN: no audit documents (*.md) found under {root}")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("Audit documents look complete.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
