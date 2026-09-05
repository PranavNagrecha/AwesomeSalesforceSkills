# Well-Architected Notes — Process Automation Selection

## Relevant Pillars

- **Scalability** - the wrong automation surface becomes a limit problem under real volume.
- **Reliability** - clear boundaries reduce recursion, overlap, and unpredictable order-of-execution behavior.
- **Operational Excellence** - migration off legacy automation and clearer tool ownership reduce support cost.

## Architectural Tradeoffs

- **Declarative default vs code control:** Flow is easier to own, but Apex provides stronger control for complex or high-volume transaction behavior.
- **Single surface purity vs mixed boundary design:** keeping everything in one tool is simpler, but a deliberate Flow-plus-Apex split can be safer when responsibilities differ.
- **Legacy preservation vs migration:** preserving old automation lowers immediate effort, but increases long-term risk and confusion.
- **Deciding once vs deciding repeatedly:** a written decision record costs an hour now and removes the argument permanently; an undocumented choice is re-litigated by whoever inherits the object, usually with worse information.
- **Routing centrally vs routing per skill:** the decision trees hold one copy of the routing logic so it can be corrected in one place. A skill that restates a branch drifts from the tree silently — cite the question number instead.

## Anti-Patterns

1. **Apex by reflex** - using code for simple same-record automation that Flow already handles better.
2. **Flow by ideology** - forcing complex transaction or service logic into declarative automation that cannot hold it cleanly.
3. **Legacy logic as architecture baseline** - keeping Workflow Rule or Process Builder as the model for new design.
4. **Deciding without inventorying** - proposing a new automation for an object before listing what already runs on it, which turns the existing rules into surprises rather than rejected alternatives.
5. **Rejected alternatives with no reasons** - a record that names what was not chosen but not why is unreviewable; the reason is the part a later reader needs.

## Official Sources Used

- Apex Developer Guide — "Triggers and Order of Execution", steps 3, 4, 8, 11 and 14 and the recursive-save note (positions of before-save flow, before triggers, after triggers, workflow field-update re-fire and after-save flow; supports gotchas 1, 5 and 6 and the Core Concepts "positional" section): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Developer Guide — "Triggers" ("The records that fire the after trigger are read-only"; updating or deleting a record in its before trigger, or deleting it in its after trigger, raises a runtime error; supports gotcha 7): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Salesforce Developer Limits and Allocations Quick Reference — Apex Governor Limits table (100/200 SOQL, 50,000 rows, 150 DML statements, 10,000 DML rows, stack depth 16, 6 MB / 12 MB heap, 10,000 ms / 60,000 ms CPU; supports gotcha 8 and the volume fields on the decision record): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf
- Metadata API Developer Guide — `FlowStart`, `FlowSchedule`, `FlowScheduledPath` (`recordTriggerType` and `triggerType` enums, `schedule` required when `triggerType` is `Scheduled`, one interview per queried record, `maxBatchSize` 1–200 default 200, `frequency` enum; supports gotcha 11 and worked decisions 1 and 3): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — Flow warning on retrieved Process Builder metadata (`processType` `Workflow` / `InvocableProcess` must not be edited and redeployed) and `WorkflowRule.failedMigrationToolVersion` (supports gotchas 9 and 10 and the legacy-inventory step): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Object Reference for the Salesforce Platform — `FlowDefinitionView` (`IsActive`, `IsOutOfDate`, `ProcessType`, `TriggerType`, `RecordTriggerType`, `TriggerOrder` 1–2,000, `TriggerObjectOrEventLabel`) and `ApexTrigger` (`TableEnumOrId`, `Status`, the `Usage*` context flags) — supports the one-object-one-order inventory queries: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- `standards/decision-trees/automation-selection.md` — the canonical Flow-vs-Apex routing tree this skill applies (Q1–Q12, the graduation conditions, and the Workflow Rule / Process Builder end-of-support statement sourced to Salesforce Help article 001096524)
- `standards/decision-trees/flow-pattern-selector.md` — which kind of Flow once the routing tree says Flow (Q1–Q9, and the ~50k schedule-triggered line at Q6)
- `standards/decision-trees/async-selection.md` — which async mechanism once the routing tree says Apex (Q1, Q8 scope sizing, and the capability matrix)
