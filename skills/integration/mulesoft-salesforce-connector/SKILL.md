---
name: mulesoft-salesforce-connector
description: "Designing and configuring MuleSoft Anypoint Salesforce Connector flows: API selection (SOAP/REST/Bulk/Streaming), OAuth 2.0 JWT Bearer auth, watermark-based incremental sync with Object Store, batch processing with record-level error isolation, and replay topic subscriptions. Use when building Mule 4 flows that read from or write to Salesforce, migrating from Mule 3 watermark to Mule 4 Object Store, or troubleshooting connector authentication and API limits. NOT for native Salesforce-to-Salesforce integration without MuleSoft (use platform-events-integration or change-data-capture-integration). NOT for generic REST callout patterns from Apex (use rest-api-patterns)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Performance
triggers:
  - "how do I connect MuleSoft to Salesforce with OAuth JWT Bearer"
  - "mulesoft salesforce connector watermark incremental sync"
  - "batch processing salesforce records through mulesoft without losing failures"
  - "which salesforce API should my mule flow use bulk REST SOAP streaming"
  - "mulesoft replay topic subscriber for platform events"
tags:
  - mulesoft
  - anypoint-connector
  - salesforce-connector
  - watermark
  - batch-processing
  - oauth-jwt-bearer
  - bulk-api
inputs:
  - "Salesforce org edition and API version in use"
  - "Integration pattern: real-time sync, batch/bulk, event-driven, or request-reply"
  - "Volume estimate: records per sync cycle and peak concurrency"
  - "Authentication method currently in use or planned (OAuth 2.0, username-password, JWT Bearer)"
outputs:
  - "Mule 4 flow XML snippet with correct connector operation and API selection"
  - "OAuth 2.0 JWT Bearer connected app configuration checklist"
  - "Watermark-based incremental sync flow design with Object Store"
  - "Batch processing scope configuration with error-handling strategy"
dependencies:
  - oauth-flows-and-connected-apps
  - rest-api-patterns
  - retry-and-backoff-patterns
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# MuleSoft Salesforce Connector

This skill activates when a practitioner is building, configuring, or troubleshooting MuleSoft Anypoint Platform flows that integrate with Salesforce. It covers connector API selection, authentication setup, watermark-based incremental synchronization, batch scope error handling, and streaming/replay topic subscriptions. It does not cover native Salesforce platform integration mechanisms (Platform Events consumed in Apex, Change Data Capture triggers) or generic Apex HTTP callout patterns.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Salesforce API entitlements and limits:** The connector wraps four Salesforce APIs (SOAP, REST, Bulk, Streaming). Each has distinct governor limits. Confirm the org's API call allocation (visible in Setup > Company Information) and whether Bulk API is enabled.
- **Connected App configuration:** The connector authenticates via a Connected App. For server-to-server flows (no interactive user), OAuth 2.0 JWT Bearer is recommended. Verify that a Connected App with the correct certificate, scopes, and pre-authorized profile exists before building the flow.
- **Mule runtime version:** Mule 4 replaced the built-in watermark element with Object Store-backed watermark. Flows migrated from Mule 3 that still reference `<watermark>` will fail at deployment. Confirm the target runtime is Mule 4.x.

---

## Core Concepts

### Connector API Selection — Four APIs, One Connector

The Salesforce Connector (version 11.x) exposes operations backed by four distinct Salesforce APIs. Choosing the wrong one causes limit exhaustion, timeouts, or data loss:

- **SOAP API** — Default for single-record CRUD. Best for real-time request-reply with < 200 records. Counts against the org's daily API call limit (one call per operation invocation).
- **REST API** — Used for Composite and SObject Tree operations. Enables creating up to 200 records in a single API call via Composite, reducing limit consumption.
- **Bulk API 2.0** — Required for high-volume loads (> 10,000 records). Operates asynchronously via jobs. Does not count against the standard API call limit but has its own daily rolling limit (150,000,000 records or 15,000 batches, whichever is hit first).
- **Streaming API / Pub/Sub API** — Used for Subscribe Topic and Replay Topic operations. Consumes CometD long-polling or gRPC streams. Requires Push Topic or Platform Event configuration in Salesforce.

### Watermark-Based Incremental Sync (Mule 4 + Object Store)

In Mule 4, the legacy `<watermark>` element is removed. Incremental sync is implemented manually using Mule's Object Store to persist the last-processed timestamp or record Id between flow executions. The pattern is:

1. On flow start, read the stored watermark value from Object Store (default to epoch if absent).
2. Query Salesforce with a `WHERE LastModifiedDate > :watermark` filter.
3. Process results.
4. After successful processing, update the Object Store with the maximum `LastModifiedDate` from the result set.

If the flow fails mid-batch, the watermark is not advanced, so the next execution re-processes the failed window. This provides at-least-once delivery semantics.

### Batch Scope and Record-Level Error Isolation

MuleSoft's `<batch:job>` scope processes records individually within each batch step. A failure on one record does not abort the entire batch. Instead, the failing record is routed to the `<batch:on-complete>` phase with a `FAILED` status while successful records continue. This is critical for Salesforce integrations where partial-success is common (e.g., validation rule failures on specific records). Always configure `maxFailedRecords` to a sensible threshold rather than the default of 0 (which aborts the batch on the first failure).

---

## Common Patterns

### Pattern 1: JWT Bearer Server-to-Server Authentication

**When to use:** Automated scheduled syncs, daemon integrations, or any flow without an interactive Salesforce user session.

**How it works:**

