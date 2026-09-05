# Gotchas — Workflow Field Update Patterns

Non-obvious behaviors of Salesforce field-update automation.

---

## Gotcha 1: Before-save flows are governor-free for same-record updates

**What happens.** Many admin teams reflexively build same-record
stamps as after-save flows because that's how they learned. Each
stamp counts as a second DML, eats governor budget, and risks
recursion.

**When it occurs.** Default automation pattern across most orgs.

**How to avoid.** Use **before-save** flow for same-record stamps.
Modifies the in-flight record in place; no DML; no recursion. The
single highest-leverage admin-side performance improvement.

---

## Gotcha 2: After-save flow updating same record recurses without a guard

**What happens.** After-save flow on Account that updates an Account
field re-fires the Account trigger / flow on its own update. With no
guard, infinite loop until the platform's recursion detection cuts
it at 16 levels.

**When it occurs.** Default behavior; explicit guard required.

**How to avoid.**
- `ISCHANGED(Field__c)` in the entry condition — flow only fires
  if the field-being-updated changed.
- Decision branch: skip Update Records if the value already matches
  what we'd write.
- Migrate to before-save flow if same-record stamp doesn't need
  post-save context.

---

## Gotcha 3: Workflow Rule field updates are deprecated for new actions

**What happens.** Admin tries to add a new Field Update action to
an existing Workflow Rule. Setup blocks it: "Workflow Rule field
updates can no longer be created. Migrate to Flow."

**When it occurs.** Modernizing legacy automation; orgs created
before late-2022 still have the existing rules running.

**How to avoid.** Use the Migrate to Flow tool. Existing rules
continue to run; new automation must be flow.

---

## Gotcha 4: Formula fields are computed at read time, not stored

**What happens.** Admin builds a formula field; reports filter on
it; query performance is slower than expected. The formula
evaluates per row at query time.

**When it occurs.** High-volume objects with complex formulas in
filter / sort positions.

**How to avoid.** For very high-volume read paths, stamp the value
via before-save flow into a stored field. Formula for low-volume,
stamped for performance-critical paths. Trade is automation cost
vs query cost.

---

## Gotcha 5: Before-save flows always run before before-update triggers, so the trigger wins

**What happens.** Admin builds a before-save flow that depends on
a value stamped by a before-update trigger. It never sees that value:
the flow is step 3 and the trigger is step 4, so the flow runs first,
every time. The dependency is backwards, not flaky. The reverse
direction bites too — the trigger reads what the flow wrote and can
silently overwrite it, so the flow's value never reaches the database.

**When it occurs.** Mixing before-save flow with before-update
trigger on the same object.

**How to avoid.** Pick one tool for the same-record before-save
slot. If both must exist, write them knowing the fixed order:
step 3 (flow) then step 4 (trigger), with the trigger having the last
word before validation rules at step 5.

---

## Gotcha 6: Cross-object update from a flow fires the target object's automation

**What happens.** Flow on Case updates the parent Account's
counter. Account's own automation fires (rollup recompute, audit
field, downstream notification). Side effects multiply across the
chain.

**When it occurs.** Cross-object updates on objects with rich
automation.

**How to avoid.** Document the chain. Each automation level adds
governor pressure; bulk operations against a Case object can
cascade through Account / Contact / Opportunity automation. Plan
the chain in design, not in production triage.

---

## Gotcha 7: Multiple flows on the same object fire in non-deterministic order

**What happens.** Admin team A builds a record-triggered flow on
Account. Team B builds another. Both fire on every save. Their
relative ordering is not guaranteed; one team's flow sometimes
sees the other team's results, sometimes doesn't.

**When it occurs.** Multi-team admin orgs with fragmented flow
ownership.

**How to avoid.** Consolidate into one flow per object per
save-time slot (one before-save, one after-save). Internal
decision branches handle per-team logic. Documented ownership;
predictable order.

---

## Gotcha 8: ISCHANGED() returns true on insert (the value "changed" from null)

