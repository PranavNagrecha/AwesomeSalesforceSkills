#!/usr/bin/env python3
"""Checker script for Einstein Analytics Data Model (XMD) skill.

Validates required content about XMD layers, REST API mechanics,
and dataset versioning. Uses stdlib only — no pip dependencies.
"""

import sys
import re
from pathlib import Path


def check_skill(skill_path: Path) -> list[str]:
    errors = []
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        errors.append("SKILL.md missing")
        return errors

    content = skill_md.read_text()

    if "system XMD" not in content and "xmds/system" not in content:
        errors.append("SKILL.md should explain system XMD layer")
    if "main XMD" not in content and "xmds/main" not in content:
        errors.append("SKILL.md should explain main XMD layer")
    if "immutable" not in content.lower() and "HTTP 400" not in content:
        errors.append("SKILL.md should mention system XMD immutability")
    if "SOQL" not in content or "WaveXmd" not in content:
        errors.append("SKILL.md should warn that WaveXmd is not SOQL-queryable")

    for ref in ["examples.md", "gotchas.md", "well-architected.md", "llm-anti-patterns.md"]:
        ref_path = skill_path / "references" / ref
        if not ref_path.exists():
            errors.append(f"references/{ref} missing")
            continue
        if "TODO" in ref_path.read_text():
            errors.append(f"references/{ref} still contains TODO markers")

    anti_path = skill_path / "references" / "llm-anti-patterns.md"
    if anti_path.exists():
        count = len(re.findall(r"## Anti-Pattern \d+", anti_path.read_text()))
        if count < 5:
            errors.append(f"llm-anti-patterns.md has {count} anti-patterns; need 5+")

    wa_path = skill_path / "references" / "well-architected.md"
    if wa_path.exists() and "## Official Sources Used" not in wa_path.read_text():
        errors.append("well-architected.md missing '## Official Sources Used' section")

    return errors


def main():
    skill_path = Path(__file__).parent.parent
    errors = check_skill(skill_path)
    if errors:
        print(f"ERRORS in {skill_path.name}:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print(f"OK: {skill_path.name} passes all checks")
    sys.exit(0)


if __name__ == "__main__":
    main()
