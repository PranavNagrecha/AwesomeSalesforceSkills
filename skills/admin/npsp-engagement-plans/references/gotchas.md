# Gotchas — NPSP Engagement Plans

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Templates Are Data Records — Change Sets Cannot Deploy Them

**What happens:** Engagement Plan Templates (`npsp__Engagement_Plan_Template__c`) and their child task definitions (`npsp__Engagement_Plan_Task__c`) are stored as data records in the NPSP managed package schema, not as Salesforce metadata components. When an admin builds templates in sandbox and then deploys to production via Change Set or Metadata API, the templates are silently absent from production.

**When it occurs:** Any time a team uses the standard Salesforce deployment pipeline (Change Sets, SFDX, Salesforce CLI) to promote templates from sandbox to production or from one sandbox to another.

**How to avoid:** Treat template migration as a data migration task. Use Data Loader, Dataloader.io, or the Salesforce REST API to export `npsp__Engagement_Plan_Template__c` and `npsp__Engagement_Plan_Task__c` records (with their relationship fields) from the source org and import to the target org. Document all templates in a canonical reference spreadsheet that lives in version control so they can be recreated if needed.

---

## Gotcha 2: Template Edits Are Not Retroactive to Existing Plan Instances

**What happens:** When a template is modified — adding a new task, changing a subject line, adjusting a day offset — none of the existing `npsp__Engagement_Plan__c` instances that were already applied to records are updated. The `npsp__Engagement_Plan_Task__c` records associated with those instances, and the Salesforce Tasks already generated from them, remain exactly as they were at the time of application.

**When it occurs:** Any time an admin updates a template after it has already been applied to records. Common scenario: a fundraising director requests a subject-line correction or a new stewardship step after the annual campaign has already started.

**How to avoid:** Before editing a widely-applied template, communicate to the team that existing in-flight plans will not change. If the changes must apply to existing records, identify all active `npsp__Engagement_Plan__c` instances for that template, delete them (which does not delete already-created Tasks), and reapply the updated template. Be aware this will regenerate Tasks including ones that may already be complete — filter or manage accordingly.

---

## Gotcha 3: Auto-Update Child Due Date Fires on Task Completion, Not Date Edit

**What happens:** When child `npsp__Engagement_Plan_Task__c` records are configured with a parent dependency and the "Auto-Update Child Due Date" setting is active, the child Task due-date recalculation only fires when the parent Salesforce Task is set to Status = "Completed." Manually editing the parent Task's ActivityDate (due date) field — including dragging it in a calendar view or typing a new date — does not trigger any recalculation on child tasks.

**When it occurs:** Occurs whenever a coordinator reschedules a parent task by editing its due date rather than by completing it. The parent moves; the children do not. If the parent is then completed on the new date, children recalculate from that completion date — but only if the completion happens after the manual date edit.

**How to avoid:** Train users that parent task due-date changes only cascade to children upon parent Task completion. If rescheduling a parent task is needed, users should use the date edit (for their own awareness) but understand that child tasks must be manually adjusted if the parent is not yet complete. Document this behavior in end-user training materials and the onboarding guide for development coordinators.

---

## Gotcha 4: Engagement Plans on Custom Objects Require Explicit Configuration

**What happens:** Out of the box, Engagement Plans can be applied to Account, Contact, Opportunity, Campaign, Case, and Recurring Donation. Attempting to apply a plan to a custom object without additional setup results in the custom object not appearing as a target option and no relationship field available on `npsp__Engagement_Plan__c`.

**When it occurs:** When an org has custom objects for programs, grants, or events and wants engagement plans to drive stewardship on those records.

**How to avoid:** Two steps are required before custom objects can use Engagement Plans: (1) Enable Activities on the custom object in Object Manager > [Custom Object] > Details > Allow Activities; (2) Add a lookup or master-detail field on `npsp__Engagement_Plan__c` pointing to the custom object. Once both steps are complete, the custom object can be selected when applying a template.

---

## Gotcha 5: Engagement Plans Produce Tasks Only — Non-Task Actions Require a Separate Flow

**What happens:** Practitioners sometimes configure an engagement plan expecting it to send emails, update field values, or post to Chatter as part of the stewardship sequence. NPSP Engagement Plans create standard Salesforce Task records only. There is no native mechanism in the Engagement Plan feature to trigger email sends, field updates, or other non-Task automation.

**When it occurs:** When a fundraising or communications team designs a stewardship cadence that includes automated touchpoints beyond reminders (e.g., "send a thank-you email at Day 7").

**How to avoid:** Pair the Engagement Plan with a separately configured Salesforce Flow. The Flow handles non-Task actions (email alerts via Email Action, field updates, Chatter posts) triggered on the same record and timing. The two automations complement each other: the Engagement Plan owns Task creation; the Flow owns everything else.
