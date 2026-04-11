---
name: financial-planning-process
description: "Use this skill when configuring FSC financial planning objects, designing periodic review cycles, modeling risk assessment workflows, or tracking goal progress in Financial Services Cloud. Trigger keywords: FinancialGoal, FinancialPlan, goal tracking, risk tolerance, review cycle, financial planning workflow, Discovery Framework, Revenue Insights. NOT for financial advice, investment recommendations, or high-level process mapping (see wealth-management-requirements for that)."
category: admin
salesforce-version: "Summer '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "how do I set up financial goals and plans for clients in FSC and track progress against those goals"
  - "how do I build an annual review cycle in Financial Services Cloud using Action Plan templates with offset-based task deadlines"
  - "how do I capture client risk tolerance in FSC when there is no dedicated risk object in the data model"
  - "what is the difference between FinancialGoal in the managed package versus FSC Core and why do my API names break after migration"
  - "how do I configure Revenue Insights dashboards to show goal progress and what license is required"
tags:
  - financial-planning-process
  - financial-services-cloud
  - fsc
  - financial-goal
  - financial-plan
  - action-plan
  - review-cycle
  - risk-tolerance
  - discovery-framework
inputs:
  - FSC org type (managed package with FinServ__ namespace, or FSC Core with standard objects introduced in Summer 2025)
  - List of goal categories in scope (retirement, education, homeownership, emergency fund, etc.)
  - Intended review cadence (annual, semi-annual, quarterly) and responsible roles
  - Risk assessment methodology in use (Discovery Framework, custom fields, third-party tool)
  - Whether Revenue Insights / CRM Analytics for Financial Services license is available
outputs:
  - FinancialGoal and FinancialPlan object configuration guidance with correct API names per org type
  - Action Plan template design for periodic review cycles with offset-based task deadlines
  - Risk tolerance data-model recommendation (custom fields, Discovery Framework, or third-party integration)
  - Decision guidance on Revenue Insights licensing requirements
  - Review checklist for goal-plan setup and review cycle validation
dependencies:
  - admin/fsc-action-plans
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Financial Planning Process

This skill activates when a practitioner needs to configure FSC financial planning objects (FinancialGoal, FinancialPlan), design client review cycle workflows using Action Plan templates, model risk tolerance data, or understand the licensing boundary for Revenue Insights analytics. It does NOT cover financial advice, investment strategy, or high-level process mapping (use the wealth-management-requirements skill for that).

---

## Before Starting

Gather this context before working on anything in this domain:

- **Identify the org type first.** The FinancialGoal and FinancialPlan API names differ between FSC managed-package orgs and FSC Core orgs. In the managed package, every object carries the `FinServ__` prefix (e.g., `FinServ__FinancialGoal__c`). In FSC Core (Summer 2025 and later), these became standard objects — `FinancialGoal` — with no namespace prefix. Using the wrong API name causes silent data misroutes or broken integrations.
- **Check the FSC license type.** Revenue Insights dashboards (goal progress analytics, AUM trends, household rollups) require a separate CRM Analytics / Revenue Intelligence for Financial Services license. They are not included in the base FSC license. Teams frequently assume Revenue Insights is included and are caught by this at project go-live.
- **Risk tolerance has no dedicated native FSC object.** The Discovery Framework can capture structured assessment responses, but scoring, weighting, and recommendation tracking require custom fields on the client record or integration with a third-party risk profiling tool (e.g., Riskalyze, FinaMetrica). Do not attempt to use native FSC objects alone for quantitative risk scoring without extending the data model.
- **Action Plan templates are the primary native mechanism for review cycles.** Offset-based task deadlines (`DaysFromStart` on `ActionPlanTemplateItem`) provide the scheduling backbone for periodic reviews. Refer to the `fsc-action-plans` skill for the full Action Plan configuration guide.

---

## Core Concepts

### FinancialGoal and FinancialPlan Objects

A `FinancialGoal` record represents a single discrete financial objective for a client household — for example, "Retire by 65 with $1.5M", "Fund college education for two children", or "Build a six-month emergency fund". Each goal stores target amount, current amount, target date, goal type (picklist), and status.

