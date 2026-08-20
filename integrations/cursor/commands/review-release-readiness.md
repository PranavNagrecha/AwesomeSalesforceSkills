---
name: review-release-readiness
description: Given an explicit release scope, say whether it is ready, what still blocks it, and which evidence is missing. Read-only. Fixture-first via get_flow_test_result.
---

# /review-release-readiness

Coordinate these Cursor subagents in order. Pass structured handoffs only (no transcripts):

1. `sf-org-grounder` — fixture file **or** `get_flow_test_result(result_path)`
2. `sf-project-inspector` — **optional** local DX project discovery
3. `sf-context-librarian` — select ≤8 domain skill/reference files (hard limit 12)
4. `release-readiness-reviewer` — diagnose
5. `sf-evidence-reviewer` — reject unsupported/unsafe claims

Then follow `agents/release-readiness-reviewer/AGENT.md` output contract.

## Safety

Do not deploy, DML, or change permissions.
Show verification commands; do not execute them.
