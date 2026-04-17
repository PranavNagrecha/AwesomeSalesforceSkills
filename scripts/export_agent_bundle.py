#!/usr/bin/env python3
"""
export_agent_bundle.py — Per-agent bundle exporter (Wave 8)

Produces a self-contained, installable copy of a single agent plus every
file it declares in its frontmatter `dependencies` block. The result drops
into another project's `.cursor/agents/`, `.claude/agents/`, or equivalent
without any ambient `agents/_shared/` infrastructure.

This addresses the Cursor-in-Excelsior incident where a hand-copied
AGENT.md lost its probe recipe and the consuming AI had to improvise
SOQL — which is how `PermissionSetGroupAssignment` (a nonexistent object)
got invented.

Usage:
  python3 scripts/export_agent_bundle.py --agent user-access-diff
  python3 scripts/export_agent_bundle.py --agent user-access-diff --out ./my-bundle
  python3 scripts/export_agent_bundle.py --agent user-access-diff --rewrite-paths
  python3 scripts/export_agent_bundle.py --all-runtime
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = REPO_ROOT / "agents"
SKILLS_DIR = REPO_ROOT / "skills"
TEMPLATES_DIR = REPO_ROOT / "templates"
STANDARDS_DIR = REPO_ROOT / "standards"
SHARED_DIR = AGENTS_DIR / "_shared"
PROBES_DIR = SHARED_DIR / "probes"
DEFAULT_OUTPUT = REPO_ROOT / "exports" / "agent-bundles"


# ── Frontmatter parsing ──────────────────────────────────────────────────────

def parse_frontmatter(path: Path) -> tuple[dict, str, str]:
    """Return (frontmatter_dict, frontmatter_raw_text, body_text)."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not m:
        return {}, "", text
    raw = m.group(1)
    body = m.group(2)

    # Minimal YAML parser — same shape as export_skills.py.
    meta: dict = {}
    current_key: str | None = None
    current_list: list | None = None
    current_sub_dict: dict | None = None

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Nested list item under a sub-dict: "    - value"
        if line.startswith("    - ") and current_sub_dict is not None and current_key is not None:
            current_sub_dict.setdefault(current_key, []).append(line[6:].strip().strip('"'))
            continue

        # Flat list item: "  - value"
        if line.startswith("  - ") and current_list is not None:
            current_list.append(line[4:].strip().strip('"'))
            continue

        # Sub-dict key: "  subkey:"
        if line.startswith("  ") and ":" in line and not line.startswith("    ") and current_sub_dict is not None:
            key, _, rest = line.strip().partition(":")
            current_key = key.strip()
            rest = rest.strip()
            if rest:
                current_sub_dict[current_key] = rest.strip('"')
                current_key = None
            else:
                current_sub_dict[current_key] = []  # awaiting list items
            continue

        # Top-level key.
        if ":" in line and not line.startswith(" "):
            key, _, rest = line.partition(":")
            key = key.strip()
            rest = rest.strip()
            if not rest:
                # Could be a list (next lines start with "  -") or a dict (next lines indent deeper).
                # We distinguish when we peek the next line — but stream-parsing requires a heuristic.
                # Mark both possibilities open.
                meta[key] = []  # assume list; overwrite to dict if we find sub-keys
                current_key = key
                current_list = meta[key]
                current_sub_dict = None
            else:
                meta[key] = rest.strip('"')
                current_key = None
                current_list = None
                current_sub_dict = None
            continue

        # Sub-key detection: indented "  key:" following a top-level "key:" with empty value.
        if line.startswith("  ") and ":" in line and current_key is not None and isinstance(meta.get(current_key), list) and not meta[current_key]:
            # Promote from list to dict.
            meta[current_key] = {}
            current_sub_dict = meta[current_key]
            sub_key, _, sub_rest = line.strip().partition(":")
            sub_key = sub_key.strip()
            sub_rest = sub_rest.strip()
            if sub_rest:
                current_sub_dict[sub_key] = sub_rest.strip('"')
                current_key = sub_key  # but sub_rest consumed; null-out
            else:
                current_sub_dict[sub_key] = []
                current_key = sub_key
            current_list = None
            continue

    return meta, raw, body


