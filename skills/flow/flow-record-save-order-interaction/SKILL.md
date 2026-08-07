---
name: flow-record-save-order-interaction
description: "Reason about how record-triggered flows interleave with the Salesforce Save Order (validation, before-save flows, before triggers, duplicate rules, after-save flows, workflow, after triggers, assignment, auto-response, escalation). Trigger keywords: save order, before-save flow, after-save flow, dml order, trigger vs flow order. Does NOT cover writing trigger handlers, approval process setup, or workflow rule migration."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - save order
  - before-save flow
  - after-save flow
  - dml execution order
  - trigger flow interaction
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Flow & Save Order Interaction

## Diagnostic Symptoms

- Multiple automations fire on the same object and you need to predict
  outcome.
- A value is being read stale, or a flow appears to run twice.
- Deciding whether to put logic in a before-save Flow vs a before
  trigger vs an after-save Flow.
- Diagnosing a recursion loop crossing triggers and flows.

## Out of Scope

- Plain CRUD with a single automation — there is nothing to order.
- Platform-event-triggered or schedule-triggered flows — they are not
  part of the DML save order.

## The Save Order (canonical, 20 steps)

Numbering matches the Apex Developer Guide, *Triggers and Order of Execution*. Use these numbers verbatim — several superseded 16-, 18-, and 19-step numberings are still in wide circulation and do not line up.

1. Load the original record from the database (or initialize it for an upsert).
2. Overwrite with the new field values from the request; run request-type system validation.
3. **Before-save Flows** (record-triggered, "Fast Field Updates").
4. **Before triggers.**
5. System validation re-run (required / field type / max length) **and** custom validation rules.
6. Duplicate rules (a block action stops the save here).
7. DML save (record not committed yet).
8. After triggers.
9. Assignment rules (Lead / Case only).
10. Auto-response rules (Lead / Case only).
11. Workflow rules. A workflow **field update** re-runs system validations and before update / after update triggers one more time, and only one more time.
12. Escalation rules (Case only).
13. Process Builder and workflow-launched Flows — not in a guaranteed order.
14. **After-save Flows** (record-triggered).
15. Entitlement rules.
16. Roll-up summary on the parent; the parent then goes through its own save procedure.
17. Roll-up summary on the grandparent.
18. Criteria-based sharing evaluation.
19. Commit.
20. Post-commit logic (email, `@future` / Queueable / Batch, asynchronous Flow paths).

**Before-save Flow vs before trigger is determinate.** Step 3 and step 4 are separate, consecutive steps. The Flow always runs first; the trigger always runs second. If both write the same field, the trigger's value is what saves — every time, in every org. Older guidance that puts both at "step 3" and calls the outcome indeterminate is describing a superseded version of the docs page.

## Decision: Before-Save Flow vs Before Trigger

- **Before-save Flow** — same-record field updates with no DML, no SOQL
  in the hot path. Cheapest option.
- **Before trigger** — when you need SOQL, related-record lookup, or
  complex control flow.
- **After-save Flow** — cross-record DML, external calls, creating
  related records.

## Recommended Workflow

1. List every automation on the object (flows, triggers, validation,
   duplicate rules, assignment, workflow).
2. Pin each one to its save-order slot.
3. Verify data each stage actually needs. Before-save flows cannot see
   rolled-up or after-trigger-computed values.
4. For recursion suspicion, trace the save chain: which automation
   re-issues DML on the same record in the same transaction?
5. Add a recursion guard or move the logic earlier to prevent the loop.
6. Validate using Flow Debug Log + Apex Debug Log in the same
   transaction.
7. Document the ordering decision in the flow's description so future
   admins see intent.

## Official Sources Used

- Triggers and Order of Execution (20-step list; before-save Flows step 3, before
  triggers step 4) —
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm
- Metadata API Developer Guide — Flow (`triggerOrder`, API 54.0+) —
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_visual_workflow.htm
- Before-Save Flows —
  https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_before_save.htm
