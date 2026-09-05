---
name: record-triggered-flow-patterns
description: "Use when designing or reviewing Salesforce record-triggered Flows, especially before-save vs after-save behavior, entry criteria, recursion avoidance, and when to escalate to Apex. Triggers: 'before save vs after save', '$Record__Prior', 'record-triggered flow', 'order of execution', 'flow recursion', 'triggerOrder', 'doesRequireRecordChangedToMeetCriteria', 'scheduled path', 'RecordBeforeDelete', 'flow-meta.xml', 'FlowTest'. NOT for tracing save order against triggers — use flow/flow-record-save-order-interaction. NOT for bulk-load failures once the trigger model is right — use flow/flow-bulkification."
category: flow
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Reliability
  - Scalability
  - Operational Excellence
tags:
  - record-triggered-flow
  - before-save
  - after-save
  - order-of-execution
  - recursion
triggers:
  - "before save vs after save flow choice"
  - "record triggered flow running too often"
  - "after save flow updating the same record"
  - "how do I use $Record__Prior in flow"
  - "when should this be apex instead of flow"
  - "flow runs too many times on update"
  - "write a record-triggered flow-meta.xml I can deploy"
  - "set triggerOrder for two flows on the same object"
  - "add a scheduled path to a record-triggered flow"
  - "archive a record before it is deleted with flow"
  - "flow created two tasks for the same opportunity"
  - "test a record-triggered flow before activating it"
  - "convert an after-save update to before-save"
  - "before save flow update same record without an update element"
  - "record triggered flow entry conditions only when a field changes"
inputs:
  - "business event that should trigger automation"
  - "whether only the current record or related records must change"
  - "existing Apex, validation rules, and other automation on the same object"
outputs:
  - "record-triggered flow design recommendation"
  - "review findings for trigger context and recursion risk"
  - "decision on before-save, after-save, or Apex"
dependencies: []
version: 2.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

Use this skill when the hard part is not "how do I automate" but "what is the right record-triggered pattern for this object and this event?" The purpose is to choose the correct trigger context (before-save vs after-save), control how often the flow runs (entry criteria + prior-value checks), align with Salesforce order-of-execution semantics (so the flow plays well with Validation Rules, Apex triggers, and duplicate rules), and know when the answer is to escalate to Apex rather than force more logic into Flow.

Getting this choice wrong is expensive. The wrong trigger context causes recursion that produces runaway automation under bulk load. The wrong entry criteria causes the flow to run on every save, burning transaction budget on changes it doesn't care about. The wrong order-of-execution assumption causes Validation-Rule-after-field-update surprises that surface in production as "the rule worked yesterday."

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.

Gather if not available:
- Is the requirement only to change fields on the triggering record, or must it touch related data, send notifications, or call external systems?
- What other automation already runs on the object: validation rules, Apex triggers, duplicate rules, other record-triggered flows, managed-package automation?
- Does the flow need to act on create only, update only, specific field changes, or every save?
- What is the expected bulk cardinality (see `flow/flow-bulkification` for the scale math)?
- Is there an active trigger framework in the org? (If yes, coexistence requires explicit coordination.)

## Questions to Ask Before Configuring

