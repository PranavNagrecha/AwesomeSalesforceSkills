# Well-Architected Notes — Industries Insurance Setup

## Relevant Pillars

- **Security** — The FSC Insurance permission set license model enforces object-level and field-level access at the license tier, not just at the profile/permission set level. Insurance data (policies, claims, coverage) is highly regulated PII in most jurisdictions. Field-level security on InsurancePolicy, InsurancePolicyCoverage, and Claim objects must be reviewed against least-privilege principles. The Insurance Policy Administration Connect API endpoints use standard OAuth; no additional insurance-specific auth tokens are required, but API client scopes must include `api` and `connect` permissions. Shield Platform Encryption should be considered for fields like PolicyNumber and ClaimNumber in regulated environments.

- **Reliability** — The Connect API issue-policy endpoint (`POST /connect/insurance/policy-administration/policies`) is atomic for the InsurancePolicy + InsurancePolicyCoverage creation. However, it is subject to standard API rate limits and is not idempotent by default — duplicate POST calls can create duplicate policy records. OmniScript issue-policy steps should include idempotency checks (e.g., query for existing policy with same policy number before issuing). InsProductService.getRatedProducts is a synchronous Apex call and counts toward Apex CPU time limits in complex rating scenarios.

- **Scalability** — InsurancePolicyCoverage records scale linearly with policy volume. On orgs with millions of policies, SOQL queries on InsurancePolicyCoverage that lack indexed filters (PolicyId, CoverageType) will hit query timeout thresholds. Design batch renewal and endorsement jobs to process by PolicyId ranges, not full-table scans. The participant model (InsurancePolicyParticipant) introduces additional child records per policy — factor this into storage capacity planning.

- **Operational Excellence** — The managed-package to native-core transition requires operational discipline: track which platform path the org is on, document namespace differences, and establish a formal upgrade plan with Salesforce when native-core GA is reached. Insurance Settings irreversible decisions must be documented in an org configuration register (not just in deployment notes) so future administrators understand what was enabled and why. OmniScript versioning for quoting flows should follow a versioned activation pattern — never deactivate a quoting OmniScript version without confirming no in-flight quotes reference it.

## Architectural Tradeoffs

**Managed Package vs Native Core:** The managed-package Digital Insurance Platform is stable and documented but carries namespace overhead and managed-package upgrade dependencies. The native-core path is the strategic direction but is not fully GA for all features as of Spring '25. Orgs starting new implementations should confirm the current GA status of native-core features with their Salesforce AE before committing to the native-core path.

**OmniScript Quoting vs Screen Flow Quoting:** OmniScript provides the prebuilt `insOsGridProductSelection` LWC and native Remote Action integration with InsProductService. Screen Flow requires custom Apex actions to call InsProductService and custom LWC for product display. OmniScript is the recommended path for insurance quoting because it is the path that receives prebuilt component investment from Salesforce. Screen Flow is acceptable only if OmniStudio is not licensed.

**Atomic Connect API Issuance vs Manual DML:** The Connect API issue-policy endpoint creates InsurancePolicy + InsurancePolicyCoverage atomically. Manual Apex DML requires the developer to correctly manage parent-child record creation, rollback on failure, and coverage record completeness validation. The Connect API is the recommended path — it encapsulates this logic and is the path tested and supported by Salesforce Insurance engineering.

## Anti-Patterns

1. **Treating Insurance Settings as reversible admin toggles** — Enabling irreversible settings (many-to-many relationships, multiple producers) without architectural sign-off and then discovering mid-project that the wrong model was chosen. Correct approach: document the participant model before touching Insurance Settings; treat every toggle as a permanent architectural decision.

2. **Using standard CPQ or generic REST for insurance quoting and issuance** — Building quoting with Pricebook/QuoteLineItem or issuing policies via generic DML. These approaches produce incomplete insurance object graphs (missing coverage records, missing participant records, missing clause records) that break renewals, endorsements, billing integration, and regulatory reporting. Correct approach: use InsProductService for rating and the Insurance Policy Administration Connect API for issuance.

3. **Mixing managed-package and native-core namespace references** — Configuring OmniScript Remote Actions with class names from documentation that applies to the other platform path. Correct approach: determine the platform path at project start, document it, and use only path-appropriate references throughout.

## Official Sources Used

- Salesforce Help: Set Up Insurance for Financial Services Cloud — https://help.salesforce.com/s/articleView?id=sf.fsc_admin_insurance_setup.htm
- Salesforce Insurance Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.insurance_dev_guide.meta/insurance_dev_guide/insurance_dev_guide_intro.htm
- Insurance Policy Administration Connect API Reference — https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/connect_resources_insurance_policy_admin.htm
- Trailhead: Insurance for FSC Admin Essentials — https://trailhead.salesforce.com/content/learn/modules/insurance-for-fsc-admin-essentials
- Trailhead: Insurance Policy and Claim Details Setup — https://trailhead.salesforce.com/content/learn/modules/insurance-policy-and-claim-details-setup
- Trailhead: Create OmniScripts for Quoting — https://trailhead.salesforce.com/content/learn/modules/create-omniscripts-for-quoting
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference: InsurancePolicy — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_insurancepolicy.htm
