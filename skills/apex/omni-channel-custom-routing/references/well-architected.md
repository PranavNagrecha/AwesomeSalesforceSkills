# Well-Architected Notes — Omni-Channel Custom Routing

## Relevant Pillars

- **Reliability** — The three-DML sequence must be wrapped in error handling with orphan cleanup. A partial insert that leaves a `PendingServiceRouting` record without associated `SkillRequirement` records or without the `IsReadyForRouting` flag flipped will leave work items stranded in a pending state indefinitely. Reliable implementations treat all three DML steps as an atomic unit and delete on failure.
- **Performance** — SOQL queries for `ServiceChannel` and `Skill` must be issued once per transaction, not per record. Bulk patterns (collect, query, map, apply) are mandatory for any routing logic that fires from a trigger or batch job handling more than one record at a time.
- **Adaptable** — `ServiceChannelId` must never be hardcoded. Skill configurations change as business needs evolve. Routing logic that references `DeveloperName` values (resolvable at runtime) survives org migrations, sandbox refreshes, and environment promotions without code changes.
- **Security** — `PendingServiceRouting` and `SkillRequirement` are system-managed objects. Only system-level code (Apex running in system mode or with `with sharing` explicitly set) should interact with them. Expose routing logic through well-defined service methods, not directly from triggers, to allow consistent permission boundary enforcement.
- **Operational Excellence** — Routing failures should log enough context to diagnose problems: the `WorkItemId`, the `ServiceChannel.DeveloperName` attempted, and the exception message. Silent failures (where the insert succeeds but routing never fires) are the hardest to diagnose; structured logging prevents this.

## Architectural Tradeoffs

**Custom Apex routing vs. declarative routing rules.** Declarative routing configurations in Omni-Channel Setup (routing configurations, queues, skills assignments) cover the majority of standard routing scenarios with zero code. Custom Apex routing via `PendingServiceRouting` is appropriate only when routing decisions require runtime data unavailable to declarative rules — for example, routing based on entitlement levels read from related records, or dynamic skill requirements derived from case classification output. Defaulting to Apex routing when declarative rules suffice adds maintenance burden without capability benefit.

**Skill relaxation vs. manual fallback queues.** Using `IsAdditionalSkill = true` for overflow keeps routing logic inside the platform's native engine, which manages timeout and retry automatically. Building a custom fallback (e.g., a scheduled job that re-inserts routing records targeting a broader queue after a timeout) creates more moving parts and is harder to monitor. Prefer native relaxation unless the org requires overflow behavior that the platform's relaxation model cannot express.

**Trigger-based vs. batch-based routing.** Routing from an after-insert trigger provides the lowest latency but is subject to tighter governor limits. Batch-based routing allows more headroom and is preferable for backfill operations or high-volume scenarios. For real-time SLA requirements, use trigger-based routing with strict bulkification. For overnight or catch-up processing, use a batch job.

## Anti-Patterns

1. **Three-step collapse to one or two DML statements** — Attempting to insert `PendingServiceRouting` with `IsReadyForRouting = true` and no `SkillRequirement` records causes incorrect routing (any agent) or a DML exception. The three-step sequence is non-negotiable and must be treated as platform protocol, not a guideline.

2. **Environment-specific Id literals in Apex** — Embedding `ServiceChannelId` or `SkillId` literals in Apex source or custom labels that vary by environment creates a class of deployment bugs that are invisible to static analysis and only surface at runtime. All org-specific Ids must be resolved dynamically by querying stable `DeveloperName` or `Name` values.

3. **Missing orphan cleanup on partial failure** — Leaving an inserted `PendingServiceRouting` record without the subsequent `SkillRequirement` and `IsReadyForRouting = true` update strands the work item permanently. The next routing attempt fails with DUPLICATE_VALUE. Cleanup in the `catch` block is not optional defensive coding — it is required for the system to remain self-healing.

## Official Sources Used

- PendingServiceRouting Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_pendingservicerouting.htm
- SkillRequirement Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_skillrequirement.htm
- How Skills-Based Routing Works — https://help.salesforce.com/s/articleView?id=sf.omnichannel_skills_based_routing_how_it_works.htm
- Omni-Channel Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.omni_channel_dev_guide.meta/omni_channel_dev_guide/omni_channel_dev_guide.htm
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