# ── Bundle assembly ──────────────────────────────────────────────────────────

def bundle_paths_for(agent_id: str, deps: dict) -> list[tuple[Path, str]]:
    """Return (source_path, bundle_relative_path) tuples for all dependency files."""
    out: list[tuple[Path, str]] = []

    # The AGENT.md itself.
    out.append((AGENTS_DIR / agent_id / "AGENT.md", "AGENT.md"))

    # Probes.
    for name in deps.get("probes", []):
        src = PROBES_DIR / name
        if src.exists():
            out.append((src, f"probes/{name}"))

    # Skills.
    for skill_id in deps.get("skills", []):
        domain, slug = skill_id.split("/", 1)
        src_dir = SKILLS_DIR / domain / slug
        if not src_dir.exists():
            continue
        for file in src_dir.rglob("*"):
            if file.is_file():
                rel = file.relative_to(src_dir).as_posix()
                out.append((file, f"skills/{domain}/{slug}/{rel}"))

    # Shared root-level docs.
    for name in deps.get("shared", []):
        # Some live at repo root (AGENT_RULES.md), others under _shared/ (AGENT_CONTRACT.md).
        candidates = [REPO_ROOT / name, SHARED_DIR / name]
        for cand in candidates:
            if cand.exists():
                out.append((cand, f"shared/{name}"))
                break

    # Output schemas — every runtime agent conforms to these, and the
    # AGENT.md references them. Always bundle.
    for schema_name in ("output-envelope.schema.json", "observation.schema.json",
                         "citation.schema.json", "agent-frontmatter.schema.json"):
        src = SHARED_DIR / "schemas" / schema_name
        if src.exists():
            out.append((src, f"shared/schemas/{schema_name}"))

    # Wave 10: always bundle the Deliverable Contract + emit_deliverable helper.
    # Every runtime agent depends on both, regardless of whether the frontmatter
    # `dependencies` block explicitly lists them.
    wave10_contract = SHARED_DIR / "DELIVERABLE_CONTRACT.md"
    if wave10_contract.exists():
        out.append((wave10_contract, "shared/DELIVERABLE_CONTRACT.md"))
    wave10_helper = SHARED_DIR / "lib" / "emit_deliverable.md"
    if wave10_helper.exists():
        out.append((wave10_helper, "shared/lib/emit_deliverable.md"))

    # Wave 11: bundle every commands/<alias>.md that links back to this agent.
    # A single agent may have multiple aliases (e.g. automation-migration-router
    # has /migrate-workflow-pb, /migrate-wfr-to-flow, /migrate-pb-to-flow).
    # We ship them in EVERY supported target-specific location so the bundle
    # drop-in works regardless of which tool the consumer uses.
    commands_dir = REPO_ROOT / "commands"
    if commands_dir.exists():
        wrap_pat = re.compile(rf"agents/{re.escape(agent_id)}/AGENT\.md")
        for cmd_md in sorted(commands_dir.glob("*.md")):
            try:
                body = cmd_md.read_text(encoding="utf-8")
            except OSError:
                continue
            if not wrap_pat.search(body):
                continue
            # Ship into every slash-command-supporting target's convention.
            # The bundle consumer drops the bundle root into their project;
            # whichever subdir their tool reads, the command is there.
            for target_subdir in (
                ".cursor/commands",
                ".claude/commands",
                ".windsurf/workflows",
                ".augment/commands",
                "codex-prompts",
            ):
                out.append((cmd_md, f"{target_subdir}/{cmd_md.name}"))

    # Templates.
    for rel in deps.get("templates", []):
        src = TEMPLATES_DIR / rel
        if src.exists():
            out.append((src, f"templates/{rel}"))

    # Decision trees.
    for name in deps.get("decision_trees", []):
        src = STANDARDS_DIR / "decision-trees" / name
        if src.exists():
            out.append((src, f"standards/decision-trees/{name}"))

    return out


# ── Path rewriting (bundle-relative mode) ────────────────────────────────────

