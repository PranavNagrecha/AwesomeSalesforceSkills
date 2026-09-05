---
name: flow-record-save-order-interaction
description: "Reason about how record-triggered flows interleave with the Salesforce Save Order (validation, before-save flows, before triggers, duplicate rules, after-save flows, workflow, after triggers, assignment, auto-response, escalation). Trigger keywords: save order, before-save flow, after-save flow, dml order, trigger vs flow order, order of execution step, recursive save, triggerOrder, doesRequireRecordChangedToMeetCriteria, AsyncAfterCommit, FLOW_START_INTERVIEW_BEGIN, stale field after save. NOT for choosing before-save vs after-save for one flow — use flow/record-triggered-flow-patterns. NOT for picking which tool stamps a field on save — use admin/workflow-field-update-patterns."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "save order"
  - "before-save flow"
  - "after-save flow"
  - "dml execution order"
  - "trigger flow interaction"
  - "trace which automation overwrote my field on save"
  - "why did my before-save flow value fail a validation rule"
  - "my after-save flow runs twice on one update"
  - "flow updates the record and triggers itself again"
  - "duplicate rule blocked the save and the after-save flow never ran"
  - "parent after-save flow never fires from a child roll-up"
  - "which step of the order of execution does my flow run in"
  - "after trigger sees the wrong case owner"
  - "map every automation on this object to the 20-step save order"
  - "two flows on the same object run in the wrong order"
  - "workflow field update did not re-run my flow"
  - "scheduled path ran against committed data"
  - "after-save flow keeps re-triggering itself in the order of execution"
tags:
  - flow
  - save-order
  - record-triggered
  - triggers
  - automation-ordering
inputs:
  - Object with multiple automations firing on insert/update
  - Suspected ordering issue (recursion, stale value, double-save)
outputs:
  - Save-order trace
  - Recommendation (move earlier, collapse, or relocate logic)
  - Recursion-guard plan
dependencies:
  - flow/record-triggered-flow-patterns
  - flow/flow-migration-from-trigger
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Flow & Save Order Interaction

This skill answers one question: **at the step where this flow runs, what can
it see, and what can it change?** Everything else — which trigger context to
pick, how to govern a flow portfolio, how to bulkify — belongs to the siblings
listed at the bottom.

## Diagnostic Symptoms

- Multiple automations fire on the same object and you need to predict
  outcome.
- A value is being read stale, or a flow appears to run twice.
- Deciding whether to put logic in a before-save Flow vs a before
  trigger vs an after-save Flow.
- Diagnosing a recursion loop crossing triggers and flows.
- A save "succeeded" but a downstream record never appeared, with no error.

## Out of Scope

- Plain CRUD with a single automation — there is nothing to order.
- Platform-event-triggered or schedule-triggered flows — they are not
  part of the DML save order (see `references/gotchas.md` Gotcha 12).
- Choosing before-save vs after-save for a single new flow —
  `flow/record-triggered-flow-patterns`.
- Making `triggerOrder` a merge gate across the portfolio —
  `flow/flow-governance`.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it
first.

Gather if not available:
- The object, and the DML operation in question (insert, update, upsert,
  delete).
- Every automation already on it: record-triggered flows and their
  `triggerType` / `recordTriggerType` / `triggerOrder`, Apex triggers,
  validation rules, duplicate rules, workflow rules still active, assignment
  and escalation rules, roll-up summary fields on the parent.
- The specific field or side effect that is wrong, and what the reporter
  expected instead.
- Whether the symptom appears on a single-record save, a bulk load, or both.

## Questions to Ask Before Configuring

