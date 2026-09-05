# Gotchas — What A Flow Can And Cannot Observe At Each Save-Order Step

Every step number below is from the Apex Developer Guide, *Triggers and Order
of Execution* (`apexdev.txt` L15416–L15489). Each entry is a platform
behaviour that surprises people, not advice.

## Gotcha 1: Custom validation rules run after the before-save flow, so the flow's own value is what gets rejected

**What happens:** a before-save flow assigns a value that a validation rule
then blocks, and the error names a field the user never touched.

**When it occurs:** any save where the flow at step 3 writes a field the rule
at step 5 tests. The guide's step 5 is "Runs most system validation steps
again … and runs any custom validation rules" (`apexdev.txt` L15442–L15444) —
two steps after the flow. It also names the one exception: "The only system
validation that Salesforce doesn't run a second time (when the request comes
from a standard UI edit page) is the enforcement of layout-specific rules."
So a layout-required field is checked at step 2 only, against the value the
*user* submitted, and a before-save flow blanking it afterwards will not be
caught.

**How to avoid:** treat the before-save flow as an input to validation, not an
escape from it. Either set every field the rule needs in the same flow, or
scope the rule so the flow-written value is legal. Never "fix" it by moving
the assignment to after-save — that adds a save cycle without changing which
rule ran.

## Gotcha 2: Duplicate rules also see the flow's value — and a block stops the transaction before any after-save flow exists

**What happens:** a before-save flow normalises a field into a shape the
matching rule keys on, and the save is blocked as a duplicate. The step-14
after-save flow that was supposed to handle the record never runs at all, and
nothing writes an error row.

**When it occurs:** step 6 follows step 3, so duplicate rules match on
flow-populated values, not on submitted ones. The guide is explicit about what
a block costs: "If the duplicate rule identifies the record as a duplicate and
uses the block action, the record isn't saved and no further steps, such as
after triggers and workflow rules, are taken" (`apexdev.txt` L15445–L15446).
Steps 7 through 20 are all "further steps".

**How to avoid:** if a flow writes any field a matching rule uses, review the
rule and the flow together. The widespread belief that a duplicate rule cannot
see a before-save flow's write is backwards — it can, because step 6 is later
than step 3. Design fault handling on the assumption that a block leaves you
with no after-save flow, no after trigger and no log row.

## Gotcha 3: The before trigger is the later writer, so it wins any shared field

**What happens:** a before-save flow and an Apex before trigger both assign
the same field. The trigger's value is the one on the saved record, every
time — no race, no org-dependent behaviour.

**When it occurs:** always. Step 3 is "Executes record-triggered flows that
are configured to run before the record is saved" and step 4 is "Executes all
before triggers" (`apexdev.txt` L15440–L15441) — separate, consecutive,
numbered steps. Anything claiming the two share step 3 or that the outcome is
indeterminate is quoting a superseded revision of the page.

**How to avoid:** give the field one owner. If both genuinely must write,
condition the **trigger**, because the flow has already finished by the time
the trigger runs — conditioning the flow changes nothing.
**UNVERIFIED (2026-09-05): `apexdev.txt` states the step ordering but does not
state last-writer-wins semantics for two automations assigning the same
in-flight field.** The conclusion follows from the ordering; confirm in a
debug log before designing a shared field deliberately.

## Gotcha 4: A before-save flow cannot see anything produced at step 8 or later

**What happens:** a before-save flow reads `OwnerId` on a new Case, or a
roll-up on the parent, or the record's own `Id`, and gets the pre-save value.

**When it occurs:** on every insert. The row is not written until step 7, the
assignment-rule owner is not chosen until step 9, workflow field updates land
at step 11, and the parent roll-up is not recalculated until step 16 — all
after step 3.

**How to avoid:** pick the automation by the step it needs, not by the tool
you prefer. Something that must see the assigned owner belongs at step 14 or
later; something that must see a recalculated roll-up belongs in the parent's
own save (see Gotcha 8).

