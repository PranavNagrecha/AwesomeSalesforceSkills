---
name: profile-automation
description: Show which Salesforce automation runs for an object operation, in what order, and where recursion or DML amplification exists. Read-only. Fixture-first via get_automation_inventory.
---

# /profile-automation

Coordinate these Cursor subagents in order. Pass structured handoffs only (no transcripts):

1. `sf-org-grounder` — fixture file **or** `get_automation_inventory(result_path)`
2. `sf-project-inspector` — **optional** local DX project discovery
3. `sf-context-librarian` — select ≤8 domain skill/reference files (hard limit 12)
4. `automation-transaction-profiler` — diagnose
5. `sf-evidence-reviewer` — reject unsupported/unsafe claims

Then follow `agents/automation-transaction-profiler/AGENT.md` output contract.

## Safety

Do not deploy, DML, or change permissions.
Show verification commands; do not execute them.
