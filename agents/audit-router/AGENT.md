---
id: audit-router
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-17
updated: 2026-04-17
default_output_dir: "docs/reports/audit-router/"
output_formats:
  - markdown
  - json
multi_dimensional: true
dependencies:
  skills:
    - admin/agent-output-formats
    - admin/analytics-permission-and-sharing
    - admin/approval-process-apex-patterns
    - admin/cpq-approval-workflows
    - admin/custom-button-to-action-migration
    - admin/data-export-service
    - admin/global-actions-and-quick-actions
    - admin/global-search-configuration
    - admin/lightning-experience-transition
    - admin/list-views-and-compact-layouts
    - admin/picklist-data-integrity
    - admin/record-type-id-management
    - admin/related-list-configuration
    - admin/report-performance-tuning
    - admin/report-type-strategy
    - admin/reports-and-dashboards
    - admin/reports-and-dashboards-fundamentals
    - devops/metadata-diff-between-sandboxes
    - security/dynamic-sharing-recalculation
    - security/guest-user-security-audit
    - security/sso-saml-troubleshooting
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
---
# Audit Router Agent

## What This Agent Does

Dispatches one of the audit domains in the [`audit_harness`](../_shared/harnesses/audit_harness/README.md) into its domain-specific classifier, returning a uniform output envelope: inventory + findings (P0/P1/P2 with domain-scoped codes) + optional mechanical patches + Process Observations + citations. Replaces 15 single-mode auditor agents whose logic was 80% duplicated boilerplate. Wave 3b-1 shipped 5 domains; Wave 3b-2 adds the remaining 10 for a total of 15 audit surfaces through one router.

**Scope:** one `--domain` per invocation. Output is a review-ready plan; the router never modifies org metadata and never deploys.

---

## Invocation

