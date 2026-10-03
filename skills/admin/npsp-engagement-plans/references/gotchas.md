# Gotchas — NPSP Engagement Plans

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

Source key used below. "NPSP source" means the Salesforce.org NPSP repository on GitHub (`SalesforceFoundation/NPSP`, branch `main`), read on 2026-10-03. File paths are relative to `force-app/main/default/` unless stated otherwise.

## Gotcha 1: Templates Are Data Records, So Change Sets Cannot Deploy Them

**What happens:** Engagement Plan Templates (`npsp__Engagement_Plan_Template__c`) and their child task definitions (`npsp__Engagement_Plan_Task__c`) are stored as data records in the NPSP managed package schema, not as Salesforce metadata components. When an admin builds templates in sandbox and then deploys to production via Change Set or Metadata API, the templates are silently absent from production.

**When it occurs:** Any time a team uses the standard Salesforce deployment pipeline (Change Sets, SFDX, Salesforce CLI) to promote templates from sandbox to production or from one sandbox to another.

**How to avoid:** Treat template migration as a data migration task. Use Data Loader, Dataloader.io, or the Salesforce REST API to export `npsp__Engagement_Plan_Template__c` and `npsp__Engagement_Plan_Task__c` records (with their relationship fields) from the source org and import to the target org. Keep `Parent_Task__c` links intact by loading parent rows first or by using a reference-based import plan (see `references/metadata-examples.md`). Document all templates in a canonical reference spreadsheet that lives in version control so they can be recreated if needed.

**Source:** NPSP source, `objects/Engagement_Plan_Template__c/` and `objects/Engagement_Plan_Task__c/` are custom objects; template rows are records of those objects.

---

## Gotcha 2: Template Edits Do Not Rewrite Existing Tasks

**What happens:** When a template is modified (adding a new task, changing a subject line, adjusting a day offset), the Salesforce Tasks already generated for existing `npsp__Engagement_Plan__c` instances keep the subject, owner, and due date they had at application time.

**When it occurs:** Any time an admin updates a template after it has already been applied to records. Common scenario: a fundraising director requests a subject-line correction or a new stewardship step after the annual campaign has already started.

**How to avoid:** Before editing a widely-applied template, tell the team that existing Tasks will not change. If the changes must apply to existing records, identify the active `npsp__Engagement_Plan__c` instances for that template, delete them, and reapply the updated template. Deleting a plan does not delete its Tasks, because the `Engagement_Plan__c` lookup on Activity uses `SetNull` and NPSP registers no delete handler for plans. The reapply therefore creates a second set of Tasks next to the old ones, including tasks that were already done. Filter or close the duplicates as part of the change.

**Source:** NPSP source, `objects/Activity/fields/Engagement_Plan__c.field-meta.xml` (`deleteConstraint` `SetNull`); `force-app/tdtm/classes/TDTM_DefaultConfig.cls` registers `EP_EngagementPlans_TDTM` for `BeforeInsert;BeforeUpdate;AfterInsert` only.

---

## Gotcha 3: Auto-Update Child Due Date Fires When the Parent Task Closes, Not on a Date Edit

**What happens:** When child `npsp__Engagement_Plan_Task__c` records are configured with a parent dependency and the template's Automatically Update Child Task Due Date box is checked, the child Task due date is recalculated only when the parent Salesforce Task becomes closed. NPSP checks that `IsClosed` changed from false to true, so any Task status flagged as closed counts, not only "Completed". Manually editing the parent Task's ActivityDate, including dragging it in a calendar view, does not trigger any recalculation on child tasks.

**When it occurs:** Whenever a coordinator reschedules a parent task by editing its due date rather than by closing it. The parent moves; the children do not. When the parent is later closed, the direct children get a new due date of the close date plus their own Days After value.

**How to avoid:** Train users that parent task due-date changes only cascade to children when the parent Task is closed. If rescheduling a parent task is needed, users should adjust child tasks by hand while the parent is open. Confirm which Task statuses are flagged as closed in the org, because closing a parent with a status such as "Deferred" also activates its children if that status is marked closed. Document this behavior in end-user training materials.

