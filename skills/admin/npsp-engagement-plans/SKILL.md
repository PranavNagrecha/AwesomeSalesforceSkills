---
name: npsp-engagement-plans
description: "Use this skill when configuring, applying, or troubleshooting NPSP Engagement Plans — the framework that automatically generates standard Salesforce Task records on a timed schedule to guide donor stewardship and constituent outreach. Trigger keywords: engagement plan, donor stewardship tasks, NPSP task automation, engagement template, major donor follow-up. NOT for marketing automation, email campaigns, or Flow-based automation."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "How do I set up automatic follow-up tasks for major donors in NPSP?"
  - "Engagement plan tasks are not being created when I apply a template to a Contact"
  - "I want to deploy engagement plan templates to production using a Change Set"
tags:
  - npsp
  - engagement-plans
  - donor-stewardship
  - tasks
  - nonprofit
  - templates
inputs:
  - Target object (Account, Contact, Opportunity, Campaign, Case, or Recurring Donation)
  - Stewardship or outreach cadence (days between tasks, task subjects, assigned-to user or queue)
  - Org NPSP version and whether custom objects need engagement plan support
outputs:
  - Configured npsp__Engagement_Plan_Template__c record with child npsp__Engagement_Plan_Task__c records
  - Applied npsp__Engagement_Plan__c instance linked to the target record
  - Standard Salesforce Task records created from the template on the correct due dates
  - Decision guidance on pairing Engagement Plans with Flow for non-Task actions
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# NPSP Engagement Plans

This skill activates when a practitioner needs to design, configure, or troubleshoot the NPSP Engagement Plans feature — a structured way to automatically generate Salesforce Task records on a timed schedule tied to a target record (Contact, Account, Opportunity, Campaign, Case, or Recurring Donation). It covers the three-object data model, template deployment constraints, retroactivity rules, child task due-date behavior, and when to layer Flow on top for actions beyond Task creation.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm NPSP is installed and the org has the three Engagement Plan objects visible: `npsp__Engagement_Plan_Template__c`, `npsp__Engagement_Plan__c`, and `npsp__Engagement_Plan_Task__c`.
- Identify the target object. Standard supported objects (Account, Contact, Opportunity, Campaign, Case, Recurring Donation) work out of the box. Custom objects require Activities enabled on the custom object and a lookup field added to `npsp__Engagement_Plan__c`.
- Establish whether templates need to move between sandboxes and production — they are stored as data records, not metadata, so Change Sets cannot carry them.
- Clarify whether users need non-Task actions (emails, field updates, Chatter posts) as part of the cadence; those require a separate Flow triggered on the same record.

---

## Core Concepts

### Three-Object Data Model

NPSP Engagement Plans use three sObjects:

1. **`npsp__Engagement_Plan_Template__c`** — The master template. Contains configuration such as name, description, skip weekends flag, and which object type it targets. This is what admins build and manage.
2. **`npsp__Engagement_Plan__c`** — The instance created when a template is applied to a specific record. It acts as the junction between the template and the target record (Contact, Opportunity, etc.) and holds the applied-on date from which task due dates are calculated.
3. **`npsp__Engagement_Plan_Task__c`** — Individual task definitions within a template (subject, days offset, dependent parent task, assigned-to user). When the plan is applied, NPSP creates one standard Salesforce `Task` record per `npsp__Engagement_Plan_Task__c`.

Engagement Plans create standard `Task` records only. They do not send emails, update fields, post to Chatter, or trigger other automation by themselves.

### Templates Are Data, Not Metadata

Engagement Plan Templates are stored as standard data records in `npsp__Engagement_Plan_Template__c`, not as Salesforce metadata components. This means:

- Change Sets, Metadata API deployments, and Salesforce CLI packages cannot include them.
- Moving templates between sandboxes and production requires manual recreation or a data migration tool (e.g., Data Loader, Dataloader.io, or a custom script using the Salesforce REST API).
- Version control of template definitions must be handled outside the standard deployment pipeline — document templates in a spreadsheet, wiki, or a custom export script.

### Template Changes Are Not Retroactive

Editing a template (adding tasks, changing offsets, renaming subjects) has no effect on Engagement Plan instances that have already been applied. Existing `npsp__Engagement_Plan__c` and `npsp__Engagement_Plan_Task__c` records, and the Tasks already created from them, are frozen at the state of the template at the time of application. To roll out a revised template to existing records, you must delete the old plan instance and reapply the updated template.

### Auto-Update Child Due Date Behavior

When a task hierarchy is configured (one `npsp__Engagement_Plan_Task__c` depends on a parent task), NPSP can recalculate child task due dates relative to the parent. This recalculation fires only when the parent Task record is marked **Complete** (Status = "Completed"). It does NOT fire when the parent task's due date is manually edited. Practitioners who drag a parent task's due date in the calendar and expect child tasks to shift are surprised when nothing moves.

---

## Common Patterns

### Major Donor Stewardship Cadence

**When to use:** A fundraising team wants every new major donor (Opportunity stage = Closed Won above a threshold) to receive a consistent 30/60/90-day stewardship task sequence.

