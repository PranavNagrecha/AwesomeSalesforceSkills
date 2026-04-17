#!/usr/bin/env python3
"""Wave 10 migration: bring every runtime agent into Deliverable Contract compliance.

For each `class: runtime, status != deprecated` agent:

1. Add frontmatter fields:
   - `default_output_dir: docs/reports/<agent-id>/`
   - `output_formats: [markdown, json]`
   - `multi_dimensional: true` for known multi-dim agents

2. Add to Mandatory Reads section:
   - `agents/_shared/DELIVERABLE_CONTRACT.md`

3. Inside "## Output Contract" section, ensure Persistence + Scope Guardrails
   sub-sections exist. If missing, append them.

Idempotent — re-running does not duplicate entries.

Usage:
    python3 scripts/migrate_deliverable_contract.py --dry-run
    python3 scripts/migrate_deliverable_contract.py
    python3 scripts/migrate_deliverable_contract.py --agent user-access-diff

Exit codes:
  0 — migration complete (or no-op)
  1 — at least one agent couldn't be migrated
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = REPO_ROOT / "agents"

# Agents flagged as multi-dimensional — their output covers 3+ independently-
# comparable dimensions. Sourced from the Wave 10 plan approval.
# Note: code-reviewer (class=build) and org-drift-detector (status=deprecated,
# replaced by audit-router) don't need this flag.
MULTI_DIMENSIONAL_AGENTS = {
    "user-access-diff",
    "deployment-risk-scorer",
    "security-scanner",
    "audit-router",
    "field-impact-analyzer",
    "waf-assessor",
    "data-model-reviewer",
    "profile-to-permset-migrator",
}


PERSISTENCE_BLOCK = """
### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/{agent_id}/<run_id>.md`
- **JSON envelope:** `docs/reports/{agent_id}/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.
"""

SCOPE_GUARDRAILS_BLOCK = """
### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.
"""


def parse_agent_frontmatter(text: str) -> tuple[str, str]:
    """Split the text into (frontmatter_raw, body_raw)."""
    m = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not m:
        return "", text
    return m.group(1), m.group(2)


def parse_frontmatter_fields(raw: str) -> dict:
    """Very minimal YAML parser — enough to detect existing keys."""
    out: dict = {}
    current_top: str | None = None

    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
            if val == "":
                out[key] = True  # marker that it starts a block
                current_top = key
            else:
                out[key] = val
                current_top = None
    return out


def inject_frontmatter_fields(raw_fm: str, agent_id: str, is_multi_dim: bool) -> tuple[str, list[str]]:
    """Append missing Wave 10 fields to the frontmatter. Returns (new_fm, changes)."""
    existing = parse_frontmatter_fields(raw_fm)
    changes = []
    lines = raw_fm.rstrip().splitlines()

    if "default_output_dir" not in existing:
        lines.append(f'default_output_dir: "docs/reports/{agent_id}/"')
        changes.append("default_output_dir")

    if "output_formats" not in existing:
        lines.append("output_formats:")
        lines.append("  - markdown")
        lines.append("  - json")
        changes.append("output_formats")

    if is_multi_dim and "multi_dimensional" not in existing:
        lines.append("multi_dimensional: true")
        changes.append("multi_dimensional")

    return "\n".join(lines), changes


def inject_mandatory_read(body: str) -> tuple[str, bool]:
    """Add DELIVERABLE_CONTRACT.md to Mandatory Reads if not present. Returns (new_body, changed)."""
    if "DELIVERABLE_CONTRACT.md" in body:
        return body, False

    # Find the "## Mandatory Reads Before Starting" section (or any variant).
    heading_pattern = re.compile(r"^(##\s+Mandatory Reads[^\n]*)$", re.MULTILINE)
    m = heading_pattern.search(body)
    if not m:
        return body, False

    # Find where to insert. After the heading, locate the numbered list, find
    # the last numbered item, and insert a new one after it.
    section_start = m.end()
    # Find next "## " section or end of body.
    next_heading = re.search(r"^## ", body[section_start:], re.MULTILINE)
    section_end = section_start + next_heading.start() if next_heading else len(body)
    section = body[section_start:section_end]

    # Find the last numbered item in the section.
    item_pattern = re.compile(r"^(\d+)\.\s+(.+)$", re.MULTILINE)
    items = list(item_pattern.finditer(section))
    if not items:
        return body, False

    last_item = items[-1]
    last_num = int(last_item.group(1))
    new_num = last_num + 1
    insert_pos = section_start + last_item.end()

    new_entry = f"\n{new_num}. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)"
    new_body = body[:insert_pos] + new_entry + body[insert_pos:]
    return new_body, True


def inject_output_contract_subsections(body: str, agent_id: str) -> tuple[str, list[str]]:
    """Append Persistence + Scope Guardrails sub-sections to the Output Contract
    section if not present. Returns (new_body, changes)."""
    changes = []

    # Find the "## Output Contract" section.
    heading_pattern = re.compile(r"^(##\s+Output Contract)$", re.MULTILINE)
    m = heading_pattern.search(body)
    if not m:
        return body, []

    section_start = m.end()
    next_heading = re.search(r"^## ", body[section_start:], re.MULTILINE)
    section_end = section_start + next_heading.start() if next_heading else len(body)
    section = body[section_start:section_end]

    # Check for existing sub-sections.
    has_persistence = "### Persistence" in section or "docs/reports/" in section
    has_guardrails = "### Scope Guardrails" in section or "Scope Guardrails" in section

    blocks_to_insert = []
    if not has_persistence:
        blocks_to_insert.append(PERSISTENCE_BLOCK.format(agent_id=agent_id))
        changes.append("Persistence sub-section")
    if not has_guardrails:
        blocks_to_insert.append(SCOPE_GUARDRAILS_BLOCK)
        changes.append("Scope Guardrails sub-section")

    if not blocks_to_insert:
        return body, []

    # Insert just before the next "## " (or at end of body).
    insertion = "\n" + "\n".join(b.strip() + "\n" for b in blocks_to_insert) + "\n"
    new_body = body[:section_end].rstrip() + "\n" + insertion + body[section_end:]
    return new_body, changes


def process_agent(path: Path, dry_run: bool) -> tuple[str, list[str]]:
    """Migrate one AGENT.md. Returns (status, list_of_changes)."""
    agent_id = path.parent.name
    text = path.read_text(encoding="utf-8")
    raw_fm, body = parse_agent_frontmatter(text)
    if not raw_fm:
        return "skipped-no-frontmatter", []

    existing_fm_fields = parse_frontmatter_fields(raw_fm)
    if existing_fm_fields.get("class") != "runtime":
        return "skipped-not-runtime", []
    if existing_fm_fields.get("status") == "deprecated":
        return "skipped-deprecated", []

    is_multi_dim = agent_id in MULTI_DIMENSIONAL_AGENTS
    all_changes: list[str] = []

    new_fm, fm_changes = inject_frontmatter_fields(raw_fm, agent_id, is_multi_dim)
    all_changes.extend(f"frontmatter:{c}" for c in fm_changes)

    new_body, mr_changed = inject_mandatory_read(body)
    if mr_changed:
        all_changes.append("mandatory-read:DELIVERABLE_CONTRACT.md")

    new_body, oc_changes = inject_output_contract_subsections(new_body, agent_id)
    all_changes.extend(f"output-contract:{c}" for c in oc_changes)

    if not all_changes:
        return "no-changes-needed", []

    new_text = f"---\n{new_fm}\n---\n{new_body}"

    if not dry_run:
        path.write_text(new_text, encoding="utf-8")

    return ("would-update" if dry_run else "updated"), all_changes


def main() -> int:
    parser = argparse.ArgumentParser(description="Wave 10 Deliverable Contract migration.")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing.")
    parser.add_argument("--agent", help="Migrate one agent by id.")
    args = parser.parse_args()

    if args.agent:
        paths = [AGENTS_DIR / args.agent / "AGENT.md"]
        if not paths[0].exists():
            print(f"No AGENT.md at {paths[0]}", file=sys.stderr)
            return 1
    else:
        paths = sorted(AGENTS_DIR.glob("*/AGENT.md"))

    totals: dict[str, int] = {}
    for path in paths:
        status, changes = process_agent(path, dry_run=args.dry_run)
        totals[status] = totals.get(status, 0) + 1
        if status in {"updated", "would-update"}:
            agent_id = path.parent.name
            verb = "Would update" if args.dry_run else "Updated"
            changes_short = ", ".join(changes[:4])
            if len(changes) > 4:
                changes_short += f", +{len(changes) - 4} more"
            print(f"  {verb:12} {agent_id}: {changes_short}")

    print("\nSummary:")
    for status, count in sorted(totals.items()):
        print(f"  {status}: {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
