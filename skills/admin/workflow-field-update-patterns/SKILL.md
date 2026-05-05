---
name: workflow-field-update-patterns
description: "Cross-tool decision matrix for field-update automation in Salesforce — Before-Save Flow vs After-Save Flow vs Apex Trigger vs the deprecated Workflow Rule + Field Update. Covers the recursion / re-entrancy rules, governor cost per pattern (Before-Save flow is governor-free for the same record), the order-of-execution slot each tool occupies, and the Workflow-Rule-to-Flow migration playbook for field-update-specific actions. NOT for the basic Salesforce order-of-execution sequence (use admin/order-of-execution), NOT for designing the Flow / Trigger itself (use the corresponding skill for the chosen tool)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "before save flow vs trigger field update performance"
  - "workflow rule field update migrate to flow"
  - "field update recursion same-record after save flow"
  - "cross-object field update flow vs apex trigger"
  - "field update order of execution slot"
  - "stamp same-record field on save without recursion"
tags:
  - field-update
  - automation-selection
  - before-save-flow
  - after-save-flow
  - apex-trigger
  - workflow-rule-migration
inputs:
  - "Field-update target: same record being saved, parent record, child records, unrelated records"
  - "Whether the value can be derived from other fields on the same record (formula candidate)"
  - "Volume: < 200 records / day, hundreds, thousands, hundreds of thousands"
  - "Existing automation on the object (recursion risk)"
outputs:
  - "Tool choice (formula field, before-save flow, after-save flow, Apex trigger)"
  - "Order-of-execution slot the choice occupies"
  - "Recursion guard if applicable"
  - "Workflow Rule migration plan if replacing legacy automation"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
---

# Workflow Field Update Patterns

The most common automation question in Salesforce admin work: "I need
to set field X to Y when condition Z." The answer depends on whether
X is on the *same* record being saved (cheap, before-save flow), the
parent (cross-object after-save), or a child (multi-record DML),
plus volume, recursion risk, and whether the value can be derived as
a formula instead of stamped.

This skill is the decision layer. It does NOT teach you to build the
chosen tool — `flow/flow-best-practices`, `apex/trigger-framework`,
and so on cover that. It also doesn't redefine the Salesforce
order-of-execution sequence — see `admin/order-of-execution`.

What this skill IS: a decision matrix between the four field-update
tools (formula, before-save flow, after-save flow, Apex trigger),
plus the migration playbook for replacing legacy Workflow Rule
field-update actions (deprecated as of late-2022).

---

## Before Starting

- **Confirm the field-update need.** If the value is purely a
  derivation of other fields on the same record, a **formula field**
  is the right answer — no automation needed at all. Don't reach
  for flow / trigger if formula fits.
- **Identify the target record.** Same record being saved, parent,
  child, unrelated. Different targets need different tools.
- **Identify the volume.** < 200 records per save event = standard
  paths. Bulk loads of 1M records hit Apex governor budgets that
  Flow can't always handle.
- **Inventory existing automation on the target object.** Adding a
  new before-save flow to an object that already has 3 triggers and
  2 flows is the recursion-risk territory.

---

## Core Concepts

### The four field-update tools

| Tool | Target | Governor cost | Order-of-execution slot |
|---|---|---|---|
| **Formula field** | Same record, derived | Free (computed at read time) | N/A — not stored |
| **Before-Save Flow** | Same record, stamped | Governor-free for same-record updates | After validation, before save |
| **After-Save Flow** | Same record (re-DML), parent, child, unrelated | DML governor against limit | After before-triggers + before-save flows |
| **Apex Trigger (before-update)** | Same record, stamped | Same as before-save flow | Same slot (before-save flows are processed alongside) |
| **Apex Trigger (after-update)** | Parent / child / unrelated via DML | DML governor | After after-save flows |

The standout: **before-save flows updating the same record being
saved are governor-free**. They don't fire a second DML; they
modify the in-flight record before commit. This is the cheapest
field-update mechanism on the platform.

### Same-record before-save vs same-record after-save

Updating a field on the SAME record being saved:

- **Before-save flow / trigger** — modify the in-flight record;
  no second DML; no recursion possible (it's the same save event).
- **After-save flow / trigger** — must issue an Update DML against
  the just-saved record; counts as a second DML; can recurse if the
  trigger that produced the update fires again on its own update.

The platform charges you (in DML, governor budget, recursion risk)
to do the same work after-save that you can do free before-save.
Before-save is the right choice unless you specifically need a value
that's only computed after the initial save (record Id on insert is
the canonical example — but lookup-relationship integrity often
makes after-save the wrong shape too).

