#!/usr/bin/env python3
"""
export_skills.py — Multi-platform skill exporter

Converts the SfSkills repo into formats consumed by:
  - Cursor       (.cursor/rules/*.mdc)
  - Aider        (CONVENTIONS.md)
  - Windsurf     (.windsurf/rules/*.md)
  - Augment      (.augment/rules/*.md)
  - Claude Code  (.claude/skills/<name>/) — canonical format, no conversion needed

Usage:
  python3 scripts/export_skills.py --platform cursor
  python3 scripts/export_skills.py --platform aider
  python3 scripts/export_skills.py --platform windsurf
  python3 scripts/export_skills.py --platform augment
  python3 scripts/export_skills.py --all
  python3 scripts/export_skills.py --platform cursor --domain apex
  python3 scripts/export_skills.py --platform cursor --skill apex/trigger-framework

Output directories:
  exports/cursor/
  exports/aider/
  exports/windsurf/
  exports/augment/
"""

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
EXPORTS_DIR = REPO_ROOT / "exports"
REGISTRY_FILE = REPO_ROOT / "registry" / "skills.json"

PLATFORMS = ["cursor", "aider", "windsurf", "augment"]


# ── Frontmatter parsing ───────────────────────────────────────────────────────

def parse_frontmatter(skill_md_path: Path) -> tuple[dict, str]:
    """Parse YAML frontmatter and body from a SKILL.md file. Stdlib only."""
    content = skill_md_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {}, content

    end = content.find("---", 3)
    if end == -1:
        return {}, content

    fm_text = content[3:end].strip()
    body = content[end + 3:].strip()

    # Minimal YAML parser for our specific frontmatter shape (no nested structures)
    meta = {}
    current_key = None
    current_list = None

    for line in fm_text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue

        if line.startswith("  - ") and current_list is not None:
            current_list.append(line[4:].strip().strip('"'))
            continue

        if ":" in line and not line.startswith(" "):
            current_list = None
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"')
            if val == "":
                current_list = []
                meta[key] = current_list
                current_key = key
            else:
                # Handle inline lists like: tags: [a, b, c]
                if val.startswith("[") and val.endswith("]"):
                    meta[key] = [v.strip().strip('"') for v in val[1:-1].split(",")]
                else:
                    meta[key] = val
                    current_key = key

    return meta, body


def load_all_skills(domain_filter: str = None, skill_filter: str = None) -> list[dict]:
    """Load all skill packages, optionally filtered by domain or specific skill."""
    skills = []

    for skill_md in sorted(SKILLS_DIR.rglob("SKILL.md")):
        # Skip agent SKILL.md files
        if "agents" in str(skill_md):
            continue

        parts = skill_md.parts
        try:
            skills_idx = parts.index("skills")
            domain = parts[skills_idx + 1]
            skill_name = parts[skills_idx + 2]
        except (ValueError, IndexError):
            continue

        if domain_filter and domain != domain_filter:
            continue
        if skill_filter and f"{domain}/{skill_name}" != skill_filter:
            continue

        meta, body = parse_frontmatter(skill_md)
        if not meta.get("name"):
            continue

        skill_path = skill_md.parent

        # Load supporting files
        references = {}
        for ref_file in ["examples.md", "gotchas.md", "well-architected.md"]:
            ref_path = skill_path / "references" / ref_file
            if ref_path.exists():
                references[ref_file] = ref_path.read_text(encoding="utf-8")

        templates = {}
        templates_dir = skill_path / "templates"
        if templates_dir.exists():
            for tmpl in templates_dir.glob("*.md"):
                templates[tmpl.name] = tmpl.read_text(encoding="utf-8")

        skills.append({
            "name": meta.get("name", skill_name),
            "description": meta.get("description", ""),
            "category": meta.get("category", domain),
            "domain": domain,
            "skill_name": skill_name,
            "tags": meta.get("tags", []),
            "triggers": meta.get("triggers", []),
            "version": meta.get("version", "1.0.0"),
            "body": body,
            "references": references,
            "templates": templates,
            "path": str(skill_path),
            "meta": meta,
        })

    return skills


