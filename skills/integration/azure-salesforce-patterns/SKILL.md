---
name: azure-salesforce-patterns
description: "Azure integration patterns for Salesforce — pick between the native Azure Service Bus Connector, Azure Functions / API Management as the callout target, Data 360 (Data Cloud) Azure Blob Storage ingestion, Azure AD as IdP via SAML/OIDC, and the Power Platform Salesforce connector. Decision matrix + auth model guidance (Named Credentials with External Credentials, OAuth 2.0 client-credentials, JWT Bearer, SAML). NOT for AWS integration (see integration/aws-salesforce-patterns), NOT for MuleSoft as the integration backbone, NOT for in-Azure architecture details (Function code style, Service Bus topic/queue topology), NOT for Marketing Cloud-to-Azure data shares."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "salesforce to azure integration which service should I use"
  - "azure service bus connector salesforce setup"
  - "should I use service bus connector or apex callout to azure functions"
  - "salesforce azure ad sso saml or oidc"
  - "azure blob storage data cloud ingestion path"
  - "power platform salesforce connector limits"
tags:
  - azure
  - azure-service-bus
  - azure-ad
  - azure-blob-storage
  - power-platform
  - integration-pattern
  - decision-matrix
inputs:
  - "Direction of data flow (Salesforce → Azure, Azure → Salesforce, or bidirectional)"
  - "Latency requirement (real-time event, near-real-time, scheduled batch)"
  - "Volume estimate (events / day, total bytes / day)"
  - "Whether the org already has an Enterprise Connected App and a Named Credential strategy"
outputs:
  - "Recommendation: which Azure integration service (Service Bus Connector / Apex → Function / Data Cloud Blob ingestion / Azure AD SSO / Power Platform connector)"
  - "Auth model decision (Named Credential + External Credential vs OAuth 2.0 vs JWT Bearer vs SAML)"
  - "Specific limits and licensing the chosen path will hit and how to budget around them"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-01
---

# Azure Salesforce Integration Patterns

When a Salesforce org needs to talk to Azure — listen on a Service Bus queue,
call an Azure Function, sync to Azure Blob Storage, federate identity via Azure
AD, or expose Salesforce to Power Apps — there are four distinct managed paths
and a fifth do-it-yourself fallback. Picking the wrong one creates the same
operational debt the AWS side suffers from: an Apex callout where the native
Service Bus Connector would have eliminated all middleware, or a custom SAML
setup when the OIDC Auth Provider was the cleaner posture.

This skill is the **decision layer**. It does not re-derive Service Bus
topology, the Function host plan, or in-Azure governance — those belong on
the Azure side. It also does not cover MuleSoft (different decision tree) or
AWS integration (see `integration/aws-salesforce-patterns`).

---

## Before Starting

- Confirm whether the integration is **Salesforce → Azure**, **Azure → Salesforce**, or **bidirectional**. Each has a different recommended path; bidirectional usually means stitching two unidirectional flows.
- Identify the **Azure tenant id and subscription id** of the consuming services. Cross-tenant traffic and Azure Private Link availability vary by region; the Service Bus Connector requires a Service Bus namespace SAS or managed identity scoped to a single namespace.
- Check whether the org already runs an **Enterprise Connected App** with the right OAuth flow enabled. The Service Bus Connector's outbound auth and Power Platform's inbound auth both depend on a working Connected App; standing one up retroactively means a security review.
- Confirm Salesforce **edition and add-on licensing**. The Azure Service Bus Connector ships in core Salesforce (no separate license), but the Data 360 (Data Cloud) Azure Blob ingestion path needs a Data Cloud edition. Power Platform's Salesforce connector lives on the Power Platform side and counts against Power Platform request quotas.

---

## Core Concepts

### The four managed Azure integration paths

1. **Azure Service Bus Connector (native)** — Salesforce ships an in-product Azure Service Bus Connector that lets a Flow or Apex publish messages to a Service Bus queue or topic, and a Message Listener (background process) that subscribes and emits Platform Events back into the org. Auth is Shared Access Signature on a Service Bus namespace. *Right when the contract is event-level "react to this happening" between the two clouds, and you do not want to operate any middleware.*
2. **Apex → Azure Functions / API Management callout** — Salesforce makes an HTTP request to an Azure Function URL or APIM endpoint via a Named Credential with an External Credential. Auth is OAuth 2.0 client-credentials against Azure AD, or function-key for low-stakes paths. *Right when the integration must run inside a Salesforce transaction (validation, enrichment, screen-flow callout) and the response must come back before commit.*
3. **Data 360 (Data Cloud) Azure Blob Storage ingestion** — Data Cloud's Azure Blob connector reads structured files (Parquet, CSV) into Data Model Objects on a schedule. *Right when the source of truth is files in an Azure data lake and the consumer is Data Cloud (calculated insights, identity resolution, activations).* It is **not** a way to load data into core CRM custom objects — for that, AppFlow / Apex / Bulk API are still the path on the AWS side; Azure has no AppFlow equivalent.
4. **Azure AD identity federation (SSO + SCIM)** — Azure AD as IdP for Salesforce login via either SAML 2.0 (mature, common) or OpenID Connect via the Auth Provider framework (newer; better when you want JIT provisioning + token claims as User attributes). User provisioning rides on SCIM via the Azure AD Salesforce Enterprise gallery app. *Right when the goal is identity, not data movement.*

