#!/usr/bin/env python3
"""Checker script for AI Training Data Preparation skill.

Validates that SKILL.md and references for this skill contain
required content markers for Einstein ML data preparation guidance.
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

    # Check for fill-rate threshold mention
    if "70%" not in content and "fill rate" not in content.lower():
        errors.append("SKILL.md should mention fill rate threshold (~70%) for Einstein Discovery")

    # Check for minimum row count mention
    if "400" not in content:
        errors.append("SKILL.md should mention minimum 400 rows requirement for Einstein Discovery")

    # Check for leakage mention
    if "leakage" not in content.lower():
        errors.append("SKILL.md should address leakage/proxy field risk")

    # Check for EPB vs Einstein Discovery distinction
    if "Prediction Builder" not in content:
        errors.append("SKILL.md should distinguish Einstein Prediction Builder from Einstein Discovery")

    # Check references exist
    for ref in ["examples.md", "gotchas.md", "well-architected.md", "llm-anti-patterns.md"]:
        ref_path = skill_path / "references" / ref
        if not ref_path.exists():
            errors.append(f"references/{ref} missing")
            continue
        ref_content = ref_path.read_text()
        if "TODO" in ref_content:
            errors.append(f"references/{ref} still contains TODO markers")

    # Check llm-anti-patterns has 5+ entries
    anti_patterns_path = skill_path / "references" / "llm-anti-patterns.md"
    if anti_patterns_path.exists():
        pattern_count = len(re.findall(r"## Anti-Pattern \d+", anti_patterns_path.read_text()))
        if pattern_count < 5:
            errors.append(f"references/llm-anti-patterns.md has {pattern_count} anti-patterns; need 5+")

    # Check well-architected has Official Sources
    wa_path = skill_path / "references" / "well-architected.md"
    if wa_path.exists():
        if "## Official Sources Used" not in wa_path.read_text():
            errors.append("references/well-architected.md missing '## Official Sources Used' section")

    return errors


def main():
    skill_path = Path(__file__).parent.parent
    errors = check_skill(skill_path)

    if errors:
        print(f"ERRORS in {skill_path.name}:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print(f"OK: {skill_path.name} passes all checks")
        sys.exit(0)


if __name__ == "__main__":
    main()
