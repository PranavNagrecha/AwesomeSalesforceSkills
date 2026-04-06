# Well-Architected Notes — Opportunity Trigger Patterns

## Relevant Pillars

- **Reliability** — Opportunity triggers sit in a high-traffic transaction path. Failures in stage-change handlers or rollup logic affect the sales process directly. Split percentage arithmetic errors fail silently in test assertions but loudly in production saves.
- **Performance** — Every Opportunity save can fire related rollups and split redistributions. Queries or DML inside loops are the primary performance failure mode. Aggregate SOQL patterns and single-DML updates keep the transaction overhead predictable.
- **Scalability** — Data migrations and bulk imports frequently update hundreds of Opportunity records in a single transaction. All handler logic must be written for 200-record batches from day one, not retrofitted later.
- **Security** — Handler classes must declare `with sharing` unless there is a documented business reason to elevate sharing context. Rollups that write to Account fields must not expose data the running user should not see. OpportunityTeamMember DML is gated by Salesforce sharing permissions — test as both the record owner and a non-owner user.
- **Operational Excellence** — An activation bypass (Custom Metadata or Custom Setting) on the Opportunity trigger must be present for data loads and incident response. Without it, any bad trigger logic requires a deployment to disable, which increases MTTR.

## Architectural Tradeoffs

**Synchronous rollup vs. asynchronous rollup:** Performing Account rollups synchronously in the trigger guarantees data consistency but adds DML to every Opportunity save. For orgs with very high Opportunity volume, consider a Platform Event boundary that queues the rollup outside the save transaction, accepting eventual consistency. The synchronous pattern is correct for most orgs; choose async only after measuring actual transaction time.

**Trigger-based split management vs. Flow-based:** OpportunitySplit records cannot be managed by Flow directly — Flow has no supported action for split DML. Apex is the only option for split redistribution logic. Do not let an LLM suggest Flow for this use case.

**Shared handler vs. per-trigger handler:** If the org uses a trigger framework (FFLIB, Kevin O'Hara), the Opportunity-specific logic must be implemented inside that framework's dispatch. A standalone `OpportunityTriggerHandler` class that ignores the existing framework creates two execution paths on the same object with undefined ordering.

## Anti-Patterns

1. **Logic directly in the trigger body** — Any business logic placed directly in `OpportunityTrigger.trigger` (rather than delegated to a handler) is untestable at the unit level, cannot be bypassed without a deployment, and violates the single-responsibility principle. The trigger body should contain only the activation guard, handler instantiation, and context dispatch.

2. **Split DML in before-context without an error boundary** — Placing split DML in a before-context is a platform error, not a design choice. LLMs sometimes generate this pattern because before-context "seems" earlier and "safer." It is a hard runtime exception and must never appear in generated code.

3. **Rollup that ignores old AccountId on reparenting** — A rollup trigger that only reads `Trigger.new.AccountId` silently creates stale data on the former parent Account. This is an invisible data quality issue that compounds over time in orgs that allow Opportunity reassignment.

## Official Sources Used

- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- Apex Trigger Best Practices — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_bestprac.htm
- OpportunitySplit Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_opportunitysplit.htm
- OpportunityTeamMember Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_opportunityteammember.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
