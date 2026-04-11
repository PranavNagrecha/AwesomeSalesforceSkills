---
name: wealth-management-architecture
description: "Use this skill when designing or reviewing a Salesforce Financial Services Cloud (FSC) wealth management platform — covering advisor workspace configuration, client portal setup, portfolio data integration, Compliant Data Sharing, and FSC feature enablement decisions. NOT for investment product advice, financial planning calculations, or FSC Health Cloud configurations."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Scalability
  - Reliability
tags:
  - fsc
  - wealth-management
  - financial-services-cloud
  - advisor-workspace
  - compliant-data-sharing
  - portfolio-analytics
  - integration-patterns
inputs:
  - FSC org edition and license types (base FSC vs CRM Plus + FSC product CRM)
  - Custodian data feed format and update frequency (batch vs real-time)
  - Regulatory requirements for data access segmentation (Compliant Data Sharing scope)
  - Advisor workspace and client portal feature requirements
  - Deal Management and AI feature enablement decisions
outputs:
  - FSC feature enablement checklist (IndustriesSettings metadata flags)
  - Compliant Data Sharing configuration plan per object type
  - Custodian integration pattern selection (Batch vs Remote Call-In)
  - Advisor analytics licensing verification report
  - Architecture decision record for portfolio data flow
triggers:
  - "designing a wealth management platform on Financial Services Cloud and need to know which features to enable"
  - "FSC advisor workspace components not appearing after FSC license assigned"
  - "custodian data not syncing into portfolio records or portfolio totals are stale after nightly feed"
  - "setting up Compliant Data Sharing and advisors can no longer see any client records"
  - "Scoring Framework dashboards are blank and we have FSC but not sure what license is missing"
  - "how to integrate Schwab or Fidelity custodian data into Salesforce FSC using Bulk API"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Wealth Management Architecture

Use this skill when designing, implementing, or reviewing a Financial Services Cloud (FSC) wealth management platform. It covers the full platform layer: FSC feature flag enablement, Compliant Data Sharing setup, custodian-to-FSC data integration patterns, advisor workspace configuration, and licensing verification for the Scoring Framework.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the exact FSC license type in the org: base FSC licensing does NOT include the Scoring Framework used by advisor analytics dashboards — that requires the CRM Plus license plus the FSC product CRM license. Validate this before designing any analytics capability.
- Identify all custodian data sources: their update cadence (nightly batch vs event-driven real-time) and data volume. This determines the integration pattern (Bulk API 2.0 batch sync vs FSC Integrations API Remote Call-In).
- Determine which object types require Compliant Data Sharing — Account, Opportunity, Interaction, Interaction Summary, and custom objects are each enabled independently. It is off by default and must be explicitly turned on per object.

---

## Core Concepts

### FSC Feature Enablement via IndustriesSettings Metadata

FSC wealth management capabilities are gated behind discrete metadata flags in the `IndustriesSettings` settings type. The three most impactful for wealth management platforms are:

- **`enableWealthManagementAIPref`** — available from API v63.0 (Spring '25). Unlocks AI-powered portfolio analysis and client insights in the advisor workspace. This is NOT on by default even in FSC orgs. Requires the feature to be deployed via Metadata API before the UI surface appears.
- **`enableDealManagement`** — enables Financial Deal Management, exposing the Interaction-to-Deal junction objects that link client interactions to active financial deals. Required for deal pipeline tracking in advisor workspaces.
- **Compliant Data Sharing** — separate from the above two flags; it is enabled per object type, not globally. Each object type (Account, Opportunity, Interaction, Interaction Summary, custom objects) must be independently activated. Activation creates access-control metadata that governs which advisor roles can read records. Turning it on mid-implementation after data already exists requires a data migration pass to back-fill sharing records.

### Custodian Integration Pattern Selection

Portfolio data from external custodians (Schwab, Fidelity, Pershing, etc.) flows into FSC through one of two patterns defined in the Salesforce Integration Patterns Guide:

- **Batch Data Synchronization via Bulk API 2.0** — the correct pattern for large nightly feeds. Custodians export position, transaction, and account data in CSV or JSON. An ETL layer (MuleSoft, AWS Glue, or custom middleware) transforms the payload and submits ingest jobs to Bulk API 2.0. Each job is asynchronous; poll for completion before committing downstream rollup recalculations. This pattern handles millions of records without hitting DML limits.
- **Remote Call-In via FSC Integrations API** — the correct pattern for real-time custodian updates (price changes, same-day trade confirmations). The external system calls into Salesforce over HTTPS using Connected App OAuth. The FSC Integrations API accepts structured payloads and creates or updates Financial Account and Financial Account Transaction records synchronously. Use this only for low-volume, time-sensitive events — do not route large nightly batches through this path.

### Scoring Framework and License Dependency

The FSC Scoring Framework powers the advisor analytics dashboards that display client health scores, engagement scores, and referral opportunity scores. A critical licensing dependency applies: the Scoring Framework requires the **CRM Plus license** in addition to the standard FSC product CRM license. Orgs that purchased base FSC without CRM Plus will not see the scoring configuration UI, and any Flow or Apex that references the scoring objects will fail with object-not-found errors at deployment time. Verify licensing in the subscriber org before scoping any analytics work that depends on scoring.

### Compliant Data Sharing Per-Object Architecture

Compliant Data Sharing (CDS) is FSC's mechanism for enforcing regulatory data access controls — it ensures an advisor only sees the client records they are authorized to access. The architecture implication is that CDS is not a toggle on the FSC product but a per-object configuration layer. Each object type that requires segmentation must be explicitly enrolled. The enrollment triggers the creation of a shadow access-control table for that object. Critically: if records exist before CDS enrollment, those records have no sharing entries, meaning advisors may see no data after activation. The implementation sequence must be: enable CDS on the object type, then run the sharing recalculation batch, then activate advisor access.

---

## Common Patterns

### Pattern: Nightly Custodian Batch Sync (Bulk API 2.0)

**When to use:** Custodian provides a nightly data export of portfolio positions, transactions, and account balances. Dataset is large (100K–5M records per feed).

**How it works:**
1. Custodian drops delimited file to SFTP or S3.
2. ETL job transforms to Bulk API 2.0-compatible JSON/CSV payload.
3. Create ingest job via `POST /services/data/v63.0/jobs/ingest/` with `object: FinServ__FinancialAccountTransaction__c`.
4. Upload batches (max 150 MB per upload). Close the job.
5. Poll job state until `jobComplete`. Handle `Failed` rows with a dead-letter queue.
6. After successful completion, trigger async recalculation of FSC rollup fields (Net Worth, Total Assets) via a scheduled Apex job or Platform Event.

**Why not the alternative:** Using the REST Composite API for large custodian feeds causes CPU and DML limit breaches. Bulk API 2.0 is the purpose-built path for high-volume record ingestion.

### Pattern: Real-Time Trade Confirmation via Remote Call-In

**When to use:** Custodian sends same-day trade confirmations or intraday price updates for premium client portfolios requiring live dashboard data.

**How it works:**
1. Register custodian system as a Connected App with JWT Bearer OAuth grant.
2. Custodian POSTs trade confirmation to FSC Integrations API endpoint.
3. FSC creates `FinServ__FinancialAccountTransaction__c` record and triggers the relevant rollup rule.
4. Advisor workspace refreshes via Lightning Data Service wire adapter.

**Why not the alternative:** Queuing real-time events into the nightly batch introduces a 12–24 hour data lag, which is unacceptable for high-net-worth client portfolios where same-day position accuracy is a regulatory expectation.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Custodian feed is nightly, volume > 50K records | Batch Data Synchronization via Bulk API 2.0 | Avoids DML limits; handles large volumes asynchronously |
| Real-time trade events, volume < 1K/day | Remote Call-In via FSC Integrations API | Synchronous path for low-volume time-critical events |
| Regulatory data segmentation required per advisor | Compliant Data Sharing per object type | Purpose-built FSC access control; do not use manual sharing rules as a substitute |
| AI portfolio insights needed in advisor workspace | Enable `enableWealthManagementAIPref` via IndustriesSettings (API v63.0+) | Gate is off by default; must be explicitly deployed |
| Analytics dashboards with scoring required | Verify CRM Plus license present before scoping | Scoring Framework objects not available in base FSC |
| Deal pipeline tracking needed | Enable `enableDealManagement` in IndustriesSettings | Exposes Interaction-to-Deal junction objects |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify licensing and edition** — Confirm the org has the FSC product CRM license. Check whether CRM Plus is present for Scoring Framework requirements. Pull the list from Setup > Company Information > User Licenses. Flag any gap before any scoping conversation.
2. **Audit required IndustriesSettings flags** — Check which of `enableWealthManagementAIPref`, `enableDealManagement`, and Compliant Data Sharing flags are required by the project spec. Retrieve the current `IndustriesSettings` metadata to see what is already enabled. Plan a Metadata API deployment for each flag that needs to change.
3. **Design Compliant Data Sharing enrollment sequence** — For each object type that needs CDS (Account, Opportunity, Interaction, Interaction Summary, custom), determine if records already exist. If they do, plan the sharing recalculation batch as a post-activation step. Document the object enrollment order to avoid dependency failures.
4. **Select and design custodian integration pattern** — Confirm custodian data volume and update cadence. Map each feed to either Batch Data Synchronization (Bulk API 2.0) or Remote Call-In (FSC Integrations API). Define error handling: dead-letter queues for bulk failures, retry logic for Remote Call-In timeouts. Document the ETL transformation layer requirements.
5. **Configure advisor workspace and client portal surfaces** — Map required FSC standard components (Financial Account list, Net Worth tile, Interaction timeline) to advisor workspace page layouts. Confirm which components require Deal Management or AI preferences to be enabled. Validate Experience Cloud permissions if a client-facing portal is in scope.
6. **Validate rollup and scoring configuration** — Confirm FSC rollup rules are active for Net Worth, Total Assets, and Total Liabilities. If Scoring Framework is in scope, deploy scoring configuration objects and validate they appear in Setup. Run a test scoring calculation against a sandbox portfolio.
7. **Review data sharing posture before go-live** — Run the Compliant Data Sharing verification report for each enrolled object type. Confirm advisors can only see their assigned client records. Test cross-advisor record access to verify segmentation is working.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] CRM Plus license confirmed present if Scoring Framework is in scope
- [ ] All required IndustriesSettings flags deployed via Metadata API (not toggled manually)
- [ ] Compliant Data Sharing enrollment completed for each required object type, with sharing recalculation run after activation
- [ ] Custodian integration pattern documented (Batch vs Remote Call-In) with error handling defined
- [ ] FSC rollup rules validated against test portfolio records in sandbox
- [ ] Advisor workspace page layouts reviewed against enabled feature flags
- [ ] Client portal Experience Cloud permissions verified

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Scoring Framework silent failure on base FSC** — When Scoring Framework objects are not available due to missing CRM Plus license, deployments that reference those objects silently succeed but the components render blank in the UI. There is no deployment error. Teams discover the problem only when advisors report empty score tiles.
2. **Compliant Data Sharing activation data gap** — Enabling CDS on an object type does not retroactively create sharing entries for existing records. Existing records become invisible to all advisors until the sharing recalculation batch completes. Activating CDS on Account in production without running the batch immediately causes every advisor to see zero client accounts.
3. **`enableWealthManagementAIPref` requires API v63.0 minimum** — Attempting to deploy or retrieve this flag via an earlier API version results in an unknown-field error that does not clearly identify the version mismatch. Orgs on Winter '25 or earlier cannot use this flag.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| FSC Feature Enablement Checklist | List of IndustriesSettings flags, their current state, and deployment plan |
| Compliant Data Sharing Configuration Plan | Per-object enrollment sequence, sharing recalculation steps, rollback plan |
| Custodian Integration Design | Integration pattern selection, ETL transformation spec, error handling approach |
| Advisor Analytics Licensing Report | License verification output mapping features to required license types |

---

## Related Skills

- fsc-relationship-groups — configure Household, Professional Group, and Trust group structures that anchor portfolio rollup calculations within the wealth management platform