**What happens.** Entry condition `ISCHANGED(Field__c) AND
ISPICKVAL(Field__c, 'Closed')` fires on insert of a record with
`Field__c = 'Closed'`, not just on the close transition. Admin
expected close-transition-only behavior.

**When it occurs.** Status-transition flows that should fire only
on update, not on insert.

**How to avoid.** Add `AND PRIORVALUE(Field__c) != null` or
explicit "Run when: A record is updated" trigger setting (not
"created or updated"). Be deliberate about insert-vs-update
behavior.

---

## Gotcha 9: Migrate-to-Flow tool produces drafts; doesn't auto-deactivate the source

**What happens.** Admin uses Migrate to Flow on a Workflow Rule.
Tool creates a draft flow. Admin activates the flow but doesn't
deactivate the WFR. Both fire on every save. Field gets stamped
twice — usually idempotent but sometimes not (if the value depends
on order or accumulates).

**When it occurs.** Migration runs that miss the deactivation step.

**How to avoid.** Migration sequence: activate flow → test in
sandbox → deactivate WFR → test again → deploy both as one change
set. Deactivation is the last step, gated on flow validation.

---

## Gotcha 10: Migrating a field update to before-save Flow deletes a second trigger pass nobody wrote down

**What happens.** Step 11 of the save procedure runs workflow rules,
and if there are workflow field updates the platform "Updates the
record again… Executes before update triggers and after update
triggers, regardless of the record operation (insert or update), one
more time (and only one more time)". `admin/process-automation-selection`
§ 5 documents that behaviour and what does *not* re-run alongside it.

The field-update-specific consequence is what happens on cutover day.
Move that same field update into a before-save Flow at step 3 and the
step-11 re-save disappears with it — so every Apex trigger on the
object now executes **once** per save instead of twice, with no change
to a single line of Apex. Handlers that increment a counter, enqueue a
Queueable, fire an outbound integration, or rely on a `skipOnce()`
sentinel being consumed by a second pass all change behaviour silently.
Bugs land in the trigger, days after a deploy whose diff contained only
a Flow and a `<active>false</active>`.

**When it occurs.** Any object where an active Workflow Rule field
update and an Apex trigger coexist — the standard shape of a
half-migrated org.

**How to avoid.** Before the cutover deploy, list every Apex trigger on
the object and decide for each whether double execution was load-bearing.
Trace it in a sandbox with debug logs on: count trigger entries for one
save before and after the rule is deactivated. Treat any difference in
counter values, enqueued jobs or callouts as a migration blocker, not a
post-deploy surprise.

*Source: Apex Developer Guide, "Triggers and Order of Execution", step 11,
apexdev.txt:15451–15460.*

---

## Gotcha 11: `reevaluateOnChange` restarts every rule on the object, and Flow has no equivalent switch

**What happens.** `WorkflowFieldUpdate.reevaluateOnChange` is not a
re-run of the rule that fired it. "When set to `true`, if the field
update changes the field's value, **all** workflow rules on the
associated object are reevaluated. Any workflow rules whose criteria
are met as a result of the field value change are triggered." Chained
updates that also carry the flag keep going: "This cascade of workflow
rule reevaluation and triggering can happen up to 5 times after the
initial field update that started it."

Record-triggered Flow has no corresponding element. A migration that
maps only the field write produces an automation that runs once where
the workflow ran up to six times, and rules that only ever fired as
second-order effects of another rule's update simply stop firing.

**When it occurs.** Orgs with several rules on one object where at
least one field update sets a field another rule filters on. The
dependency is invisible in the rule list — it lives in one boolean
element inside the `fieldUpdates` block.

**How to avoid.** Grep the retrieved workflow file for
`<reevaluateOnChange>true</reevaluateOnChange>` before planning the
migration. For each hit, find every rule whose `criteriaItems` or
`formula` references the updated field; those are the rules that were
running on the cascade. Rebuild the chain explicitly — usually as
additional branches inside the one replacement Flow, evaluated in
order — rather than as separate Flows hoping to re-create it.