## Gotcha 5: An after-save flow's DML re-enters the save order, but a *truncated* one

**What happens:** an after-save flow updates a record, that update runs its
own save procedure, and the automation you expected to fire on the second pass
silently does not.

**When it occurs:** whenever a flow does DML. "When a process or flow executes
a DML operation, the affected record goes through the save procedure"
(`apexdev.txt` L15468). But that nested pass is a recursive save, and "During
a recursive save, Salesforce skips steps 9 (assignment rules) through 17
(roll-up summary field in the grandparent record)" (`apexdev.txt`
L15414–L15415). Steps 1–8 and 18–20 run; assignment, auto-response, workflow,
escalation, Process Builder, **after-save flows (14)**, entitlement rules and
both roll-up steps do not.

**How to avoid:** when a flow's write must trigger something, put that
something at a step the recursive save still runs — a before-save flow (3), a
before trigger (4) or an after trigger (8). Do not route it through a second
after-save flow. The runaway barrier, if you reach it, is documented: "Total
stack depth for any Apex invocation that recursively fires triggers due to
insert, update, or delete statements" is **16** (`apexdev.txt` L19559). That
is a crash limit, not a design budget.

## Gotcha 6: `doesRequireRecordChangedToMeetCriteria` tests a transition, not a state — which is why it stops loops

**What happens:** a flow with a plain `Status = 'Escalated'` entry filter fires
again on every later edit while the record is still escalated, creating a
duplicate task or a double-counted metric each time.

**When it occurs:** on the second and every subsequent update. The switch that
changes this is documented as: "If set to true, conditions evaluate to true
only if the record didn't meet the required conditions before the triggering
update but now meets the conditions after the update" (`api_meta.txt`
L72322–L72325, API 50.0 and later). Note the wording — "before the triggering
**update**". It is defined against an update, so it does no work for a
`recordTriggerType` of `Create`.

**How to avoid:** set
`<doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>`
whenever the requirement is a *becomes*, and pair it with a marker field when
the record can legitimately cross the boundary more than once. The two guards
cover different cases: the transition test covers repeat edits inside one
state, the marker covers repeat crossings across transactions. See
`references/metadata-examples.md` § 2 for both in one flow.
`flow/record-triggered-flow-patterns` owns the choice of trigger context
itself.

## Gotcha 7: A workflow field update re-fires triggers but never re-fires flows

**What happens:** a legacy workflow field update changes a value, an Apex
before-update trigger sees the new value, and the record-triggered flow that
also cares about that field never runs a second time. The org behaves as if
the flow "missed" the change.

**When it occurs:** at step 11, when workflow field updates exist. The guide
enumerates exactly what re-runs: "Runs system validations again. Custom
validation rules, flows, duplicate rules, processes built with Process
Builder, and escalation rules aren't run again", then "Executes before update
triggers and after update triggers, regardless of the record operation
(insert or update), one more time (and only one more time)" (`apexdev.txt`
L15455–L15460).

**How to avoid:** do not leave a workflow field update writing a field that a
flow's entry criteria depend on. There is a second trap in the same area:
"If a workflow rule field update is triggered by a record update, `Trigger.old`
doesn't hold the newly updated field by the workflow after the update"
(`apexdev.txt` L15494–L15497) — the re-fired trigger's old map shows the value
from before the *original* edit, not from before the workflow's edit.

## Gotcha 8: A roll-up-driven parent save never reaches the parent's after-save flow

**What happens:** a child record changes, the parent's roll-up recalculates,
and the parent's after-save flow — written specifically to react to that
number — never executes. No error, no log row.

**When it occurs:** at step 16, "If the record contains a roll-up summary
field or is part of a cross-object workflow, performs calculations and updates
the roll-up summary field in the parent record. Parent record goes through
save procedure" (`apexdev.txt` L15472–L15473). That parent save is a recursive
save, so steps 9–17 are skipped — and after-save flows are step 14.

