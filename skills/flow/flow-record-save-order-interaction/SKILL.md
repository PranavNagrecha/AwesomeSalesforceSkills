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

## The Save Order (canonical, abridged)

1. System validation (required / field type / max length).
2. Before-save Flows (record-triggered "Fast Field Updates").
3. Before triggers.
4. Duplicate rules.
5. System + custom validation rules.
6. DML save (record not committed yet).
7. After triggers.
8. Assignment rules.
9. Auto-response rules.
10. Workflow rules / field updates (legacy).
11. Processes + record-triggered Flows on after-save.
12. Escalation rules.
13. Entitlement rules.
14. Roll-ups + sharing rule recalculations.
15. Commit.
16. Post-commit logic (platform events, `@future`, async Apex).

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

- Triggers and Order of Execution —
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm
- Before-Save Flows —
  https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_before_save.htm
