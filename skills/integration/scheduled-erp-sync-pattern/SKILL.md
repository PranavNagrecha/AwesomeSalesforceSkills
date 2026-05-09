---
name: scheduled-erp-sync-pattern
description: "Use when designing a recurring (15-minute / hourly / nightly) data exchange between Salesforce and an external ERP system (Oracle EBS, SAP, NetSuite, Workday, Dynamics, etc.) where Salesforce is the *initiator* and pulls or pushes deltas on a schedule. Covers the full pattern: scheduled Apex → Queueable callout chain → REST request to ERP → upsert into a staging custom object → downstream reconciliation; plus watermark management (timestamp / cursor / full-refresh modes), idempotency via External ID, retry with exponential backoff, dead-letter custom object, and the volume thresholds that should redirect you to Bulk API 2.0, Change Data Capture, or MuleSoft. Triggers: 'integration to oracle erp every 15 minutes', 'scheduled sync pattern enterprise erp', 'pull netsuite invoices into salesforce nightly', 'apex schedulable callout to sap', 'how do i sync salesforce contacts to workday hourly', 'design a polling integration to my erp'. NOT for one-shot ETL imports (use data/data-loader-bulk-api), NOT for real-time inbound from ERP via Platform Events / Pub-Sub API (use integration/platform-events-publish-subscribe), NOT for outbound *event-driven* push (use integration/change-data-capture-consumer-pattern), NOT for MuleSoft / iPaaS architecture decisions (use architect/mulesoft-vs-native-integration-decision). When the data volume routinely exceeds 10K records per cycle or sub-minute latency is required, explicitly route to the Streaming / CDC / iPaaS skills instead."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
tags:
  - scheduled-erp-sync-pattern
  - scheduled-apex
  - queueable
  - named-credentials
  - idempotency
  - dead-letter-queue
  - watermark
  - bulk-api-2
  - integration-pattern
triggers:
  - "design an integration to oracle erp that runs every 15 minutes"
  - "scheduled sync pattern between salesforce and our enterprise erp"
  - "pull netsuite invoices into salesforce on a nightly cron"
  - "apex schedulable that makes a callout to sap"
  - "how do i sync salesforce contacts to workday on an hourly basis"
  - "design a polling integration from salesforce to my erp"
  - "what's the right architecture for a 15-minute erp delta sync"
  - "we need a watermark or high-water-mark for our erp sync, where does it live"
  - "scheduled apex is throwing 'callout from scheduled context' errors"
  - "how do we add a dead-letter queue for failed erp callouts"
inputs:
  - "ERP system name and authentication mechanism (OAuth client credentials, JWT bearer, basic auth, mTLS)"
  - "Direction of sync (SF→ERP push, ERP→SF pull, or bidirectional)"
  - "Cadence target (15-min, hourly, nightly) and acceptable lag"
  - "Approximate delta volume per cycle and peak burst size"
  - "Whether the ERP exposes a `modifiedSince` / cursor parameter or only full-refresh endpoints"
  - "Whether the records have a stable, ERP-side primary key suitable for use as a Salesforce External ID"
outputs:
  - "Architecture diagram identifying Schedulable, Queueable, staging object, dead-letter object, and watermark store"
  - "Apex class shells: Schedulable entrypoint, Queueable callout chain, retry harness, DLQ writer"
  - "Custom Metadata Type definitions for endpoint config + field mapping"
  - "Watermark strategy decision (timestamp vs cursor vs full-refresh) with justification"
  - "Volume / SLA threshold check that flags whether the user should escalate to Bulk API 2.0 / CDC / MuleSoft"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-08
---

# Scheduled ERP Sync Pattern

Activate this skill when a user wants to set up — or fix — a Salesforce-initiated recurring data exchange with an enterprise ERP system on a fixed cadence (typically 15 minutes, hourly, or nightly). The skill produces an architecture and the Apex skeletons; it does not write the org-specific business logic that maps the staging object into the live data model.

---

## Before Starting

Gather this context before proposing or building anything:

- **Direction of the sync.** Outbound-only (SF→ERP), inbound-only (ERP→SF), or bidirectional. Bidirectional needs a conflict-resolution rule, never silent last-writer-wins.
- **Authentication mechanism the ERP supports.** OAuth 2.0 client credentials, JWT bearer flow for service accounts, mTLS, and (rarely) basic auth all map to a Named Credential + External Credential, but they do *not* configure identically. Skip this and you will hit token-refresh outages later.
- **Whether the ERP supports a `modifiedSince` / cursor parameter.** This decides watermark mode. Some legacy ERP REST APIs only offer full-table endpoints; that pushes you toward CDC or Bulk API patterns instead of polling.
- **Stable ERP-side primary key.** If the ERP record has no immutable ID, you cannot do upsert-by-External-ID and the integration will create duplicates on every retry. This is not a fixable Salesforce-side problem — it is an ERP-side prerequisite.
- **Volume and burst profile.** A "15-minute sync" of 50 records per cycle is a different design than 50K. The volume bands at the bottom of *Concept 4* are the deciding factor between this pattern and the alternatives.
- **What "the integration is broken" should look like.** The DLQ + alerting design (Concept 3) only works if the team has decided what failure looks like — N consecutive cycle failures, a record-count anomaly, a watermark that hasn't advanced, or all three.

---

## Core Concepts

### Concept 1 — Cursor strategy: timestamp vs cursor vs full-refresh

A scheduled poll has to answer "what changed since last time?" The answer drives the entire design. Three modes, with sharply different failure profiles:

| Mode | How it works | Use when | Risk |
|---|---|---|---|
| **Timestamp** (`modifiedSince`) | Store the last-successful-poll UTC timestamp in a Custom Metadata or Custom Setting record. Each cycle queries `?modifiedSince=<watermark>` and on success advances the watermark to *the cycle start time*, not "now". | ERP exposes a reliable last-modified timestamp and clock skew between ERP and Salesforce is bounded. | Clock skew + missed-records on ERP-side bulk loads that backdate timestamps. |
| **Cursor / opaque token** | ERP returns a continuation token (`nextCursor`, `etag`, sequence number). Salesforce stores the token and passes it back next cycle. | ERP explicitly supports cursors (REST Link header pagination, opaque change-feed token, log-based CDC endpoint). | Cursor invalidation if the ERP rotates or expires it; needs reset-to-full-refresh fallback. |
| **Full-refresh with delta computation** | Pull the full data set every cycle, diff against staging, derive a delta. | ERP has no `modifiedSince`, no cursor, and the dataset is small (< a few thousand rows). | Volume cost. Becomes infeasible above ~5K rows on a 15-minute cadence. |

The biggest mistake here is advancing the watermark to `Datetime.now()` *after* the cycle finishes. If the cycle takes 90 seconds and the ERP modifies a record during second 30, that record's `modifiedDate` may be older than your post-cycle "now" and the next cycle will skip it. Always capture the watermark at *cycle start* and persist it only after end-to-end success.

### Concept 2 — Idempotency: External ID upsert is non-negotiable

Every record fetched from the ERP must arrive at Salesforce with an `External_Id__c` (or domain-specific equivalent like `ERP_Invoice_Number__c`) marked as External ID + Unique on the target sObject. The DML is `Database.upsert(records, ERP_Id__c)` — never `insert`.

Why this matters in a *scheduled* pattern more than in a one-shot import:

- A schedulable cycle that throws after partial commit will be retried — either by the platform's retry semantics or by your own DLQ replay. Without an External ID, replays create duplicates indefinitely.
- A bidirectional sync with last-writer-wins logic needs a stable join key on both sides. Without it you cannot tell whether SF Account #5 maps to ERP Customer #12345 — and the wrong join means writing a customer's address onto a different customer's record.
- ERP outages cause partial replication. When the ERP comes back, you re-poll the same `modifiedSince` window. Without idempotency you double-write everything you successfully fetched on the previous attempt.

For *bidirectional* sync, the conflict-resolution rule must be explicit and documented. The two viable options are (a) ERP wins by default (use `LastModifiedDate` comparison server-side and skip the SF-side update if ERP timestamp is older), or (b) field-level lineage tracking via a "last-changed-by-system" custom field. Silent last-writer-wins is *not* a strategy — it is a future data-corruption bug that surfaces at quarter-end.

### Concept 3 — Error handling: retry strategy + dead-letter queue + N-failure alerting

A production scheduled-sync pattern has three error layers stacked:

1. **In-cycle retry with exponential backoff.** Inside the Queueable, retry transient HTTP failures (5xx, 408, 429, network timeout) up to 3 times with `Limits.getCallouts()`-aware backoff. Never retry 4xx other than 408/429 — they indicate a permanent payload or auth issue. Important: a Queueable cannot `Thread.sleep()`; the "backoff" is achieved by re-enqueueing a new Queueable with a jittered delay, or by chaining and letting the platform schedule the next attempt.

