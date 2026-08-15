# Migration Guide — SfSkills Agent Consolidation

Permanent record of every agent retired during the Wave 3 consolidation: what
replaced it, how to migrate, and what state each redirect is in today.

## Deprecation Principles

1. **Every retired agent leaves behind a stub `AGENT.md`** with
   `status: deprecated` and `deprecated_in_favor_of: <replacement-id>`, unless
   the agent was deleted outright (noted per row below).
2. **Legacy slash-commands ship as aliases** pointing at the canonical router
   command with a preset parameter. An alias body begins "LEGACY ALIAS".
3. **No behavior is dropped.** Every rule from every retired agent is preserved
   in the replacement's decision table or classifier, so a reviewer can trace
   rule-by-rule equivalence.
4. **What the validator actually enforces.** `pipelines/agent_validators.py`
   validates each `AGENT.md`'s frontmatter against
   `agents/_shared/schemas/agent-frontmatter.schema.json`, whose `allOf` block
   makes `deprecated_in_favor_of` **required** when `status: deprecated`. So a
   stub without a replacement pointer fails the build.
   `mcp/sfskills-mcp/tests/test_agent_frontmatter.py` asserts the same thing
   independently.

   Deprecated stubs are also relaxed on structure: they need only `Plan` and
   `What This Agent Does NOT Do`, not the full 8-section runtime shape.

   > **Not enforced:** there is no gate that an alias command points at a
   > router that exists. The gate runs the other way — every `class: runtime`,
   > non-deprecated agent must have some `commands/*.md` whose body links
   > `agents/<id>/AGENT.md` (ERROR at `pipelines/agent_validators.py:661`). An
   > alias whose target router was deleted would not be caught. Check alias
   > targets by hand when retiring a router.

## Wave 3a — Automation Migration Router

4 retired migrators → 1 canonical router. Agent directories **deleted**;
stubs and aliases removed early (see below).

| Retired agent (deleted) | Replacement | Old slash-command (deleted) | Canonical form |
|---|---|---|---|
| `workflow-rule-to-flow-migrator` | `automation-migration-router` | `/migrate-wfr-to-flow` | `/automation-migration-router --source-type=wf_rule` |
| `process-builder-to-flow-migrator` | `automation-migration-router` | `/migrate-pb-to-flow` | `/automation-migration-router --source-type=process_builder` |
| `approval-to-flow-orchestrator-migrator` | `automation-migration-router` | `/migrate-approval-to-orchestrator` | `/automation-migration-router --source-type=approval_process` |
| `workflow-and-pb-migrator` (pre-Wave-3 deprecated) | `automation-migration-router` | `/migrate-workflow-pb` | `/automation-migration-router --source-type=auto` |

**Where the rule set lives now:**
[`agents/_shared/harnesses/migration_router/decision_table.md`](../agents/_shared/harnesses/migration_router/decision_table.md).
Each retired agent's classification tables, refusal conditions, and mandatory
reads are preserved in the corresponding `source_type` row.

**Removal:** originally targeted two minor versions after commit `cf0c4813d`
(2026-04-17, "Wave 3a: automation-migration-router (replaces 4 migrators)").
The stubs and aliases were removed on 2026-04-27, early, because no consumers
remained on the legacy invocations. Verified: none of the four agent
directories and none of the four command files exist today. The old paths now
produce a not-found error.

## Wave 3b — Audit Router

15 retired auditors → 1 canonical router with 15 per-domain classifiers. 14
deprecation stubs remain under `agents/`; `approval-process-auditor` was
deleted outright.

### Wave 3b-1 (5 auditors, commit `1db5b8194`, 2026-04-17)

| Retired agent | Domain | Slash-command alias | Canonical form |
|---|---|---|---|
| `validation-rule-auditor` | `validation_rule` | `/audit-validation-rules` (ships) | `/audit-router --domain=validation_rule` |
| `picklist-governor` | `picklist` | `/govern-picklists` (ships) | `/audit-router --domain=picklist` |
| `approval-process-auditor` *(agent deleted 2026-04-27)* | `approval_process` | `/audit-approvals` *(deleted)* | `/audit-router --domain=approval_process` |
| `record-type-and-layout-auditor` | `record_type_layout` | `/audit-record-types` (ships) | `/audit-router --domain=record_type_layout` |
| `report-and-dashboard-auditor` | `report_dashboard` | `/audit-reports` (ships) | `/audit-router --domain=report_dashboard` |

### Wave 3b-2 (10 auditors, commit `03810f783`, 2026-04-17)

