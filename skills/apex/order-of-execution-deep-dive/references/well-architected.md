# Well-Architected Notes — Order of Execution Deep Dive

## Relevant Pillars

- **Reliability** — The order of execution is a deterministic platform contract. Automation that respects it produces predictable outcomes. Automation that ignores it introduces intermittent failures that are hard to reproduce because they depend on which other automations are active, which fields are populated, and whether workflow rules fire on a given run.
- **Operational Excellence** — Explicit knowledge of the 20-step sequence reduces mean time to resolution for automation bugs. Teams that document which automations occupy which steps can reason systematically about interaction effects and maintain automation over time without breaking changes.

## Architectural Tradeoffs

**Before-save Flow vs. Before Apex Trigger for field derivation:** Both write to the record without extra DML, but they occupy different steps — Flow at step 3, trigger at step 4. Before-save Flows are preferred by Salesforce for simple field computations because they require no code and are easier to maintain by admin-level contributors. Before Apex triggers are preferred when the logic requires collection operations, complex conditionals, or platform APIs not available in Flow. The tradeoff is maintainability (Flow wins for admins) vs. capability (Apex wins for complex logic). Avoid both writing the same field — and note that if they do, the trigger's value is what persists, because step 4 follows step 3.

**After-save Flow vs. After Apex Trigger for related record work:** After Apex triggers (step 8) run within the same transaction as the originating DML, which allows them to create related records that are committed atomically. After-save Flows (step 14) also run within the same transaction but later, after workflow rules and Process Builder. The tradeoff: after Apex is earlier and can be queried in the same transaction by subsequent after triggers; after-save Flow is later and more accessible to non-developers but cannot be queried by Apex triggers in the same transaction.

**Workflow field updates vs. before-save Flow for field updates:** A workflow field update at step 11 re-fires before update and after update triggers once. This makes all triggers on the object effectively non-idempotent unless guarded. Before-save Flows (step 3) do not trigger a re-fire because they write to the in-memory record, not via a separate DML. Migrating workflow field updates to before-save Flows is a reliability improvement: it simplifies execution, removes re-fire risk, and removes the dependency on the legacy workflow engine.

## Anti-Patterns

1. **Multi-tool field ownership without coordination** — Two or more automations (trigger, Flow, workflow) writing to the same field at different steps with no coordination produces a "last writer wins" outcome that is unpredictable as automations are added or modified over time. Assign one automation as the authoritative writer for each field. This is the automation equivalent of the Salesforce Well-Architected principle of single sources of truth.

2. **Non-idempotent triggers without recursion guards** — An after trigger that unconditionally creates records, sends messages, or increments counters without a static guard will execute its side effects twice whenever a workflow field update re-fires triggers, or on every recursive DML cycle. Idempotency in Apex triggers is not optional in orgs with active workflow rules.

3. **Implicit timing dependency between Flow and Apex** — Designs where an after Apex trigger queries for records that an after-save Flow is supposed to have just created are architecturally fragile. They rely on step 8 vs. step 14 ordering in the same transaction, which is stable but creates a hidden coupling. If the Flow is deactivated or the trigger is moved, the query silently returns zero rows. Make the dependency explicit by either consolidating to one tool or adding a defensive null check with a clear comment.

## Official Sources Used

- Apex Developer Guide — Triggers and Order of Execution (20-step list; before-save Flows step 3, before triggers step 4) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm
- Metadata API Developer Guide — Flow (`triggerOrder`, API 54.0+) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_visual_workflow.htm
- Salesforce Well-Architected — Reliability — https://architect.salesforce.com/well-architected/reliable
- Salesforce Well-Architected — Operational Excellence — https://architect.salesforce.com/well-architected/operational-excellence