### Recursion: the after-save trap

A record-triggered after-save flow that updates a field on the same
record fires again on its own update. Without a guard, infinite loop
— Salesforce's recursion-detection cuts it at around 16 levels with
an exception. With a guard (a custom static variable, a field-set
check, a "do nothing if X is already set" decision branch in the
flow), the second invocation no-ops.

The cleanest guards:

- **`isChanged(Field__c)` decision** in the flow's entry condition
  — only run if the field-being-updated changed.
- **Static `Set<Id>` recursion sentinel** in Apex — track which
  records the trigger has already processed in this transaction.
- **Don't write the value if it already matches** — decision branch
  before the Update Records element.

### Order of execution overlap with other automation

Salesforce's published order-of-execution puts:

1. System validation rules
2. **Before-save flows + before-update triggers (interleaved order
   not guaranteed)**
3. Custom validation rules
4. Duplicate rules
5. Save the record
6. **After-save flows + after-update triggers (interleaved order
   not guaranteed)**
7. Assignment rules, auto-response rules, escalation rules,
   workflow rules (if any), processes, entitlement rules
8. Roll-up summary fields recalculate
9. Commit

Field updates from **flows can fire other before-save flows /
triggers**. Field updates from **after-save automation re-enter the
loop** — this is the recursion source. Plan for it.

### Workflow Rule field-update deprecation

Workflow Rules with Field Update actions stopped being creatable in
new orgs and stopped accepting new Field Update actions on existing
rules in late 2022. They still RUN in orgs that have them; they're
not deleted. The migration target is record-triggered flow —
typically before-save for same-record stamps, after-save for
cross-object updates. The migration tool surfaces them in Setup; the
mapping is straightforward.

---

## Common Patterns

### Pattern A — Same-record stamp via before-save flow

**When to use.** Stamp `Account.Last_Reviewed_Date__c` to TODAY when
`Account.Status__c = 'Active'`. Same record, derived, no parent /
child involvement.

**Approach.** Record-triggered flow on `Account`, before-save,
entry condition `Status__c = 'Active' AND ISCHANGED(Status__c)`.
Single Update Records element setting `Last_Reviewed_Date__c =
{!$Flow.CurrentDate}`. Done.

**Why before-save.** Free (no DML), no recursion possible.

### Pattern B — Same-record stamp where formula would be enough

**When to use.** `Opportunity.Display_Stage__c = "Won (" +
TEXT(StageName) + ")"` for a custom UI rendering.

**Wrong instinct.** Build a flow that stamps it on every save.

**Right answer.** **Formula field**. Computed at read time, no
storage, no automation, no recursion, no stale-value risk.

If the formula approach can express it, that's the right answer.
Reach for flow / trigger only when the value can't be expressed as
a formula (depends on related-record state that formulas can't
traverse, requires history that formulas don't have access to,
needs to be settable by other automation downstream).

### Pattern C — Cross-object update via after-save flow

**When to use.** When `Case.Status__c = 'Closed'`, decrement the
parent `Account.Open_Cases__c` by 1.

**Approach.** Record-triggered flow on `Case`, after-save (must be
after-save — cross-object DML can't happen in before-save). Update
Records element on the parent Account, decrementing the field.

**Recursion guard.** The Account update doesn't fire a Case trigger,
so no Case-side recursion. But the Account-side automation may
react. Account before-save flow that re-stamps a derived field on
Account is fine; Account after-save flow that updates Account's
own fields is the standard recursion territory.

### Pattern D — Apex trigger when flow can't express the logic

**When to use.** Field update requires complex logic — a Schema
describe call, a callout result, a Type.forName dispatch, a
batched DML across multiple objects in one transaction.

**Approach.** Use `templates/apex/TriggerHandler.cls` as the base.
Recursion guard via static `Set<Id>`. Bulkify; the trigger fires
for batches up to 200 (or 2000 for Platform Event triggers).

The honest cost: Apex requires test coverage, deploy via metadata,
admin can't edit it. Use only when flow can't express it.

### Pattern E — Migrating Workflow Rule field updates

**When to use.** Existing org with Workflow Rules that include
Field Update actions; modernizing to flow.

**Per-rule mapping.**

| Workflow concept | Flow equivalent |
|---|---|
| Rule trigger "created" / "edited" / "created and any time edited" | Record-triggered flow start setting matching the trigger choice |
| Rule criteria | Flow entry condition |
| Field Update action | Update Records element setting the same field |
| Re-evaluate workflow rules after field changes | Default flow behavior (chains downstream automation) |

**Migration order.** Use Salesforce's Migrate to Flow tool (Setup
→ Workflow Rules → Migrate to Flow). It produces a draft flow that
you review, test, activate, and only THEN deactivate the original
Workflow Rule. Don't deactivate first; the gap leaves the field
unstamped.

