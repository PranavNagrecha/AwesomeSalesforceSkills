# Well-Architected Notes — Workflow Field Update Patterns

## Relevant Pillars

- **Reliability** — Recursion is the field-update reliability
  problem. After-save flows and triggers updating the same record
  recurse silently until the platform's 16-level cap; intermittent
  errors that are hard to reproduce. Before-save flow eliminates
  the class.
- **Operational Excellence** — One flow per object per save-time
  slot (vs fragmented per-team flows that all fire) is the
  highest-leverage operational discipline. Predictable order; one
  place to audit; one place to disable.

## Architectural Tradeoffs

- **Formula vs stamped (flow / trigger).** Formula = no automation,
  computed at read; stamped = automation cost but stored value
  cheaper to query. Cross-over depends on read volume vs write
  volume on the field.
- **Before-save flow vs Apex before-update trigger.** Both occupy
  the same order-of-execution slot. Flow is admin-editable, no test
  class needed. Apex is more expressive (callouts, Schema describe,
  complex types). Default to flow; reach for Apex when the logic
  exceeds flow's expressive power.
- **After-save flow vs after-update Apex trigger.** Same trade as
  above for the post-save slot. Flow handles the common cases.
- **One flow per object vs many.** Many is easier per-team; one is
  easier to audit and reason about. As orgs grow, one wins on
  governance.

## Anti-Patterns

1. **Same-record stamp implemented as after-save instead of
   before-save.** Wastes DML; introduces recursion risk.
2. **After-save flow updating same record without recursion guard.**
   Default behavior recurses.
3. **Reflexively building a flow for what could be a formula
   field.** No-automation is the right answer when the value is
   purely derived.
4. **Multiple per-team flows on the same object firing on the same
   save event.** Order is non-deterministic; debugging is painful.
5. **Migrating Workflow Rules without deactivating the source.**
   Both fire; field stamped twice.
6. **Before-save flow + before-update trigger on the same object
   with cross-dependency.** The order is fixed — flow at step 3, then
   trigger at step 4 — so a flow that depends on the trigger's output
   is structurally impossible, and the trigger can overwrite the flow.
7. **Migrating a field update without counting trigger passes.** The
   step-11 re-save fires update triggers a second time; moving the
   field update to before-save removes that pass, changing Apex
   behaviour in a deploy whose diff contains no Apex.
8. **Mapping `reevaluateOnChange` to nothing.** Flow has no equivalent
   element, so rules that only ever fired on the cascade stop firing
   and nobody notices until the downstream stamp goes missing.
9. **Leaving both writers live after cutover.** The workflow rule
   writes at step 11 and wins over the before-save Flow at step 3, so
   the "migrated" automation is not the one running.

## Official Sources Used

Every line reference below is to the plain-text extraction of the Summer '26
(v62) PDF named beside it.

- **Apex Developer Guide — "Triggers and Order of Execution"**
  (apexdev.txt:15402–15481) —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
  (the 20-step sequence used in SKILL.md's slot table; step 11's "Updates the
  record again… Executes before update triggers and after update triggers…
  one more time (and only one more time)", which grounds Gotcha 10; the
  recursive-save skip of steps 9–17 cited in metadata-examples Example 3).
- **Apex Developer Guide — "Additional Considerations" / "Fields Not Updateable
  in Before Triggers"** (apexdev.txt:15494–15499, 15593–15612) — same PDF
  (`Trigger.old` holding pre-initial-update values after a workflow field
  update, Gotcha 14; the field list that makes a before-save Flow the wrong
  replacement for some field updates, Gotcha 13).
- **Metadata API Developer Guide — `WorkflowFieldUpdate`**
  (api_meta.txt:140118–140245) —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
  (the element table in metadata-examples.md; the `operation` enum;
  `reevaluateOnChange`'s five-cascade limit, Gotcha 11; `NextValue` /
  `PreviousValue` picklist-only restriction, Gotcha 12; "Only User is supported
  in the current API" for `LookupValue`, Gotcha 15; `targetObject` as the
  cross-object case).
- **Metadata API Developer Guide — `Workflow`, `WorkflowRule`,
  `WorkflowTimeTrigger` and the Workflow sample definition**
  (api_meta.txt:139874–139943, 140374–140442, 140524–140545, 140555–140700) —
  same PDF (one file per object holding every workflow component; the
  `triggerType` enum that Example 2's mapping table converts to Flow settings;
  `failedMigrationToolVersion`; `workflowTimeTriggers` and Gotcha 16; the
  XML-escaping convention in `formula`).
- **Metadata API Developer Guide — `Flow`, `FlowStart`, `FlowRule`,
  `FlowRecordUpdate`** (api_meta.txt:71264–71296, 72322–72326, 72448–72553) —
  same PDF (`triggerType` `RecordBeforeSave` / `RecordAfterSave`;
  `recordTriggerType`; `doesRequireRecordChangedToMeetCriteria` as the exact
  equivalent of `onCreateOrTriggeringUpdate`; `scheduledPaths`; the
  `recordUpdates` element used in Example 3).
- **Metadata API Developer Guide — `CustomField`** (api_meta.txt:43422–43425) —
  same PDF (`formula` and `formulaTreatBlanksAs` in the formula-field artifact
  in examples.md Example 4).
- **Object Reference — `OpportunityFieldHistory`**
  (object_reference.txt:193408–193482) —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
  (the post-cutover verification query; its field table is also why
  `CreatedDate` carries an UNVERIFIED marker there).
- **Decision tree** — `standards/decision-trees/automation-selection.md` Q2–Q5
  (same-record vs cross-object vs Apex routing used in Examples 3 and 4) and
  `standards/decision-trees/flow-pattern-selector.md` Q2–Q3, Q5 (before-save vs
  after-save vs scheduled path).
- **Sibling skills** — `admin/process-automation-selection` (order-of-execution
  and `failedMigrationToolVersion` gotchas this skill cross-references rather
  than restates), `apex/order-of-execution-deep-dive`,
  `flow/record-triggered-flow-patterns`, `flow/workflow-rule-to-flow-migration`.
- **Salesforce Well-Architected — Overview**
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
  (the Reliability / Operational Excellence framing at the top of this file).
- **Salesforce Help — Before-Save Updates in Record-Triggered Flows**
  https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_before_save.htm&type=5
  (the governor-free same-record claim in Gotcha 1; retained from the skill's
  original source list — help.salesforce.com is not fetchable from this
  environment, so it was not re-verified in this pass).
- **Salesforce Help — Migrate to Flow Tool**
  https://help.salesforce.com/s/articleView?id=sf.workflow_migration_tool.htm&type=5
  (the Migrate to Flow sequence in examples.md Example 3; retained from the
  original source list, not re-verified in this pass).
