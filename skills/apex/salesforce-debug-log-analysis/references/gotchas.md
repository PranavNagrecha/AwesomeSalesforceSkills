# Gotchas — Salesforce Debug Log Analysis

Non-obvious platform behaviors that mislead forensic log analysis. Each one has burned a real investigation at least once.

## The 20 MB Log Cap Truncates Silently

**What happens:** A single debug log is capped at 20 MB. Anything past that is dropped with no end-of-log marker and no `FATAL_ERROR`. The user thinks the transaction completed cleanly because the log "just ends."

**When it occurs:** Large cascades (DLRS recalculation across hundreds of records, CPQ QLI updates, bulk loads through a Flow). Heavy trace-flag levels like `APEX_CODE,FINEST` fill 20 MB in seconds.

**How to avoid:** Compare `wc -c` against 20,000,000. If the log is exactly at the cap (within a few KB) and has no `EXECUTION_FINISHED`, it is truncated. Ask the user to lower `APEX_CODE` to `FINE` and re-capture, or use the `tail -f` pattern via `sf apex tail log`.

---

## Managed-Package Code Is A Black Box Below `ENTERING_MANAGED_PKG`

**What happens:** When execution enters a managed-package namespace, the log prints `ENTERING_MANAGED_PKG|<ns>` and then shows only a handful of events (DML, exceptions). Internal method calls and variable assignments are hidden by design.

**When it occurs:** Every time a subscriber trigger fires inside CPQ, Vlocity, nCino, FinServ, DLRS, EDA, TracRTC, DocuSign, Conga, Pardot, or any ISV-installed package.

**How to avoid:** Do not attempt to diagnose internal package logic from the log. Use `references/managed-packages.md` to map the namespace to known behaviors. For support cases, capture the log, redact org data, and file with the package vendor — Salesforce Support will not debug ISV code.

---

## `FLOW_ASSIGNMENT_DETAIL` Only Appears At `WORKFLOW,FINER` Or Higher

**What happens:** A flow runs and writes a field, but the log has no `FLOW_ASSIGNMENT_DETAIL` event. Analysts conclude the flow did not run, when it actually did.

**When it occurs:** Default `WORKFLOW,INFO` level captures `FLOW_START_INTERVIEW_BEGIN` and `FLOW_ELEMENT_BEGIN/END` but suppresses assignment details.

**How to avoid:** Check the header category line. If `WORKFLOW` is below `FINER`, state clearly that flow assignments cannot be attributed from this log and request a recapture with `WORKFLOW,FINER`.

---

## Formula Fields Have No Write Event

**What happens:** A user says "this formula field keeps changing." Analysts hunt for a writer that does not exist.