### The fifth path (fallback)

5. **Power Platform Salesforce connector (Power Automate / Logic Apps)** — Power Automate flows or Logic Apps call Salesforce via a managed connector that wraps the REST API. *Right for citizen-developer-owned automation between Salesforce and Microsoft 365 (e.g., "create a Planner task when an Opportunity closes"), where governance is acceptable on the Power Platform side and the volume is light.* Not a replacement for the Service Bus Connector for high-volume event traffic; the action limits are governed by Power Platform throttling, not Salesforce limits.

### How to pick

The decision turns on three questions: **direction**, **synchrony**, and
**downstream consumer**. The matrix in the next section resolves nearly
every real case.

---

## Common Patterns

### Pattern A — Salesforce → Azure events, no middleware

**When to use:** A Platform Event or CDC event in Salesforce should
trigger downstream Azure work (Function, Logic App, dataflow), and you
do not want to operate connector code.

**How it works:** Configure the **Azure Service Bus Connector** in
Salesforce Setup with a SAS connection string for the target Service
Bus namespace. Use Flow or Apex to publish messages to a queue or
topic. Downstream, an Azure Function or Logic App subscribes to the
queue/topic; outputs come back to Salesforce by publishing to a
return queue that the Salesforce Message Listener consumes and converts
into Platform Events.

**Why not the alternative:** A custom Apex → Function callout solves
the same problem but requires a transactional retry layer, adds
governor-limit risk for bulk transactions, and gives you no built-in
idempotency or DLQ behavior. Service Bus has both natively.

### Pattern B — Synchronous enrichment / validation

**When to use:** A Salesforce transaction must call out to Azure-hosted
business logic and use the response inside the same transaction (e.g., a
real-time pricing call or a fraud check during a screen flow).

**How it works:** Stand up an Azure Function or APIM endpoint. In
Salesforce, create a **Named Credential** + **External Credential** with
an OAuth 2.0 client-credentials principal against Azure AD (preferred)
or with a header-based Function Key (acceptable for non-PII). Call from
Apex with `Http` + `HttpRequest` using the Named Credential URL. For
screen flows, use **HTTP Callout actions** wrapping the same Named
Credential.

**Why not the alternative:** Async paths (Service Bus, event-driven
patterns) cannot return a response before commit. Hard-coded function
keys in custom-metadata are an anti-pattern — see Gotchas.

### Pattern C — Data lake to Data Cloud

**When to use:** The source of truth is structured files (Parquet, CSV,
JSON) in Azure Blob Storage and the consumer is Data Cloud (Calculated
Insights, segments, activations).

**How it works:** In Data Cloud, configure the **Azure Blob Storage
connector** with a service principal and the storage account container.
Define an ingestion stream that maps the file schema to a Data Lake
Object, then promote to a Data Model Object. Schedule cadence honors
the connector's minimum interval (currently every 15 min on standard
ingestion).

**Why not the alternative:** Loading the same files into core CRM via
Apex Bulk API works mechanically but creates millions of rows in a
transactional store that should hold relationship-grade data. Data
Cloud is the correct destination shape for analytics / activation data.

### Pattern D — Azure AD SSO

**When to use:** Azure AD already holds the workforce identity and you
want to retire any Salesforce-local password posture.

**How it works:** Use the **Azure AD Salesforce Enterprise gallery
app**. SAML 2.0 is the default; OpenID Connect is supported via a
custom Auth Provider when you want claims to flow into User fields on
JIT. SCIM provisioning via the gallery app handles user lifecycle.

**Why not the alternative:** Hand-rolled SAML works but loses the
gallery app's drift detection. Local-password fallback should be off
once SSO is live.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Salesforce event → Azure compute, async | **Service Bus Connector + queue** | Native, durable, no middleware. Best operational profile. |
| Salesforce transaction needs Azure response now | **Apex / Flow → Function via Named Credential + External Credential** | Only synchronous path. Use OAuth 2.0 client-credentials. |
| Azure Blob files → Data Cloud | **Data 360 Azure Blob ingestion** | Correct destination for analytics/identity data. |
| Azure Blob files → core CRM custom objects | **Apex Bulk API job** *(no managed path)* | Azure has no AppFlow equivalent. Bulk API is the manual fallback. |
| Workforce SSO from Azure AD | **Azure AD gallery app, SAML or OIDC + SCIM** | Mature path; SCIM handles lifecycle. |
| Citizen automation between Salesforce + M365 | **Power Platform connector in Power Automate** | Right for low-volume office-automation glue, not a high-volume integration backbone. |
| High-volume event traffic with replay | **Service Bus Connector + topic + DLQ** | Service Bus DLQ + replay is the durable path. Power Automate throttles too aggressively. |
| Sensitive PII in transit | **Named Credential + External Credential + Private Link** | Avoid Function Keys for any PII path; require TLS + AAD principal. |