- **Direct read** — "Follow `agents/audit-router/AGENT.md` with domain=validation_rule for Opportunity"
- **Slash command** — [`/audit-router`](../../commands/audit-router.md). Legacy aliases for all 15 retired auditors (e.g. `/audit-validation-rules`, `/govern-picklists`, `/audit-approvals`, `/audit-record-types`, `/audit-reports`, `/audit-case-escalation`, `/audit-record-page`, `/audit-list-views`, `/audit-actions`, `/audit-report-folder-sharing`, `/govern-field-history`, `/audit-sharing`, `/detect-drift`, `/audit-identity-and-session`, `/govern-prompt-library`) each invoke the router with a preset `--domain` and emit a one-line deprecation notice. Aliases ship until the removal window declared in `docs/MIGRATION.md` (Wave 7).
- **MCP** — `get_agent("audit-router")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md` § Run-time Agents — the repo-wide hard rules this run is bound by: never write to the org, never auto-chain to another agent, never cite a skill path that does not resolve. `AGENT_CONTRACT.md` says what this file must contain; `AGENT_RULES.md` says what the agent may do while executing it.
3. `agents/_shared/harnesses/audit_harness/README.md`
4. `agents/_shared/harnesses/audit_harness/output_schema.md`
5. `agents/_shared/harnesses/audit_harness/severity_rubric.md`
6. `agents/_shared/harnesses/audit_harness/classifier_contract.md`
7. The domain's classifier at `agents/_shared/harnesses/audit_harness/classifiers/<domain>.md` — read entirely before running any probe.
8. The **Mandatory Reads** block inside that classifier — every skill / template listed there is a hard requirement for this run.
9. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)
10. `skills/devops/metadata-diff-between-sandboxes` — two-org metadata diff for org_drift classifier
11. `skills/admin/lightning-experience-transition` — Lightning Experience Transition program orchestration — when an LE-Transition or readiness-check audit is requested, route to this skill for asset triage and wave planning instead of a single-page LRP audit
12. `skills/admin/data-export-service` — Data Export Service vs real backup gap — flag any 'we have backups via weekly export' claim
13. `skills/admin/report-type-strategy` — Custom report types, with/without joins, report type strategy
14. `skills/security/guest-user-security-audit` — Experience Cloud guest user 2021 changes audit
15. `skills/security/sso-saml-troubleshooting` — SAML response inspection, SSO debugging (my_domain_session_security)
16. `skills/admin/analytics-permission-and-sharing` — CRM Analytics apps and datasets are gated by row-level security predicates, not by the report-folder sharing the router just audited; without it the run closes a PII-exposure finding on the folder surface while the same data stays open through an Analytics dataset
17. `skills/admin/approval-process-apex-patterns` — supplies the `ProcessInstance` / `ProcessInstanceWorkitem` query shape the `approval_process` inventory needs; without it `APPROVAL_STALE_INFLIGHT` and `APPROVAL_INACTIVE_WITH_PENDING` have no way to count pending requests and both silently report zero
18. `skills/admin/cpq-approval-workflows` — a negative check: on a CPQ org the approval logic lives in `SBAA__ApprovalRule__c` records that a `ProcessDefinition` inventory cannot see; without it the router reports an approval surface as thin when most of it is in the managed package it is about to refuse
19. `skills/admin/custom-button-to-action-migration` — supplies the `suggested_fix` behind `QA_VF_ORPHANED`, `QA_VF_BACKED_DEEMPHASIZED` and `QA_DUPLICATES_STANDARD`; without it those three codes name a migration target with no route to it, and the JavaScript-button cases get a fix that cannot be implemented
20. `skills/admin/global-actions-and-quick-actions` — the `quick_action` domain's object model: which action types exist, how predefined values and action layouts are built; without it the router cannot tell a headless action legitimately carrying no layout from the `QA_NO_LAYOUT` P0 it is meant to raise
21. `skills/admin/list-views-and-compact-layouts` — the `list_view_search_layout` domain's object model, including the sharing modes a list view can carry; without it the router reads "visible to All Users" as a display setting rather than the data-exposure finding it is
22. `skills/admin/picklist-data-integrity` — restricted-vs-unrestricted, GVS-vs-local and the per-record-type value model behind `PICKLIST_NOT_RESTRICTED`, `PICKLIST_GVS_ELIGIBLE` and `PICKLIST_UNUSED_VALUE`; without it the router flags every unrestricted picklist alike and misses that deactivating a value breaks the reports already filtering on it
23. `skills/admin/record-type-id-management` — record types get referenced by hard-coded 18-character Id as often as by DeveloperName; without it the reference scan behind `RT_INACTIVE_REFERENCED` misses every Id-literal reference and the router recommends retiring an RT under `RT_ORPHAN` that Apex and Flow still point at
24. `skills/admin/report-performance-tuning` — the selectivity model behind the `report_dashboard` row-limit checks; without it the router scores every large report as a performance finding instead of separating an unselective filter from a legitimately large result set
25. `skills/admin/reports-and-dashboards` — dashboard running-user posture is the finding both report domains turn on; without it the router reads a narrowly-shared folder as safe and misses that a "run as specified user" dashboard bypasses the viewer's access entirely
26. `skills/admin/reports-and-dashboards-fundamentals` — the report type decides which rows a report can ever return; without it the router scores a zero-row report as stale when the actual defect is a with-child report type on an object whose children were never created
27. `skills/security/dynamic-sharing-recalculation` — the operational content behind `SHARE_RECALC_COST_HIGH`'s suggested fix; without it the router reports a recalculation cost with no advice on how the recalc is actually triggered or sequenced, and the finding cannot be acted on
28. `skills/admin/global-search-configuration` — search-layout and searchable-field settings the list-view and record-page audit domains both depend on
29. `skills/admin/related-list-configuration` — related-list scope for the record-page audit domain — a page can look clean while its related lists carry the debt

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `domain` | yes | 15 values: `validation_rule`, `picklist`, `approval_process`, `record_type_layout`, `report_dashboard`, `case_escalation`, `lightning_record_page`, `list_view_search_layout`, `quick_action`, `reports_dashboards_folder_sharing`, `field_audit_trail_history_tracking`, `sharing`, `org_drift`, `my_domain_session_security`, `prompt_library` |
| `target_org_alias` | yes | `prod`, `uat` |
| `object_name` | conditional — required by `validation_rule` / `record_type_layout`; optional for `picklist` / `approval_process` | `Opportunity` |
| `audit_scope` | conditional — for `approval_process` | `org` \| `object:<Name>` \| `process:<Name>` |
| `scope` | conditional — for `picklist` | `object:<Name>` \| `org` |
| `folder_filter` | optional — for `report_dashboard` | `Sales_Dashboards` |
| Domain-specific | optional | See the classifier's `Inputs` table |

If a required input is missing, STOP and ask — never guess.

---

## Plan

### Step 1 — Resolve the classifier

