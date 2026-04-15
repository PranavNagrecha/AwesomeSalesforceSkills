---
name: industries-integration-architecture
description: "Use when designing or reviewing the integration layer between Salesforce Industries clouds (Insurance, Communications, Energy & Utilities) and vertical backend systems such as policy administration systems, BSS/OSS platforms, or Customer Information Systems (CIS). NOT for generic Salesforce integration patterns unrelated to industry verticals, NOT for OmniStudio component design decisions (see omnistudio-vs-standard-architecture), NOT for FSC data model or module licensing (see insurance-cloud-architecture)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Performance
triggers:
  - "How do I integrate Salesforce Insurance Cloud with an external policy administration system?"
  - "What is the recommended pattern for connecting Communications Cloud to BSS/OSS platforms?"
  - "How should Energy and Utilities Cloud sync with a Customer Information System CIS?"
  - "We need to call an external backend from an OmniScript Integration Procedure — what pattern should I use?"
  - "Should our Industries integration use MuleSoft gateway or Direct Access for TM Forum APIs?"
tags:
  - industries-integration-architecture
  - insurance-integration
  - communications-integration
  - energy-utilities-integration
  - bss-oss
  - cis-integration
  - tm-forum-api
  - integration-procedure
  - omnistudio-integration
inputs:
  - "Industry vertical: Insurance, Communications/Telecom, or Energy & Utilities"
  - "Identity of the external backend: policy admin system, BSS/OSS platform, or CIS platform"
  - "Data ownership decision: which system is authoritative for which records (policy state, rate plans, fulfillment status)"
  - "Connectivity available: direct API, MuleSoft gateway, or middleware"
  - "Salesforce Industries licensed features and active feature flags in the org"
outputs:
  - "Integration architecture decision document identifying system-of-record boundaries per data domain"
  - "OmniStudio Integration Procedure design (IP action chain, remote action config, error handling strategy)"
  - "TM Forum API layer pattern selection for Communications Cloud (Direct Access vs deprecated MuleSoft gateway)"
  - "CIS-to-Salesforce data sync pattern for Energy & Utilities (sync scope, direction, frequency)"
  - "Review checklist confirming engagement-layer vs system-of-record boundary enforcement"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-15
---

# Industries Integration Architecture

This skill activates when an architect or senior practitioner must design or review the integration layer between a Salesforce Industries cloud (Insurance Cloud, Communications Cloud, or Energy & Utilities Cloud) and vertical-specific backend systems. The core challenge in every Industry integration is the same: Salesforce is an engagement and orchestration layer, not an operational system of record — and failing to respect that boundary produces brittle, dual-write systems that corrupt data on both sides.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm which Salesforce Industries cloud is licensed: Insurance Cloud, Communications Cloud, or Energy & Utilities (E&U) Cloud. Each has a distinct external backend archetype and a different authoritative source for core business data.
- Identify the external backend system and its role: policy administration system (insurance), BSS/OSS stack (telecom), or Customer Information System/CIS (utilities). These systems own operational data that Salesforce must not attempt to duplicate as a write-back system of record.
- For Communications Cloud: determine whether the org is using Direct TM Forum API Access or the MuleSoft API Gateway path. The MuleSoft gateway pattern is deprecated as of Winter '27 — any new design must use Direct Access.
- For Insurance: confirm whether Integration Procedures are already deployed and which external policy admin system they call. Check whether Salesforce or the external system owns policy state (most architecturally sound: external system is authoritative).
- For E&U: confirm whether CIS RatePlan records are being synced into Salesforce read-only or whether there is any attempt to write rates back to CIS from Salesforce (write-back to CIS for rates is an anti-pattern).

---

## Core Concepts

### Concept 1: Salesforce Industries as Engagement + Orchestration Layer

Salesforce Industries clouds are designed to be the engagement layer — the system where agents, customers, and partners interact — and the orchestration layer where service-order workflows run. They are not designed to be the operational system of record for backend data such as policy premiums, network fulfillment states, active rate plans, or billing balances.

This is a hard architectural boundary. When practitioners attempt to make Salesforce the authoritative store for data that a downstream system (policy admin, BSS, CIS) already owns, they create dual-write conflicts, stale data problems, and synchronization failures that are extremely difficult to unwind.

The correct model: backend systems own operational data. Salesforce reads it on demand (via Integration Procedures or Connected Apps), caches a read-only projection where latency requires it, and writes back only engagement-layer data (interaction records, service requests, case notes, consent flags).

### Concept 2: OmniStudio Integration Procedures as the Industries Integration Runtime

