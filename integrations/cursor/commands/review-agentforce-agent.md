---
name: review-agentforce-agent
description: Review an Agentforce agent, topics, actions, grounding, guardrails, and tests for correctness and release readiness. Read-only. Fixture-first via get_agentforce_test_result.
---

# /review-agentforce-agent

Coordinate these Cursor subagents in order. Pass structured handoffs only (no transcripts):

1. `sf-org-grounder` — fixture file **or** `get_agentforce_test_result(result_path)`
2. `sf-project-inspector` — **optional** local DX project discovery
3. `sf-context-librarian` — select ≤8 domain skill/reference files (hard limit 12)
4. `agentforce-quality-engineer` — diagnose
5. `sf-evidence-reviewer` — reject unsupported/unsafe claims

Then follow `agents/agentforce-quality-engineer/AGENT.md` output contract.

## Safety

Do not deploy, DML, or change permissions.
Show verification commands; do not execute them.