---

## Decision Guidance

| Situation | Approach | Reason |
|---|---|---|
| Value is purely derived from other fields on same record | **Formula field** | No automation; no recursion; no governor cost |
| Stamp same-record field on save | **Before-save flow** | Governor-free; no recursion possible |
| Cross-object update (parent / child / unrelated) | **After-save flow** | Cross-object DML requires after-save context |
| Logic is too complex for flow (callouts, Schema describe, etc.) | **Apex trigger** | Use TriggerHandler template + recursion guard |
| Existing Workflow Rule field update | **Migrate to record-triggered flow** | Workflow Rule field updates are deprecated for new actions |
| Volume > 100K records on a single save event | **Apex with explicit bulkification** | Flow governor budget can be tight at extreme bulk |
| Field update fires on every record save indiscriminately | **Add ISCHANGED() entry condition** | Otherwise the automation runs on every save, even no-op |
| After-save flow updating the same record's other field | **`isChanged()` guard** | Default behavior recurses |
| Field update produces a value that triggers other automation | **Document the chain** | Each automation level adds governor pressure |
| Multiple admins each adding their own field-update flow | **Consolidate into one flow per object** | "One flow per save event" prevents per-flow overhead and ordering ambiguity |

---

## Recommended Workflow

1. **Try formula field first.** If the value is derived from same-record fields, no automation is the right answer.
2. **If automation needed: same record? → before-save flow.**
3. **Cross-object? → after-save flow.**
4. **Logic too complex for flow? → Apex trigger** (template + recursion guard).
5. **Existing Workflow Rule? → Migrate to Flow tool**, test in sandbox, deactivate WFR last.
6. **Always add an entry condition** that scopes the flow to actual changes (`ISCHANGED()`, status transitions, etc.) — don't run on every save.
7. **Document the recursion guard** for any after-save flow / trigger that updates fields on the triggering object.

---

## Review Checklist

- [ ] Formula field was considered before reaching for flow / trigger.
- [ ] Before-save flow used when same-record stamp doesn't need post-save context.
- [ ] After-save flow / trigger has a recursion guard (`ISCHANGED` or static set).
- [ ] Entry condition scopes the automation to relevant changes only.
- [ ] Workflow Rule field updates have been migrated (or migration is planned with deactivation gating).
- [ ] One flow per object per save event (no fragmented per-team flows that all fire).
- [ ] Apex trigger uses `templates/apex/TriggerHandler.cls` if a trigger is the right answer.

---

## Salesforce-Specific Gotchas

1. **Before-save flows are governor-free for same-record updates.** Don't re-implement same-record stamps in after-save. (See `references/gotchas.md` § 1.)
2. **After-save flow updating the same record recurses without a guard.** Default behavior; explicit guard required. (See `references/gotchas.md` § 2.)
3. **Workflow Rule field updates are deprecated for new actions** as of late 2022 — migrate or accept they're frozen. (See `references/gotchas.md` § 3.)
4. **Formula fields are computed at read time, not stored.** Reports / dashboards can sort / filter on them but at query cost. (See `references/gotchas.md` § 4.)
5. **Order of execution interleaves before-save flows with before-update triggers** — relative ordering between them is not guaranteed. (See `references/gotchas.md` § 5.)
6. **Cross-object update from a flow fires the target object's automation.** Plan the chain. (See `references/gotchas.md` § 6.)
7. **Multiple flows on the same object firing on the same save event** all run; ordering is not guaranteed across flows. (See `references/gotchas.md` § 7.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Field-update tool decision | Formula / before-save flow / after-save flow / trigger, with rationale |
| Recursion-guard implementation | `ISCHANGED` / static set / decision-branch — explicit and tested |
| Entry condition expression | Scope the automation to relevant changes |
| Workflow Rule migration plan | If applicable: Migrate-to-Flow output, sandbox test, deactivation gating |

---

## Related Skills

- `admin/order-of-execution` — broader save-time sequencing; this skill is the field-update slice.
- `flow/flow-best-practices` — building the chosen flow.
- `apex/trigger-framework` — building the chosen trigger; canonical template at `templates/apex/TriggerHandler.cls`.
- `flow/flow-error-notification-patterns` — fault handling for after-save flows.
- `apex/dynamic-apex` — when an Apex trigger needs Schema describe calls.