_REWRITES = [
    # Probe citations: `agents/_shared/probes/foo.md` → `./probes/foo.md`
    (re.compile(r"agents/_shared/probes/([a-z0-9-]+(?:\.md)?)"), r"./probes/\1"),
    # Wave 10 helper: `agents/_shared/lib/emit_deliverable.md` → `./shared/lib/emit_deliverable.md`
    (re.compile(r"agents/_shared/lib/([a-z0-9_-]+\.md)"), r"./shared/lib/\1"),
    # Schema references: `agents/_shared/schemas/foo.json` → `./shared/schemas/foo.json`
    (re.compile(r"agents/_shared/schemas/([a-z0-9-]+\.schema\.json)"), r"./shared/schemas/\1"),
    # Other shared docs under _shared/: `agents/_shared/FOO.md` → `./shared/FOO.md`
    (re.compile(r"agents/_shared/([A-Z][A-Z_0-9]+\.md)"), r"./shared/\1"),
    # Root-level shared docs: `AGENT_RULES.md` (only when backticked bare) → `./shared/AGENT_RULES.md`
    (re.compile(r"`AGENT_RULES\.md`"), r"`./shared/AGENT_RULES.md`"),
    # Skill citations: `skills/admin/user-management` → `./skills/admin/user-management`
    (re.compile(r"`skills/([a-z0-9-]+)/([a-z0-9-]+)((?:/[A-Za-z0-9_./-]*)?)`"), r"`./skills/\1/\2\3`"),
    # Template citations: `templates/apex/TriggerHandler.cls` → `./templates/apex/TriggerHandler.cls`
    (re.compile(r"`templates/([A-Za-z0-9_./-]+)`"), r"`./templates/\1`"),
    # Decision tree citations.
    (re.compile(r"`standards/decision-trees/([a-z0-9-]+\.md)`"), r"`./standards/decision-trees/\1`"),
]


def rewrite_agent_md(text: str) -> str:
    """Rewrite repo-absolute paths to bundle-relative form."""
    out = text
    for pattern, replacement in _REWRITES:
        out = pattern.sub(replacement, out)
    # Flip dependency_path_mode in frontmatter.
    if "dependency_path_mode:" in out:
        out = re.sub(r"dependency_path_mode:\s*repo-absolute", "dependency_path_mode: bundle-relative", out)
    else:
        # Inject into frontmatter.
        out = re.sub(
            r"(\nupdated:\s*\S+\n)",
            r"\1dependency_path_mode: bundle-relative\n",
            out,
            count=1,
        )
    return out


# ── Bundle emission ──────────────────────────────────────────────────────────

def write_install_doc(agent_id: str, deps: dict, output_dir: Path) -> None:
    """Write a short INSTALL.md explaining how to drop the bundle into a project."""
    content = f"""# Install — {agent_id} bundle

This bundle was generated by `scripts/export_agent_bundle.py` from
AwesomeSalesforceSkills. It contains the agent's `AGENT.md` plus every file
it declares in its frontmatter `dependencies` block. The agent can run
standalone in any project that supports markdown-based agents.

## Drop-in locations

| Tool / client | Location |
|---|---|
| Claude Code | `.claude/agents/{agent_id}/` |
| Cursor | `.cursor/agents/{agent_id}/` |
| Any MCP client | expose via a local MCP server or direct AGENT.md read |
| Raw LLM | paste `AGENT.md` as system prompt; reference `probes/`, `skills/`, etc. as needed |

## What's in the bundle

```
{agent_id}/
├── AGENT.md                           ← the agent (paths rewritten to bundle-relative)
├── probes/                            ← probe recipes (SOQL + post-processing)
├── skills/                            ← every skill cited in Mandatory Reads
├── shared/                            ← AGENT_CONTRACT, REFUSAL_CODES, etc.
├── templates/                         ← referenced canonical building blocks (if any)
├── standards/decision-trees/          ← routing logic (if any)
└── INSTALL.md
```

## Why a bundle and not "just copy AGENT.md"

An AGENT.md by itself is ~8 sections of instructions. But the instructions
reference probes, skills, shared docs, templates, and decision trees.
Without those files, any AI executing the agent has to improvise — and in
one documented incident that produced a hallucinated Salesforce object
name (`PermissionSetGroupAssignment`, which doesn't exist). The bundle
ships everything the agent needs, with paths rewritten to resolve inside
the bundle root.

## Dependencies declared by this agent

"""
    for key in ("probes", "skills", "shared", "templates", "decision_trees"):
        items = deps.get(key, [])
        if not items:
            continue
        content += f"**{key}:**\n"
        for it in items:
            content += f"- `{it}`\n"
        content += "\n"

    content += """## Updating

Regenerate from the source repo:
```bash
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
cd AwesomeSalesforceSkills
python3 scripts/export_agent_bundle.py --agent """ + agent_id + """ --rewrite-paths
```

## See also

- Full repo: https://github.com/PranavNagrecha/AwesomeSalesforceSkills
- Parity contract: `docs/multi-ai-parity.md`
- Single-agent install guide: `docs/installing-single-agents.md`
"""
    (output_dir / "INSTALL.md").write_text(content, encoding="utf-8")