**Source:** NPSP source, `classes/EP_TaskDependency_TDTM.cls` (after update, `newTask.isClosed && !oldTask.isClosed`); `classes/EP_Task_UTIL.cls` (`updateActivateTask` recalculates `ActivityDate` only when `Automatically_Update_Child_Task_Due_Date__c` is true).

---

## Gotcha 4: Engagement Plans on Custom Objects Require Explicit Configuration

**What happens:** Out of the box, `npsp__Engagement_Plan__c` has lookups to Account, Campaign, Case, Contact, Opportunity, and Recurring Donation. A custom object cannot be targeted until a lookup to it exists on `npsp__Engagement_Plan__c`.

**When it occurs:** When an org has custom objects for programs, grants, or events and wants engagement plans to drive stewardship on those records.

**How to avoid:** Two steps are required before custom objects can use Engagement Plans: (1) Enable Activities on the custom object in Object Manager > [Custom Object] > Details > Allow Activities, because NPSP writes the target ID into `Task.WhatId`; (2) Add a lookup or master-detail field on `npsp__Engagement_Plan__c` pointing to the custom object. NPSP discovers every custom relationship field on the plan object (other than the template field) at run time, so no extra registration step is needed once the field exists. UNVERIFIED (2026-10-03): the Allow Activities requirement is stated in Salesforce Help; the Object Reference only says `Task.WhatId` can reference custom objects.

