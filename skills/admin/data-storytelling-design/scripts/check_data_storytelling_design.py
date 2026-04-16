#!/usr/bin/env python3
"""Checker script for Data Storytelling Design skill.

Validates required content about CRM Analytics storytelling patterns,
text widgets, Z-pattern layout, and narrative API guidance.
Uses stdlib only — no pip dependencies.
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

    if "text widget" not in content.lower() and "text_widget" not in content.lower():
        errors.append("SKILL.md should mention text widgets as the CRM Analytics narrative tool")
    if "Z-pattern" not in content and "z-pattern" not in content.lower():
        errors.append("SKILL.md should mention Z-pattern layout for CRM Analytics")
    if "Story" not in content:
        errors.append("SKILL.md should reference Tableau Story sheets for sequential narrative")

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
