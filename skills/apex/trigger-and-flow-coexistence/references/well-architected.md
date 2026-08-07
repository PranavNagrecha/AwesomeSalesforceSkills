# Well-Architected Notes — Trigger And Flow Coexistence

## Relevant Pillars

- **Reliability** — Mixed automation on the same object leads to silent field-overwrite bugs. The execution order itself is deterministic (before-save Flow at step 3, before trigger at step 4), so the overwrite is reproducible on every save — but nothing in the platform reports it, so the *behaviour* is predictable while the *design* is not visible to anyone reading either automation in isolation. Reliable systems require explicit field ownership and recursion guards when triggers and Flows coexist.
- **Operational Excellence** — Coexistence increases the cognitive load for both developers and admins. Without an automation inventory, no single person can reason about what happens when a record is saved. Operational excellence requires documentation, a single-entry-point aspiration, and a change management process that prevents uncoordinated automation additions.
- **Scalability** — Each additional automation on an object adds DML, SOQL, and CPU consumption to the transaction. When triggers and Flows both run, the combined resource usage can exceed governor limits under bulk operations that work fine in single-record testing. Scalable coexistence requires bulk-safe patterns in both the trigger and the Flow.

## Architectural Tradeoffs

**Single entry point vs. team autonomy.** The ideal architecture is one automation type per object per timing slot. However, this requires either all logic in triggers (which excludes admin-maintained Flows) or all logic in Flows (which limits complex programmatic patterns). Most orgs land on a hybrid: triggers own complex, cross-object, or integration logic while Flows own simple field defaulting and notifications. This hybrid is acceptable if field ownership is documented and enforced.

**Guard complexity vs. migration investment.** Implementing cross-automation recursion guards (InvocableMethod bridges, hidden checkbox fields) adds complexity. If the org plans to consolidate to a single automation type within 6-12 months, the guard investment may not be worthwhile. Conversely, if coexistence will persist for years, guards are essential and should be treated as first-class infrastructure.

**Declarative validation vs. trigger validation.** In-trigger field validation (step 4) only sees the record as of step 4; later automation such as a workflow field update (step 11) can change what the trigger approved. Moving validation to declarative validation rules — which run at step 5, after both the before-save Flow and the before trigger — removes the gap between the two before-save automations. The tradeoff is that validation rules are less expressive than Apex code. Note that a before-save Flow cannot bypass a trigger's validation: it runs at step 3, before the trigger.

## Anti-Patterns

1. **Ungoverned automation sprawl** — Adding Flows to objects with triggers (or vice versa) without checking the automation inventory. This is the root cause of most coexistence bugs. Every new automation must be reviewed against the existing automation map.
2. **Assuming deployment order controls execution order** — Developers sometimes believe the trigger will run before the Flow because it was deployed first. Salesforce does not use deployment order, creation timestamp, or alphabetical order to sequence before-save automation; the sequence is fixed by step number (Flow at 3, trigger at 4). Design decisions justified by deployment history are unsound even when they happen to produce the right answer.
3. **Static-variable-only recursion guards** — Using a static Boolean to prevent trigger recursion without exposing the flag to Flows via InvocableMethod. The Flow continues to execute on every re-entrant save, causing one-sided infinite loops that are hard to diagnose because the trigger log shows it correctly skipping.

## Official Sources Used

- Apex Developer Guide: Triggers and Order of Execution (20-step list; before-save Flows step 3, before triggers step 4) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm
- Metadata API Developer Guide: Flow (`triggerOrder`, API 54.0+) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_visual_workflow.htm
- Salesforce Help: Record-Triggered Automation Decision Guide — https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger.htm
- Salesforce Architects: Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
- Salesforce Help: Flow Trigger Explorer — https://help.salesforce.com/s/articleView?id=sf.flow_trigger_explorer.htm
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
