# Well-Architected Notes — Financial Planning Process

## Relevant Pillars

- **Security** — Financial goal and plan records contain sensitive client financial data (target amounts, current portfolio values, retirement dates). Field-level security, sharing rules, and profile permissions must restrict access to authorized advisors and relationship managers only. Discovery Framework response records that capture risk assessment data are equally sensitive and require the same access controls. Encryption at rest (Shield Platform Encryption) should be evaluated for `TargetValue`, `ActualValue`, and any custom risk score fields that hold personally identifiable financial information.

- **Reliability** — The accuracy of goal progress data depends entirely on the reliability of the update mechanism for `ActualValue`. If the update process (manual advisor entry, custodial integration, or batch job) fails silently, goal statuses become stale and the review cycle workflow operates on incorrect data. The review cycle Action Plan template must be version-controlled (clone-and-republish) to prevent disruption to in-flight plans when task sequences change. Published templates are immutable and cannot be changed retroactively.

- **Operational Excellence** — Review cycle Action Plan templates provide the observable, traceable audit trail that compliance and regulatory reporting require. Each plan instance records which tasks were completed, by whom, and when — supporting defensible compliance documentation. Risk tolerance re-assessment tasks embedded in the review Action Plan ensure the process is executed consistently rather than relying on advisor discretion.

- **Performance** — Financial goal queries filtered by Status and by parent FinancialPlan should use selective filters. In orgs with large book-of-business datasets (tens of thousands of goal records), unindexed queries on `ActualValue` or formula fields can cause SOQL timeout or long-running report generation. Index `Status`, `GoalType`, and the parent plan lookup. Avoid constructing formula fields that require full table scans for evaluation.

- **Scalability** — As the client book grows, the volume of FinancialGoal and ActionPlan records grows proportionally. At-Risk alert Flows triggered on every `ActualValue` update should be evaluated against governor limits if the custodial integration writes bulk updates. Consider using a scheduled batch to re-evaluate goal statuses nightly rather than a record-triggered Flow if update volume is high (thousands of goal records updated per batch window).

## Architectural Tradeoffs

**Native FSC objects vs. custom-built goal model:** FinancialGoal and FinancialPlan are native FSC objects with pre-built page layouts, related list integration, and FSC app page support. Using them means accepting the platform's data model constraints (no native aggregation on FinancialPlan, no native risk scoring). Building a fully custom goal tracking model on custom objects provides more flexibility but loses native FSC integration, future roadmap alignment, and AppExchange compatibility. Prefer native FSC objects for goal tracking; extend with custom fields and automation rather than replacing the native model.

**Discovery Framework vs. custom risk questionnaire:** The Discovery Framework provides a structured, FSC-native questionnaire delivery mechanism with response tracking. It requires additional development to derive scores from responses. A custom-built questionnaire on a custom object gives full control over scoring logic and UI but requires more build effort and loses any future FSC platform enhancements to the Discovery Framework. For most use cases, the Discovery Framework plus a scoring Flow or Apex is the better tradeoff.

**Action Plans vs. Flow-created Tasks for review cycles:** Action Plans provide grouped plan-level tracking, offset-based deadline scheduling, and versioned templates — all advantages over Flow-created individual tasks. The tradeoff is that Action Plan template updates require a clone-and-republish cycle, which is more operationally complex than modifying a Flow. For regulated financial services firms that require auditable review cycles, Action Plans are the correct choice.

## Anti-Patterns

1. **Hardcoding managed-package API names across a migration** — Referencing `FinServ__FinancialGoal__c` in Apex, Flow, and integrations without a plan to update those references before migrating to FSC Core results in widespread compile errors and broken integrations. The correct pattern is to create an API name reference document for the org type and enforce its use across all development artifacts before any migration work begins.

2. **Assuming base FSC includes Revenue Insights** — Building analytics and goal-progress dashboards that depend on Revenue Insights features (CRM Analytics for Financial Services) without verifying the license is provisioned creates features that exist only in over-provisioned sandboxes and do not survive to production. The correct pattern is to confirm license availability before designing any Revenue Insights-dependent capability.

3. **Treating FinancialPlan as a calculation engine** — Expecting FinancialPlan to automatically aggregate goal values, compute funding gaps, or maintain a health score results in empty plan records and advisor confusion. FinancialPlan is a grouping container; aggregation logic must be explicitly built using formula fields, rollup triggers, or Revenue Insights dashboards.

## Official Sources Used

- FSC Financial Plans and Goals (Salesforce Help) — https://help.salesforce.com/s/articleView?id=ind.fsc_financial_goals.htm
- Action Plans in Financial Services Cloud (FSC Admin Guide) — https://help.salesforce.com/s/articleView?id=ind.fsc_admin_action_plans.htm
- FSC Developer Guide (Spring '26) — https://developer.salesforce.com/docs/atlas.en-us.financial_services_cloud_object_reference.meta/financial_services_cloud_object_reference/fsc_dev_guide.htm
- ActionPlanTemplate Object Reference (Salesforce Platform) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_actionplantemplate.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Well-Architected: Trusted Pillar — https://architect.salesforce.com/docs/architect/well-architected/trusted/overview.html
- Salesforce Well-Architected: Reliable Pillar — https://architect.salesforce.com/docs/architect/well-architected/reliable/overview.html
