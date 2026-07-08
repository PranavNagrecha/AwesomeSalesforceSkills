# Well-Architected Notes — Record Triggered Flow Patterns

## Relevant Pillars

### Reliability

Choosing the right record-triggered pattern keeps transactions predictable and reduces accidental recursion or hidden side effects.

### Scalability

Before-save and after-save have very different scale characteristics, and the trigger model needs to fit the real record volume.

### Operational Excellence

Well-scoped entry criteria and explicit trigger context make record-triggered automation easier to reason about, debug, and hand over.

## Architectural Tradeoffs

- **Before-save efficiency vs after-save flexibility:** Before-save is cheaper, but after-save is necessary for committed side effects and related-record work.
- **Declarative speed vs code-level control:** Flow is easier to maintain for moderate logic, while Apex provides tighter orchestration for complex transaction behavior.
- **Broad starts vs explicit business events:** Broad starts are quicker to configure, but field-change-aware criteria produce more reliable automation.
- **Trigger order vs consolidation:** Trigger order values (1–2,000) make an existing multi-flow phase deterministic, which is real operational value. They also make it cheap to keep adding flows to that phase. Prefer consolidation; use trigger order to stabilize what already exists, and remember it cannot sequence a flow against Apex or across the before-save/after-save boundary.

## Anti-Patterns

1. **After-save used for simple same-record updates** — wastes DML and creates avoidable recursion risk.
2. **Record-triggered flows that run on every edit** — operationally noisy and harder to troubleshoot.
3. **Ignoring mixed automation on the same object** — the flow design fails because validation rules or Apex still shape the transaction.
4. **Partial trigger order coverage** — numbering some flows in a phase and not others produces an ordering nobody predicted, because unset flows sequence between the 1–1,000 and 1,001–2,000 bands.
5. **Treating trigger order as a platform-wide priority** — it never moves a flow ahead of an Apex trigger or across the save-phase boundary.

## Official Sources Used

- Triggers and Order of Execution (Apex Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm — step numbering, the recursive-save skip window (steps 9–17), and the workflow-field-update sub-sequence ("flows ... aren't run again"; before/after update triggers run "one more time (and only one more time)")
- Build a Record-Triggered Flow (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/record-triggered-flows/build-a-record-triggered-flow — the Fast Field Updates vs Actions and Related Records tradeoff, including "you can update any record (not just the record that triggered the flow) and perform actions"
- Before-Save Record-Triggered Flows — https://help.salesforce.com/s/articleView?id=platform.flow_concepts_trigger_record.htm&language=en_US&type=5 — before-save scope and `$Record__Prior`
- Define the Run Order of Record-Triggered Flows for an Object — https://help.salesforce.com/s/articleView?id=platform.flow_task_trigger_run_order.htm&language=en_US&type=5
- Guidelines for Defining the Run Order of Record-Triggered Flows — https://help.salesforce.com/s/articleView?id=platform.flow_concepts_trigger_guidelines.htm&language=en_US&type=5
- Spring '22 Release Notes: Define the Run Order of Record-Triggered Flows for an Object — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_builder_trigger_order.htm&release=236&type=5 — the three trigger-order bands, the alphabetical-API-name tie-break, and "you can't prioritize an after-save flow to run before any before-save flows or before an Apex trigger"
