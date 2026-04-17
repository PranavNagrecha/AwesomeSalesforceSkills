---
name: record-triggered-flow-patterns
description: "Use when designing or reviewing Salesforce record-triggered Flows, especially before-save vs after-save behavior, entry criteria, recursion avoidance, and when to escalate to Apex. Triggers: 'before save vs after save', '$Record__Prior', 'record-triggered flow', 'order of execution', 'flow recursion'. NOT for screen-flow UX or pure bulkification work when the trigger model is already correct."
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
inputs:
  - "business event that should trigger automation"
  - "whether only the current record or related records must change"
  - "existing Apex, validation rules, and other automation on the same object"
outputs:
  - "record-triggered flow design recommendation"
  - "review findings for trigger context and recursion risk"
  - "decision on before-save, after-save, or Apex"
dependencies: []
version: 2.0.0
author: Pranav Nagrecha
updated: 2026-04-17
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

- **Before-save record-triggered flows run BEFORE Validation Rules.** Fields you set in before-save get validated. An enrichment flow that sets an invalid value will be blocked by a Validation Rule — sometimes with a confusing error message.
- **After-save record-triggered flows run AFTER Apex after-triggers.** Apex triggers see the record as-saved; after-save flows see the record AFTER Apex has had a chance to modify it.
- **After-save flows run AFTER Workflow Rules (for orgs still running them)** and AFTER Process Builder (deprecated but still active in some orgs). Layered automation on the same object creates order-of-execution chains that are hard to trace.
- **Multiple record-triggered flows on the same object run in unspecified order.** Salesforce has introduced "Flow Trigger Explorer" and ordering controls, but the canonical guidance is: one record-triggered flow per object per save context.

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

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Common Patterns above; consult the Decision Guidance table
4. Validate — run the skill's checker script and verify against the Review Checklist above
5. Document — record any deviations from standard patterns and update the template if needed

---

## Salesforce-Specific Gotchas

1. **After-save updates to the triggering record can retrigger automation** — this is one of the most common Flow recursion smells. Before-save avoids it entirely for same-record writes.
2. **Before-save cannot replace all trigger behaviors** — if the logic needs related-record work, notifications, or callouts, the design must move to after-save or another boundary.
3. **A broad start condition becomes hidden operational cost** — flows that fire on every edit are harder to debug, more likely to clash with other automation, and more expensive to refactor later.
4. **Multiple automations on one object still interact** — record-triggered flows are not isolated from Apex triggers, duplicate rules, or validation behavior. When adding a new flow to an object, `list_flows_on_object` + `tooling_query` for existing triggers is non-negotiable.
5. **`$Record__Prior` is null on insert triggers** — guard with `NOT(ISNEW())` before comparing, or the comparison throws.
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

## Related Skills

- **flow/flow-bulkification** — use when the pattern is correct but the volume behavior is unsafe.
- **flow/fault-handling** — use when the main concern is rollback behavior and user/admin error paths.
- **flow/orchestration-flows** — use when the automation spans multiple approval or assignment stages rather than a single save context.
- **apex/trigger-framework** — use when Flow is no longer the right transaction boundary (Pattern 3).
- **apex/trigger-and-flow-coexistence** — use when the object has both; this is the coexistence skill.
- **standards/decision-trees/automation-selection.md** — upstream decision (Flow vs Apex vs Agentforce vs Approval Process).
