# Examples — NPSP Engagement Plans

## Example 1: Creating a Major Donor Stewardship Engagement Plan Template (30/60/90-Day Tasks)

**Context:** A nonprofit wants every major gift ($10,000+) closed in NPSP to automatically generate three follow-up Tasks: a thank-you call at 30 days, an impact report delivery at 60 days, and a cultivation meeting at 90 days. The development director should own all three tasks.

**Problem:** Without an Engagement Plan template, gift officers must manually create three Tasks on every closed Opportunity — inconsistently, incompletely, and with no guarantee of timing. There is no auditable record of whether stewardship was initiated.

**Solution:**

Navigate to NPSP Settings > Engagement Plans > Engagement Plan Templates > New.

```
Template: Major Gift Stewardship — 30/60/90
Skip Weekends: true
Description: Applied to Opportunities ≥ $10,000 at Closed Won stage.

Engagement Plan Tasks:
  Task 1:
    Subject:      "Thank-You Call — Major Gift"
    Days After:   30
    Type:         Call
    Priority:     High
    Assigned To:  Development Director (a User; the field is a User lookup, not a queue)
    Parent Task:  (none — independent)

  Task 2:
    Subject:      "Send Impact Report — Major Gift"
    Days After:   60
    Type:         Email
    Priority:     Medium   (picklist values are High, Medium, Low)
    Assigned To:  Development Director
    Parent Task:  (none — independent)

  Task 3:
    Subject:      "Cultivation Meeting — Major Gift"
    Days After:   90
    Type:         Meeting
    Priority:     High
    Assigned To:  Development Director
    Parent Task:  Task 2 (optional — set if meeting should shift when report slips)
```

After saving the template, build a Record-Triggered Flow on Opportunity (after save, entry criteria: Amount >= 10000 AND StageName = "Closed Won") that creates an `npsp__Engagement_Plan__c` record:

```
Object:                      npsp__Engagement_Plan__c
npsp__Engagement_Plan_Template__c: {Template Id}
npsp__Opportunity__c:        {Opportunity.Id}
```

NPSP generates the three Task records automatically with due dates calculated from the `npsp__Engagement_Plan__c` creation date.

**Why it works:** The template enforces a consistent cadence for every qualifying gift. The Flow removes manual application errors. Task 3's optional dependency on Task 2 means the cultivation meeting Task is created at once with status `Waiting on Dependent Task`. When the impact report Task closes, the meeting Task becomes active and, with Automatically Update Child Task Due Date checked, gets a due date 90 days after the close date. Editing Task 2's due date by hand moves nothing.

---

## Example 2: Applying an Engagement Plan to a Campaign and Verifying Tasks Created

**Context:** A nonprofit runs annual giving campaigns and wants a post-campaign stewardship sequence applied to every new Campaign record of Type = "Annual Fund." The sequence is: Day 7 donor acknowledgment list review, Day 14 board thank-you letter coordination, Day 30 retention analysis meeting.

**Problem:** Campaign managers forget to initiate stewardship follow-up after campaigns close. There is no standard prompt or audit trail.

**Solution:**

1. Build the template. Templates have no target-object setting; the Campaign target is chosen later by populating `npsp__Campaign__c` on the plan. Campaign already appears in the Object Reference list of objects that `Task.WhatId` can reference.

```
Template: Annual Fund — Post-Campaign Stewardship

Engagement Plan Tasks:
  Task 1:
    Subject:     "Review Donor Acknowledgment List"
    Days After:  7
    Assigned To: Campaign Manager (user lookup)

  Task 2:
    Subject:     "Coordinate Board Thank-You Letters"
    Days After:  14
    Assigned To: Executive Director

  Task 3:
    Subject:     "Retention Analysis Meeting"
    Days After:  30
    Assigned To: (blank, so the template's Default Assignee decides;
                 Assigned_To__c cannot hold a queue)
```

2. Apply the plan manually (or via Flow) to a Campaign record: open the Campaign, navigate to the Engagement Plans related list, click New, select the template. NPSP creates three Task records.

3. Verify by navigating to the Campaign's Activity timeline or the Open Activities related list. Confirm:
   - Three Tasks are present
   - Subjects match the template definitions
   - Due dates are 7, 14, and 30 days from today's date (the plan application date)
   - Assigned-to users match the template configuration

4. To test retroactivity behavior: edit the template (change Day 7 task subject to "Review Acknowledgment List — UPDATED"). Reload the applied Campaign. The existing Task subject does NOT change — confirming non-retroactivity. New plans applied after the edit will use the updated subject.

**Why it works:** The Engagement Plans related list on Campaign provides a clear audit trail of which template was applied and when. The Activity timeline gives gift officers a consolidated view of all stewardship tasks without navigating multiple records. The retroactivity test confirms the expected platform behavior before go-live, preventing confusion when templates are revised.

---

## Anti-Pattern: Attempting to Deploy Templates via Change Set

**What practitioners do:** Build engagement plan templates in sandbox, add "NPSP Engagement Plan Templates" to a Change Set, and attempt to deploy to production.

**What goes wrong:** Salesforce does not expose `npsp__Engagement_Plan_Template__c` or `npsp__Engagement_Plan_Task__c` records as metadata components. The Change Set will not include them. Production remains empty. Go-live day reveals missing templates with no obvious error message during deployment.

**Correct approach:** Export templates from sandbox using Data Loader (export `npsp__Engagement_Plan_Template__c` and `npsp__Engagement_Plan_Task__c` with relationship fields), strip sandbox-specific IDs, and import to production. Alternatively, document templates in a canonical reference sheet and manually recreate them in production. For teams with many templates, a Python script using the Salesforce REST API can automate the export/import cycle.

---

## Example 3: Deployable Flow That Applies the Template

The deployable artifacts for this skill (the record-triggered Flow that creates the plan, the template data plan, and the `package.xml` member form) are in `references/metadata-examples.md`. The Flow is metadata and moves through a Change Set. The template rows are data and move with `sf data import tree`.

```text
Deploy order:
1. Flow  Apply_Major_Gift_Stewardship_Plan   (metadata: sf project deploy start)
2. Template + template tasks                 (data: sf data import tree --plan)
3. Activate the Flow after step 2 so its Get Records step finds the template by Name.
```
