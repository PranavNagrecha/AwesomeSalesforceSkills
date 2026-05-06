#!/usr/bin/env python3
"""Scaffold a new skill package with all required files.

Usage:
    python3 scripts/new_skill.py <domain> <skill-name>

Example:
    python3 scripts/new_skill.py apex bulkification-patterns

After scaffolding, fill in every TODO in the created files, then run:
    python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name>
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ALLOWED_CATEGORIES = {
    "admin", "apex", "lwc", "flow", "omnistudio",
    "agentforce", "security", "integration", "data", "devops",
    "experience", "servicecloud", "architect",
}

# Pre-seeded official sources by domain — injected into well-architected.md on scaffold.
# Codex starts with real URLs, not a blank section.
DOMAIN_OFFICIAL_SOURCES: dict[str, list[str]] = {
    "apex": [
        "Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm",
        "Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm",
        "Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html",
    ],
    "lwc": [
        "LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html",
        "Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide",
        "LWC Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html",
    ],
    "admin": [
        "Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm",
        "Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm",
        "Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html",
    ],
    "flow": [
        "Flow Reference — https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5",
        "Flow Builder — https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5",
        "Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm",
    ],
    "integration": [
        "REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm",
        "Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html",
        "Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html",
    ],
    "security": [
        "Shield Platform Encryption Implementation Guide — https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm&type=5",
        "Secure Apex Classes — https://developer.salesforce.com/docs/platform/lwc/guide/apex-security",
        "Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5",
    ],
    "devops": [
        "Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm",
        "Salesforce CLI Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm",
        "Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm",
    ],
    "data": [
        "Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm",
        "Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm",
        "Data Loader Guide — https://help.salesforce.com/s/articleView?id=sf.data_loader.htm&type=5",
    ],
    "omnistudio": [
        "OmniStudio Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm",
        "OmniStudio Integration Procedures — https://help.salesforce.com/s/articleView?id=sf.os_integration_procedures.htm&type=5",
        "Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html",
    ],
    "agentforce": [
        "Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html",
        "Einstein Platform Services — https://developer.salesforce.com/docs/einstein/genai/guide/overview.html",
        "Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html",
    ],
    "experience": [
        "Experience Cloud Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.communities_dev.meta/communities_dev/communities_dev_intro.htm",
        "Experience Cloud Builder — https://help.salesforce.com/s/articleView?id=sf.community_builder_overview.htm&type=5",
        "Experience Cloud Guest User Security — https://help.salesforce.com/s/articleView?id=sf.networks_guest_access.htm&type=5",
        "Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5",
    ],
    "servicecloud": [
        "Service Cloud Overview — https://help.salesforce.com/s/articleView?id=sf.service_cloud_overview.htm&type=5",
        "Entitlements and Milestones — https://help.salesforce.com/s/articleView?id=sf.entitlements_overview.htm&type=5",
        "Omni-Channel Routing — https://help.salesforce.com/s/articleView?id=sf.omnichannel_intro.htm&type=5",
        "Salesforce Knowledge — https://help.salesforce.com/s/articleView?id=sf.knowledge_whatis.htm&type=5",
        "REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm",
    ],
}


def _list_runtime_agents() -> list[tuple[str, str]]:
    """Return [(agent_id, primary-output-blurb)] for every agent dir.

    Build-time and deprecated agents are filtered out. The primary-output
    blurb is read from the agent's AGENT.md frontmatter ``primary_output``
    or ``role`` field; falls back to the first paragraph of the body.
    """
    out: list[tuple[str, str]] = []
    agents_dir = ROOT / "agents"
    if not agents_dir.exists():
        return out
    for agent_dir in sorted(agents_dir.iterdir()):
        if not agent_dir.is_dir() or agent_dir.name == "_shared":
            continue
        agent_md = agent_dir / "AGENT.md"
        if not agent_md.exists():
            continue
        try:
            text = agent_md.read_text(encoding="utf-8")
        except OSError:
            continue
        if "deprecated: true" in text.lower() or "lifecycle: build-time" in text.lower():
            continue
        # Pull a short blurb. Look for `primary_output:` or first non-empty body line.
        m = re.search(r"^primary_output:\s*[\"']?([^\n\"']+)", text, re.MULTILINE)
        if not m:
            m = re.search(r"^role:\s*[\"']?([^\n\"']+)", text, re.MULTILINE)
        blurb = m.group(1).strip() if m else ""
        if not blurb:
            # First non-empty line after frontmatter
            after = text.split("---", 2)[-1] if text.startswith("---") else text
            for line in after.splitlines():
                s = line.strip()
                if s and not s.startswith("#"):
                    blurb = s[:80]
                    break
        out.append((agent_dir.name, blurb))
    return out


def _suggest_agents_for(domain: str) -> list[str]:
    """Cheap default mapping from skill domain → likely agents."""
    return {
        "admin": ["object-designer", "field-impact-analyzer", "audit-router"],
        "apex": ["apex-builder", "apex-refactorer", "code-reviewer"],
        "lwc": ["lwc-builder", "lwc-auditor"],
        "flow": ["flow-builder", "flow-analyzer"],
        "agentforce": ["agentforce-builder", "agentforce-action-reviewer"],
        "security": ["security-scanner", "audit-router"],
        "integration": ["integration-catalog-builder", "bulk-migration-planner"],
        "data": ["data-model-reviewer", "data-loader-pre-flight"],
        "devops": ["deployment-risk-scorer", "changeset-builder"],
        "architect": ["waf-assessor", "fit-gap-analyzer"],
        "omnistudio": [],  # no agent owns this domain yet
    }.get(domain, [])


def _prompt_agent_decision(
    domain: str, skill_name: str
) -> tuple[list[str], bool, str | None]:
    """Interactive prompt for the agent-wiring decision.

    Returns (agent_ids, runtime_orphan, orphan_reason). Exits on abort.
    """
    agents = _list_runtime_agents()
    suggested = _suggest_agents_for(domain)
    print("\n┌─ Agent wiring decision ─────────────────────────────────────────────┐")
    print("│  Every skill must record a decision: which run-time agent(s) cite   │")
    print("│  it, OR mark it as a deliberate runtime_orphan.                     │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    if suggested:
        print(f"\nSuggested agents for domain '{domain}':")
        for a in suggested:
            blurb = next((b for aid, b in agents if aid == a), "")
            print(f"  • {a:40s}  {blurb[:70]}")
    print("\nOptions:")
    print("  [1] Cite this skill from one or more run-time agents (recommended)")
    print("  [2] Mark as runtime_orphan (no agent owns this topic)")
    print("  [?] List all run-time agents")
    print("  [q] Abort scaffolding")
    while True:
        choice = input("\nChoice [1/2/?/q]: ").strip().lower()
        if choice in ("q", "quit", "abort"):
            raise SystemExit("Aborted.")
        if choice == "?":
            print("\nRun-time agents:")
            for aid, blurb in agents:
                print(f"  {aid:40s}  {blurb[:70]}")
            continue
        if choice == "1":
            raw = input(
                "\nAgent id(s), comma-separated "
                f"[default: {','.join(suggested) or 'none'}]: "
            ).strip()
            if not raw and suggested:
                raw = ",".join(suggested)
            ids = [a.strip() for a in raw.split(",") if a.strip()]
            if not ids:
                print("⚠  Empty list. Try again or pick option 2.")
                continue
            valid = {a for a, _ in agents}
            bad = [a for a in ids if a not in valid]
            if bad:
                print(f"⚠  Unknown agent(s): {', '.join(bad)}. Try again.")
                continue
            return ids, False, None
        if choice == "2":
            reason = input(
                "Reason this skill has no run-time agent owner "
                "(one sentence): "
            ).strip()
            if not reason:
                print("⚠  A reason is required. Try again.")
                continue
            return [], True, reason
        print("⚠  Invalid choice. Pick 1, 2, ?, or q.")


def _patch_agent_with_skill(agent_id: str, skill_id: str, description: str) -> None:
    """Run scripts/patch_agent_skill.py to add this skill to an agent."""
    import subprocess
    cmd = [
        sys.executable, str(ROOT / "scripts" / "patch_agent_skill.py"),
        agent_id, skill_id, "### Mandatory Reads", description,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        # Common fallback: the agent may use a different section heading
        for fallback in ("### Skills", "### Skills consulted", "*end*"):
            cmd2 = cmd[:-2] + [fallback, description]
            r2 = subprocess.run(cmd2, capture_output=True, text=True)
            if r2.returncode == 0:
                print(f"  ✔  wired into {agent_id} (under {fallback})")
                return
        raise SystemExit(
            f"✘ could not wire skill into {agent_id}.\n"
            f"   stdout: {r.stdout}\n   stderr: {r.stderr}\n"
            f"   Fix the agent's AGENT.md or pick a different agent and re-run."
        )
    print(f"  ✔  wired into {agent_id}")


def _add_orphan_marker(skill_md_path: Path, reason: str) -> None:
    """Insert `runtime_orphan: true` and `runtime_orphan_reason:` into frontmatter."""
    text = skill_md_path.read_text(encoding="utf-8")
    # Insert just before the closing `---` of the frontmatter
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise SystemExit(f"✘ could not find frontmatter in {skill_md_path}")
    fm = parts[1]
    inject = f"\nruntime_orphan: true\nruntime_orphan_reason: {json.dumps(reason)}\n"
    new_fm = fm.rstrip("\n") + inject
    skill_md_path.write_text(f"---{new_fm}---{parts[2]}", encoding="utf-8")


def _check_coverage(query: str, domain: str) -> bool:
    """Return True if search_knowledge.py reports has_coverage for this query."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "search_knowledge.py"), query, "--domain", domain, "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False
    try:
        payload = json.loads(result.stdout)
        return bool(payload.get("has_coverage", False))
    except Exception:
        return False


