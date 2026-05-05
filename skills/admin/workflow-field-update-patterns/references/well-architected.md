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
   with cross-dependency.** Order between them is not guaranteed.

## Official Sources Used

- Triggers and Order of Execution — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm
- Before-Save Updates in Record-Triggered Flows — https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_before_save.htm&type=5
- Migrate to Flow Tool — https://help.salesforce.com/s/articleView?id=sf.workflow_migration_tool.htm&type=5
- Workflow Rule Field Update Deprecation — https://help.salesforce.com/s/articleView?id=000392547&type=1
- Formula Field reference — https://help.salesforce.com/s/articleView?id=sf.fields_about_formula_fields.htm&type=5
- Sibling skill — `skills/admin/order-of-execution/SKILL.md` (when one exists)
- Sibling skill — `skills/flow/flow-best-practices/SKILL.md`
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
