# Well-Architected Notes — FSC Action Plans

## Relevant Pillars

- **Reliability** — Action Plan templates provide a consistent, repeatable task sequence for every execution of a client-facing process. Versioning via clone-and-republish ensures that in-flight plans are never disrupted by template changes, preserving plan integrity throughout the process lifecycle. Required-task enforcement prevents premature plan closure.

- **Operational Excellence** — Centralized template management means changes to onboarding or compliance workflows are made once in the template rather than across hundreds of manually created tasks. The ActionPlan object provides a unified reporting surface for tracking process completion across the book of business.

- **Security** — Task assignment via queues rather than individual user records ensures that no task is permanently blocked by user deactivation. Field-level security on ActionPlanTemplate and ActionPlanItem governs who can view, modify, or complete task items. Access to the "Manage Action Plans" permission should be scoped to admins and process owners.

- **Performance** — Action Plan launches create one ActionPlanItem record per template task. For templates approaching the 75-task limit, consider the DML and record creation volume at plan launch, especially if plans are launched in bulk via automation. Bulk plan launches should be processed asynchronously to avoid exceeding governor limits.

- **Scalability** — Templates enable consistent process execution at scale without proportional admin overhead. The 75-task-per-plan hard limit is the primary scaling constraint; multi-phase template design addresses this for complex workflows. Report performance on the ActionPlan and ActionPlanItem objects should be monitored as plan volume grows into the tens of thousands.

## Architectural Tradeoffs

**Template versioning vs. single living template:** Salesforce's immutability model for published templates forces a clone-and-publish versioning workflow. This prevents in-flight plan corruption but means the org accumulates multiple template versions over time. Teams must decide how long to retain prior versions (until all in-flight plans are closed) versus archiving or deactivating older templates. A governance process for template lifecycle management is required at scale.

**Action Plans vs. Flow-created Tasks:** Action Plan templates provide out-of-box deadline offset calculation, grouped plan visibility, Required-task enforcement, and a single reporting object. Flow-created Tasks are more flexible (can include branching logic, conditional task creation) but require custom reports, lack built-in deadline offset math, and cannot enforce Required-task completion. For structured, repeatable workflows with a fixed task set, Action Plans are the correct architectural choice. For conditional or branching workflows, Flow is more appropriate.

**Queue-based vs. user-based task assignment:** Assigning template tasks to queues rather than individual users provides assignment flexibility at plan launch time, avoids blocking on user deactivation, and supports team-based accountability. The tradeoff is that queue members must self-assign tasks, which requires operational discipline. For workflows where a specific named individual must complete each task (audit trail requirement), user-based assignment is necessary but introduces fragility.

## Anti-Patterns

1. **Editing a published template directly** — Attempting to modify an Active ActionPlanTemplate or its items to fix a process without creating a new version. This is blocked by the platform but practitioners unfamiliar with FSC Action Plans try it repeatedly. The correct pattern is always clone-and-republish. Direct editing leaves the process in a broken state during the failed edit attempt.

2. **Assuming new template versions update in-flight plans** — Believing that publishing an updated template automatically applies changes to all open plan instances. This leads to compliance gaps where advisors think clients' open plans have the new regulatory task list when they are actually still running against the old one. The correct pattern is to accept version binding and either complete plans before versioning or explicitly migrate open plans.

3. **Building all process steps into a single 75-task template** — Attempting to model an entire complex onboarding lifecycle in one template, hitting the 75-task limit, and experiencing plan launch failures. The correct pattern is multi-phase templates with sequential launch automation.

## Official Sources Used

- Action Plans in Financial Services Cloud (FSC Admin Guide) — https://help.salesforce.com/s/articleView?id=sf.fsc_admin_action_plans.htm
- ActionPlanTemplate Object Reference (Salesforce Platform) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_actionplantemplate.htm
- ActionPlan Object Reference (Salesforce Platform) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_actionplan.htm
- ActionPlanTemplateItem Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_actionplantemplateitem.htm
- Financial Services Cloud Administrator Guide — https://help.salesforce.com/s/articleView?id=sf.fsc_admin.htm
- Salesforce Well-Architected: Reliable Pillar — https://architect.salesforce.com/docs/architect/well-architected/reliable/overview.html
- Salesforce Well-Architected: Operational Excellence Pillar — https://architect.salesforce.com/docs/architect/well-architected/efficient/overview.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
