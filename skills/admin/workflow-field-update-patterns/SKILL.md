---
name: workflow-field-update-patterns
description: "Cross-tool decision matrix for field-update automation in Salesforce — Before-Save Flow vs After-Save Flow vs Apex Trigger vs the deprecated Workflow Rule + Field Update. Covers the recursion / re-entrancy rules, governor cost per pattern (Before-Save flow is governor-free for the same record), the order-of-execution slot each tool occupies, and the Workflow-Rule-to-Flow migration playbook for field-update actions. NOT for the full record-save order of execution — use apex/order-of-execution-deep-dive. NOT for building the record-triggered Flow once the tool is chosen — use flow/record-triggered-flow-patterns. Trigger keywords: WorkflowFieldUpdate, reevaluateOnChange, onCreateOrTriggeringUpdate, doesRequireRecordChangedToMeetCriteria, failedMigrationToolVersion, Migrate to Flow, workflow-meta.xml, field update deprecated, double writer, second trigger pass."
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
  - "my trigger runs twice on every save"
  - "field stopped being set after I deactivated the workflow rule"
  - "before-save flow assigns the field but the value does not save"
  - "what replaces reevaluateOnChange in flow"
  - "flow has no next value operation for a picklist field update"
  - "cannot add a new field update action to a workflow rule"
  - "workflow rule and flow both writing the same field"
  - "trigger.old shows the wrong prior value after a field update"
  - "how do I inventory every workflow field update in the org"
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
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
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

## Questions to Ask Before Configuring

Ask these before opening Flow Builder. Each one maps to a specific way this
goes wrong later; skipping them produces automation that works on the demo
record and diverges from the legacy behaviour it replaced.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which record does the value land on — this one, its parent, its children, or an unrelated one?" | Same-record is a free before-save Assignment; anything else is a DML and re-enters the save procedure | The tool, the order-of-execution slot, and whether a recursion guard is needed at all |
| "Is the target field one the platform computes during save — `IsClosed`, `Amount` with line items, `ForecastCategory`, `ActivatedDate`?" | Before-save cannot write those; the workflow field update at step 11 could | The choice between before-save and after-save, before the Flow is built and found to do nothing (§ 13) |
| "Does the existing rule carry `reevaluateOnChange`, a `targetObject`, or a `workflowTimeTriggers` block?" | Each maps to something Flow does differently, or not at all | The real scope: one Flow, two Flows, or a cascade to rebuild by hand (§§ 11, 16) |
| "Which Apex triggers already run on this object, and how many times does each run today?" | A field update forces a second update-trigger pass; removing it removes that pass | A measured before/after trigger-entry count instead of a post-deploy incident (§ 10) |
| "Does anything read this field later in the same transaction?" | Step 3 and step 11 are eight steps apart; readers in between see different values | The list of downstream consumers that have to be re-tested, not just the field itself |
| "Is the source rule `onCreateOnly`, `onCreateOrTriggeringUpdate`, or `onAllChanges`?" | It maps to a pair of Flow settings, and getting the pair wrong changes fire frequency without any error | The correct `recordTriggerType` plus `doesRequireRecordChangedToMeetCriteria`, verified by parity rows 4 and 6 |
| "Who owns the field, and what breaks if it stops being written for an hour?" | Decides whether cutover can be a single deploy or needs a dual-write window | The rollback plan, and whether the deploy can go out on a Friday |

What a proper configuration adds over just building the Flow: the replacement
fires on exactly the saves the old rule fired on, every Apex trigger on the
object still runs the number of times its author assumed, and the field-history
row after cutover proves which writer produced the value.

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

Salesforce's published order-of-execution is a fixed 20-step sequence.
The steps this skill touches, using the documented step numbers:

| Step | What runs |
|---|---|
| 3 | Before-save record-triggered flows |
| 4 | Before triggers |
| 5 | System validation and custom validation rules |
| 6 | Duplicate rules |
| 7 | Record saved to the database, not yet committed |
| 8 | After triggers |
| 9–12 | Assignment, auto-response, workflow rules (11 — where Workflow Rule field updates fire), escalation |
| 13 | Process Builder and workflow-launched flows, **not in a guaranteed order** — the one genuinely indeterminate slot |
| 14 | After-save record-triggered flows |
| 15 | Entitlement rules |
| 16–17 | Roll-up summary fields recalculate on parent, then grandparent |
| 19 | Commit |

Before-save flows (3) and before-update triggers (4) are **separate,
ordered steps** — the flow always runs first. The same holds for after
triggers (8) and after-save flows (14): the trigger always runs first,
with steps 9–13 in between. Neither pair is interleaved.

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

**Where each `operation` lands.** `WorkflowFieldUpdate.operation` has
six values and they do not all have a Flow equivalent. The full
element-by-element mapping — including entry criteria, trigger type and
time triggers — is the table in `references/metadata-examples.md`.

