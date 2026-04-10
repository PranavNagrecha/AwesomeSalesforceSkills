# Gotchas — FSC Action Plans

Non-obvious Salesforce FSC platform behaviors that cause real production problems.

## Gotcha 1: Published Templates Are Immutable — Edits Require Clone-and-Republish

**What happens:** Once an `ActionPlanTemplate` Status is set to `Active`, the template record and all of its `ActionPlanTemplateItem` child records are locked by the platform. Any attempt to edit an item (change subject, DaysFromStart, AssignedTo, priority, or Required flag) returns a validation error in the UI and a DML error via the API. This is not a permission issue — it is enforced by Salesforce regardless of the user's profile.

**When it occurs:** Any time an admin or developer tries to update an existing published template to reflect a task change, deadline update, or assignment change. Also occurs if a developer tries to bulk-update template items via Data Loader or a script targeting ActionPlanTemplateItem records on an Active template.

**How to avoid:** Treat published templates as immutable artifacts from day one. Adopt a naming and versioning convention (e.g., `[Use Case] v[N]`). When a change is required, clone the active template, edit the Draft clone, publish the clone under the new version name, and communicate the change to plan launchers. Never delete the old version until all plans bound to it are closed.

---

## Gotcha 2: In-Flight Action Plans Are Never Retroactively Updated by a New Template Version

**What happens:** When a new version of an ActionPlanTemplate is published (via clone-and-republish), all previously launched ActionPlan instances continue to run against the original template's task list. No tasks are added, removed, or recalculated on in-progress plans. Admins who expect the new version to "push" updates to open plans are surprised to find open plans still showing outdated tasks.

**When it occurs:** After publishing a new template version when the old version has active plan instances (Status != Completed or Cancelled). Common in compliance-driven workflows where regulatory changes require updating the review checklist mid-cycle.

**How to avoid:** Accept that in-flight plans are permanently bound to their launch-time template version. If a regulatory change is critical enough that open plans must reflect new tasks, the only option is to close or cancel existing plans and relaunch from the new template — a deliberate data migration decision, not an automatic platform capability.

---

## Gotcha 3: FSC-Specific TargetEntityType Values Are Only Available With FSC License Active

**What happens:** The `TargetEntityType` picklist on ActionPlanTemplate does not display FSC-specific object types (FinancialAccount, FinancialGoal, InsurancePolicy, ResidentialLoanApplication, PersonLifeEvent, BusinessMilestone) unless the Financial Services Cloud feature is active in the org. In sandbox refreshes, developer orgs, or partial scratch org configurations without FSC enabled, only the standard object types (Account, Contact, Opportunity, Lead, Contract, Case, Campaign) appear.

**When it occurs:** During sandbox testing, scratch org setup, or partial deployment to orgs that have Action Plans enabled but FSC disabled. Also occurs in orgs where the FSC managed package was uninstalled.

**How to avoid:** Before designing templates for FSC objects, verify FSC is enabled in Setup and the org license includes FSC. When provisioning sandboxes or scratch orgs for FSC Action Plan development, include FSC feature flags in the scratch org definition file or sandbox template. Validate the full picklist on ActionPlanTemplate early in the configuration process.

---

## Gotcha 4: BusinessDays Deadline Mode Skips Weekends Only — Not Org Holidays

**What happens:** When `TaskDeadlineType = BusinessDays`, Salesforce computes task due dates by skipping Saturdays and Sundays from the plan start date. However, it does not automatically skip public holidays configured in the org's holiday records (Setup > Business Hours > Holidays). A plan starting on the Thursday before a public holiday Friday will compute a 1-business-day task as due on Friday (the holiday), not the following Monday.

**When it occurs:** Any time a plan is launched with a start date adjacent to a holiday, or when the firm's definition of "business day" includes holiday exclusions as a regulatory or operational requirement.

**How to avoid:** For compliance-critical deadlines that must exclude holidays, either: (a) use Calendar deadline mode and manually account for holidays in DaysFromStart, (b) build post-launch automation that adjusts task due dates when they fall on holiday records, or (c) communicate to plan launchers to adjust the plan start date when launching near holidays to avoid the gap.

---

## Gotcha 5: 75-Task Hard Limit Per Action Plan Cannot Be Extended

**What happens:** Each ActionPlan instance supports a maximum of 75 ActionPlanItem child records. If an ActionPlanTemplate has more than 75 ActionPlanTemplateItem records and a plan is launched from it, the launch fails with an error. There is no configuration, permission, or governor-limit exception to raise this limit.

**When it occurs:** Complex onboarding workflows for high-net-worth or institutional clients, mortgage origination checklists, or multi-phase compliance reviews that attempt to pack all tasks into a single template.

**How to avoid:** Keep templates under 75 tasks. For complex workflows requiring more tasks, split the workflow into sequenced templates (e.g., "Onboarding Phase 1" and "Onboarding Phase 2"). Use Flow or Process Builder to automatically launch the Phase 2 plan when Phase 1 is marked complete. Design Phase 1 tasks to represent the first wave of activities with Phase 2 tasks representing follow-on activities.

---

## Gotcha 6: Required Tasks Block Plan Completion But Do Not Auto-Escalate

**What happens:** ActionPlanTemplateItem records marked Required must have their corresponding ActionPlanItem closed before the parent ActionPlan can be marked Complete. However, the platform does not automatically escalate, reassign, or alert anyone if a Required task is overdue. An action plan can sit incomplete indefinitely if a Required task is never closed, with no built-in notification to managers.

**When it occurs:** Compliance workflows where certain tasks (e.g., "Compliance officer sign-off") are required, but the compliance officer is unavailable, on leave, or the task was not re-assigned after an org user deactivation.

**How to avoid:** Build supplemental monitoring: create a report on ActionPlanItem filtered by Required = True, Status = Open, and ActivityDate < Today to surface overdue required tasks. Use Salesforce Flow or an email alert to notify a manager when a Required task passes its due date without being closed. Assign Required tasks to queues rather than individual users to avoid blocking on user unavailability.