1. Create a Connected App in Salesforce with "Enable OAuth Settings" and "Use digital signatures" checked. Upload the X.509 certificate.
2. Pre-authorize the Connected App for the integration user's profile (Setup > Connected Apps > Manage > Edit Policies > Permitted Users = "Admin approved users are pre-authorized").
3. In the Mule Salesforce Connector configuration, select "OAuth 2.0 JWT Bearer" and supply the consumer key, the integration user's username, the keystore path, and keystore password.
4. The connector exchanges a signed JWT assertion for an access token with no browser redirect. Token refresh is handled automatically by the connector.

**Why not the alternative:** Username-password auth embeds credentials in the Mule app properties and breaks when the user's password changes or MFA is enforced. OAuth 2.0 Web Server flow requires an interactive browser session, which is not possible in headless runtime environments.

### Pattern 2: High-Volume Sync via Bulk API with Watermark

**When to use:** Nightly or scheduled syncs moving 10,000+ records between Salesforce and an external system.

**How it works:**

1. Read watermark from Object Store.
2. Use the connector's `query` operation with `fetchSize` set and Bulk API enabled in the connector config (`useBulkApi="true"`).
3. Pipe results through a `<batch:job>` with `blockSize` tuned to 200 (matching Salesforce DML batch size).
4. In the `<batch:on-complete>` phase, update the Object Store watermark only if the batch success rate exceeds the configured threshold.

**Why not the alternative:** Using SOAP API for high-volume loads burns through the org's daily API limit and may hit the 2,000-record query-more loop, causing timeouts in flows with transformation logic.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| < 200 records, real-time, request-reply | SOAP or REST API (Composite) | Low latency, single API call, synchronous response |
| 200 - 10,000 records, near-real-time | REST API Composite with chunking | Reduces API calls by 200x vs single-record SOAP |
| > 10,000 records, scheduled batch | Bulk API 2.0 | Async processing, does not count against standard API limit |
| Real-time event-driven (CDC, Platform Events) | Streaming API / Pub/Sub subscriber | Push-based, no polling, durable replay with replay ID |
| Server-to-server auth, no interactive user | OAuth 2.0 JWT Bearer | No password rotation risk, MFA-compatible, certificate-based |
| Interactive user context required | OAuth 2.0 Authorization Code (Web Server) | Maintains user identity for row-level sharing enforcement |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner configuring a MuleSoft Salesforce integration:

1. **Identify the integration pattern.** Determine whether the use case is request-reply, batch/bulk, event-driven, or bidirectional sync. This drives API and connector operation selection.
2. **Configure authentication.** For server-to-server: set up a Connected App with JWT Bearer, upload the certificate, pre-authorize the integration user's profile. For user-context: configure OAuth 2.0 Authorization Code with callback URL.
3. **Select the correct connector API.** Map the pattern from Step 1 to the API decision table above. Configure the connector's global element with the chosen API mode (e.g., `useBulkApi`, `useRestApi`).
4. **Implement watermark if incremental.** For any polling-based sync, use Object Store to persist watermark. Query with `LastModifiedDate > :watermark`. Advance watermark only after successful processing.
5. **Configure batch error handling.** Wrap Salesforce write operations in a `<batch:job>` with `maxFailedRecords` set to an acceptable threshold. Log failed records to a dead-letter queue or error topic for retry.
6. **Test with realistic volume.** Run the flow against a full sandbox with production-scale data. Verify API limit consumption, batch throughput, and watermark advancement after partial failures.
7. **Validate security and monitoring.** Confirm the Connected App has minimum required scopes, IP restrictions are applied if feasible, and Anypoint Monitoring dashboards track error rates and API consumption.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Connected App uses JWT Bearer (not username-password) for server-to-server flows
- [ ] Connector global configuration specifies the correct API mode for the volume and pattern
- [ ] Watermark is stored in Object Store and only advanced after successful processing
- [ ] Batch scope has `maxFailedRecords` set to a non-zero threshold with dead-letter logging
- [ ] API call budget verified: daily limit headroom confirmed for SOAP/REST; Bulk API limits checked for bulk flows
- [ ] Integration user has a dedicated profile with minimum required object/field permissions
- [ ] Flow tested with partial-failure scenarios (validation rule rejects, duplicate rules) to confirm error isolation

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Bulk API daily rolling limit is separate from standard API limit** — Bulk API 2.0 has its own 24-hour rolling window limit (150M records processed or 15,000 batches). Teams that assume Bulk API is "free" and run frequent intraday bulk syncs hit this limit and get `EXCEEDED_ID_LIMIT` errors with no warning until the job fails.
2. **Query-more pagination and session timeout** — SOAP API queries returning > 2,000 records use query-more with a server-side cursor. If the Mule flow takes too long processing between pages (> 15 minutes), the cursor expires and the query fails. Bulk API avoids this entirely by writing results to a retrievable file.
3. **JWT Bearer token caching and clock skew** — The connector caches the access token. If the Mule runtime's clock drifts > 5 minutes from Salesforce's servers, JWT assertion validation fails silently with an "invalid_grant" error that does not indicate clock skew. Use NTP sync on all Mule runtime hosts.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Mule 4 flow XML snippet | Connector configuration with selected API mode, auth, and watermark logic |
| Connected App setup checklist | Step-by-step JWT Bearer Connected App configuration for the Salesforce org |
| Batch error handling design | `<batch:job>` configuration with `maxFailedRecords`, dead-letter logging, and retry strategy |
| Object Store watermark design | Key naming, default values, and advancement-only-on-success guard logic |

---

## Related Skills

- oauth-flows-and-connected-apps — Use when configuring the Salesforce Connected App that the connector authenticates against
- retry-and-backoff-patterns — Use when the Mule flow needs retry logic for transient Salesforce API errors (503, 429)
- rest-api-patterns — Use when comparing native Apex REST callout alternatives to the MuleSoft connector approach
- change-data-capture-integration — Use when evaluating CDC as an alternative to polling-based sync via the connector