**How it works:**
1. Build a template with three `npsp__Engagement_Plan_Task__c` records: Day 30 thank-you call, Day 60 impact report delivery, Day 90 cultivation meeting.
2. Create a Flow (Record-Triggered, after-save) on Opportunity that fires when Amount ≥ threshold and Stage = "Closed Won". The Flow applies the engagement plan by creating an `npsp__Engagement_Plan__c` record with a lookup to the Opportunity and the template.
3. NPSP generates the three Task records with due dates calculated from the plan's creation date.

**Why not the alternative:** Manually creating tasks per donor per close is error-prone, inconsistent, and not auditable at the template level. Engagement Plans enforce the same sequence every time.

### Extending to Non-Task Actions with Flow

**When to use:** The stewardship cadence requires an automated email send or a field update in addition to creating Tasks.

**How it works:**
1. Build the Engagement Plan template for the Task creation part of the cadence.
2. Build a separate scheduled-path Flow (or a Process Builder replacement using Flow) that fires on the same record and same timing offset to handle the non-Task action (e.g., send an email alert, stamp a "Last Outreach Date" field).
3. The two automations run independently but together cover the full cadence.

**Why not the alternative:** Practitioners sometimes expect Engagement Plans to handle email sends directly. They do not — attempting to add email logic to the NPSP template configuration will fail silently or produce no result.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need timed Task reminders for donor stewardship | Engagement Plan Template | Native NPSP feature; auditable; no code |
| Need to deploy templates to production | Manual data migration or Data Loader | Templates are data records, not metadata |
| Need to update all in-flight plans after template change | Delete existing plan instances, reapply updated template | Changes are not retroactive |
| Need email sends as part of the cadence | Add a scheduled Flow alongside the engagement plan | Engagement Plans produce Tasks only |
| Need engagement plans on a custom object | Enable Activities on the object; add lookup to npsp__Engagement_Plan__c | Required to associate plans with custom records |
| Child tasks not shifting when parent date changes | Mark parent Task Complete to trigger recalculation | Auto-Update fires on Complete, not date edit |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify prerequisites** — Confirm NPSP is installed, the three Engagement Plan objects are present, and the target object has Activities enabled. For custom objects, add the lookup field to `npsp__Engagement_Plan__c` before proceeding.
2. **Design the template** — Define the task sequence: subject lines, days offset from plan application date, assigned-to user or queue, and any parent-child dependencies. Document the design in the work template before building to avoid schema errors.
3. **Build the template in the target org** — Navigate to NPSP Settings > Engagement Plans (or use the Engagement Plan Templates tab) to create the `npsp__Engagement_Plan_Template__c` record and its child `npsp__Engagement_Plan_Task__c` records. If this is a sandbox, plan for manual recreation or Data Loader migration to production.
4. **Apply and verify** — Apply the template to a test record (manually or via Flow). Confirm that one standard `Task` record is created per engagement plan task, due dates are correct, and the `npsp__Engagement_Plan__c` instance links correctly to the target record.
5. **Validate edge cases** — Test the Auto-Update Child Due Date feature by marking the parent Task Complete and confirming child task due dates recalculate. Confirm that editing the parent task's due date directly does NOT shift children. Document and communicate this behavior to the team.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Template `npsp__Engagement_Plan_Template__c` record created with correct name and target object
- [ ] All `npsp__Engagement_Plan_Task__c` records have accurate subjects, day offsets, and assignees
- [ ] Plan applied to a test record; correct number of Task records created with correct due dates
- [ ] Template migration plan documented (manual recreation or Data Loader) for production deployment
- [ ] Team informed that template changes do not update existing in-flight plan instances
- [ ] Auto-Update Child Due Date behavior tested and communicated (fires on Complete, not date edit)
- [ ] Non-Task actions (emails, field updates) handled via a separate Flow, not within the Engagement Plan

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Templates Cannot Be Deployed via Change Set** — Because `npsp__Engagement_Plan_Template__c` records are data, not metadata components, they are invisible to Change Sets and the Metadata API. Admins who build templates in sandbox and then run a Change Set to production will find the templates missing. The fix is manual recreation in each org or a Data Loader export/import.
2. **Template Edits Have No Effect on Active Plans** — Modifying a template after it has been applied to records does not update those plan instances or regenerate tasks. The only way to apply changes to existing records is to delete the `npsp__Engagement_Plan__c` instance and reapply the updated template, which may regenerate already-completed tasks if not filtered.
3. **Auto-Update Child Due Date Requires Task Completion, Not Date Edit** — The child task due-date cascade runs when the parent Task Status is set to "Completed". Manually editing the parent task's due date field does not trigger any recalculation. This is a common source of confusion when coordinators reschedule tasks by hand.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `npsp__Engagement_Plan_Template__c` record | Master template defining the task cadence; must be manually migrated between orgs |
| `npsp__Engagement_Plan_Task__c` records | Child task definitions within the template; one per planned task |
| `npsp__Engagement_Plan__c` instance | Applied plan record linking the template to a specific target record |
| Standard `Task` records | The actual activity records created for users to act on; one per engagement plan task |
| Flow (optional) | Separate automation for non-Task actions (emails, field updates) triggered on the same record |

---

## Related Skills

- `npsp-custom-rollups` — Use when engagement plan completion milestones need to roll up to summary fields on Donor or Account records
- `npsp-trigger-framework-extension` — Use when engagement plan application needs custom Apex logic beyond what native NPSP supports
- `fsc-action-plans` — Parallel concept in Financial Services Cloud; useful for comparing template-based task automation patterns across Salesforce products