def _check_similarity_neighbours(skill_name: str, domain: str) -> list[tuple[str, float, str]]:
    """Build a stub fingerprint for the proposed skill and return its top-5
    neighbours in the existing corpus. Description is the slug-as-prose since
    we don't have a real description yet — coarse, but enough to catch the
    "you're about to scaffold a near-duplicate" case.

    Returns ``[(neighbour_skill_id, total_score, description), ...]``."""
    from pipelines.similarity import (
        SkillFingerprint,
        compute_similarity,
        fingerprint_corpus,
        load_threshold_from_config,
        normalize_tags,
        tokenize_triggers,
    )
    threshold, weights = load_threshold_from_config(ROOT)

    pseudo_description = skill_name.replace("-", " ").lower()
    pseudo = SkillFingerprint(
        skill_id=f"{domain}/{skill_name}",
        domain=domain,
        description=pseudo_description,
        tags=normalize_tags([]),
        trigger_words=tokenize_triggers([pseudo_description]),
        path=ROOT / "skills" / domain / skill_name / "SKILL.md",
    )

    corpus = fingerprint_corpus(ROOT)
    scored: list[tuple[str, float, str]] = []
    for other in corpus:
        if other.skill_id == pseudo.skill_id:
            continue
        score = compute_similarity(pseudo, other, weights)
        if score.total >= threshold:
            scored.append((other.skill_id, score.total, other.description))
    scored.sort(key=lambda t: t[1], reverse=True)
    return scored[:5]


