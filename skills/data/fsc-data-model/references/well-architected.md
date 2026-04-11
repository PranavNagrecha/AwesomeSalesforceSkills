# Well-Architected Notes — FSC Data Model

## Relevant Pillars

- **Reliability** — The FSC rollup framework is asynchronous and batch-driven. A reliable implementation ensures rollup batches are scheduled, monitored, and re-triggered after bulk data operations. Household financial summaries must be treated as eventually consistent, not real-time.
- **Performance Efficiency** — Financial account and holding queries at household scale can return hundreds of records per household. Reading pre-computed rollup fields on the household Account is the correct pattern for aggregate display; real-time SOQL aggregation does not scale. Selective SOQL with indexed fields (`PrimaryOwner__c`, `AccountId` on ACR) is essential for advisor dashboards.
- **Security** — FSC financial objects carry sensitive personal financial data. The FSC Compliant Data Sharing framework and object-level security settings on `FinServ__FinancialAccount__c` and `FinancialAccountParty` control advisor visibility. Do not bypass FSC sharing by querying financial data in system-mode Apex without explicit business justification.
- **Scalability** — Household size and the number of financial accounts per household grow over time. The data model choice (Core FSC `FinancialAccountParty` vs. managed-package two-lookup model) directly affects how many ownership relationships can be represented. Multi-owner use cases must be scoped before choosing the deployment type.
- **Operational Excellence** — The FSC data model is a versioned managed-package or a platform-native schema. Either way, namespace consistency must be enforced across all metadata artifacts (SOQL, Apex, Flow, Reports, Dashboards). Mixed-namespace references cause deployment failures. Automated checks (see `scripts/check_fsc_data_model.py`) catch namespace mismatches before they reach production.

## Architectural Tradeoffs

**Core FSC vs. Managed-Package FSC:**
Core FSC offers standard-object flexibility and unlimited ownership via `FinancialAccountParty`, but it is only available for new orgs. Managed-package FSC has a wider ecosystem of AppExchange integrations and ISV tools built against the `FinServ__` namespace. The choice is irreversible without a full data migration — make it at project inception, not mid-implementation.

**Async Rollup Reliability:**
The FSC rollup engine's async nature means displayed totals are only as fresh as the last batch run. For real-time use cases (e.g., a trading platform displaying live net worth), the FSC rollup model is inappropriate and a different architecture (streaming aggregation, external data platform) is needed. Document the eventual-consistency characteristic explicitly in UI designs and user training.

**FinancialAccountParty Unlimited Ownership:**
Core FSC's unlimited ownership model is architecturally cleaner for complex trusts and partnerships, but it introduces query complexity — retrieving all owners of an account requires a subquery through the junction object rather than a simple field read. This is a worthwhile tradeoff for orgs with genuine multi-owner needs.

## Anti-Patterns

1. **Replicating FSC Rollup Logic with Native Salesforce Tooling** — Attempting to use native ROLLUP summary fields, Process Builder, or Flow to aggregate financial account data to the household Account bypasses the FSC rollup engine and produces inconsistent or zero results. The FSC rollup batch is the only supported mechanism for maintaining household financial totals in FSC-governed orgs.

2. **Writing FSC Code Before Confirming Deployment Type** — Generating SOQL, Apex, or Flow that references `FinServ__` objects without first verifying the org's installed packages produces code that fails entirely in Core FSC orgs. Namespace-agnostic abstractions or explicit org-type checks must be built in for any tooling intended to work across FSC deployment types.

3. **Conflating FSC Household with NPSP Household** — Applying NPSP household concepts, rollup utilities, or record type assumptions to an FSC implementation produces a broken data model. The two products are architecturally distinct. Household in FSC is a standard Business Account with `AccountContactRelation`-based membership; NPSP household uses its own object model.

## Official Sources Used

- Financial Services Cloud Data Model — Salesforce Help: https://help.salesforce.com/s/articleView?id=sf.fsc_data_model.htm
- Financial Services Cloud Developer Guide — Salesforce Developer Docs: https://developer.salesforce.com/docs/atlas.en-us.financial_services_cloud_dev.meta/financial_services_cloud_dev/
- Industries Common Resources Developer Guide v66.0 — Salesforce Developer Docs: https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/
- Financial Services Cloud Object Reference — Salesforce Developer Docs: https://developer.salesforce.com/docs/atlas.en-us.financial_services_cloud_dev.meta/financial_services_cloud_dev/fsc_dev_object_reference.htm
- Salesforce Well-Architected Framework: https://architect.salesforce.com/well-architected/overview