**How to avoid:** hook the parent's *before* or *after trigger* (steps 4 and 8,
both of which still run on a recursive save). The child's own after-save flow
is not a substitute: it runs at step 14 of the child's save, before the parent
recalculation at step 16, so it would have to compute the number itself.
Step 16 is also before the commit at step 19 — "roll-ups recalculate after
commit" is a common but incorrect gloss.

## Gotcha 9: After triggers cannot see the assignment-rule owner; after-save flows are on the other side of that line

**What happens:** an after-insert Apex trigger on Case or Lead emails "the
assigned owner" and mails the record creator instead.

**When it occurs:** always, on Case and Lead. All after triggers are step 8;
"Executes assignment rules" is step 9 (`apexdev.txt` L15448–L15449). The
`AssignmentRule` sObject "Represents an assignment rule associated with a Case
or Lead" (`object_reference.txt` L7044), so other objects skip step 9
entirely — assignment on Account is a territory feature, and the REST
Assignment Rule Header covers "Accounts, Cases, or Leads" for that reason
(`api_rest.txt` L692–L694).

**How to avoid:** put owner-dependent side effects at step 14 (after-save
flow) or later, not step 8. The step boundary favours flows here — one of the
few places it does.
**UNVERIFIED (2026-09-05): `apexdev.txt` places the after-save flow at step 14
but does not state whether the flow's `$Record` snapshot is refreshed with
field values written at steps 9–13.** Read one debug log before shipping a
design that depends on it.

## Gotcha 10: An `AsyncAfterCommit` scheduled path reads committed data and cannot roll the save back

**What happens:** an async path fails, the user sees a successful save, and
the downstream record is never written. Nothing rolls back, because there is
nothing left to roll back.

**When it occurs:** every time. `pathType` `AsyncAfterCommit` means "the
scheduled path runs asynchronously after a save" (`api_meta.txt`
L71414–L71415), and step 20 is "After the changes are committed to the
database, executes post-commit logic", whose examples include "Asynchronous
paths in record-triggered flows" (`apexdev.txt` L15479, L15489). The commit at
step 19 has already happened.

**How to avoid:** design the async path as its own unit of work — fault paths
that write a durable log row, and a way to replay. Treat "the save succeeded"
and "the async path succeeded" as two separate facts, because the platform
does.

## Gotcha 11: A flow's platform event can be published before the save it belongs to succeeds

**What happens:** a flow publishes a platform event, the transaction then
fails, and a subscriber acts on a record change that never happened.

**When it occurs:** when the event's `publishBehavior` is
`PublishImmediately` — "the event message is published when the publish call
executes, regardless of whether the transaction succeeds". The alternative,
`PublishAfterCommit`, means "the event message is published only after a
transaction commits successfully. If the transaction fails, the event message
isn't published." **The default is `PublishImmediately`** (`api_meta.txt`
L42222–L42229). Step 19 is the commit, and a step-14 flow publishes five steps
earlier — with plenty left to fail: entitlement rules (15), parent and
grandparent saves (16, 17) and criteria-based sharing (18).

**How to avoid:** set `publishBehavior` to `PublishAfterCommit` on any event a
record-triggered flow publishes to represent "this record changed". Leave
`PublishImmediately` for signals that are true regardless of the save's fate.

## Gotcha 12: Platform-event-triggered and schedule-triggered flows are not in this list at all

**What happens:** someone reasons about a platform-event-triggered flow as if
it sits between two steps of the save order and expects it to see, or block,
the save.

**When it occurs:** whenever the flow is not a record-triggered flow. The
order of execution is scoped to "When you save a record with an insert,
update, or upsert statement" (`apexdev.txt` L15403–L15404); the only flow
entries in the list are step 3, step 13 (Process Builder and flows launched by
workflow rules, "not in a guaranteed order", `apexdev.txt` L15462–L15463),
step 14, and asynchronous paths at step 20.