def _scaffold_skill_md(template_path: Path, skill_name: str, domain: str) -> str:
    title = skill_name.replace("-", " ").title()
    today = date.today().isoformat()
    return (
        template_path.read_text(encoding="utf-8")
        .replace("{skill_name}", skill_name)
        .replace("{skill_name_title}", title)
        .replace("{domain}", domain)
        .replace("{today}", today)
    )


def _scaffold_examples_md(skill_name: str) -> str:
    title = skill_name.replace("-", " ").title()
    return f"""# Examples — {title}

## Example 1: TODO: Name the scenario

**Context:** TODO: describe the real-world situation

**Problem:** TODO: what goes wrong without this skill's guidance

**Solution:**

```apex
// TODO: paste a representative code example or configuration
```

**Why it works:** TODO: explain the key insight

---

## Example 2: TODO: Name the scenario

**Context:** TODO: describe the scenario

**Problem:** TODO: what goes wrong

**Solution:**

```apex
// TODO: example
```

**Why it works:** TODO: explanation

---

## Anti-Pattern: TODO: Name a common mistake

**What practitioners do:** TODO: describe the wrong approach

**What goes wrong:** TODO: explain the failure mode

**Correct approach:** TODO: describe the right way
"""


def _scaffold_gotchas_md(skill_name: str) -> str:
    title = skill_name.replace("-", " ").title()
    return f"""# Gotchas — {title}

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: TODO: Name

**What happens:** TODO: describe the unexpected behavior

**When it occurs:** TODO: describe the conditions that trigger it

**How to avoid:** TODO: describe the fix or prevention

---

## Gotcha 2: TODO: Name

**What happens:** TODO: describe the unexpected behavior

**When it occurs:** TODO: describe the conditions

**How to avoid:** TODO: fix or prevention

---

## Gotcha 3: TODO: Name

**What happens:** TODO: describe the unexpected behavior

**When it occurs:** TODO: describe the conditions

**How to avoid:** TODO: fix or prevention
"""