A `FinancialPlan` record acts as a container that links to one or more `FinancialGoal` records, providing a consolidated view of a client's overall planning engagement. The FinancialPlan-to-FinancialGoal relationship is a standard parent-child lookup, not a master-detail, so goals can technically exist without a parent plan (though best practice is to always associate them).

**API name differences by org type:**

| Concept | Managed-Package API Name | FSC Core API Name (Summer 2025+) |
|---|---|---|
| Goal object | `FinServ__FinancialGoal__c` | `FinancialGoal` |
| Plan object | `FinServ__FinancialPlan__c` | `FinancialPlan` |
| Goal → Plan lookup | `FinServ__FinancialPlan__c` (field) | `FinancialPlanId` |
| Goal type picklist | `FinServ__GoalType__c` | `GoalType` |
| Target amount | `FinServ__TargetValue__c` | `TargetValue` |
| Current amount | `FinServ__ActualValue__c` | `ActualValue` |

Any Apex, Flow, or integration that references these objects must use the correct API name for the deployed org type. Mixing namespace-prefixed and standard names in the same deployment causes compilation errors or silent failures.

### Managed-Package FSC vs. FSC Core

FSC was originally delivered as a managed package under the `FinServ__` namespace. In Summer 2025, Salesforce promoted a set of Financial Services objects — including `FinancialGoal` and `FinancialPlan` — to standard platform objects under FSC Core. FSC Core orgs receive these objects without the namespace prefix. Migration between managed-package and FSC Core requires explicit data and metadata migration; the two object families are not automatically interchangeable.

Admins and developers working on orgs that have migrated (or are in the process of migrating) to FSC Core must audit every reference to `FinServ__FinancialGoal__c` and replace it with `FinancialGoal`. Reports, list views, formula fields, validation rules, Apex classes, and integration mappings are common sources of stale namespace references.

### Action Plans as the Review Cycle Engine

FSC Action Plan templates are the primary native mechanism for modeling periodic client review cycles. A template configured with `TargetEntityType = FinancialGoal` or `TargetEntityType = FinancialAccount` produces a set of tasks with due dates computed from `DaysFromStart` offsets relative to the plan's start date.

A typical annual review Action Plan template includes tasks such as: "Update goal progress values" (Day 0), "Send pre-meeting questionnaire to client" (Day -14, or offset from a 'review date' field), "Run portfolio performance report" (Day 0), "Document updated risk tolerance responses" (Day 0), "Advisor review sign-off" (Day 5), "Submit updated plan to compliance" (Day 7). The `TaskDeadlineType` controls whether offsets count calendar days or business days.

Because published templates are immutable, a versioning strategy (clone-and-republish) is required whenever the review task list changes year-over-year.

### Risk Tolerance Modeling

Risk tolerance in FSC does not map to a single dedicated native object. The platform offers three approaches:

1. **Discovery Framework:** A structured questionnaire and response framework natively available in FSC. It can capture multiple-choice and scored responses for risk assessment questions. However, it does not natively aggregate responses into a composite risk score or recommendation — that logic requires custom Apex, Flow, or a third-party integration.
2. **Custom fields on the Account/Household object:** Adding fields such as `Risk_Tolerance_Score__c` (Number), `Risk_Profile__c` (Picklist: Conservative / Moderate / Aggressive), and `Last_Risk_Assessment_Date__c` (Date) to the Account record provides a lightweight structured approach suitable for most advisory workflows.
3. **Third-party risk profiling tools:** Tools such as Riskalyze (Nitrogen) or FinaMetrica integrate via API to push scored risk profiles back into Salesforce. In this pattern, Salesforce stores the output (score and recommendation) as custom fields; the tool handles the assessment logic.

---

## Common Patterns

### Annual Review Cycle Using Action Plan Template

**When to use:** The firm requires a documented, trackable annual review workflow for every managed client relationship, with tasks staggered across 30 days and assigned to advisor, operations, and compliance roles.

