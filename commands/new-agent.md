# /new-agent — New Run-time Agent Workflow

Triggers creation of a new run-time agent under `agents/<agent-id>/AGENT.md`.

## Usage

```
/new-agent
```

A run-time agent uses the existing skill library to do real Salesforce work against a user's org or codebase. Build-time agents (which produce the library itself) follow a different lifecycle — see `agents/_shared/AGENT_CONTRACT.md`.

## What Happens

### Step 1 — Confirm the agent is needed

Before scaffolding, sanity-check:

- Is the work this agent does *really* not covered by an existing run-time agent? Read `agents/_shared/RUNTIME_VS_BUILD.md` and search for adjacent agents. If overlap is high, extend an existing agent instead of creating a new one.
- Is the work bounded enough to be one agent? "Audit everything in the org" is too big — split.
- Is the agent invocable as a one-shot with a clear input contract? If it needs multi-turn conversation, reconsider the shape.

### Step 2 — Scaffold the agent directory

Create `agents/<agent-id>/AGENT.md` following the 8-section contract in `agents/_shared/AGENT_CONTRACT.md`. The frontmatter must validate against `agents/_shared/schemas/agent-frontmatter.schema.json`.

```yaml
---
id: <agent-id>           # must match the folder name (kebab-case)
class: runtime
version: 0.1.0
status: beta
requires_org: true       # or false if codebase-only
modes: [single]
owner: <team-or-handle>
created: YYYY-MM-DD
updated: YYYY-MM-DD
dependencies:
  skills: []             # filled in Step 4
  shared: []
  templates: []
  decision_trees: []
---
```

The 8 required sections (per `AGENT_CONTRACT.md`): What This Agent Does, Invocation, Mandatory Reads Before Starting, Inputs, Plan, Output Contract (with the Process Observations subsection), Escalation / Refusal Rules, What This Agent Does NOT Do.

### Step 3 — Define the agent's job in one paragraph

Write the "What This Agent Does" section first, in plain prose, before touching anything else. If you can't describe the agent's job in one paragraph, the scope isn't tight enough — go back to Step 1.

### Step 4 — Find existing skills that this agent would genuinely use

This is a **judgment** step, not a sweep. Walk the skill library and decide which skills belong in this agent's `Mandatory Reads`. The bar: a skill should be cited only when reading it would change the agent's output for a real invocation. If you can't name the scenario in which the agent would be wrong without it, the skill doesn't belong.

1. **Discover candidates.** Use `python3 scripts/search_skills.py "<topic>"` and `python3 scripts/search_knowledge.py "<query>"` for each capability the agent needs. Walk the relevant domain folders under `skills/<domain>/`.

2. **Filter by relevance.** For each candidate, name the concrete scenario where this skill matters for *this* agent. If you can't, drop it. Aim for the smallest set that covers the agent's real failure modes — typically 5–25 skills, occasionally more for cross-domain agents like `field-impact-analyzer`. More than ~30 is a smell that the agent's scope is too broad or the citations are too defensive.

3. **Wire each kept skill** by adding it to the YAML `dependencies.skills:` block (alphabetical) and to the appropriate `### subsection` of the agent's Mandatory Reads. The subsections should reflect the agent's mental model (e.g., "Field shape & data model", "Access / sharing", "Apex / SOQL impact") — not the source-domain folder names.

4. **Don't invent skills to fit.** If the agent needs a topic the library doesn't cover, file a `commands/request-skill.md` or scaffold via `/new-skill` rather than fabricating citations. Every citation must resolve to a real `skills/<domain>/<slug>/SKILL.md` at commit time — `validate_repo.py` rejects invented paths.

5. **Cite templates and decision trees too.** `templates/<domain>/...` for canonical code idioms; `standards/decision-trees/...` for cross-skill routing. List them in their own subsections.

### Step 5 — Add the agent to the supporting indexes

- `agents/_shared/RUNTIME_VS_BUILD.md` — add the agent to the appropriate tier list.
- `agents/_shared/SKILL_MAP.md` — add an entry summarizing the citations (Wave A/B/C agents only). Developer-tier agents skip this.
- `mcp/sfskills-mcp/src/sfskills_mcp/agents.py` — add the agent id to the `_RUNTIME_AGENTS` frozenset and the matching `EXPECTED_RUNTIME` test in `mcp/sfskills-mcp/tests/test_agents.py`. This is what makes the agent appear as `kind: "runtime"` in the MCP `list_agents` output.
- `commands/<command-name>.md` — if the agent has a slash command, create the command file pointing to the agent.

### Step 6 — Validate

```bash
python3 scripts/validate_repo.py --agents
```

The agent validator checks:

- 8-section structure per `AGENT_CONTRACT.md`
- frontmatter conforms to `schemas/agent-frontmatter.schema.json`
- every cited skill / template / decision tree resolves to a real file
- Process Observations subsection exists in the Output Contract

The orphan-skill check (`scripts/validate_repo.py` without `--agents`) re-runs across the whole library and may show *fewer* orphans now that the new agent cites previously-orphan skills — that is the expected, healthy direction.

## Quality Gate

A new run-time agent is not complete unless:

- All 8 contract sections are present and non-trivial.
- Every citation in `Mandatory Reads` resolves to a real file.
- The agent is registered in `RUNTIME_VS_BUILD.md` and the MCP runtime frozenset.
- `python3 scripts/validate_repo.py --agents` exits 0.

## Anti-Patterns

- **Citing every adjacent skill** — bloats Mandatory Reads, dilutes the signal, and makes the agent slow at startup. Cite the skills the agent actually reaches for, no more.
- **Citing skills you didn't read** — every citation is a contract that the agent will consult that file. Read each one, confirm it applies, then cite.
- **Inventing skills to fill perceived gaps** — if a topic isn't covered, create the skill via `/new-skill` separately. Don't ship an agent with a citation pointing at a TODO.
- **Fabricating orphan-rescue logic** — the goal is the agent's job, not orphan reduction. If wiring an orphan skill makes the agent better, do it. If it doesn't, don't.

## Related

- `agents/_shared/AGENT_CONTRACT.md` — the 8-section contract.
- `agents/_shared/SKILL_MAP.md` — existing agent → skill mappings.
- `agents/_shared/RUNTIME_VS_BUILD.md` — full agent roster.
- `commands/new-skill.md` — the inverse workflow (new skill → check existing agents).
- `scripts/patch_agent_skill.py` — mechanical helper for adding a skill to an existing agent's citations.