# ── Platform exporters ────────────────────────────────────────────────────────

def export_cursor(skills: list[dict], output_dir: Path) -> int:
    """
    Cursor format: .cursor/rules/<skill-name>.mdc
    Frontmatter: description (for discovery), globs (optional), alwaysApply: false
    Body: full skill content
    """
    rules_dir = output_dir / ".cursor" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for skill in skills:
        # Cursor description must be concise — use first sentence only
        description = skill["description"]
        first_sentence = description.split(".")[0].strip()
        if len(first_sentence) > 120:
            first_sentence = first_sentence[:117] + "..."

        # Build combined content: skill body + gotchas + examples
        combined = skill["body"]
        if skill["references"].get("gotchas.md"):
            combined += "\n\n---\n\n" + skill["references"]["gotchas.md"]
        if skill["references"].get("examples.md"):
            combined += "\n\n---\n\n" + skill["references"]["examples.md"]

        mdc_content = f"""---
description: {first_sentence}
alwaysApply: false
---

{combined}
"""
        out_file = rules_dir / f"{skill['domain']}-{skill['skill_name']}.mdc"
        out_file.write_text(mdc_content, encoding="utf-8")
        count += 1

    # Write index
    index_lines = ["# SfSkills — Cursor Rules Index\n"]
    index_lines.append("Auto-generated. Do not edit manually — run `python3 scripts/export_skills.py --platform cursor`\n\n")
    for skill in sorted(skills, key=lambda s: (s["domain"], s["name"])):
        index_lines.append(f"- `{skill['domain']}-{skill['skill_name']}.mdc` — {skill['name']}\n")
    (output_dir / ".cursor" / "rules" / "INDEX.md").write_text("".join(index_lines), encoding="utf-8")

    return count


def export_aider(skills: list[dict], output_dir: Path) -> int:
    """
    Aider format: single CONVENTIONS.md concatenating all skills.
    Organized by domain with clear section headers.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    sections = {}
    for skill in skills:
        domain = skill["domain"]
        if domain not in sections:
            sections[domain] = []
        sections[domain].append(skill)

    lines = [
        "# Salesforce Coding Conventions & Skills\n\n",
        "This file is auto-generated from the SfSkills repository.\n",
        "Do not edit manually — run `python3 scripts/export_skills.py --platform aider`\n\n",
        "---\n\n",
    ]

    for domain in sorted(sections.keys()):
        lines.append(f"# {domain.upper()}\n\n")
        for skill in sorted(sections[domain], key=lambda s: s["name"]):
            lines.append(f"## {skill['name']}\n\n")
            lines.append(f"_{skill['description']}_\n\n")
            lines.append(skill["body"])
            lines.append("\n\n")
            if skill["references"].get("gotchas.md"):
                lines.append("### Gotchas\n\n")
                lines.append(skill["references"]["gotchas.md"])
                lines.append("\n\n")
            lines.append("---\n\n")

    (output_dir / "CONVENTIONS.md").write_text("".join(lines), encoding="utf-8")
    return len(skills)


def export_windsurf(skills: list[dict], output_dir: Path) -> int:
    """
    Windsurf format: .windsurf/rules/<skill-name>.md
    Frontmatter: description, trigger (optional)
    """
    rules_dir = output_dir / ".windsurf" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for skill in skills:
        description = skill["description"]
        if len(description) > 200:
            description = description[:197] + "..."

        # Triggers as activation hints
        trigger_hint = ""
        if skill.get("triggers"):
            trigger_hint = "\n".join(f"  - {t}" for t in skill["triggers"][:3])

        combined = skill["body"]
        if skill["references"].get("gotchas.md"):
            combined += "\n\n---\n\n" + skill["references"]["gotchas.md"]

        content = f"""---
