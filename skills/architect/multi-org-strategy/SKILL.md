---
name: multi-org-strategy
description: "Use when deciding whether to use multiple Salesforce production orgs, designing a hub-and-spoke integration topology, reviewing an existing multi-org architecture for risk, or troubleshooting cross-org integration failures. Trigger phrases: 'should we have separate Salesforce orgs', 'how do we share data between two orgs', 'we acquired a company that uses Salesforce', 'our EU data must stay in Europe', 'cross-org integration keeps hitting API limits', 'Salesforce-to-Salesforce stopped working', 'how do we do SSO across multiple orgs'. NOT for sandbox strategy (use sandbox-strategy). NOT for individual integration callout implementation (use integration/ skills). NOT for Named Credential configuration in isolation (use integration/named-credentials-and-callouts)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Scalability
  - Reliability
  - Operational Excellence
tags:
  - multi-org
  - org-strategy
  - hub-and-spoke
  - salesforce-to-salesforce
  - named-credentials
  - external-objects
  - salesforce-connect
  - sso
  - data-residency
  - connected-app
  - org-topology
  - architecture-decision
triggers:
  - "should we use separate Salesforce orgs or keep everything in one org"
  - "we acquired a company running on Salesforce — how do we handle two orgs"
  - "our EU data residency requirement forces a separate Salesforce org in Europe"
  - "how do we share records or data between two different Salesforce production orgs"
  - "Salesforce-to-Salesforce is hitting our API limits — what should we use instead"
  - "users need to log in to multiple Salesforce orgs — how do we do SSO across all of them"
  - "our org topology has grown to five orgs and nobody understands how data flows between them"
inputs:
  - "Business justification for considering multiple orgs (regulatory, M&A, business unit separation, etc.)"
  - "Data classification and residency requirements per region or business unit"
  - "Current org inventory with descriptions of what each org owns"
  - "Integration touchpoints: which orgs need to share data, in which direction, at what frequency"
  - "User base: do users need access to more than one org? How are identities managed today?"
  - "License footprint: how many licenses exist in each org?"
  - "Whether Salesforce-to-Salesforce (S2S) is currently in use"
outputs:
  - "Go/no-go recommendation on adding or maintaining multiple production orgs, with explicit reasoning"
  - "Recommended org topology (single org, hub-and-spoke, or peer-to-peer) with tradeoffs"
  - "Integration pattern recommendation per org pair (REST API, Bulk API, External Objects via Salesforce Connect)"
  - "Named Credential and Connected App design for cross-org OAuth"
  - "SSO design: shared IdP configuration, user provisioning strategy across orgs"
  - "Risk register: governor limit exposure, user management duplication, licensing implications"
  - "Callout of legacy Salesforce-to-Salesforce usage with migration path"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

Use this skill when evaluating whether to use multiple Salesforce production orgs, designing how those orgs will exchange data, reviewing an existing multi-org architecture for hidden risks, or troubleshooting cross-org integration failures. This skill addresses the structural decision layer — it does not replace role-specific skills for building individual integrations, configuring Named Credentials, or setting up SSO providers.

---

## Before Starting

- **What is the actual driver?** Regulatory data residency, M&A, distinct business unit with no data overlap, or has "we should have separate orgs" become an assumption without a justification? The answer shapes everything.
- **Is this really a sandbox question?** Development, QA, and UAT isolation is handled by sandboxes — not by separate production orgs. If the conversation is about dev/prod separation, use the sandbox-strategy skill instead.
- **What data needs to cross org boundaries?** If the answer is "most of it," that is a signal that multiple orgs may be the wrong call.
- **Who manages user access across the orgs?** Deactivation, permission changes, and onboarding must be replicated independently in each org unless an external IdP handles provisioning.

---

## Core Concepts

### Single Org Is the Default Recommendation

Salesforce architects strongly recommend single-org architecture unless a specific, documented requirement justifies multiple orgs. A single org eliminates:

- Cross-org data synchronization overhead (no API calls, no sync jobs, no eventual consistency risk)
- User management duplication (one user record, one deactivation action, one permission set assignment)
- Licensing complexity (licenses belong to one org; none are shared across orgs)
- Governor limit exposure from cross-org callouts (each callout consumes limits on both sides)
- Deployment coordination across two or more separate release pipelines

When requirements can be satisfied inside a single org using standard multi-tenancy features (Sharing Rules, Record Types, Permission Sets, Business Units in Marketing Cloud), a single org is always the lower-risk, lower-cost path.

### When Multiple Production Orgs Are Justified

Multiple production orgs are justified only when a single org structurally cannot satisfy the requirement:

| Scenario | Justification | Notes |
|---|---|---|
| Regulatory data residency | EU GDPR or similar law requires that personal data remain in a specific geographic region and Salesforce's Hyperforce region selection in a single org does not satisfy the regulator | Verify with Salesforce Account team whether Hyperforce resolves the requirement before committing to a second org |
| Distinct business units with zero data overlap | Two fully independent companies or brands that happen to share a Salesforce contract, but share no customers, users, or processes | Rare in practice; most BU separation is handled with Sharing Rules and Permission Sets |
| M&A integration (transitional state) | An acquired company runs a separate Salesforce org and migration into the acquiring org has not yet been completed | Treat this as a temporary state with a migration plan; do not design permanent multi-org architectures around M&A without a clear end state |
| Independent ISV product with tenant isolation | A product sold to external customers requires strict data isolation per customer (not just Sharing Rules) | ISV-specific pattern; consult Salesforce ISV architect guidance |

### What Multiple Orgs Do NOT Solve

- **Development vs. production isolation**: That is sandboxes. Use sandboxes.
- **Performance problems in a single org**: Multiple orgs do not redistribute governor limits in a meaningful way; they duplicate them.
- **Large data volume concerns**: LDV strategies (indexes, archival, Big Objects, skinny tables) are the correct approach inside a single org.

---

## Mode 1: Design a Multi-Org Strategy from Scratch

Use this mode when a new org topology is being designed before any build begins.

### Step 1 — Confirm the multi-org justification

Ask the client or stakeholder to provide a written requirement that a single org cannot satisfy. If they cannot articulate one, default to single-org architecture. Document the justification in the architecture decision record.

### Step 2 — Select an org topology

**Option A: Single Hub Org**
All business processes live in one production org. Cross-system data exchange is handled via Salesforce APIs to external systems (non-Salesforce). This is the preferred end state.

**Option B: Hub-and-Spoke**
One "hub" org aggregates and coordinates data from multiple "spoke" orgs. The hub holds canonical records or reporting aggregates. Spoke orgs hold domain-specific data.

- Hub-to-spoke and spoke-to-hub data flow uses REST API or Bulk API 2.0 — not Salesforce-to-Salesforce.
- Salesforce Connect (External Objects) in the hub org can surface spoke data as virtual records without full replication.
- The hub org's integration user must have a Connected App in each spoke org with appropriate OAuth scopes.

**Option C: Peer-to-Peer**
Two or more orgs exchange data directly with no central coordinator. This topology has the highest complexity and is the hardest to govern. Avoid it unless the orgs have truly independent data domains with only occasional cross-org lookups.

### Step 3 — Design cross-org data exchange

For each org pair that must exchange data:

1. **Choose the integration mechanism:**
   - REST API: preferred for record-by-record or small-batch synchronous exchange
   - Bulk API 2.0: preferred for large-volume nightly or periodic sync jobs (millions of records)
   - Salesforce Connect (External Objects): preferred for near-real-time cross-org lookup without full replication; data is queried on-demand via OData 2.0/4.0 adapter or a custom adapter

2. **Authenticate with Named Credentials:**
   - Create a Connected App in the target org (the org being called).
   - Create a Named Credential in the calling org that stores the OAuth 2.0 JWT Bearer credentials for that Connected App.
   - Never store client secrets, access tokens, or refresh tokens in Custom Settings, Custom Metadata, or Apex code.
   - Use the JWT Bearer flow (server-to-server, no user interaction) for scheduled or automated cross-org calls.

3. **Define data ownership:**
   - Each record has exactly one system of record. The owning org creates and updates it. Other orgs read or receive copies.
   - Avoid bidirectional sync unless absolutely required; bidirectional sync requires conflict resolution logic and has no native Salesforce support.

### Step 4 — Design identity and SSO

- Use an external IdP (Okta, Azure AD, Ping) as the SSO provider for all orgs.
- Configure each Salesforce org as a separate Service Provider (SP) registered with the same IdP.
- Users authenticate once against the IdP and receive a SAML assertion for the target org.
- User provisioning (SCIM) from the IdP to each org automates account creation and deactivation.
- Do not rely on manual admin processes to deactivate users across orgs — deactivation in one org does not deactivate in another.

### Step 5 — Account for licensing

- Each Salesforce production org requires its own license allocation.
- Licenses are not shared across orgs. A user who needs access to two orgs requires two license seats.
- Validate the license implications with the Salesforce Account team before finalizing the topology.

---

## Mode 2: Review an Existing Multi-Org Architecture

Use this mode when reviewing an inherited or in-flight multi-org design for risks and improvement opportunities.

#
## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

