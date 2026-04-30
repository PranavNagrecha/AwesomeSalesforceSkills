# Well-Architected Notes — Flow Recursion and Re-Entry Prevention

## Relevant Pillars

- **Reliability** — Flow loops are an availability problem. The cascade either crashes ("Maximum trigger depth exceeded") or silently consumes CPU until governor limits stop the transaction. Either failure mode interrupts user-facing work and produces hard-to-diagnose tickets. Reliability here means "the same DML that succeeded yesterday succeeds today, regardless of how many automations chain off it."
- **Performance** — Even when a loop doesn't reach the depth limit, every cascade level burns CPU, SOQL queries, and DML statements against per-transaction governor budgets. A Flow that fires three times when it should fire once consumes 3× the budget of the single intended firing. Recursion prevention is performance prevention.

## Architectural Tradeoffs

- **State guard vs. hash idempotency vs. shared lock:** State guards (Pattern 1) are simplest and most maintainable, but they require the "already done" state to be characterizable in a formula. Hash idempotency (Pattern 2) handles the case where state can't be characterized but adds a custom field and computation. Shared locks (Pattern 3) handle cross-object cascades cleanly but introduce a new piece of data that two flows must coordinate around — a mini-protocol that future maintainers must understand. Pick the simplest pattern that fits.
- **Fix the loop vs. consolidate the automations:** A loop between Flow A and Flow B is sometimes a symptom of two automations that should be one. Combining them eliminates the cross-flow cascade entirely and is often the architecturally cleaner fix — if the team can absorb the consolidation cost. The "loop fix" patterns here are tactical; the strategic fix is sometimes "stop having two flows on the same object that write to each other's trigger fields."
- **Flow vs. Apex for high-recursion-risk logic:** Flow's lack of static state makes it a poor fit for logic that frequently needs recursion guards. If a single feature requires three-plus separate guard mechanisms, the team is fighting Flow's mental model. Migrating that feature to Apex (which has `static`, easier debugging, and clearer order-of-execution control) may be the right Well-Architected call. Cite `architect/automation-migration-router` when this tradeoff comes up.

## Anti-Patterns

1. **Relying on the trigger-depth limit as the recursion guard** — The limit is a failure mode, not a prevention mode. A loop that fits in 15 levels still wastes CPU and DML and will eventually grow to 17. Always add an explicit guard.
2. **Time-window throttles** — Skipping the Flow if the last update was less than N seconds ago. Race conditions and silent dropped updates. Use deterministic state-based guards instead.
3. **Disabling Flow during a problematic save (`Skip Save Actions` or similar bypass)** — Punts the problem; the underlying entry criteria are still wrong. The Flow either does its work or it doesn't, but the answer is to define "should this fire?" precisely, not to wallpaper over it.

## Official Sources Used

- Flow Reference — https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5
- Build a Record-Triggered Flow — https://help.salesforce.com/s/articleView?id=sf.flow_build_record_triggered.htm&type=5
- Apex Developer Guide — Triggers and Order of Execution — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm
- Flow Trigger Explorer — https://help.salesforce.com/s/articleView?id=sf.flow_trigger_explorer.htm&type=5
- Salesforce Well-Architected — Resilient — https://architect.salesforce.com/well-architected/resilient/overview
- Trailblazer Community — "Maximum Trigger Depth Exceeded" reference patterns — https://trailhead.salesforce.com/trailblazer-community
