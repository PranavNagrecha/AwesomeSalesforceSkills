# Well-Architected Notes — Workflow Rule to Flow Migration

## Relevant Pillars

- **Reliability** — Migrated flows must be as reliable as the rules they replace. Fault paths, bulk testing, and validated SOAP payload schemas ensure no silent failure modes are introduced.
- **Operational Excellence** — Flow Trigger Explorer provides explicit execution order visibility that Workflow Rules never offered. Migration is an opportunity to rationalize all automation per object.

## Architectural Tradeoffs

1. **Tool migration vs. manual rebuild**: The tool is fastest but only handles a subset of Workflow Rule capabilities. Rules with ISCHANGED/ISNEW criteria, tasks, time-based actions, or global variables require manual rebuild. Attempting the tool on unsupported rules produces flows that appear correct but fire too broadly.

2. **One-to-one migration vs. consolidation**: Consolidating multiple Workflow Rules on the same object into a single record-triggered flow with Decision elements is architecturally cleaner, but harder to test and review. One-to-one migration is safer for complex orgs but increases Flow Trigger Explorer maintenance.

3. **Cutover timing for time-based actions**: Deactivating a rule immediately cancels all pending time-based actions. Teams must weigh fast cutover (some in-flight actions lost) against delayed cutover (longer parallel operation risk).

## Anti-Patterns

1. **Running both Workflow Rule and replacement Flow simultaneously** — Even briefly running both active on the same object creates double execution of field updates and double email alerts. Deactivate the Workflow Rule the moment the Flow is activated.

2. **Assuming the Migrate to Flow tool is comprehensive** — The tool handles the most common Workflow Rule patterns only. ISCHANGED criteria, tasks, and time-based actions are silently dropped. Every generated flow must be reviewed against the source rule.

3. **Not verifying Outbound Message payload compatibility** — SOAP integration partners may break after migration if the payload schema changes. Always capture and compare before/after payloads.

## Official Sources Used

- Transition to Flow — Retirement of Workflow Rules and Process Builder — https://help.salesforce.com/s/articleView?id=000389396&type=1
- Workflow Rules Retirement — https://help.salesforce.com/s/articleView?id=001096524&type=1
- Migrate to Flow Tool Considerations — https://help.salesforce.com/s/articleView?id=sf.migrate_to_flow_tool_considerations.htm&type=5
- Send an Outbound Message from a Record-Triggered Flow — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_builder_outbound_message.htm&release=234&type=5
- Flow Reference — https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5