**Source:** NPSP source, `objects/Engagement_Plan__c/fields/*.field-meta.xml`; `classes/EP_EngagementPlans_UTIL.cls` (`lookupFieldsToRelationship` collects custom fields with a relationship name); Object Reference for the Salesforce Platform (Spring '26), Task, `WhatId`.

---

## Gotcha 5: Engagement Plans Produce Tasks Only, With One Narrow Email Exception

**What happens:** Practitioners sometimes configure an engagement plan expecting it to send emails to donors, update field values, or post to Chatter as part of the stewardship sequence. NPSP Engagement Plans create standard Salesforce Task records only. The only email in the feature is the Send Email checkbox on a template task, which asks the platform to send the standard task notification to the assigned user when the Task becomes active.

**When it occurs:** When a fundraising or communications team designs a stewardship cadence that includes automated touchpoints beyond reminders (for example, "send a thank-you email at Day 7"), or when someone reads "Send Email" as a donor email.

**How to avoid:** Pair the Engagement Plan with a separately configured Salesforce Flow. The Flow handles non-Task actions (email alerts, field updates, Chatter posts) triggered on the same record and timing. Use Send Email only to notify staff that a task is now theirs.

**Source:** NPSP source, `objects/Engagement_Plan_Task__c/fields/Send_Email__c.field-meta.xml` ("an email is sent to the user in the Task's Assigned To field when the Task becomes active"); `classes/EP_EngagementPlans_TDTM.cls` (`options.EmailHeader.triggerUserEmail = true` on the insert).

---

## Gotcha 6: Adding a Task to a Template Leaves Older Plans Stuck at In Progress

**What happens:** The plan's `Status__c` is a formula: Completed when `Completed_Tasks__c` equals `Total_EP_Tasks__c`. `Total_EP_Tasks__c` is itself a formula that reads the template's current `Total_Tasks__c` roll-up count. Add a fourth task to a three-task template and every plan created earlier still has three Tasks, so its completed count can never reach four. Remove a task and older plans can complete more Tasks than the template now counts, which also fails the equality test.

**When it occurs:** Any time the number of `npsp__Engagement_Plan_Task__c` rows on a live template changes. Reports and list views that filter on plan Status then undercount finished stewardship.

**How to avoid:** Treat the task list of a live template as frozen. Clone the template, edit the clone, and point new plans at it. If the template must be edited, report on `Completed_Tasks__c` and `Total_Tasks__c` (the plan's own count of Tasks) instead of `Status__c` for plans created before the change.

**Source:** NPSP source, `objects/Engagement_Plan__c/fields/Status__c.field-meta.xml`, `Total_EP_Tasks__c.field-meta.xml` (`Engagement_Plan_Template__r.Total_Tasks__c`), and `classes/EP_TaskRollup_TDTM.cls`.

---

## Gotcha 7: Dependent Tasks Exist From Day One With Status "Waiting on Dependent Task"

**What happens:** NPSP inserts every Task in the template when the plan is created, including dependent ones. Dependent Tasks get the status `Waiting on Dependent Task`, no reminder, and a provisional due date equal to today plus the sum of Days After values up the chain. Users see them in their task lists immediately. When the parent closes, the child switches to the template task's Status value (or the org default Task status), gets its reminder, and sends the Send Email notification if checked.

**When it occurs:** On every plan whose template uses `Parent_Task__c`. Teams that filter "My Open Tasks" by due date see waiting tasks with dates that are not real yet.

**How to avoid:** Exclude `Status = 'Waiting on Dependent Task'` from coordinator list views and dashboards. Confirm the Task Status picklist and any validation rules on Task accept that value before go-live, because the insert writes it directly. UNVERIFIED (2026-10-03): whether NPSP installation adds this value to the Task Status picklist was not confirmed from the source.

**Source:** NPSP source, `classes/EP_EngagementPlans_UTIL.cls` (`TASK_STATUS_WAITING = 'Waiting on Dependent Task'`); `classes/EP_Task_UTIL.cls` (`createTask`, `updateActivateTask`). The field help text on `Engagement_Plan_Task__c.Status__c` says "Waiting on Parent Task", which does not match the constant the code writes.

---

## Gotcha 8: One Failed Task Rolls Back the Whole Plan

**What happens:** NPSP creates the plan's Tasks with `Database.insert` and `OptAllOrNone = true` inside the plan's after-insert trigger. If any one Task fails (a Task validation rule, a required custom field, an owner that cannot own Tasks), the exception rolls back the plan insert. Nothing is created.

**When it occurs:** When a Flow or data load applies plans in bulk and one template row assigns a Task to a user who cannot receive it, or when a Task validation rule was added after the template was designed.

**How to avoid:** Apply each template once to a test record after every Task validation rule change. Give every Flow that creates `npsp__Engagement_Plan__c` a fault path that logs the error and notifies an admin. Keep `Assigned_To__c` values pointed at active users and review them when staff leave.

**Source:** NPSP source, `classes/EP_EngagementPlans_TDTM.cls` (`options.OptAllOrNone = true`).

---

## Gotcha 9: A Plan Must Have Exactly One Target, and It Cannot Be Moved

**What happens:** The plan's before-insert trigger raises an error when no target lookup is populated or when two are populated. Its before-update trigger rejects a change of the target lookup after the plan exists.

**When it occurs:** When a Flow sets both `npsp__Contact__c` and `npsp__Opportunity__c` "for reporting", when an import maps an Account and a Contact on the same row, or when a user tries to reassign a plan to a merged duplicate.

**How to avoid:** Populate one lookup per plan. Report across objects through the target record instead of through a second lookup. To move a plan, delete it and apply the template to the new record.

**Source:** NPSP source, `classes/EP_EngagementPlans_UTIL.cls` (`getTargetObjectField` adds `engagementPlanTwoLookups` or `engagementPlanNoLookups`); `classes/EP_EngagementPlans_TDTM.cls` (`engagementPlanCantEdit` on update).

---

## Gotcha 10: Blank Assignees and Weekend Dates Follow Template Defaults

**What happens:** A template task with a blank Assigned To is owned by the template's Default Assignee: the owner of the target record, or the user who created the plan. When a Flow running as an automated user applies the plan, "User Creating Engagement Plan" assigns every blank task to that automation user. Separately, Skip Weekends defaults to true, so a Saturday due date moves to Monday unless Reschedule To says Friday.

**When it occurs:** On any template that leaves Assigned To blank or that keeps the defaults without review.

**How to avoid:** Set Default Assignee to "Owner of Object for Engagement Plan" for templates applied by automation. Record a Skip Weekends and Reschedule To decision on every template. Test with a plan created on a Friday so the weekend shift is visible.

**Source:** NPSP source, `objects/Engagement_Plan_Template__c/fields/Default_Assignee__c.field-meta.xml`, `Skip_Weekends__c.field-meta.xml` (`defaultValue` true), `Reschedule_To__c.field-meta.xml`; `classes/EP_EngagementPlans_TDTM.cls` (owner fallback); `classes/EP_Task_UTIL.cls` (`skipWeekend`).