**How it works:**
1. Create an `ActionPlanTemplate` with `TargetEntityType = FinancialAccount` (or `Account` for the household), `TaskDeadlineType = Calendar`, Status = `Draft`.
2. Add `ActionPlanTemplateItem` records for each review step. Representative items:
   - "Pull year-end account statements" — DaysFromStart: 0, Assigned: Operations queue
   - "Update FinancialGoal ActualValue fields" — DaysFromStart: 1, Assigned: Advisor
   - "Send client pre-meeting document request" — DaysFromStart: 2, Assigned: Advisor
   - "Conduct risk tolerance reassessment (Discovery Framework)" — DaysFromStart: 5, Assigned: Advisor
   - "Complete advisor review notes and recommendation" — DaysFromStart: 14, Assigned: Advisor
   - "Compliance documentation sign-off" — DaysFromStart: 21, Required: true, Assigned: Compliance queue
   - "File completed review record" — DaysFromStart: 28, Assigned: Operations queue
3. Publish the template (Status = Active) and test by launching a plan from a test FinancialAccount record.
4. At the start of each annual review season, launch plan instances in bulk using a Flow or batch process targeting accounts flagged for review.

**Why not the alternative:** Creating individual Tasks or using a Flow with fixed due dates loses grouped plan-level visibility, lacks offset-based scheduling, cannot be versioned as a template, and produces no plan-completion tracking at the portfolio level.

### Goal Progress Tracking Configuration

**When to use:** The practice wants advisors and clients to see current-vs-target goal progress on each FinancialGoal record, and wants to trigger an alert when a goal falls below a minimum funding threshold.

**How it works:**
1. Confirm the `ActualValue` field (managed: `FinServ__ActualValue__c`; Core: `ActualValue`) is being updated on a regular cadence — either by the advisor manually, by an integration from the custodial system, or by a nightly batch.
2. Add a formula field `Goal_Progress_Pct__c = ActualValue / TargetValue * 100` to the FinancialGoal object to show percentage completion.
3. Create a validation or alert rule: if `Goal_Progress_Pct__c < threshold AND Status != 'At Risk'`, update the Status picklist to "At Risk" via a Flow record-update trigger.
4. Add the FinancialGoal related list to the FinancialPlan and Household page layouts so advisors see all goal statuses in one view.
5. If Revenue Insights is licensed, use the pre-built "Goals" dashboard to visualize goal progress and funding gaps across the book of business.

