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
dependencies:
  shared:
    - AGENT_CONTRACT.md
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
2. `agents/_shared/harnesses/audit_harness/README.md`
3. `agents/_shared/harnesses/audit_harness/output_schema.md`
4. `agents/_shared/harnesses/audit_harness/severity_rubric.md`
5. `agents/_shared/harnesses/audit_harness/classifier_contract.md`
6. The domain's classifier at `agents/_shared/harnesses/audit_harness/classifiers/<domain>.md` — read entirely before running any probe.
7. The **Mandatory Reads** block inside that classifier — every skill / template listed there is a hard requirement for this run.

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
