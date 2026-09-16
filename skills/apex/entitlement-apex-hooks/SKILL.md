---
name: entitlement-apex-hooks
description: "Apex triggers and classes that read or write CaseMilestone records: completing milestones, detecting violations, reacting to SLA state changes. Trigger keywords: CaseMilestone trigger, auto-complete milestone Apex, milestone violation polling, CompletionDate write pattern. NOT for entitlement auto-association or assignment rules in a Case trigger — use apex/case-trigger-patterns. NOT for entitlement process and milestone setup in Setup — use admin/entitlements-and-milestones."
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
  - "auto complete case milestone apex CompletionDate IsViolated hooks"
  - "complete a case milestone from apex"
  - "stop the SLA clock when a case is pending customer"
  - "write CompletionDate on an open CaseMilestone in a bulk-safe trigger"
  - "test a CaseMilestone trigger when you cannot create an SlaProcess"
  - "poll for violated case milestones on a schedule"
  - "pause and resume an entitlement process on a case from apex"
  - "why does my case milestone query return nothing in an after update trigger"
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
version: 1.1.3
author: Pranav Nagrecha
updated: 2026-09-16
---

# Entitlement Apex Hooks

Use this skill when you need Apex code that reads or writes to `CaseMilestone` records as part of entitlement and SLA enforcement. It covers the platform constraints that make this area unexpectedly difficult: `IsCompleted` carries no `Update` property, the only supported call on `CaseMilestone` is `update()`, entitlement rules run after every trigger, and there is no documented Apex event for milestone violations.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm that Entitlement Management is enabled in the org (Setup > Entitlement Settings). Triggers on `CaseMilestone` compile but produce no records if entitlement processes are not active.
- Know the exact `MilestoneType.Name` values whose completion the trigger should control. Copy them from Setup rather than from the requirement document — a name that does not match returns zero rows, and zero rows is not an exception.
- Understand whether you need synchronous completion (trigger on Case field change) or asynchronous violation detection (scheduled Apex polling). These are separate patterns and require separate implementations.

---

## Questions to Ask Before Configuring

Milestone automation fails silently more often than it fails loudly, so most of the cost
of getting it wrong is discovered months later in an SLA report. Each question below is
the one that would have prevented a specific gotcha; the gotcha number points at the full
write-up in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| **1. Which exact `MilestoneType` name should this complete, and who is allowed to rename it?** (Gotcha 1, Gotcha 11) | The completion query filters on `MilestoneType.Name`. A wrong or renamed string returns zero rows, which is not an error — the automation just stops working. | A name copied from Setup rather than from the requirement document, plus the name of the admin who owns it. | The name lands in one named constant or a Custom Metadata record instead of a literal per call site, so a Setup rename is a one-line change and not a hunt. |
| **2. Does the case status change that completes the milestone ever happen on the same save that puts the case into the entitlement process?** (Gotcha 3) | Entitlement rules run at step 15 of the order of execution, after all after triggers at step 8. On the entitlement-applying save the milestone rows do not exist yet. | A concrete answer about the intake path — web-to-case, an integration upsert, a Flow that sets `EntitlementId` and `Status` together. | The trigger is hung off a later save, or moved to a post-commit async path, instead of shipping a trigger that works in manual testing and returns nothing in production. |
| **3. Are there workflow field updates, escalation rules, or record-triggered flows on `Case` in this org?** (Gotcha 4) | A workflow field update re-fires before-update and after-update triggers one more time on the same save, so the completion body genuinely runs twice. | An inventory of the existing `Case` automation, not an assumption that this trigger is alone. | `CompletionDate = NULL` is in the query as a deliberate idempotency guard with a test that proves the second pass is a no-op — rather than as an incidental filter nobody can explain. |
| **4. Is the requirement to complete milestones, or to change when they are due, or to pause them?** (Gotcha 2, Gotcha 8) | These are three different problems with three different answers. Only the first is an Apex write. `TargetDate` is not updateable and there is no `SlaExitDate` on `CaseMilestone` at all; pausing is `Case.IsStopped`. | The business rule in plain language — "the clock should not run while we are waiting on the customer" — rather than a proposed field write. | A deadline requirement becomes an entitlement-process design change in Setup and a pause requirement becomes a `Case.IsStopped` write, instead of Apex against a field that does not compile. |
| **5. Which org will this be tested in, and does it have an active entitlement process?** (Gotcha 5, Gotcha 6) | A test cannot create an `SlaProcess` and cannot create a `CaseMilestone` — neither object supports `create()`. Without a configured process the test queries an empty list and passes vacuously. | A named sandbox with entitlement management configured, and a decision on whether `@IsTest(SeeAllData=true)` is acceptable to the team. | The test asserts loudly on the missing prerequisite and keeps one method that still runs without it, instead of producing a green build that certifies automation which has never executed. |
| **6. What should happen when one milestone in a bulk update fails — abort the case save, or complete the rest?** (Gotcha 10) | All-or-nothing `update` rolls the case save back; `Database.update(list, false)` completes the rest but throws nothing, so failures vanish unless the results array is iterated. | An explicit business answer about whether a failed milestone should block the agent's save. | The `Database.SaveResult` loop and a logging destination are part of the design, rather than boilerplate that gets trimmed in review and takes the error signal with it. |
| **7. How does the business need to see violations and time remaining — a notification, a report, or custom logic?** (Gotcha 7, Gotcha 9) | Notifications and field updates are native milestone actions and need no Apex. Custom logic needs a scheduled poll, because there is no documented DML event for the `IsViolated` transition. And `TimeRemainingInMins` is a text field, so a "due within 30 minutes" report cannot filter on it. | A distinction between "tell someone" and "do something", plus the actual shape of the report. | Half the requirement is met declaratively with no code to maintain, and the half that needs Apex is a scheduled job with an idempotency guard rather than a trigger that never fires. |
| **8. Which entitlement process, by name, does the target org run for this case type — and does the org already carry others?** (Gotcha 6, Gotcha 13) | A test needs `@IsTest(SeeAllData=true)` to reach a real `SlaProcess` at all. If the target org already has its own active process for this case type, an unfiltered `WHERE IsActive = true LIMIT 1` can silently return that pre-existing process instead of the one being deployed. | The exact process name (and label form, if different) the deployed automation should enter, plus a list of any other active processes the org already runs. | The test selects the process by name and asserts exactly one match, instead of a `LIMIT 1` query that passes vacuously against the wrong process — a defect that only an org dry run surfaces, never a scratch org. |

