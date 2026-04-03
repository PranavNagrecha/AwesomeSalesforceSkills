#!/usr/bin/env python3
"""
skill_graph.py — Skill dependency graph and related-skill navigator

Given a skill ID (domain/skill-name), shows:
  1. Explicit dependencies  — listed in the skill's `dependencies:` frontmatter
  2. Dependents             — skills that explicitly depend on THIS skill
  3. Related skills         — skills with shared tags, same domain, or common triggers

Usage:
  python3 scripts/skill_graph.py apex/trigger-framework
  python3 scripts/skill_graph.py apex/trigger-framework --depth 2
  python3 scripts/skill_graph.py apex/trigger-framework --json
  python3 scripts/skill_graph.py --all                       # full graph summary
  python3 scripts/skill_graph.py --domain apex               # all relations in domain
  python3 scripts/skill_graph.py --tags bulkification        # skills by tag

Output (human mode):
  apex/trigger-framework
  ├── Depends on:     (none — add to dependencies: frontmatter)
  ├── Depended on by: (none found)
  └── Related skills:
        apex/governor-limits           [shared tags: bulkification]
        apex/recursive-trigger-prevention [same domain + shared tags: triggers]
        apex/test-class-standards      [same domain]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"

# ── Frontmatter parser (stdlib only) ─────────────────────────────────────────

def parse_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter from a SKILL.md string."""
    if not text.startswith("---"):
        return {}

    lines = text.splitlines()
    end = -1
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end = i
            break
    if end == -1:
        return {}

    fm: dict = {}
    current_key = None
    in_list = False
    in_inline_list = False

    for line in lines[1:end]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Inline list: key: [a, b, c]
        m = re.match(r'^(\w[\w-]*)\s*:\s*\[(.+)\]$', line)
        if m:
            key = m.group(1)
            vals = [v.strip().strip('"').strip("'") for v in m.group(2).split(",") if v.strip()]
            fm[key] = vals
            current_key = key
            in_list = False
            continue

        # Key: value (scalar)
        m = re.match(r'^(\w[\w-]*)\s*:\s*(.+)$', line)
        if m:
            key = m.group(1)
            val = m.group(2).strip().strip('"')
            # Empty list
            if val == "[]":
                fm[key] = []
            else:
                fm[key] = val
            current_key = key
            in_list = False
            continue

        # Key: (no value — starts a block list)
        m = re.match(r'^(\w[\w-]*)\s*:$', line)
        if m:
            key = m.group(1)
            fm[key] = []
            current_key = key
            in_list = True
            continue

        # List item
        if stripped.startswith("- ") and current_key:
            val = stripped[2:].strip().strip('"').strip("'")
            if isinstance(fm.get(current_key), list):
                fm[current_key].append(val)
            else:
                fm[current_key] = [val]
            in_list = True
            continue

    return fm


def load_all_skills() -> dict[str, dict]:
    """
    Load all SKILL.md files.
    Returns: { "domain/skill-name": {frontmatter + "_path": Path} }
    """
    skills = {}
    for skill_md in sorted(SKILLS_DIR.rglob("SKILL.md")):
        parts = skill_md.parts
        # Find position of "skills" in path
        try:
            idx = list(parts).index("skills")
        except ValueError:
            continue
        if len(parts) < idx + 3:
            continue
        domain = parts[idx + 1]
        skill_name = parts[idx + 2]
        skill_id = f"{domain}/{skill_name}"

        text = skill_md.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        fm["_id"] = skill_id
        fm["_path"] = skill_md
        skills[skill_id] = fm

    return skills


# ── Graph construction ────────────────────────────────────────────────────────