Ask these before opening Flow Builder. Each one decides an element in the XML, and each one traces to a gotcha that only shows up in production. An agent that skips them ships a flow that passes deploy and fires twice.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Does this change fields on the record being saved, or does it touch anything else?" | Same-record-only is the only case that fits `RecordBeforeSave`; everything else forces `RecordAfterSave` | The `triggerType`, and whether the flow can have DML elements at all (`references/gotchas.md` § before-save assignments) |
| "Is this a state or a transition — 'while Status is Approved' or 'when Status becomes Approved'?" | Decides `doesRequireRecordChangedToMeetCriteria`; the wrong answer creates a duplicate record on every later edit | The `<start>` block: `filters` + `doesRequire…` for a transition, `filterFormula` for a state test (`references/gotchas.md` § transition vs state) |
| "What else already runs on this object, in which save context, at which `triggerOrder`?" | Two flows in one save context with no declared order is undefined sequencing, and a before-trigger writing the same field always wins over a before-save flow | The `triggerOrder` value and the list of fields this flow may not own (`references/gotchas.md` § triggerOrder ties) |
| "Does anything downstream update this record again?" | An after-save flow that re-saves its own object re-enters the save procedure, and steps 9–17 are skipped on that pass — so the behaviour differs from the first save | The recursion guard: marker field, changed-field criteria, or a move to before-save (`references/gotchas.md` § recursive save) |
| "If the related-record write fails at 2am, who finds out and how?" | Without a `faultConnector` the interview stops and the error is invisible outside the flow error email | A fault path on every Create/Update/Delete/Get, landing on `Application_Log__c` per `templates/flow/FaultPath_Template.md` |
| "Does any of this work need to happen later — hours or days after the save?" | A scheduled path is a `FlowScheduledPath`, batches up to 200 interviews, and an `AsyncAfterCommit` path runs post-commit where it cannot roll the save back | The `scheduledPaths` block with `offsetUnit`, `recordField`, and a deliberate `maxBatchSize` (`references/gotchas.md` § scheduled path batching) |
| "When a record of this type is deleted, does anything have to be preserved or cleaned up?" | `RecordBeforeDelete` is the only delete context that exists — there is no after-delete record-triggered flow, and cascade deletes may never reach it | A third flow (or an explicit decision not to have one) instead of discovering the gap after a mass delete (`references/gotchas.md` § no after-delete) |

What a proper configuration adds over just building the flow: the trigger context matches the requirement instead of defaulting to after-save, entry criteria encode the business *transition* rather than a state that stays true, every failure path writes a row someone can query, and the object's save context has a declared run order instead of an accidental one.

---

## Core Concepts

### Before-Save Is For Fast Same-Record Changes

Before-save record-triggered flows are optimized for updating fields on the record currently being saved. They execute IN THE SAME DML statement as the save — no extra DML, no recursion risk for same-record writes. They should be the default choice when the requirement is enrichment, normalization, or lightweight decisioning on that same record.

**What before-save can do:**
- Assign a value to `$Record.<field>` based on other fields on the same record.
- Assign a value to `$Record.<field>` based on a parent record's fields (if the parent is accessible via relationship — lazy-loaded).
- Call invocable Apex that returns a value for assignment (but NOT one that performs DML).
- Use `$Record__Prior` to compare against the old value (on update triggers).

**What before-save CANNOT do:**
- Create, update, or delete related records.
- Send emails, post to Chatter, publish Platform Events.
- Call invocable Apex that performs DML.
- Have scheduled paths (before-save is transactional, not time-delayed).
- Be called from Platform-Event-Triggered contexts.

UNVERIFIED (2026-09-05): the Metadata API guide describes `RecordBeforeSave` as running "to make more updates to that record before it's saved to the database" (`api_meta.txt` L72539–72542) and defines `scheduledPaths` on `FlowStart` without restricting it by `triggerType` (L72465–72466). The prohibitions in that list are Flow Builder's, documented on help.salesforce.com, which cannot be fetched. Treat them as design rules — the checker enforces the DML ones — but confirm in a sandbox before telling a customer the platform blocks a specific one.

### After-Save Is For Committed Side Effects

After-save flows exist for related-record writes, notifications, subflows, actions, and work that depends on the record being committed. They are more flexible, but they are also more expensive (each related write is a new DML statement) and easier to design badly (recursion risk, fan-out risk).

**When after-save is the ONLY option:**
- Creating related records (e.g. auto-creating a Task when an Opportunity closes).
- Updating related records (e.g. rolling up data to a parent).
- Sending email / custom notifications / Chatter posts.
- Invoking external actions (HTTP callouts via External Services).
- Publishing Platform Events.
- Triggering downstream subflows or invocable Apex that perform DML.

### Entry Criteria Is A Design Tool, Not Just A Filter

A record-triggered flow that runs on every update without clear entry criteria becomes hidden operational debt. Three layers of filtering matter:

1. **Entry criteria on the Flow itself** — "Record was updated AND Status = 'Approved'". This is the cheapest filter; records that don't match never start the interview.
2. **"Optimized start settings"** — Salesforce evaluates the criteria BEFORE the full Flow loads; faster than running the Flow and exiting early via Decision.
3. **Field-change conditions** — "Record was updated AND Status changed from anything other than 'Approved' to 'Approved'". Prevents the Flow from re-running when the record is edited for unrelated reasons.