**Why not the alternative:** Relying on periodic report-and-email alert flows without updating the Status field on the record itself means no single system-of-record status, and no ability to filter a list view to "At-Risk Goals" for proactive advisor action.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org uses managed-package FSC | Use `FinServ__FinancialGoal__c` and `FinServ__FinancialPlan__c` API names | Managed-package objects carry the FinServ__ namespace; standard names cause compile or query errors |
| Org uses FSC Core (Summer 2025+) | Use `FinancialGoal` and `FinancialPlan` without namespace prefix | Core promotes these to standard objects; namespace prefix causes errors in Core orgs |
| Need periodic review task sequence | Build an Action Plan template with offset-based DaysFromStart | Native FSC mechanism; versioned, trackable, and supports FSC object target types |
| Need risk tolerance scoring | Use Discovery Framework for capture + custom fields for score output | No native risk scoring object; Discovery captures responses, custom fields hold aggregate scores |
| Need portfolio-level goal analytics | Confirm Revenue Insights / CRM Analytics for Financial Services license first | Base FSC does not include Revenue Insights dashboards; separate license required |
| Migrating from managed package to FSC Core | Audit all references to FinServ__ prefix objects and update to standard API names | Core objects are not aliases — both sets of API names can coexist in a migrating org, causing dual-write confusion |
| Goal progress needs to update from custodial data | Build or configure an integration that writes to ActualValue field | There is no native custodial data feed in FSC; ActualValue requires explicit update via integration, batch, or manual entry |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm org type and object API names** — Determine whether the org uses the managed-package FSC (namespace: `FinServ__`) or FSC Core (Summer 2025+, no namespace). Document the correct API names for `FinancialGoal`, `FinancialPlan`, and all relevant fields before touching any configuration. Reference the API name table in Core Concepts above.
2. **Audit existing goal and plan records** — If goals or plans already exist in the org, check whether they are on the correct object, whether the FinancialPlan-to-FinancialGoal relationships are populated, and whether Status and ActualValue fields are being maintained.
3. **Configure FinancialGoal and FinancialPlan page layouts** — Add key fields (GoalType, TargetValue, ActualValue, TargetDate, Status, progress formula field) to the page layout. Add the FinancialGoal related list to FinancialPlan. Ensure the FinancialPlan related list appears on the Household or Account layout.
4. **Design and build the review cycle Action Plan template** — Following the pattern above, define the task sequence, assign roles/queues, set `DaysFromStart` offsets, choose Calendar vs. BusinessDays, and publish. Cross-reference the `fsc-action-plans` skill for template immutability and versioning rules.
5. **Model risk tolerance data** — Decide among Discovery Framework, custom fields, or third-party integration. Implement the chosen approach: configure Discovery Framework questionnaires, add custom fields to Account/Household, or document the integration mapping from the third-party tool to Salesforce fields.
6. **Validate Revenue Insights licensing and dashboard access** — If goal progress analytics or book-of-business dashboards are in scope, confirm the Revenue Intelligence for Financial Services license is provisioned before building any dashboard dependencies on it.
7. **Run end-to-end review cycle test** — Launch a test plan from a FinancialAccount or Account record, verify task due dates are correct, confirm goal status fields update as expected, and validate that the risk tolerance fields are populated on the record after the review workflow completes.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Correct API names used for FinancialGoal and FinancialPlan matching the org type (managed-package vs. FSC Core)
- [ ] FinancialPlan-to-FinancialGoal relationship is populated for all active goals
- [ ] Goal ActualValue and Status fields have a defined update mechanism (manual, integration, or batch)
- [ ] Action Plan template TargetEntityType matches the intended FSC object and template is in Active status
- [ ] DaysFromStart offsets produce correct due dates when tested with a real plan launch
- [ ] Risk tolerance capture method selected and fields/framework configured
- [ ] Revenue Insights license confirmed before building any goal-analytics dashboard dependencies
- [ ] No references to the wrong namespace (FinServ__ in a Core org, or missing namespace in a managed-package org)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **FinancialGoal API names differ between managed-package and FSC Core** — In the managed package, the object is `FinServ__FinancialGoal__c`; in FSC Core (Summer 2025+), it is the standard object `FinancialGoal` with no prefix. Flows, Apex, integrations, and reports referencing the wrong name fail silently or throw compilation errors. Always confirm org type before building any reference to these objects.
2. **FinancialPlan is a container, not a calculation engine** — FinancialPlan does not natively aggregate goal values, compute funding gaps, or produce a "plan health" score. These calculations require formula fields, custom Apex rollups, or Revenue Insights. Expecting native plan-level aggregation leads to missing data on plan records.
3. **Revenue Insights requires a separate license** — The Revenue Intelligence for Financial Services (CRM Analytics) license is not bundled with the base FSC license. Admins who configure Revenue Insights dashboards in a sandbox provisioned with the add-on license will find the dashboards missing in production if the production org does not have the matching license.
4. **Discovery Framework captures responses but does not score them** — The Discovery Framework records questionnaire answers as structured response objects but provides no native aggregation, weighting, or risk-score computation. Custom logic (Apex or Flow) is required to derive a composite risk score from raw responses.
5. **Goal Status field is not auto-updated by the platform** — FinancialGoal Status (On Track, At Risk, Completed, etc.) is not automatically maintained by Salesforce. It requires explicit updates via advisor input, a Flow rule comparing ActualValue to TargetValue, or an integration process. Stale statuses on goal records undermine the reliability of any portfolio-level reporting.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| FinancialGoal and FinancialPlan configuration guide | API name reference, field setup, layout configuration, and relationship wiring per org type |
| Annual review Action Plan template | Published ActionPlanTemplate with offset-based task sequence for periodic client reviews |
| Risk tolerance data model decision | Recommended approach (Discovery Framework, custom fields, or third-party) with field specifications |
| Goal progress formula field | `Goal_Progress_Pct__c` formula and At-Risk alert flow configuration |
| Revenue Insights licensing decision record | Documented confirmation of whether Revenue Intelligence for Financial Services is licensed |

---

## Related Skills

- admin/fsc-action-plans — Full configuration guide for ActionPlanTemplate and ActionPlanItem objects; required when designing the review cycle Action Plan template referenced in this skill.
- data/fsc-data-model — Covers the complete FSC object model including managed-package vs. Core API name differences; use for broader data model context beyond FinancialGoal and FinancialPlan.
- admin/financial-account-setup — Covers FinancialAccount object configuration; FinancialGoal Action Plan templates often target FinancialAccount as the parent record.
