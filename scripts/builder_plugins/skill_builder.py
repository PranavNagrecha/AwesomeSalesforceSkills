"""SkillBuilderPlugin — shared gated QA for all skill-builder agents.

Six agents share this plugin:
  admin-skill-builder, architect-skill-builder, data-skill-builder,
  devops-skill-builder, security-skill-builder, dev-skill-builder.

Each agent targets a distinct skills/<domain>/ directory but the Gate C
contract is identical:
  * SKILL.md exists with all required frontmatter keys.
  * references/ subdir has examples.md, gotchas.md, well-architected.md,
    llm-anti-patterns.md.
  * llm-anti-patterns.md lists ≥5 numbered or bulleted items.
  * SKILL.md body includes a `## Recommended Workflow` heading with
    ≥3 and ≤7 numbered steps.
  * frontmatter `category` matches the agent's domain.

No live oracle — skill-builder runs library-only against the repo. Confidence
is driven by static-check cleanliness alone (floor/high_tier both = 0).
"""

from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path
from typing import Any

from .base import LiveCheckResult


REQUIRED_FRONTMATTER_KEYS = {
    "name", "description", "category", "salesforce-version",
    "well-architected-pillars", "tags", "inputs", "outputs",
    "dependencies", "version", "author", "updated",
}

REQUIRED_REFERENCES = {"examples.md", "gotchas.md", "well-architected.md", "llm-anti-patterns.md"}

AGENT_DOMAINS: dict[str, tuple[str, set[str]]] = {
    # agent_name → (default skills/<domain> directory, valid frontmatter category values)
    "admin-skill-builder":    ("admin",    {"admin"}),
    "architect-skill-builder":("architect",{"architect"}),
    "data-skill-builder":     ("data",     {"data"}),
    "devops-skill-builder":   ("devops",   {"devops"}),
    "security-skill-builder": ("security", {"security"}),
    "dev-skill-builder":      ("apex",     {"apex", "lwc", "flow", "omnistudio", "integration", "agentforce"}),
}


def _bullets(items: list[str], indent: str = "  ") -> str:
    if not items:
        return f"{indent}- _(none)_"
    return "\n".join(f"{indent}- {it}" for it in items)