def build_graph(skills: dict[str, dict]) -> dict:
    """
    Build adjacency structures:
      - explicit_deps:   skill_id → [skill_ids it declares in dependencies:]
      - explicit_rdeps:  skill_id → [skill_ids that declare it as a dependency]
      - tag_index:       tag → [skill_ids with that tag]
      - domain_index:    domain → [skill_ids in that domain]
    """
    explicit_deps: dict[str, list[str]] = defaultdict(list)
    explicit_rdeps: dict[str, list[str]] = defaultdict(list)
    tag_index: dict[str, list[str]] = defaultdict(list)
    domain_index: dict[str, list[str]] = defaultdict(list)

    for sid, fm in skills.items():
        domain = sid.split("/")[0]
        domain_index[domain].append(sid)

        # Tags
        for tag in fm.get("tags", []):
            tag_index[tag.lower()].append(sid)

        # Explicit dependencies
        deps = fm.get("dependencies", [])
        if isinstance(deps, list):
            for dep in deps:
                dep = dep.strip()
                if dep and dep in skills:
                    explicit_deps[sid].append(dep)
                    explicit_rdeps[dep].append(sid)

    return {
        "explicit_deps": dict(explicit_deps),
        "explicit_rdeps": dict(explicit_rdeps),
        "tag_index": dict(tag_index),
        "domain_index": dict(domain_index),
    }


# ── Related skill finder ──────────────────────────────────────────────────────

def find_related(skill_id: str, skills: dict, graph: dict, top_k: int = 8) -> list[dict]:
    """
    Score and rank skills related to skill_id.
    Scoring:
      +3  shared tag (each)
      +2  same domain
      +1  overlapping trigger keywords
    Returns top_k results, excluding the skill itself and explicit deps/rdeps.
    """
    fm = skills.get(skill_id, {})
    my_tags = {t.lower() for t in fm.get("tags", [])}
    my_domain = skill_id.split("/")[0]
    my_triggers = " ".join(fm.get("triggers", [])).lower()

    exclude = {skill_id}
    exclude.update(graph["explicit_deps"].get(skill_id, []))
    exclude.update(graph["explicit_rdeps"].get(skill_id, []))

    scores: dict[str, dict] = {}

    for sid, sfm in skills.items():
        if sid in exclude:
            continue
        score = 0
        reasons = []

        # Shared tags
        their_tags = {t.lower() for t in sfm.get("tags", [])}
        shared = my_tags & their_tags
        if shared:
            score += len(shared) * 3
            reasons.append(f"shared tags: {', '.join(sorted(shared))}")

        # Same domain
        if sid.split("/")[0] == my_domain:
            score += 2
            reasons.append("same domain")

        # Trigger keyword overlap
        their_triggers = " ".join(sfm.get("triggers", [])).lower()
        trigger_words = set(re.findall(r'\b\w{5,}\b', my_triggers))
        their_words = set(re.findall(r'\b\w{5,}\b', their_triggers))
        overlap = trigger_words & their_words
        if overlap:
            score += min(len(overlap), 3)  # cap at 3
            if "shared tags" not in " ".join(reasons):  # don't double-note
                reasons.append("similar triggers")

        if score > 0:
            scores[sid] = {"score": score, "reasons": reasons}

    ranked = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
    return [
        {"id": sid, "score": info["score"], "reasons": info["reasons"]}
        for sid, info in ranked[:top_k]
    ]


# ── BFS / depth traversal ─────────────────────────────────────────────────────

def traverse_deps(skill_id: str, graph: dict, depth: int, direction: str = "down") -> dict:
    """
    BFS traversal of explicit dependency graph.
    direction="down" → follow explicit_deps (what this skill needs)
    direction="up"   → follow explicit_rdeps (what needs this skill)
    Returns nested dict tree.
    """
    key = "explicit_deps" if direction == "down" else "explicit_rdeps"
    visited = set()

    def _recurse(sid: str, remaining_depth: int) -> dict:
        if remaining_depth == 0 or sid in visited:
            return {}
        visited.add(sid)
        children = {}
        for dep in graph[key].get(sid, []):
            children[dep] = _recurse(dep, remaining_depth - 1)
        return children

    return _recurse(skill_id, depth)


# ── Output ────────────────────────────────────────────────────────────────────

def _tree_lines(tree: dict, prefix: str = "", is_last: bool = True) -> list[str]:
    lines = []
    items = list(tree.items())
    for i, (sid, subtree) in enumerate(items):
        connector = "└── " if i == len(items) - 1 else "├── "
        lines.append(f"{prefix}{connector}{sid}")
        ext = "    " if i == len(items) - 1 else "│   "
        lines.extend(_tree_lines(subtree, prefix + ext))
    return lines


