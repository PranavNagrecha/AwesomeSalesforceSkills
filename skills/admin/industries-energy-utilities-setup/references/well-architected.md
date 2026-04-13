# Well-Architected Notes — Industries Energy Utilities Setup

## Relevant Pillars

- **Reliability** — E&U Cloud setup directly governs billing cycle integrity. Incomplete CIS integration, null RatePlan references on ServiceContracts, and incorrectly configured market type settings all produce silent failures that surface during billing runs — potentially weeks after initial setup. A reliable setup requires validating all integration dependencies before creating dependent records, and testing the full billing cycle in a sandbox before production deployment.
- **Security** — Industry objects (ServicePoint, Meter, ServiceContract, RatePlan) carry customer utility data and tariff information that is subject to data privacy requirements in most regulated and competitive market jurisdictions. OWD sharing settings for these objects must be configured explicitly; default OWD settings from standard Salesforce do not carry over to industry objects. Role hierarchy and sharing rules must be reviewed separately for each industry object.
- **Operational Excellence** — The setup sequence (license activation → permission sets → CIS integration → ServicePoint → Meter → ServiceContract) must be documented and repeatable. Environment-specific variation (regulated vs competitive market) must be captured in the setup checklist, not assumed. Runbook documentation should include CIS sync validation steps as a pre-flight check before any billing-relevant configuration.

## Architectural Tradeoffs

**CIS as authoritative source vs Salesforce-native rate plan management:** The most significant architectural tradeoff in E&U Cloud setup is deciding whether the external CIS owns rate plan definitions or whether Salesforce manages them natively. In nearly all regulated utility implementations, the CIS is legally and operationally authoritative for tariff definitions — Salesforce should synchronize from the CIS, not override it. In some competitive market implementations, Salesforce may serve as a rate plan catalog alongside or upstream of the CIS. This decision must be made before building the CIS integration, because it determines the data flow direction and which system triggers rate plan changes.

**ServicePoint granularity:** A single customer Account may have many ServicePoints (e.g., a large commercial customer with 50 metered locations). The decision of how to model the Account-to-ServicePoint relationship affects query performance, sharing rule design, and service order volume. In high-volume implementations, the one-to-many Account-ServicePoint relationship requires indexing on ServicePoint.AccountId and pagination strategies for related list components.

## Anti-Patterns

1. **Setting up E&U Cloud before CIS integration is operational** — Creating ServiceContracts without confirmed RatePlan sync from the CIS produces null RatePlan references that silently break billing. The correct approach is to treat CIS integration as a prerequisite for ServiceContract creation, not a parallel workstream.

2. **Using standard Salesforce permission sets instead of managed package permission sets** — Granting object CRUD on E&U Cloud objects via custom permission sets does not provide access to managed package functionality, OmniStudio integrations, or industry-specific UI components. Always assign the E&U Cloud managed package permission sets.

3. **Reusing regulated-market configuration templates in competitive-market orgs** — Market type is a structural setup decision, not a data value. Applying the wrong market configuration template produces ServicePoint records that appear complete but fail in service order and billing workflows.

## Official Sources Used

- Energy and Utilities Cloud Data Model — https://help.salesforce.com/s/articleView?id=sf.eu_data_model.htm
- Energy and Utilities Cloud Developer Guide Spring 26 — https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/energy_utilities_cloud.pdf
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