Every row below decides a step number, and every row traces to a documented
behaviour in `references/gotchas.md`. An agent that skips them produces a
design that is correct about the tool and wrong about the timing.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which step does this logic need to *read* from, and which step does it need to *write* at?" | The two are often different steps, and only one automation type sits at each | The trigger context is chosen by the data it needs, not by habit (Gotcha 4) |
| "Does any validation rule or duplicate rule test a field this flow writes?" | Steps 5 and 6 both run after step 3, so a before-save write is what gets validated and what gets matched — and a duplicate block ends the transaction before step 7 | The rule and the flow get reviewed as one unit, and the fault design accounts for a save that stops at step 6 (Gotchas 1, 2) |
| "Is anything else already writing this field — an Apex before trigger, a workflow field update, another flow?" | Step 4 always overwrites step 3, and a workflow field update at step 11 re-fires triggers but never re-fires flows | A single owner per field, and the list of fields this flow may not touch (Gotchas 3, 7, 14) |
| "Is the requirement a state ('while Escalated') or a transition ('when it becomes Escalated')?" | `doesRequireRecordChangedToMeetCriteria` is defined against the triggering *update*; a state filter re-fires on every later edit | The `<start>` block, and whether a marker field is needed alongside the transition test (Gotcha 6) |
| "Does this flow write back to its own triggering object, and what is supposed to react to that write?" | The nested save skips steps 9–17, so after-save flows, assignment, workflow, escalation, entitlement and roll-ups do not run on it | The reaction gets hooked at a step the recursive save still runs — 3, 4 or 8 — instead of silently never firing (Gotchas 5, 8) |
| "Does anything downstream need to be true only *after* the commit?" | An `AsyncAfterCommit` path runs at step 20 and cannot roll the save back; a platform event defaults to publishing before the commit | A deliberate `pathType`, a deliberate `publishBehavior`, and a replay story for the async half (Gotchas 10, 11) |
| "Is this object Case or Lead, and does an assignment, escalation or entitlement rule participate?" | Steps 9, 10, 12 and 15 only do work on those objects, and an old `apiVersion` moves after-save flows to the far side of step 15 | The owner-dependent and entitlement-dependent logic lands after the step that produces it (Gotchas 9, 13) |

**What a proper configuration adds over just doing it:** every field on the
object has one writing step and a known set of reading steps, so "the value is
stale" and "the flow ran twice" become statements someone can check against
`templates/save-order-map.md` and the checker's map output, instead of
opinions traded in a thread.

## The Save Order (canonical, 20 steps)

Numbering matches the Apex Developer Guide, *Triggers and Order of Execution*
(`apexdev.txt` L15416–L15489). Use these numbers verbatim — several superseded
16-, 18-, and 19-step numberings are still in wide circulation and do not line
up.

1. Load the original record from the database (or initialize it for an upsert).
2. Overwrite with the new field values from the request; run request-type system validation.
3. **Before-save Flows** (record-triggered, "Fast Field Updates").
4. **Before triggers.**
5. Most system validation re-run **and** custom validation rules. Layout-specific rules are the one check not repeated on a standard UI edit.
6. Duplicate rules (a block action stops the save here — steps 7–20 do not run).
7. DML save (record not committed yet).
8. After triggers.
9. Assignment rules (Case / Lead).
10. Auto-response rules (Case / Lead).
11. Workflow rules. A workflow **field update** re-runs system validations and before update / after update triggers one more time, and only one more time.
12. Escalation rules (Case only).
13. Process Builder and workflow-launched Flows — not in a guaranteed order.
14. **After-save Flows** (record-triggered), ranked among themselves only by `triggerOrder`.
15. Entitlement rules.
16. Roll-up summary on the parent; the parent then goes through its own save procedure.
17. Roll-up summary on the grandparent.
18. Criteria-based sharing evaluation.
19. Commit.
20. Post-commit logic (email, `@future` / Queueable / Batch, asynchronous Flow paths).

**A recursive save runs a truncated list.** A save that begins inside another
save skips steps 9 through 17 (`apexdev.txt` L15414–L15415). The documented
case is the parent save the platform launches at step 16, but a flow's own DML
produces the same shape. Steps 1–8 and 18–20 still run; after-save Flows do
not. That single fact explains most "it worked when I tested it by hand"
reports — see `references/gotchas.md` Gotcha 5.

**Before-save Flow vs before trigger is determinate.** Step 3 and step 4 are
separate, consecutive steps. The Flow always runs first; the trigger always
runs second. Guidance that puts both at "step 3" and calls the outcome
indeterminate is describing a superseded version of the docs page.

