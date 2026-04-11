# LLM Anti-Patterns — NPSP Engagement Plans

Common mistakes AI coding assistants make when generating or advising on NPSP Engagement Plans.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating Engagement Plans as General Automation (Expecting Email or Field Update Capability)

**What the LLM generates:** Instructions like "configure the Engagement Plan to send a thank-you email on Day 7" or "set the Engagement Plan task to update the Donor Stage field when completed."

**Why it happens:** LLMs conflate NPSP Engagement Plans with general workflow automation because the term "engagement" implies broad constituent interaction. Training data may mix Engagement Plans with Marketing Cloud Journeys or Pardot programs that do support email sends.

**Correct pattern:**

```
Engagement Plans create standard Salesforce Task records only.
For email sends, field updates, or Chatter posts as part of the cadence:
  - Build a separate Record-Triggered Flow on the same object
  - Trigger the Flow on the same conditions that apply the Engagement Plan
  - Use Email Alert actions, Update Records actions, or Post to Chatter actions in the Flow
The Engagement Plan and the Flow run independently but together form a complete stewardship cadence.
```

**Detection hint:** Flag any instruction that tells a user to configure an Engagement Plan (or `npsp__Engagement_Plan_Task__c`) to perform an action other than creating a Task — especially "send email," "update field," or "post to Chatter."

---

## Anti-Pattern 2: Advising Change Set or Metadata API Deployment of Templates

**What the LLM generates:** "To deploy your Engagement Plan templates to production, add them to a Change Set under Custom Objects or Custom Settings and deploy as part of your release."

**Why it happens:** LLMs default to the standard Salesforce deployment pipeline because it handles most org configuration. They do not distinguish between metadata components and data records stored in managed-package sObjects.

**Correct pattern:**

```
Engagement Plan Templates are data records in npsp__Engagement_Plan_Template__c.
They are NOT metadata components.
Change Sets and Metadata API deployments will NOT include them.

To migrate templates between orgs:
  1. Export from source org using Data Loader:
     - Object: npsp__Engagement_Plan_Template__c
     - Object: npsp__Engagement_Plan_Task__c (with npsp__Engagement_Plan_Template__c lookup)
  2. Strip environment-specific IDs from the export
  3. Import to target org using Data Loader upsert on external ID or Name
  Alternatively: manually recreate templates in the target org using a documented reference sheet.
```

**Detection hint:** Flag any suggestion to include `npsp__Engagement_Plan_Template__c` in a Change Set, `package.xml`, or SFDX source push/pull operation.

---

## Anti-Pattern 3: Expecting Template Edits to Update In-Flight Plan Instances

**What the LLM generates:** "Update the Engagement Plan Template with the new 45-day task and all existing engagement plans will automatically reflect the change."

**Why it happens:** LLMs familiar with metadata-driven configuration (e.g., page layouts, validation rules) expect that editing a template propagates to all instances. NPSP Engagement Plan instances are data records frozen at the time of application — they do not have a live reference to the template.

**Correct pattern:**

```
Template changes have NO effect on existing npsp__Engagement_Plan__c instances.
To apply a template change to records that already have a plan:
  1. Identify all active npsp__Engagement_Plan__c records using the old template version
     (SOQL: SELECT Id, npsp__Account__c FROM npsp__Engagement_Plan__c
            WHERE npsp__Engagement_Plan_Template__c = '<template_id>')
  2. Delete the existing plan instances (this does NOT delete already-created Tasks)
  3. Reapply the updated template to those records
  4. Review any Tasks that were already created and determine if they need adjustment
```

**Detection hint:** Flag any claim that modifying a template automatically updates existing plans, existing tasks, or in-progress stewardship sequences.

---

## Anti-Pattern 4: Assuming Child Due Dates Recalculate When Parent Due Date Is Edited

**What the LLM generates:** "To reschedule child tasks, simply update the parent task's due date and NPSP will automatically adjust all dependent child tasks."

**Why it happens:** LLMs infer that "Auto-Update Child Due Date" means due-date changes cascade on any modification to the parent task. The actual trigger is narrower: parent Task completion (Status = "Completed").

**Correct pattern:**

```
Auto-Update Child Due Date in NPSP Engagement Plans fires ONLY when:
  - The parent Salesforce Task Status is set to "Completed"

It does NOT fire when:
  - The parent Task's ActivityDate (due date) is manually edited
  - The parent Task is rescheduled via calendar drag-and-drop
  - Any other field on the parent Task is updated

To shift child task due dates:
  Option A: Mark the parent Task Complete (if appropriate) — children recalculate from completion date
  Option B: Manually update child Task due dates directly
  Option C: Delete the plan instance and reapply the template (resets all tasks)
```

**Detection hint:** Flag any statement that parent task due-date edits will propagate to child tasks, or any instruction to "update the parent due date to reschedule children."

---

## Anti-Pattern 5: Omitting the Custom Object Configuration Steps

**What the LLM generates:** "You can apply Engagement Plans to any object in your org by selecting it when creating the template."

**Why it happens:** LLMs generalize from the list of standard supported objects (Account, Contact, Opportunity, Campaign, Case, Recurring Donation) without noting that custom objects require explicit configuration steps before they become eligible targets.

**Correct pattern:**

```
Engagement Plans support custom objects only after TWO setup steps:

Step 1: Enable Activities on the custom object
  Setup > Object Manager > [Custom Object] > Details > Edit
  Check: "Allow Activities" checkbox
  Save

Step 2: Add a lookup field to npsp__Engagement_Plan__c
  Setup > Object Manager > npsp__Engagement_Plan__c > Fields & Relationships > New
  Field Type: Lookup Relationship
  Related To: [Custom Object]
  Field Label: [Custom Object Name]
  Save

Only after both steps is the custom object available as an Engagement Plan target.
```

**Detection hint:** Flag any response that says Engagement Plans work "on any object" or that custom objects can be targeted without additional setup. Also flag responses that omit the lookup field requirement on `npsp__Engagement_Plan__c`.

---

## Anti-Pattern 6: Conflating NPSP Engagement Plans with FSC Action Plans

**What the LLM generates:** Advice that mixes `ActionPlan`, `ActionPlanTemplate`, and `ActionPlanTemplateItem` (FSC) objects with `npsp__Engagement_Plan__c`, `npsp__Engagement_Plan_Template__c`, and `npsp__Engagement_Plan_Task__c` (NPSP).

**Why it happens:** Both features use the phrase "plan" and "template" and both create Tasks. LLMs trained on FSC Action Plans documentation apply that knowledge to NPSP contexts, or vice versa.

**Correct pattern:**

```
NPSP Engagement Plans:
  - Objects: npsp__Engagement_Plan_Template__c, npsp__Engagement_Plan__c, npsp__Engagement_Plan_Task__c
  - Package: Nonprofit Success Pack (NPSP) managed package
  - Task generation: synchronous on npsp__Engagement_Plan__c insert
  - Deployment: data migration only

FSC Action Plans:
  - Objects: ActionPlanTemplate, ActionPlan, ActionPlanTemplateItem (standard Salesforce objects)
  - Package: Financial Services Cloud (FSC)
  - Task generation: platform-native
  - Deployment: can be included in metadata deployments as standard objects

These are separate features. Do not apply FSC Action Plan guidance to NPSP Engagement Plans.
```

**Detection hint:** Flag any response that uses `ActionPlanTemplate` or `ActionPlan` API names when the context is NPSP. Also flag FSC-specific configuration steps (e.g., Action Plan Lightning Component) being suggested for NPSP orgs.
