# Eval: flow/flow-bulkification

- **Skill under test:** `skills/flow/flow-bulkification/SKILL.md`
- **Priority:** P0
- **Cases:** 3
- **Last verified:** 2026-04-16
- **Related templates:** `templates/flow/RecordTriggered_Skeleton.flow-meta.xml`, `templates/flow/FaultPath_Template.md`
- **Related decision trees:** `standards/decision-trees/automation-selection.md`

## Pass criteria

Any Flow produced or reviewed must: avoid Get/Update/Create Records inside
loops, use collection-based DML, keep a single record-triggered flow per
object with entry criteria decisions, and have a fault path for every
external-effect element.

## Case 1 — "Flow is hitting SOQL limit" triage

**Priority:** P0

**User prompt:**

> "My record-triggered Flow on `Order__c` is failing with
> `SOQL queries: 101`. It fires on every update, loops the Order line items,
> and does a `Get Records` for each one. How do I fix it?"

**Expected output MUST include:**

- Root cause: `Get Records` inside a loop.
- Fix: pull all Line Items in one `Get Records` BEFORE the loop, using a
  filter like `Order_Number__c IN {!orderNumbers}`.
- Assemble a `Map` keyed by OrderId via a loop that just populates the
  collection (no SOQL).
- Collection-based Update/Create after the loop — one DML, not N.
- Run once per 200 Orders to prove bulk safety.
- Add a fault connector on the Update to route to a Platform Event error
  or a log record.
- If multiple record-triggered Flows exist on Order, consolidate into one
  with entry-criteria decisions.

**Expected output MUST NOT include:**

- "Reduce the number of Orders in the transaction" (wrong direction).
- "Convert everything to Apex" (overshoot — fix the Flow first).
- Leaving `Get Records` inside the loop but "making the query more selective".

**Rubric (0–5):**

- **Correctness:** Root cause identified.
- **Completeness:** Pre-loop query + Map + collection DML + fault path.
- **Bulk safety:** Explicitly notes 200-record test.
- **Security:** Entry criteria still respects sharing (Flow runs as running user by default).
- **Citation of official docs:** Links to Flow best practices + Bulkification.

**Reference answer (gold):**

"Classic Flow bulkification issue. `Get Records` inside a loop = 1 SOQL per iteration = 101 query limit at 101 Orders.

Fix:

1. **Before the loop**: `Get Records` on `Order_Line_Item__c` with filter
   `Order__c IN {!triggerRecordIds}` (where you built `triggerRecordIds`
   from `{!$Record.Id}` across the trigger collection). Store in a
   `LineItems` collection variable.
2. **Assignment element**: loop the `LineItems` collection once to build a
   `Map<Order Id, List<LineItem>>` — call it `LineItemsByOrderId`.
3. **Main loop**: for each Order, read `LineItemsByOrderId` from memory.
   No SOQL.
4. **After the loop**: collection-based Update Records on a single
   `OrdersToUpdate` collection — one DML, regardless of input size.
5. **Fault connector** on the Update: route to a `Log_Flow_Error` subflow
   that creates an `Application_Log__c` record (see
   `templates/flow/FaultPath_Template.md`).

Test: a developer-side Apex test that inserts 200 Orders and asserts
`Limits.getQueries() < 20` after the transaction. If one Flow doesn't hold
the line, consolidate every Flow on `Order__c` into one record-triggered
Flow with entry-criteria Decisions, so the pre-loop SOQL is done once.

Reference `automation-selection.md` Q3 — this is still a Flow decision,
not an Apex one. You're not hitting Flow's expressiveness limits, just its
shape."

## Case 2 — "One Flow per field" cleanup

**Priority:** P0

**User prompt:**

> "Our Account object has 18 record-triggered Flows, one per automation
> requirement. Deploys are slow and behaviour is unpredictable. How do I
> consolidate?"

**Expected output MUST include:**

- Canonical guidance: one record-triggered Flow per object per trigger
  type (before-save vs after-save).
- Consolidation pattern: one master Flow with entry-criteria Decisions
  that branches to sub-flow invocations per concern.