## What Each Context Can Observe And Mutate

This table is the skill. Read down the left column to find the data you need,
then take the context on the right — not the one you were already planning to
use.

| You need to … | Available from step | Context that can do it | Context that cannot, and why |
|---|---|---|---|
| Write a field on the record being saved, with no extra DML | 3 | Before-save flow assigning `$Record.<field>` | After-save flow — its `recordUpdates` is a second save procedure (checker rule R1) |
| Be the last writer of a contested field | 4 | Apex before trigger | Before-save flow — step 4 overwrites it |
| Have a value tested by a custom validation rule | before 5 | Before-save flow (3), before trigger (4) | After-save flow — step 14 is past validation |
| Have a value matched by a duplicate rule | before 6 | Before-save flow (3), before trigger (4) | Anything at step 8 or later |
| Read the record's `Id` on an insert | 7 | After trigger (8), after-save flow (14) | Before-save flow — the row does not exist yet |
| Read the assignment-rule owner (Case / Lead) | 9 | After-save flow (14), workflow (11) | After trigger (8) — one step too early |
| React to a workflow field update | 11 | Before/after update triggers, re-fired once | Record-triggered flows — they are explicitly not re-run |
| React to a recalculated roll-up on the parent | 16 | Parent's before (4) or after (8) trigger | Parent's after-save flow — step 14 is inside the recursive save's skipped range |
| Act only on data that is durably committed | 19 | `AsyncAfterCommit` scheduled path (20), Queueable, `@future` | Anything at steps 3–18 |
| Roll the save back on failure | up to 18 | Before-save flow, triggers, after-save flow | Async path — the commit already happened |

## Decision: Before-Save Flow vs Before Trigger

- **Before-save Flow** — same-record field updates. Cheapest option; the
  assignment to `$Record` *is* the write, so there is no second DML.
- **Before trigger** — when you need SOQL, related-record lookup, complex
  control flow, or you must be the final writer of a field.
- **After-save Flow** — cross-record DML, external calls, creating related
  records, or anything that needs data produced at steps 7–13.

UNVERIFIED (2026-09-05): the rule that a before-save flow cannot perform DML,
send email, publish platform events or carry scheduled paths is documented
only on help.salesforce.com. `api_meta.txt` defines `recordCreates`,
`recordUpdates`, `recordDeletes`, `actionCalls`, `subflows` and
`scheduledPaths` on `Flow`/`FlowStart` without restricting any of them by
`triggerType`. The checker reports these as ADVISORY, not ERROR, for that
reason.

## Recommended Workflow

1. **Build the map before forming a theory.** Copy
   `templates/save-order-map.md` and fill one row per automation. Generate the
   flow half mechanically:
   `python3 skills/flow/flow-record-save-order-interaction/scripts/check_flow_record_save_order_interaction.py --manifest-dir force-app/main/default --map-only`
   — it prints every record-triggered flow grouped by object, placed at step 3
   or 14, ordered by `triggerOrder`, with its scheduled paths flagged.
2. **Name the writing step and the reading step for the field in dispute.**
   Use the observe/mutate table above. Most reports resolve here: the reader is
   earlier in the list than the writer, or the writer is a step that a
   recursive save skips.
3. **If a loop is suspected, trace the DML chain, not the flow.** Follow each
   `recordUpdates` / `recordCreates` to the object it writes, and apply the
   step 9–17 truncation to every nested pass (`references/gotchas.md`
   Gotcha 5). Confirm with two `FLOW_START_INTERVIEW_BEGIN` entries naming the
   same flow in one debug log (`references/metadata-examples.md` § 8b).
4. **Fix by relocating the step, then by guarding.** Move a same-record write
   to step 3; move an owner-dependent side effect to step 14; hook a roll-up
   reaction on the parent's trigger. Only then add
   `doesRequireRecordChangedToMeetCriteria`, a `filterFormula` or a marker
   field — guards on a flow that is at the wrong step just make the wrong
   behaviour rarer.