description: >
  {description}
triggers:
{trigger_hint}
---

{combined}
"""
        out_file = rules_dir / f"{skill['domain']}-{skill['skill_name']}.md"
        out_file.write_text(content, encoding="utf-8")
        count += 1

    return count


def export_augment(skills: list[dict], output_dir: Path) -> int:
    """
    Augment format: .augment/rules/<skill-name>.md
    Frontmatter: type: auto, description
    """
    rules_dir = output_dir / ".augment" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for skill in skills:
        description = skill["description"]
        first_sentence = description.split(".")[0].strip()

        combined = skill["body"]
        if skill["references"].get("gotchas.md"):
            combined += "\n\n---\n\n" + skill["references"]["gotchas.md"]
        if skill["references"].get("examples.md"):
            combined += "\n\n---\n\n" + skill["references"]["examples.md"]

        content = f"""---
type: auto
description: {first_sentence}
---

{combined}
"""
        out_file = rules_dir / f"{skill['domain']}-{skill['skill_name']}.md"
        out_file.write_text(content, encoding="utf-8")
        count += 1

    return count


# ── Main ──────────────────────────────────────────────────────────────────────

EXPORTERS = {
    "cursor": export_cursor,
    "aider": export_aider,
    "windsurf": export_windsurf,
    "augment": export_augment,
}


def main():
    parser = argparse.ArgumentParser(
        description="Export SfSkills to platform-specific formats.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/export_skills.py --platform cursor
  python3 scripts/export_skills.py --platform aider --domain apex
  python3 scripts/export_skills.py --all
  python3 scripts/export_skills.py --platform cursor --skill apex/trigger-framework
        """,
    )
    parser.add_argument(
        "--platform",
        choices=PLATFORMS,
        help="Target platform to export for",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Export for all supported platforms",
    )
    parser.add_argument(
        "--domain",
        help="Filter: only export skills from this domain (e.g. apex, admin, lwc)",
    )
    parser.add_argument(
        "--skill",
        help="Filter: only export one skill (e.g. apex/trigger-framework)",
    )
    parser.add_argument(
        "--output",
        default=str(EXPORTS_DIR),
        help=f"Output directory (default: {EXPORTS_DIR})",
    )

    args = parser.parse_args()

    if not args.platform and not args.all:
        parser.error("Specify --platform <name> or --all")

    output_root = Path(args.output)

    # Load skills
    print(f"Loading skills from {SKILLS_DIR}...")
    skills = load_all_skills(
        domain_filter=args.domain,
        skill_filter=args.skill,
    )

    if not skills:
        print("ERROR: No skills found matching the filter.")
        sys.exit(1)

    print(f"  Found {len(skills)} skills")

    # Determine which platforms to export
    platforms_to_run = PLATFORMS if args.all else [args.platform]

    # Run exporters
    results = {}
    for platform in platforms_to_run:
        platform_dir = output_root / platform
        exporter = EXPORTERS[platform]
        print(f"\nExporting to {platform}...")
        count = exporter(skills, platform_dir)
        results[platform] = count
        print(f"  {count} skills exported → {platform_dir}")

    # Summary
    print("\n" + "=" * 50)
    print("EXPORT COMPLETE")
    print("=" * 50)
    for platform, count in results.items():
        print(f"  {platform:12} {count} skills → exports/{platform}/")

    print("\nInstallation instructions:")
    print("  Cursor:   Copy exports/cursor/.cursor/ → your project root")
    print("  Aider:    Copy exports/aider/CONVENTIONS.md → your project root")
    print("  Windsurf: Copy exports/windsurf/.windsurf/ → your project root")
    print("  Augment:  Copy exports/augment/.augment/ → your project root")
    print("  Claude Code: Skills are already in skills/ — no export needed")


if __name__ == "__main__":
    main()
