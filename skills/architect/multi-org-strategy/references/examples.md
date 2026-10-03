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

- The US hub defines a Salesforce Connect external data source with a custom adapter (`ExternalDataSource` type `ApexClassId`, built with the Apex Connector Framework) that calls an Apex REST resource in the EU org returning only aggregates. The hub displays EU pipeline totals without replicating EU personal data. (Corrected wording: the data source lives in the reading org, not the EU org. The cross-org adapter, type `SfdcOrg`, was not used because it would surface EU records, including personal data, rather than aggregates.)
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

---

## Example 4: Decision Record For A Two-Year Hub-And-Spoke After An Acquisition

**Context:** A manufacturer (hub org, Unlimited Edition, 900 Salesforce licences) acquires a distributor whose org (spoke, Enterprise Edition, 40 Salesforce licences) has two accepted Salesforce to Salesforce connections publishing Accounts and Opportunities into the hub. The distributor's contracts require its customer data to stay in its own org until the contracts are re-papered, which legal dates to the end of next year.

**Step 1: inventory, run in both orgs.**

```soql
-- S2S connections (fails with "sObject type not supported" where S2S was never enabled)
SELECT ConnectionName, ConnectionStatus, ConnectionType, ReplicationRole, ResponseDate
FROM PartnerNetworkConnection

-- Records currently shared through each connection
SELECT ConnectionId, COUNT(Id) records
FROM PartnerNetworkRecordConnection
WHERE EndDate = null
GROUP BY ConnectionId
```

UNVERIFIED (2026-10-03): `PartnerNetworkRecordConnection` lists `create()` and `query()` as supported calls, but whether `COUNT()` with `GROUP BY ConnectionId` is accepted on it was not confirmed; fall back to a plain query and count client-side if the aggregate is rejected.

**Step 2: the allocation arithmetic** (Limits Quick Reference, Total API Request Allocations):

| Org | Edition | Licences | 24-hour inbound allocation |
|---|---|---|---|
| Hub | Unlimited | 900 Salesforce | 100,000 + 900 x 5,000 = 4,600,000 |
| Spoke | Enterprise | 40 Salesforce | 100,000 + 40 x 1,000 = 140,000 |

Every call into the spoke, from every integration, shares the 140,000.

**Step 3: the decision record** at `docs/adr/0042-distributor-org-hub-and-spoke.md`.

```markdown
# ADR-0042: Keep the distributor org as a spoke until contract re-papering; retire S2S

## Status
Accepted (2026-10-03), Enterprise Architecture Board

## Context
- Distributor contracts require its customer data to stay in its org
  until re-papered (legal estimate: 2027-12-31).
- Two accepted PartnerNetworkConnection records (Accounts, Opportunities)
  publish into the hub. No owner, no retry, no monitoring.
- Spoke inbound allocation: 140,000 calls per 24 hours for everything.
- Hub sales leaders need distributor pipeline on hub Account pages.
- Price books are mastered in the hub; the spoke re-keys them by hand.

## Decision
1. Topology: hub-and-spoke for 24 months, then migrate the spoke into
   the hub and decommission it.
2. Systems of record: Account and Opportunity for distributor customers
   stay in the spoke. Product2 and Pricebook2 are mastered in the hub.
3. Pipeline in the hub: Salesforce Connect cross-org adapter.
   ExternalDataSource Distributor_Org, type SfdcOrg, isWritable false,
   principalType NamedUser (integration user dist_xorg_reader in the
   spoke, read-only permission set, excluded from leaver automation).
4. Price data to the spoke: nightly Bulk API 2.0 ingest job from the
   hub's middleware into the spoke, upsert on Product2.Hub_Product_Id__c.
   Estimated 3,000 rows per night; a handful of API calls per run.
5. Retire both S2S connections after 30 days of parallel run.
6. Identity: Microsoft Entra ID as IdP; one SamlSsoConfig per org with
   that org's My Domain login URL as samlEntityId; Federation ID mapping;
   JIT off. Deprovisioning: IdP provisioning connector to both orgs plus
   a weekly reconciliation of IdP leavers against active users.

## Consequences
### Positive
- No cross-org writes; the spoke keeps sole ownership of its customers.
- Spoke API use drops from per-record S2S traffic to page-view reads
  plus one nightly job.
### Negative
- Hub automation cannot react to spoke Opportunity changes: external
  objects take no Apex triggers. Alerts must originate in the spoke.
- No roll-up of distributor pipeline onto hub Accounts; totals live in
  CRM Analytics through the Salesforce External Connector.
- Every hub page view of distributor pipeline is a live call into the
  spoke and counts against its 140,000 allocation.
- Salesforce Connect is a separately licensed add-on in the hub.

## Alternatives Considered
### Keep S2S
Rejected: connection lifecycle with no supported growth path; nobody
owns it; no retry or monitoring.
### Replicate distributor Accounts and Opportunities into the hub nightly
Rejected: moves customer data out of the spoke before re-papering.
### Merge the orgs now
Rejected: blocked by the contractual data location requirement.

## Review Trigger
Contract re-papering complete, or 2027-12-31, whichever comes first.
Owner: Head of CRM Platform.
```

