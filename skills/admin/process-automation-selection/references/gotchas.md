# Process Automation Selection — Gotchas

Each entry is a platform behaviour that makes a defensible-looking tool choice wrong once it
is live. Line ranges point at the extracted Summer '26 / v62 guides named in
`references/well-architected.md` § Official Sources Used.

---

## 1. Choosing A Tool Chooses A Position In The Save Procedure

**What happens:** The four record-save automation surfaces do not run adjacently. The save
procedure executes record-triggered flows configured to run *before* the record is saved at
step 3, all before triggers at step 4, all after triggers at step 8, and record-triggered
flows configured to run *after* the record is saved at step 14. Anything the before trigger
computes at step 4 is invisible to the before-save flow that already ran at step 3.

**When it occurs:** Any object where one business rule is split across Flow and Apex, and any
time someone "just adds a before-save flow" to an object that already has a before trigger.

**How to avoid:** Keep a single same-record derivation on one side of the step 3 / step 4
boundary. If both surfaces must exist, record in the decision record which one owns which
field, and never let both write the same field.

*Source: Apex Developer Guide, "Triggers and Order of Execution", apexdev.txt L15440, L15441,
L15448, L15470.*

---

## 2. A Working Legacy Automation Is Still Architecture Debt

**What happens:** Workflow Rule and Process Builder logic keeps executing, so it never
announces itself. The decision discussion then silently anchors on the old implementation
rather than on the requirement.

**When it occurs:** Any object whose automation predates the migration push and has not been
inventoried since.

**How to avoid:** Inventory the legacy behavior explicitly with the queries and the `Workflow`
retrieve in `references/decision-record-examples.md`, then rebuild it on a current automation
boundary instead of planning around it.

---

## 3. Before-Save Flow Is Underused, And Its Element Set Is The Reason People Skip It

**What happens:** Teams jump to Apex or after-save Flow because those surfaces feel more
flexible — and the before-save element set genuinely is narrower, with no Create/Update/Delete
Records element to reach for.

**When it occurs:** Field defaulting, normalisation and light same-record calculation, which
is exactly the work before-save was built for.

**How to avoid:** Ask whether the requirement writes anything other than fields on the
triggering record. If the answer is no, `automation-selection.md` Q2 resolves to before-save
and the discussion is over.

---

## 4. Mixed Automation Layers Hide Ownership Problems

**What happens:** One business rule split across Flow, trigger logic and a validation rule can
be individually valid at every layer and collectively unsupportable. The defect is the support
burden, not any single component.

**When it occurs:** Objects that have accumulated automation across several projects with no
per-object owner.

**How to avoid:** Keep one clear owner for each automation concern, and document the exception
in the decision record when both Flow and Apex are deliberately involved.

---

## 5. A Workflow Field Update Re-Runs Update Triggers — And Only Update Triggers

**What happens:** At step 11 the save procedure executes workflow rules. If there are workflow
field updates, Salesforce updates the record again, runs system validations again, and then
executes before update triggers and after update triggers "regardless of the record operation
(insert or update), one more time (and only one more time)". Custom validation rules, flows,
duplicate rules, Process Builder processes and escalation rules are *not* run again in that
second pass. So a trigger sees the record twice while the flow beside it sees it once.

**When it occurs:** Any object still carrying an active Workflow Rule with a field update
alongside an Apex trigger — the common shape in a half-migrated org.

**How to avoid:** Treat a surviving workflow field update as a reason to finish the migration
before adding anything new to the object. Moving the field update into the before-save flow
removes the second trigger pass entirely.

*Source: Apex Developer Guide, "Triggers and Order of Execution", step 11, apexdev.txt
L15451–L15460.*

---

## 6. A Recursive Save Silently Skips A Block Of The Sequence

**What happens:** During a recursive save, Salesforce skips steps 9 (assignment rules) through
17 (roll-up summary field in the grandparent record). That range swallows assignment rules,
auto-response rules, workflow rules, escalation rules, Process Builder, **after-save
record-triggered flows at step 14**, entitlement rules and the parent/grandparent roll-up
recalculations.

**When it occurs:** Whenever one automation's DML sends a record back through the save
procedure — an after-save flow updating a related record that itself has automation, or a
trigger that reparents.

**How to avoid:** Never design a rule that depends on an after-save flow or an assignment rule
firing on a record that another automation touched in the same transaction. If the requirement
needs it, that is a Q3 signal to move the whole chain into Apex where the ordering is explicit.

*Source: Apex Developer Guide, "Triggers and Order of Execution", note above step 1,
apexdev.txt L15414–L15415.*

---

## 7. After-Trigger Records Are Read-Only, And Before-Trigger Self-Updates Throw

**What happens:** "The records that fire the after trigger are read-only." Separately, "if you
update or delete a record in its before trigger, or delete a record in its after trigger, you
will receive a runtime error" — including both direct and indirect operations.

**When it occurs:** A design that picks "after save" for a rule that turns out to need a change
to the triggering record, then tries to bolt the same-record write back on.

**How to avoid:** Settle the same-record question before the timing question. If the rule
writes the triggering record, timing is `before_save` and nothing later reopens it.