class SkillBuilderPlugin:
    """Shared skill-builder plugin. Parameterized by agent_name so we can
    register the same class against all 6 skill-builder aliases."""

    def __init__(self, agent_name: str):
        if agent_name not in AGENT_DOMAINS:
            raise ValueError(f"unknown skill-builder agent: {agent_name}")
        self.agent = agent_name
        self.default_domain, self.valid_categories = AGENT_DOMAINS[agent_name]

    # --- Gate A ------------------------------------------------------------
    def additional_input_checks(self, inputs: dict[str, Any]) -> tuple[list[str], list[str]]:
        missing: list[str] = []
        invalid: list[str] = []
        if not inputs.get("skill_slug"):
            missing.append("skill_slug (kebab-case, matches the skill directory name)")
        if not inputs.get("domain"):
            missing.append(f"domain (one of {sorted(self.valid_categories)})")
        else:
            d = inputs["domain"]
            if d not in self.valid_categories:
                invalid.append(f"domain '{d}' is not in this agent's valid categories {sorted(self.valid_categories)}")
        return missing, invalid

    # --- Gate B ------------------------------------------------------------
    def grounding_sobjects(self, inputs: dict[str, Any]) -> list[str]:
        return []

    def expected_resources(self, inputs: dict[str, Any]) -> list[dict[str, str]]:
        return []

    def expected_citations(self, inputs: dict[str, Any]) -> list[dict[str, str]]:
        return [
            {"type": "standard", "id": "CLAUDE.md"},
            {"type": "standard", "id": "AGENT_RULES.md"},
        ]

    # --- deliverables ------------------------------------------------------
    def class_inventory(self, inputs: dict[str, Any]) -> list[str]:
        slug = inputs.get("skill_slug") or "new-skill"
        domain = inputs.get("domain") or self.default_domain
        base = f"skills/{domain}/{slug}"
        return [
            f"{base}/SKILL.md",
            f"{base}/references/examples.md",
            f"{base}/references/gotchas.md",
            f"{base}/references/well-architected.md",
            f"{base}/references/llm-anti-patterns.md",
        ]

    def expected_deliverable_stems(self, inputs: dict[str, Any]) -> set[str]:
        return set()

    # --- grounding symbols for REQUIREMENTS --------------------------------
    def grounding_symbols(self, inputs: dict[str, Any]) -> list[str]:
        return [
            f"Skill slug: `{inputs.get('skill_slug') or '_(unspecified)_'}`",
            f"Domain directory: `skills/{inputs.get('domain') or self.default_domain}/` (must exist)",
            "Standard: `CLAUDE.md` Required Skill Frontmatter section",
            "Standard: `AGENT_RULES.md` skill-builder workflow",
        ]

    # --- requirements template vars ----------------------------------------
    def requirements_template_vars(
        self,
        inputs: dict[str, Any],
        run_id: str,
        inputs_sha256: str,
        agent_version: str = "1.0.0",
    ) -> dict[str, str]:
        return {
            "{{feature_summary_short}}": (inputs.get("feature_summary") or "").strip()[:80],
            "{{run_id}}": run_id,
            "{{generated_at}}": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "{{agent_version}}": agent_version,
            "{{inputs_sha256}}": inputs_sha256,
            "{{feature_summary}}": inputs.get("feature_summary", "_(unspecified)_"),
            "{{skill_slug}}": inputs.get("skill_slug", "_(unspecified)_"),
            "{{domain}}": inputs.get("domain", self.default_domain),
            "{{skill_category}}": inputs.get("skill_category", inputs.get("domain", self.default_domain)),
            "{{api_version}}": inputs.get("api_version", "60.0"),
            "{{target_org_alias_or_library_only}}": inputs.get("target_org_alias") or "_(library-only mode)_",
            "{{skill_inventory_bullets}}": _bullets([f"`{c}`" for c in self.class_inventory(inputs)]),
            "{{grounding_symbols_bullets}}": _bullets(self.grounding_symbols(inputs)),
        }

    # --- Gate C ------------------------------------------------------------
    def discover_emitted_files(self, emitted_dir: Path) -> list[Path]:
        if not emitted_dir.exists():
            return []
        out: list[Path] = []
        # SKILL.md at root, plus everything under references/.
        skill_md = emitted_dir / "SKILL.md"
        if skill_md.exists():
            out.append(skill_md)
        refs = emitted_dir / "references"
        if refs.exists():
            out.extend(sorted(refs.rglob("*.md")))
        return out

    def static_check(self, files: list[Path]) -> list[str]:
        errors: list[str] = []
        by_name = {f.name: f for f in files}

        skill_md = by_name.get("SKILL.md")
        if not skill_md:
            return ["no SKILL.md in emitted_dir"]

        errors.extend(self._check_skill_md(skill_md))

        # required references
        found_refs = {f.name for f in files if f.parent.name == "references"}
        for req in REQUIRED_REFERENCES:
            if req not in found_refs:
                errors.append(f"references/{req} missing")
        anti = by_name.get("llm-anti-patterns.md")
        if anti:
            body = anti.read_text(encoding="utf-8", errors="replace")
            items = len(re.findall(r"^\s*(?:\d+\.|-|\*)\s+\S", body, flags=re.MULTILINE))
            if items < 5:
                errors.append(f"references/llm-anti-patterns.md: only {items} listed items; need ≥5")
        return errors

    def live_check(
        self,
        files: list[Path],
        target_org: str,
        api_version: str,
        timeout_sec: int = 300,
    ) -> LiveCheckResult:
        # Skill-builders are library-only — there is no live oracle.
        res = LiveCheckResult(oracle_label="(library-only: no live oracle)")
        res.ran = False
        res.succeeded = True
        return res

    def coverage_thresholds(self, inputs: dict[str, Any]) -> dict[str, int]:
        return {"floor": 0, "high_tier": 0}

    # --- private helpers ---------------------------------------------------
    def _check_skill_md(self, path: Path) -> list[str]:
        errors: list[str] = []
        body = path.read_text(encoding="utf-8", errors="replace")
        m = re.match(r"^---\n(.*?)\n---\n", body, flags=re.DOTALL)
        if not m:
            return [f"{path.name}: missing YAML frontmatter delimited by ---"]
        fm_text = m.group(1)
        keys_seen: set[str] = set()
        category_value: str | None = None
        for line in fm_text.splitlines():
            km = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
            if km:
                keys_seen.add(km.group(1))
                if km.group(1) == "category":
                    category_value = km.group(2).strip()
        missing_keys = REQUIRED_FRONTMATTER_KEYS - keys_seen
        for k in sorted(missing_keys):
            errors.append(f"{path.name}: frontmatter missing required key `{k}`")

        if category_value and category_value not in self.valid_categories:
            errors.append(f"{path.name}: frontmatter category `{category_value}` not in {sorted(self.valid_categories)}")

        # Recommended Workflow: 3-7 numbered steps
        body_after_fm = body[m.end():]
        wf = re.search(r"^##\s+Recommended Workflow\s*$(.*?)^##\s", body_after_fm, flags=re.DOTALL | re.MULTILINE)
        if not wf:
            # may be the last section
            wf = re.search(r"^##\s+Recommended Workflow\s*$(.*)\Z", body_after_fm, flags=re.DOTALL | re.MULTILINE)
        if not wf:
            errors.append(f"{path.name}: missing `## Recommended Workflow` section")
        else:
            steps = re.findall(r"^\s*\d+\.\s+\S", wf.group(1), flags=re.MULTILINE)
            if len(steps) < 3:
                errors.append(f"{path.name}: Recommended Workflow has only {len(steps)} numbered steps; need ≥3")
            if len(steps) > 7:
                errors.append(f"{path.name}: Recommended Workflow has {len(steps)} numbered steps; max 7")

        return errors
