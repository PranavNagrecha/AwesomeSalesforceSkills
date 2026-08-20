---
name: plan-metadata-change
description: Before a metadata change, identify direct and transitive dependents, deploy order, tests, and rollback constraints. Read-only. Fixture-first via get_component_dependency_evidence.
---

# /plan-metadata-change

Coordinate these Cursor subagents in order. Pass structured handoffs only (no transcripts):

1. `sf-org-grounder` — fixture file **or** `get_component_dependency_evidence(result_path)`
2. `sf-project-inspector` — **optional** local DX project discovery
3. `sf-context-librarian` — select ≤8 domain skill/reference files (hard limit 12)
4. `change-impact-planner` — diagnose
5. `sf-evidence-reviewer` — reject unsupported/unsafe claims

Then follow `agents/change-impact-planner/AGENT.md` output contract.

## Safety

Do not deploy, DML, or change permissions.
Show verification commands; do not execute them.