UNVERIFIED (2026-10-03): that Salesforce Connect is a separately licensed add-on comes from Salesforce Help and pricing pages, which do not fetch; confirm with the account team before the record is accepted.

**Step 4: the cross-org data source, deployed to the hub** at `force-app/main/default/dataSources/Distributor_Org.dataSource-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExternalDataSource xmlns="http://soap.sforce.com/2006/04/metadata">
    <authProvider>Distributor_Org_Auth</authProvider>
    <customConfiguration>{"apiVersion":"67.0","environment":"CUSTOM","searchEnabled":"true","timeout":"120"}</customConfiguration>
    <endpoint>https://distributor.my.salesforce.com</endpoint>
    <isWritable>false</isWritable>
    <label>Distributor Org</label>
    <principalType>NamedUser</principalType>
    <protocol>Oauth</protocol>
    <type>SfdcOrg</type>
</ExternalDataSource>
```

`type`, `customConfiguration` keys, `isWritable`, `principalType`, `protocol`, and the `.dataSource` suffix in the `dataSources` folder are from the Metadata API ExternalDataSource reference; `authProvider` references an `AuthProvider` of `providerType` `Salesforce`. UNVERIFIED (2026-10-03): the reference's cross-org sample shows only `"environment":"CUSTOM"`; other values for production or sandbox login endpoints were not confirmed. The OAuth grant for the named user is completed in Setup after deployment, which this file cannot carry; that step is documented in Salesforce Help only.

**Step 5: release manifest members** (types from the Metadata API; member names are this org's):

| Component | Org | Type | `package.xml` member form |
|---|---|---|---|
| Cross-org data source | Hub | `ExternalDataSource` | `<members>Distributor_Org</members><name>ExternalDataSource</name>` |
| Auth provider for the data source | Hub | `AuthProvider` | `<members>Distributor_Org_Auth</members><name>AuthProvider</name>` |
| External object for spoke Opportunities | Hub | `CustomObject` | `<members>Distributor_Opportunity__x</members><name>CustomObject</name>` |
| Middleware connected app | Spoke | `ConnectedApp` | `<members>Hub_Price_Sync</members><name>ConnectedApp</name>` |
| SAML configuration | Each org | `SamlSsoConfig` | `<members>Entra_ID</members><name>SamlSsoConfig</name>` |
| Reader permission set | Spoke | `PermissionSet` | `<members>Distributor_XOrg_Reader</members><name>PermissionSet</name>` |

External objects deploy as `CustomObject` with the `__x` suffix ("In Metadata API, external objects are represented by the CustomObject metadata type"; Object Reference: external object API names end in `__x`).

**Why it works:** the record ties every choice to a constraint that can be checked (the contract date, the 140,000-call allocation, the no-trigger rule on external objects), names the objects and users each org depends on, and states the date the topology is meant to end.

