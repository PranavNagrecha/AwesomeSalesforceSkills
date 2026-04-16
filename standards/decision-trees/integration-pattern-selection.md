# Decision Tree — Integration Pattern Selection

Which integration pattern should I use?
**REST · SOAP · GraphQL · Bulk API · Streaming / CDC · Platform Events · Pub/Sub API · Salesforce Connect (External Objects) · Named Credentials · Salesforce Connect OData · Outbound Messages · MuleSoft / iPaaS**

Use this tree BEFORE proposing a specific integration pattern to the user.

---

## Strategic defaults

1. Direction matters more than tech. Decide **Salesforce → external**,
   **external → Salesforce**, or **bi-directional / decoupled**, then pick.
2. Prefer **event-driven** over polling whenever the producer can emit events.
3. Prefer **Named Credentials + External Credentials** over any form of
   hardcoded endpoints or stored secrets.
4. For high-volume external → Salesforce writes, use **Bulk API 2.0** — not
   REST composite with batching.
5. For Salesforce data that should appear in another system *without copying*,
   use **Salesforce Connect (OData)** or **Pub/Sub API subscribers** on the
   external side — do not ETL.

---

## Direction 1: Salesforce calls out (Salesforce → external)

```
START: Salesforce needs data from / needs to send data to an external system.

Q1. Is the call synchronous to a user action?
    ├── Yes, < 120s, user watches a spinner     → Continuation (see apex/continuation-callouts)
    ├── Yes, under 10s, LWC imperative call     → @AuraEnabled Apex → HttpClient (Named Credential)
    ├── No, fire-and-forget                     → Queueable with AllowsCallouts
    └── No, bulk ingest/egress                  → Batch Apex or MuleSoft / iPaaS

Q2. Authentication?
    ├── Username/password basic                 → Named Credential with Basic auth (dev/test only)
    ├── OAuth 2.0 client credentials            → Named Credential + External Credential (OAuth 2.0 CC)
    ├── OAuth 2.0 per-user                      → Named Credential + External Credential (Per-User OAuth 2.0)
    ├── JWT bearer                              → Named Credential + External Credential (JWT Bearer)
    ├── Custom header / API key                 → Named Credential + External Credential (Custom)
    └── mTLS                                    → Named Credential + External Credential (Mutual TLS) + uploaded cert

Q3. Payload shape?
    ├── JSON REST                               → HttpClient + JSON.serialize/deserialize
    ├── SOAP                                    → WSDL2Apex-generated client OR raw HttpRequest + XML
    ├── GraphQL                                 → HttpClient with body='{"query":...}'
    ├── Binary (file upload)                    → HttpClient with Blob body; respect 6MB heap
    └── Event stream                            → Pub/Sub API gRPC (if external produces events SF must react to)

Q4. Rate limiting / retry?
    ├── Known transient 5xx patterns            → HttpClient with retryOnTransient(true)
    ├── Known 429 throttling                    → Queueable with exponential backoff + Finalizer
    ├── Idempotency key required                → Generate in Apex, send as header; tie to Request_Id__c
    └── Ordering-sensitive                      → Single-threaded Queueable chain (no parallel dispatch)
```

---

## Direction 2: External writes into Salesforce (external → Salesforce)

```
Q5. How much volume?
    ├── < 1k rows/day                           → REST API (POST /services/data/vXX.X/sobjects)
    ├── 1k–1M rows/day                          → REST Composite (collections endpoint, up to 200/request)
    └── > 1M rows/day OR bulk upsert/delete     → Bulk API 2.0 (async ingest)

Q6. Latency requirement?
    ├── Real-time (< 10s)                       → REST / Platform Events publish from external
    ├── Near-real-time (< 5 min)                → REST Composite batches
    └── Batch (hourly/nightly)                  → Bulk API 2.0

Q7. Does the external system know Salesforce record IDs?
    ├── Yes                                     → Direct PATCH by Id
    ├── No, but has a stable external key       → Upsert on External Id field
    └── No, reference by name                   → Strongly discouraged — require an External Id

Q8. Are writes idempotent?
    ├── Yes (designed idempotent)               → Retries safe; use Bulk API 2.0
    ├── No                                      → Require idempotency key header + custom REST endpoint that dedupes
    └── Can't guarantee either                  → Platform Event ingestion with subscriber-side dedup

Q9. Does the external data belong in Salesforce tables?
    ├── Yes, with business logic attached       → Custom REST (@RestResource)  + service layer
    ├── Yes, plain CRUD                         → Standard REST on sObject
    ├── No — users just need to read it in SF   → Salesforce Connect + External Objects (OData)
    └── Yes but ephemeral (sessions, carts)     → Platform Cache + custom REST
```

---

## Direction 3: Bi-directional or decoupled fan-out