| Retired agent | Domain | Slash-command alias | Canonical form |
|---|---|---|---|
| `case-escalation-auditor` | `case_escalation` | `/audit-case-escalation` (ships) | `/audit-router --domain=case_escalation` |
| `lightning-record-page-auditor` | `lightning_record_page` | `/audit-record-page` (ships) | `/audit-router --domain=lightning_record_page` |
| `sharing-audit-agent` | `sharing` | `/audit-sharing` (ships) | `/audit-router --domain=sharing` |
| `org-drift-detector` | `org_drift` | `/detect-drift` (ships) | `/audit-router --domain=org_drift` |
| `prompt-library-governor` | `prompt_library` | `/govern-prompt-library` (ships) | `/audit-router --domain=prompt_library` |
| `list-view-and-search-layout-auditor` | `list_view_search_layout` | `/audit-list-views` *(removed)* | `/audit-router --domain=list_view_search_layout` |
| `quick-action-and-global-action-auditor` (audit mode only) | `quick_action` | `/audit-actions` *(removed)* | `/audit-router --domain=quick_action` |
| `reports-and-dashboards-folder-sharing-auditor` | `reports_dashboards_folder_sharing` | `/audit-report-folder-sharing` *(removed)* | `/audit-router --domain=reports_dashboards_folder_sharing` |
| `field-audit-trail-and-history-tracking-governor` | `field_audit_trail_history_tracking` | `/govern-field-history` *(removed)* | `/audit-router --domain=field_audit_trail_history_tracking` |
| `my-domain-and-session-security-auditor` | `my_domain_session_security` | `/audit-identity-and-session` *(removed)* | `/audit-router --domain=my_domain_session_security` |

Alias state above was verified by listing `commands/`: 9 of the 15 aliases
still ship. Five were removed on 2026-05-08 in commit `014a069b3` ("infra: P0
FTS5 sanitizer fix + remove 6 deprecated commands" — the sixth was
`run-queue.md`), and `/audit-approvals` went with its agent on 2026-04-27 in
commit `d7edef137`. All 15 domains remain reachable through
`/audit-router --domain=<value>`.

**Where the rule set lives now:**
[`agents/_shared/harnesses/audit_harness/classifiers/<domain>.md`](../agents/_shared/harnesses/audit_harness/classifiers/)
— 15 files, one per domain. Each retired auditor's rule table, severity tiers,
patch templates, and refusal conditions are preserved there.

**Finding code prefixes** (for cross-run rollups):
`VR_*` (validation_rule), `PICKLIST_*`, `APPROVAL_*`, `RT_*`
(record_type_layout), `REPORT_*` / `DASHBOARD_*`, `CASE_*` (case_escalation),
`LRP_*` (lightning_record_page), `LV_*` / `SL_*` (list_view_search_layout),
`QA_*` (quick_action), `FOLDER_*` (reports_dashboards_folder_sharing),
`FAT_*` (field_audit_trail_history_tracking), `SHARE_*` (sharing),
`DRIFT_*` (org_drift), `MD_*` / `MFA_*` / `SESSION_*` / `PWD_*` / `IP_*` /
`LH_*` / `CA_*` (my_domain_session_security), `PROMPT_*` (prompt_library).

The retired `agents/<name>/` directories still exist as reference stubs.
`agents/_shared/RUNTIME_VS_BUILD.md`, `agents/audit-router/AGENT.md`, and
`agents/orchestrator/AGENT.md` continue to reference them as the canonical
mapping.

**Unfinished forward reference.**
`agents/quick-action-and-global-action-auditor/AGENT.md` says its *design* mode
"migrates separately to Wave 3c's `designer_base` harness (as
`action-designer`)". No `action-designer` agent was created, and Wave 3c
retired nothing. Quick-action **design** currently has no owning agent; only
the audit mode is routed. Treat that sentence as a plan, not a state.

## Wave 3c — Designer Base Harness

Not a consolidation. A shared-convention documentation pass — **no agents were
retired and no migration is required.** Existing slash-commands and invocation
paths continue to work; the harness is additive governance.

Agents declaring `harness: designer_base` in frontmatter inherit conventions
from
[`agents/_shared/harnesses/designer_base/`](../agents/_shared/harnesses/designer_base/README.md).
`grep '^harness:' agents/*/AGENT.md` returns **12** today:

| Original Wave 3c eight | Added since |
|---|---|
| `object-designer` | `config-workbook-author` |
| `permission-set-architect` | `omnistudio-designer` |
| `flow-builder` | `process-flow-mapper` |
| `omni-channel-routing-designer` | `story-drafter` |
| `sales-stage-designer` | |
| `lead-routing-rules-designer` | |
| `duplicate-rule-designer` | |
| `sandbox-strategy-designer` | |

`agents/_shared/harnesses/designer_base/README.md` still says "8 designer
agents" and lists only the left column. That is stale; the frontmatter is the
source of truth.

Harness compliance is enforced (`_validate_harness`,
`pipelines/agent_validators.py:436–466`): declaring an unknown harness, using
`modes` outside the designer_base set, or omitting the
`## Escalation / Refusal Rules` section is an ERROR.

## Removal Timeline

