#!/usr/bin/env python3
"""Auto-populate the `dependencies` frontmatter block on every AGENT.md.

Parses each AGENT.md's Mandatory Reads section + all citation patterns in the
body, infers which files the agent depends on, and writes a `dependencies:`
block into the frontmatter if one doesn't already exist.

One-time migration introduced in Wave 8. Re-runnable — idempotent.

Usage:
    python3 scripts/migrate_agent_dependencies.py --dry-run    # preview
    python3 scripts/migrate_agent_dependencies.py              # write
    python3 scripts/migrate_agent_dependencies.py --agent foo  # one agent
    python3 scripts/migrate_agent_dependencies.py --force      # overwrite

Why this exists: `dependencies` is the load-bearing block for
`scripts/export_skills.py --agent <id>` (Wave 8). Without it, the bundle
exporter can't know what to bundle alongside each agent. The migration
reads the human-authored Mandatory Reads section — which was already the
source of truth — and shapes it into a machine-readable list.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / "agents"

# Citation-extraction patterns mirror pipelines/agent_validators.py
_SKILL_BACKTICK = re.compile(r"`skills/([a-z0-9-]+)/([a-z0-9-]+)(?:/[A-Za-z0-9_./-]*)?`")
_SKILL_BARE = re.compile(r"`([a-z0-9-]+)/([a-z0-9-]+)`")
_PROBE = re.compile(r"`agents/_shared/probes/([a-z0-9-]+)(?:\.md)?`")
_TEMPLATE = re.compile(r"`templates/([A-Za-z0-9_./-]+)`")
_STANDARD = re.compile(r"`standards/([A-Za-z0-9_./-]+)`")
_SHARED = re.compile(r"`(?:agents/)?_shared/([A-Z][A-Z_0-9]+\.md)`|`(AGENT_RULES\.md|AGENT_CONTRACT\.md|REFUSAL_CODES\.md|SKILL_MAP\.md)`")

SKILL_DOMAINS = {
    "admin", "apex", "lwc", "flow", "omnistudio", "agentforce",
    "security", "integration", "data", "devops", "architect",
}


def extract_dependencies(body: str, root: Path) -> dict:
    """Walk the AGENT.md body + return a normalized dependencies dict."""
    probes: set[str] = set()
    skills: set[str] = set()
    shared: set[str] = set()
    templates: set[str] = set()
    decision_trees: set[str] = set()

    for m in _PROBE.finditer(body):
        name = m.group(1)
        if not name.endswith(".md"):
            name = f"{name}.md"
        candidate = root / "agents" / "_shared" / "probes" / name
        if candidate.exists():
            probes.add(name)

    for m in _SKILL_BACKTICK.finditer(body):
        domain, slug = m.group(1), m.group(2)
        if domain not in SKILL_DOMAINS:
            continue
        if (root / "skills" / domain / slug).exists():
            skills.add(f"{domain}/{slug}")

    for m in _SKILL_BARE.finditer(body):
        domain, slug = m.group(1), m.group(2)
        if domain not in SKILL_DOMAINS:
            continue
        if (root / "skills" / domain / slug).exists():
            skills.add(f"{domain}/{slug}")

    for m in _TEMPLATE.finditer(body):
        rel = m.group(1)
        if (root / "templates" / rel).exists():
            templates.add(rel)

    for m in _STANDARD.finditer(body):
        rel = m.group(1)
        if rel.startswith("decision-trees/"):
            name = rel.split("/", 1)[1]
            if (root / "standards" / "decision-trees" / name).exists():
                decision_trees.add(name)

    for m in _SHARED.finditer(body):
        name = m.group(1) or m.group(2)
        if not name:
            continue
        # Shared docs live either at repo root or under agents/_shared/.
        if (root / name).exists() or (root / "agents" / "_shared" / name).exists():
            shared.add(name)

    result = {}
    if probes:
        result["probes"] = sorted(probes)
    if skills:
        result["skills"] = sorted(skills)
    if shared:
        result["shared"] = sorted(shared)
    if templates:
        result["templates"] = sorted(templates)
    if decision_trees:
        result["decision_trees"] = sorted(decision_trees)
    return result


def render_dependencies_yaml(deps: dict, indent: int = 0) -> str:
    """Render a dependencies dict as YAML lines, suitable for insertion into frontmatter."""
    pad = " " * indent
    lines = [f"{pad}dependencies:"]
    for key in ("probes", "skills", "shared", "templates", "decision_trees"):
        if key not in deps:
            continue
        lines.append(f"{pad}  {key}:")
        for item in deps[key]:
            lines.append(f"{pad}    - {item}")
    return "\n".join(lines)


def process_agent(path: Path, force: bool, dry_run: bool) -> tuple[str, dict]:
    """Update one AGENT.md. Returns (status, deps) tuple where status is one of
    'skipped-already-has-block', 'skipped-no-deps', 'updated', 'would-update'.
    """
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not m:
        return "skipped-no-frontmatter", {}

    frontmatter_block, body = m.group(1), m.group(2)

    if "\ndependencies:" in f"\n{frontmatter_block}\n" and not force:
        return "skipped-already-has-block", {}

    deps = extract_dependencies(body, ROOT)
    if not deps:
        return "skipped-no-deps", {}

    if force:
        # Remove any existing dependencies block
        new_frontmatter = re.sub(
            r"\ndependencies:\n(?:  [A-Za-z_]+:\n(?:    - .*\n)+)+",
            "\n",
            f"\n{frontmatter_block}\n",
        ).strip("\n")
    else:
        new_frontmatter = frontmatter_block

    deps_yaml = render_dependencies_yaml(deps, indent=0)
    new_frontmatter = new_frontmatter.rstrip() + "\n" + deps_yaml
    new_text = f"---\n{new_frontmatter}\n---\n{body}"

    if dry_run:
        return "would-update", deps
    path.write_text(new_text, encoding="utf-8")
    return "updated", deps


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate AGENT.md files to declare an explicit dependencies block.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print what would change without writing.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing dependencies block.")
    parser.add_argument("--agent", help="Process a single agent by id (kebab-case folder name).")
    args = parser.parse_args()

    if args.agent:
        agent_paths = [AGENTS_DIR / args.agent / "AGENT.md"]
        if not agent_paths[0].exists():
            print(f"No AGENT.md at {agent_paths[0]}", file=sys.stderr)
            return 1
    else:
        agent_paths = sorted(AGENTS_DIR.glob("*/AGENT.md"))

    totals = {"updated": 0, "would-update": 0, "skipped-already-has-block": 0, "skipped-no-deps": 0, "skipped-no-frontmatter": 0}
    for path in agent_paths:
        status, deps = process_agent(path, force=args.force, dry_run=args.dry_run)
        totals[status] = totals.get(status, 0) + 1
        if status in {"updated", "would-update"}:
            counts = " ".join(f"{k}={len(v)}" for k, v in deps.items())
            verb = "Would update" if args.dry_run else "Updated"
            print(f"{verb} {path.parent.name}: {counts}")

    print("\nSummary:")
    for k, v in totals.items():
        if v:
            print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
