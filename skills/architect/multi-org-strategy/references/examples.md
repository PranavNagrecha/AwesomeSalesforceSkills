# Examples — Multi-Org Strategy

---

## Example 1: Global Enterprise with GDPR-Mandated EU Data Residency

### Situation

A US-headquartered financial services firm uses a single Salesforce production org (US region) for all sales and service operations globally. Their European legal team determines that personal data for EU-resident customers must remain within EU data center boundaries at all times to comply with GDPR Article 46 data transfer restrictions. The existing US org cannot satisfy this requirement through configuration alone because Hyperforce regional data residency was not available in their contract edition at the time of assessment.

The firm has approximately 8,000 EU customer records, 200 EU-based sales reps, and a service team of 50 in Frankfurt. EU and US business processes are operationally separate — no US rep is assigned to an EU account and no EU rep is assigned to a US account.

### Architecture Decision

A second production org is provisioned in the EU (Hyperforce Frankfurt). The US org remains the system of record for US and global accounts. The EU org is the system of record for EU-domiciled customer accounts.

**Org topology:** Hub-and-spoke. The US org acts as hub for global reporting. The EU org is a spoke with full operational independence for EU processes.

**Data exchange design:**

- EU org exposes a Salesforce Connect external data source (custom adapter) so the US hub can display EU aggregate pipeline data without replicating EU personal data into the US org.
- Only non-personal aggregate data (pipeline value by region, win rates, deal counts) flows from EU to US, avoiding cross-border personal data transfer.
- Product catalog and price book data are mastered in the US org and replicated nightly to the EU org via Bulk API 2.0 (no personal data involved in this flow).

**Authentication:**
- EU org: Connected App with OAuth 2.0 JWT Bearer. Certificate stored in the US org's Named Credential.
- Integration user in EU org is a dedicated service account with minimum required permissions (no UI access, no Chatter, no reports).

**SSO:** Both orgs are registered as Service Providers in the firm's existing Okta tenant. Users authenticate once; Okta issues SAML assertions to whichever org the user navigates to. SCIM provisioning from Okta handles user creation and deactivation across both orgs automatically — removing the manual risk of leaving active EU org users when an employee is terminated.

**License implications:** 200 EU reps require 200 Sales Cloud licenses in the EU org. They do not require seats in the US org (they never log into it). The 50 service reps in Frankfurt require Service Cloud licenses in the EU org.

### Key Lessons

- The EU org was justified by a specific legal requirement, not by a preference for separation. This is documented in the architecture decision record.
- Personal data does not cross org boundaries — only aggregated, non-personal data flows from EU to US.
- SSO and SCIM eliminate the biggest operational risk of multi-org: orphaned active accounts after termination.
- Hyperforce regional selection should be re-evaluated at contract renewal — if it satisfies the regulator, collapsing back to single-org is the preferred long-term direction.

---

## Example 2: Post-M&A Integration — Two Acquired Companies on Separate Salesforce Orgs

### Situation

A mid-market SaaS company (the acquirer) runs its sales and support operations in a single Salesforce org. It acquires two companies within 18 months of each other:

- **AcquiCo A**: B2B software, 150 sales reps, heavy Salesforce CPQ customization, 3 years of opportunity history.
- **AcquiCo B**: Professional services, 80 consultants, light Salesforce usage (Accounts, Contacts, Cases only), 1 year of history.

Both acquisitions arrive with their own Salesforce production orgs. The acquirer's CTO wants a single Salesforce org within 24 months but needs a transition architecture that keeps all three orgs operational while migration planning proceeds.

### Transition Architecture

**Phase 1 (months 1–6): Stabilize and inventory**

- Map the data model in all three orgs. Identify objects, fields, and custom metadata that have equivalents across orgs.
- Do not integrate the orgs yet. Resist pressure to "just connect them with Salesforce-to-Salesforce" — S2S creates a coupling that makes migration harder.
- Stand up a shared Okta SSO configuration. All three orgs become Service Providers under the same Okta tenant.
- Audit users: identify any users who appear in more than one org and standardize their email/username format.

**Phase 2 (months 6–18): Selective cross-org reporting**

- The acquirer's RevOps team needs consolidated pipeline reporting across all three orgs.
- Solution: CRM Analytics with three data connectors (one per org). No Salesforce-to-Salesforce. No record replication.
- Each org's integration user authenticates via Named Credential (JWT Bearer) from the CRM Analytics connector.
- This provides consolidated reporting without creating cross-org data coupling.

**Phase 3 (months 18–24): Migration**

- AcquiCo B (light usage) migrates first. Its Accounts, Contacts, and Cases are migrated into the acquirer's org via Data Loader / Bulk API 2.0. B's org is decommissioned.
- AcquiCo A's CPQ migration is more complex. A phased migration plan treats CPQ configuration separately from transactional data.
- During migration overlap, a one-way record sync (AcquiCo A → acquirer org) uses Bulk API 2.0 nightly jobs for new Opportunity records only.

### Key Lessons

- Salesforce-to-Salesforce was explicitly avoided even though it was the "easy" button — it would have created technical debt that slowed migration.
- CRM Analytics connectors provided cross-org reporting without data replication, satisfying RevOps while keeping the architecture clean.
- SSO was the first integration work done because it provided the most value (user experience) with the lowest migration complexity.
- The multi-org state is treated as temporary by design. Every architectural decision was evaluated against the question: "does this make the eventual single-org easier or harder?"

---

## Example 3: ISV Partner Org — Shared Platform, Isolated Tenant Data

### Situation

A Salesforce ISV builds a field service scheduling product distributed as a managed package. They need a "platform org" for their own internal operations (their sales team selling the product) and a separate "packaging org" for developing, versioning, and distributing the managed package. These are genuinely separate orgs with no data overlap.

### Architecture

**Packaging org:** Development-only org. No end-customer data. Houses the managed package namespace, code, and components. Accessed only by the ISV's engineering team.

**Platform (sales) org:** Houses the ISV's own CRM data — prospects, customers, contracts. Runs the released version of their own product as a subscriber (dogfooding).

**No cross-org data exchange is needed.** The two orgs serve entirely separate purposes. The only link is that the platform org installs the managed package from the packaging org via AppExchange — a package installation, not an integration.

**Authentication:** Each org has its own SSO configuration. Engineering team members who need access to both orgs have separate user records in each, authenticated through the same Okta tenant.

### Key Lessons

- This is a valid multi-org pattern because the two orgs have genuinely different purposes with no data overlap.
- No integration was required between the orgs — the temptation to "sync customer data from platform org into packaging org for testing" was avoided; sandboxes serve that purpose.
- Packaging org governance: strict change management; no ad-hoc metadata changes; all changes go through a formal namespace release process.