**Rule:** Never design a record-triggered flow without entry criteria. "Runs on every save" is a smell even when it happens to match the requirement today — the requirement will narrow, and undoing loose entry criteria at scale is hard.

### Order Of Execution Still Applies

Record-triggered flows participate in Salesforce's documented order of execution. Key points:

- **Before-save record-triggered flows run at step 3 — first in the save.** Fields you set in before-save get validated at step 5. An enrichment flow that sets an invalid value will be blocked by a Validation Rule — sometimes with a confusing error message.
- **Before-save flows run BEFORE Apex before-triggers (step 3 vs step 4).** These are separate, consecutively numbered steps, so the ordering is documented and fixed — not a race. If a flow and a before-trigger write the same field, the **trigger's value is what saves**, every time. Fix that by giving the field one owner, or by conditioning the trigger; a condition on the flow changes nothing, because the flow has already finished.
- **After-save record-triggered flows run at step 14, AFTER Apex after-triggers at step 8.** Apex after-triggers see the record as-saved; after-save flows see the record after Apex has had a chance to modify it. A record created by an after-trigger is visible to the after-save flow; the reverse is not true.
- **After-save flows run AFTER Workflow Rules (step 11, for orgs still running them)** and AFTER Process Builder (step 13, deprecated but still active in some orgs). Layered automation on the same object creates order-of-execution chains that are hard to trace.
- **Multiple record-triggered flows of the same type on one object are ordered by `triggerOrder`.** Set it (Metadata API 54.0+, valid range 1 to 2,000 — `api_meta.txt` L68438–68441; surfaced as Flow Trigger Explorer) rather than leaving the sequence to chance. The canonical guidance is still one record-triggered flow per object per save context.
- **A recursive save is not the same transaction shape as the first one.** "During a recursive save, Salesforce skips steps 9 (assignment rules) through 17 (roll-up summary field in the grandparent record)" (`apexdev.txt` L15414–15415). Step 14 is inside that window, so a nested save re-runs before-save flows and both trigger phases but not after-save flows — which is why "it worked when I tested it by hand" and "it looped in the data load" can both be true.
- **The flow's own `<apiVersion>` moves it in the list.** "In API version 53.0 and earlier, after-save record-triggered flows run after entitlements are executed" (`apexdev.txt` L15509). An old flow retrieved from a legacy org and redeployed unchanged sits in a different place in the save order than a new one.

When designing a new flow, ALWAYS check existing automation on the object first (`list_flows_on_object`, `tooling_query` on `ApexTrigger`, `list_validation_rules`). Not knowing what's already there is a scale-invariant mistake.

### $Record__Prior Makes Recursion Control Possible

On update triggers, `$Record__Prior` holds the record's field values BEFORE the current save. Using it in entry criteria ("ISCHANGED(Status)" or equivalent) is the canonical way to keep the flow from re-firing on unrelated edits — including edits it makes to itself.

```text
Flow entry criteria:
  {!$Record.Status} = 'Approved'
  AND {!$Record__Prior.Status} != 'Approved'
```

This condition fires exactly once per actual status-change-to-approved, regardless of how many times the record gets edited afterward.

## Common Patterns

### Pattern 1: Before-Save Enrichment Pattern

**When to use:** Only the triggering record needs calculated defaults, normalized values, or field derivation.

**Structure:**
```text
Before-save record-triggered Flow:
    Entry criteria: (condition to filter records that need enrichment)
    └── [Decision: does field X need normalization?]
         └── Yes → [Assignment: $Record.Field_X = normalized value]
    → [Decision: does field Y need defaulting?]
         └── Yes → [Assignment: $Record.Field_Y = default value]
    (No DML — the assignments persist as part of the save)
```

**Why not the alternative:** An after-save flow would spend extra DML, trigger re-save recursion, and run on every edit instead of the relevant ones.

### Pattern 2: After-Save Related-Record Pattern

**When to use:** Saving the parent record should create, update, or notify something else.

