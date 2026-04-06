---
name: entitlement-apex-hooks
description: "Use this skill when writing Apex triggers or classes that interact with CaseMilestone records — completing milestones, detecting violations, or reacting to SLA state changes. Trigger keywords: CaseMilestone trigger, auto-complete milestone Apex, milestone violation polling, CompletionDate write pattern. NOT for entitlement process admin setup, milestone configuration in Setup UI, or Flow-based milestone actions."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Operational Excellence
triggers:
  - "How do I auto-complete a CaseMilestone from an Apex trigger when a case status changes?"
  - "CaseMilestone.IsCompleted is read-only — how do I mark a milestone as complete in Apex?"
  - "How do I detect and react to SLA milestone violations in Apex without a native callback?"
tags:
  - entitlements
  - milestones
  - case-milestone
  - sla
  - apex-trigger
  - service-cloud
inputs:
  - "List of MilestoneType names that the trigger should auto-complete"
  - "Case status values that should trigger milestone completion"
  - "Whether violation detection should be synchronous (trigger) or asynchronous (scheduled job)"
outputs:
  - "After-update trigger on Case that writes CompletionDate to open CaseMilestone records"
  - "Scheduled Apex class that queries and processes violated milestones"
  - "Test class covering IsCompleted read-only constraint and bulk DML patterns"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Entitlement Apex Hooks

Use this skill when you need Apex code that reads or writes to `CaseMilestone` records as part of entitlement and SLA enforcement. It covers the platform constraints that make this area unexpectedly difficult: `IsCompleted` is read-only, `SlaExitDate` is system-managed, and there is no native Apex callback for milestone violations.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm that Entitlement Management is enabled in the org (Setup > Entitlement Settings). Triggers on `CaseMilestone` compile but produce no records if entitlement processes are not active.
- Know the exact `MilestoneType.Name` values whose completion the trigger should control. Name strings are case-sensitive and must match what is configured in Setup.
- Understand whether you need synchronous completion (trigger on Case field change) or asynchronous violation detection (scheduled Apex polling). These are separate patterns and require separate implementations.

---

## Core Concepts

### CaseMilestone.IsCompleted Is Read-Only

`CaseMilestone.IsCompleted` is a formula-derived field. The platform sets it to `true` automatically when `CompletionDate` is non-null. You cannot write `IsCompleted = true` in DML — the attempt compiles silently but the field is ignored at save time, leaving the milestone incomplete. The correct write is `caseMilestone.CompletionDate = System.now()` in an `update` DML call.

This is the single most common source of broken milestone automation. The field appears writable in the schema explorer because it is not marked as a formula field in the UI, but the Salesforce Entitlements Implementation Guide explicitly states that `CompletionDate` is the control field.

### SlaExitDate Is System-Managed

`CaseMilestone.SlaExitDate` represents when the SLA window closes. It is calculated and maintained entirely by the platform based on the entitlement process definition and business hours. Apex cannot write to this field. Any attempt to set it in DML is silently discarded. If your requirement involves changing when a milestone deadline occurs, that change must be made through the entitlement process configuration in Setup, not through Apex.

### No Native Apex Callback for Milestone Violations

Salesforce does not fire a trigger, platform event, or callback when a `CaseMilestone` transitions to a violated state. The `IsViolated` field on `CaseMilestone` is set by the platform when `TargetDate < NOW() AND CompletionDate = null`, but this state change does not cause a trigger execution. The only supported Apex pattern for acting on violations is a Scheduled Apex class that periodically queries:

```apex
SELECT Id, CaseId, MilestoneType.Name, TargetDate
FROM CaseMilestone
WHERE IsViolated = true
  AND CompletionDate = null
```

Alternatively, you can use declarative milestone violation actions (email alerts, field updates) configured in the entitlement process — these are native and do not require Apex.

### Trigger Context for CaseMilestone Completion

Milestone completion triggered by a case field change (e.g., Status becomes "Resolved") should be handled in an `after update` trigger on `Case`. The pattern is:

1. Filter `Trigger.new` records for cases where the relevant field changed.
2. Query `CaseMilestone` records for those case IDs where `CompletionDate = null` and `MilestoneType.Name` matches the target types.
3. Set `CompletionDate = System.now()` on each returned record.
4. `update` the list.

The trigger must be `after update` (not `before update`) because writing `CompletionDate` requires a separate DML call. Writing to `CaseMilestone` in a `before update` trigger on `Case` is unsupported and will cause mixed-DML errors in certain contexts.

---

## Common Patterns

### Pattern: Auto-Complete Milestone on Case Status Change

**When to use:** A business rule requires that a specific milestone (e.g., "First Response") is marked complete when the case status changes to a particular value (e.g., "In Progress" or any non-new status).

**How it works:**

1. `after update` trigger on `Case` fires.
2. Collect IDs of cases where `Status` changed to the target value.
3. Query `CaseMilestone WHERE CaseId IN :changedCaseIds AND CompletionDate = null AND MilestoneType.Name = 'First Response'`.
4. For each result, set `CompletionDate = System.now()`.
5. `update` the `CaseMilestone` list.

**Why not the alternative:** Setting `IsCompleted = true` directly appears to work (no DML exception) but the field value is discarded by the platform. The milestone stays open. This silent failure is the canonical trap in this domain.

### Pattern: Violation Detection via Scheduled Apex