**What proper configuration adds over just doing it:** the three failure modes in this
domain — a query that returns nothing, a write to a field that is not updateable, and a
test that passes without ever touching a milestone — all produce no error message. Asking
these seven questions first is what converts them from a silent SLA breach discovered in a
quarterly report into a loud failure at build time.

---

## Core Concepts

### CaseMilestone.IsCompleted Is Not an Updateable Field

The Object Reference lists `IsCompleted`'s properties on `CaseMilestone` as `Defaulted on create, Filter` — no `Update`. `CompletionDate` carries `Filter, Nillable, Update`, and is one of only two fields on the object that do (the other is `StartDate`). So "complete this milestone" has exactly one implementation: `caseMilestone.CompletionDate = System.now()` followed by an `update`.

This is the single most common source of broken milestone automation, because the field whose *name* describes the outcome is not the field the API lets you set. Assert on `CompletionDate` being non-null; treat `IsCompleted` as a reporting convenience rather than the thing your code controls. See Gotcha 1 in `references/gotchas.md` for what is grounded here and what is not.

### There Is No SlaExitDate on CaseMilestone

`SlaExitDate` is not a `CaseMilestone` field. The field of that name belongs to `WorkOrder`, where it is read-only. Referencing it on a `CaseMilestone` variable or in a `CaseMilestone` `SELECT` list is a compile error, not a silently-discarded write — which is the good kind of failure.

The `CaseMilestone` deadline field is `TargetDate`, and its only documented property is `Filter`: it is not updateable. Milestone deadlines are therefore not adjustable from Apex at all. Variable deadlines are modelled as separate entitlement processes with different milestone time triggers, applied to the case based on its attributes. Pausing the clock is a different field again — `Case.IsStopped`, which *is* writable. See Gotcha 2 and Gotcha 8.

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

The trigger must be `after update`, not `before update`, and the reason is the order of execution rather than mixed DML (`CaseMilestone` is not a setup object, so mixed DML does not apply). Before triggers run at step 4 and after triggers at step 8, while entitlement rules — the engine that creates the milestone rows — run at step 15. Neither trigger context can see milestones created by the save it is running inside, so completion has to hang off a *later* save than the one that applies the entitlement. See Gotcha 3.

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
| Change when a milestone deadline occurs | Modify entitlement process configuration in Setup | `TargetDate` is not updateable, and there is no `SlaExitDate` on `CaseMilestone` |
| Pause the SLA clock while waiting on the customer | Write `Case.IsStopped = true` from a Case trigger or Flow | It is the writable switch; nothing on `CaseMilestone` pauses anything |
| Send email or update fields on violation | Declarative milestone violation actions in entitlement process | No Apex required; native and more reliable than polling |
| Bulk-complete milestones for many cases | Batch Apex querying `CaseMilestone` and writing `CompletionDate` | Avoids trigger CPU/heap limits; respects governor limits per batch |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm entitlement setup** — Verify Entitlement Management is enabled and at least one entitlement process with milestones is active. Copy the exact `MilestoneType.Name` strings from Setup and put them in one constant or Custom Metadata record.
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
- [ ] No reference to `SlaExitDate` and no write to `TargetDate` anywhere in the code
- [ ] `CompletionDate = NULL` is in the milestone query — both the open-milestone filter and the idempotency guard
- [ ] `Database.update(list, false)` results are iterated and failures are logged somewhere queryable
- [ ] `scripts/check_entitlement_apex_hooks.py --manifest-dir <tree> --strict` returns clean
- [ ] Violation detection uses `IsViolated = true` query, not a trigger callback
- [ ] Bulk-safe: trigger uses `Trigger.new` list, queries use `IN :idSet`, DML uses list `update`
- [ ] Test class creates the full entitlement process hierarchy so `CaseMilestone` records actually exist during test execution
- [ ] Idempotency guard in scheduled violation handler (prevents double-escalation on the same milestone)
- [ ] A `SeeAllData` test selects its `SlaProcess` by name and asserts exactly one match — not `WHERE IsActive = true LIMIT 1` with no name filter (Gotcha 13)
- [ ] Any `CaseMilestone` write from a trigger-called service that no permission set grants the running persona is bound in an explicit `AccessLevel.SYSTEM_MODE`, with a `// reason:` comment (Gotcha 14)
- [ ] Every test assertion after a `Database.update(..., false)` call also asserts `result.failures.size() == 0` (or iterates `SaveResult.getErrors()`) — not only an attempt or success count (Gotcha 14)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

