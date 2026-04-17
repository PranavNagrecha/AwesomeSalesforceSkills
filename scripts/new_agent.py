#!/usr/bin/env python3
"""Scaffold a new runtime agent that conforms to all active waves' contracts.

Emits:

1. `agents/<agent-id>/AGENT.md` with:
   - Frontmatter carrying Wave 8 dependencies block + Wave 10 output-contract
     fields (default_output_dir, output_formats, multi_dimensional)
   - All 8 required sections with TODO markers
   - Pre-filled Wave 10 Persistence + Scope Guardrails sub-sections under
     Output Contract (so the agent passes test_deliverable_contract.py
     from day one)
2. `commands/<slash-alias>.md` — a matching slash-command file, so the
   Wave 5 slash-command-coverage validator passes immediately

Why this script exists: autonomous builders (agent-authoring pipelines,
forks, external contributors) would otherwise ship agents that fail the
Wave 10 deliverable-contract test or the Wave 5 slash-coverage test.
This scaffolder makes "contract-compliant by default" the path of least
resistance.

Usage:
    python3 scripts/new_agent.py <agent-id> <slash-alias> [--multi-dim] [--requires-org]

    python3 scripts/new_agent.py my-new-agent /my-new-agent
    python3 scripts/new_agent.py org-audit-x /audit-x --multi-dim --requires-org
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = REPO_ROOT / "agents"
COMMANDS_DIR = REPO_ROOT / "commands"


AGENT_TEMPLATE = """---
id: {agent_id}
class: runtime
version: 1.0.0
status: stable
requires_org: {requires_org}
modes: [single]
owner: sfskills-core
created: {today}
updated: {today}
default_output_dir: "docs/reports/{agent_id}/"
output_formats:
  - markdown
  - json
{multi_dim_line}dependencies:
  probes: []
  skills: []
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
---

# {agent_title}

## What This Agent Does

TODO: One paragraph in plain English. End with an explicit scope boundary ("Scope: ...").

---

## Invocation

- **Direct read** — "Follow `agents/{agent_id}/AGENT.md` for ..."
- **Slash command** — [`{slash_alias}`](../../commands/{alias_stem}.md)
- **MCP** — `get_agent("{agent_id}")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)
4. TODO: cite each probe, skill, template, or decision tree the agent needs

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `target_org_alias` | {requires_org_y_n} | `prod` |
| TODO | TODO | TODO |

Refuse if required inputs are missing or ambiguous.

---

## Plan

### Step 1 — TODO: name the step

TODO: describe. Cite the skill/probe/template you use.

### Step 2 — TODO

TODO: describe.

### Step 3 — TODO

TODO: describe.

---

## Output Contract

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md` and `agents/_shared/schemas/output-envelope.schema.json`.

### Deliverables

1. **Summary** — one paragraph, the deliverable in a single screen.
2. **Confidence** — HIGH / MEDIUM / LOW, with rationale keyed to the rubric.
3. TODO: agent-specific findings / tables / diagrams.
4. **Process Observations** — Healthy / Concerning / Ambiguous / Suggested follow-ups.
5. **Citations** — every skill, probe, and MCP tool consulted.

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/{agent_id}/<run_id>.md`
- **JSON envelope:** `docs/reports/{agent_id}/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.
{dimensions_block}
---

## Escalation / Refusal Rules

TODO: list each refusal condition + the canonical REFUSAL_CODE (see `agents/_shared/REFUSAL_CODES.md`).

- TODO: refusal condition → code `TODO_CODE`
- `target_org_alias` not connected via `sf` CLI → refuse with code `ORG_UNREACHABLE` (when `requires_org: true`)

---

## What This Agent Does NOT Do

TODO: list explicit non-goals. Prevents scope creep.

- TODO
- TODO
- Does not chain to other agents automatically.
"""


COMMAND_TEMPLATE = """# {slash_alias} — TODO: one-line description

Wraps [`agents/{agent_id}/AGENT.md`](../agents/{agent_id}/AGENT.md).

---

## Step 1 — Collect inputs

Ask the user:

```
1. TODO: input
2. TODO: input
```

If any required input is missing, STOP and ask.

---

## Step 2 — Load the agent