def _scaffold_well_architected_md(skill_name: str, domain: str) -> str:
    title = skill_name.replace("-", " ").title()
    sources = DOMAIN_OFFICIAL_SOURCES.get(domain, [
        "Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html",
    ])
    source_lines = "\n".join(f"- {s}" for s in sources)
    return f"""# Well-Architected Notes — {title}

## Relevant Pillars

TODO: Identify which Well-Architected pillars apply and why.

- **Security** — TODO: explain if/how security applies to this skill
- **Performance** — TODO: explain if/how performance applies
- **Scalability** — TODO: explain if/how scalability applies
- **Reliability** — TODO: explain if/how reliability applies
- **Operational Excellence** — TODO: explain if/how operational excellence applies

## Architectural Tradeoffs

TODO: Document the key tradeoffs a practitioner will face. Reference the patterns section in SKILL.md.

## Anti-Patterns

TODO: List 2–3 architectural anti-patterns this skill helps avoid.

1. **TODO: Anti-pattern name** — TODO: explain why this is bad and what to do instead.
2. **TODO: Anti-pattern name** — TODO: explanation.

## Official Sources Used

{source_lines}
"""


def _scaffold_checker_script(skill_name: str, domain: str) -> str:
    noun = skill_name.replace("-", "_")
    title = skill_name.replace("-", " ").title()
    return f'''#!/usr/bin/env python3
"""Checker script for {title} skill.

Checks org metadata or configuration relevant to {title}.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_{noun}.py [--help]
    python3 check_{noun}.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check {title} configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_{noun}(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    TODO: Implement real checks relevant to this skill.
    Each returned string should describe a concrete, actionable issue.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {{manifest_dir}}")
        return issues

    # TODO: Add real checks here. Examples:
    # - Parse XML metadata files and check for prohibited patterns
    # - Count fields/objects/flows and warn against limits
    # - Detect anti-patterns described in references/gotchas.md
    issues.append("TODO: implement actual checks for {title}")

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_{noun}(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {{issue}}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
'''


