---
name: marketing-integration-patterns
description: "Use when designing or selecting an integration pattern between Marketing Cloud and an external system or Salesforce CRM — including Triggered Sends, Journey injection via Event API, async batch contact entry, SFTP file-based batch sync, and MC Connect Synchronized Data Extensions. Triggers: 'send transactional email from external app', 'inject contacts into a journey from e-commerce', 'batch sync customer records into Marketing Cloud', 'connect Marketing Cloud to Salesforce CRM', 'real-time triggered messages from external platform'. NOT for generic integration framework design unrelated to Marketing Cloud, NOT for Marketing Cloud Automation Studio scripting logic, NOT for Salesforce core-to-core integration patterns (use architect/sales-cloud-integration-patterns)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Scalability
tags:
  - marketing-cloud
  - journey-builder
  - triggered-send
  - event-api
  - journey-injection
  - mc-connect
  - sftp
  - automation-studio
  - transactional-messaging
  - oauth2
  - installed-package
inputs:
  - "Source system type (CRM, e-commerce platform, ERP, mobile app, or Salesforce core)"
  - "Message type and latency requirement (transactional single-send, journey enrollment, batch campaign)"
  - "Contact volume per day and peak request rate"
  - "Whether Salesforce core (Sales/Service Cloud) is involved as the data source"
  - "Data extension schema for subscriber attributes"
  - "Whether contacts already exist in Marketing Cloud All Subscribers list or must be created"
outputs:
  - "Integration pattern recommendation with rationale"
  - "Authentication setup checklist (Installed Package, OAuth 2.0 client credentials)"
  - "API endpoint and payload structure for the chosen pattern"
  - "Data flow diagram showing external system to Marketing Cloud contact entry point"
  - "Error handling and retry strategy per pattern"
  - "Decision table matching scenario to recommended pattern"
triggers:
  - "send transactional email from external application to Marketing Cloud"
  - "inject contacts into a Marketing Cloud journey from e-commerce platform"
  - "batch sync customer records nightly into Marketing Cloud data extensions"
  - "connect Marketing Cloud to Salesforce CRM for real-time data"
  - "real-time triggered messages from external platform via REST API"

dependencies:
  - apex/marketing-cloud-api
  - admin/marketing-cloud-connect
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Marketing Integration Patterns

Use this skill when choosing and designing how an external system — an e-commerce platform, CRM, ERP, or mobile backend — sends data to or triggers messaging in Marketing Cloud. The skill covers the three primary real-time patterns (Triggered Sends, Journey Injection via Event API, and async batch contact entry), batch file-based sync via SFTP and Automation Studio, and near-real-time CRM sync via MC Connect Synchronized Data Extensions. All patterns require authentication setup through an Installed Package with API Integration.

---

## Before Starting

Gather this context before working on anything in this domain:

- What is the latency requirement? Triggered Sends target sub-second delivery for single messages; Journey Injection is near-real-time but involves Journey processing overhead; SFTP batch is typically 15–60 minute latency depending on Automation Studio schedule.
- What is the integration initiator — an external non-Salesforce system, Salesforce core (Sales/Service Cloud), or an internal Marketing Cloud process?
- Does the contact need to receive a single transactional message, or be enrolled in a multi-step Journey with decision logic?
- What is the daily contact volume and peak burst rate? Async batch via Event API accepts up to 100 contacts per request; SFTP file drops handle millions of records.
- Does the Installed Package with API Integration exist in Marketing Cloud? Every REST API pattern requires this — there is no workaround.

---

## Core Concepts

### Installed Package and OAuth 2.0 Client Credentials

Every Marketing Cloud REST API integration requires an Installed Package with an API Integration component configured in Marketing Cloud Setup. The API Integration issues a `clientId` and `clientSecret`. All calls must first authenticate via the Marketing Cloud authentication endpoint to obtain a short-lived Bearer token:

```
POST https://<tenant-specific-subdomain>.auth.marketingcloudapis.com/v2/token
Content-Type: application/json

{
  "grant_type": "client_credentials",
  "client_id": "<clientId>",
  "client_secret": "<clientSecret>"
}
```

The response includes an `access_token` (valid 20 minutes) and a `rest_instance_url` for subsequent REST calls. Tokens must be cached and refreshed before expiry — do not re-authenticate on every request. The Installed Package must have the correct scopes enabled: at minimum `Email` > `Send Email` for Triggered Sends, and `Journeys` > `Execute` for Journey Injection.

### Triggered Sends — Transactional Single-Message REST