```
Q10. Who is the producer of the "something happened" signal?
     ├── Salesforce                             → Q11
     └── External system                        → Q13

Q11. Who are the subscribers?
     ├── Internal (Apex / Flow)                 → Platform Event (internal channel)
     ├── External (another system)              → Platform Event + Pub/Sub API gRPC subscriber
     ├── Both                                   → Platform Event; external side uses Pub/Sub API
     └── Audit / replication target             → Change Data Capture (CDC)

Q12. Ordering guarantees needed across subscribers?
     ├── Yes, strict                            → One-producer, one-partition; document the constraint
     ├── At-least-once                          → Platform Event default; build idempotency in subscriber
     └── Exactly-once required                  → Not natively supported; use idempotency key pattern

Q13. External producer emits events Salesforce must react to.
     ├── External supports Pub/Sub API          → Pub/Sub API subscriber (Salesforce side)
     ├── External can push HTTP                 → Custom REST endpoint → Platform Event re-publish
     ├── External supports webhooks             → Custom REST endpoint (@HttpPost)
     └── External can only emit files           → SFTP / MuleSoft / Bulk API ingest

Q14. Does Salesforce + external need to stay replicated?
     ├── One-way, SF → external                 → CDC + Pub/Sub API subscriber
     ├── One-way, external → SF                 → Bulk API 2.0 scheduled OR streaming ingest
     ├── Bi-directional                         → MuleSoft / iPaaS — don't roll your own two-way sync
     └── Read-only SF view of external          → Salesforce Connect (OData)
```

---

## Pattern summary

| Pattern | Best for | Avoid when |
|---|---|---|
| REST API (standard sObject) | Simple CRUD from external | Volume > 200 records/request |
| REST Composite | Mid-volume batched CRUD | Volume > ~1M rows/day |
| Bulk API 2.0 | High-volume ingest/egress | Need sub-10s latency |
| Custom REST (`@RestResource`) | Exposing business logic, not raw CRUD | Standard sObject CRUD suffices |
| Apex callouts + Named Credentials | Salesforce calling external APIs | Long-running (> 120s) — use Bulk API or Queueable chain |
| Continuation | Synchronous, user-initiated, < 120s external call | Async / headless contexts |
| Platform Events | Internal fan-out, decoupled producers | Transactional rollback across pub+sub is required |
| Change Data Capture | Replicate SF changes to another system | You need custom event shape — use Platform Events |
| Pub/Sub API (gRPC) | External subscriber to SF events | External can only consume REST |
| Salesforce Connect (OData) | Surface external data without copying | Users need to write back frequently at scale |
| Streaming API (PushTopic) | Legacy — prefer Pub/Sub API | Any new work (PushTopic is maintenance-mode) |
| Outbound Messages | Legacy SOAP webhook from workflow | Any new work (Workflow Rules retired) |
| MuleSoft / iPaaS | Multi-system orchestration, transformations, long-running | Single point-to-point integrations you already own |

---

## Named Credentials — always, not sometimes

Rules enforced across this repo:

1. Never hardcode an endpoint hostname. Use `callout:<NamedCredential>/<path>`.
2. Never store an API key in Custom Setting, Custom Metadata, or Apex source.
   Use External Credentials → Principals.
3. Rotate credentials by editing the External Credential — never by redeploying.
4. Test callouts with `MockHttpResponseGenerator` (see
   `templates/apex/tests/`) — NEVER hit a real endpoint from an Apex test.

See `skills/integration/oauth-flows` and `standards/security/*` for deeper
treatment.

---

## Anti-patterns

- **Polling for changes.** Use CDC or Platform Events — every "check every N
  minutes" job is technical debt.
- **Hand-rolled retry loops in Apex.** Use `HttpClient.retryOnTransient(true)`
  or Queueable chaining — hand-rolled loops leak into governor limits.
- **Bulk API inside a trigger.** Bulk API calls are meant for async / external
  ingestion, not the synchronous DML path.
- **PushTopic for new work.** Pub/Sub API replaces it; PushTopic is legacy.
- **Outbound Messages.** Workflow Rules are retired. Every Outbound Message is
  technical debt to be migrated to Platform Events or Flow + Apex.
- **"We'll just sync everything nightly."** Almost always wrong. Real-time is
  cheaper than the bug-report cycles from stale data.
- **Custom REST that duplicates a standard sObject endpoint.** The standard
  one is bulk-optimized and maintained. Custom REST is for *new* behavior.

---

## Security overlays (always apply)

- **Transport:** TLS 1.2+ — enforced by the platform on Named Credentials.
- **AuthN:** OAuth 2.0 > JWT > Basic. Never Basic in production.
- **AuthZ:** The running user's CRUD/FLS still applies in custom REST. Use
  `templates/apex/SecurityUtils.cls` or `WITH USER_MODE`.
- **Rate limits:** Know the per-org API limits; use `/limits` endpoint to
  monitor.
- **PII:** Honour Shield / field encryption — do not exfiltrate plaintext
  fields that are encrypted at rest.

---

## Related skills

- `integration/callouts-and-http-integrations`
- `integration/rest-api-patterns`
- `integration/bulk-api-2-patterns`
- `integration/platform-events-integration`
- `integration/change-data-capture-for-external-subscribers`
- `integration/pub-sub-api-patterns`
- `integration/named-credentials`
- `integration/oauth-flows`
- `integration/graphql`
- `integration/salesforce-connect`
- `architect/event-driven-salesforce-architecture`

## Related templates

- `templates/apex/HttpClient.cls` — Named-Credential-aware callout wrapper
- `templates/apex/tests/MockHttpResponseGenerator.cls` — callout mocks (required in tests)
- `templates/apex/ApplicationLogger.cls` — correlate request IDs across systems