- [ ] **Justification is documented:** Each production org has a written requirement that a single org cannot satisfy. If not, consolidation should be evaluated.
- [ ] **No Salesforce-to-Salesforce (S2S) in active use for new integrations:** S2S is a legacy feature. Any active S2S connections should have a migration plan to REST API + Named Credentials.
- [ ] **Named Credentials used for all cross-org callouts:** No hard-coded org IDs, client secrets, or access tokens in Apex, Custom Settings, or Custom Metadata.
- [ ] **Connected Apps scoped correctly:** Each Connected App grants the minimum required OAuth scopes. Avoid `full` scope.
- [ ] **Data ownership is defined:** Each record type has exactly one system of record. Bidirectional sync is explicitly documented and has conflict resolution logic.
- [ ] **User deactivation process spans all orgs:** When a user is offboarded, the process covers every org they have access to (or the IdP SCIM push handles it automatically).
- [ ] **Governor limit budget is understood:** Cross-org callouts consume Apex callout limits (100 callouts per transaction), HTTP limits, and SOQL limits on both sides. The design should account for peak load.
- [ ] **External Objects are used for read-only cross-org lookup:** If an org only needs to display data from another org without owning it, Salesforce Connect is lower overhead than full record replication.
- [ ] **Bulk API 2.0 used for high-volume sync:** Nightly or periodic sync of more than a few thousand records should use Bulk API 2.0, not REST API row-by-row.

---

## Mode 3: Troubleshoot Multi-Org Integration Problems

Use this mode when cross-org integrations are failing, hitting limits, or behaving inconsistently.

### Diagnostic Table

| Symptom | Likely cause | Where to look |
|---|---|---|
| Cross-org callout hitting API limit | Both orgs consuming callout limits simultaneously; or S2S hitting SOAP API limits on both ends | Debug logs on calling org (check `CALLOUT_REQUEST`/`CALLOUT_RESPONSE`); API Usage in target org Setup |
| Named Credential OAuth token expired or invalid | JWT certificate rotation or Connected App scope change | Named Credential config in calling org; Connected App session policies in target org |
| External Object query returning no rows | OData adapter endpoint URL changed; target org API version mismatch; integration user permission revoked | Salesforce Connect external data source setup; Check integration user profile and permission set in target org |
| Hard-coded org ID causing failures in new environment | Org ID embedded in Apex, Custom Settings, or Flow | Search Apex source for 18-char Salesforce org ID pattern; check Custom Settings and Flow variable defaults |
| Salesforce-to-Salesforce connection broken after org refresh | S2S connections are environment-specific; sandbox refresh resets them | Migrate off S2S; use Named Credentials + REST API instead |
| Users can SSO into one org but not the other | SP configuration mismatch in IdP; Entity ID or ACS URL wrong for second org | SAML settings in both orgs; IdP application configuration |
| Sync job creates duplicates | No deduplication key defined; bidirectional sync without conflict resolution | Upsert key selection on target org; review sync job logic for idempotency |
| Bulk API 2.0 job failing for cross-org data load | Integration user lacks bulk API permission; field-level security on target org blocking fields | Integration user profile in target org; Bulk API permission set assignment |

---

## Integration Pattern Decision Matrix

| Scenario | Recommended Pattern |
|---|---|
| Read another org's record on-demand (low volume) | Salesforce Connect (External Objects) — OData adapter to target org REST API |
| Sync a small number of records in near-real-time | REST API callout from Apex or Flow → Named Credential + Connected App |
| Nightly full sync of hundreds of thousands of records | Bulk API 2.0 job from scheduled Apex or MuleSoft/external ETL |
| New multi-org integration replacing Salesforce-to-Salesforce | REST API + Named Credentials (JWT Bearer) — deprecate S2S immediately |
| Report across data in multiple orgs | CRM Analytics with multi-org data connectors, or replicate to a dedicated analytics org |

---

## Salesforce-to-Salesforce (S2S) — Legacy Feature Notice

Salesforce-to-Salesforce is a native Salesforce feature that allows records to be published from one org and subscribed in another. It exists and continues to function, but Salesforce considers it a legacy integration approach.

**Do not use S2S for new integrations.** Reasons:

- S2S uses SOAP API under the hood, consuming API call limits on both orgs for every record exchange.
- It does not scale to high record volumes — each record publication is a separate API transaction.
- It offers no support for modern OAuth patterns, Named Credentials, or JWT Bearer flows.
- It creates tight coupling between orgs with no abstraction layer for error handling or retry logic.

**Migration path from S2S:** Replace with a REST API integration authenticated via Named Credentials (JWT Bearer flow) in the calling org, with a Connected App in the target org. For high volume, use Bulk API 2.0.

---

## Related Skills

- `integration/named-credentials-and-callouts` — for Named Credential and Connected App configuration details
- `architect/solution-design-patterns` — for broader automation layer decisions
- `security/` skills — for OAuth scope design and IP range restrictions on Connected Apps
- `data/` skills — for LDV design within a single org (an alternative to multi-org for data volume concerns)