def print_skill_view(skill_id: str, skills: dict, graph: dict, depth: int) -> None:
    fm = skills.get(skill_id, {})
    if not fm:
        print(f"ERROR: Skill '{skill_id}' not found.")
        print("Run: python3 scripts/skill_graph.py --all  to see available skills")
        return

    print(f"\n{skill_id}")
    desc = fm.get("description", "")
    if desc:
        # Show first sentence only
        short = desc.split(".")[0]
        print(f"  {short}.")
    print("")

    # Explicit deps
    deps = graph["explicit_deps"].get(skill_id, [])
    rdeps = graph["explicit_rdeps"].get(skill_id, [])

    print("── Explicit dependencies (this skill requires) ──────────────────")
    if deps:
        dep_tree = traverse_deps(skill_id, graph, depth, "down")
        for line in _tree_lines(dep_tree):
            print(f"  {line}")
    else:
        print("  (none — add skill IDs to `dependencies:` in SKILL.md to link them)")

    print("")
    print("── Depended on by ───────────────────────────────────────────────")
    if rdeps:
        rdep_tree = traverse_deps(skill_id, graph, depth, "up")
        for line in _tree_lines(rdep_tree):
            print(f"  {line}")
    else:
        print("  (no skills declare this as a dependency yet)")

    print("")
    print("── Related skills (by tag + domain similarity) ──────────────────")
    related = find_related(skill_id, skills, graph)
    if related:
        for r in related:
            reasons_str = "; ".join(r["reasons"])
            print(f"  {r['id']:<50} [{reasons_str}]")
    else:
        print("  (no related skills found)")

    print("")


def print_domain_view(domain: str, skills: dict, graph: dict) -> None:
    sids = graph["domain_index"].get(domain, [])
    if not sids:
        print(f"No skills found in domain: {domain}")
        return

    print(f"\nDomain: {domain} ({len(sids)} skills)\n")
    for sid in sorted(sids):
        deps = graph["explicit_deps"].get(sid, [])
        rdeps = graph["explicit_rdeps"].get(sid, [])
        dep_str = f"  deps→[{', '.join(deps)}]" if deps else ""
        rdep_str = f"  ←used-by[{', '.join(rdeps)}]" if rdeps else ""
        print(f"  {sid}{dep_str}{rdep_str}")


def print_all_view(skills: dict, graph: dict) -> None:
    print(f"\nSfSkills Graph Summary — {len(skills)} skills\n")

    # Domain breakdown
    print("── By domain ─────────────────────────────────────────────────────")
    for domain, sids in sorted(graph["domain_index"].items()):
        print(f"  {domain:<15} {len(sids):>3} skills")

    # Connection stats
    total_links = sum(len(v) for v in graph["explicit_deps"].values())
    print(f"\n── Explicit dependency links: {total_links} ──────────────────────────")
    if total_links == 0:
        print("  No explicit dependencies set yet.")
        print("  Add skill IDs to `dependencies:` frontmatter to link skills.")
        print("  Example:")
        print("    dependencies:")
        print("      - apex/governor-limits")
        print("      - apex/test-class-standards")
    else:
        print("\n  Most-depended-on skills (hubs):")
        rdep_counts = [(sid, len(rdeps)) for sid, rdeps in graph["explicit_rdeps"].items()]
        for sid, count in sorted(rdep_counts, key=lambda x: -x[1])[:10]:
            print(f"    {sid:<50} ← {count} skills depend on it")

    # Top tags
    print(f"\n── Top tags ──────────────────────────────────────────────────────")
    tag_counts = [(tag, len(sids)) for tag, sids in graph["tag_index"].items()]
    for tag, count in sorted(tag_counts, key=lambda x: -x[1])[:15]:
        print(f"  {tag:<35} {count:>3} skills")