**How to avoid:** reason about them separately, and do not put a numbered step
next to them in a design document.
**UNVERIFIED (2026-09-05): that a platform-event-triggered flow runs in a
transaction separate from the publishing save is not stated in `apexdev.txt`,
`api_meta.txt` or `object_reference.txt`.** What *is* grounded is the
publish-timing switch in Gotcha 11 and the absence of any such flow from the
20-step list.

## Gotcha 13: The flow's own `apiVersion` moves it in the save order

**What happens:** a flow retrieved from an old org and redeployed unchanged
runs at a different point than a newly authored one, and an entitlement-driven
field it depends on is populated in one case and not the other.

**When it occurs:** below API 54.0. The guide's "Additional Considerations"
states: "In API version 53.0 and earlier, after-save record-triggered flows
run after entitlements are executed" (`apexdev.txt` L15509) — that is, after
step 15 rather than before it.

**How to avoid:** read `<apiVersion>` before reasoning about any inherited
flow's position, and treat an `apiVersion` bump as a behavioural change that
needs a test, not as housekeeping.

## Gotcha 14: Two triggers on the same object have no order, and neither do two flows inside one step

**What happens:** two before-insert Apex triggers, or two after-save flows
with no `triggerOrder`, produce different results on different saves.

**When it occurs:** as soon as there is a second one. For Apex the guide is
blunt: "If more than one trigger is defined on an object for the same event,
the order of trigger execution isn't guaranteed" (`apexdev.txt`
L15502–L15504). For flows, steps 3 and 14 each name the category once and
never rank the members; `triggerOrder` ("the run order of a record-triggered
flow, from 1 to 2,000", API 54.0 and later, `api_meta.txt` L68438–L68441) is
the only rank the Metadata API offers, and it is nullable.

**How to avoid:** one trigger per object routed through a handler
(`apex/trigger-and-flow-coexistence`), and a declared `triggerOrder` on every
co-resident flow — rule R3 of this skill's checker.
`flow/flow-governance` owns the portfolio-level rule and the merge gate.

## Gotcha 15: A before-save flow is not allowed the elements that would let it act on another row

**What happens:** Flow Builder refuses to save a `RecordBeforeSave` flow that
contains a Create/Update/Delete Records element, an action that sends email or
publishes a platform event, or a scheduled path — so the design has to be
split before it can be built, not after.

**When it occurs:** at design time, not at runtime, which is why it usually
surfaces after the flow has already been drawn.

**How to avoid:** decide the split first: same-record field assignments go in
the step-3 flow, everything else in a step-14 flow that the same entry
criteria select. Checker rule R4 reports the shape.
**UNVERIFIED (2026-09-05): this prohibition is not stated in `api_meta.txt`,
`apexdev.txt` or `object_reference.txt`. `api_meta.txt` defines
`recordCreates`, `recordDeletes` and `recordUpdates` in the `Flow` field
table (L68363, L68365, L68372), `actionCalls`, `subflows` and `waits` in the
same table, and `scheduledPaths` on `FlowStart` (L72465–L72466) — none of them
restricted by `triggerType`; the rule is
documented only on help.salesforce.com, which is not fetchable.** The checker
reports it as ADVISORY for that reason — confirm in a sandbox before quoting
it to a customer as a platform guarantee.

## Gotcha 16: A before-save assignment does not re-trigger the record's own automation; an after-save update does

**What happens:** teams add a recursion guard to a before-save flow that
writes `$Record`, and it does nothing, because there was never a loop to
guard. The same guard is then omitted from the after-save flow that actually
needs it.

**When it occurs:** whenever the two are treated as interchangeable ways to
set a field. The distinction is mechanical: the order of execution re-enters
only on DML — "When a process or flow executes a DML operation, the affected
record goes through the save procedure" (`apexdev.txt` L15468). A step-3
assignment to `$Record` issues no DML; it changes the row that step 7 is about
to write. An after-save `recordUpdates` on the same row issues a real update
and starts a second pass.

**How to avoid:** spend the guard where the DML is. If a same-record write is
the whole requirement, moving it to step 3 removes the loop instead of
constraining it — which is what checker rule R1 recommends.
