# Examples — AWS Salesforce Integration Patterns

## Example 1 — "Stream Closed-Won opportunities to a downstream provisioning Lambda"

**Context.** Sales-Ops wants every Closed-Won opportunity to trigger an
AWS workflow that provisions the customer's tenant in their SaaS product
(Step Functions → Lambda → DynamoDB). They want sub-minute latency,
at-least-once delivery, and a 24-hour replay window if the AWS side is
down for maintenance.

**Wrong instinct.** Spin up an `OpportunityTrigger` that publishes a
Platform Event, then a separate Apex class that subscribes and HTTP-POSTs
to a Lambda URL.

**Why it's wrong.** Reinvents at-least-once delivery. Apex callouts have
no built-in retry, no replay, no back-pressure. A single AWS-side outage
loses events permanently. Plus 100-callout governor and 120 s wall-clock
constraints fight you on bulk operations.

**Right answer.** **Pattern A — Event Relay → EventBridge.** Configure a
Pub/Sub channel on `OpportunityChangeEvent` (or a custom Platform Event
the Apex publishes), bind it via Relay Config to the AWS partner
event-source, accept the source on the EventBridge bus, attach a rule
that targets Step Functions. At-least-once delivery and 72-hour replay
are the managed defaults. Implementation lives in
`integration/event-relay-configuration` — link to it, don't re-derive.

---

## Example 2 — "Nightly account sync to Redshift for BI"

**Context.** Analytics team wants accounts and their open opportunities in
Redshift by 06:00 every morning. Volume is ~500 K accounts, ~2 M
opportunities. Field-level changes don't matter; full snapshot is fine.

**Wrong instinct.** Stand up a Heroku worker that uses the Salesforce REST
API to paginate accounts, dumps to S3, then a separate process loads to
Redshift.

**Why it's wrong.** Three moving pieces (Heroku, S3, Redshift loader),
three failure modes, three sets of monitoring. AppFlow does this end-to-end
with one console flow.

**Right answer.** **Pattern B — AppFlow scheduled flow.** Source:
Salesforce (connection via Authorization-Code OAuth — let AWS manage the
connected app). Destination: Redshift. Schedule: daily 04:00 UTC. API
Preference: `Automatic` — under the 1 M source-record threshold REST
handles it, above that AppFlow auto-switches to Bulk 2.0. Volume is well
under the 15 GB / 7.5 M record cap per run, so a single flow covers both
accounts and opportunities. No Apex.

---

## Example 3 — "Inline currency conversion during quote save"

**Context.** Quote pricing must be converted to the customer's currency
using the current mid-market rate from a corporate FX service exposed as
a Lambda Function URL. Conversion must happen *inside* the save
transaction so the persisted price reflects the converted value.

**Wrong instinct.** Use AppFlow to nightly-sync FX rates into a custom
object, then a Quote trigger reads from there.

**Why it's wrong-ish.** It works, but the data is up to 24 hours stale
and the synced custom object now has a daily refresh schedule the team
has to own. If business says "current rate", AppFlow cannot deliver
synchronous reads.

**Right answer.** **Pattern C — Apex callout to Lambda.** Named Credential
pointing at the Function URL (or API Gateway in front of it). Use
`templates/apex/HttpClient.cls` for the actual call — it wraps retry,
circuit-breaker, and observable logging. Bulkify by batching all quote
line items into one payload: single callout per Quote save, not one
per line.

---

## Example 4 — "Ingest 30 GB of historical event logs from S3 into Data Cloud"

**Context.** Migration from a legacy on-prem CDP. Five years of
clickstream events, ~30 GB total, gzipped JSON in S3.

**Wrong instinct.** AppFlow source-from-S3 to a Salesforce custom object.

**Why it's wrong.** AppFlow caps at 15 GB / run; this would need to be
split. Salesforce custom objects are also wrong storage for clickstream
— too expensive, too narrow.

**Right answer.** **Data Cloud's S3 connector** ingests directly into
Data Model Objects, which is the right shape for clickstream. Configure
the data stream with the IAM role Data Cloud provides; the connector
handles batch ingestion natively. Once in DMOs, harmonize / map / build
identity resolution. AppFlow is not the right tool when the destination
is Data Cloud — use the native connector.

---

## Example 5 — "Voice agent answers an inbound call routed by Amazon Connect"

**Context.** Service center wants Salesforce screen-pop with the caller's
contact + open cases when an Amazon Connect call lands.

**Right answer.** **Service Cloud Voice + Amazon Connect.** Not a generic
data-integration path; it's a packaged telephony + CRM integration.
Connect contact flow → Lambda lookups (caller-id → Contact ID via
Salesforce REST) → Voice console screen-pop. See Service Cloud Voice
docs for the full setup; the Apex/LWC layer is in
`admin/service-cloud-voice-setup`.
