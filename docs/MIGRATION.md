# Migration Guide — SfSkills Agent Consolidation

This document records every agent deprecated during the Wave 3 consolidation (see `/Users/pranavnagrecha/.claude/plans/keen-napping-wombat.md`) — what replaced it, how to migrate, and when the deprecation stub will be removed.

## Deprecation Principles

1. **Every retired agent leaves behind a stub `AGENT.md`** with `status: deprecated` and `deprecated_in_favor_of: <replacement-id>`. Stubs stay for **two minor versions** after the Wave-3 commit that retired the source agent.
2. **Every legacy slash-command ships as an alias** pointing at the canonical router command with a preset parameter. Aliases emit a one-line deprecation notice at runtime and ship for the same two-version window.
3. **No behavior is dropped.** Every rule from every retired agent is preserved in the replacement's decision table / classifier / harness document — reviewers can trace rule-by-rule equivalence.
4. **The validator enforces the contract.** `pipelines/agent_validators.py` fails the build if a deprecated agent lacks `deprecated_in_favor_of` or if an alias command references a missing router.

## Wave 3a — Automation Migration Router

4 retired migrators → 1 canonical router. **Stubs and aliases removed early** (see Removal note below).

| Retired agent (deleted) | Replacement | Old slash-command (deleted) | Canonical form |
|---|---|---|---|
| `workflow-rule-to-flow-migrator` | `automation-migration-router` | `/migrate-wfr-to-flow` | `/automation-migration-router --source-type=wf_rule` |
| `process-builder-to-flow-migrator` | `automation-migration-router` | `/migrate-pb-to-flow` | `/automation-migration-router --source-type=process_builder` |
| `approval-to-flow-orchestrator-migrator` | `automation-migration-router` | `/migrate-approval-to-orchestrator` | `/automation-migration-router --source-type=approval_process` |
| `workflow-and-pb-migrator` (pre-Wave-3 deprecated) | `automation-migration-router` | `/migrate-workflow-pb` | `/automation-migration-router --source-type=auto` |

**Where the rule set lives now:** [`agents/_shared/harnesses/migration_router/decision_table.md`](../agents/_shared/harnesses/migration_router/decision_table.md). Each retired agent's classification tables, refusal conditions, and mandatory-reads are preserved verbatim in the corresponding `source_type` row.

**Removal:** Originally targeted two minor versions after commit `cf0c481`. The deprecation stubs (`AGENT.md` redirects) and slash-command aliases were **removed in 2026-04-27** — early — because no consumers remained on the legacy invocations. Anyone still attempting the old paths will get a not-found error pointing at this guide.

## Wave 3b — Audit Router

15 retired auditors → 1 canonical router with 15 per-domain classifiers.

### Wave 3b-1 (5 auditors, commit `1db5b81`)

| Retired agent | Domain | Slash-command alias | Canonical form |
|---|---|---|---|
| `validation-rule-auditor` | `validation_rule` | `/audit-validation-rules` | `/audit-router --domain=validation_rule` |
| `picklist-governor` | `picklist` | `/govern-picklists` | `/audit-router --domain=picklist` |
| `approval-process-auditor` *(deleted 2026-04-27)* | `approval_process` | `/audit-approvals` *(deleted)* | `/audit-router --domain=approval_process` |
| `record-type-and-layout-auditor` | `record_type_layout` | `/audit-record-types` | `/audit-router --domain=record_type_layout` |
| `report-and-dashboard-auditor` | `report_dashboard` | `/audit-reports` | `/audit-router --domain=report_dashboard` |

### Wave 3b-2 (10 auditors, commit `03810f7`)

| Retired agent | Domain | Slash-command alias | Canonical form |
|---|---|---|---|
| `case-escalation-auditor` | `case_escalation` | `/audit-case-escalation` | `/audit-router --domain=case_escalation` |
| `lightning-record-page-auditor` | `lightning_record_page` | `/audit-record-page` | `/audit-router --domain=lightning_record_page` |
| `list-view-and-search-layout-auditor` | `list_view_search_layout` | `/audit-list-views` | `/audit-router --domain=list_view_search_layout` |
| `quick-action-and-global-action-auditor` (audit mode only; design mode → Wave 3c) | `quick_action` | `/audit-actions` | `/audit-router --domain=quick_action` |
| `reports-and-dashboards-folder-sharing-auditor` | `reports_dashboards_folder_sharing` | `/audit-report-folder-sharing` | `/audit-router --domain=reports_dashboards_folder_sharing` |
| `field-audit-trail-and-history-tracking-governor` | `field_audit_trail_history_tracking` | `/govern-field-history` | `/audit-router --domain=field_audit_trail_history_tracking` |
| `sharing-audit-agent` | `sharing` | `/audit-sharing` | `/audit-router --domain=sharing` |
| `org-drift-detector` | `org_drift` | `/detect-drift` | `/audit-router --domain=org_drift` |
| `my-domain-and-session-security-auditor` | `my_domain_session_security` | `/audit-identity-and-session` | `/audit-router --domain=my_domain_session_security` |
| `prompt-library-governor` | `prompt_library` | `/govern-prompt-library` | `/audit-router --domain=prompt_library` |

**Where the rule set lives now:** [`agents/_shared/harnesses/audit_harness/classifiers/<domain>.md`](../agents/_shared/harnesses/audit_harness/classifiers/). Each retired auditor's rule table, severity tiers, patch templates, and refusal conditions are preserved verbatim in the corresponding classifier.

