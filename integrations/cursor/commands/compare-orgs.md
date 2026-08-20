---
name: compare-orgs
description: Compare two explicit org snapshots and separate expected environmental differences from dangerous configuration drift. Read-only. Fixture-first via compare_org_snapshots.
---

# /compare-orgs

Coordinate these Cursor subagents in order. Pass structured handoffs only (no transcripts):

1. `sf-org-grounder` — fixture file **or** `compare_org_snapshots(result_path)`
2. `sf-project-inspector` — **optional** local DX project discovery
3. `sf-context-librarian` — select ≤8 domain skill/reference files (hard limit 12)
4. `multi-org-drift-analyzer` — diagnose
5. `sf-evidence-reviewer` — reject unsupported/unsafe claims

Then follow `agents/multi-org-drift-analyzer/AGENT.md` output contract.

## Safety

Do not deploy, DML, or change permissions.
Show verification commands; do not execute them.
