# Well-Architected Notes — NPSP Engagement Plans

## Relevant Pillars

### Operational Excellence

Engagement Plans directly support the Operational Excellence pillar. By encoding stewardship sequences in a reusable template, organizations remove ad-hoc task creation from gift officers' workflows and replace it with a consistently applied, auditable process. The template acts as a documented runbook for donor stewardship: every major gift receives the same sequence, reducing variance and enabling process measurement. Teams can report on plan adherence (how many plans were applied vs. completed) using NPSP's standard reporting on `npsp__Engagement_Plan__c` and related Task records.

The Operational Excellence risk area in this domain is template governance: because templates are data records rather than version-controlled metadata, undocumented template changes can silently alter stewardship behavior. Maintaining an external canonical reference (spreadsheet or wiki) of template definitions mitigates this risk and supports change management.

### Reliability

Reliability applies to the task-generation mechanism. NPSP creates Task records synchronously in the after-insert trigger of `npsp__Engagement_Plan__c`, with an all-or-none insert. If one Task fails (e.g., validation rule on Task, trigger error, governor limit), the plan insert rolls back with it, and a Flow without a fault path hides the reason. Reliable implementations include:

- A post-application verification step (confirm Task count matches expected template tasks)
- Monitoring via a scheduled report that flags `npsp__Engagement_Plan__c` records with zero associated Tasks (indicating a creation failure)
- Error handling in any Flow that creates plan instances (fault paths that notify admins)

The non-retroactivity of template changes is also a reliability concern: in-flight stewardship sequences can drift from current best practice if templates are updated without a retroactive remediation plan.

## Architectural Tradeoffs

**Template granularity vs. maintainability:** Fine-grained templates (one per donor segment, campaign type, and giving level) provide precise cadences but create a large library of templates that must be maintained and migrated individually. Coarser templates with fewer variants are easier to govern but may not fit all stewardship scenarios. The recommended balance: start with 3–5 templates covering the most common cadences; add variants only when a segment's stewardship requirements genuinely differ.

**Native Engagement Plans vs. custom Flow/Apex task creation:** NPSP Engagement Plans are zero-code and produce auditable plan instances. Custom Flow or Apex task creation offers more flexibility (conditional logic, dynamic assignees, non-Task actions) but requires ongoing maintenance and testing. Prefer native Engagement Plans for standard stewardship cadences; use Flow/Apex only when the native feature cannot meet the requirement.

**Plan application via Flow vs. manual:** Automating plan application via Record-Triggered Flow ensures no qualifying records are missed. Manual application gives gift officers control over timing and template selection but relies on human discipline. For high-volume, well-defined triggers (closed gifts above a threshold), automate. For nuanced relationship management where the right template depends on context, manual application may be appropriate.

## Anti-Patterns

1. **Using Engagement Plans as an All-In-One Automation Engine** — Engagement Plans create Tasks only. Attempting to substitute them for email automation, field update workflows, or complex multi-step processes leads to incomplete implementations. Use Engagement Plans for what they are designed for (Task cadences) and pair them with Flow for broader automation needs.

2. **Skipping Template Documentation in Favor of In-Org Config** — Because templates are data records, they have no version history in source control. Orgs that rely solely on the in-org configuration lose the ability to audit changes, recover from accidental edits, or reproduce templates in a new org. Maintain an external canonical record of every template's design as a governance control.

3. **Applying Templates Without a Retroactive Change Policy** — Orgs that lack a policy for handling template updates to in-flight plans accumulate drift between the current template standard and active stewardship sequences. Establish a change management process: when a template is updated, identify active instances, communicate to owners, and decide whether to retroactively reapply.

## Official Sources Used

Read for the 2026-10-03 revision:

- NPSP source, object definitions: https://github.com/SalesforceFoundation/NPSP/tree/main/force-app/main/default/objects (Engagement_Plan__c, Engagement_Plan_Template__c, Engagement_Plan_Task__c, Activity/fields/Engagement_Plan__c and Engagement_Plan_Task__c, Level__c/fields/Engagement_Plan_Template__c). Supports field names, picklist values, defaults, master-detail and SetNull relationships, and the Status formula.
- NPSP source, `EP_EngagementPlans_TDTM.cls`: https://github.com/SalesforceFoundation/NPSP/blob/main/force-app/main/default/classes/EP_EngagementPlans_TDTM.cls. Supports Task creation at plan insert, all-or-none insert, owner fallback, Send Email header, and the target-lookup validations.
- NPSP source, `EP_EngagementPlans_UTIL.cls`: https://github.com/SalesforceFoundation/NPSP/blob/main/force-app/main/default/classes/EP_EngagementPlans_UTIL.cls. Supports the `Waiting on Dependent Task` constant, custom-lookup discovery, and the one-target rule.
- NPSP source, `EP_Task_UTIL.cls`: https://github.com/SalesforceFoundation/NPSP/blob/main/force-app/main/default/classes/EP_Task_UTIL.cls. Supports due-date math, weekend shifting, reminders, and dependent-task activation.
- NPSP source, `EP_TaskDependency_TDTM.cls` and `EP_TaskRollup_TDTM.cls`: https://github.com/SalesforceFoundation/NPSP/tree/main/force-app/main/default/classes. Supports the IsClosed trigger for child recalculation and the plan task counts.
- NPSP source, `TDTM_DefaultConfig.cls`: https://github.com/SalesforceFoundation/NPSP/blob/main/force-app/tdtm/classes/TDTM_DefaultConfig.cls. Supports which trigger events the engagement plan handlers run on.
- Object Reference for the Salesforce Platform (Spring '26), Task `WhatId` and the reference-field rules for WhoId/WhatId: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Metadata API Developer Guide (Spring '26), Flow (`FlowRecordLookup`, `FlowCustomError`) and ActionPlanTemplate: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Salesforce CLI Command Reference, `data import tree` plan ordering: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/sfdx_cli_reference.pdf

Carried from earlier revisions (not re-read on 2026-10-03; help.salesforce.com does not render to a fetcher):

- Configure Engagement Plans — Salesforce Help: https://help.salesforce.com/s/articleView?id=sfdo.NPSP_Engagement_Plans.htm
- Create and Manage Engagement Plans — Salesforce Help: https://help.salesforce.com/s/articleView?id=sfdo.npsp_config_engage_plans.htm
- Engagement Plans and Levels — Trailhead (NPSP module)
- Salesforce Well-Architected: Operational Excellence Pillar — https://architect.salesforce.com/well-architected/operational-excellence
- Salesforce Well-Architected: Reliable Pillar — https://architect.salesforce.com/well-architected/reliable
