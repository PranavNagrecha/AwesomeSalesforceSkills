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
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
EXPORTS_DIR = REPO_ROOT / "exports"
REGISTRY_FILE = REPO_ROOT / "registry" / "skills.json"
MANIFEST_FILE = REPO_ROOT / "registry" / "export_manifest.json"

# First-class targets (Wave 2): Claude, Cursor, MCP must contain the same
# SET of skill IDs on every export. Second-class targets (Windsurf, Aider,
# Augment) may be a documented subset — see docs/multi-ai-parity.md (Wave 6).
PLATFORMS = ["claude", "cursor", "mcp", "windsurf", "aider", "augment"]
FIRST_CLASS_TARGETS = {"claude", "cursor", "mcp"}


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


# ── First-class targets: Claude + MCP ────────────────────────────────────────

def _write_claude_skill(skill: dict, output_skill_dir: Path) -> None:
    """Write a skill into the Claude target layout.

    Claude Code reads ``skills/<domain>/<slug>/SKILL.md`` natively. We emit
    the canonical layout unchanged (SKILL.md + references/ + templates/) so
    any Claude-compatible client can mount ``exports/claude/skills/`` as-is.
    Deterministic: sorted references/templates, fixed line endings.
    """
    output_skill_dir.mkdir(parents=True, exist_ok=True)

    # Reassemble SKILL.md: YAML frontmatter + body. We don't re-parse-then-
    # re-emit the frontmatter (that would risk key reordering); instead we
    # copy the source file verbatim. Determinism is guaranteed by the source.
    source_path = Path(skill["path"]) / "SKILL.md"
    (output_skill_dir / "SKILL.md").write_text(
        source_path.read_text(encoding="utf-8"), encoding="utf-8"
    )

    # references/ — emit the four canonical files in alphabetical order.
    refs_out = output_skill_dir / "references"
    refs_out.mkdir(exist_ok=True)
    for name in sorted(skill.get("references", {}).keys()):
        (refs_out / name).write_text(skill["references"][name], encoding="utf-8")
    # Also emit llm-anti-patterns.md if it exists on disk (not loaded by
    # load_all_skills today but part of the canonical package).
    src_refs = Path(skill["path"]) / "references"
    if (src_refs / "llm-anti-patterns.md").exists() and not (refs_out / "llm-anti-patterns.md").exists():
        (refs_out / "llm-anti-patterns.md").write_text(
            (src_refs / "llm-anti-patterns.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    # templates/ — copy every file if present (Claude respects the canonical
    # layout, including non-markdown templates like .cls / .js).
    tpl_out = output_skill_dir / "templates"
    src_tpl = Path(skill["path"]) / "templates"
    if src_tpl.exists():
        tpl_out.mkdir(exist_ok=True)
        for f in sorted(src_tpl.iterdir()):
            if f.is_file():
                (tpl_out / f.name).write_bytes(f.read_bytes())


def export_claude(skills: list[dict], output_dir: Path) -> int:
    """Claude target: canonical SfSkills layout under ``exports/claude/skills/``.

    Matches the source tree one-to-one. Claude Code, any MCP client, and
    anything else that reads ``SKILL.md`` natively works against this bundle
    without transformation.
    """
    for skill in skills:
        _write_claude_skill(
            skill,
            output_dir / "skills" / skill["domain"] / skill["skill_name"],
        )

    # INDEX.md with stable ordering for diff legibility.
    lines = ["# SfSkills — Claude Skills\n\n"]
    lines.append(
        "Auto-generated. Run `python3 scripts/export_skills.py --target claude`.\n\n"
    )
    for skill in sorted(skills, key=lambda s: (s["domain"], s["skill_name"])):
        lines.append(f"- `skills/{skill['domain']}/{skill['skill_name']}/SKILL.md` — {skill['name']}\n")
    (output_dir / "INDEX.md").write_text("".join(lines), encoding="utf-8")
    return len(skills)


def export_mcp(skills: list[dict], output_dir: Path) -> int:
    """MCP target: canonical skills/ tree plus the registry so the SfSkills
    MCP server (or any MCP client reading ``registry/skills.json``) can run
    against this bundle standalone. Layout mirrors Claude so the set-parity
    test compares skill IDs directly."""
    # Same skill tree as Claude — byte-identical skill bodies, so set parity
    # is trivially preserved.
    for skill in skills:
        _write_claude_skill(
            skill,
            output_dir / "skills" / skill["domain"] / skill["skill_name"],
        )

    # Include the compiled registry so the MCP server can serve ``get_skill``
    # and ``search_skill`` without rebuilding state from the raw tree.
    if REGISTRY_FILE.exists():
        (output_dir / "registry").mkdir(exist_ok=True)
        shutil.copy2(REGISTRY_FILE, output_dir / "registry" / "skills.json")

    lines = ["# SfSkills — MCP Bundle\n\n"]
    lines.append(
        "Auto-generated. Run `python3 scripts/export_skills.py --target mcp`.\n\n"
        "To serve this bundle: `python3 -m sfskills_mcp` with this directory "
        "on PYTHONPATH.\n\n"
    )
    for skill in sorted(skills, key=lambda s: (s["domain"], s["skill_name"])):
        lines.append(f"- `skills/{skill['domain']}/{skill['skill_name']}/SKILL.md` — {skill['name']}\n")
    (output_dir / "INDEX.md").write_text("".join(lines), encoding="utf-8")
    return len(skills)


# ── Manifest (determinism + set-parity contract) ──────────────────────────────

def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _hash_target_tree(target_dir: Path) -> tuple[str, dict[str, str]]:
    """Compute (overall_hash, per-skill hashes) for a target's output.

    A skill's hash is sha256 of the concatenated bytes of every file under
    its ``skills/<domain>/<slug>/`` subtree (or the equivalent for targets
    that flatten the tree like Cursor). Overall hash = sha256 of
    ``"<skill_id>:<skill_hash>\\n"`` for each skill in sorted order.
    """
    per_skill: dict[str, str] = {}

    # Claude/MCP layout: exports/<target>/skills/<domain>/<slug>/...
    skills_root = target_dir / "skills"
    if skills_root.is_dir():
        for domain_dir in sorted(skills_root.iterdir()):
            if not domain_dir.is_dir():
                continue
            for skill_dir in sorted(domain_dir.iterdir()):
                if not skill_dir.is_dir():
                    continue
                skill_id = f"{domain_dir.name}/{skill_dir.name}"
                h = hashlib.sha256()
                for file_path in sorted(skill_dir.rglob("*")):
                    if file_path.is_file():
                        h.update(file_path.relative_to(skill_dir).as_posix().encode("utf-8"))
                        h.update(b"\0")
                        h.update(file_path.read_bytes())
                        h.update(b"\0")
                per_skill[skill_id] = h.hexdigest()

    # Cursor layout: exports/cursor/.cursor/rules/<domain>-<slug>.mdc
    cursor_rules = target_dir / ".cursor" / "rules"
    if cursor_rules.is_dir():
        for mdc in sorted(cursor_rules.glob("*.mdc")):
            # "<domain>-<slug>.mdc" — split on first hyphen-that-belongs-to-
            # domain-separator. We know valid domains, so match against them.
            stem = mdc.stem
            for domain in sorted(["admin", "apex", "lwc", "flow", "omnistudio",
                                  "agentforce", "security", "integration",
                                  "data", "devops", "architect"], key=len, reverse=True):
                if stem.startswith(f"{domain}-"):
                    slug = stem[len(domain) + 1:]
                    skill_id = f"{domain}/{slug}"
                    per_skill[skill_id] = _sha256_file(mdc)
                    break

    # Windsurf: exports/windsurf/.windsurf/rules/<domain>-<slug>.md
    windsurf_rules = target_dir / ".windsurf" / "rules"
    if windsurf_rules.is_dir():
        for md in sorted(windsurf_rules.glob("*.md")):
            stem = md.stem
            for domain in sorted(["admin", "apex", "lwc", "flow", "omnistudio",
                                  "agentforce", "security", "integration",
                                  "data", "devops", "architect"], key=len, reverse=True):
                if stem.startswith(f"{domain}-"):
                    slug = stem[len(domain) + 1:]
                    skill_id = f"{domain}/{slug}"
                    per_skill[skill_id] = _sha256_file(md)
                    break

    # Augment: exports/augment/.augment/rules/<domain>-<slug>.md
    augment_rules = target_dir / ".augment" / "rules"
    if augment_rules.is_dir():
        for md in sorted(augment_rules.glob("*.md")):
            stem = md.stem
            for domain in sorted(["admin", "apex", "lwc", "flow", "omnistudio",
                                  "agentforce", "security", "integration",
                                  "data", "devops", "architect"], key=len, reverse=True):
                if stem.startswith(f"{domain}-"):
                    slug = stem[len(domain) + 1:]
                    skill_id = f"{domain}/{slug}"
                    per_skill[skill_id] = _sha256_file(md)
                    break

    # Aider: single CONVENTIONS.md — one entry keyed by literal "CONVENTIONS.md"
    # since skills aren't individually addressable in this target.
    aider_conv = target_dir / "CONVENTIONS.md"
    if aider_conv.exists():
        per_skill["CONVENTIONS.md"] = _sha256_file(aider_conv)

    # Overall = sha256 of sorted "id:hash" pairs. Deterministic across runs.
    overall = hashlib.sha256()
    for skill_id in sorted(per_skill.keys()):
        overall.update(f"{skill_id}:{per_skill[skill_id]}\n".encode("utf-8"))
    return overall.hexdigest(), per_skill


def _build_manifest(output_root: Path, targets: list[str]) -> dict:
    """Build the full manifest dict by hashing each target's tree."""
    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "first_class_targets": sorted(FIRST_CLASS_TARGETS),
        "targets": {},
    }
    for target in targets:
        target_dir = output_root / target
        if not target_dir.exists():
            continue
        overall, per_skill = _hash_target_tree(target_dir)
        manifest["targets"][target] = {
            "overall_hash": f"sha256:{overall}",
            "skill_count": len(per_skill),
            "skills": {k: f"sha256:{v}" for k, v in sorted(per_skill.items())},
        }
    return manifest


def _write_manifest(manifest: dict, path: Path = MANIFEST_FILE) -> None:
    """Write manifest with stable key order so git diffs are meaningful."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _manifest_diff(current: dict, committed: dict) -> list[str]:
    """Return human-readable diffs. Empty list = identical.

    Ignores ``generated_at`` — it's expected to change every run. Everything
    else must match byte-for-byte.
    """
    diffs: list[str] = []
    if current.get("schema_version") != committed.get("schema_version"):
        diffs.append(
            f"schema_version: {committed.get('schema_version')!r} -> {current.get('schema_version')!r}"
        )
    current_targets = current.get("targets", {})
    committed_targets = committed.get("targets", {})
    all_names = set(current_targets) | set(committed_targets)
    for name in sorted(all_names):
        if name not in committed_targets:
            diffs.append(f"target {name!r} added")
            continue
        if name not in current_targets:
            diffs.append(f"target {name!r} removed")
            continue
        cur = current_targets[name]
        com = committed_targets[name]
        if cur.get("overall_hash") != com.get("overall_hash"):
            diffs.append(
                f"target {name!r}: overall_hash changed "
                f"({com.get('overall_hash')} -> {cur.get('overall_hash')})"
            )
        cur_skills = cur.get("skills", {})
        com_skills = com.get("skills", {})
        added = sorted(set(cur_skills) - set(com_skills))
        removed = sorted(set(com_skills) - set(cur_skills))
        changed = sorted(
            k for k in set(cur_skills) & set(com_skills)
            if cur_skills[k] != com_skills[k]
        )
        if added:
            diffs.append(f"target {name!r}: +{len(added)} new skill(s): {added[:5]}{' ...' if len(added) > 5 else ''}")
        if removed:
            diffs.append(f"target {name!r}: -{len(removed)} removed skill(s): {removed[:5]}{' ...' if len(removed) > 5 else ''}")
        if changed:
            diffs.append(f"target {name!r}: {len(changed)} changed skill(s): {changed[:5]}{' ...' if len(changed) > 5 else ''}")
    return diffs


def assert_first_class_parity(manifest: dict) -> list[str]:
    """Assert Claude + Cursor + MCP have the same set of skill IDs.

    Wave 6 promotes this to a CI gate. Wave 2 exposes it as a helper the
    parity tests can import. Returns a list of violations — empty means OK.
    """
    targets = manifest.get("targets", {})
    # Claude & MCP use skill-id keys; Cursor uses the same keys because we
    # decode its filenames back to ``<domain>/<slug>`` in _hash_target_tree.
    claude_ids = set(targets.get("claude", {}).get("skills", {}))
    cursor_ids = set(targets.get("cursor", {}).get("skills", {}))
    mcp_ids = set(targets.get("mcp", {}).get("skills", {}))

    violations: list[str] = []
    if claude_ids and cursor_ids:
        diff = (claude_ids ^ cursor_ids)
        if diff:
            violations.append(
                f"set parity broken: claude XOR cursor = {sorted(diff)[:5]}{' ...' if len(diff) > 5 else ''}"
            )
    if claude_ids and mcp_ids:
        diff = (claude_ids ^ mcp_ids)
        if diff:
            violations.append(
                f"set parity broken: claude XOR mcp = {sorted(diff)[:5]}{' ...' if len(diff) > 5 else ''}"
            )
    if cursor_ids and mcp_ids:
        diff = (cursor_ids ^ mcp_ids)
        if diff:
            violations.append(
                f"set parity broken: cursor XOR mcp = {sorted(diff)[:5]}{' ...' if len(diff) > 5 else ''}"
            )
    return violations


# ── Main ──────────────────────────────────────────────────────────────────────

EXPORTERS = {
    "claude": export_claude,
    "cursor": export_cursor,
    "mcp": export_mcp,
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
  python3 scripts/export_skills.py --target cursor
  python3 scripts/export_skills.py --target aider --domain apex
  python3 scripts/export_skills.py --all
  python3 scripts/export_skills.py --target cursor --skill apex/trigger-framework
  python3 scripts/export_skills.py --all --manifest   # regenerate registry/export_manifest.json
  python3 scripts/export_skills.py --check             # verify tree matches committed manifest; exit 1 on drift
        """,
    )
    # --target is the Wave-2 canonical name. --platform stays as a back-compat
    # alias so old scripts keep working.
    target_group = parser.add_mutually_exclusive_group()
    target_group.add_argument(
        "--target",
        choices=PLATFORMS,
        help="Target platform to export for (canonical name)",
    )
    target_group.add_argument(
        "--platform",
        choices=PLATFORMS,
        help="Alias for --target (kept for back-compat with Wave-0 scripts)",
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
    parser.add_argument(
        "--manifest",
        action="store_true",
        help="After exporting, write registry/export_manifest.json with per-"
             "target content hashes. Use this from CI or when updating the "
             "parity baseline.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Non-destructive. Rebuild every target in a scratch dir, hash, "
             "and diff against registry/export_manifest.json. Exits 0 if the "
             "current tree would produce an identical manifest; exits 1 with "
             "a human-readable diff on mismatch. This is the Wave-6 parity "
             "gate's local mirror.",
    )

    args = parser.parse_args()

    # --check runs without doing any user-visible exports; it builds in a
    # throwaway temp dir and compares against the committed manifest.
    if args.check:
        return _run_check(args)

    # Resolve --target (canonical) / --platform (alias).
    selected = args.target or args.platform
    if not selected and not args.all:
        parser.error("Specify --target <name> or --all (or use the --platform alias)")

    output_root = Path(args.output)

    print(f"Loading skills from {SKILLS_DIR}...")
    skills = load_all_skills(
        domain_filter=args.domain,
        skill_filter=args.skill,
    )

    if not skills:
        print("ERROR: No skills found matching the filter.")
        sys.exit(1)

    print(f"  Found {len(skills)} skills")

    platforms_to_run = PLATFORMS if args.all else [selected]

    results = {}
    for platform in platforms_to_run:
        platform_dir = output_root / platform
        # Wipe the prior target output so this run is idempotent and
        # deterministic. Otherwise a stale file from a previous run could
        # contaminate the hash.
        if platform_dir.exists():
            shutil.rmtree(platform_dir)
        exporter = EXPORTERS[platform]
        print(f"\nExporting to {platform}...")
        count = exporter(skills, platform_dir)
        results[platform] = count
        print(f"  {count} skills exported → {platform_dir}")

    print("\n" + "=" * 50)
    print("EXPORT COMPLETE")
    print("=" * 50)
    for platform, count in results.items():
        print(f"  {platform:12} {count} skills → exports/{platform}/")

    if args.manifest:
        manifest = _build_manifest(output_root, platforms_to_run)
        _write_manifest(manifest)
        print(f"\nManifest written to {MANIFEST_FILE.relative_to(REPO_ROOT)}")
        parity_violations = assert_first_class_parity(manifest)
        if parity_violations:
            print("WARN: first-class parity violations (Claude/Cursor/MCP "
                  "must share skill IDs):")
            for v in parity_violations:
                print(f"  - {v}")

    print("\nInstallation instructions:")
    print("  Claude Code:  skills/ is the canonical source; or copy exports/claude/skills/ into your project")
    print("  MCP clients:  point at exports/mcp/ (includes registry/skills.json for standalone serving)")
    print("  Cursor:       copy exports/cursor/.cursor/ → your project root")
    print("  Aider:        copy exports/aider/CONVENTIONS.md → your project root")
    print("  Windsurf:     copy exports/windsurf/.windsurf/ → your project root")
    print("  Augment:      copy exports/augment/.augment/ → your project root")


def _run_check(args: argparse.Namespace) -> int:
    """Rebuild the full exports tree in a temp dir and diff against the
    committed manifest. Returns 0 on match, 1 on drift."""
    import tempfile

    if not MANIFEST_FILE.exists():
        print(f"ERROR: {MANIFEST_FILE.relative_to(REPO_ROOT)} does not exist — "
              "run `python3 scripts/export_skills.py --all --manifest` first.")
        return 1

    committed = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))

    print(f"Loading skills from {SKILLS_DIR}...")
    skills = load_all_skills()
    print(f"  Found {len(skills)} skills")

    with tempfile.TemporaryDirectory(prefix="sfskills-check-") as scratch:
        scratch_root = Path(scratch)
        for platform in PLATFORMS:
            platform_dir = scratch_root / platform
            EXPORTERS[platform](skills, platform_dir)
        current = _build_manifest(scratch_root, PLATFORMS)

    diffs = _manifest_diff(current, committed)
    parity_violations = assert_first_class_parity(current)

    if not diffs and not parity_violations:
        print(f"\n✓ export manifest matches {MANIFEST_FILE.relative_to(REPO_ROOT)}")
        return 0

    print(f"\n✖ export drift detected against {MANIFEST_FILE.relative_to(REPO_ROOT)}:")
    for d in diffs:
        print(f"  - {d}")
    if parity_violations:
        print("\n✖ first-class parity violations:")
        for v in parity_violations:
            print(f"  - {v}")
    print("\nTo update the baseline: "
          "python3 scripts/export_skills.py --all --manifest")
    return 1


if __name__ == "__main__":
    main()