def export_bundle(agent_id: str, output_root: Path, rewrite_paths: bool) -> Path:
    """Produce a self-contained bundle for one agent. Returns the bundle root."""
    agent_md_path = AGENTS_DIR / agent_id / "AGENT.md"
    if not agent_md_path.exists():
        raise SystemExit(f"No AGENT.md at {agent_md_path}")

    meta, _, _ = parse_frontmatter(agent_md_path)
    deps = meta.get("dependencies") or {}
    if not deps or not isinstance(deps, dict):
        print(f"WARN: agent '{agent_id}' has no `dependencies` block — bundle will "
              "contain only the AGENT.md. Run "
              "`python3 scripts/migrate_agent_dependencies.py --agent "
              f"{agent_id}` first to populate it.")
        deps = {}

    bundle_root = output_root / agent_id
    if bundle_root.exists():
        shutil.rmtree(bundle_root)
    bundle_root.mkdir(parents=True)

    # Copy every dependency file.
    file_count = 0
    for src, rel in bundle_paths_for(agent_id, deps):
        dst = bundle_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        file_count += 1

    # Rewrite AGENT.md paths if requested.
    if rewrite_paths:
        agent_md_dst = bundle_root / "AGENT.md"
        original = agent_md_dst.read_text(encoding="utf-8")
        agent_md_dst.write_text(rewrite_agent_md(original), encoding="utf-8")

    write_install_doc(agent_id, deps, bundle_root)

    print(f"✓ {agent_id}: {file_count} file(s) bundled → {bundle_root.relative_to(REPO_ROOT) if bundle_root.is_relative_to(REPO_ROOT) else bundle_root}")
    if rewrite_paths:
        print(f"  paths rewritten bundle-relative")
    return bundle_root


def list_runtime_agents() -> list[str]:
    out = []
    for agent_md in sorted(AGENTS_DIR.glob("*/AGENT.md")):
        meta, _, _ = parse_frontmatter(agent_md)
        if meta.get("class") == "runtime" and meta.get("status") != "deprecated":
            out.append(agent_md.parent.name)
    return out


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bundle one agent (or all runtime agents) with its dependencies.",
    )
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--agent", help="Agent id to bundle (e.g. 'user-access-diff').")
    selector.add_argument("--all-runtime", action="store_true",
                          help="Bundle every non-deprecated runtime agent.")
    parser.add_argument("--out", default=str(DEFAULT_OUTPUT),
                        help=f"Output directory (default: {DEFAULT_OUTPUT.relative_to(REPO_ROOT)})")
    parser.add_argument("--rewrite-paths", action="store_true",
                        help="Rewrite AGENT.md citations to bundle-relative form. "
                             "Set dependency_path_mode=bundle-relative. Recommended "
                             "for drop-in installs; skip if the bundle will be consumed "
                             "by tooling that knows how to resolve agents/_shared/* paths.")
    args = parser.parse_args()

    output_root = Path(args.out).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    if args.agent:
        export_bundle(args.agent, output_root, rewrite_paths=args.rewrite_paths)
    else:
        agents = list_runtime_agents()
        print(f"Bundling {len(agents)} runtime agent(s) into {output_root.relative_to(REPO_ROOT) if output_root.is_relative_to(REPO_ROOT) else output_root}\n")
        for a in agents:
            export_bundle(a, output_root, rewrite_paths=args.rewrite_paths)

    return 0


if __name__ == "__main__":
    sys.exit(main())