| `operation` | Replacement |
|---|---|
| `Literal` | Assignment with a typed literal value |
| `Formula` | `formulas` resource + Assignment by `elementReference` |
| `Null` | Assignment against an empty value; there is no null operator |
| `LookupValue` | Assignment of the Id; only `User` was ever supported here (§ 15) |
| `NextValue` / `PreviousValue` | No equivalent — rebuild as an explicit transition map (§ 12) |

**Migration order.** Use Salesforce's Migrate to Flow tool (Setup
→ Workflow Rules → Migrate to Flow). It produces a draft flow that
you review, test, activate, and only THEN deactivate the original
Workflow Rule. Don't deactivate first; the gap leaves the field
unstamped. Ship the activation and the deactivation as one deploy —
`references/metadata-examples.md` has the cutover manifest and the
field-history verification query.

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

1. **Inventory before designing.** Retrieve `Workflow` with the wildcard manifest in
   `references/metadata-examples.md`, then run
   `python3 scripts/check_workflow_field_update_patterns.py --manifest-dir force-app/main/default`.
   The inventory block gives the counts that set the scope: field updates per object,
   `reevaluateOnChange` flags, `targetObject` cross-object updates, time triggers, and rules
   that already defeated the Migrate to Flow tool.
2. **Rule the field out of automation entirely.** If the value is a function of same-record
   fields at read time, it is a formula field — `references/examples.md` Example 4 has the
   `CustomField` XML and the one behavioural difference (`formulaTreatBlanksAs`) to check
   before deleting the automation it replaces.
3. **Answer the seven questions above and route.** `automation-selection.md` Q2 (same record,
   under ~10s) → before-save Flow; Q4/Q5 (crosses objects, linear) → after-save Flow; Q3
   (callout retry, savepoints, recursive same-object DML) → Apex on
   `templates/apex/TriggerHandler.cls`. `flow-pattern-selector.md` Q3 confirms before-save vs
   after-save; Q5 routes a time trigger to a scheduled path.
4. **Build from the matching example, not from scratch.**
   `references/metadata-examples.md` Example 2 (before-save Flow), Example 3 (after-save,
   `targetObject` case), Example 4 (Apex `beforeUpdate` excerpt). Map every legacy element
   through the table there; anything with no row is a design decision to record, not to skip.
5. **Fill `templates/workflow-field-update-patterns-template.md`.** Sections 3 and 4 are the
   ones that catch migrations: the element-by-element legacy mapping, and the measured
   trigger-entry count per save before and after the cutover.
6. **Run the checker against the change, not just the org.** Re-run
   `check_workflow_field_update_patterns.py --manifest-dir <tree>` on the branch. Zero ERRORs is
   the deploy gate; the double-writer WARN firing means the cutover is only half-built.
7. **Parity-test, then cut over in one deploy.** Run the seven-row table from
   `references/metadata-examples.md` with the legacy rule live, then with it deactivated —
   identical results both times. Deploy the `Active` Flow and `<active>false</active>` together,
   then confirm with the field-history query.

---

## Review Checklist

- [ ] Formula field was considered before reaching for flow / trigger.
- [ ] Before-save flow used when same-record stamp doesn't need post-save context.
- [ ] After-save flow / trigger has a recursion guard (`ISCHANGED` or static set).
- [ ] Entry condition scopes the automation to relevant changes only.
- [ ] Workflow Rule field updates have been migrated (or migration is planned with deactivation gating).
- [ ] One flow per object per save event (no fragmented per-team flows that all fire).
- [ ] Apex trigger uses `templates/apex/TriggerHandler.cls` if a trigger is the right answer.
- [ ] `check_workflow_field_update_patterns.py --manifest-dir` reports zero ERRORs on the branch.
- [ ] Every legacy element has a row in the mapping table, including `reevaluateOnChange`, `targetObject` and `workflowTimeTriggers` — or a recorded decision that it is intentionally dropped.
- [ ] Trigger-entry count per save measured before and after the cutover, and any difference accepted in writing.
- [ ] Target field checked against the "not updateable in before triggers" list before choosing before-save.
- [ ] Parity table run twice — legacy rule live, then deactivated — with identical results.
- [ ] Flow activation and rule deactivation ship in the same `package.xml`.
- [ ] Post-deploy field-history query returns a new row for the field.

---

## Salesforce-Specific Gotchas

