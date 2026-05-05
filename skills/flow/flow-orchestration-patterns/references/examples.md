# Examples — Flow Orchestration Patterns

## Example 1 — Single-step "approval" implemented as orchestration

**Context.** Admin builds an orchestration with one stage and one
interactive step. The step assigns a Work Item to the manager.

**Why it's overkill.** Single-stage, single-step orchestration has
all the operational overhead of an orchestration (Work Item
inbox, persistence, version-binding) with none of the multi-stage
benefit. A plain Approval Process or a screen flow on the record
page would do the same thing with less surface area.

**Right answer.** Reach for orchestration when you have ≥ 2
meaningful stages OR ≥ 2 humans involved at different steps.
Single-decision approvals are Approval Process territory.

---

## Example 2 — Formula-derived assignee returning null leaves step stuck

**Context.** Orchestration step assigned via formula
`{!$Record.Account.Owner.ManagerId}`. Some accounts have an Owner
whose `ManagerId` is null. The Work Item is created with no
assignee; nobody can open it; the orchestration is stuck at that
step indefinitely.

**Right answer.** Fallback logic in the formula:

```
IF(
    NOT(ISBLANK({!$Record.Account.Owner.ManagerId})),
    {!$Record.Account.Owner.ManagerId},
    {!$Setup.Default_Approver_Group__c.Default_Approver__c}
)
```

The fallback resolves to a default-approver custom-setting value or
a queue. Test the formula's null path before deploying.

---

## Example 3 — Long-running orchestration, source record changes mid-flight

**Context.** Multi-week onboarding orchestration. On day 3, the
employee is terminated; their User record is deactivated and their
custom `Onboarding_Status__c` field is set to `Cancelled`.
Day 5, the orchestration tries to send them their week-1 training
Work Item.

**Wrong outcome.** Work Item is created and assigned to a
deactivated user. The Work Item sits in the (former) employee's
inbox indefinitely.

**Right answer.** **Evaluation flow on each stage exit** that
checks `User.IsActive = TRUE` and `Onboarding_Status__c !=
'Cancelled'`. Returns false if either condition fails. The
orchestration holds at the stage exit; an admin sees the
held-orchestration list and can cancel cleanly.

---

## Example 4 — Mixing interactive + background in a stage

**Context.** Day-1 onboarding stage:

- Step 1A — Provision IDP account (Background — Apex action).
- Step 1B — HR document collection (Interactive — assigned to HR queue).
- Step 1C — Slack welcome (Background — webhook action).

All three run in parallel. Stage 1 completes when all three finish.
The HR step is the long pole (HR can take days); provisioning and
Slack happen in seconds.

**Common mistake.** Putting Step 1A, 1B, 1C in three separate
sequential stages. That serializes work that should be parallel —
the employee waits days for IDP access because they're queued
behind the HR document step.

**Right answer.** All three in stage 1; stage 2 starts only when all
finish.

---

## Example 5 — Cancel pathway via admin-only autolaunched flow

**Context.** Orchestration has been in flight for two weeks. Admin
realizes the source record was created with wrong data; needs to
cancel the orchestration.

**There is no direct "cancel" UI.** Salesforce doesn't surface a
button.

**Designed-in cancel pathway.** The admin runs a separate
"Cancel_Orchestration" autolaunched flow that:
1. Sets a `Cancelled__c` flag on the source record.
2. Every interactive step in every orchestration starts with a
   "is this orchestration cancelled?" decision; if yes, the step
   completes immediately as no-op.
3. Stage exit evaluation flows check the same flag; if set, they
   return true (let the stage complete and the orchestration
   wind down).

The cancel doesn't terminate immediately — it lets the orchestration
drain through its remaining stages quickly. Cleaner than trying to
force-terminate.

---

## Anti-Pattern: Orchestration as Process Builder replacement

**What it looks like.** Admin replaces a 4-step Process Builder
chain with an orchestration containing four sequential stages, each
with a single background step.

**Why it's wrong.** Process Builder chains were single-flow-execution
(all four steps in one transaction). Orchestration's stage / step
model adds asynchronous boundaries between stages — what was a
single-transaction operation now spans multiple transactions, with
visibility / persistence overhead.

**Correct.** Migrate Process Builder to a record-triggered flow
with all four actions in a single flow. Orchestration is for
multi-human / multi-day processes, not single-transaction automation.
