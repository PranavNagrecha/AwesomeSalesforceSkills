#!/usr/bin/env python3
"""Add a skill citation to a run-time agent's AGENT.md.

Usage:
    python3 scripts/patch_agent_skill.py <agent_id> <skill_id> <section_heading> "<short description>"

Example:
    python3 scripts/patch_agent_skill.py field-impact-analyzer admin/lookup-filter-cross-object-patterns "### Field shape" "lookup filters cite fields"

What it does:
    1. Inserts `    - <skill_id>` into the YAML `dependencies.skills:` block, preserving alphabetical order.
    2. Appends a numbered bullet `<N>. \`skills/<skill_id>\` — <description>` at the end of the block under <section_heading>.
    3. Renumbers every subsequent numbered list item in the Mandatory Reads section so the sequence stays monotonic.

Idempotent: re-running with the same args is a no-op (skill already cited).

Stdlib only.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _yaml_skill_block_bounds(lines: list[str]) -> tuple[int, int]:
    """Return (start, end) line indices (inclusive) of `  skills:` items."""
    in_deps = False
    in_skills = False
    start = end = -1
    for i, line in enumerate(lines):
        stripped = line.rstrip("\n")
        if not in_deps and re.match(r"^dependencies:\s*$", stripped):
            in_deps = True
            continue
        if in_deps and re.match(r"^  skills:\s*$", stripped):
            in_skills = True
            start = i + 1
            continue
        if in_skills:
            if re.match(r"^    -\s+\S", stripped):
                end = i
            elif stripped.startswith("---") or re.match(r"^  [a-z]", stripped):
                break
            elif not stripped.strip():
                continue
            else:
                break
    if start == -1 or end == -1:
        raise SystemExit("Could not find dependencies.skills block")
    return start, end


def insert_yaml_skill(lines: list[str], skill_id: str) -> bool:
    start, end = _yaml_skill_block_bounds(lines)
    existing = [lines[i].strip().removeprefix("- ").strip() for i in range(start, end + 1)]
    if skill_id in existing:
        return False
    insert_line = f"    - {skill_id}\n"
    for i in range(start, end + 1):
        existing_id = lines[i].strip().removeprefix("- ").strip()
        if skill_id < existing_id:
            lines.insert(i, insert_line)
            return True
    lines.insert(end + 1, insert_line)
    return True


def _mandatory_reads_bounds(lines: list[str]) -> tuple[int, int]:
    start = end = -1
    for i, line in enumerate(lines):
        if re.match(r"^## Mandatory Reads\b", line):
            start = i
        elif start != -1 and re.match(r"^## ", line):
            end = i - 1
            break
    if start == -1:
        raise SystemExit("No '## Mandatory Reads' section found")
    if end == -1:
        end = len(lines) - 1
    return start, end


def append_under_section(
    lines: list[str], section_heading: str, skill_id: str, description: str
) -> bool:
    mr_start, mr_end = _mandatory_reads_bounds(lines)

    if section_heading == "*end*":
        section_idx = mr_start
        next_section_idx = mr_end + 1
    else:
        section_idx = -1
        for i in range(mr_start, mr_end + 1):
            if lines[i].rstrip("\n") == section_heading:
                section_idx = i
                break
        if section_idx == -1:
            raise SystemExit(f"Section '{section_heading}' not found inside Mandatory Reads")

        next_section_idx = mr_end + 1
        for i in range(section_idx + 1, mr_end + 1):
            if re.match(r"^### ", lines[i]):
                next_section_idx = i
                break

    last_numbered_idx = -1
    last_n = 0
    for i in range(section_idx + 1, next_section_idx):
        m = re.match(r"^(\d+)\. ", lines[i])
        if m:
            last_numbered_idx = i
            last_n = int(m.group(1))

    skill_line = f"`skills/{skill_id}`"
    for i in range(mr_start, mr_end + 1):
        m = re.match(r"^\d+\. (.*)$", lines[i].rstrip("\n"))
        if m and m.group(1).startswith(skill_line):
            return False

    new_n = last_n + 1
    new_line = f"{new_n}. `skills/{skill_id}` — {description}\n"

    if last_numbered_idx == -1:
        insert_at = section_idx + 1
        while insert_at < next_section_idx and not lines[insert_at].strip():
            insert_at += 1
        lines.insert(insert_at, new_line)
        if insert_at + 1 < len(lines) and lines[insert_at + 1].strip():
            lines.insert(insert_at + 1, "\n")
    else:
        lines.insert(last_numbered_idx + 1, new_line)

    for i in range(last_numbered_idx + 2, mr_end + 2):
        if i >= len(lines):
            break
        m = re.match(r"^(\d+)\. (.*)$", lines[i])
        if m:
            lines[i] = f"{int(m.group(1)) + 1}. {m.group(2)}\n"
    return True


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("agent_id")
    p.add_argument("skill_id")
    p.add_argument("section_heading", help='e.g. "### Field shape & data model"')
    p.add_argument("description")
    args = p.parse_args()

    agent_md = REPO / "agents" / args.agent_id / "AGENT.md"
    if not agent_md.exists():
        print(f"ERROR: {agent_md} not found", file=sys.stderr)
        return 1

    skill_md = REPO / "skills" / f"{args.skill_id}/SKILL.md"
    if not skill_md.exists():
        print(f"ERROR: skill {args.skill_id} not found at {skill_md}", file=sys.stderr)
        return 1

    lines = agent_md.read_text(encoding="utf-8").splitlines(keepends=True)
    a = insert_yaml_skill(lines, args.skill_id)
    b = append_under_section(lines, args.section_heading, args.skill_id, args.description)

    if not a and not b:
        print(f"[{args.agent_id}] {args.skill_id} already cited")
        return 0

    agent_md.write_text("".join(lines), encoding="utf-8")
    actions: list[str] = []
    if a:
        actions.append("YAML")
    if b:
        actions.append("Mandatory Reads")
    print(f"[{args.agent_id}] added {args.skill_id} to: {' + '.join(actions)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