Integration Procedures (IPs) are the primary integration runtime for Salesforce Industries. They are server-side declarative action chains that can call HTTP Actions (REST callouts), Data Raptors (Salesforce read/write), and custom Apex actions. OmniScripts invoke Integration Procedures to retrieve data from external systems at guided process runtime without writing Apex callout logic.

Key constraints for IP-based integration:
- HTTP Actions in Integration Procedures execute synchronously within a single Salesforce transaction. Long-running external calls (> ~5 seconds) should be delegated to Apex async patterns or Platform Events to avoid governor limit breaches on the OmniScript session.
- Integration Procedures cannot hold a Salesforce database transaction open while waiting for an external response. Design external calls to be idempotent — the IP may be re-executed if the OmniScript session resumes from a saved state.
- IP metadata is version-controlled by the `IntegrationProcedureKey` and `IntegrationProcedureVersion` fields. Org deployments must include both the IP definition and its dependent DataRaptor definitions or HTTP Named Credentials.

### Concept 3: TM Forum API Layer for Communications / Telecom

Communications Cloud integrates with BSS/OSS using TM Forum Open API standards — particularly TMF620 (Product Catalog), TMF622 (Product Ordering), and TMF629 (Customer Management). Salesforce exposes and consumes these via a dedicated API layer.

**Critical forward-compatibility fact:** The MuleSoft API Gateway integration pattern for Communications Cloud is deprecated effective Winter '27. Any architecture that routes Communications Cloud ↔ BSS/OSS traffic through a MuleSoft API Gateway is on a dead-end path. The forward-compatible pattern is Direct TM Forum API Access — configuring Communications Cloud to call BSS/OSS TM Forum endpoints directly, and exposing Salesforce Communications data to BSS/OSS via Salesforce-hosted TM Forum API resources.

### Concept 4: CIS Authority for Energy & Utilities Rate Plans

In Energy & Utilities Cloud, the Customer Information System (CIS) is the operational system of record for rate plan definitions, meter readings, and billing data. Salesforce E&U is the engagement layer: it surfaces service order requests, handles field service coordination, and manages customer-facing case workflows.

The correct data sync pattern: CIS pushes RatePlan records to Salesforce via a one-way sync (typically scheduled batch or event-driven from CIS). Salesforce reads these records to display rate options during a service enrollment flow. Salesforce does not write rate plan definitions back to CIS — all rate changes originate in CIS and flow downstream.

---

## Common Patterns

### Pattern 1: Insurance — OmniScript + Integration Procedure for Policy Data Retrieval

**When to use:** An OmniScript-guided interaction (new policy quote, policy change, claims intake) needs to display or validate policy data from an external policy administration system during the guided process. The policy admin system is the authoritative source; Salesforce holds the engagement record only.

**How it works:**
1. OmniScript is configured with a step that invokes an Integration Procedure via a `Set Values` or `Integration Procedure` element.
2. The Integration Procedure contains an `HTTP Action` element that calls the policy admin system's REST API using a Named Credential for auth. The IP maps the raw JSON response through a response transformation into the OmniScript data JSON.
3. The OmniScript reads policy values from the IP response and displays them in the guided form. If the agent submits changes, the OmniScript triggers a separate write-path IP that calls the policy admin system's write endpoint — Salesforce does not write policy state to its own objects as the canonical record.
4. On submission, the OmniScript creates or updates Salesforce engagement objects (Interaction Summary, Case, or custom records) to record that a transaction occurred and what the outcome was. These are engagement artifacts — not replicas of the policy admin record.

**Why not the alternative:** Writing policy state to Salesforce Insurance objects (InsurancePolicy, InsurancePolicyCoverage) as a synchronous write-back during the guided process creates a dual-write system. If the external policy admin call succeeds but the Salesforce write fails (or vice versa), the two systems hold inconsistent state with no clean rollback path. Salesforce should hold engagement records, not replicate backend operational state.

### Pattern 2: Communications — Direct TM Forum API Access for BSS/OSS Integration

**When to use:** Communications Cloud must exchange product catalog, order management, or customer account data with a BSS/OSS stack that exposes TM Forum Open APIs.

**How it works:**
1. Configure Communications Cloud's TM Forum API settings to point directly at the BSS/OSS TM Forum API endpoints. Use a Named Credential to store the BSS/OSS base URL and OAuth credentials.
2. For product catalog sync (TMF620): BSS/OSS is the catalog authority. Configure a scheduled sync job or platform event handler that reads product catalog entries from BSS/OSS TMF620 endpoints and creates/updates ProductCatalog and ProductSpecification records in Salesforce read-only.
3. For order management (TMF622): Salesforce Communications Cloud originates order requests (from CPQ or Order Management flows). The order is submitted to BSS/OSS via a Direct TM Forum API POST. Salesforce stores the order reference ID and tracks fulfillment status by polling or receiving order state events from BSS/OSS. Salesforce does not duplicate order fulfillment logic.
4. Do not route Communications Cloud ↔ BSS/OSS traffic through a MuleSoft API Gateway. That pattern is deprecated Winter '27 and will require re-architecture.

