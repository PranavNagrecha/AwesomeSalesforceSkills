---
name: review-security-posture
description: Assess a named Salesforce scope for evidence-backed access, code, session, and integration risks. Read-only. Fixture-first via get_code_analysis_result.
---

# /review-security-posture

Coordinate these Cursor subagents in order. Pass structured handoffs only (no transcripts):

1. `sf-org-grounder` — fixture file **or** `get_code_analysis_result(result_path)`
2. `sf-project-inspector` — **optional** local DX project discovery
3. `sf-context-librarian` — select ≤8 domain skill/reference files (hard limit 12)
4. `security-posture-reviewer` — diagnose
5. `sf-evidence-reviewer` — reject unsupported/unsafe claims

Then follow `agents/security-posture-reviewer/AGENT.md` output contract.

## Safety

Do not deploy, DML, or change permissions.
Show verification commands; do not execute them.
