# Agent Eval Framework

This file defines the fixture schema and scoring rubric for agent evals. The runner at `evals/agents/scripts/run_agent_evals.py` is the reference implementation.

## Fixture schema

Each fixture is a single YAML document under `evals/agents/fixtures/<agent-slug>/<case-id>.yaml` with four top-level sections: `eval`, `inputs`, `org_stub`, `expect`.

### `eval` — fixture metadata (required)

| Key | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Globally unique (`<agent>__<case-id>`). |
| `agent` | string | yes | Must be a real folder under `agents/`. |
| `mode` | string | yes | Must be one of the modes declared in the agent's frontmatter.modes. |
| `priority` | string | yes | `P0` \| `P1` \| `P2`. P0 cases block release. |
| `last_verified` | date | yes | ISO date of the last time a human confirmed the expected outputs are still correct. |
| `description` | string | no | One-line human description. |

### `inputs` — agent input packet (required)

Free-form object matching the agent's `inputs.schema.json` when one exists. When the agent has no inputs schema yet, the eval runner only lints for presence and logs a `WARN`.

### `org_stub` — org-state fixture (optional)

Structured stub of the live-org data the agent would otherwise fetch via MCP. Keys are free-form but follow conventions per domain:

- `apex_hits`, `flow_hits`, `matching_rule_hits`, `duplicate_rule_hits` — arrays of probe hits the agent would have fetched.
- `ps_assignments`, `ps_composition` — for permission agents.
- `org_metadata` — `describe_org` response body.

If the fixture omits `org_stub`, the runner assumes the agent is expected to refuse per `REFUSAL_ORG_UNREACHABLE` (useful for refusal-path cases).

### `expect` — what the envelope must look like (required)

All keys are optional; absent keys simply aren't checked. Present keys are all enforced.

| Key | Type | Meaning |
|---|---|---|
| `confidence` | `HIGH` \| `MEDIUM` \| `LOW` | Exact match required. |
| `refusal_code` | string | Envelope must have a `refusal.code` equal to this. Mutually exclusive with deliverable expectations below. |
| `must_include_findings_with_any_of_ids` | array<string> | At least one `findings[].id` must match. |
| `must_include_findings_with_all_of_ids` | array<string> | Every id listed must appear in `findings[].id`. |
| `must_not_include_findings_with_ids` | array<string> | None of these may appear. |
| `must_cite_any_of` | array<{type,id}> | At least one matching citation required. |
| `must_cite_all_of` | array<{type,id}> | Every listed citation must appear. |
| `must_not_cite_probes` | array<string> | Listed probe ids must NOT appear as citations. |
| `process_observations.min_count` | integer | Minimum number of observations. |
| `process_observations.categories_present_any_of` | array<string> | At least one observation must match one of these categories. |
| `followups_include_any_of` | array<string> | Recommended `followups[].agent` slugs. |

## Scoring rubric

| Outcome | Points | Gate |
|---|---|---|
| Envelope validates against `output-envelope.schema.json` | +1 | P0 |
| Every `expect.*` check passes | +1 each | P0 |
| Citations in the envelope resolve to real paths/tool names | +1 | P0 |
| Confidence rationale is present when confidence != HIGH | +1 | P1 |
| Process observations are non-empty when the fixture has `org_stub` | +1 | P1 |

A fixture is **pass** iff every P0 item scores its point. Failing any P0 on a P0 fixture returns exit code 2.

## When an eval fails

1. First triage: structural lint, envelope validity, schema resolution.
2. If the lint is clean but the agent produced wrong findings, re-read the agent's AGENT.md against the rubric expectations. One of the two is drifting.
3. Do NOT loosen the fixture to make the agent pass unless a human reviewer confirms the fixture was wrong. The default assumption is "the agent changed and it shouldn't have".

## Relationship to skill evals

| Scope | Skill evals | Agent evals |
|---|---|---|
| Input | a single user prompt | a structured input packet + org stub |
| Output | free-text + code samples | a structured output envelope |
| Grade via | LLM rubric grader | deterministic envelope match |
| Lives in | `evals/golden/` | `evals/agents/fixtures/` |
| Blocks release on | P0 fail | P0 fail |

The two are complementary: skill evals grade "does this skill generate good code"; agent evals grade "does this agent compose skills into a reliable deliverable".