Read `agents/{agent_id}/AGENT.md` + all Mandatory Reads.

---

## Step 3 — Execute the plan

Follow the 3-step plan. Capture tool-call outputs for the envelope.

---

## Step 4 — Deliver the output

Return the Output Contract per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- Markdown report at `docs/reports/{agent_id}/<run_id>.md`
- JSON envelope at `docs/reports/{agent_id}/<run_id>.json`
- Chat: short confirmation + envelope JSON block

---

## Step 5 — Recommend follow-ups

- TODO: other agent / command to recommend next

---

## What this command does NOT do

- TODO: explicit non-goals.
"""


DIMENSIONS_BLOCK = """
### Dimensions (Wave 10 contract)

The agent's envelope MUST place every dimension below in either `dimensions_compared[]` or `dimensions_skipped[]`. Partial or count-only coverage is recorded with `state: count-only | partial`, not elided.

| Dimension | Notes |
|---|---|
| TODO: dimension-a | TODO |
| TODO: dimension-b | TODO |
| TODO: dimension-c | TODO |
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a contract-compliant runtime agent.")
    parser.add_argument("agent_id", help="Kebab-case agent folder name, e.g. 'my-new-agent'")
    parser.add_argument("slash_alias", help="Slash command alias (with leading '/'), e.g. '/my-new-agent'")
    parser.add_argument("--multi-dim", action="store_true",
                        help="Mark as multi-dimensional (3+ independent dimensions in output)")
    parser.add_argument("--requires-org", action="store_true",
                        help="Set requires_org: true (agent refuses without an sf org alias)")
    args = parser.parse_args()

    if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", args.agent_id):
        print(f"ERROR: agent_id must be kebab-case: {args.agent_id}", file=sys.stderr)
        return 1
    if not args.slash_alias.startswith("/"):
        print(f"ERROR: slash_alias must start with '/': {args.slash_alias}", file=sys.stderr)
        return 1
    alias_stem = args.slash_alias.lstrip("/")
    if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", alias_stem):
        print(f"ERROR: slash_alias body must be kebab-case: {args.slash_alias}", file=sys.stderr)
        return 1

    agent_dir = AGENTS_DIR / args.agent_id
    cmd_file = COMMANDS_DIR / f"{alias_stem}.md"
    if agent_dir.exists():
        print(f"ERROR: {agent_dir} already exists", file=sys.stderr)
        return 1
    if cmd_file.exists():
        print(f"ERROR: {cmd_file} already exists", file=sys.stderr)
        return 1

    today = dt.date.today().isoformat()
    agent_title = " ".join(word.capitalize() for word in args.agent_id.split("-")) + " Agent"

    agent_content = AGENT_TEMPLATE.format(
        agent_id=args.agent_id,
        agent_title=agent_title,
        slash_alias=args.slash_alias,
        alias_stem=alias_stem,
        today=today,
        requires_org="true" if args.requires_org else "false",
        requires_org_y_n="yes" if args.requires_org else "no",
        multi_dim_line="multi_dimensional: true\n" if args.multi_dim else "",
        dimensions_block=DIMENSIONS_BLOCK if args.multi_dim else "",
    )
    cmd_content = COMMAND_TEMPLATE.format(
        agent_id=args.agent_id,
        slash_alias=args.slash_alias,
    )

    agent_dir.mkdir(parents=True)
    (agent_dir / "AGENT.md").write_text(agent_content, encoding="utf-8")
    cmd_file.write_text(cmd_content, encoding="utf-8")

    print(f"✓ Scaffolded {args.agent_id}")
    print(f"  AGENT.md:  {agent_dir / 'AGENT.md'}")
    print(f"  Command:   {cmd_file}")
    print()
    print("Next steps:")
    print(f"  1. Fill every TODO in {agent_dir / 'AGENT.md'}")
    print(f"  2. Fill every TODO in {cmd_file}")
    print(f"  3. Populate dependencies block (probes, skills, templates)")
    print(f"  4. Run: python3 scripts/validate_repo.py --agents")
    print(f"  5. Run: cd mcp/sfskills-mcp && python3 -m unittest tests")
    print(f"  6. Run: python3 scripts/export_skills.py --all --manifest")
    print(f"  7. Commit + push.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