Read `classifiers/<domain>.md`. Confirm every skill / template / probe it cites resolves (the validator's citation gate enforces this at PR time; at runtime the router still verifies via `search_skill`). If any citation is unresolvable, STOP with `REFUSAL_NEEDS_HUMAN_REVIEW` and the missing-skill id.

### Step 2 — Inventory (harness Phase 1)

Run every probe the classifier's `Inventory Probe` section lists. Emit the `Inventory` table per `output_schema.md` — minimum columns `id`, `name`, `active` plus the domain-specific columns the classifier declares.

If inventory returns zero rows, STOP with `REFUSAL_OUT_OF_SCOPE` and a "nothing to audit" summary.

### Step 3 — Classify (harness Phase 2)

Walk every row against every check in the classifier's `Rule Table`. For each triggered check, emit a finding row with all 7 required fields (`code`, `severity`, `subject_id`, `subject_name`, `description`, `evidence`, `suggested_fix`). Every `code` must appear in the classifier's Rule Table — the router MAY NOT invent codes.

### Step 4 — Patches (harness Phase 3, optional)

If the classifier has a `Patches` section and any finding maps to a patch template, emit the filled-in patch in the `Patches` block of the output envelope. Each patch's header comments (`<!-- target: ... -->` / `<!-- addresses: ... -->` / `<!-- cites: ... -->`) must be literal. Empty patches block if no classifier patches or no matching findings.

### Step 5 — Process Observations + Citations (harness Phase 4 + 5)

Per AGENT_CONTRACT: healthy / concerning / ambiguous / suggested-follow-ups. Each observation cites the evidence the agent was looking at when it noticed the pattern. Every skill / template / decision-tree / MCP tool / probe the run consulted lands in Citations.

---

## Output Contract

Conforms to [`output_schema.md`](../_shared/harnesses/audit_harness/output_schema.md). At minimum:

1. **Summary** — domain, target_org_alias, scope, inventory_count, P0/P1/P2 counts, max severity, confidence.
2. **Inventory** — id / name / active + domain-specific columns.
3. **Findings** — one row per finding with all 7 strict fields.
4. **Patches** — optional; included only when the classifier produces mechanical patches.
5. **Process Observations** — four buckets or the literal "nothing notable" string.
6. **Citations** — per AGENT_CONTRACT.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/audit-router/<run_id>.md`
- **JSON envelope:** `docs/reports/audit-router/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

### Dimensions (Wave 10 contract)

The agent's envelope MUST place every classifier below in either `dimensions_compared[]` or `dimensions_skipped[]`. Classifier state reflects whether the underlying probe ran fully, partially, or not at all.

Domain classifiers (one dimension per `--domain` value):
`validation_rule`, `picklist`, `approval_process`, `record_type_layout`, `report_dashboard`, `case_escalation`, `lightning_record_page`, `list_view_search_layout`, `quick_action`, `report_folder_sharing`, `field_history`, `sharing`, `org_drift`, `my_domain_session`, `prompt_library`.

## Escalation / Refusal Rules

Refusal codes come from [`agents/_shared/REFUSAL_CODES.md`](../_shared/REFUSAL_CODES.md). Canonical conditions:

- Required input missing → `REFUSAL_MISSING_INPUT`.
- `target_org_alias` not authenticated with `sf` CLI → `REFUSAL_MISSING_ORG` / `REFUSAL_ORG_UNREACHABLE`.
- `domain` specifies a classifier that doesn't exist → `REFUSAL_OUT_OF_SCOPE` (recommend adding the classifier via the `classifier_contract.md` process).
- Inventory returns zero rows → `REFUSAL_OUT_OF_SCOPE` with "nothing to audit".
- Domain-specific refusal from the classifier's `Escalation / Refusal Rules` — propagate verbatim.
- Object / process / folder is managed-package → `REFUSAL_MANAGED_PACKAGE`.
- Scope limit (e.g. > 100 rules, > 10k reports) → `REFUSAL_OVER_SCOPE_LIMIT`; return top-N + truncation note.

---

## What This Agent Does NOT Do

- Does not modify org metadata.
- Does not deploy patches — emits them for the human to apply.
- Does not chain to other agents — recommends them in Process Observations.
- Does not invent new finding codes — only codes declared in a classifier's Rule Table may appear in output.
- Does not audit multiple domains in one invocation — one `--domain` per run.
- Does not execute Apex or run cleanup jobs — strictly advisory.
