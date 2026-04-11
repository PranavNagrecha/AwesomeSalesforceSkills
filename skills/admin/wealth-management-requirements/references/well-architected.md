# Well-Architected Notes — Wealth Management Requirements

## Relevant Pillars

- **Operational Excellence** — The primary pillar for this skill. FSC wealth management requirements work is the foundation for a well-operating implementation. A requirements process that fails to confirm the managed package vs. FSC Core architecture, scope the correct object model, or surface ISV compatibility constraints will produce a build that is operationally fragile — prone to namespace errors, missing rollup data, and broken integrations. Structured discovery and a validated fit-gap analysis are the operational excellence deliverables.

- **Reliability** — FSC wealth management data flows (custodian feeds, household rollups, AccountFinancialSummary population) are only reliable when the underlying architecture is confirmed and the integration dependencies (PSL integration user, ISV package certification) are captured at requirements time. Reliability risks that are not surfaced during requirements discovery become production incidents.

- **Security** — Wealth management involves highly sensitive financial data. Requirements discovery must surface data visibility requirements: which advisors see which client accounts, how household-level data is shared across advisor teams, whether Compliant Data Sharing (CDS) policies are required, and how client portal access is scoped. These are security architecture inputs that must be captured during requirements, not retrofitted post-build.

- **Scalability** — Volume discovery is a requirements activity. The number of client households, financial accounts per household, ActionPlan instances per year, and FinancialHolding positions per account all drive scalability decisions in the build phase. Requirements that omit volume data leave architects unable to design for scale.

- **Performance** — Household-level rollup requirements (total AUM, net worth, goal progress) have direct performance implications depending on whether they are implemented via AccountFinancialSummary (Core batch), Apex triggers (managed package), or CRM Analytics datasets. The correct implementation path must be determined during requirements — not during performance testing.

## Architectural Tradeoffs

**Managed package vs. FSC Core:** The core architectural tradeoff in FSC wealth management requirements. Managed package offers broader ISV ecosystem compatibility and is battle-tested in large enterprise orgs. FSC Core offers modern data model capabilities (FinancialAccountParty, AccountFinancialSummary, native Record Rollups) but requires ISV validation and a more complex rollup infrastructure setup. Requirements must expose this tradeoff explicitly rather than defaulting to one model without stakeholder input.

**Standard FSC features vs. custom development:** Many wealth management requirements can be met by standard FSC features (ActionPlan, FinancialGoal, FinancialPlan) if the implementation uses them correctly. The tradeoff is between leveraging standard FSC capabilities — which are upgrade-safe, supported by Salesforce, and require less custom code — and building custom logic that exactly mirrors current-state processes but creates maintenance burden and upgrade risk. Requirements should always document why a standard feature is or is not sufficient before recommending custom development.

**Household rollup approach:** In managed-package orgs, household-level balance rollups require Apex triggers. In Core orgs, they use AccountFinancialSummary + PSL integration user. Both approaches have infrastructure requirements that must be surfaced during requirements. A requirements document that says "show total household AUM" without specifying the rollup mechanism leaves an open architecture decision that will be made incorrectly by default.

## Anti-Patterns

1. **Object naming before architecture confirmation** — Writing requirements with specific FSC object API names (e.g., `FinServ__FinancialGoal__c`) before confirming whether the org uses the managed package or FSC Core. This produces requirements documents that are incorrect for at least one architecture and causes systematic translation errors during build. Requirements should describe business intent; object names should be added only after the architecture is confirmed.

2. **Treating custodian data feed as a configuration task** — Requirements that classify custodian data integration (e.g., "load nightly position data from Black Diamond") as a Salesforce configuration item rather than a formal integration requirement. Custodian data feeds are integration projects with their own source system analysis, field mapping, error handling, and scheduling requirements. Misclassifying them understates project scope and omits critical requirements (data format, transformation rules, error retry behavior).

3. **Deferring volume discovery to architecture phase** — Treating "how many records will this generate?" as an architecture concern rather than a requirements concern. Advisor count, household count, ActionPlan volume, and FinancialHolding position count all drive architecture decisions. BAs must collect this data during discovery — it is a requirements deliverable, not an architectural assumption.

## Official Sources Used

- Salesforce Help — Set Up and Manage Wealth Management: https://help.salesforce.com/s/articleView?id=sf.fsc_wealth_management.htm
- FSC Object Reference — FinancialGoal: https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/sforce_api_objects_financialgoal.htm
- Salesforce Help — Financial Plans and Goals Considerations and Limitations: https://help.salesforce.com/s/articleView?id=sf.fsc_financial_plans_goals_considerations.htm
- FSC Industries Developer Guide (IndustriesSettings metadata, Wealth Management AI pref): https://developer.salesforce.com/docs/industries/financial-services/guide/industries-developer-guide.html
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
