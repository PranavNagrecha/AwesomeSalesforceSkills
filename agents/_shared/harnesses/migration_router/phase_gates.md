# Migration Router — Shared Phase Gates

The four phases every source-type dispatch runs in the same order. The
source-specific logic lives in `decision_table.md`; everything here is
source-agnostic.

## Phase 1 — Inventory

The source probe listed in `decision_table.md` for the active `source_type`.
Every row of the inventory carries:

- source artifact id + name
- active/inactive flag
- trigger type (record-saved / time-dependent / other)
- action list (or approval-step list for `approval_process`)
- timestamps: `CreatedDate`, `LastModifiedDate`

Inventory output is emitted as `inventory_table` in the output envelope
regardless of source type.

## Phase 2 — Classify + design

Per `decision_table.md`. Every target element cites the **source artifact
id** plus the **canonical skill or template** the shape came from. This is
the audit trail reviewers use to trace every element back to the rule it
replaced.

## Phase 3 — Parallel-run validation

**Default pattern (field-update-bearing migrations):**

1. Deploy the new Flow / Orchestrator in **inactive** state.
2. Clone into an `audit-only` variant that writes the computed value to a
   shadow field `Flow_Migration_Shadow__c` on the object (or an Audit
   Custom Object if the target field is locked / managed / can't be added).
3. Leave the source automation active. For **N business days (default 7)**,
   compare the shadow to the live value via a daily report.
4. On zero drift for N consecutive days, activate the new automation and
   deactivate the source in the same deployment window.

**Approval-process specific (`approval_process` migrations):**

The shadow-field pattern does not apply directly. Replace with a
staged-submission pattern:

1. Deploy the new Orchestration in **inactive** state.
2. Route a **canary population** of submissions (e.g. a single queue or a
   specific record type) to the new Orchestration via a Flow Decision
   before the Submit for Approval action.
3. Monitor approval-cycle latency, rejection rate, and escalation counts
   on the canary population for the agreed runway (default 14 days).
4. Expand canary to 100% in stages of 10% / 50% / 100%, rolling back on
   any elevated rejection-rate signal.

**Fallback (shadow field unavailable):**

- Bulk query comparison via CLI, dumped nightly to CSV, diffed against the
  source's expected post-change state. The agent documents the exact query
  to run; does NOT execute it.

## Phase 4 — Rollback

Uniform across source types. Cite `skills/flow/flow-versioning-strategy`
(rollback = activate prior inactive version, not redeploy) and
`skills/flow/flow-record-save-order-interaction` (verify the new flow's
save-order slot does not collide with the source it is replacing).

1. Within N days of cutover, if divergence is found: deactivate the new
   automation, reactivate the source. For flow-side rollback specifically,
   this is the "activate the prior inactive version" one-click path from
   `skills/flow/flow-versioning-strategy` — never a redeploy.
2. Any field changes made by the new automation during the divergence
   window need a data-fix. The agent lists the affected fields + suggests
   the fix shape; does NOT generate fix SOQL/DML. Route to a human via
   `REFUSAL_NEEDS_HUMAN_REVIEW` if the blast radius exceeds 10k rows.
3. Document the metrics to watch pre-cutover and post-cutover:
   - record count per day on the object
   - average save latency (from `FlowInterviewLog` or Apex `Limits.getCpuTime`)
   - flow error count from `FlowInterviewLog` + Orchestrator error log
   - (for `approval_process` only) approval-cycle latency + rejection rate

## Scheduled Paths — a cross-cutting subphase

For any `wf_rule` / `process_builder` source with time-dependent actions:

- Default: translate each `WorkflowTimeTrigger` into a Scheduled Path on
  the after-save flow. Offset, direction (before/after), and reference
  field map directly.
- Document the one non-obvious behavior: **Scheduled Paths fire even if the
  record has since changed to fail the original entry criteria.** Every
  scheduled path starts with a re-evaluation Decision that checks the same
  criteria and exits early if they no longer hold. This is canonical per
  `skills/flow/scheduled-flows` and mirrors the "Re-evaluate Workflow Rules
  After Update" semantics users may have relied on.
- Escape hatch: the `time_dependent_handling: defer-to-scheduled-flow` input
  switches to a nightly Scheduled Flow that re-evaluates records. Use when
  the time-dependent action runs on a large record population and the org
  is under async-Apex pressure.
- Escape hatch 2: `time_dependent_handling: refuse` emits the time-dependent
  actions as unmigrated items with `REFUSAL_NEEDS_HUMAN_REVIEW`.

## Process Observations

Source-type-agnostic observation categories (extend with source-specific
flags in the agent's plan, not here):

- **Healthy** — source artifacts with clean entry criteria, narrowly
  scoped, and well-documented; target org has fault-email recipients
  configured.
- **Concerning** — overlapping sources writing to the same field; inactive
  but still-deployed artifacts; artifacts whose email templates reference
  retired merge fields; approval processes with zero submissions in the
  last 90 days (candidate for retirement rather than migration).
- **Ambiguous** — time-dependent actions keyed on fields that no longer
  exist; artifacts whose original business owner is identifiable only by a
  departed user.
- **Suggested follow-ups** — `flow-analyzer` for post-cutover health;
  `validation-rule-auditor` for VR vs migrated-flow conflicts;
  `apex-refactorer` when the target depends on an Apex-held invariant;
  `agentforce-builder` for `approval_process` candidates marked
  `ROUTE_TO_AGENTFORCE`.