---

## Recommended Workflow

When this skill activates, follow these steps in order:

1. **Confirm direction and synchrony.** Ask: which side originates the data, and does the originating transaction need the response back? That choice alone eliminates 3 of the 5 paths.
2. **Estimate volume.** If events / day exceed Power Platform connector limits or Service Bus tier limits, the path is Service Bus Connector + the right tier; otherwise Power Platform may be acceptable.
3. **Map the auth model.** For Service Bus, choose SAS vs managed identity. For Functions/APIM, default to OAuth 2.0 client-credentials with Azure AD; reject Function Keys for PII.
4. **Decide on Private Connect / Private Link.** If the data is regulated, plan the network path before choosing the connector — some connectors require public endpoints unless paired with Private Link in a supported region.
5. **Spec the message contract.** For Service Bus, define the message JSON schema, partition key, and DLQ behavior. For Functions, define request/response with explicit error codes Salesforce can act on.
6. **Confirm the licensing path.** Data Cloud Azure Blob ingestion needs a Data Cloud edition; Service Bus Connector ships in core; Power Platform usage counts against Power Platform request quotas, not Salesforce limits.
7. **Cite the matching Salesforce documentation in the design** — see `references/well-architected.md` for the canonical link set.

---

## Review Checklist

Before approving an Azure integration design:

- [ ] Direction (SF→Azure / Azure→SF / bidirectional) and synchrony are stated explicitly.
- [ ] Auth model is named: SAS, managed identity, OAuth 2.0 client-credentials, JWT Bearer, or SAML/OIDC.
- [ ] No Function Keys are used for PII; no shared secrets are stored outside Named Credentials / External Credentials.
- [ ] Volume estimate exists and matches the chosen path's limits (Service Bus tier, Power Platform throttle, Data Cloud ingestion cadence).
- [ ] DLQ / retry / replay behavior is documented for each async path.
- [ ] Private Link / Private Connect requirement is decided, not deferred.
- [ ] Identity is federated through Azure AD with SCIM, not synced via custom Apex.
- [ ] Power Platform usage is gated to citizen-automation use cases, not high-volume backbone.

---

## Salesforce-Specific Gotchas

1. **The Azure Service Bus Connector requires a high-volume Platform Event channel for the listener path.** Standard Platform Events do not survive subscriber slowness. Forgetting this surfaces as silent message loss under load. Configure the receiving channel as high-volume from day one.
2. **Function Keys end up checked into version control more often than any other Azure secret.** Salesforce custom-metadata or custom-settings is not the right place — use a Named Credential + External Credential principal, even if the Azure side currently accepts a Function Key. The migration path is much cheaper before there are 30 callers.
3. **Azure AD JIT provisioning silently overwrites Profile and Permission Set assignments** if the SCIM mapping declares them. Set the SCIM mapping to govern only `username`, `email`, `firstname`, `lastname`, `isActive`, and let Salesforce-side rules govern entitlements — otherwise an Azure AD admin can grant Salesforce permissions without a Salesforce review.
4. **Power Platform's Salesforce connector throttles at the Microsoft tenant level**, not the Salesforce org level. A noisy Power Automate flow elsewhere in the same M365 tenant can starve your business-critical flow. This is invisible from the Salesforce side. Mitigate by reserving a dedicated connection / service account.
5. **The Data Cloud Azure Blob connector reads files at rest, not as a stream.** A frequently overwritten file in Blob Storage produces ingestion-time race conditions where a partial file is read. Use immutable file naming with a date+UUID suffix and append-only writes; never let the producer overwrite the file Data Cloud is currently reading.
6. **OAuth 2.0 client-credentials for Azure AD requires a Connected App with the right Refresh-Token Policy.** "Refresh token is valid until revoked" is the policy that keeps server-to-server flows alive without operator intervention; the default ("first use") will fail at the first token expiry.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Path recommendation | Which of the 5 Azure integration paths to use, with one-paragraph rationale |
| Auth model decision | Named/External Credential plan, OAuth flow choice, SAS vs managed identity |
| Limit & licensing budget | Per-tier limits the chosen path will hit and any add-on licensing required |
| Risk register | Dedicated PII / DLQ / private-link items the design must close before go-live |

---

## Related Skills

- `integration/aws-salesforce-patterns` — sibling decision layer for AWS; same shape.
- `integration/oauth-flows-and-connected-apps` — auth-flow selector across all integrations; cite from Pattern B.
- `integration/named-credentials-and-callouts` — outbound auth pattern from Apex.
- `integration/platform-events-basics` — event publishing / subscription mechanics behind Pattern A.
- `data/data-cloud-foundation` — required reading before activating Pattern C.
- `architect/multi-cloud-architecture` — strategic framing when both Azure and AWS are in scope.

See also `standards/decision-trees/integration-pattern-selection.md` for the higher-level Salesforce-side integration choice (REST vs Bulk vs Pub/Sub vs Salesforce Connect vs MuleSoft) before this skill activates.
