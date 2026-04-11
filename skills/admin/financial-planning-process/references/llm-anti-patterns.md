# LLM Anti-Patterns — Financial Planning Process

Common mistakes AI coding assistants make when generating or advising on Financial Planning Process in Salesforce FSC.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using FinServ__ Namespace API Names in FSC Core Orgs

**What the LLM generates:**
```apex
// Generated Apex in an FSC Core org
List<FinServ__FinancialGoal__c> goals = [
    SELECT Id, FinServ__TargetValue__c, FinServ__ActualValue__c
    FROM FinServ__FinancialGoal__c
    WHERE FinServ__FinancialPlan__c = :planId
];
```

**Why it happens:** LLMs are trained on large volumes of FSC documentation and community content that predates Summer 2025, when FinancialGoal became a standard object. The managed-package API names (`FinServ__`) dominate the training corpus, so the model defaults to them even in contexts where the org type is FSC Core.

**Correct pattern:**
```apex
// FSC Core org — no FinServ__ prefix
List<FinancialGoal> goals = [
    SELECT Id, TargetValue, ActualValue
    FROM FinancialGoal
    WHERE FinancialPlanId = :planId
];
```

**Detection hint:** Search generated code for `FinServ__FinancialGoal` or `FinServ__FinancialPlan`. If the org is FSC Core (Summer 2025+), these names are wrong. If the org uses the managed package, the standard names without prefix are wrong.

---

## Anti-Pattern 2: Assuming FinancialPlan Natively Aggregates Goal Values

**What the LLM generates:** Advice such as "the FinancialPlan record shows the total of all linked goal values and overall plan health" or SOQL that reads a `TotalTargetValue` or `PlanHealth` field directly off FinancialPlan.

```apex
// Wrong — these fields do not exist natively on FinancialPlan
Decimal totalTarget = plan.TotalTargetValue__c;
String planHealth = plan.PlanHealthScore__c;
```

**Why it happens:** LLMs infer that a parent-container object (FinancialPlan) should logically aggregate its children (FinancialGoals) and generate field names that sound plausible. These fields do not exist natively.

**Correct pattern:**
```apex
// Correct — aggregate goal values explicitly in Apex or via formula field
AggregateResult[] results = [
    SELECT SUM(ActualValue) totalActual, SUM(TargetValue) totalTarget
    FROM FinancialGoal
    WHERE FinancialPlanId = :planId
];
```
Or use a custom rollup field built on the FinancialPlan object if the relationship is master-detail.

**Detection hint:** Check for field references like `TotalTargetValue`, `PlanHealth`, `AggregateGoalValue`, or any similar compound field on the FinancialPlan object that implies automatic rollup.

---

## Anti-Pattern 3: Claiming Revenue Insights Is Included in the Base FSC License

**What the LLM generates:** Guidance such as "In FSC, you can use the Revenue Insights dashboard to track goal progress across the book of business — it's available as part of your FSC license."

**Why it happens:** LLMs frequently conflate feature availability with licensing. Revenue Insights is a real FSC-adjacent feature and appears in FSC documentation, leading models to assume it is bundled with the base license.

**Correct pattern:**
```
Revenue Insights (CRM Analytics for Financial Services / Revenue Intelligence for Financial Services)
requires a SEPARATE license from the base FSC license.
Confirm the license is provisioned in Setup > Company Information > Feature Licenses
before designing any Revenue Insights-dependent capability.
```

**Detection hint:** Look for phrases like "available in FSC", "included with Financial Services Cloud", or "no additional license required" adjacent to any reference to Revenue Insights, CRM Analytics, or goal analytics dashboards.

---

## Anti-Pattern 4: Treating Discovery Framework as a Risk Scoring Engine

**What the LLM generates:** Instructions to configure Discovery Framework and then read back a composite risk score from a `RiskScore` field or `RiskProfile` field on the DiscoveryFramework response object.

```apex
// Wrong — Discovery Framework does not produce a risk score field
String riskProfile = response.RiskScore__c; // Does not exist
```

**Why it happens:** The Discovery Framework's name and purpose (structured discovery/assessment) implies to the model that it produces a scored output. The model generates field names that sound like risk assessment outputs but do not exist on the response objects.

**Correct pattern:**
```
Discovery Framework captures individual question responses as structured records.
To derive a risk profile:
1. Query the response records for the completed assessment.
2. Apply weighting logic in a Flow or Apex trigger.
3. Write the computed score to a custom field on Account or Household:
   Risk_Tolerance_Score__c (Number) and Risk_Profile__c (Picklist).
```

**Detection hint:** Look for generated field names such as `RiskScore`, `RiskProfile`, `AssessmentScore`, or `CompositeScore` on Discovery Framework response objects. These do not exist natively.

---

## Anti-Pattern 5: Assuming FinancialGoal Status Is Auto-Maintained

**What the LLM generates:** Guidance that says "the FinancialGoal Status field automatically updates to 'At Risk' when the current value falls below the target trajectory" or SOQL that treats Status as a reliable real-time indicator without verifying the update mechanism.

**Why it happens:** It is semantically logical that a financial goal object would maintain its own status. LLMs generate this claim because it is the expected behavior, not because it is documented platform behavior.

**Correct pattern:**
```
FinancialGoal Status is NOT auto-maintained by the Salesforce platform.
The Status field value is whatever was last written to it — by an advisor, an integration,
a Flow, or a batch job. Without an explicit update mechanism, Status values become stale.

Required: Implement one of:
- A Record-Triggered Flow on FinancialGoal that evaluates ActualValue vs TargetValue
  and updates Status accordingly when ActualValue changes.
- A nightly scheduled batch that re-evaluates all active goal statuses.
- An integration process that updates Status as part of custodial data sync.
Document the chosen mechanism in the org configuration guide.
```

**Detection hint:** Check for any assumption that `Status = 'At Risk'` reliably reflects current goal funding health without an explicit update mechanism being documented or implemented. Also check for SOQL reports or dashboard filters that rely on Status without confirming the maintenance process is in place.

---

## Anti-Pattern 6: Ignoring FSC Core vs. Managed-Package for FinancialPlan Relationship Fields

**What the LLM generates:** Flow or Apex that references the goal-to-plan relationship using the managed-package field name in an FSC Core org, or vice versa.

```
// Managed package: goal's lookup to plan is FinServ__FinancialPlan__c
// FSC Core: goal's lookup to plan is FinancialPlanId (standard relationship field)
```

**Why it happens:** Even when the LLM correctly identifies that FinancialGoal should not use the `FinServ__` prefix in Core, it still generates the managed-package relationship field name for the lookup to FinancialPlan, because that relationship name is prominent in training data.

**Correct pattern:**
```
FSC Core (Summer 2025+):
  - Relationship field on FinancialGoal pointing to FinancialPlan: FinancialPlanId
  - SOQL: SELECT Id FROM FinancialGoal WHERE FinancialPlanId = :planId

Managed Package FSC:
  - Relationship field: FinServ__FinancialPlan__c
  - SOQL: SELECT Id FROM FinServ__FinancialGoal__c WHERE FinServ__FinancialPlan__c = :planId
```

**Detection hint:** When reviewing generated SOQL or Flow field references for FinancialGoal, check not only the object name but also the relationship field name. Mixed-namespace references (standard object name + managed-package field name) are a common partial fix that still causes errors.