2. **Dead-letter custom object (`Integration_DLQ__c`).** When retries are exhausted on a *record* (not a whole cycle), write the failing payload, the failing endpoint, the HTTP status, the response body, and the cycle ID into `Integration_DLQ__c`. Do not silently log to debug logs; logs are not queryable, do not survive 24 hours, and cannot drive replay tooling. The DLQ object is the audit trail and the replay queue.

3. **N-consecutive-cycle alerting.** A separate scheduled job (or a `LimitException`-handler in the Schedulable) tracks consecutive failed cycles. When the count exceeds a threshold (typically 3 for a 15-minute job, 1 for a nightly job), send a `Messaging.CustomNotification` to the integration ops group AND post to the integration-monitoring Slack/Teams channel via an Outbound Message or Apex callout. The threshold is tunable, but the principle is: don't alert on every cycle failure (transient) and don't wait for human discovery (silent).

The DLQ object should have at minimum: `Cycle_Id__c`, `Record_Payload__c` (LongTextArea, redact PII), `Endpoint__c`, `Http_Status__c`, `Response_Body__c` (LongTextArea, truncated to 32K), `Failed_At__c`, `Retry_Count__c`, `Status__c` (`New | Replayed | Resolved | Permanent`).

### Concept 4 — Scaling: the volume thresholds that redirect to a different pattern

This skill's pattern is the right answer in a defined volume + cadence band. Outside that band, route to a different pattern explicitly:

| Volume per cycle | Cadence | Use this pattern? | If not, use |
|---|---|---|---|
| < 200 records | Any cadence | Yes — vanilla scheduled Apex + Queueable + REST callout | — |
| 200–2K records | 15-min / hourly | Yes — but chain Queueables in batches of ~200 records per callout | — |
| 2K–10K records | 15-min | Borderline — measure callout time + heap usage; consider stepping cadence to hourly | Bulk API 2.0 ingest job from ERP-side; Salesforce becomes the *target* of an ERP-driven bulk load |
| > 10K records | Any | No | Bulk API 2.0 (ERP→SF) or platform-events/CDC if the requirement is "near-real-time" rather than "high volume" |
| Sub-minute latency requirement | — | No | Platform Events (push from ERP) or Salesforce Pub/Sub API consumer |

Two limits force the upper bound. First, an Apex transaction has a hard cap of **100 callouts per transaction** (see Salesforce Apex Limits). Even chained Queueables can only do 100 each, so a single record per callout caps you at 100 records per Queueable; batching multiple records per request is mandatory at scale. Second, *total* daily callout time and outbound-volume governor limits accumulate across all scheduled jobs; a 15-minute cadence × 96 cycles/day × multiple Queueable chains is a non-trivial slice of org-wide capacity.

When the ERP supports it, **Change Data Capture (CDC) consumed via the Pub/Sub API is almost always a better answer for bidirectional, near-real-time, high-volume sync**. Polling is a pull pattern and pull patterns waste capacity at low-change times and underprovision at high-change times. Use scheduled poll only when CDC / Platform Events are unavailable on the ERP side, or when the cadence is genuinely slow (nightly / hourly with low volume) and the operational simplicity of polling beats the engineering cost of streaming.

---

## Recommended Workflow

1. **Confirm volume + cadence + cursor support.** Use the Concept 4 table to verify the user's scenario fits the polling band. If volume is > 10K per cycle or sub-minute latency is required, escalate to Platform Events / CDC / Bulk API and stop here. If the ERP exposes no `modifiedSince` and no cursor, route to a full-refresh design and warn explicitly about the volume ceiling.