**Why not the alternative:** The MuleSoft Gateway path adds a mediation layer that will cease to be a supported pattern after Winter '27, requiring a forced re-architecture at a high project cost. Direct Access avoids that runway risk and reduces latency.

### Pattern 3: Energy & Utilities — CIS One-Way Rate Plan Sync

**When to use:** An E&U Cloud deployment needs to display available rate plans to customers or agents during a service enrollment flow. The rate plan definitions live in CIS.

**How it works:**
1. CIS pushes RatePlan records to Salesforce on a scheduled basis (typically nightly or on change events from CIS). The integration uses an inbound REST call from CIS middleware or a scheduled batch that pulls from the CIS API.
2. Rate plan records land in Salesforce as read-only reference data (linked to the `EnergyRatePlan` or equivalent standard E&U object). Field-level security ensures Salesforce users cannot edit rate plan fields that originate in CIS.
3. OmniScripts or LWC components read the local Salesforce copy of CIS rate data for display during service enrollment. This avoids a live callout to CIS on every user interaction.
4. When a customer selects a rate plan during a service enrollment OmniScript, Salesforce creates a `ServiceOrder` record that references the CIS rate plan ID. The fulfillment system (CIS or a middleware orchestrator) reads the ServiceOrder and activates the rate in CIS. Salesforce tracks the order state but does not write rate assignments back to CIS directly.