def _scaffold_llm_anti_patterns_md(skill_name: str, domain: str) -> str:
    title = skill_name.replace("-", " ").title()
    return f"""# LLM Anti-Patterns — {title}

Common mistakes AI coding assistants make when generating or advising on {title}.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: TODO: Name the mistake

**What the LLM generates:** TODO: show the wrong output

**Why it happens:** TODO: explain why LLMs default to this (e.g. Java bleed, training data bias, hallucinated API)

**Correct pattern:**

```
TODO: show the correct output
```

**Detection hint:** TODO: regex or keyword to spot this mistake

---

## Anti-Pattern 2: TODO: Name the mistake

**What the LLM generates:** TODO: wrong output

**Why it happens:** TODO: explanation

**Correct pattern:**

```
TODO: correct output
```

**Detection hint:** TODO: how to catch it

---

## Anti-Pattern 3: TODO: Name the mistake

**What the LLM generates:** TODO: wrong output

**Why it happens:** TODO: explanation

**Correct pattern:**

```
TODO: correct output
```

**Detection hint:** TODO: how to catch it

---

## Anti-Pattern 4: TODO: Name the mistake

**What the LLM generates:** TODO: wrong output

**Why it happens:** TODO: explanation

**Correct pattern:**

```
TODO: correct output
```

**Detection hint:** TODO: how to catch it

---

## Anti-Pattern 5: TODO: Name the mistake

**What the LLM generates:** TODO: wrong output

**Why it happens:** TODO: explanation

**Correct pattern:**

```
TODO: correct output
```

**Detection hint:** TODO: how to catch it
"""