The full write-up, with source lines and explicit `UNVERIFIED` markers where the corpus does not support a widely-repeated claim, is in `references/gotchas.md`. The short list:

| # | Gotcha | One-line form |
|---|---|---|
| 1 | `IsCompleted` is not updateable | `CompletionDate` and `StartDate` are the only two fields on the object that carry `Update` |
| 2 | No `SlaExitDate` on `CaseMilestone` | It belongs to `WorkOrder`; the milestone deadline field is the read-only `TargetDate` |
| 3 | Entitlement rules run at step 15 | After every trigger — milestone rows do not exist on the entitlement-applying save |
| 4 | Workflow field updates re-fire the trigger | The body runs twice per save; `CompletionDate = NULL` is the idempotency guard |
| 5 | Only `update()` is supported | No `create()`, no `delete()` — the platform owns the row lifecycle |
| 6 | A test cannot create an `SlaProcess` | No `create()` call; the process must exist in the org, so the test must fail loudly without it |
| 7 | `TimeRemainingInMins` is text | Typed `text`, formatted "minutes and seconds" — a numeric comparison is meaningless |
| 8 | Pausing is `Case.IsStopped` | Writable on `Case`; `Case.StopStartDate` is read-only |
| 9 | No documented DML event for `IsViolated` | Poll with Scheduled Apex or use native milestone violation actions |
| 10 | Partial-success DML hides failures | `Database.update(list, false)` throws nothing; iterate the `SaveResult` array |
| 11 | The milestone type name is a string match | A Setup rename returns zero rows, not an error |
| 12 | A generated test class ships without the template it calls | `TestDataFactory` and other `templates/apex/**` classes must be copied into the same deployable set |
| 13 | A `SeeAllData` test must select its entitlement process by name | `WHERE IsActive = true LIMIT 1` can return the target org's own pre-existing process instead of the deployed one |
| 14 | The milestone stamp is a system-integrity write | Bound it in explicit `AccessLevel.SYSTEM_MODE`, and assert `result.failures.size() == 0` — partial-success DML never throws |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CaseMilestone completion trigger | `after update` trigger on Case that writes `CompletionDate` to open milestone records when a case status change occurs |
| Milestone violation scheduler | Scheduled Apex class that queries violated open milestones and applies custom business logic with idempotency |
| Test class | Apex test covering bulk completion, read-back of `IsCompleted`, and violation polling query |

---

## Related Skills

- `admin/entitlements-and-milestones` — the Setup side: entitlement process, milestone types, and the deployable metadata. Nothing in this skill has records to act on until that one is done
- `admin/case-management-setup` — broader case configuration around the entitlement process
- `apex/case-trigger-patterns` — entitlement auto-association and assignment logic in a Case trigger, which is a different job from milestone completion
- `apex/opportunity-trigger-patterns` — general Apex trigger bulk-safety patterns applicable here
- `apex/test-class-standards` Gotcha 15 — seeds a test fixture in `AccessLevel.SYSTEM_MODE` and acts as the persona; Gotcha 14 in this skill draws the same boundary one level up, for a shipped service's own write
- `apex/apex-security-patterns` — the general access-mode decision table (`WITH USER_MODE` vs `WITH SYSTEM_MODE`) that Gotcha 14's system-mode write follows

## Deployable Reference

`references/code-examples.md` carries the complete bundle: `CaseMilestoneService.cls`,
`CaseMilestoneTriggerHandler.cls`, `CaseMilestoneTrigger.trigger`,
`CaseMilestoneServiceTest.cls`, every `-meta.xml` at `apiVersion` 67.0, a `package.xml`,
the deploy order, and the checker run that verifies it.