1. **Before-save flows are governor-free for same-record updates.** Don't re-implement same-record stamps in after-save. (See `references/gotchas.md` § 1.)
2. **After-save flow updating the same record recurses without a guard.** Default behavior; explicit guard required. (See `references/gotchas.md` § 2.)
3. **Workflow Rule field updates are deprecated for new actions** as of late 2022 — migrate or accept they're frozen. (See `references/gotchas.md` § 3.)
4. **Formula fields are computed at read time, not stored.** Reports / dashboards can sort / filter on them but at query cost. (See `references/gotchas.md` § 4.)
5. **Before-save flows run at step 3, before-update triggers at step 4** — the order is fixed and documented, so a before trigger always sees values the before-save flow already wrote, and can overwrite them. (See `references/gotchas.md` § 5.)
6. **Cross-object update from a flow fires the target object's automation.** Plan the chain. (See `references/gotchas.md` § 6.)
7. **Multiple flows on the same object firing on the same save event** all run; ordering is not guaranteed across flows. (See `references/gotchas.md` § 7.)
8. **`ISCHANGED()` is true on insert** — the value changed from null. Scope the trigger setting deliberately. (See `references/gotchas.md` § 8.)
9. **Migrate to Flow produces a draft and leaves the source rule active.** Both writers run until you deactivate it. (See `references/gotchas.md` § 9.)
10. **Retiring a field update deletes a second update-trigger pass** that no Apex author wrote down; trigger behaviour changes in a deploy containing no Apex. (See `references/gotchas.md` § 10.)
11. **`reevaluateOnChange` restarts every rule on the object, up to five cascades.** Flow has no equivalent element. (See `references/gotchas.md` § 11.)
12. **`NextValue` / `PreviousValue` walk the picklist's own order** and have no Flow counterpart; rebuild as a transition map. (See `references/gotchas.md` § 12.)
13. **A before-save Flow cannot write the fields the system computes during save** — the workflow field update at step 11 could. (See `references/gotchas.md` § 13.)
14. **In the pass after a field update, `Trigger.old` holds pre-update values,** not what the user submitted. (See `references/gotchas.md` § 14.)
15. **`LookupValue` only ever supported `User`,** despite `lookupValueType` advertising `Queue` and `RecordType`. (See `references/gotchas.md` § 15.)
16. **A rule with both immediate and time-dependent field updates becomes two Flows,** in different save-time slots. (See `references/gotchas.md` § 16.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Field-update tool decision | Formula / before-save flow / after-save flow / trigger, with rationale |
| Recursion-guard implementation | `ISCHANGED` / static set / decision-branch — explicit and tested |
| Entry condition expression | Scope the automation to relevant changes |
| Workflow Rule migration plan | If applicable: Migrate-to-Flow output, sandbox test, deactivation gating |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing the deployable XML: the legacy `Workflow` file, the before-save and after-save Flow replacements, the Apex variant, the element-by-element mapping table, `package.xml`, retrieve/deploy commands, the cutover sequence and the parity test table |
| `references/gotchas.md` | Sixteen platform behaviours that make a correct-looking field update wrong — the second trigger pass, `reevaluateOnChange`, `NextValue`, before-trigger write restrictions, `Trigger.old`, `LookupValue`, time triggers |
| `references/examples.md` | Looking for a worked case: after-save done wrong, cross-object counter, a WFR migration with the inventory commands, the formula-field replacement with its `CustomField` XML, the Apex-only case |
| `references/llm-anti-patterns.md` | Reviewing generated field-update advice — the eight failure modes assistants reproduce from pre-2022 training data |
| `references/well-architected.md` | Framing the choice against Reliability and Operational Excellence, and for the full source list with line references |
| `templates/workflow-field-update-patterns-template.md` | Before building or migrating any field update worth reviewing — the decision record, the legacy mapping table, and the cutover checklist |
| `scripts/check_workflow_field_update_patterns.py` | Inventorying an org, and as the pre-deploy gate on a migration branch (`--manifest-dir`) |

---

## Related Skills

- **admin/process-automation-selection**: Use for the tool-choice decision record and the save-procedure gotchas this skill cross-references rather than restates — step 11's second trigger pass, the recursive-save skip, `failedMigrationToolVersion`.
- **apex/order-of-execution-deep-dive**: Use when the question is the full 20-step sequence rather than the field-update slice of it.
- **flow/workflow-rule-to-flow-migration**: Use when migrating a whole rule, including alerts, tasks and outbound messages. This skill covers only the field-update action.
- **admin/flow-for-admins**: Use for the Flow XML surface in general — element ordering, `filters` vs `filterFormula`, `status` handling, activation.
- **flow/record-triggered-flow-patterns**: Use to build the replacement Flow once the slot is chosen.
- **flow/recursion-and-re-entry-prevention**: Use when the after-save variant needs a guard beyond an entry condition.
- **flow/flow-time-based-patterns**: Use when the source rule carried `workflowTimeTriggers` and the replacement needs scheduled paths.
- **apex/trigger-framework**: Use when the decision tree routes to Apex; canonical base at `templates/apex/TriggerHandler.cls`.
- **flow/flow-error-notification-patterns**: Use for fault handling on the after-save variant's DML.
- **admin/approval-processes**: Use when the field update is an approval action rather than a rule action — the same `WorkflowFieldUpdate` component, a different owner.
- **admin/formula-fields**: Use when the answer is no automation at all.
- **apex/dynamic-apex**: Use when the Apex variant needs Schema describe calls.
