#!/usr/bin/env python3
"""Batch scaffolder + agent wirer.

Reads a YAML batch spec, materialises N skills (stubs or from staging content),
and patches listed agents (dependencies.skills, Mandatory Reads, kind enum).

Usage:
    python3 scripts/skill_forge.py --batch batches/my-batch.yaml
    python3 scripts/skill_forge.py --batch batches/my-batch.yaml --dry-run

Batch spec:

    skills:
      - slug: apex-foo-bar
        category: apex
        description: "Use when ... NOT for ..."
        pillars: [Security, Reliability]
        tags: [foo-bar, foo]
        triggers:
          - "user phrase 1"
          - "user phrase 2"
          - "user phrase 3"
        inputs:
          - "input the skill needs"
        outputs:
          - "artifact the skill produces"
        # Optional — path to a staging directory holding pre-authored
        # content files (SKILL_body.md, examples.md, gotchas.md,
        # llm-anti-patterns.md, well-architected.md, template.md, check.py).
        # Missing files fall back to TODO stubs.
        staging_dir: staging/apex-foo-bar
        agents:
          - name: apex-builder
            descriptor: "short gloss for Mandatory Reads line"
            kind: foo_kind      # optional — also added to inputs.schema.json enum

Spec validation fails fast; no partial writes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml  # PyYAML, listed in requirements.txt

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Reuse new_skill.py's stub writers so stub output stays consistent.
from scripts import new_skill as _ns  # noqa: E402

ALLOWED_CATEGORIES = _ns.ALLOWED_CATEGORIES
ALLOWED_PILLARS = {
    "Security",
    "Performance",
    "Scalability",
    "Reliability",
    "User Experience",
    "Operational Excellence",
}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


# ----------------------------- spec model ----------------------------- #


@dataclass
class AgentWire:
    name: str
    descriptor: str
    kind: str | None = None


@dataclass
class SkillSpec:
    slug: str
    category: str
    description: str
    pillars: list[str]
    tags: list[str]
    triggers: list[str]
    inputs: list[str]
    outputs: list[str]
    staging_dir: Path | None
    agents: list[AgentWire] = field(default_factory=list)
    salesforce_version: str = "Spring '25+"
    version: str = "1.0.0"
    author: str = "Pranav Nagrecha"


def _validate_spec(raw: dict, index: int) -> SkillSpec:
    def err(msg: str) -> SystemExit:
        return SystemExit(f"Spec error (skill #{index + 1}): {msg}")

    for req in ("slug", "category", "description", "pillars", "tags", "triggers", "inputs", "outputs"):
        if req not in raw:
            raise err(f"missing required field '{req}'")

    slug = raw["slug"]
    if not SLUG_RE.fullmatch(slug):
        raise err(f"slug '{slug}' must be lowercase, hyphenated, alphanumeric only")

    category = raw["category"]
    if category not in ALLOWED_CATEGORIES:
        raise err(f"category '{category}' not in {sorted(ALLOWED_CATEGORIES)}")

    pillars = list(raw["pillars"])
    bad = [p for p in pillars if p not in ALLOWED_PILLARS]
    if bad:
        raise err(f"unknown pillars {bad}; allowed: {sorted(ALLOWED_PILLARS)}")

    triggers = list(raw["triggers"])
    if len(triggers) < 3:
        raise err("triggers must have at least 3 phrases (frontmatter convention)")

    staging = raw.get("staging_dir")
    staging_path: Path | None
    if staging:
        p = (ROOT / staging).resolve()
        if not p.exists() or not p.is_dir():
            raise err(f"staging_dir '{staging}' does not exist or is not a directory")
        staging_path = p
    else:
        staging_path = None

    agents_raw = raw.get("agents", []) or []
    agents: list[AgentWire] = []
    for a_idx, a in enumerate(agents_raw):
        if not isinstance(a, dict) or "name" not in a or "descriptor" not in a:
            raise err(f"agents[{a_idx}] must be a mapping with 'name' and 'descriptor'")
        agent_dir = ROOT / "agents" / a["name"]
        if not agent_dir.exists():
            raise err(f"agents[{a_idx}].name '{a['name']}' does not resolve to agents/{a['name']}")
        agents.append(AgentWire(name=a["name"], descriptor=a["descriptor"], kind=a.get("kind")))

    return SkillSpec(
        slug=slug,
        category=category,
        description=raw["description"],
        pillars=pillars,
        tags=list(raw["tags"]),
        triggers=triggers,
        inputs=list(raw["inputs"]),
        outputs=list(raw["outputs"]),
        staging_dir=staging_path,
        agents=agents,
        salesforce_version=raw.get("salesforce_version", "Spring '25+"),
        version=raw.get("version", "1.0.0"),
        author=raw.get("author", "Pranav Nagrecha"),
    )


def _load_batch(path: Path) -> list[SkillSpec]:
    if not path.exists():
        raise SystemExit(f"Batch file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "skills" not in data:
        raise SystemExit("Batch YAML must be a mapping with a top-level 'skills:' list")
    specs = data["skills"]
    if not isinstance(specs, list) or not specs:
        raise SystemExit("'skills' must be a non-empty list")
    return [_validate_spec(s, i) for i, s in enumerate(specs)]


# --------------------------- file materialisation --------------------------- #


def _frontmatter(spec: SkillSpec) -> str:
    today = date.today().isoformat()
    pillars = "\n".join(f"  - {p}" for p in spec.pillars)
    triggers = "\n".join(f'  - "{_esc_yaml(t)}"' for t in spec.triggers)
    tags = "\n".join(f"  - {t}" for t in spec.tags)
    inputs = "\n".join(f'  - "{_esc_yaml(i)}"' for i in spec.inputs)
    outputs = "\n".join(f'  - "{_esc_yaml(o)}"' for o in spec.outputs)
    return (
        "---\n"
        f"name: {spec.slug}\n"
        f'description: "{_esc_yaml(spec.description)}"\n'
        f"category: {spec.category}\n"
        f'salesforce-version: "{spec.salesforce_version}"\n'
        "well-architected-pillars:\n"
        f"{pillars}\n"
        "triggers:\n"
        f"{triggers}\n"
        "tags:\n"
        f"{tags}\n"
        "inputs:\n"
        f"{inputs}\n"
        "outputs:\n"
        f"{outputs}\n"
        "dependencies: []\n"
        f"version: {spec.version}\n"
        f"author: {spec.author}\n"
        f"updated: {today}\n"
        "---\n\n"
    )


def _esc_yaml(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _read_staging(spec: SkillSpec, filename: str) -> str | None:
    if spec.staging_dir is None:
        return None
    candidate = spec.staging_dir / filename
    if candidate.exists():
        return candidate.read_text(encoding="utf-8")
    return None


def _skill_md_body_stub(spec: SkillSpec) -> str:
    title = spec.slug.replace("-", " ").title()
    return (
        f"# {title}\n\n"
        "TODO: Write a 1-2 sentence activation summary.\n\n"
        "---\n\n"
        "## Before Starting\n\n"
        "- TODO: context question 1\n"
        "- TODO: context question 2\n\n"
        "---\n\n"
        "## Core Concepts\n\n"
        "TODO: key platform concepts.\n\n"
        "---\n\n"
        "## Common Patterns\n\n"
        "### Pattern 1: TODO\n\n"
        "**When to use:** TODO\n\n"
        "```apex\n// TODO\n```\n\n"
        "---\n\n"
        "## Decision Guidance\n\n"
        "| Situation | Recommended Approach | Reason |\n"
        "|---|---|---|\n"
        "| TODO | TODO | TODO |\n\n"
        "---\n\n"
        "## Recommended Workflow\n\n"
        "1. TODO\n"
        "2. TODO\n"
        "3. TODO\n\n"
        "---\n\n"
        "## Review Checklist\n\n"
        "- [ ] TODO\n\n"
        "---\n\n"
        "## Salesforce-Specific Gotchas\n\n"
        "See `references/gotchas.md`.\n\n"
        "---\n\n"
        "## Output Artifacts\n\n"
        "| Artifact | Description |\n"
        "|---|---|\n"
        f"| `scripts/check_{spec.slug.replace('-', '_')}.py` | Stdlib checker |\n"
        f"| `templates/{spec.slug}-template.md` | Work template |\n\n"
        "---\n\n"
        "## Related Skills\n\n"
        "- TODO\n"
    )


def _materialise_skill(spec: SkillSpec, dry_run: bool) -> list[Path]:
    skill_dir = ROOT / "skills" / spec.category / spec.slug
    if skill_dir.exists():
        raise SystemExit(f"Skill already exists: skills/{spec.category}/{spec.slug}")

    noun = spec.slug.replace("-", "_")
    title = spec.slug.replace("-", " ").title()

    # Content — staging preferred, stubs as fallback.
    skill_body = _read_staging(spec, "SKILL_body.md") or _skill_md_body_stub(spec)
    examples = _read_staging(spec, "examples.md") or _ns._scaffold_examples_md(spec.slug)
    gotchas = _read_staging(spec, "gotchas.md") or _ns._scaffold_gotchas_md(spec.slug)
    llm_ap = _read_staging(spec, "llm-anti-patterns.md") or _ns._scaffold_llm_anti_patterns_md(
        spec.slug, spec.category
    )
    wa = _read_staging(spec, "well-architected.md") or _ns._scaffold_well_architected_md(
        spec.slug, spec.category
    )
    template_md = _read_staging(spec, "template.md") or _ns._scaffold_template_md(spec.slug)
    checker_py = _read_staging(spec, "check.py") or _ns._scaffold_checker_script(
        spec.slug, spec.category
    )

    skill_md = _frontmatter(spec) + skill_body

    writes: list[tuple[Path, str, bool]] = [
        (skill_dir / "SKILL.md", skill_md, False),
        (skill_dir / "references" / "examples.md", examples, False),
        (skill_dir / "references" / "gotchas.md", gotchas, False),
        (skill_dir / "references" / "llm-anti-patterns.md", llm_ap, False),
        (skill_dir / "references" / "well-architected.md", wa, False),
        (skill_dir / "templates" / f"{spec.slug}-template.md", template_md, False),
        (skill_dir / "scripts" / f"check_{noun}.py", checker_py, True),
    ]

    created: list[Path] = []
    if dry_run:
        for path, _, _ in writes:
            created.append(path)
        return created

    for path, content, executable in writes:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        if executable:
            path.chmod(0o755)
        created.append(path)
    return created


# --------------------------- agent patching --------------------------- #

_DEP_LINE_RE = re.compile(r"^\s+-\s+(?P<val>[a-z0-9_\-/]+)\s*$")


def _patch_agent_md(agent_name: str, category: str, slug: str, descriptor: str, dry_run: bool) -> None:
    path = ROOT / "agents" / agent_name / "AGENT.md"
    if not path.exists():
        raise SystemExit(f"Agent file not found: {path}")
    text = path.read_text(encoding="utf-8")

    dep_entry = f"    - {category}/{slug}"
    reads_entry = f"`skills/{category}/{slug}` — {descriptor}"

    if dep_entry in text and reads_entry in text:
        return  # idempotent no-op

    new_text = _insert_into_deps(text, category, slug, agent_name)
    new_text = _insert_into_mandatory_reads(new_text, category, slug, descriptor, agent_name)

    if new_text == text:
        return
    if dry_run:
        return
    path.write_text(new_text, encoding="utf-8")


def _insert_into_deps(text: str, category: str, slug: str, agent_name: str) -> str:
    """Insert '<category>/<slug>' alphabetically into dependencies.skills (YAML frontmatter)."""
    entry = f"    - {category}/{slug}"
    if entry in text:
        return text

    # Frontmatter lives between two '---' lines at the top.
    lines = text.splitlines(keepends=True)
    fm_start, fm_end = None, None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "---":
            if fm_start is None:
                fm_start = i
            else:
                fm_end = i
                break
    if fm_start is None or fm_end is None:
        raise SystemExit(f"agents/{agent_name}/AGENT.md has no YAML frontmatter")

    # Find 'skills:' under 'dependencies:' within frontmatter.
    in_deps = False
    skills_line = None
    for i in range(fm_start + 1, fm_end):
        line = lines[i]
        if re.match(r"^dependencies\s*:\s*$", line):
            in_deps = True
            continue
        if in_deps and re.match(r"^\s+skills\s*:\s*$", line):
            skills_line = i
            break
        if in_deps and re.match(r"^\S", line):
            break

    if skills_line is None:
        raise SystemExit(f"agents/{agent_name}/AGENT.md missing dependencies.skills block")

    # Collect the existing skill entries that follow, stop at the first less-indented line.
    i = skills_line + 1
    skill_lines: list[tuple[int, str]] = []
    while i < fm_end:
        line = lines[i]
        if _DEP_LINE_RE.match(line):
            skill_lines.append((i, _DEP_LINE_RE.match(line).group("val")))
            i += 1
        elif line.strip() == "" or line.startswith("    "):
            # Blank or further-indented line inside the block (rare but allow).
            i += 1
        else:
            break

    # Alphabetic insertion.
    new_value = f"{category}/{slug}"
    insert_at = skills_line + 1
    for idx, val in skill_lines:
        if new_value < val:
            insert_at = idx
            break
        insert_at = idx + 1

    new_lines = lines[:insert_at] + [entry + "\n"] + lines[insert_at:]
    return "".join(new_lines)


def _insert_into_mandatory_reads(
    text: str, category: str, slug: str, descriptor: str, agent_name: str
) -> str:
    target = f"`skills/{category}/{slug}`"
    if target in text:
        return text

    lines = text.splitlines(keepends=True)

    # Find '## Mandatory Reads Before Starting' anchor.
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("## Mandatory Reads"):
            start = i
            break
    if start is None:
        raise SystemExit(f"agents/{agent_name}/AGENT.md has no '## Mandatory Reads' section")

    # Scan forward, find the last numbered line that references a skills/ path.
    num_re = re.compile(r"^\s*(\d+)\.\s+`skills/")
    last_skill_idx = None
    last_num = 0
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line.strip().startswith("##"):
            break
        m = num_re.match(line)
        if m:
            last_skill_idx = i
            last_num = int(m.group(1))

    new_line = f"{last_num + 1}. `skills/{category}/{slug}` — {descriptor}\n"

    if last_skill_idx is None:
        # No skills entries yet — insert right after the heading + blank line.
        insert_at = start + 2 if (start + 1 < len(lines) and lines[start + 1].strip() == "") else start + 1
        return "".join(lines[:insert_at] + [new_line] + lines[insert_at:])

    # Insert after the last skills/ entry, shifting all later numbered lines by +1.
    insert_at = last_skill_idx + 1
    head = lines[:insert_at]
    tail = lines[insert_at:]
    shifted = _renumber_list_tail(tail, last_num + 1)
    return "".join(head + [new_line] + shifted)


def _renumber_list_tail(tail: list[str], start_num_excluded: int) -> list[str]:
    """Bump subsequent numbered list items in the same section by +1.

    start_num_excluded is the number we just inserted; the FIRST numbered item
    we encounter should become start_num_excluded + 1, etc.
    """
    num_re = re.compile(r"^(\s*)(\d+)(\.\s+)")
    out: list[str] = []
    expected = start_num_excluded + 1
    for line in tail:
        if line.strip().startswith("##"):
            out.extend(tail[len(out):])
            return out
        m = num_re.match(line)
        if m:
            out.append(f"{m.group(1)}{expected}{m.group(3)}{line[m.end():]}")
            expected += 1
        else:
            out.append(line)
    return out


def _patch_inputs_schema(agent_name: str, kind: str, dry_run: bool) -> None:
    path = ROOT / "agents" / agent_name / "inputs.schema.json"
    if not path.exists():
        return  # agent may have no inputs schema
    data = json.loads(path.read_text(encoding="utf-8"))
    enum = data.get("properties", {}).get("kind", {}).get("enum")
    if enum is None:
        return
    if kind in enum:
        return
    # Insert before 'test_only' if present, else append.
    if "test_only" in enum:
        idx = enum.index("test_only")
        enum.insert(idx, kind)
    else:
        enum.append(kind)
    if dry_run:
        return
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


# --------------------------- CLI --------------------------- #


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch scaffolder + agent wirer.")
    parser.add_argument("--batch", required=True, help="Path to batch YAML.")
    parser.add_argument("--dry-run", action="store_true", help="Plan only; no writes.")
    args = parser.parse_args()

    specs = _load_batch(Path(args.batch))
    print(f"Loaded {len(specs)} skill spec(s) from {args.batch}")

    created_files: list[Path] = []
    for spec in specs:
        paths = _materialise_skill(spec, dry_run=args.dry_run)
        created_files.extend(paths)
        for agent in spec.agents:
            _patch_agent_md(agent.name, spec.category, spec.slug, agent.descriptor, dry_run=args.dry_run)
            if agent.kind:
                _patch_inputs_schema(agent.name, agent.kind, dry_run=args.dry_run)
        action = "Would create" if args.dry_run else "Created"
        print(f"  {action}: skills/{spec.category}/{spec.slug}/ ({len(paths)} files)")
        for a in spec.agents:
            kind_str = f" +kind={a.kind}" if a.kind else ""
            action = "would patch" if args.dry_run else "patched"
            print(f"    {action} agents/{a.name}/AGENT.md{kind_str}")

    print(
        f"\n{'[DRY-RUN] ' if args.dry_run else ''}Done. "
        f"{len(specs)} skill(s), {len(created_files)} file(s) {'planned' if args.dry_run else 'written'}."
    )
    if not args.dry_run:
        print("\nNext: python3 scripts/skill_sync.py --changed-only && "
              "python3 scripts/validate_repo.py --changed-only")
    return 0


if __name__ == "__main__":
    sys.exit(main())
