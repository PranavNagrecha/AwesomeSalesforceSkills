---
name: triage-integration
description: Correlate Salesforce and supplied integration evidence to classify an incident and the failing boundary. Read-only. Fixture-first via get_integration_config_summary.
---

# /triage-integration

Coordinate these Cursor subagents in order. Pass structured handoffs only (no transcripts):

1. `sf-org-grounder` — fixture file **or** `get_integration_config_summary(result_path)`
2. `sf-project-inspector` — **optional** local DX project discovery
3. `sf-context-librarian` — select ≤8 domain skill/reference files (hard limit 12)
4. `integration-incident-triager` — diagnose
5. `sf-evidence-reviewer` — reject unsupported/unsafe claims

Then follow `agents/integration-incident-triager/AGENT.md` output contract.

## Safety

Do not deploy, DML, or change permissions.
Show verification commands; do not execute them.