2. **Set up the Named Credential and External Credential.** Choose Auth Provider type (OAuth 2.0 client credentials for server-to-server, JWT bearer for fine-grained service account flows, mTLS for high-security ERPs). Verify token refresh is automatic (Salesforce handles refresh on 401 *only if* the Named Credential is configured for it — do not store tokens in Custom Settings, that is anti-pattern #4 in `references/llm-anti-patterns.md`).

3. **Design the watermark store.** Create a Custom Metadata Type `ERP_Sync_Watermark__mdt` with one record per (object, direction) pair, with fields `Last_Successful_Cycle_Start__c` (DateTime), `Cursor_Token__c` (Text 255), and `Last_Synced_Record_Id__c` (Text 36). Use Custom Metadata, not Custom Settings, because Custom Metadata is deployable as part of the package and can be diffed across environments; Custom Settings cannot.

4. **Implement the Schedulable + Queueable chain.** The Schedulable's `execute()` must do *zero* callouts (see Gotcha 3 — Schedulable contexts cannot make callouts directly). Its only job is to (a) read the watermark, (b) capture the cycle start time, (c) `System.enqueueJob()` the first Queueable, and (d) return. The Queueable does the callouts, the staging upserts, and chains the next Queueable. See `references/examples.md` for the canonical skeleton.

5. **Build the staging object + downstream reconciliation.** Land all ERP records into `ERP_Stage__c` first (External ID = `ERP_Record_Id__c`). A separate, independently-runnable Queueable reconciles staging → live records. Decoupling the callout from the data-model write means you can replay reconciliation from staging without re-calling the ERP.

6. **Implement the DLQ + alerting.** Create `Integration_DLQ__c` with the schema in Concept 3. Implement a separate scheduled job that counts `Status__c = 'New'` records older than 1 hour and sends a `Messaging.CustomNotification` when the count is non-zero. Add a threshold for "N consecutive cycle failures" tracked in a `Sync_Cycle_Run__c` audit object.

7. **Write the test class with `HttpCalloutMock`.** Cover: happy path, 5xx-then-recover, 4xx-permanent, watermark advance, watermark non-advance on failure, DLQ write on retry exhaustion, External ID upsert idempotency. Without a `HttpCalloutMock` test, the deployment will fail at the org-level test-coverage gate the moment a callout is added.

---

## Review Checklist

Run through these before marking the integration complete:

- [ ] Named Credential created; no hardcoded URLs or tokens in Apex
- [ ] Watermark stored in Custom Metadata (not Custom Setting), captured at *cycle start*, advanced only on end-to-end success
- [ ] Every staged record has an External ID + Unique field for upsert
- [ ] Schedulable does no callouts; Queueable does all callouts (`Database.AllowsCallouts` interface implemented)
- [ ] DLQ object exists with the 8 required fields; retry exhaustion writes to DLQ
- [ ] N-consecutive-failure alert wired to Custom Notification + monitoring channel
- [ ] HttpCalloutMock test covers happy / 5xx-recover / 4xx-permanent / DLQ paths
- [ ] Volume profile re-checked against Concept 4 table

---

## Salesforce-Specific Gotchas

1. **Schedulable cannot make callouts directly** — `execute(SchedulableContext)` runs in a context that does not permit callouts. The Schedulable must enqueue a Queueable, which does. See Gotcha 3 in `references/gotchas.md`.
2. **Watermark advanced to `Datetime.now()` after cycle skips records** — capture at cycle start, never at cycle end. See Gotcha 5.
3. **Named Credential token refresh requires Auth Provider, not just header config** — the "Per User" / "Named Principal" choice and the "Generate Authorization Header" flag must align. See Gotcha 2.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Architecture diagram | One-page diagram naming Schedulable, Queueable, staging object, DLQ, watermark store, alerting hook |
| Apex skeletons | Schedulable, Queueable chain, DLQ writer, retry harness — see `references/examples.md` |
| Custom Metadata definition | `ERP_Sync_Watermark__mdt` and `ERP_Field_Mapping__mdt` schemas |
| Test class | `HttpCalloutMock`-backed test covering the 7 scenarios in Workflow step 7 |
| Volume / cadence decision note | One-line answer: "polling is correct here because…" or "escalate to CDC because…" |

---

## Related Skills

- `integration/platform-events-publish-subscribe` — when ERP can publish near-real-time events instead of being polled
- `integration/change-data-capture-consumer-pattern` — when the data direction is ERP→SF and CDC on the ERP side is available
- `apex/apex-queueable-chain-pattern` — deeper coverage of Queueable chaining, governor reset, depth limits
- `data/data-loader-bulk-api` — when the volume tips past 10K records per cycle and the right answer is Bulk API 2.0 ingest
- `architect/mulesoft-vs-native-integration-decision` — when the integration is part of a larger middleware footprint and an iPaaS layer changes the calculus
- `security/named-credentials-and-external-credentials` — depth on auth provider configuration, token refresh, mTLS, JWT bearer
