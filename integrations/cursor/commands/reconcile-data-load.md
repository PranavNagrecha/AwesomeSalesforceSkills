---
name: reconcile-data-load
description: Explain whether a data migration reconciled, where rows or relationships were lost, and which checks to run next. Read-only. Fixture-first via get_data_load_result.
---

# /reconcile-data-load

Coordinate these Cursor subagents in order. Pass structured handoffs only (no transcripts):

1. `sf-org-grounder` — fixture file **or** `get_data_load_result(result_path)`
2. `sf-project-inspector` — **optional** local DX project discovery
3. `sf-context-librarian` — select ≤8 domain skill/reference files (hard limit 12)
4. `data-migration-reconciler` — diagnose
5. `sf-evidence-reviewer` — reject unsupported/unsafe claims

Then follow `agents/data-migration-reconciler/AGENT.md` output contract.

## Safety

Do not deploy, DML, or change permissions.
Show verification commands; do not execute them.
