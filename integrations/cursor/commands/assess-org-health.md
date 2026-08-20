---
name: assess-org-health
description: Produce an evidence-backed health roadmap across Trusted, Easy, and Adaptable dimensions without a fake single score. Read-only. Fixture-first via get_org_snapshot_manifest.
---

# /assess-org-health

Coordinate these Cursor subagents in order. Pass structured handoffs only (no transcripts):

1. `sf-org-grounder` — fixture file **or** `get_org_snapshot_manifest(result_path)`
2. `sf-project-inspector` — **optional** local DX project discovery
3. `sf-context-librarian` — select ≤8 domain skill/reference files (hard limit 12)
4. `org-health-assessor-v2` — diagnose
5. `sf-evidence-reviewer` — reject unsupported/unsafe claims

Then follow `agents/org-health-assessor-v2/AGENT.md` output contract.

## Safety

Do not deploy, DML, or change permissions.
Show verification commands; do not execute them.