5. **Write the artifacts from `references/metadata-examples.md`** — § 1 for
   the before-save shape, § 2 for the after-save-plus-guards shape, § 3 for the
   `triggerOrder` pair, § 4 for the post-commit path, § 5 for the `FlowTest`
   that proves the transition rather than the state.
6. **Run the checker without `--map-only`, then a check-only deploy.** R1
   catches an after-save flow updating `$Record`, R2 an unguarded self-write,
   R3 an undeclared run order, R4 a before-save flow carrying after-save
   elements. Then
   `sf project deploy validate --manifest manifest/package.xml`.
7. **Verify the order in a log, not in a diagram.** Follow
   `references/metadata-examples.md` § 8b: Workflow category at `FINE`,
   Validation at `INFO`, then check that `FLOW_START_INTERVIEW_BEGIN` precedes
   the before-trigger `CODE_UNIT_STARTED`, that `VALIDATION_RULE` follows both,
   and that the step-14 interviews appear after the after-trigger code units.
   Record the result in the save-order map so the next person inherits
   evidence rather than a theory.

## Official Sources Used

- Apex Developer Guide — *Triggers and Order of Execution* (`apexdev.txt`
  L15402–L15510): the 20-step list, the recursive-save note, the workflow
  field-update re-fire, the API 53.0 entitlement ordering, and the
  no-guaranteed-order rule for multiple triggers.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Metadata API Developer Guide — `Flow`, `FlowStart`, `FlowScheduledPath`,
  `FlowRecordUpdate`, `FlowTest` (`api_meta.txt` L68020–L68450, L71264–L71424,
  L72279–L72545, L73920–L74460): `triggerType`, `recordTriggerType`,
  `triggerOrder`, `doesRequireRecordChangedToMeetCriteria`, `filterFormula`,
  `pathType` `AsyncAfterCommit`, and the deployable XML shapes.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Object Reference — `AssignmentRule` (`object_reference.txt` L7044): the
  Case/Lead scope of save-order step 9.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf

The full source list, with the claim each one supports, is in
`references/well-architected.md`.

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are writing or reviewing the actual XML: a before-save flow assigning `$Record`, an after-save flow updating a parent with both recursion guards, a `triggerOrder` pair on one object, an `AsyncAfterCommit` scheduled path, a `FlowTest`, `package.xml`, deploy order, and the debug-log event table that proves where each flow ran |
| `references/gotchas.md` | The design looks right and the behaviour is wrong — a value read stale, a duplicate block that swallowed the transaction, a parent flow that never fires, an event published before the save succeeded |
| `references/examples.md` | You want the worked traces: two designs for the same requirement scored step by step, and the recursion and roll-up cases end to end |
| `references/llm-anti-patterns.md` | You are reviewing save-order claims produced by an AI assistant, or checking your own output for the "indeterminate step 3" and "full parent save" errors |
| `references/well-architected.md` | You need the pillar framing, the tradeoffs, or the source behind a specific claim |
| `templates/save-order-map.md` | You are recording the per-object map — one row per automation, one owner per field, the recursion chain and the sign-off |
| `scripts/check_flow_record_save_order_interaction.py` | Before every deploy (`--manifest-dir <source tree>`), and with `--map-only` at the start of any investigation |

## Related Skills

- **flow/record-triggered-flow-patterns** — owns the before-save vs after-save
  choice for a single new flow; come here once the flow exists and the
  question is where it sits relative to everything else.
- **flow/flow-governance** — owns `triggerOrder` as a portfolio rule, the
  undeclared-tie query and the merge gate.
- **flow/flow-bulkification** — owns the limits arithmetic once the ordering is
  right and the volume is not.
- **flow/flow-migration-from-trigger** — owns moving logic out of Apex, which
  changes which step it runs at.
- **apex/trigger-and-flow-coexistence** — owns an object that has both, and
  the handoff between step 4/8 and steps 3/14.
- **apex/recursive-trigger-prevention** — owns the Apex-side guard once the
  loop crosses into code.
- **admin/validation-rules** — owns the rule itself; this skill only owns when
  it runs relative to the flow.
- **standards/decision-trees/automation-selection.md** — upstream: whether this
  should be a flow at all.
