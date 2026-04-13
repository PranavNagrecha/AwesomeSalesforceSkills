# Well-Architected Notes — Insurance Cloud Architecture

## Relevant Pillars

- **Security** — Insurance data (policy details, coverage amounts, claim histories, beneficiary information) is regulated under state insurance data protection laws and, in some jurisdictions, GDPR. FSC Compliant Data Sharing must be configured for InsurancePolicy and related objects. Field-level security must restrict sensitive coverage fields from inappropriate profiles.
- **Reliability** — External rating engine integrations must be designed with retry logic and circuit-breaker patterns. Insurance workflows (quote, bind, claim intake) involve synchronous UX paths where external system latency directly impacts user experience. Async Integration Procedure patterns with error handling are required.
- **Performance Efficiency** — Insurance orgs with large policy portfolios face SOQL query design challenges on InsurancePolicy and InsurancePolicyCoverage. Selective indexes on status, effective date, and policyholder Account fields are necessary for agent workspaces.
- **Operational Excellence** — InsuranceUnderwritingRule lifecycle management (Draft → Active → Inactive) requires operational procedures and monitoring. Rules deployed in Draft status silently fail to evaluate — post-deployment validation is mandatory.

## Architectural Tradeoffs

**Salesforce as System of Record vs. Engagement Layer:** Many insurers have an existing policy administration system (Guidewire, Duck Creek). The key architectural decision is whether Salesforce owns the policy record of truth or acts as an engagement and service layer syncing from an external system. Salesforce as the engagement layer reduces data model complexity but requires robust bidirectional sync and conflict resolution design.

**Declarative underwriting vs. Apex underwriting:** InsuranceUnderwritingRule + Insurance Product Administration APIs provide a fully declarative, auditable underwriting framework but require OmniStudio licensing. Custom Apex can replicate decision logic but creates governance and audit gaps.

## Anti-Patterns

1. **Designing insurance workflows without confirming module licensing first** — Insurance Cloud modules are separately licensed and activated. Designs referencing Claims Management objects before the module is licensed result in rework and delayed go-lives. Always baseline the licensed module list before starting object model or workflow design.
2. **Putting underwriting logic in Flow decision elements** — Flow decision tables are not auditable via Insurance APIs, cannot be managed by business analysts, and cannot interface with external rating engines. Underwriting logic belongs in InsuranceUnderwritingRule and the Insurance Product Administration API.
3. **Using Contact-based relationships for policy participants** — InsurancePolicyParticipant links to Account (via PrimaryParticipantAccountId), not Contact. Architects who model participant roles as Contact relationships produce SOQL that fails and integrations that send the wrong ID types.

## Official Sources Used

- Salesforce Insurance Developer Guide v66.0 — https://developer.salesforce.com/docs/atlas.en-us.insurance_dev.meta/insurance_dev/insurance_dev_intro.htm
- Get Started With Financial Services Cloud for Insurance — https://help.salesforce.com/s/articleView?id=sf.fsc_admin_insurance_getting_started.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- FSC Compliant Data Sharing — https://help.salesforce.com/s/articleView?id=sf.fsc_admin_compliant_data_sharing.htm
