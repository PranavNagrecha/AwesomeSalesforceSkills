# Gotchas — Financial Planning Process

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: FinancialGoal and FinancialPlan API Names Are Not the Same Across Org Types

**What happens:** Code, Flows, and integrations that reference `FinServ__FinancialGoal__c` (managed-package API name) fail in FSC Core orgs, and vice versa — code referencing `FinancialGoal` (standard object, no prefix) fails in managed-package FSC orgs that have not yet migrated.

**When it occurs:** This bites teams during org migrations from managed-package FSC to FSC Core (introduced Summer 2025), when sandbox environments have a different org type than production, when a developer copies metadata or Apex from one org to another without checking the installed package state, or when an integration is configured using object names from documentation that does not distinguish between org types.

**How to avoid:** Always confirm the org type before any development. In Setup > Installed Packages, check whether the Financial Services Cloud managed package (namespace: `FinServ`) is listed. If it is, use `FinServ__FinancialGoal__c`. If FSC Core is active and the managed package is not installed, use `FinancialGoal`. During migration, run a global metadata search for all `FinServ__FinancialGoal` references and replace them before deploying to the target org.

---

## Gotcha 2: Revenue Insights Requires a Separate License Not Included in Base FSC

**What happens:** Admins enable Revenue Insights dashboards in a sandbox (which has the CRM Analytics for Financial Services add-on provisioned), configure goal-progress and AUM dashboards, and then find those dashboards are completely absent in production — because the production org does not have the Revenue Intelligence for Financial Services license.

**When it occurs:** This happens whenever teams build analytics features in a sandbox that has been over-provisioned with add-on licenses for evaluation, without verifying that production has the same license. The gap is often discovered at UAT or go-live.

**How to avoid:** Before designing any goal analytics or Revenue Insights dashboard, confirm the Revenue Intelligence for Financial Services (CRM Analytics) license is provisioned in the production org. In Setup > Company Information > Feature Licenses, look for "CRM Analytics for Financial Services" or confirm with your Salesforce Account Executive. Do not build Revenue Insights features in a sandbox unless production has the matching license or the project explicitly includes a license procurement work stream.

---

## Gotcha 3: Discovery Framework Captures Responses but Does Not Produce a Risk Score

**What happens:** Teams configure the Discovery Framework to present risk tolerance questions to clients or advisors and assume the framework will automatically calculate and store a composite risk profile (e.g., Conservative / Moderate / Aggressive). The framework stores individual question responses as structured records, but no risk score or profile value appears on the client record.

**When it occurs:** This occurs when teams use the Discovery Framework without reading the platform's native capability boundary. The framework handles questionnaire delivery and response capture; it does not include response aggregation, weighting, or scoring logic.

**How to avoid:** Explicitly design the scoring layer before configuring the Discovery Framework. Either: (a) build a Flow or Apex trigger that reads Discovery Framework response records after completion and computes a weighted score, writing the result to a custom field on Account/Household; or (b) integrate a third-party risk profiling tool (Riskalyze, FinaMetrica) that handles scoring internally and pushes the output score to a mapped Salesforce field. Document which approach is in use and what field stores the canonical risk profile.

---

## Gotcha 4: FinancialGoal Status Field Is Not Auto-Maintained by the Platform

**What happens:** FinancialGoal Status values (On Track, At Risk, Completed, etc.) remain on their initial value indefinitely. Reports and dashboards relying on Status show stale data. Advisors see "On Track" on goals that are significantly underfunded.

**When it occurs:** This occurs whenever ActualValue is updated (manually or by an integration) but there is no corresponding logic to evaluate and update the Status field. The platform does not evaluate goal funding health natively.

**How to avoid:** Implement a Record-Triggered Flow on FinancialGoal that fires on ActualValue changes and applies status logic based on the ratio of ActualValue to TargetValue adjusted for time elapsed. Alternatively, use a nightly scheduled batch that re-evaluates all active goals and updates Status fields in bulk. Document the update mechanism in the org's configuration guide so future admins do not assume the platform maintains this field automatically.

---

## Gotcha 5: FinancialPlan Does Not Aggregate Goal Values Natively

**What happens:** Admins create a FinancialPlan record and expect to see a rolled-up total target value, total current value, and overall plan health score on the plan record. None of these fields are populated by the platform.

**When it occurs:** This happens when teams treat FinancialPlan as a calculation engine rather than a container/grouping object. The FinancialPlan-to-FinancialGoal relationship is a lookup, and there are no native rollup summary fields provided out-of-the-box by the platform on this relationship.

**How to avoid:** Build rollup summary fields on FinancialPlan if the relationship is changed to master-detail, or use custom Apex rollup triggers / Flow aggregate calculations to push totals from goals to the parent plan record. Alternatively, use a Revenue Insights dashboard (if licensed) for plan-level aggregation views rather than expecting the FinancialPlan record itself to show aggregate totals.
