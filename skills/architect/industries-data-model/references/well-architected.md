# Well-Architected Notes — Industries Data Model

## Relevant Pillars

- **Reliability** — Industries data models are additive extensions to the core Salesforce platform. Using standard Industries objects (InsurancePolicy, CarePlan, ServicePoint) rather than custom objects ensures that platform upgrades, patch releases, and managed package updates do not break data model contracts. Reliability failures occur when custom objects duplicate standard Industries objects and fall out of sync with platform capabilities.

- **Operational Excellence** — Correctly using standard Industries objects reduces operational overhead by leveraging built-in OmniStudio integration, standard reports and dashboards, and pre-built Lightning components. Misusing the data model — particularly the Account vs Contact participant relationship in Insurance Cloud — creates operational debt that surfaces as integration failures, incorrect reports, and manual data correction overhead.

- **Security** — Industries objects inherit Salesforce's standard object-level and field-level security model. Record access for InsurancePolicy and CarePlan records follows org-wide defaults, sharing rules, and profile/permission set controls exactly as standard objects do. There is no Industries-specific security bypass. Sensitive health and financial data in Industries objects must be governed with the same FLS and record-sharing policies applied to Account and Contact.

- **Performance** — SOQL queries against Industries objects benefit from standard Salesforce indexing on lookup fields (AccountId on InsurancePolicyParticipant, InsurancePolicyId on InsurancePolicyCoverage). Queries without selective WHERE clauses on large Industries object tables will hit governor limits. Communications Cloud Account queries without RecordType filtering are the most common source of non-selective query warnings in Comms Cloud orgs.

- **Scalability** — Industries data models are designed to scale with Salesforce's standard platform capabilities. The object hierarchy (InsurancePolicy → InsurancePolicyCoverage, InsurancePolicyParticipant) distributes data across related objects, which scales better than flattening all policy data onto a single object with many fields.

## Architectural Tradeoffs

**Standard Industries objects vs. custom objects:** Standard Industries objects carry upgrade-safe behavior, OmniStudio integration support, and pre-built relationships. Custom objects give more schema flexibility but require maintaining all relationships, validations, and integrations from scratch. For any entity that maps cleanly to a standard Industries object, the standard object is always the right choice.

**Person Account vs. Contact for policyholder modeling (Insurance Cloud):** Insurance Cloud requires Person Accounts for individual policyholders because InsurancePolicyParticipant links to Account. This means enabling Person Accounts in the org, which is an irreversible org configuration change. Evaluate Person Account enablement as an architectural decision before go-live, not as an implementation detail.

**Record types vs. separate objects for Communications account subtypes:** Communications Cloud uses record types on Account rather than separate objects for account subtypes. This simplifies the data model and leverages existing Account infrastructure but requires disciplined query filtering. Alternative designs using custom objects for BillingAccount or ServiceAccount add schema complexity without benefit and break compatibility with standard Communications Cloud components.

## Anti-Patterns

1. **Custom objects that shadow standard Industries objects** — Creating `Policy__c`, `Coverage__c`, or `CarePlan__c` in an org that already has the corresponding standard Industries objects creates a parallel data model that diverges over time, produces integration mapping confusion, and cannot use standard OmniStudio or Industries Lightning components. Always audit the standard Industries object catalog before designing custom schema.

2. **Contact-centric participant modeling in Insurance Cloud** — Modeling policyholders, beneficiaries, and named insureds as Contacts (or Contact lookups) rather than Accounts contradicts the Insurance Cloud data model design and breaks every standard Insurance Cloud component and integration that reads participant data. This anti-pattern typically originates in migration design documents authored without Insurance Cloud-specific data model knowledge.

3. **Unfiltered Account queries in Communications Cloud** — Treating the Account object in a Communications Cloud org as a single-type object without RecordType filtering produces data integrity problems at every layer: reports, integrations, billing logic, and UI pages. This is the highest-frequency operational problem in Communications Cloud implementations and is directly preventable through consistent query discipline.

## Official Sources Used

- Insurance Policy Standard Objects — Salesforce Insurance Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.insurance_developer_guide.meta/insurance_developer_guide/insurance_standard_objects.htm
- Industries Data Models for Communications — Salesforce Help — https://help.salesforce.com/s/articleView?id=sf.comms_cloud_data_model.htm
- Health Cloud Object Reference — Salesforce Developer Documentation — https://developer.salesforce.com/docs/atlas.en-us.health_api.meta/health_api/health_api_reference.htm
- Energy & Utilities Cloud Data Model — Salesforce Help — https://help.salesforce.com/s/articleView?id=sf.eu_data_model.htm
- Communications Cloud Data Model Gallery — Salesforce Developer Documentation — https://developer.salesforce.com/docs/atlas.en-us.comms_cloud.meta/comms_cloud/comms_cloud_data_model.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