def print_tag_view(tag: str, skills: dict, graph: dict) -> None:
    tag_lower = tag.lower()
    sids = graph["tag_index"].get(tag_lower, [])
    if not sids:
        # Fuzzy match
        matches = [t for t in graph["tag_index"] if tag_lower in t]
        if matches:
            print(f"Tag '{tag}' not found. Did you mean: {', '.join(matches[:5])}")
        else:
            print(f"Tag '{tag}' not found.")
            print(f"Available tags: {', '.join(sorted(graph['tag_index'].keys())[:20])}")
        return

    print(f"\nSkills tagged '{tag}' ({len(sids)}):\n")
    for sid in sorted(sids):
        fm = skills[sid]
        desc = fm.get("description", "")
        short = desc.split(".")[0] if desc else ""
        print(f"  {sid}")
        if short:
            print(f"    {short}.")


# ── JSON output ───────────────────────────────────────────────────────────────

def json_skill_view(skill_id: str, skills: dict, graph: dict, depth: int) -> dict:
    deps = graph["explicit_deps"].get(skill_id, [])
    rdeps = graph["explicit_rdeps"].get(skill_id, [])
    related = find_related(skill_id, skills, graph)

    dep_tree = traverse_deps(skill_id, graph, depth, "down")
    rdep_tree = traverse_deps(skill_id, graph, depth, "up")

    fm = skills.get(skill_id, {})
    return {
        "skill_id": skill_id,
        "name": fm.get("name", ""),
        "category": fm.get("category", ""),
        "tags": fm.get("tags", []),
        "explicit_dependencies": deps,
        "explicit_dependency_tree": dep_tree,
        "depended_on_by": rdeps,
        "dependent_tree": rdep_tree,
        "related": related,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Skill dependency graph and related-skill navigator.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/skill_graph.py apex/trigger-framework
  python3 scripts/skill_graph.py apex/trigger-framework --depth 2
  python3 scripts/skill_graph.py apex/trigger-framework --json
  python3 scripts/skill_graph.py --all
  python3 scripts/skill_graph.py --domain apex
  python3 scripts/skill_graph.py --tags bulkification
        """,
    )
    parser.add_argument("skill", nargs="?", help="Skill ID (domain/skill-name)")
    parser.add_argument("--all", action="store_true", help="Show full graph summary")
    parser.add_argument("--domain", help="Show all skills in a domain")
    parser.add_argument("--tags", help="Show skills with a specific tag")
    parser.add_argument("--depth", type=int, default=1, help="Traversal depth for explicit deps (default: 1)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--list-skills", action="store_true", help="List all skill IDs")

    args = parser.parse_args()

    skills = load_all_skills()
    graph = build_graph(skills)

    if args.list_skills:
        for sid in sorted(skills.keys()):
            print(sid)
        return 0

    if args.all:
        if args.json:
            out = {
                "total_skills": len(skills),
                "domains": {d: sorted(sids) for d, sids in sorted(graph["domain_index"].items())},
                "explicit_links": sum(len(v) for v in graph["explicit_deps"].values()),
                "top_tags": sorted(
                    [{"tag": t, "count": len(sids)} for t, sids in graph["tag_index"].items()],
                    key=lambda x: -x["count"]
                )[:20],
            }
            print(json.dumps(out, indent=2))
        else:
            print_all_view(skills, graph)
        return 0

    if args.domain:
        if args.json:
            sids = graph["domain_index"].get(args.domain, [])
            out = []
            for sid in sorted(sids):
                out.append(json_skill_view(sid, skills, graph, args.depth))
            print(json.dumps(out, indent=2))
        else:
            print_domain_view(args.domain, skills, graph)
        return 0

    if args.tags:
        if args.json:
            tag_lower = args.tags.lower()
            sids = graph["tag_index"].get(tag_lower, [])
            print(json.dumps({"tag": args.tags, "skills": sorted(sids)}, indent=2))
        else:
            print_tag_view(args.tags, skills, graph)
        return 0

    if args.skill:
        if args.json:
            out = json_skill_view(args.skill, skills, graph, args.depth)
            print(json.dumps(out, indent=2))
        else:
            print_skill_view(args.skill, skills, graph, args.depth)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