**When it occurs:** Any field defined as `Formula__c` in metadata. Rollup summary fields (`SummaryField__c`) do have write events (via the platform's internal recalculation), but they appear as before/after deltas without a specific writer in user code.

**How to avoid:** If a field appears in `SELECT` results with different values but never in `VARIABLE_ASSIGNMENT`, `FLOW_ASSIGNMENT_DETAIL`, or `WF_FIELD_UPDATE`, it is a formula. Check the field's metadata type before continuing. The "change" is the formula recalculating against changed input fields — investigate the inputs instead.

---

## The Running User In Async Context Is Not The Initiating User

**What happens:** The log header shows `USER_INFO|0050B00000ABCDE|IntegrationUser@org`. Analysts conclude the integration user caused the issue. In reality, a human user's click queued the Queueable minutes ago.

**When it occurs:** All async contexts — `@future`, Queueable, Batch, Scheduled, Platform Event subscriber, CDC subscriber. These run as the user who enqueued them, but the `DELEGATED` user context of assignment rules, auto-response, and certain managed-package jobs can flip mid-transaction.

**How to avoid:** For async logs, also check `AsyncApexJob.CreatedById` (Setup > Monitoring > Apex Jobs) to find the enqueuing user. That is usually the user who owns the problem.

---

## Empty Bracket List In `INSUFFICIENT_ACCESS_OR_READONLY`

**What happens:** The log shows `INSUFFICIENT_ACCESS_OR_READONLY: entity is not accessible: []`. The bracket list is empty.

**When it occurs:** On merge, mass transfer, or other multi-record operations where the platform obscures which specific record ID caused the access failure. This is by design — exposing the ID would leak existence of records the caller cannot see.

**How to avoid:** Do not try to extract the ID from the log. Provide the user a remediation path outside the log: query related children as admin, run `SELECT Id FROM <Type> WHERE Id IN :potentialIds` while logged in as the merging user, and compare the two result sets. The missing ID is the blocker.

---

## `DML_BEGIN.Rows` Is Per-Statement, Not Cumulative

**What happens:** Analysts sum `Rows` across all `DML_BEGIN` events to estimate transaction volume. That number is meaningless — bulk DML operations may still log one event per sub-batch.

**When it occurs:** Anywhere bulk data is moved: Batch Apex `execute()`, Bulk API, Data Loader operations, cascading deletes.

**How to avoid:** For governor-limit math, use `TESTING_LIMITS` or `LIMIT_USAGE_FOR_NS` events. They are the only authoritative per-namespace, per-limit accounting in the log.

---

## `ASYNC_DML_BEGIN` Does Not Mean Your Code Published An Event

**What happens:** A log shows `ASYNC_DML_BEGIN|Op:Insert|Type:Event__e`. An engineer concludes their code published a platform event.

**When it occurs:** Salesforce internally uses async DML for formula recalculation, indirect relationship maintenance, sharing recalculation, and several platform features. Not every `ASYNC_DML_BEGIN` traces back to user code.

**How to avoid:** Check the stack preceding `ASYNC_DML_BEGIN`. If it is inside `System.*` or has no user-code `METHOD_ENTRY` before it, it is a platform-internal async operation.

---

## `CRON_TRIGGER_` In The Header Does Not Mean Apex Scheduled The Job

**What happens:** The header shows `CRON_TRIGGER_0123000000XYZ`. Analysts look for the `System.schedule` call that created it.

**When it occurs:** Salesforce uses cron triggers for scheduled flows, scheduled reports, email alerts with delayed execution, and several setup-configured jobs — none of which were scheduled via Apex.

**How to avoid:** Query `CronTrigger` and `CronJobDetail` to identify the schedule source. `CronJobDetail.JobType` distinguishes Apex-scheduled (`7`) from scheduled flow (`9`) from scheduled report (`4`).

---

## `WF_` Events Persist Long After You Migrated To Flow

**What happens:** An org "migrated to Flow" but `WF_FIELD_UPDATE` events still appear. Analysts assume the migration is incomplete.

**When it occurs:** Some workflow field updates remain active because Process Builder or Flow migration tooling only migrates rules, not their downstream field-update actions. The migrated flow triggers a `WF_FIELD_UPDATE` from a surviving legacy action.

**How to avoid:** Query `WorkflowRule` where `IsActive = true`. Any remaining row is a candidate for the legacy write, regardless of what Flow now exists.

---

## Time-Based Workflows Fire In A Different Transaction Than The Trigger

**What happens:** A field changes "out of nowhere" hours or days after a user's save. The log at the time of the save shows nothing writing the field.

**When it occurs:** Time-based workflow actions, scheduled-path flow actions, and approval process time-dependent actions all execute in a separate transaction triggered by the Apex Job queue, not the original UI action.

**How to avoid:** For unexplained field changes, ask the user to check `FlowOrchestrationInstance`, `ProcessInstance`, and `WorkflowRule` time-based entries. The triggering transaction will not contain the write; a later Apex Job transaction will.

---

## `VARIABLE_ASSIGNMENT` For An SObject Field Does Not Mean The Field Was Saved

**What happens:** The log shows `VARIABLE_ASSIGNMENT|myAccount.Industry|Healthcare`. Analysts report the Industry was changed to Healthcare.

**When it occurs:** Any Apex code that mutates an in-memory SObject without calling `update`. If the transaction throws before the DML, the assignment shows but the DB was never updated.

**How to avoid:** Correlate `VARIABLE_ASSIGNMENT` with a following `DML_BEGIN|Op:Update|Type:<SObject>` and a successful `DML_END`. Without the DML pair, the assignment did not persist.

---

## `ENTERING_MANAGED_PKG` Wraps The Wrong Namespace Sometimes

**What happens:** A log shows `ENTERING_MANAGED_PKG|dlrs` but the subsequent DML is against an nCino object. Analysts conclude DLRS wrote to nCino.

**When it occurs:** When one managed package calls another (DLRS rolling up nCino fields, CPQ invoking Conga, etc.), the `ENTERING_MANAGED_PKG` reflects the currently executing namespace — which can change mid-line if packages call each other.

**How to avoid:** For suspicious package attribution, grep for every `ENTERING_MANAGED_PKG|*` and `CODE_UNIT_FINISHED|*` pair near the suspect line. The innermost unfinished namespace is the actual executor.
