# Agent Contract

Every agent in this repo — build-time or run-time — follows the same contract. This file defines that contract.

---

## Two classes of agents

| Class | Purpose | Examples | Invoked by |
|---|---|---|---|
| **Build-time** | Produce and maintain the skill library itself | `orchestrator`, `task-mapper`, `content-researcher`, the 4 `*-skill-builder` agents, `validator`, `currency-monitor` | Repo maintainers via `/run-queue`, scheduled task |
| **Run-time** | Use the skill library to do real Salesforce work against a user's org / codebase | `apex-refactorer`, `trigger-consolidator`, `test-class-generator`, `soql-optimizer`, `security-scanner`, `flow-analyzer`, `bulk-migration-planner`, `lwc-auditor`, `deployment-risk-scorer`, `agentforce-builder`, `org-drift-detector` | End users via slash commands, direct AGENT.md read, or MCP `get_agent` tool |

See [`RUNTIME_VS_BUILD.md`](./RUNTIME_VS_BUILD.md) for the full roster.

---

## What an AGENT.md must contain

Each agent lives at `agents/<agent-name>/AGENT.md` and MUST have these sections, in this order:

1. **What This Agent Does** — one paragraph, plain English, ends with the scope boundary.
2. **Invocation** — the three invocation modes (direct read / slash command / MCP `get_agent`) and what args the agent expects.
3. **Mandatory Reads Before Starting** — the files and skills the agent MUST read first. Always includes `AGENT_RULES.md` + any domain-specific decision trees or templates.
4. **Inputs** — structured list of what the agent needs from the caller (file paths, object names, target org alias, etc.). Ask for missing inputs up front; never guess.
5. **Plan** — numbered steps. Each step cites the skill, template, or decision tree it relies on. Steps use MCP tools where the agent needs live-org data.
6. **Output Contract** — exactly what the agent returns. Format (markdown report, generated files, PR-ready patch, etc.). Every run-time agent returns at minimum: a finding summary, a confidence score (HIGH/MEDIUM/LOW), and links to the skills/templates it used.
7. **Escalation / Refusal Rules** — conditions under which the agent stops and asks a human. At minimum: missing org connection when one is required, ambiguous inputs, contradicting skills (resolved per `standards/source-hierarchy.md`).
8. **What This Agent Does NOT Do** — explicit non-goals. Prevents scope creep.

---

## Rules every agent follows

1. **Skill-first, never freestyle.** If `search_skill` or `get_skill` returns a matching skill, the agent MUST use that skill's guidance. If no skill matches, the agent MAY freestyle but MUST flag `confidence: LOW` and suggest adding the missing skill via `/request-skill`.

2. **Templates are canonical.** When generating Apex / LWC / Flow / Agentforce scaffolds, reference the file under `templates/` — never inline a parallel implementation. If a template is incomplete for the use case, flag it in the report instead of freestyling.

3. **Decision trees route technology choices.** If the user's request involves picking between automation / async / integration / sharing mechanisms, the agent MUST consult the matching file under `standards/decision-trees/` and cite which branch it followed.

4. **Source hierarchy for contradictions.** When skills disagree, Tier 1 (official Salesforce docs) wins. Per `standards/source-hierarchy.md`.

5. **Org-aware where possible.** If an MCP target-org is connected, the agent SHOULD call `describe_org` / `list_custom_objects` / `list_flows_on_object` / `validate_against_org` to ground recommendations in reality. If no org is connected, the agent MUST say so in the output and continue in "library-only" mode.

6. **No hidden side effects.** Run-time agents NEVER deploy to an org, NEVER run `sf project deploy`, NEVER mutate files outside the paths the user gave as input. They produce plans, patches, and reports — execution is the human's call.

7. **One agent per invocation.** No auto-chaining. If another agent would help, recommend it in the output; don't silently invoke it.

8. **Return a report the user can paste into a PR.** Every output ends with a "Citations" block listing every skill id, template path, and decision tree branch the agent consulted.

---

## Anti-patterns

- ❌ Reading `skills/` by globbing. Use `search_skill` or `get_skill` — they respect the registry.
- ❌ Inlining Apex patterns from memory. Use `templates/apex/*.cls`.
- ❌ Recommending a technology without citing the decision tree.
- ❌ Returning "HIGH confidence" without at least one official Salesforce docs citation in the skill's `references/`.
- ❌ Running `sf project deploy`, `sf data upsert`, or any write operation against the org.

---

## Testing an agent

Before a new AGENT.md is merged, it must pass:

1. **Structural gate** — `python3 scripts/validate_repo.py --agents` passes (TBD: currently structural checks live in the skill validator; extending to agents is future work).
2. **Citation gate** — every skill / template / decision tree the AGENT.md mentions must exist at the cited path.
3. **Dry-run gate** — the maintainer runs the agent's plan against a sample input and checks that the output contract is respected.

See [`commands/review.md`](../../commands/review.md) for the review flow.