def _scaffold_template_md(skill_name: str) -> str:
    title = skill_name.replace("-", " ").title()
    return f"""# {title} — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `{skill_name}`

**Request summary:** (fill in what the user asked for)

## Context Gathered

TODO: Record the answers to the Before Starting questions from SKILL.md here.

- Setting / configuration:
- Known constraints:
- Failure modes to watch for:

## Approach

TODO: Which pattern from SKILL.md applies? Why?

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] TODO
- [ ] TODO

## Notes

TODO: Record any deviations from the standard pattern and why.
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a new Salesforce skill package.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
After scaffolding:
  1. Open skills/<domain>/<skill-name>/SKILL.md and fill every TODO.
  2. Fill references/ and scripts/ files.
  3. Run:  python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name>
  4. Fix any validation errors reported, then re-run sync until it passes.
""",
    )
    parser.add_argument("domain", choices=sorted(ALLOWED_CATEGORIES), help="Skill domain.")
    parser.add_argument(
        "skill_name",
        metavar="skill-name",
        help="Skill name (lowercase, hyphenated, e.g. bulkification-patterns).",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Block scaffolding when the proposed skill name produces a "
             "near-duplicate (similarity >= configured threshold) against any "
             "existing skill. Default behavior warns only — strict turns the "
             "warning into a hard exit so agents can't silently create overlaps.",
    )
    parser.add_argument(
        "--agent", metavar="AGENT_ID", action="append",
        help="Run-time agent that should cite this skill. May be repeated for "
             "multiple agents. The skill is added to the agent's "
             "`dependencies.skills:` block and to its `## Mandatory Reads` "
             "section. Either --agent or --runtime-orphan is required (in TTY "
             "mode the scaffolder will prompt instead).",
    )
    parser.add_argument(
        "--runtime-orphan", action="store_true",
        help="Mark this skill as deliberately unowned by any run-time agent "
             "(adds `runtime_orphan: true` to the frontmatter). Use only when "
             "no agent reasonably owns this topic. Pair with --orphan-reason "
             "to record why.",
    )
    parser.add_argument(
        "--orphan-reason", metavar="TEXT",
        help="One-sentence explanation written to `runtime_orphan_reason:` in "
             "the frontmatter. Required (and only valid) with --runtime-orphan.",
    )
    args = parser.parse_args()

    # --agent and --runtime-orphan are mutually exclusive
    if args.agent and args.runtime_orphan:
        raise SystemExit(
            "✘ --agent and --runtime-orphan are mutually exclusive. "
            "Pick one: either wire the skill to one or more agents, or "
            "mark it as a deliberate orphan."
        )
    if args.orphan_reason and not args.runtime_orphan:
        raise SystemExit(
            "✘ --orphan-reason is only valid with --runtime-orphan."
        )

    domain: str = args.domain
    skill_name: str = args.skill_name

    # Enforce naming convention
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill_name):
        raise SystemExit(
            f"Invalid skill name '{skill_name}'. Use lowercase letters, digits, and hyphens only.\n"
            "Example: bulkification-patterns"
        )

    skill_dir = ROOT / "skills" / domain / skill_name

    if skill_dir.exists():
        raise SystemExit(
            f"Skill directory already exists: {skill_dir}\n"
            "To update an existing skill, edit its files and run skill_sync.py."
        )

    # Coverage check — warn if topic is likely already covered
    print(f"Checking local coverage for '{skill_name}' in domain '{domain}'…")
    if _check_coverage(skill_name.replace("-", " "), domain):
        print(
            f"\n⚠  WARNING: Local knowledge already has coverage for this topic.\n"
            f"   Run `python3 scripts/search_knowledge.py \"{skill_name.replace('-', ' ')}\"` to review.\n"
            f"   If this skill is genuinely distinct, proceed. Otherwise extend the existing skill.\n"
        )
        response = input("Continue scaffolding? [y/N] ").strip().lower()
        if response != "y":
            print("Aborted.")
            return 0

    # Similarity check — surface near-duplicates in the existing corpus.
    print(f"Checking pairwise similarity against {domain} corpus…")
    neighbours = _check_similarity_neighbours(skill_name, domain)
    if neighbours:
        print(
            f"\n⚠  Near-duplicate candidates (similarity ≥ configured threshold):\n"
        )
        for sid, score, desc in neighbours:
            print(f"   {score:.2f}  {sid}")
            if desc:
                print(f"          {desc[:140]}{'…' if len(desc) > 140 else ''}")
        print(
            f"\n   If this skill is genuinely distinct, proceed. Otherwise "
            f"extend an existing skill or rename to clarify scope.\n"
        )
        if args.strict:
            raise SystemExit(
                "✘ --strict: refusing to scaffold a near-duplicate. "
                "Drop --strict to override (you'll still see this warning), "
                "or pick a more distinct name / scope."
            )
        response = input("Continue scaffolding anyway? [y/N] ").strip().lower()
        if response != "y":
            print("Aborted.")
            return 0

    # ── Agent-wiring decision (mandatory; happens BEFORE scaffolding) ──
    agents_to_wire: list[str] = []
    is_orphan = False
    orphan_reason: str | None = None
    if args.agent:
        # Validate every supplied agent id exists.
        valid_ids = {a for a, _ in _list_runtime_agents()}
        bad = [a for a in args.agent if a not in valid_ids]
        if bad:
            raise SystemExit(
                f"✘ unknown agent id(s): {', '.join(bad)}. "
                f"Run with --help or list with `ls agents/`."
            )
        agents_to_wire = list(args.agent)
    elif args.runtime_orphan:
        is_orphan = True
        orphan_reason = args.orphan_reason or (
            f"No run-time agent currently owns the {domain} topic."
        )
    else:
        # No flags → require interactive decision. Fail loudly in non-TTY.
        if not sys.stdin.isatty():
            raise SystemExit(
                "✘ Agent-wiring decision is mandatory.\n"
                "   Pass --agent <id> [--agent <id> ...] to cite this skill from "
                "one or more run-time agents,\n"
                "   OR pass --runtime-orphan --orphan-reason \"<why>\" to "
                "deliberately leave it unowned.\n"
                "   See `python3 scripts/new_skill.py --help`."
            )
        agents_to_wire, is_orphan, orphan_reason = _prompt_agent_decision(
            domain, skill_name
        )

    # Read scaffold template
    scaffold_template = ROOT / "config" / "skill-scaffold.md"
    if not scaffold_template.exists():
        raise SystemExit(f"Scaffold template not found: {scaffold_template}")

    # Create directory structure
    (skill_dir / "references").mkdir(parents=True, exist_ok=True)
    (skill_dir / "templates").mkdir(parents=True, exist_ok=True)
    (skill_dir / "scripts").mkdir(parents=True, exist_ok=True)

    noun = skill_name.replace("-", "_")

    files_created: list[str] = []

    def write(path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")
        files_created.append(str(path.relative_to(ROOT)))

    write(skill_dir / "SKILL.md", _scaffold_skill_md(scaffold_template, skill_name, domain))
    write(skill_dir / "references" / "examples.md", _scaffold_examples_md(skill_name))
    write(skill_dir / "references" / "gotchas.md", _scaffold_gotchas_md(skill_name))
    write(skill_dir / "references" / "well-architected.md", _scaffold_well_architected_md(skill_name, domain))
    write(skill_dir / "references" / "llm-anti-patterns.md", _scaffold_llm_anti_patterns_md(skill_name, domain))
    write(skill_dir / "templates" / f"{skill_name}-template.md", _scaffold_template_md(skill_name))

    checker = skill_dir / "scripts" / f"check_{noun}.py"
    write(checker, _scaffold_checker_script(skill_name, domain))
    checker.chmod(0o755)

    print(f"\n✔  Scaffolded: skills/{domain}/{skill_name}/")
    print("\nFiles created:")
    for f in files_created:
        print(f"  {f}")

    # ── Apply the agent-wiring decision ──────────────────────────────────
    skill_id = f"{domain}/{skill_name}"
    if is_orphan:
        _add_orphan_marker(skill_dir / "SKILL.md", orphan_reason or "")
        print(
            f"\n📌 Marked runtime_orphan: true (reason: {orphan_reason}).\n"
            f"   The validator will accept this skill without an agent citation."
        )
    elif agents_to_wire:
        # Use the first sentence of the description as the wiring blurb.
        # If the description is still TODO at this point, fall back to the skill name.
        try:
            from pipelines.frontmatter_io import parse_markdown_with_frontmatter
            parsed = parse_markdown_with_frontmatter(skill_dir / "SKILL.md")
            desc = (parsed.metadata.get("description") or "").strip()
            blurb = desc.split(". ")[0].strip(' "\'.')[:120] if desc else ""
        except Exception:
            blurb = ""
        if not blurb or blurb.upper().startswith("TODO"):
            blurb = skill_name.replace("-", " ")
        print(f"\n🔌 Wiring '{skill_id}' into {len(agents_to_wire)} agent(s):")
        for aid in agents_to_wire:
            _patch_agent_with_skill(aid, skill_id, blurb)

    # Print official sources prominently — MUST read before writing any content
    official_sources = DOMAIN_OFFICIAL_SOURCES.get(domain, [
        "Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html",
    ])
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║  ⚠  MANDATORY: READ OFFICIAL DOCS BEFORE WRITING ANY CONTENT        ║
║  Do NOT rely on local RAG alone — it can be wrong or outdated.       ║
║  Every factual claim must be grounded in an official Salesforce doc. ║
╠══════════════════════════════════════════════════════════════════════╣""")
    print(f"║  Official sources for domain '{domain}':{' ' * max(0, 28 - len(domain))}║")
    for src in official_sources:
        # Wrap long lines
        line = f"║    {src}"
        if len(line) < 71:
            line = line + " " * (71 - len(line)) + "║"
        else:
            line = line[:69] + "… ║"
        print(line)
    print("""╚══════════════════════════════════════════════════════════════════════╝""")

    print(f"""
┌─ Next steps ─────────────────────────────────────────────────────────┐
│                                                                      │
│  STEP 1 — Read the official docs listed above (non-negotiable).      │
│           The sources are also pre-seeded in references/             │
│           well-architected.md for easy reference while you write.    │
│                                                                      │
│  STEP 2 — Open skills/{domain}/{skill_name}/SKILL.md       │
│           Fill every TODO. Description MUST include "NOT for ..."    │
│           Triggers need 3+ natural-language symptom phrases.         │
│                                                                      │
│  STEP 3 — Fill references/examples.md, references/gotchas.md,       │
│           and references/well-architected.md                         │
│                                                                      │
│  STEP 4 — Implement scripts/check_{noun}.py            │
│           (stdlib only — no pip dependencies)                        │
│                                                                      │
│  STEP 5 — Run:                                                       │
│       python3 scripts/skill_sync.py --skill skills/{domain}/{skill_name}  │
│           Validation runs first. Fix errors, re-run until it passes. │
│                                                                      │
│  STEP 6 — Add a query fixture to vector_index/query-fixtures.json    │
│           then run: python3 scripts/validate_repo.py                 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
""")

    return 0


if __name__ == "__main__":
    sys.exit(main())
