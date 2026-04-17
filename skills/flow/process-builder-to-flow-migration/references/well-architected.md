# Well-Architected Notes — Process Builder to Flow Migration

## Relevant Pillars

- **Reliability** — Migrated flows must be as reliable as the processes they replace. This means adding fault paths, testing bulk scenarios, and ensuring execution order is deterministic via Flow Trigger Explorer.
- **Performance Efficiency** — Migration unlocks ~10× improvement on before-save Fast Field Updates and ~50% improvement on after-save flows vs. Process Builder. These gains require bulk-safe flow design (no SOQL/DML in loops).
- **Operational Excellence** — Flow Trigger Explorer provides explicit, auditable execution order that Process Builder never offered. Migration is an opportunity to document and rationalize all automation on each object.

## Architectural Tradeoffs

1. **Tool migration vs. manual rebuild**: The Migrate to Flow tool is faster but only handles a subset of Process Builder capabilities. Manual rebuild is required for any process with invocable Apex, callouts, tasks, scheduled actions, or ISCHANGED/ISNEW criteria. Attempting to use the tool for unsupported processes produces flows that appear correct but behave differently.

2. **Consolidation vs. one-to-one replacement**: Multiple Process Builder processes on the same object are best consolidated into a single record-triggered flow with Decision elements routing between branches. One-to-one replacement with multiple flows on the same object works but increases Flow Trigger Explorer maintenance overhead.

3. **Cutover timing for scheduled actions**: Deactivating Process Builder immediately cancels pending scheduled actions. Teams must choose between accepting some missed scheduled actions (fast cutover) or delaying cutover until the scheduled action queue drains (safer but slower).

## Anti-Patterns

1. **Running PB and Flow simultaneously** — Activating a replacement flow while leaving the source Process Builder active creates undefined execution order and double-execution of field updates. Always deactivate PB the moment the Flow is activated.

2. **Assuming the migration tool produces production-ready flows** — The Migrate to Flow tool generates a starting point, not a final product. Generated flows lack fault paths, may mis-map criteria, and do not include monitoring instrumentation. Always review in Flow Builder before activation.

3. **Ignoring in-flight scheduled actions at cutover** — Deactivating a Process Builder process with hundreds of pending scheduled actions silently cancels them all. This is a data integrity issue, not just a functionality gap.

## Official Sources Used

- Move Processes and Workflows to Flow Builder with the Migrate to Flow Tool — https://help.salesforce.com/s/articleView?id=platform.flow_migrate_to_flow.htm&type=5
- Migrate to Flow Tool Considerations — https://help.salesforce.com/s/articleView?id=platform.migrate_to_flow_tool_considerations.htm&type=5
- Transition to Flow — Retirement of Workflow Rules and Process Builder — https://help.salesforce.com/s/articleView?id=000389396&type=1
- Workflow Rules Retirement — https://help.salesforce.com/s/articleView?id=001096524&type=1
- Flow Reference — https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5
- Flow Builder — https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5
