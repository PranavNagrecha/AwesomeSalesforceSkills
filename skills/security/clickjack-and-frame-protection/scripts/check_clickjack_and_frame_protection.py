#!/usr/bin/env python3
"""Static checker stub for clickjack-and-frame-protection.

This checker is intentionally minimal — the heavy lifting lives in the shared
validator. Exit 0 if the skill package is shaped correctly for security, 1
otherwise. Intended as a pre-commit or CI smoke check.
"""
from __future__ import annotations
import sys
from pathlib import Path

REQUIRED = [
    "SKILL.md",
    "references/examples.md",
    "references/gotchas.md",
    "references/well-architected.md",
    "references/llm-anti-patterns.md",
    "templates",
    "scripts",
]


def main() -> int:
    base = Path(__file__).resolve().parents[1]
    missing = [r for r in REQUIRED if not (base / r).exists()]
    if missing:
        print(f"ERROR [clickjack-and-frame-protection] missing files: {missing}", file=sys.stderr)
        sys.exit(1)
    print(f"[clickjack-and-frame-protection] shape OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