- **T+0 (Wave 3 commit)** — deprecation stubs and aliases ship; canonical
  replacements available.
- **T+1** — migration warnings become more prominent in alias output.
- **T+2** — stubs and aliases removed. This document remains as the permanent
  record.

In practice both Wave 3a and part of Wave 3b were removed **ahead** of that
schedule, on the judgement that nobody was still calling them. Do not assume a
redirect will survive to T+2; check `commands/` before depending on one.

> **There is no repository version tag to pin to.** `git tag` returns only
> `mcp-v0.4.0`, `mcp-v0.4.1`, `mcp-v0.4.4`, `mcp-v0.4.6` — all MCP package
> releases, not library versions. Earlier drafts of this document told
> consumers to "pin to a `v1.x` tag"; no such tag exists. If you need a fixed
> surface, pin to a commit SHA.

## How to Migrate a Specific Workflow

### 1. Check whether your slash-command is an alias

`ls commands/` and open the file for your command. If the body starts with
"LEGACY ALIAS", you are on a deprecated command — update the caller (bot macro,
Slack shortcut, documentation, training material) to the canonical form in the
tables above. If the file is absent entirely, the alias has already been
removed; go straight to the canonical form.

### 2. Check whether an agent you reference directly is deprecated

Read its `AGENT.md` frontmatter. If `status: deprecated`, `deprecated_in_favor_of`
names the replacement id. Update any direct-read invocations
("Follow `agents/<x>/AGENT.md`") to the replacement.

Over MCP, `list_agents(kind="deprecated")` enumerates the stubs and
`list_deprecated_redirects` resolves each to its replacement.

### 3. Rebuild registry + manifest

```bash
python3 scripts/skill_sync.py --all --skip-embeddings
python3 scripts/validate_repo.py --agents
python3 scripts/export_skills.py --check
```

Use `--skip-embeddings`: `config/retrieval-config.yaml` has embeddings enabled,
and a bare `--all` attempts a chunk-level encode measured in hours when the
cache is cold.

`validate_repo.py --agents` takes about 0.4 s and must exit 0.

`export_skills.py --check` rebuilds every export target in a scratch directory,
hashes it, and diffs against the committed baseline
`registry/export_manifest.json`. It exits non-zero whenever skills have changed
since the baseline was last regenerated, which is normal and not a migration
failure. When the diff is expected, run
`python3 scripts/export_skills.py --all --manifest`, review, and commit.

### 4. Regression-test against your existing output

The replacements preserve every rule of their predecessors, but output
formatting differs (domain-scoped finding codes, uniform envelope shape). If
you have dashboards or tooling that parses agent output, update the parser to
match
[`audit_harness/output_schema.md`](../agents/_shared/harnesses/audit_harness/output_schema.md)
or
[`migration_router/output_schema.md`](../agents/_shared/harnesses/migration_router/output_schema.md).

## FAQ

### "My Slack bot calls `/audit-validation-rules`. Will it keep working?"

That alias ships today and emits a deprecation notice. But five sibling aliases
were removed ahead of their announced window, so do not treat "ships today" as
a commitment. Move to `/audit-router --domain=validation_rule` when convenient.

### "Do deprecation stubs count toward the agent roster?"

Yes. They are 14 of the 76 `AGENT.md` files, and `list_agents()` with no filter
returns them.

Filter by `kind`, not by status: `list_agents` returns
`{name, kind, path, summary}` per agent and has no `status` field in its
output. `kind="runtime"` gives the 48 active run-time agents, `kind="build"`
the 14 build-time agents, `kind="deprecated"` the 14 stubs, and
`None` / `"all"` everything.

### "Can I extend a deprecated agent's rules?"

No. Extend the replacement's decision table or classifier. Changes to a stub
are lost when it is removed.

### "I have a custom agent that cites a deprecated agent in its Mandatory Reads"

Update the citation. `_validate_citations` ERRORs on a follow-up reference to
`agents/<id>` that does not resolve, so the build breaks as soon as the stub is
deleted.

### "What if I need the old behavior specifically?"

Pin to a commit SHA from before the removal. Better: file an issue if the
replacement genuinely regresses a capability — those are bugs.

## See Also

- [`agents/_shared/harnesses/migration_router/README.md`](../agents/_shared/harnesses/migration_router/README.md) — Wave 3a harness architecture.
- [`agents/_shared/harnesses/audit_harness/README.md`](../agents/_shared/harnesses/audit_harness/README.md) — Wave 3b harness architecture.
- [`agents/_shared/harnesses/designer_base/README.md`](../agents/_shared/harnesses/designer_base/README.md) — Wave 3c harness conventions.
- [`CHANGELOG.md`](../CHANGELOG.md) — release notes including the Wave 3 consolidation entry.
- [`agents/_shared/REFUSAL_CODES.md`](../agents/_shared/REFUSAL_CODES.md) — canonical refusal codes used across routers and classifiers.