**When to use:** The org needs custom business logic when milestones are violated — for example, escalating to a manager, creating a task, or updating a related field — and the declarative milestone actions in the entitlement process are insufficient.

**How it works:**

1. Implement `Schedulable` and query `CaseMilestone WHERE IsViolated = true AND CompletionDate = null`.
2. For each violated milestone, apply the business logic (create a task, send a notification, update the parent Case).
3. Schedule the class to run at an appropriate interval (e.g., every 15–30 minutes via a cron expression).
4. Guard against re-processing: add a custom checkbox field on `Case` (e.g., `ViolationEscalated__c`) and filter it out of the query to avoid duplicate actions.

**Why not the alternative:** There is no trigger or platform event that fires when `IsViolated` becomes `true`. Attempting to intercept this via a trigger on `CaseMilestone` itself will not work for violation detection because the field is set by a background platform process, not by a DML operation that would fire a trigger.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Mark milestone complete when a Case field changes | `after update` trigger on Case writing `CompletionDate = System.now()` | Only supported write path; IsCompleted is read-only |
| React to milestone violations with custom logic | Scheduled Apex polling `IsViolated = true` | No native callback exists; polling is the only Apex path |
| Change when a milestone deadline occurs | Modify entitlement process configuration in Setup | `SlaExitDate` is system-managed and cannot be written by Apex |
| Send email or update fields on violation | Declarative milestone violation actions in entitlement process | No Apex required; native and more reliable than polling |
| Bulk-complete milestones for many cases | Batch Apex querying `CaseMilestone` and writing `CompletionDate` | Avoids trigger CPU/heap limits; respects governor limits per batch |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm entitlement setup** — Verify Entitlement Management is enabled and at least one entitlement process with milestones is active. Identify the exact `MilestoneType.Name` strings you need to target (case-sensitive).
2. **Choose the correct pattern** — Decide whether you need synchronous completion (trigger on Case field change) or asynchronous violation detection (Scheduled Apex). Document the requirement before writing code.
3. **Write the trigger or class** — For completion: `after update` on Case, query open `CaseMilestone` records for affected cases, write `CompletionDate`, bulk-safe DML. For violation detection: `Schedulable` class, query `IsViolated = true AND CompletionDate = null`, apply business logic with idempotency guard.
4. **Write the test class** — Cover: (a) the `CompletionDate` write path succeeds, (b) `IsCompleted` reads back as `true` after the write, (c) bulk scenario with 200 cases, (d) the `IsViolated` polling query returns expected records in test context.
5. **Validate in a sandbox with an active entitlement process** — `CaseMilestone` records only exist when a case has an active entitlement process applied. Tests that run without this setup will pass vacuously with empty lists. Use `@testSetup` to create the entitlement hierarchy.
6. **Deploy and monitor** — After deployment, verify milestone completion timestamps appear correctly on cases. For scheduled jobs, confirm the job is scheduled and check the Apex Jobs log for exceptions.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Trigger writes `CompletionDate = System.now()` — NOT `IsCompleted = true`
- [ ] Trigger is `after update` on Case (not `before update`, not a trigger on CaseMilestone itself for completion)
- [ ] No attempt to write `SlaExitDate` anywhere in the code
- [ ] Violation detection uses `IsViolated = true` query, not a trigger callback
- [ ] Bulk-safe: trigger uses `Trigger.new` list, queries use `IN :idSet`, DML uses list `update`
- [ ] Test class creates the full entitlement process hierarchy so `CaseMilestone` records actually exist during test execution
- [ ] Idempotency guard in scheduled violation handler (prevents double-escalation on the same milestone)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **IsCompleted silently ignores direct writes** — Writing `caseMilestone.IsCompleted = true` does not throw an exception but the value is discarded. The milestone remains incomplete. Always write `CompletionDate` instead.
2. **SlaExitDate DML is silently discarded** — Attempting to set `SlaExitDate` in an update call produces no error but the field value is not persisted. The only way to change the milestone deadline is through the entitlement process setup in the admin UI.
3. **No trigger fires on IsViolated state transition** — The platform sets `IsViolated = true` through a background calculation, not through a DML operation. No Apex trigger on `CaseMilestone` fires at the moment of violation. Relying on a `CaseMilestone` after-update trigger to catch violations will produce false results.
4. **CaseMilestone records do not exist in developer or partial-copy sandboxes without entitlement processes** — If the sandbox org does not have an active entitlement process configured and applied to cases, `CaseMilestone` records are never created and trigger code runs against empty result sets. This causes all tests to pass vacuously.
5. **MilestoneType.Name is case-sensitive in SOQL** — `MilestoneType.Name = 'first response'` will not match a type named `'First Response'`. Query failures here produce no records, not an exception, so the silent failure is easy to miss in testing.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CaseMilestone completion trigger | `after update` trigger on Case that writes `CompletionDate` to open milestone records when a case status change occurs |
| Milestone violation scheduler | Scheduled Apex class that queries violated open milestones and applies custom business logic with idempotency |
| Test class | Apex test covering bulk completion, read-back of `IsCompleted`, and violation polling query |

---

## Related Skills

- `admin/case-management-setup` — Entitlement process and milestone configuration in Setup UI; required before any Apex milestone code has records to act on
- `apex/opportunity-trigger-patterns` — General Apex trigger bulk-safety patterns applicable here