**Structure:**
```text
After-save record-triggered Flow:
    Entry criteria: (narrow condition, e.g. "Amount > 50k AND Stage = 'Closed Won'")
    └── [Get Records: related Account]
    └── [Decision: is Account elite-tier?]
         └── Yes → [Create Records: Retention_Task__c]
                  → [Create Records: Executive_Followup_Task__c]
                  → [Send Custom Notification]
    (Explicit field-change check in entry criteria prevents re-firing on unrelated edits)
```

**Critical:** the entry criteria MUST include a field-change check if the Flow updates the SAME record (even indirectly via related Apex). Without it, the after-save flow retriggers itself.

### Pattern 3: Escalate To Apex For Complex Transaction Logic

**When to use:** The automation needs deep branching, complex collections, callouts per record, precise recursion control, or interaction with an existing Apex trigger framework.

**Signals that Flow is no longer the right boundary:**
- Flow has more than 40 elements (visual complexity).
- Flow has > 3 nested Decisions.
- Flow requires invocable Apex that itself has non-trivial logic (you're writing Apex anyway — just put it in a trigger handler).
- Flow shares an object with existing Apex triggers AND the Apex handler already covers the same event.

**Approach:** Migrate the logic to an Apex trigger handler (see `apex/trigger-framework`). Keep the Flow ONLY if it's the orchestration entry point; move the "work" to Apex. When in doubt, run `automation-migration-router --source-type process_builder` (equivalent principles apply).

### Pattern 4: Fast-Field-Update Plus Async Fan-Out

**When to use:** Same-record enrichment is cheap (before-save) but related-record work is heavy and doesn't need to be in the save transaction.

**Structure:**
```text
Before-save Flow: sets fields on $Record, publishes Platform Event with record id + change context
Platform-Event-Triggered Flow: processes the event async, does the heavy related-record work
```

Decouples the user-facing save (fast) from the downstream side effects (async, retry-able). Great for fan-out scenarios that would exceed DML limits inline.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Update fields on the saving record only | Before-save Flow (Pattern 1) | Fastest, simplest, no DML, no recursion |
| Normalize fields on save | Before-save Flow | Same reasons |
| Create or update related records after commit | After-save Flow (Pattern 2) | Related side effects require after-save |
| Need field-change detection | Use entry criteria + `$Record__Prior` comparison | Prevents irrelevant re-runs and recursion |
| Heavy orchestration or deep transaction control required | Apex trigger handler (Pattern 3) | Record-triggered Flow is not always the best boundary |
| Fan-out exceeds 10 related records per save | Async via Platform Events (Pattern 4) | Keep save transaction fast; defer the heavy work |
| Object already has Apex triggers | Consolidate: Flow OR Apex, not both on same event | Coexistence is possible but an audit liability; prefer one owner |
| Need callout per record | After-save Flow with HTTP Action OR Apex + `@future(callout=true)` | Inline HTTP from Flow is fine for low volume; use async for bulk |
| Process Builder being migrated | `automation-migration-router --source-type process_builder` | Don't reinvent the migration logic |

## Recursion Avoidance Recipe

When an after-save Flow updates records on the same sObject:

1. **Entry criteria** must include a field-change check: `ISCHANGED(Status)` or `$Record.Status != $Record__Prior.Status`.
2. **Update ONLY fields the flow's own condition doesn't depend on.** If the entry criteria is "Status changed" and the flow sets `Status`, it re-fires forever.
3. **Use a marker field** if the flow must update a field that retriggers it. Marker: `Last_Processed_At__c` — set it, then bail out on next fire if it's fresh.
4. **Consider before-save** if the update is same-record. Before-save doesn't recurse because the value is written as part of the original save.

## Review Checklist

- [ ] Before-save is used for same-record updates whenever possible.
- [ ] After-save paths justify every related-record write or action.
- [ ] Entry criteria includes field-change logic (via `$Record__Prior` or "optimized start" settings).
- [ ] The flow does not update the same record after-save without an explicit recursion guard (marker field, `ISCHANGED` condition).
- [ ] Order-of-execution interactions with Apex, Validation Rules, and managed-package automation were reviewed.
- [ ] Only ONE record-triggered flow per object per save context (before-save/after-save/after-save-delete) — or, if multiple, the ordering is documented and intentional.
- [ ] The team explicitly considered whether the use case should move to Apex (Pattern 3).
- [ ] Bulk safety math done per `flow/flow-bulkification`.
- [ ] Fault handling in place per `flow/fault-handling`.


## Recommended Workflow

1. **Inventory the object's save contexts.** Query `FlowDefinitionView` for every active record-triggered flow on the object (`references/metadata-examples.md` § 8 has the SOQL), plus `ApexTrigger` and validation rules. You need the existing `TriggerOrder` values before you can pick yours.
2. **Answer the seven questions above.** The first two fix `triggerType` and `recordTriggerType`; the third fixes `triggerOrder`; the rest decide whether you need a scheduled path, a fault path, and a delete flow.
3. **Fill in the skeleton, don't freehand the XML.** Start from `templates/flow/RecordTriggered_Skeleton.flow-meta.xml` and use the matching worked flow in `references/metadata-examples.md` — § 1 before-save, § 2 after-save with entry conditions plus a scheduled path, § 3 before-delete. Route every Create/Update/Delete/Get `faultConnector` per `templates/flow/FaultPath_Template.md`.
4. **Write the `FlowTest` before you activate.** `references/metadata-examples.md` § 4 shows the `InputTriggeringRecordInitial` / `InputTriggeringRecordUpdated` pair — the only mechanism that proves your entry criteria fire on the transition rather than on the state.
5. **Run the checker on the source tree**, then a check-only deploy: `python3 skills/flow/record-triggered-flow-patterns/scripts/check_record_triggered_flow_patterns.py --manifest-dir force-app/main/default`, then `sf project deploy validate --manifest manifest/package.xml`. The checker catches missing `faultConnector`s, before-save flows carrying DML, after-save flows re-saving their own object without changed-field criteria, Gets inside loops, and unset `triggerOrder` when the manifest has more than one flow on an object.
6. **Activate deliberately and verify twice.** Flip `<status>` to `Active`, redeploy, then confirm in Flow Trigger Explorer and in the `FlowDefinitionView` query that the run order and the active version are what you shipped — not what a stale `FlowDefinition` pinned (`references/metadata-examples.md` § 5).
7. **Prove the transition once with real data.** Drive the record through the change, then read the Task/related-record channel and `Application_Log__c`. Two side-effect records for one transition is the `doesRequireRecordChangedToMeetCriteria` bug, not a coincidence.

---

## Salesforce-Specific Gotchas

1. **After-save updates to the triggering record can retrigger automation** — this is one of the most common Flow recursion smells. Before-save avoids it entirely for same-record writes.
2. **Before-save cannot replace all trigger behaviors** — if the logic needs related-record work, notifications, or callouts, the design must move to after-save or another boundary.
3. **A broad start condition becomes hidden operational cost** — flows that fire on every edit are harder to debug, more likely to clash with other automation, and more expensive to refactor later.
4. **Multiple automations on one object still interact** — record-triggered flows are not isolated from Apex triggers, duplicate rules, or validation behavior. When adding a new flow to an object, `list_flows_on_object` + `tooling_query` for existing triggers is non-negotiable.
5. **`$Record__Prior` has no meaningful value on a create** — the platform's own transition switch, `doesRequireRecordChangedToMeetCriteria`, is defined against "the triggering **update**" (`api_meta.txt` L72322–72325), which is why the after-save example in `references/metadata-examples.md` sets `recordTriggerType` to `Update` rather than `CreateAndUpdate`. Guard prior-value comparisons with a create check. UNVERIFIED (2026-09-05): whether a prior-value comparison on a create *throws* or silently evaluates against null is not stated in `api_meta.txt` or `apexdev.txt`; do not promise either behaviour.
6. **Before-save runs before Validation Rules** — a before-save assignment to an invalid value will be caught by a VR, sometimes with a confusing error pointing at the field the user didn't touch.
7. **After-save runs after Apex triggers** — if an Apex before/after trigger changes the record, the after-save flow sees the post-Apex state. Don't assume the flow sees the user's input.
8. **Process Builder on the same object runs in a different order than Flow** — orgs mid-migration between PB and record-triggered Flows have unpredictable event sequences; complete the migration before adding more automation.
9. **Managed-package record-triggered flows are opaque** — you can see that a Flow exists via `list_flows_on_object` but the contents may be locked. Coordinate with the package vendor before adding more automation on the same save context.
10. **Salesforce's "Flow Trigger Explorer" shows ordering** — admins should use it during design, not just during incident response. Ordering disputes are easier to resolve before deploy.

## Proactive Triggers

Surface these WITHOUT being asked:

- **After-save flow doing only same-record field updates** → Flag as Critical. Convert to before-save (Pattern 1) — free performance win + removes recursion risk.
- **Record-triggered flow with no entry criteria** → Flag as High. Operational debt; add an ISCHANGED condition or field-value filter.
- **Multiple record-triggered flows on the same object in the same save context** → Flag as High. Ordering is unspecified; consolidate or document explicit ordering.
- **After-save flow that updates the triggering record without a recursion guard** → Flag as Critical. Infinite-loop risk at scale.
- **Complex branching (> 3 nested Decisions) or > 40 elements** → Flag as Medium. Candidate for migration to Apex (Pattern 3).
- **Object has both active Apex triggers and active record-triggered flows** → Flag as Medium. Coexistence works but must be documented; run `audit-router --domain validation_rule` + `flow-analyzer` to map.
- **Process Builder still active on the same object as a new record-triggered Flow** → Flag as High. Ordering confusion; complete the PB migration first.
- **No `salesforce-context.md` + no explicit order-of-execution check done** → Flag as Medium. Request the review before approving the design.

## Output Artifacts

| Artifact | Description |
|---|---|
| Trigger-context recommendation | Clear before-save, after-save, or Apex choice with reasons |
| Record-triggered flow review | Findings on entry criteria, recursion risk, order-of-execution fit, coexistence |
| Refactor plan | Specific changes to move a flow into the right trigger pattern |
| Consolidation proposal | When multiple flows on the same object should merge |

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are writing or reviewing actual `*.flow-meta.xml`: three complete flows (before-save, after-save with entry conditions and a scheduled path, before-delete), a `FlowTest`, the `FlowDefinition` activation trap, `package.xml`, deploy order, and the `FlowDefinitionView` verification query |
| `references/gotchas.md` | The flow deploys and still misbehaves — duplicate side effects, recursion, ties in run order, scheduled paths that batch differently than expected |
| `references/examples.md` | You want the narrative before/after: what a practitioner built first, what broke, and the corrected shape |
| `references/llm-anti-patterns.md` | You are reviewing flow advice or generated XML produced by an AI assistant, or self-checking your own output |
| `references/well-architected.md` | You need the pillar framing, the tradeoffs, or the source list behind a claim in this skill |
| `templates/record-triggered-flow-patterns-template.md` | You are recording the design decision — trigger context, pattern choice, recursion guard — for review |
| `scripts/check_record_triggered_flow_patterns.py` | Before every deploy. `--manifest-dir <source tree>`; exits non-zero on any finding |

---

## Related Skills

- **flow/flow-bulkification** — use when the pattern is correct but the volume behavior is unsafe.
- **flow/fault-handling** — use when the main concern is rollback behavior and user/admin error paths.
- **flow/orchestration-flows** — use when the automation spans multiple approval or assignment stages rather than a single save context.
- **apex/trigger-framework** — use when Flow is no longer the right transaction boundary (Pattern 3).
- **apex/trigger-and-flow-coexistence** — use when the object has both; this is the coexistence skill.
- **flow/flow-record-save-order-interaction** — use when the question is where this flow sits relative to validation rules, roll-ups, and other automation in the 20-step list.
- **flow/recursion-and-re-entry-prevention** — use when the flow is already looping and you need the guard patterns, not the trigger-context choice.
- **flow/subflows-and-reusability** — use when the record-triggered flow should delegate a decision to a reusable child flow; its `references/metadata-examples.md` has the parent/child pair and the input/output contract.
- **flow/flow-testing** — use when you need more than the single `FlowTest` shown here.
- **flow/flow-decision-element-patterns** — use when the branching inside the flow, not the trigger, is the hard part.
- **flow/flow-time-based-patterns** — use when the scheduled path is the design, not a side path.
- **standards/decision-trees/automation-selection.md** — upstream decision (Flow vs Apex vs Agentforce vs Approval Process).
- **standards/decision-trees/flow-pattern-selector.md** — downstream of that: which *kind* of flow, once automation-selection has said Flow.
