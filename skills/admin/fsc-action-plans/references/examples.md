# Examples — FSC Action Plans

## Example 1: Client Onboarding Action Plan for FinancialAccount

**Context:** A wealth management firm using Financial Services Cloud opens approximately 200 new accounts per month. Each new FinancialAccount requires a standard onboarding checklist: welcome communication, KYC verification, suitability questionnaire, beneficiary confirmation, and compliance sign-off. Previously these tasks were tracked in a spreadsheet.

**Problem:** Without Action Plan templates, the firm creates Tasks manually on each FinancialAccount record, with inconsistent naming, missing due dates, and no auditable tracking of which accounts have completed all onboarding steps.

**Solution:**

Create an `ActionPlanTemplate` targeting `FinancialAccount` with `TaskDeadlineType = BusinessDays`. Add `ActionPlanTemplateItem` records:

```
Template: Client Onboarding v1
TargetEntityType: FinancialAccount
TaskDeadlineType: BusinessDays
Status: Active

Items:
  1. Subject: "Send welcome letter"          DaysFromStart: 1   AssignedTo: Relationship Manager Queue   Required: true
  2. Subject: "Collect KYC documentation"    DaysFromStart: 3   AssignedTo: Compliance Queue             Required: true
  3. Subject: "Complete suitability form"    DaysFromStart: 5   AssignedTo: Relationship Manager Queue   Required: true
  4. Subject: "Confirm beneficiary info"     DaysFromStart: 7   AssignedTo: Relationship Manager Queue   Required: false
  5. Subject: "Compliance review sign-off"   DaysFromStart: 10  AssignedTo: Compliance Queue             Required: true
```

When a new FinancialAccount is opened, the advisor launches this plan from the Action Plans related list on the account record, setting `StartDate` to today. All five tasks appear as Activity records on the account, each with the correct computed due date and the correct assigned queue.

**Why it works:** The `DaysFromStart` offsets translate into absolute due dates at plan launch time. The Required flag on KYC and compliance sign-off tasks ensures the plan cannot be marked complete until those tasks are closed. Grouping tasks under one ActionPlan record gives managers a single view of onboarding completion across the entire book of business via a report on the `ActionPlan` object.

---

## Example 2: Annual Compliance Review Template — Clone-and-Republish Versioning

**Context:** A financial advisory firm runs annual client reviews required by regulation. The compliance team designs an Action Plan template each year with a specific review checklist. In year 2, the template needs three new tasks added (the regulation changed) and one task removed.

**Problem:** The year-1 template is already published (`Status = Active`) and has been used to launch 150 active review plans across client accounts. An admin attempts to edit the published template directly and receives a Salesforce platform error: the template is locked.

**Solution:**

Follow the clone-and-republish versioning workflow:

```
Step 1: Clone the active template
  - Open "Annual Compliance Review v1" (Status: Active)
  - Use the "Clone" action — Salesforce creates "Annual Compliance Review v1 (1)" with Status: Draft
  - Rename the clone to "Annual Compliance Review v2"

Step 2: Edit the Draft clone
  - Add three new ActionPlanTemplateItem records for the new regulatory tasks
  - Delete the obsolete task item from the draft
  - Verify total item count remains under 75

Step 3: Publish the clone
  - Set Status to Active on "Annual Compliance Review v2"
  - Communicate to advisors that new review plans should use v2

Step 4: Leave v1 intact
  - Do NOT delete or deactivate "Annual Compliance Review v1"
  - The 150 in-progress plans bound to v1 continue against the original task list
  - When all v1 plans are closed, v1 can be archived
```

**Why it works:** In-flight ActionPlan instances are permanently bound to the template version at the time of launch. Salesforce does not backfill new tasks or remove old tasks from running plans when a template changes. The clone-and-republish workflow preserves plan integrity for open reviews while providing the updated checklist for all new plans going forward.

---

## Example 3: Action Plan for ResidentialLoanApplication — Mortgage Origination Tasks

**Context:** A bank using FSC for mortgage origination needs to track the processing checklist for each ResidentialLoanApplication record, including document collection, underwriting steps, appraisal scheduling, and final approval.

**Problem:** The team is trying to set `TargetEntityType = ResidentialLoanApplication` on an ActionPlanTemplate but the value is not appearing in the picklist dropdown. The org has Salesforce and Action Plans enabled but the FSC license has not been activated.

**Solution:**

```
Root Cause: TargetEntityType values for FSC-specific objects 
(FinancialAccount, FinancialGoal, InsurancePolicy, ResidentialLoanApplication,
PersonLifeEvent, BusinessMilestone) only appear when the FSC managed package 
or core FSC license is active in the org.

Fix:
  1. Confirm FSC is enabled in Setup > Financial Services > Settings
  2. Verify the org license includes FSC (check Company Information > Licenses)
  3. After FSC is active, the FSC object types appear in the TargetEntityType picklist
  4. Create the template with TargetEntityType = ResidentialLoanApplication
  5. Add origination items: title search, appraisal order, underwriter review, 
     final approval sign-off — with DaysFromStart offsets appropriate to 
     the loan processing SLA
```

**Why it works:** FSC Action Plan support for its proprietary objects is gated on the FSC feature license, not just the standard Action Plans feature. This is a common environment-setup error that blocks template creation before any configuration can proceed.

---

## Anti-Pattern: Editing a Live Published Template

**What practitioners do:** After a regulatory change, an admin opens the active `ActionPlanTemplate` record and attempts to edit one of the `ActionPlanTemplateItem` records to change the task subject or deadline offset.

**What goes wrong:** The platform returns an error because published (`Active`) templates are immutable. The edit is blocked entirely. If the admin tries to work around this via the API or a data loader update to the ActionPlanTemplateItem record, the platform still rejects the DML operation with a status validation error.

**Correct approach:** Clone the active template to create a Draft copy, apply all changes to the clone, then publish the clone as the new active version. Retain the original active template until all plans launched from it are closed.
