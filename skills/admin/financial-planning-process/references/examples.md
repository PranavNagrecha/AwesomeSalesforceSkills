# Examples — Financial Planning Process

## Example 1: Annual Review Action Plan Template for FinancialAccount

**Context:** A wealth management firm using the FSC managed package (FinServ__ namespace) requires a repeatable, trackable annual review workflow. Every managed-account client must go through a seven-step review process each calendar year. Tasks must be assigned to specific queues, and the compliance sign-off task must be required before the plan can be marked complete.

**Problem:** Without an Action Plan template, advisors create ad-hoc tasks inconsistently. There is no portfolio-level visibility into which clients have completed their annual reviews, and no audit trail showing that the compliance sign-off step was completed.

**Solution:**

Configure the ActionPlanTemplate declaratively or via Metadata API:

```xml
<!-- ActionPlanTemplate metadata (Managed-Package FSC org) -->
<ActionPlanTemplate>
    <name>Annual Client Review v1</name>
    <TargetEntityType>FinancialAccount</TargetEntityType>
    <TaskDeadlineType>Calendar</TaskDeadlineType>
    <Description>Standard seven-step annual review workflow for managed accounts.</Description>
    <Status>Active</Status>
</ActionPlanTemplate>

<!-- ActionPlanTemplateItem records (DaysFromStart offsets) -->
<!-- Item 1 -->
<Subject>Pull year-end account statements</Subject>
<DaysFromStart>0</DaysFromStart>
<AssignedTo>Operations Queue</AssignedTo>
<IsRequired>false</IsRequired>

<!-- Item 2 -->
<Subject>Update FinancialGoal ActualValue fields</Subject>
<DaysFromStart>1</DaysFromStart>
<AssignedTo>Advisor</AssignedTo>
<IsRequired>false</IsRequired>

<!-- Item 3 -->
<Subject>Send pre-meeting document request to client</Subject>
<DaysFromStart>2</DaysFromStart>
<AssignedTo>Advisor</AssignedTo>
<IsRequired>false</IsRequired>

<!-- Item 4 -->
<Subject>Conduct risk tolerance reassessment (Discovery Framework)</Subject>
<DaysFromStart>5</DaysFromStart>
<AssignedTo>Advisor</AssignedTo>
<IsRequired>false</IsRequired>

<!-- Item 5 -->
<Subject>Complete advisor review notes and investment recommendation</Subject>
<DaysFromStart>14</DaysFromStart>
<AssignedTo>Advisor</AssignedTo>
<IsRequired>false</IsRequired>

<!-- Item 6 -->
<Subject>Compliance documentation sign-off</Subject>
<DaysFromStart>21</DaysFromStart>
<AssignedTo>Compliance Queue</AssignedTo>
<IsRequired>true</IsRequired>

<!-- Item 7 -->
<Subject>File completed review — update account status</Subject>
<DaysFromStart>28</DaysFromStart>
<AssignedTo>Operations Queue</AssignedTo>
<IsRequired>false</IsRequired>
```

To launch plans in bulk at the start of review season, use a Flow that queries FinancialAccount records with `Review_Due_Date__c = THIS_YEAR` and calls the `createActionPlan` standard invocable action, passing the plan start date and template ID.

**Why it works:** The offset-based deadline structure means every launched plan computes correct absolute due dates from a single start date input. The Required flag on the compliance item enforces that the plan cannot be closed without that critical step. The plan-level report on `ActionPlan` filtered by TemplateId and Status gives portfolio-level review completion visibility.

---

## Example 2: Goal Progress Tracking with At-Risk Alert

**Context:** A regional bank using FSC Core (Summer 2025 standard objects, no FinServ__ namespace) wants advisors to see at-a-glance whether each client's retirement goal is on track, and wants the system to automatically flag goals that fall below 80% of the expected funding trajectory.

**Problem:** Without a progress formula and automated status update, advisors must manually calculate funding gaps and update statuses. Goal records often have stale Status values, making goal-level reports unreliable for identifying at-risk clients.

**Solution:**

Step 1 — Add a formula field to FinancialGoal (FSC Core API names):

```
Field API Name: Goal_Progress_Pct__c
Formula Type: Number (2 decimal places)
Formula:
IF(
    TargetValue > 0,
    (ActualValue / TargetValue) * 100,
    0
)
```

Step 2 — Add an expected-trajectory formula field:

```
Field API Name: Expected_Funding_Pct__c
Formula Type: Number (2 decimal places)
Formula (linear interpolation from StartDate to TargetDate):
IF(
    AND(TargetDate > TODAY(), StartDate__c < TargetDate),
    ((TODAY() - StartDate__c) / (TargetDate - StartDate__c)) * 100,
    100
)
```

Step 3 — Build a Record-Triggered Flow on FinancialGoal (Entry Criteria: ActualValue changes):

```
Trigger: Record is Updated
Object: FinancialGoal
Condition: ActualValue changed
Action: Update Record
  IF Goal_Progress_Pct__c < (Expected_Funding_Pct__c * 0.8)
     AND Status != 'Completed'
  THEN Status = 'At Risk'
  ELSE IF Goal_Progress_Pct__c >= (Expected_Funding_Pct__c * 0.8)
     AND Status = 'At Risk'
  THEN Status = 'On Track'
```

Step 4 — Add `Goal_Progress_Pct__c`, `Expected_Funding_Pct__c`, and `Status` to the FinancialGoal compact layout so the values are visible in the related list on the FinancialPlan page.

**Why it works:** The formula fields provide always-current progress data without any scheduled batch. The Flow update ensures the Status field is a reliable system-of-record indicator. Advisors and portfolio reports can now filter by `Status = 'At Risk'` to surface clients requiring immediate outreach.

---

## Anti-Pattern: Using FinServ__ API Names in an FSC Core Org

**What practitioners do:** A developer migrating from managed-package FSC to FSC Core copies Apex classes and Flow metadata verbatim. All SOQL queries and field references still use `FinServ__FinancialGoal__c`, `FinServ__TargetValue__c`, and `FinServ__FinancialPlan__c`.

**What goes wrong:** In an FSC Core org, the `FinServ__` namespace-prefixed objects no longer exist as the primary objects. SOQL queries referencing `FinServ__FinancialGoal__c` return zero rows (if the managed-package objects are no longer present) or target a legacy managed-package version of the object that is no longer in use. Apex that compiles successfully in a scratch org with the managed package installed will fail to compile in the Core org. Integrations silently write goal data to the wrong object.

**Correct approach:** Before any development work, confirm the org type:
- In Setup > Installed Packages: if `Financial Services Cloud` managed package is listed, use `FinServ__` prefix names.
- If no managed package is listed and FSC Core is active (Summer 2025+ org), use standard object names without prefix: `FinancialGoal`, `FinancialPlan`.
- During migration, run a global search across all metadata for `FinServ__FinancialGoal` and replace with `FinancialGoal` — do not leave mixed references in the same deployment.