**Finding code prefixes** (for cross-run rollups):
- `VR_*` (validation_rule), `PICKLIST_*`, `APPROVAL_*`, `RT_*` (record_type_layout), `REPORT_*` / `DASHBOARD_*`, `CASE_*` (case_escalation), `LRP_*` (lightning_record_page), `LV_*` / `SL_*` (list_view_search_layout), `QA_*` (quick_action), `FOLDER_*` (reports_dashboards_folder_sharing), `FAT_*` (field_audit_trail_history_tracking), `SHARE_*` (sharing), `DRIFT_*` (org_drift), `MD_*` / `MFA_*` / `SESSION_*` / `PWD_*` / `IP_*` / `LH_*` / `CA_*` (my_domain_session_security), `PROMPT_*` (prompt_library).

**Removal target:** two minor versions after commit `03810f7` (Wave 3b-2 ship).

## Wave 3c — Designer Base Harness

Not a consolidation — a shared-convention documentation pass for 8 designer agents. NO AGENTS WERE RETIRED. Each of these 8 agents now declares `harness: designer_base` in frontmatter and inherits conventions from [`agents/_shared/harnesses/designer_base/`](../agents/_shared/harnesses/designer_base/README.md):

- `object-designer`
- `permission-set-architect`
- `flow-builder`
- `omni-channel-routing-designer`
- `sales-stage-designer`
- `lead-routing-rules-designer`
- `duplicate-rule-designer`
- `sandbox-strategy-designer`

**No migration required.** Existing slash-commands and invocation paths continue to work. The harness is additive governance.

## Removal Timeline

- **T+0 (Wave 3 commit)** — Deprecation stubs and aliases ship. Canonical replacements are available.
- **T+1 minor version** — Migration warnings become more prominent in alias output.
- **T+2 minor versions** — Stubs + aliases removed. The `docs/MIGRATION.md` table (this doc) remains as the permanent record.

"Minor version" maps to the Salesforce 4-month release cadence if the consumer chooses to pin to a release. Open-source consumers should use tags: the stubs/aliases are tied to the `v1.x` major version; `v2.x` will drop them.

## How to Migrate a Specific Workflow

### 1. Check if your slash-command is aliased

Run `ls commands/` or search for your command. If you find a file whose body starts with "LEGACY ALIAS", you are on a deprecated command. Update the caller (bot macro, Slack shortcut, documentation, training materials) to the canonical form listed in the alias file.

### 2. Check if an agent you directly reference is deprecated

Read the `AGENT.md` frontmatter. If `status: deprecated`, check `deprecated_in_favor_of` for the replacement id. Update any direct-read invocations (e.g. "Follow `agents/<x>/AGENT.md`") to the replacement.

### 3. Rebuild registry + manifest

After migrating off deprecated paths:

```bash
python3 scripts/skill_sync.py --all
python3 scripts/validate_repo.py --agents
python3 scripts/export_skills.py --check
```

All three should exit clean. If `--check` reports drift, run `python3 scripts/export_skills.py --all --manifest` to regenerate the baseline, review the diff, and commit.

### 4. Regression-test against your existing output

The replacement agents preserve every rule of their predecessors, but output formatting differs (domain-scoped finding codes, uniform envelope shape). If you have dashboards / tooling that parses agent output, update the parser to match the new format documented in [`agents/_shared/harnesses/audit_harness/output_schema.md`](../agents/_shared/harnesses/audit_harness/output_schema.md) or [`agents/_shared/harnesses/migration_router/output_schema.md`](../agents/_shared/harnesses/migration_router/output_schema.md).

## FAQ

### "My Slack bot calls `/audit-validation-rules`. Will it keep working?"

Yes, through at least two minor versions. It will emit a one-line deprecation notice in the output. Update the bot at your convenience; after T+2 it will fail.

### "Do deprecation stubs count toward the agent roster?"

Yes — they remain in `list_agents()` output. The `status` field lets downstream tooling filter. Consumers looking for production-ready agents should filter `status == stable`.

### "Can I extend a deprecated agent's rules?"

No. Extend the replacement's decision table or classifier. If you extend the deprecated stub, your changes will be lost at T+2.

### "I have a custom agent that cites a deprecated agent in its Mandatory Reads"

Update the citation. The validator's citation gate will fail once the stub is removed at T+2.

### "What if I need the old behavior specifically?"

Pin to a `v1.x` tag and don't upgrade past the removal version. Better: file an issue if the replacement's behavior genuinely regresses a capability — those are bugs we'll fix.

## See Also

- [`agents/_shared/harnesses/migration_router/README.md`](../agents/_shared/harnesses/migration_router/README.md) — Wave 3a harness architecture.
- [`agents/_shared/harnesses/audit_harness/README.md`](../agents/_shared/harnesses/audit_harness/README.md) — Wave 3b harness architecture.
- [`agents/_shared/harnesses/designer_base/README.md`](../agents/_shared/harnesses/designer_base/README.md) — Wave 3c harness conventions.
- [`CHANGELOG.md`](../CHANGELOG.md) — release notes including the Wave 3 consolidation entry.
- [`agents/_shared/REFUSAL_CODES.md`](../agents/_shared/REFUSAL_CODES.md) — canonical refusal codes used across routers and classifiers.