- Ordering: establish deterministic ordering by either using the
  `triggerOrder` in the Flow metadata (Spring '23+) or by consolidating
  into a single Flow so order is visible.
- Migration plan — don't big-bang. Move one sub-Flow at a time; each PR is
  one less flow in the "N flows" count.
- Keep regression tests via a skeleton Apex test class that inserts
  bulk records.

**Expected output MUST NOT include:**

- "Turn them off one by one" without replacement.
- Using Apex to consolidate (overreach).
- Ignoring the `triggerOrder` attribute.

**Rubric (0–5):**

- **Correctness:** One-Flow-per-object-per-trigger-type.
- **Completeness:** Sub-Flow architecture + triggerOrder + migration plan.
- **Bulk safety:** Consolidated Flow handles 200 records.
- **Security:** Preserves existing sharing model.
- **Citation of official docs:** Links to "Trigger Explorer" + Flow triggerOrder release note.

**Reference answer (gold):**

"Canonical shape: **one before-save Flow + one after-save Flow per object**. The before-save does defaulting; the after-save does cross-record work.

Architecture:

```
Account_BeforeSave_Master
    ├── Decision: Is Priority Customer?
    │       └── Set Priority fields (Assignment)
    ├── Decision: Is Renewal Soon?
    │       └── Set Renewal_Reminder_Date (Assignment)
    └── ...

Account_AfterSave_Master
    ├── Decision: Industry Changed?
    │       └── Subflow: SyncAccountToMarketing
    ├── Decision: Owner Changed?
    │       └── Subflow: ReassignChildRecords
    └── ...
```

Migration (one PR per concern):

1. Pick one of the 18 Flows. Move its logic into the master's Decision +
   Assignment / Subflow invocation.
2. Test by inserting/updating 200 Accounts in a scratch org.
3. Deactivate the old Flow. Don't delete yet — keep for rollback.
4. Rinse, repeat until all 18 are consolidated.
5. Purge deactivated Flows after a release cycle.

During the transition, use `triggerOrder` on the remaining standalone Flows so the execution order is deterministic. Consolidation beats triggerOrder — but it's a useful bridge."

## Case 3 — Fault paths that actually help

**Priority:** P0

**User prompt:**

> "Our Flows have fault connectors but we never look at them — errors just
> disappear. How should fault paths actually be wired?"

**Expected output MUST include:**

- Every element with side-effects (Create / Update / Delete / Action /
  Subflow / Callout) needs a fault connector.
- Default fault destination: a subflow `Flow_Error_Handler` that creates
  an `Application_Log__c` with flow name, element name,
  `{!$Flow.FaultMessage}`, user Id, record Id.
- Post-log: decide policy — user-visible screen flows get a user-friendly
  error screen, autolaunched flows can suppress or re-raise.
- For record-triggered flows, the fault path cannot "halt" the DML the way
  Apex can; use Validation Rules + Custom Errors for user-facing blocks.
- Monitor `Application_Log__c` via a report + Slack webhook for errors
  above WARN in last hour.

**Expected output MUST NOT include:**

- "Write errors to a debug log" — debug logs rotate and aren't queryable.
- Fault path that shows a toast in an autolaunched (headless) flow.
- Swallowing the error with no log.

**Rubric (0–5):**

- **Correctness:** Every side-effect element has a fault connector.
- **Completeness:** Centralised subflow + monitoring.
- **Bulk safety:** Log record creation is single-record and safe.
- **Security:** `Application_Log__c` has Private OWD.
- **Citation of official docs:** Links to Flow fault paths + `$Flow.FaultMessage`.

**Reference answer (gold):**

"Wire every side-effect to a centralised error handler.

Pattern:

1. Create `Flow_Error_Handler` autolaunched subflow. Inputs: `Source` (text),
   `ElementName` (text), `FaultMessage` (text), `RecordId` (text), `UserId` (text).
   Body: Create `Application_Log__c` with Severity = `ERROR`, Source =
   `Flow.<Source>.<ElementName>`, Message = `FaultMessage`.
2. In your record-triggered Flow, every Create/Update/Delete/Action/Subflow
   has a fault connector to `Flow_Error_Handler`.
3. For screen flows, after the error handler subflow, route to a user-friendly
   error screen.
4. For autolaunched/record-triggered, after the error handler, END — the
   user sees the platform's generic failure, the log captures detail.
5. Build a list view on `Application_Log__c` (Severity = ERROR, Source LIKE
   `Flow.%`, CreatedDate = TODAY). Wire a Slack webhook for anything above
   WARN in the last hour.

User-facing validation: for 'Status must be Open for this action', use a
Validation Rule or Flow's 'Custom Error' action — NOT a fault connector.
Fault paths are for the runtime errors you couldn't predict, not for the
business rules you can.

Reference: `templates/flow/FaultPath_Template.md` for the canonical pattern."