*Source: Metadata API Developer Guide, `WorkflowFieldUpdate`,
api_meta.txt:140186–140194.*

---

## Gotcha 12: `NextValue` and `PreviousValue` are picklist-ordinal writes with no Flow counterpart

**What happens.** Two of the six `operation` values move a picklist
along its own defined order rather than setting a value:
`NextValue` — "the field will be set to its next value" — and
`PreviousValue` — "the field is set to its previous value". Both are
"Only allowed when the field update references a picklist". The value
written depends on the picklist's value-set ordering, so reordering the
picklist in Setup changes what the automation does without touching the
automation.

Flow assignment has no "next value" operator. A migration that reads the
current production value and hardcodes it produces an automation that is
correct on the day it ships and wrong the first time someone inserts a
picklist value in the middle.

**When it occurs.** Stage-advance and status-advance rules — the classic
"nudge it to the next step" workflow — and anywhere the original author
wanted a state machine without building one.

**How to avoid.** Rebuild it as an explicit transition map, not as an
ordinal walk. Either a Decision with one outcome per source value, or a
Custom Metadata Type with `Current_Value__c` / `Next_Value__c` rows that
the Flow looks up. Both make the transition table reviewable and both
survive a picklist reorder. See `admin/design-custom-metadata` for the
CMDT shape.

*Source: Metadata API Developer Guide, `WorkflowFieldUpdate`,
`operation`, api_meta.txt:140168–140179.*

---

## Gotcha 13: A before-save Flow inherits the before-trigger write restrictions; a workflow field update never had them

**What happens.** "Some field values are set during the system save
operation, which occurs after before triggers have fired. As a result,
these fields cannot be modified or accurately detected in before insert
or before update triggers." The documented list includes
`Opportunity.Amount` (except when the Opportunity has no line items),
`Opportunity.ForecastCategory`, `Opportunity.IsWon`,
`Opportunity.IsClosed`, `Case.IsClosed`, `Task.IsClosed`,
`Solution.IsReviewed`, `Contract.ActivatedDate`, `Contract.ActivatedById`,
`Id` and `CreatedDate`.

A workflow field update writes at step 11, *after* the record has been
saved at step 7, so it was never subject to that list. Migrate such an
update into a before-save Flow at step 3 and the write silently stops
landing — the Flow activates cleanly, the interview runs, and the field
keeps its system-computed value.

**UNVERIFIED (2026-09-04)** — the guide states this restriction for before
*triggers* (step 4). Before-save Flows sit at step 3, also ahead of the
system save at step 7, so the same restriction is expected to apply, but
the guide does not say so for Flows. Confirm the specific field in a
sandbox before committing to before-save.

**When it occurs.** Opportunity and Case migrations more than any other,
because those two objects contribute most of the list.

**How to avoid.** Check the target field against the list before choosing
before-save. If it is on the list, the replacement is an **after-save**
Flow (Example 3 in `references/metadata-examples.md`), which pays a DML
but writes after the system save. Then re-read Gotcha 2 — an after-save
Flow writing the triggering record needs its recursion guard.

*Source: Apex Developer Guide, "Fields Not Updateable in Before Triggers",
apexdev.txt:15593–15612.*

---

## Gotcha 14: In the trigger pass that follows a field update, `Trigger.old` holds pre-update values, not the values the user submitted

**What happens.** "If a workflow rule field update is triggered by a
record update, `Trigger.old` doesn't hold the newly updated field by the
workflow after the update. Instead, `Trigger.old` holds the object before
the initial record update was made." The guide's own worked case: a field
starts at 1, a user sets it to 10, a workflow field update increments it
to 11 — and in the update trigger that fires after the field update,
`Trigger.old` reports **1**, not 10.

So change-detection logic in that second pass compares against a value
two steps stale. `ISCHANGED`-equivalent Apex written against the first
pass reports a different delta in the second, and code that computes
"how much did this move" double-counts.