**Why not the alternative:** A live callout to CIS for every rate plan display creates a tight runtime dependency on CIS availability. If CIS is slow or unavailable, every guided service enrollment fails. The one-way sync pattern decouples UI availability from CIS uptime.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Policy admin system is authoritative; OmniScript needs policy data at runtime | IP HTTP Action → policy admin REST API; engagement record in Salesforce | Keeps Salesforce as engagement layer; avoids dual-write conflict |
| Need to write a policy change back to external system | Write-path Integration Procedure → policy admin write endpoint; Salesforce stores interaction artifact only | Preserves single source of truth in policy admin system |
| Communications Cloud ↔ BSS/OSS integration, new architecture | Direct TM Forum API Access | MuleSoft Gateway path deprecated Winter '27 |
| Communications Cloud ↔ BSS/OSS integration, existing MuleSoft gateway | Plan migration to Direct TM Forum API Access before Winter '27 | Avoid forced emergency re-architecture at end of life |
| Rate plan data needed in E&U OmniScript | One-way CIS-to-Salesforce sync; read from local Salesforce copy | Decouples UI from CIS availability; prevents unauthorized rate writes from Salesforce |
| Stakeholder proposes writing rate changes from Salesforce to CIS | Reject: rates originate in CIS only; Salesforce triggers a ServiceOrder | CIS is the authority for rate definitions; write-back corrupts CIS state |
| Insurance org uses long-running policy admin callout (> 5s) | Delegate to Async Apex + Platform Event; IP receives callback via event | Avoids Salesforce governor limit breach on IP synchronous execution |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the vertical and external system** — Confirm which Industries cloud (Insurance, Communications, E&U) is in scope and which external backend system (policy admin, BSS/OSS, CIS) must be integrated. Record the authoritative system for each data domain (policy state, rate plans, order fulfillment).
2. **Validate the system-of-record boundary** — For each data domain involved, confirm in writing whether Salesforce or the external system is authoritative. If any domain has ambiguous ownership, resolve it before designing the integration. Salesforce should own engagement records only; operational data (premiums, rates, fulfillment status) must live in the backend system.
3. **Select the integration pattern per vertical** — Insurance: OmniScript + Integration Procedure calling policy admin REST API via Named Credential. Communications: Direct TM Forum API Access (reject MuleSoft Gateway for new work). E&U: one-way CIS-to-Salesforce sync for reference data + ServiceOrder write-back path.
4. **Design the Integration Procedure action chain** — For Insurance and E&U read paths, design the IP action chain: HTTP Action → response transformation → output mapping to OmniScript data JSON. Ensure Named Credentials are used (no hardcoded URLs or credentials). Add error handling IP elements with fallback messages for external system unavailability.
5. **Define the write-back path separately** — If Salesforce must trigger changes in the external system, create a distinct write-path Integration Procedure. Confirm the external system's write endpoint is idempotent. Ensure Salesforce stores only an interaction artifact (ServiceOrder, Case, Interaction Summary) — not a copy of the external operational record.
6. **Confirm Communications Cloud API pattern** — For Communications Cloud, verify whether the org uses Direct TM Forum API Access or MuleSoft Gateway. Flag any MuleSoft Gateway usage as requiring migration planning with a Winter '27 deadline.
7. **Review checklist and artifact handoff** — Validate the integration design against the Review Checklist. Produce the integration architecture decision document capturing system-of-record boundaries, IP designs, and API patterns selected.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] System-of-record boundaries documented per data domain (policy state, rate plans, order fulfillment, billing)
- [ ] No dual-write pattern identified — Salesforce does not write back operational data that the external system already owns
- [ ] Integration Procedures use Named Credentials for all external callouts (no hardcoded endpoints or credentials)
- [ ] Error handling IP elements present for external system unavailability on all read paths
- [ ] Communications Cloud: Direct TM Forum API Access confirmed; no new MuleSoft Gateway usage introduced
- [ ] E&U: CIS rate plan sync is one-way inbound only; no Salesforce → CIS rate write-back path designed
- [ ] Long-running external callouts (> 5s) are delegated to async patterns, not held in synchronous IP execution
- [ ] Integration Procedure versions and dependent DataRaptor/Named Credential metadata included in deployment package

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Integration Procedure synchronous timeout at OmniScript session boundary** — Integration Procedures execute synchronously within the OmniScript server-side step. If an HTTP Action in the IP calls an external system that takes more than approximately 5–10 seconds, the OmniScript session can time out or the Apex callout limit can be reached. This is most frequently seen with insurance policy admin systems that have variable response times. Mitigate by delegating slow external calls to Async Apex with a Platform Event callback, and having the OmniScript poll for the result via a fast IP.
2. **MuleSoft Gateway deprecation for Communications Cloud — Winter '27** — The MuleSoft API Gateway integration path for Communications Cloud ↔ BSS/OSS is deprecated. Orgs built on this pattern before the deprecation announcement will lose support. This is not self-evident from the Communications Cloud setup UI — the configuration still exists but will cease to be supported. Any architecture review must check which API path is active and flag MuleSoft Gateway usage for migration planning.
3. **Named Credential scope mismatch breaks IP HTTP Actions at runtime** — Integration Procedures that call external systems use Named Credentials for auth. If the Named Credential's OAuth scope does not include the required permission for the specific external API endpoint, the HTTP Action fails at runtime with a non-descriptive auth error. Debug by testing the Named Credential independently using Developer Console callout before wiring it to the IP.
4. **CIS rate plan sync overwrites Salesforce-local edits silently** — If a CIS-to-Salesforce rate plan sync job runs on a schedule and any Salesforce user has manually edited a rate plan field (even inadvertently), the sync job overwrites those edits without warning. Prevent this by locking CIS-originated rate plan fields using field-level security (read-only for all profiles) immediately after the sync lands the records.
5. **Insurance InsurancePolicy object cannot be used as engagement record for a policy admin-authoritative system without re-architecture** — The `InsurancePolicy` standard object in Insurance Cloud is designed to be the Salesforce representation of a policy. When an external policy admin system is the authority, practitioners sometimes use `InsurancePolicy` as a read-through cache while also allowing case workers to update it. This creates a split-brain state: the policy admin system updates the record externally, but case workers' Salesforce edits are overwritten on the next sync without notification. Use `InsurancePolicy` as a read-only projection with FLS locks, or separate engagement fields (custom fields) from synced policy fields.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Integration architecture decision document | Captures system-of-record boundaries per data domain, selected API patterns per vertical, and rationale for each choice |
| Integration Procedure design spec | Action chain layout, HTTP Action endpoint and auth (Named Credential), request/response mapping, error handling strategy |
| TM Forum API pattern confirmation | For Communications Cloud: Direct Access vs MuleSoft Gateway selection, with deprecation timeline if MuleSoft Gateway is in use |
| CIS sync design spec | For E&U: sync direction (CIS → Salesforce only), frequency, records in scope, FLS configuration for CIS-owned fields |
| Deployment manifest checklist | IP definitions, DataRaptor definitions, Named Credential metadata, External Credential metadata required for deployment |

---

## Related Skills

- `insurance-cloud-architecture` — For FSC data model, module licensing, and Insurance Cloud setup decisions; complements this skill for the data model layer beneath the integration
- `industries-data-model` — For understanding the standard Industries objects (InsurancePolicy, EnergyRatePlan, etc.) that integration sync targets
- `omnistudio-vs-standard-architecture` — For the upstream decision of whether to use OmniStudio Integration Procedures vs Apex/Flow for the integration runtime
- `integration-security-architecture` — For cross-cutting security controls on Named Credentials, OAuth scopes, and external system auth in any Salesforce integration
- `industries-cloud-selection` — For pre-implementation decisions about which Industries cloud to license, before integration architecture begins
