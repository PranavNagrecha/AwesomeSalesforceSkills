#!/usr/bin/env python3
"""Validate SKILL.md and work template structure for code-review-checklist-salesforce.

Ensures required sections exist, description scope exclusion is present, enough
triggers for routing metadata, and the template checklist mirrors SKILL.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_code_review_checklist_salesforce.py
    python3 check_code_review_checklist_salesforce.py --skill-dir path/to/skills/devops/code-review-checklist-salesforce
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_SKILL_HEADINGS = (
    "## Before Starting",
    "## Core Concepts",
    "## Recommended Workflow",
    "## Review Checklist",
    "## Salesforce-Specific Gotchas",
    "## Output Artifacts",
)

REQUIRED_TEMPLATE_HEADINGS = (
    "## Scope",
    "## Context Gathered",
    "## Approach",
    "## Checklist",
    "## Notes",
)

SKILL_NAME = "code-review-checklist-salesforce"


def parse_args() -> argparse.Namespace:
    default_dir = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description="Validate Salesforce code review checklist skill package files.",
    )
    parser.add_argument(
        "--skill-dir",
        type=Path,
        default=default_dir,
        help="Path to skills/devops/code-review-checklist-salesforce (default: beside this script).",
    )
    return parser.parse_args()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_frontmatter(skill_md: str) -> dict[str, str] | None:
    if not skill_md.startswith("---"):
        return None
    end = skill_md.find("\n---\n", 4)
    if end == -1:
        return None
    block = skill_md[4:end]
    data: dict[str, str] = {}
    current_key: str | None = None
    current_list: list[str] = []
    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if re.match(r"^[\w-]+:\s*", line) and not line.strip().startswith("- "):
            if current_key == "triggers" and current_list:
                data["triggers"] = "\n".join(current_list)
                current_list = []
            m = re.match(r"^([\w-]+):\s*(.*)$", line)
            if not m:
                continue
            key, rest = m.group(1), m.group(2).strip()
            current_key = key
            if rest in ("[]", "") and key in ("triggers", "tags", "inputs", "outputs"):
                data[key] = ""
            elif rest and key not in ("triggers", "tags", "inputs", "outputs", "well-architected-pillars"):
                data[key] = rest.strip('"')
            elif rest and key in ("tags", "inputs", "outputs", "well-architected-pillars"):
                data[key] = rest
        elif line.strip().startswith("- ") and current_key == "triggers":
            item = line.strip()[2:].strip().strip('"')
            if item:
                current_list.append(item)
    if current_key == "triggers" and current_list:
        data["triggers"] = "\n".join(current_list)
    return data


def _extract_review_checklist_body(skill_md: str) -> str:
    start = skill_md.find("## Review Checklist")
    if start == -1:
        return ""
    rest = skill_md[start + len("## Review Checklist") :]
    next_h2 = re.search(r"\n## ", rest)
    if next_h2:
        return rest[: next_h2.start()]
    return rest


def _checkbox_lines(section: str) -> list[str]:
    lines = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- [ ]"):
            lines.append(stripped)
    return lines


def check_code_review_checklist_salesforce(skill_dir: Path) -> list[str]:
    """Return actionable issue strings; empty means OK."""
    issues: list[str] = []

    if not skill_dir.is_dir():
        issues.append(f"Skill directory not found: {skill_dir}")
        return issues

    skill_md_path = skill_dir / "SKILL.md"
    if not skill_md_path.is_file():
        issues.append(f"Missing SKILL.md at {skill_md_path}")
        return issues

    skill_md = _read_text(skill_md_path)

    for heading in REQUIRED_SKILL_HEADINGS:
        if heading not in skill_md:
            issues.append(f"SKILL.md missing required section heading: {heading}")

    fm = _parse_frontmatter(skill_md)
    if fm is None:
        issues.append("SKILL.md: could not parse YAML frontmatter (expected --- blocks).")
    else:
        if fm.get("name") != SKILL_NAME:
            issues.append(
                f"Frontmatter name must be '{SKILL_NAME}', got {fm.get('name')!r}."
            )
        if fm.get("category") != "devops":
            issues.append(f"Frontmatter category must be 'devops', got {fm.get('category')!r}.")
        desc = fm.get("description", "")
        if "not for" not in desc.lower():
            issues.append('Frontmatter description must include a scope exclusion ("NOT for ...").')
        triggers = [t for t in fm.get("triggers", "").splitlines() if t.strip()]
        if len(triggers) < 3:
            issues.append(
                f"Frontmatter must list at least 3 triggers (natural-language routes); found {len(triggers)}."
            )
        for t in triggers:
            if len(t) < 10:
                issues.append(f"Trigger phrase too short (<10 chars): {t!r}")

    body = skill_md.split("---", 2)[-1] if skill_md.startswith("---") else skill_md
    word_tokens = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", body)
    if len(word_tokens) < 300:
        issues.append(
            f"SKILL.md body should be at least 300 words for repo validation; approximate word count: {len(word_tokens)}."
        )

    checklist_section = _extract_review_checklist_body(skill_md)
    skill_boxes = _checkbox_lines(checklist_section)
    if len(skill_boxes) < 5:
        issues.append(
            f"## Review Checklist should have at least 5 checkbox items; found {len(skill_boxes)}."
        )

    template_path = skill_dir / "templates" / f"{SKILL_NAME}-template.md"
    if not template_path.is_file():
        issues.append(f"Missing work template: {template_path}")
    else:
        template_text = _read_text(template_path)
        for heading in REQUIRED_TEMPLATE_HEADINGS:
            if heading not in template_text:
                issues.append(f"Template missing required heading: {heading}")
        tmpl_start = template_text.find("## Checklist")
        if tmpl_start == -1:
            issues.append("Template missing ## Checklist section.")
        else:
            tmpl_section = template_text[tmpl_start:]
            next_h2 = re.search(r"\n## ", tmpl_section[len("## Checklist") :])
            if next_h2:
                tmpl_section = tmpl_section[: len("## Checklist") + next_h2.start()]
            tmpl_boxes = _checkbox_lines(tmpl_section)
            if skill_boxes and tmpl_boxes != skill_boxes:
                issues.append(
                    "Template ## Checklist checkboxes must exactly match SKILL.md ## Review Checklist "
                    f"(SKILL has {len(skill_boxes)} items, template has {len(tmpl_boxes)})."
                )

    return issues


def main() -> int:
    args = parse_args()
    skill_dir: Path = args.skill_dir
    issues = check_code_review_checklist_salesforce(skill_dir)

    if not issues:
        print(f"OK: skill package at {skill_dir} passes structure checks.")
        return 0

    for issue in issues:
        print(f"ERROR: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