*Source: Apex Developer Guide, "Triggers", apexdev.txt L14866–L14875.*

---

## 8. The Transaction Has One Governor Budget, Not One Per Automation

**What happens:** Flow and Apex on the same save draw from the same per-transaction
allowances. Synchronously that is 100 SOQL queries, 50,000 records retrieved by SOQL, 150 DML
statements, 10,000 records processed by DML, 6 MB heap and 10,000 ms of CPU; asynchronously
200 SOQL, 12 MB heap and 60,000 ms of CPU. Total stack depth for any Apex invocation that
recursively fires triggers through insert, update or delete statements is 16. A flow that is
comfortably within its own budget can still be the automation that tips the transaction over.

**When it occurs:** Bulk loads and API batches, where 200 records per transaction multiply
everything the object's automation does.

**How to avoid:** Record `volume.per_transaction` as a measured number and cost the *whole*
save against these limits, not the new automation in isolation.

*Source: Salesforce Developer Limits and Allocations Quick Reference, Apex Governor Limits
table, salesforce_app_limits_cheatsheet.txt L53, L55, L64, L66, L69, L89, L91.*

---

## 9. Editing Retrieved Process Builder Metadata Bricks The Process In The Target Org

**What happens:** The Metadata API guide warns: "Don't edit the metadata of retrieved Process
Builder processes, such as flow components whose `processType` is `Workflow` or
`InvocableProcess`. If you deploy process metadata that you edited, you can't open the process
in the target org."

**When it occurs:** During the legacy inventory, when someone opens the retrieved
`.flow-meta.xml` to "just tidy the label" or to deactivate the process by hand before the
migration is planned.

**How to avoid:** Keep the inventory read-only. `check_process_automation_selection.py
--manifest-dir` flags flows whose `processType` is `Workflow` precisely so they can be listed
without being touched; rebuild in Flow Builder rather than editing the retrieved XML.

*Source: Metadata API Developer Guide, Flow, api_meta.txt L68044–L68046.*

---

## 10. A Failed Migration Attempt Is Recorded In The Workflow Metadata

**What happens:** `WorkflowRule` carries a `failedMigrationToolVersion` field: "The API version
in which a migration fails. Used as a reference to admins to retry the migration when the next
version is released." (Available in API version 54.0 and later.) A rule that looks untouched
may in fact have already defeated the Migrate to Flow tool once.

**When it occurs:** Inventorying an org where someone previously attempted a bulk migration and
abandoned the rules that failed.

**How to avoid:** Retrieve the `Workflow` metadata and read `failedMigrationToolVersion` before
estimating migration effort. A populated value means the rule needs a manual rebuild, not
another tool run, and belongs in the decision record's rejected alternatives with that reason.

*Source: Metadata API Developer Guide, `WorkflowRule`, api_meta.txt L140402–L140406.*

---

## 11. Scheduled-Flow Batch Semantics Are Per-Record, Not Per-Job

**What happens:** A schedule-triggered flow does not process a result set the way Batch Apex
does. `FlowStart.object` is "the object whose records you want to retrieve from the database. A
flow interview starts for each record that meets the filter conditions." One interview per
record, not one interview per run. On the scheduled-path side, `FlowScheduledPath.maxBatchSize`
is "the maximum number of scheduled path interviews to execute in a single batch, from 1 to
200. Default is 200." And `FlowSchedule.frequency` for a non-segment scheduled flow is limited
to `Once`, `Daily` and `Weekly` — `Hourly`, `Monthly`, `Weekdays` and `Yearly` are documented as
segment-triggered flows only.

**When it occurs:** Any "just schedule a flow for it" answer to a nightly reconciliation whose
population turns out to be six figures, or any requirement whose cadence is hourly.

**How to avoid:** Size the population before choosing, per `automation-selection.md` Q10 and
`flow-pattern-selector.md` Q6, and check the requested cadence against the `frequency` enum
before promising it.

UNVERIFIED (2026-09-04): the org-wide ceiling of 250,000 schedule-triggered flow interviews per
24 hours (or user licenses × 200, whichever is greater) is not present in the extracted
Metadata API, Apex Developer, Object Reference or App Limits Cheat Sheet text. The decision
trees source it to Salesforce Help `platform.flow_considerations_trigger_schedule`, which
cannot be fetched here — cite the tree rather than the number.

*Source: Metadata API Developer Guide, `FlowStart.object` (api_meta.txt L72425–L72427),
`FlowScheduledPath.maxBatchSize` (api_meta.txt L71397–L71398), `FlowSchedule.frequency`
(api_meta.txt L71352–L71366).*

---

## 12. Tool Choice Changes At Scale, So The Decision Needs An Expiry Date

**What happens:** A prototype-friendly Flow stops being the right answer when imports,
integrations or heavy reuse arrive. Nothing in the platform notices; the automation simply
starts appearing in limit errors that name it only incidentally.

**When it occurs:** After a data migration, a new integration, or a merger that multiplies row
counts on an object whose automation was sized for the old volume.

**How to avoid:** Put a measured volume and a `review_date` on the decision record, and re-run
`automation-selection.md` Q3 and Q10 against the current numbers on that date rather than
waiting for the first CPU-time failure.