**When it occurs.** Any Apex trigger on an object that still has an
active workflow field update — and only in the second pass, which is why
it reproduces intermittently and never in a unit test that inserts a
record without the rule active.

**How to avoid.** Do not compute deltas from `Trigger.old` on an object
that still carries a workflow field update. Read the prior value from the
record's own audit trail or from a stamped `Prior_*__c` field written in
the before-save slot. Migrating the field update away removes the second
pass and the quirk with it — which is another reason Gotcha 10's
before/after trigger-entry count belongs in the cutover plan.

*Source: Apex Developer Guide, "Triggers and Order of Execution",
Additional Considerations, apexdev.txt:15494–15499.*

---

## Gotcha 15: A field update can only look up a User, even though `lookupValueType` lists Queue and RecordType

**What happens.** `operation` `LookupValue` is described as "Similar to
`Literal`, but for an object reference, such as a contact, user, or
account. If set, the `lookupValue` element must be set. **Only User is
supported in the current API.**" The sibling `lookupValueType` enum
advertises three values — `Queue`, `RecordType`, `User` — which reads
like three supported targets and is not.

The practical shape: "reassign the record to the escalations queue"
could never be a workflow field update. Whatever the org does today for
that requirement is an assignment rule, a process, or manual work — and
a migration inventory that assumes queue assignment lived in the workflow
layer will look for something that was never there.

**When it occurs.** Ownership and record-type automation inventories,
where the `lookupValueType` enum is read as the capability list.

**How to avoid.** Read `operation` first and `lookupValueType` second.
When a Flow replacement *does* assign `OwnerId` to a Queue Id, record it
as new capability in the migration notes, not as parity — it changes who
sees the record, so it belongs in the sharing review, not the automation
review. See `admin/design-assignment-rules` for where queue assignment
actually lives.

*Source: Metadata API Developer Guide, `WorkflowFieldUpdate`,
`lookupValueType` and `operation`, api_meta.txt:140148–140172.*

---

## Gotcha 16: A rule with both immediate and time-dependent field updates becomes two Flows, not one

**What happens.** `WorkflowRule.workflowTimeTriggers` holds a
`WorkflowTimeTrigger`: an `offsetFromField` (a date field such as Created
Date, Last Modified Date, Rule Trigger Date, or a custom date field), a
`timeLength` where "A negative value represents the time length before
the trigger fires", and a `workflowTimeTriggerUnit` of `Hours` or `Days`.
Its `actions` array can hold field updates, exactly like the rule's
immediate `actions` array.

The Flow equivalent is `start/scheduledPaths` — and scheduled paths exist
only on **after-save** Flows. A rule whose immediate field update maps
cleanly to a cheap before-save Flow, but whose time-dependent field update
needs an after-save Flow with a scheduled path, cannot be one Flow. It is
two, on the same object, in different save-time slots — which is exactly
the fragmentation Gotcha 7 warns about, arriving as a consequence of the
migration rather than a choice.

**When it occurs.** Escalation-shaped rules: stamp a flag now, stamp an
overdue flag in 48 hours. Common on Case and on any custom object with an
SLA.

**How to avoid.** Split the inventory by `workflowTimeTriggers` presence
before estimating. Rules with time triggers cost more and land as
after-save Flows; plan the pair together, name them so the relationship is
obvious, and document that the before-save half is the reason there are
two. `flow/flow-time-based-patterns` owns the scheduled-path design.
Check `WorkflowRule.failedMigrationToolVersion` in the same pass — it is
recorded on the *rule*, so one un-migratable field update flags the whole
rule (`admin/process-automation-selection` § 10).

*Source: Metadata API Developer Guide, `WorkflowTimeTrigger`
(api_meta.txt:140524–140545) and `WorkflowRule.workflowTimeTriggers`
(api_meta.txt:140432–140442); `FlowStart.scheduledPaths`
(api_meta.txt:72465–72467).*
