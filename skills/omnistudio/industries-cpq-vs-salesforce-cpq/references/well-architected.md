# Well-Architected Notes — Industries CPQ vs Salesforce CPQ

## Relevant Pillars

- **Scalability** — The primary well-architected concern for CPQ selection. Industries CPQ's Calculation Procedures and catalog-item model are designed for catalogs with thousands of SKUs and complex attribute combinations. Salesforce CPQ's product-option model does not scale to the same depth without significant customization. Revenue Cloud's Scale Cache reduces SOQL pressure on the pricing engine. Choosing the wrong CPQ product for the org's catalog complexity creates a scalability ceiling that is expensive to remove later.
- **Operational Excellence** — CPQ selection directly drives long-term operational cost. Salesforce CPQ's managed-package deployment model means version upgrades are controlled by Salesforce's release schedule, not the org's. Industries CPQ's DataPack-based deployment requires OmniStudio tooling proficiency. Revenue Cloud's native-object model aligns with standard Salesforce DevOps tooling (SFDX, Metadata API) and reduces release complexity. Selecting the CPQ product that fits the org's DevOps maturity and team skills is an operational excellence decision.
- **Reliability** — Governor limits are a reliability risk for all three CPQ products. Industries CPQ Calculation Procedures run server-side and can cause timeout issues on very large carts. Salesforce CPQ's Quote Line Editor triggers pricing recalculations that can approach SOQL/DML limits on complex bundles. Revenue Cloud's Scale Cache is designed to improve reliability at scale. Reliability risk assessment must be part of CPQ selection for orgs with large transaction volumes.
- **Security** — CPQ products expose product catalog data and pricing logic. Salesforce CPQ uses standard CRUD/FLS enforcement on `SBQQ__` objects. Industries CPQ uses OmniStudio's runtime security model, which grants access through permission sets on OmniStudio components. Both models require explicit security review; neither provides security by default without proper permission set design.

## Architectural Tradeoffs

**Industries CPQ vs. Salesforce CPQ: Build vs. Buy for Industry Specificity**
Industries CPQ delivers industry-specific guided selling, attribute-based catalog, and order management flows out of the box for telco, energy, and insurance. The tradeoff is that it requires an OmniStudio licensing investment, OmniStudio-skilled developers, and a DataPack-based deployment discipline. For orgs already on an industry cloud, this cost is already paid. For orgs not on an industry cloud, this is a significant incremental investment that is only justified by the catalog complexity of the industry vertical.

**Salesforce CPQ Managed Package: Familiarity vs. Namespace Lock-in**
Salesforce CPQ is familiar, well-documented, and has a large partner ecosystem. The managed-package model means any customization referencing `SBQQ__` objects is coupled to the package. The tradeoff is acceptable for stable, long-running deployments. It becomes a liability when the org needs to migrate to Revenue Cloud, because the migration scope is proportional to how deeply `SBQQ__` is embedded in custom code, reports, and integrations.

**Revenue Cloud: Strategic Alignment vs. Feature Maturity Risk**
Revenue Cloud is the Salesforce-endorsed strategic path for enterprise CPQ. It removes namespace coupling and aligns with native platform tooling. The tradeoff is that it is newer and not yet feature-complete compared to the mature managed package. Orgs that adopt Revenue Cloud early gain strategic alignment but accept the risk of working around feature gaps.

## Anti-Patterns

1. **Selecting CPQ Based on Brand Familiarity Rather Than Business Model Fit** — Recommending Salesforce CPQ to a telco or utility because "we already know CPQ" ignores the fundamental mismatch between the product-option model and attribute-based catalog requirements. The correct approach is to match the CPQ engine to the catalog structure and industry vertical, not to the team's existing skill set.

2. **Treating End-of-Sale as an Emergency Migration Trigger** — Initiating an unplanned Revenue Cloud migration immediately after Salesforce CPQ's end-of-sale announcement introduces operational risk without proportional benefit. End-of-sale is not end-of-life. Migrations should be planned, phased, and tied to natural business change windows.

3. **Coexistence Without a Consolidation Roadmap** — Allowing both Industries CPQ and Salesforce CPQ to coexist indefinitely without a consolidation plan doubles the maintenance surface area, creates reporting fragmentation, and increases licensing cost over time. Any coexistence architecture must include a defined consolidation target.

## Official Sources Used

- Industries CPQ Help Documentation — https://help.salesforce.com/s/articleView?id=ind.comms_industries_configure__price__quote__cpq_.htm&type=5
- Download and Migrate Industries CPQ DataPacks — https://help.salesforce.com/s/articleView?id=ind.comms_download_and_migrate_industries_cpq_datapacks_to_salesforce_org.htm&type=5
- Industries CPQ Cart-Based APIs (Developer Guide) — https://developer.salesforce.com/docs/industries/cme/guide/comms-cart-based-apis-for-industries-cpq.html
- Salesforce CPQ Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_api.meta/cpq_dev_api/cpq_plugins_parent.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- OmniStudio Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm
