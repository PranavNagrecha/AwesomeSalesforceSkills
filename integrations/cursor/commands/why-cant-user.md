---
name: why-cant-user
description: Explain why a specific Salesforce user can or cannot perform an operation on a named resource, layer by layer. Read-only. Fixture-first via get_user_access_evidence.
---

# /why-cant-user

Coordinate these Cursor subagents in order. Pass structured handoffs only (no transcripts):

1. `sf-org-grounder` — fixture file **or** `get_user_access_evidence(result_path)`
2. `sf-project-inspector` — **optional** local DX project discovery
3. `sf-context-librarian` — select ≤8 domain skill/reference files (hard limit 12)
4. `access-path-explainer` — diagnose
5. `sf-evidence-reviewer` — reject unsupported/unsafe claims

Then follow `agents/access-path-explainer/AGENT.md` output contract.

## Safety

Do not deploy, DML, or change permissions.
Show verification commands; do not execute them.