A Triggered Send Definition (TSD) is a pre-configured send definition in Marketing Cloud that pairs a template, data extension, and send classification. External systems call the REST endpoint to fire a single message to a single subscriber immediately. The TSD must be in Active status before calls will succeed.

The call pattern is:
```
POST https://<rest_instance_url>/messaging/v1/messageDefinitionSends/key:<ExternalKey>/send
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "To": {
    "Address": "customer@example.com",
    "SubscriberKey": "sub-12345",
    "ContactAttributes": {
      "SubscriberAttributes": {
        "FirstName": "Jane",
        "OrderNumber": "ORD-9988"
      }
    }
  }
}
```

Triggered Sends are best for transactional messages: order confirmations, password resets, shipping notifications. They bypass subscription preferences for commercial sends only when the send classification is set to Transactional. The external key (`key:<ExternalKey>`) references the TSD's External Key field, not its internal ID.

### Journey Injection via Event API — Multi-Step Enrollment

The Event API (also called the Journey Builder Entry Event API) injects one or more contacts into a Journey as entry events. The Journey must have a REST API-based Entry Source configured, and that Entry Source generates an `eventDefinitionKey`. The `eventDefinitionKey` is what the external system passes — not the Journey ID, not the Journey name, and not the Entry Source name.

The call pattern is:
```
POST https://<rest_instance_url>/interaction/v1/events
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "ContactKey": "sub-12345",
  "EventDefinitionKey": "APIEvent-abc123-def456",
  "Data": {
    "EmailAddress": "customer@example.com",
    "ProductCategory": "Electronics",
    "CartValue": "149.99"
  }
}
```

A single call enrolls one contact. For batch injection of up to 100 contacts, use the async batch endpoint:
```
POST https://<rest_instance_url>/interaction/v1/events/async
```

The `async` endpoint accepts a `"contacts"` array with up to 100 entries per request and returns a `requestId` for polling. There is no synchronous batch; individual `/events` calls are synchronous but rate-limited.

### SFTP File Drop with Automation Studio Import Activity

For high-volume batch sync (initial loads, nightly CRM exports, daily audience refreshes), the canonical pattern is:

1. External system writes a CSV file to the Marketing Cloud SFTP location (`/import/` folder or a custom path).
2. An Automation Studio automation monitors the SFTP folder via a File Drop trigger or runs on a schedule.
3. An Import Activity picks up the file, maps columns to a Data Extension, and imports contacts using an "Add and Update" or "Overwrite" import mode.
4. Downstream activities (SQL Activity, Send Activity) execute after import completes.

This pattern handles millions of records per file and is the correct choice for bulk initial loads or nightly audience sync. It is not appropriate for latencies under 15 minutes.

### MC Connect Synchronized Data Extensions

When the data source is Salesforce Sales Cloud or Service Cloud (not a third-party system), Marketing Cloud Connect enables Synchronized Data Extensions (SDEs). SDEs are read-only replicas of Salesforce objects (Contact, Lead, Account, Campaign, CampaignMember, custom objects) that Marketing Cloud polls and refreshes on a configurable schedule (default: 15 minutes for standard, near-real-time for configured objects).

SDEs allow Journey Builder to use Salesforce CRM data as entry criteria and personalization attributes without a custom API integration. This is the recommended pattern for CRM-to-Marketing-Cloud data flow when the org has Marketing Cloud Connect installed and configured.

---

## Common Patterns

### Real-Time Transactional Email via Triggered Send

**When to use:** An external system (e-commerce checkout, password reset service, booking confirmation engine) needs to send a single personalized transactional email to a specific subscriber immediately after an event.

**How it works:**
1. Create a Triggered Send Definition in Marketing Cloud Email Studio with a Content Builder template. Set the Send Classification to Transactional.
2. Set the TSD status to Active.
3. Configure an Installed Package with API Integration. Enable the `Email` > `Send Email` scope.
4. External system authenticates via OAuth 2.0 client credentials to obtain a Bearer token.
5. POST to `/messaging/v1/messageDefinitionSends/key:<ExternalKey>/send` with subscriber attributes in the request body.
6. Marketing Cloud fires the message immediately. The response includes a `requestId` and HTTP 202 if accepted.

**Why not the alternative:** Using Journey Injection for single transactional messages adds unnecessary Journey processing latency and complexity. Journey Injection is for enrolling contacts in multi-step sequences, not one-shot transactional sends.

---

### Journey Enrollment from External E-Commerce System

**When to use:** An e-commerce platform detects a cart abandonment, product view, or purchase event and needs to enroll the customer in a Marketing Cloud Journey (welcome series, abandonment re-engagement, post-purchase nurture).

**How it works:**
1. Build the Journey in Journey Builder with a REST API Entry Source. Note the auto-generated `eventDefinitionKey` from the Entry Source configuration screen.
2. Configure an Installed Package with API Integration. Enable `Journeys` > `Execute` scope.
3. E-commerce platform triggers an event (cart abandoned, order placed).
4. Platform backend authenticates to Marketing Cloud via OAuth 2.0 client credentials.
5. POST to `/interaction/v1/events` with the `ContactKey`, `EventDefinitionKey`, and any data attributes needed for Journey personalization.
6. For bulk events (up to 100 contacts), POST to `/interaction/v1/events/async` with a `contacts` array.
7. Journey Builder processes the entry and routes the contact through the Journey steps.

**Why not the alternative:** Triggered Sends cannot branch or apply decision logic. Journey Injection is necessary when the message sequence depends on subscriber behavior or attributes evaluated within the Journey.

---

### Nightly Batch Audience Sync via SFTP

**When to use:** An external data warehouse, ERP, or CRM exports a daily audience file (potentially millions of rows) to refresh a Marketing Cloud Data Extension used for segmentation or campaign sends.

**How it works:**
1. External system generates a UTF-8 CSV file with headers matching the target Data Extension field names.
2. File is placed on the Marketing Cloud SFTP server in the designated `/import/` path using SFTP credentials from Marketing Cloud Setup.
3. An Automation Studio automation with a File Drop trigger (or scheduled trigger) detects the file.
4. An Import Activity maps the file columns to the Data Extension and runs with "Add and Update" mode to upsert records.
5. Subsequent automation steps (SQL Activity for segmentation, Send Activity) execute after import.

**Why not the alternative:** Calling the Data Extension REST API row by row for millions of records is impractical — the REST API has rate limits and per-call overhead. SFTP import is the only scalable path for bulk data loads.

---

## Decision Guidance

| Situation | Recommended Pattern | Reason |
|---|---|---|
| Single transactional message triggered by an external event (order confirmation, password reset) | Triggered Send via REST API (`/messaging/v1/messageDefinitionSends/key:<key>/send`) | Lowest latency, simplest payload, designed for single-subscriber transactional sends |
| Enroll contact in multi-step Journey from external system | Journey Injection via Event API (`/interaction/v1/events`) | Entry API is the only way to inject contacts into an active Journey with dynamic data |
| Batch inject up to 100 contacts into a Journey in one call | Async Event API (`/interaction/v1/events/async`) | Async endpoint accepts contact arrays; synchronous endpoint is single-contact only |
| Nightly or scheduled bulk audience sync (millions of records) | SFTP file drop + Automation Studio Import Activity | Only pattern that scales to millions of records without API rate-limit constraints |
| Salesforce CRM (Sales/Service Cloud) data to Marketing Cloud | MC Connect Synchronized Data Extensions | Native CRM connector; no custom API code; refreshes on schedule or near-real-time |
| Initial contact data load for a new Marketing Cloud org | SFTP file drop + Import Activity with Overwrite mode | Bulk load; no need for real-time latency during initial setup |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner designing a Marketing Cloud integration:

1. **Classify the integration trigger and latency requirement** — Determine whether the external system needs immediate single-message delivery (Triggered Send), Journey enrollment (Event API), or batch sync (SFTP). Latency, volume, and message complexity drive the pattern choice.
2. **Check Installed Package exists and has correct scopes** — Every REST API pattern requires an Installed Package in Marketing Cloud Setup with an API Integration component. Confirm the `clientId` and `clientSecret` are available and that the correct permission scopes are enabled for the chosen pattern.
3. **Locate or create the target artifact** — For Triggered Sends: confirm the Triggered Send Definition is Active and note its External Key. For Journey Injection: confirm the Journey has a REST API Entry Source and note the `eventDefinitionKey` (not the Journey ID). For SFTP: confirm the Data Extension schema matches the expected file columns.
4. **Implement OAuth 2.0 token acquisition with caching** — Authenticate using the tenant-specific auth endpoint. Cache the `access_token` and refresh before expiry (tokens live 20 minutes). Do not re-authenticate on every API call — this causes rate limit errors.
5. **Implement the integration call with the correct endpoint and payload** — Use the tenant-specific `rest_instance_url` returned in the auth response (not a hardcoded URL). For async batch, poll the returned `requestId` for status. Handle HTTP 429 (rate limit) with exponential backoff.
6. **Test with edge cases** — Verify behavior when the subscriber does not exist in the All Subscribers list (creation vs. rejection), when the TSD is in Inactive status, and when the `eventDefinitionKey` is incorrect. Document the failure modes.
7. **Validate error handling and alerting** — Ensure non-2xx responses are logged, retried where appropriate, and surfaced as alerts. Triggered Sends and Journey Injection are fire-and-forget from the caller's perspective — silent failures require explicit monitoring.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Installed Package with API Integration exists; `clientId` and `clientSecret` are stored securely (not in code)
- [ ] OAuth 2.0 token acquisition uses the tenant-specific auth endpoint, not a generic or hardcoded URL
- [ ] Access token is cached and refreshed before 20-minute expiry; no per-call re-authentication
- [ ] Triggered Send Definition is in Active status before the integration goes live
- [ ] Journey Injection uses `eventDefinitionKey` from the REST API Entry Source, not Journey ID
- [ ] Async batch calls do not exceed 100 contacts per request
- [ ] SFTP file column headers match Data Extension field API names exactly
- [ ] Error handling covers HTTP 401 (token expiry), 429 (rate limit), and 500-range errors
- [ ] Transactional send classifications are verified to bypass commercial subscription preferences correctly
- [ ] MC Connect SDEs are used instead of custom API calls when Salesforce CRM is the data source

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Journey Injection requires `eventDefinitionKey`, not Journey ID** — The Journey Builder REST API Entry Source generates a UUID-like `eventDefinitionKey` (e.g., `APIEvent-abc123-def456`). Using the Journey ID or Entry Source name in the payload will produce a 400 error with a misleading error message. The key is visible in the Entry Source properties panel in Journey Builder.
2. **Async batch endpoint cap is 100 contacts per request — not a soft limit** — The `/interaction/v1/events/async` endpoint returns a 400 error if the `contacts` array exceeds 100 entries. There is no automatic batching. Callers must split payloads into chunks of ≤ 100 before sending.
3. **All patterns require Installed Package with API Integration — there is no alternative auth method** — Marketing Cloud REST APIs do not accept username/password authentication or session-based auth. Any integration without a properly configured Installed Package will fail at the token acquisition step. This is a common gap when teams assume the Marketing Cloud FTP credentials or SOAP credentials will work for REST calls.
4. **Triggered Send Definition must be Active — Inactive or Paused TSDs return 400, not 404** — If the TSD is paused or inactive, the API returns a 400 Bad Request with no clear indication that a status change is needed. Validate TSD status programmatically before every deployment or build a monitoring check.
5. **SFTP Import Activity column mapping is case-sensitive and header-exact** — If the CSV header is `EmailAddress` and the Data Extension field API name is `email_address`, the import will fail silently — records are skipped rather than rejected with a clear error. Always verify Data Extension field API names against the file headers before configuring the Import Activity.
6. **MC Connect Synchronized Data Extensions are read-only in Marketing Cloud** — SDEs cannot be written to from Marketing Cloud — they are CRM-sourced replicas. Attempts to use them as writeable data targets in SQL Activities or import flows will fail. Use standard writable Data Extensions for Marketing Cloud-generated data.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Integration pattern recommendation | Selected pattern (Triggered Send, Journey Injection, Async Batch, SFTP, MC Connect) with rationale matched to latency and volume requirements |
| Authentication setup checklist | Installed Package configuration steps, required scopes, and token caching implementation guidance |
| API endpoint reference | Exact endpoint URL pattern, HTTP method, required headers, and example payload for the chosen pattern |
| Error handling specification | HTTP status codes to handle, retry policy, dead-letter strategy, and monitoring approach |
| Data flow diagram | Visual showing external system event through to Marketing Cloud message or data entry point |

---

## Related Skills

- `apex/marketing-cloud-api` — Use when implementing the Apex-side callout to Marketing Cloud REST endpoints from Salesforce core; covers token management and callout patterns in Apex
- `admin/marketing-cloud-connect` — Use when configuring the MC Connect CRM connector between Salesforce core and Marketing Cloud (Synchronized Data Extensions, Connected App setup)
- `architect/sales-cloud-integration-patterns` — Use when the integration involves Sales Cloud objects as the data source and the destination is not Marketing Cloud

---

## Official Sources Used

- Marketing Cloud REST API Overview — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/rest-api.html
- Marketing Cloud API Integration (Installed Package) — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/mc-create-an-installed-package.html
- Fire Entry Event (Journey Injection) — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/postEvent.html
- Insert Contacts Async (Batch Journey Injection) — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/postEventAsync.html
- Triggered Send Definition REST API — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/messageDefinitionSends.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
