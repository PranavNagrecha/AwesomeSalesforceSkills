# Integration Pattern Selection — Decision Record Examples

This is this skill's metadata-examples file. The artifact this skill produces is not a
metadata type — it is an **integration decision record** plus the auth metadata every
chosen pattern needs before a single line of it is built.

The routing logic lives in `standards/decision-trees/integration-pattern-selection.md`.
Cite it by question number (`integration-pattern-selection.md Q5`). Do not restate a
branch here; a paraphrase drifts from the tree and the tree is the one that gets updated.

---

## The Record Shape

Store one record per integration, as YAML front matter in a markdown file so it is both
greppable and readable. Every field below is required — `scripts/check_integration_pattern_selection.py --decision-record`
rejects a record that omits one.

```yaml
---
record_id: ADR-INT-0021
requirement: >
  The ERP pushes the previous day's orders into Salesforce every night so that service
  agents see order status on the Account without opening the ERP.
direction: external_to_salesforce   # salesforce_to_external | external_to_salesforce | bidirectional_or_decoupled
volume:
  per_day: 300000                   # peak measured rows per 24 hours, not the sandbox number
  per_request: 10000                # rows per API call / per Bulk batch
latency: batch                      # realtime | near_realtime | batch
idempotency: designed_idempotent    # designed_idempotent | idempotency_key_required | not_guaranteed
who_knows_ids: external_key         # salesforce_ids | external_key | neither
ordering: not_required              # strict | at_least_once | not_required
chosen_pattern: bulk_api_2
tree_questions_cited:
  - "integration-pattern-selection.md Q5 — > 1M rows/day OR bulk upsert routes to Bulk API 2.0; 300k/day with a bulk upsert operation lands on the same branch"
  - "integration-pattern-selection.md Q6 — nightly batch, so Bulk API 2.0"
  - "integration-pattern-selection.md Q7 — the ERP holds no Salesforce Ids but does hold a stable order number, so upsert on an External Id field"
  - "integration-pattern-selection.md Q8 — writes are designed idempotent, so retries are safe on Bulk API 2.0"
rejected:
  - alternative: rest_composite
    reason: >
      Q5 puts REST Composite in the 1k–1M band at up to 200 records per request, which
      means 1,500 requests a night against the org's 24-hour API allocation.
  - alternative: platform_event
    reason: >
      Q8 routes to event ingestion only when idempotency cannot be guaranteed; these
      writes are keyed on the order number and are safe to replay.
auth:
  named_credential: ERP_Orders_NC
  external_credential: ERP_Orders_EC
owner: integrations-platform-team
review_date: 2027-03-01
---
```

### How to read it

- **`tree_questions_cited` is the load-bearing field.** Each entry must name a numbered
  question in `standards/decision-trees/integration-pattern-selection.md` in the form
  `integration-pattern-selection.md Q5`. A record whose reasoning cannot be traced to a
  numbered step is a preference wearing a template.
- **`direction` is picked first, and it is the only branch in the tree.** Q1–Q4 apply to
  Salesforce → external, Q5–Q9 to external → Salesforce, Q10–Q14 to events and
  replication. Within a direction the questions are a checklist, not a graph: every one
  of them applies and each narrows a different axis.
- **`volume.per_day` and `volume.per_request` answer different questions.** Per-day
  decides the mechanism at Q5; per-request decides whether the mechanism's own batching
  ceiling is respected.
- **`who_knows_ids` decides the write shape at Q7.** If the external system holds neither
  Salesforce Ids nor a stable external key, the tree's answer is to go back and require an
  External Id — not to match on name.
- **`ordering` is not a preference either.** Q12 offers strict, at-least-once, and
  "exactly-once required", and the last of those is not natively supported.
- **`auth.named_credential` is mandatory on every record**, including inbound ones where
  the credential belongs to the *outbound* half of the round trip. The tree's
  "Named Credentials — always, not sometimes" section is a repo rule, not a suggestion.
- **`review_date` is not decoration.** Volume changes and a correct pattern expires; the
  date is when someone re-runs the tree with the current numbers.

---

## Worked Decision 1 — ERP Pushes 300k Orders Nightly → Bulk API 2.0 Upsert

**Requirement:** The ERP writes 300,000 order rows into Salesforce between 01:00 and 04:00.
It knows its own order number, not the Salesforce record Id. Re-running a night's file must
not create duplicates.

The record is the one shown above (`ADR-INT-0021`). What follows is the grounding behind it.

### What Bulk API 2.0 actually does with 300,000 rows

| Fact | Number | Source |
|---|---|---|
| Salesforce splits job data into a separate batch for every 10,000 records | 10,000 per batch | Bulk API 2.0 Developer Guide, *Understanding Bulk API 2.0 Ingest* (api_asynch.txt L1242) |
| Daily maximum records uploaded, 24-hour rolling period | 150,000,000 | Developer Limits and Allocations Quick Reference, *Limits Specific to Ingest Jobs* (salesforce_app_limits_cheatsheet.txt L779–L782), and api_asynch.txt L1242 |
| A batch that cannot be processed within this window fails and is retried automatically | 5 minutes, up to 20 retries | api_asynch.txt L1244–L1247; cheat sheet L806–L810 |
| Maximum time an ingest job can remain open | 24 hours | cheat sheet L770–L772 |
| Maximum file size | 150 MB per job (Bulk API 2.0) | cheat sheet L817 |

At 300,000 rows the job is 30 batches, and the daily 150,000,000-record ceiling is not
close to binding. What *is* binding is the 24-hour open-job window and the 5-minute
per-batch processing budget, both of which push toward fewer, wider rows rather than
narrow rows plus lookups.

### The upsert half

`externalIdFieldName` is required for upsert operations, and the field's values must also
exist in the CSV job data (Bulk API 2.0 Developer Guide, *Create a Job* request body,
api_asynch.txt L1611–L1613). The job-create payload:

```json
{
  "object": "Order",
  "externalIdFieldName": "ERP_Order_Number__c",
  "contentType": "CSV",
  "operation": "upsert",
  "lineEnding": "LF"
}
```

That shape is the guide's own upsert example with the object and field renamed
(api_asynch.txt L1439–L1444). Valid `operation` values are `insert`, `delete`,
`hardDelete`, `update` and `upsert` (api_asynch.txt L1622–L1640).

### Reading the results — three endpoints, not one

A `JobComplete` state is not a success report. After a job reaches `JobComplete` or
`Failed`, pull all three result sets (api_asynch.txt L695):

```bash
# Successfully processed records — available in API 41.0 and later (api_asynch.txt L2092-L2097)
sf api request rest "/services/data/v62.0/jobs/ingest/$JOB_ID/successfulResults/" \
  --target-org <alias> > successful.csv

# Records that errored during processing (api_asynch.txt L2138-L2143)
sf api request rest "/services/data/v62.0/jobs/ingest/$JOB_ID/failedResults/" \
  --target-org <alias> > failed.csv

# Records never processed at all — failed or aborted jobs (api_asynch.txt L2185-L2189)
sf api request rest "/services/data/v62.0/jobs/ingest/$JOB_ID/unprocessedrecords/" \
  --target-org <alias> > unprocessed.csv
```

`unprocessedrecords` is the one teams skip, and it is the one that explains a silent
shortfall: results are not recorded at all for batches that exceed the daily batch
allocation (api_asynch.txt L2178). Ingest job results stay retrievable for **7 days** after
job completion unless the job is explicitly deleted (cheat sheet L812–L816) — after that the
evidence of what the night did is gone.

**Hands off to:** `skills/integration/bulk-api-2-patterns` for the job lifecycle, and the
`agents/bulk-migration-planner/AGENT.md` run-time agent for a load plan with a rollback and
reconciliation step.

---

## Worked Decision 2 — User-Triggered Address Validation → Synchronous Apex Callout

**Requirement:** An agent editing a Contact clicks *Validate Address*. An LWC calls Apex,
Apex calls the address-verification provider, and the corrected address comes back into the
form before the agent saves. The provider's published p99 is 900 ms.

```yaml
---
record_id: ADR-INT-0034
requirement: >
  Validate a Contact's mailing address against an external verification provider when the
  agent clicks Validate Address, and return the normalised address to the LWC before save.
direction: salesforce_to_external
volume:
  per_day: 4000                     # agent clicks, measured over a fortnight
  per_request: 1                    # one address per call
latency: realtime
idempotency: designed_idempotent    # validating the same address twice returns the same answer
who_knows_ids: salesforce_ids       # nothing is written outside Salesforce
ordering: not_required
chosen_pattern: apex_callout_named_credential
tree_questions_cited:
  - "integration-pattern-selection.md Q1 — synchronous to a user action and under 10s, so @AuraEnabled Apex to HttpClient over a Named Credential, not a Continuation"
  - "integration-pattern-selection.md Q2 — OAuth 2.0 client credentials, so Named Credential plus External Credential"
  - "integration-pattern-selection.md Q3 — JSON REST payload, so HttpClient with JSON.serialize/deserialize"
  - "integration-pattern-selection.md Q4 — the provider returns transient 5xx under load, so retryOnTransient(true)"
rejected:
  - alternative: continuation
    reason: >
      Q1 routes to Continuation only when the user watches a spinner for up to 120s. A
      900ms p99 does not need the Continuation ceilings, and Continuation is unavailable
      in the async and headless contexts this Apex is also called from.
  - alternative: platform_event
    reason: >
      The agent needs the corrected address in the open form. Any asynchronous pattern
      moves the answer to a later transaction, which is not the requirement.
  - alternative: apex_callout_from_trigger
    reason: >
      Callouts must be made asynchronously from a trigger, so a trigger-based design
      would force @future and lose the synchronous return the requirement is built on.
auth:
  named_credential: AddressVerify_NC
  external_credential: AddressVerify_EC
owner: service-cloud-platform-team
review_date: 2027-06-01
---
```

### The limits this decision is spending

| Limit | Synchronous | Asynchronous | Source (salesforce_app_limits_cheatsheet.txt) |
|---|---|---|---|
| Total callouts (HTTP requests or web services calls) in a transaction | 100 | 100 | L72–L73 |
| Maximum cumulative timeout for all callouts in a transaction | 120 seconds | 120 seconds | L75–L76 |
| Default timeout of a single callout | 10 seconds | 10 seconds | L386–L387 |
| Maximum size of callout request or response | 6 MB | 12 MB | L389–L391 |

Two of those bite here and neither is the one people quote. The **default** timeout is 10
seconds, not 120 — a provider that occasionally takes 12 seconds fails on the default
setting long before the transaction's 120-second cumulative ceiling is reached, so the
timeout has to be set deliberately on the request. And the HTTP request and response sizes
count towards the total heap size (cheat sheet L397, footnote 1 to the Static Apex Limits
table), so a large validation response is spending the same 6 MB the rest of the
transaction is spending.

### The auth metadata the record commits to

The record names a Named Credential, so the Named Credential and its External Credential
are part of the deliverable. Both are deployable metadata:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExternalCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>AddressVerify EC</label>
    <authenticationProtocol>Oauth</authenticationProtocol>
    <externalCredentialParameters>
        <parameterName>ServiceAccount</parameterName>
        <parameterType>NamedPrincipal</parameterType>
        <sequenceNumber>1</sequenceNumber>
    </externalCredentialParameters>
</ExternalCredential>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<NamedCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>AddressVerify NC</label>
    <namedCredentialType>SecuredEndpoint</namedCredentialType>
    <namedCredentialParameters>
        <description>Address verification base URL</description>
        <parameterName>Url</parameterName>
        <parameterType>Url</parameterType>
        <parameterValue>https://api.example-verify.com</parameterValue>
    </namedCredentialParameters>
    <namedCredentialParameters>
        <description>Auth</description>
        <parameterName>DefaultAuth</parameterName>
        <parameterType>Authentication</parameterType>
        <externalCredential>AddressVerify_EC</externalCredential>
    </namedCredentialParameters>
    <allowMergeFieldsInBody>false</allowMergeFieldsInBody>
    <allowMergeFieldsInHeader>false</allowMergeFieldsInHeader>
    <generateAuthorizationHeader>true</generateAuthorizationHeader>
</NamedCredential>
```

**How to read those two blocks**

- `namedCredentialType` valid values are `Legacy`, `PrivateEndpoint`, `SecuredEndpoint` and
  `Standard`; `SecuredEndpoint` is the extensible type that uses external credentials to
  control authentication and permissions, and the field is available in API version 56.0 and
  later (Metadata API Developer Guide, `NamedCredential`, api_meta.txt L90126–L90140).
- `authenticationProtocol` is **required** on `ExternalCredential`. Valid values are
  `AwsSv4`, `Basic`, `Custom`, `Jwt`, `JwtExchange`, `NoAuthentication`, `Oauth` and
  `Password`; the guide marks `Jwt`, `JwtExchange`, `NoAuthentication` and `Password` as
  reserved for future use (api_meta.txt L63641–L63658).
- `ExternalCredential` components have the suffix `.externalCredential`, live in the
  `externalCredentials` folder, and are available in API version 56.0 and later
  (api_meta.txt L63613–L63619). `NamedCredential` components have the suffix
  `.namedCredential`, live in `namedCredentials`, and are available in API version 33.0 and
  later (api_meta.txt L89900–L89906).
- As of Spring '20 and later, only users with the View Setup and Configuration permission
  can access the `NamedCredential` metadata type (api_meta.txt L89909–L89910). A retrieve
  that silently returns nothing is usually this, not an empty org.
- `allowMergeFieldsInBody` and `allowMergeFieldsInHeader` default to `false` and control
  whether Apex may use merge fields to populate the body and header with org data
  (api_meta.txt L89915–L89930). Leave them `false` unless a specific requirement needs them.

**Hands off to:** `skills/apex/callouts-and-http-integrations` for the client,
`skills/integration/named-credentials-setup` for the credential setup, and
`templates/apex/HttpClient.cls` for the callout wrapper the decision names.

---

## Worked Decision 3 — Warehouse Reacts to Opportunity Closed Won → Platform Event or CDC

**Requirement:** When an Opportunity reaches Closed Won, the warehouse system must start
picking. The warehouse is external, subscribes over gRPC, and also wants a running replica
of Opportunity for its own reporting.

```yaml
---
record_id: ADR-INT-0047
requirement: >
  Notify the external warehouse system when an Opportunity is set to Closed Won so it can
  start picking, and keep its Opportunity replica current for warehouse-side reporting.
direction: bidirectional_or_decoupled
volume:
  per_day: 1200                     # Closed Won transitions per 24h at peak quarter-end
  per_request: 1
latency: near_realtime
idempotency: not_guaranteed         # the warehouse cannot promise it will not double-pick
who_knows_ids: salesforce_ids
ordering: at_least_once
chosen_pattern: platform_event
tree_questions_cited:
  - "integration-pattern-selection.md Q10 — Salesforce is the producer of the signal, so route to Q11"
  - "integration-pattern-selection.md Q11 — the subscriber is an external system, so Platform Event published from Salesforce plus a Pub/Sub API gRPC subscriber on the warehouse side"
  - "integration-pattern-selection.md Q12 — at-least-once is acceptable, so the platform-event default stands and the subscriber carries the idempotency"
  - "integration-pattern-selection.md Q14 — the replica is one-way Salesforce to external, so Change Data Capture plus a Pub/Sub API subscriber runs alongside, as a second channel"
rejected:
  - alternative: change_data_capture
    reason: >
      Q11 sends audit and replication targets to CDC, but the picking signal is a business
      event with its own shape ('Closed Won, these line items, this warehouse'), and CDC
      emits the record delta rather than a custom event shape.
  - alternative: outbound_message
    reason: >
      The tree's anti-patterns list Outbound Messages as legacy: their host, Workflow
      Rules, reached end of support on 31 December 2025.
  - alternative: rest_api
    reason: >
      A callout from the Opportunity save couples the close of a deal to warehouse
      availability. Q11 exists precisely to decouple the producer from the subscriber.
auth:
  named_credential: Warehouse_Callback_NC
  external_credential: Warehouse_Callback_EC
owner: order-management-team
review_date: 2027-02-01
---
```

Two channels, one decision: the **event** carries the picking signal, the **CDC stream**
carries the replica. Recording both in one record is the point — the reason CDC is in
`rejected` for the picking signal and simultaneously present at Q14 is exactly the
distinction a reader needs in eighteen months.

### The delivery allocations — what is grounded and what is not

The Developer Limits and Allocations Quick Reference has a *Platform Event Allocations*
chapter that points to three allocation sets — Platform Event Allocations, Change Data
Capture Allocations, and Pub/Sub API and Event Allocations
(salesforce_app_limits_cheatsheet.txt L1244–L1254). The extracted text stops at that
pointer and carries **no numeric delivery allocation**.

UNVERIFIED (2026-09-04): the per-24-hour event delivery allocation by edition, and the
per-24-hour publish allocation, do not appear anywhere in the extracted Summer '26 App
Limits Cheat Sheet, Metadata API, Object Reference, Apex Developer, REST API or Bulk API
text. The cheat sheet names the allocation sets and stops. `standards/decision-trees/integration-pattern-selection.md`
§ Official Sources Used points at the Platform Events Developer Guide page
`platform_event_limits.htm`, which cannot be fetched from this environment. Do not quote a
delivery number in this record; write the org's actual measured figure from
`PlatformEventUsageMetric` instead, and confirm the allocation against the current guide
before quoting it to a customer.

What *is* grounded, and what the record can safely state:

| Fact | Value | Source |
|---|---|---|
| Maximum `EventBus.publish` calls per transaction, for events configured to publish immediately | 150 (sync and async alike) | cheat sheet L102–L103 |
| Apex trigger batch size for platform events and Change Data Capture events | 2,000 | cheat sheet L417–L418 |
| Subscribing from the earliest stored events replays anything less than 72 hours old, and doing so when many messages are stored can slow performance and exhaust the event delivery allocation | 72 hours | Metadata API Developer Guide, `ManagedEventSubscription.defaultReplay` / `errorRecoveryReplay` (api_meta.txt L86613–L86619, L86627–L86634) |
| `CustomObject.publishBehavior` valid values, and the default when the field is omitted | `PublishAfterCommit`, `PublishImmediately`; default `PublishImmediately` | Metadata API Developer Guide, `CustomObject` (api_meta.txt L42206–L42230) |

The `publishBehavior` default is the one that catches teams: omit the field and the event
publishes when the publish call executes, regardless of whether the transaction succeeds.
For a picking signal, that means the warehouse can start picking an Opportunity whose close
then rolled back. Set it explicitly on the event definition:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <deploymentStatus>Deployed</deploymentStatus>
    <description>Emitted when an Opportunity reaches Closed Won and picking may begin.</description>
    <eventType>HighVolume</eventType>
    <label>Order Ready To Pick</label>
    <pluralLabel>Orders Ready To Pick</pluralLabel>
    <publishBehavior>PublishAfterCommit</publishBehavior>
    <fields>
        <fullName>Opportunity_Id__c</fullName>
        <label>Opportunity Id</label>
        <length>18</length>
        <required>true</required>
        <type>Text</type>
    </fields>
    <fields>
        <fullName>Warehouse_Code__c</fullName>
        <label>Warehouse Code</label>
        <length>10</length>
        <required>true</required>
        <type>Text</type>
    </fields>
</CustomObject>
```

The file is `Order_Ready_To_Pick__e.object-meta.xml`. Platform events are `CustomObject`
metadata with the `__e` suffix, and `publishBehavior` applies only to platform events and
only to event messages published through the Lightning Platform — Apex, Process Builder and
Flow Builder — not to those published through Salesforce APIs (api_meta.txt L42206–L42212).

**Hands off to:** `skills/integration/platform-events-integration` and
`skills/integration/pub-sub-api-patterns` for the publish and subscribe sides,
`skills/integration/change-data-capture-integration` for the replica channel, and
`skills/integration/idempotent-integration-patterns` for the subscriber-side dedup that
Q12's at-least-once branch requires.

---

## The Pattern Summary Table — Pointer Only

`standards/decision-trees/integration-pattern-selection.md` § *Pattern summary* is a
13-row table of "best for" and "avoid when" across every mechanism in scope. It is not
reproduced here. Read it there and cite the row; a copy in this file would be a second
source of truth that drifts the first time the tree is updated.

The same applies to § *Security overlays* (transport, AuthN ordering, CRUD/FLS in custom
REST, rate limits, PII under Shield) and § *Anti-patterns* (polling, hand-rolled retry
loops, Bulk API inside a trigger, PushTopic for new work, Outbound Messages,
"we'll just sync everything nightly", custom REST duplicating a standard endpoint).

---

## The Integration Inventory — Before Proposing Anything New

Run this before writing a record. An integration already living in the org is a rejected
alternative you have not written down yet, and a `RemoteSiteSetting` is a hard-coded
endpoint that the tree's Named Credentials rule says should not exist.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>*</members>
        <name>NamedCredential</name>
    </types>
    <types>
        <members>*</members>
        <name>ExternalCredential</name>
    </types>
    <types>
        <members>*</members>
        <name>ConnectedApp</name>
    </types>
    <types>
        <members>*</members>
        <name>PlatformEventChannel</name>
    </types>
    <types>
        <members>*</members>
        <name>PlatformEventChannelMember</name>
    </types>
    <types>
        <members>*</members>
        <name>RemoteSiteSetting</name>
    </types>
    <version>62.0</version>
</Package>
```

```bash
# Retrieve the inventory into a scratch directory (never into the project source dir).
sf project retrieve start --manifest package.xml --target-org <alias> --output-dir ./integration-inventory

# Platform event definitions are CustomObject metadata with the __e suffix; retrieve them by name.
sf project retrieve start --metadata "CustomObject:Order_Ready_To_Pick__e" \
  --target-org <alias> --output-dir ./integration-inventory

# Audit what came back: hard-coded endpoints, publish-immediately events, missing auth.
python3 scripts/check_integration_pattern_selection.py --manifest-dir ./integration-inventory

# Lint the decision record you wrote from it.
python3 scripts/check_integration_pattern_selection.py --decision-record docs/adr/ADR-INT-0021.md
```

What each type tells you, all from the Metadata API Developer Guide (api_meta.txt):

| Type | Suffix / folder | What its presence means | Line |
|---|---|---|---|
| `NamedCredential` | `.namedCredential` / `namedCredentials` | An outbound endpoint that is registered and credential-managed. API 33.0+ | L89900–L89906 |
| `ExternalCredential` | `.externalCredential` / `externalCredentials` | How Salesforce authenticates to that endpoint. API 56.0+ | L63613–L63619 |
| `ConnectedApp` | `.connectedApp` / `connectedApps` | An external app authenticating *into* the org. API 29.0+ | L35035–L35040 |
| `PlatformEventChannel` | `.platformEventChannel` / `platformEventChannels` | A custom channel; `channelType` is `data` (CDC) or `event`. API 45.0+ | L95849–L95856 |
| `RemoteSiteSetting` | `.remoteSite` / `remoteSiteSettings` | A raw registered hostname — the pre-Named-Credential way. API 19.0+ | L103804–L103816 |

Two notes worth carrying into the record:

- **Connected app creation is restricted as of Spring '26.** Existing connected apps can be
  used during and after Spring '26, and Salesforce recommends external client apps instead;
  creating new ones requires contacting Salesforce Support (api_meta.txt L35022–L35026). A
  record whose inbound half says "we'll create a connected app" needs to say why.
- **`PlatformEventChannel.channelType` is required**, and `eventType` (API 61.0+) further
  narrows it to `custom`, `data`, `monitoring` or `standard` (api_meta.txt L95875–L95898).
  A channel with `channelType` `data` is a CDC channel, not a platform-event one.

### Verification step

After the pattern is built, confirm the org agrees with the record. Two queries, both on
objects that support `query()`:

```sql
-- Every Apex trigger, process or flow subscribed to a platform event or change event.
-- Status Error or Suspended means the subscriber stopped receiving events.
SELECT Name, ExternalId, Status, Retries, LastError, LastProcessed, LastPublished, IsPartitioned
FROM   EventBusSubscriber
ORDER  BY Status, Name
```

```sql
-- Measured publish and delivery volume, so the record carries a number rather than a guess.
-- Requires Enhanced Usage Metrics for EventName / UsageType (API 58.0 and later).
SELECT EventName, EventType, UsageType, Client, StartDate, EndDate, Value
FROM   PlatformEventUsageMetric
WHERE  EndDate = LAST_N_DAYS:1
ORDER  BY Value DESC
```

Field grounding, from the Object Reference (object_reference.txt):

| Field | Meaning | Line |
|---|---|---|
| `EventBusSubscriber` | A trigger, process or flow subscribed to a platform event or change event; does *not* include CometD or Pub/Sub API subscribers | L131272–L131274 |
| `EventBusSubscriber.Status` | `Error`, `Repartitioning`, `Running`, `Suspended` | L131376–L131400 |
| `EventBusSubscriber.Retries` | Times the trigger was retried after throwing `EventBus.RetryableException`; Apex triggers only, API 43.0+ | L131370–L131375 |
| `EventBusSubscriber.LastProcessed` / `LastPublished` | Replay Id of the last processed and last published event; replace `Position` and `Tip` as of API 66.0 | L131331–L131339 |
| `PlatformEventUsageMetric.UsageType` | `PUBLISH` or `DELIVERY`; available when Enhanced Usage Metrics is enabled | L221224–L221235 |
| `PlatformEventUsageMetric.Client` | Which surface published or consumed: `PUB_SUB_API`, `EVENT_RELAY`, `REST_API`, `FLOW`, `APEX`, `BULK_API`, `SOAP_API`, `SYSTEM` for CDC publishes | L221070–L221092 |

An `EventBusSubscriber` row in `Error` means the subscriber exceeded its retry budget; the
Object Reference's own guidance is to limit retries to fewer than nine to avoid reaching
that state (object_reference.txt L131382–L131391). If the record's `ordering` field says
`at_least_once`, this query is how you find out whether "at least" turned into "not at all".

For the outbound half, the org's remaining API allocation is readable from the Limits
resource — `GET /services/data/vXX.X/limits/`, which returns `DailyApiRequests` among
others (REST API Developer Guide, api_rest.txt L7799, L7879).

---

## Hand-Off

| Decision lands on | Hand the record to |
|---|---|
| `bulk_api_2` | `skills/integration/bulk-api-2-patterns`; for a migration-shaped load, `agents/bulk-migration-planner/AGENT.md` |
| `rest_api` / `rest_composite` | `skills/integration/rest-api-patterns`, `skills/integration/composite-api-patterns` |
| `custom_rest` | `skills/integration/webhook-inbound-patterns` for the inbound contract, and `skills/admin/api-contract-documentation` for the contract document itself |
| `apex_callout_named_credential` | `skills/apex/callouts-and-http-integrations`, `skills/integration/named-credentials-setup`, `templates/apex/HttpClient.cls` |
| `continuation` | `skills/apex/continuation-callouts` |
| `platform_event` | `skills/integration/platform-events-integration`, `skills/integration/pub-sub-api-patterns` |
| `change_data_capture` | `skills/integration/change-data-capture-integration` |
| `salesforce_connect_odata` | `skills/integration/salesforce-connect-external-objects` |
| `mulesoft_ipaas` | `skills/integration/mulesoft-salesforce-connector`, `skills/architect/mulesoft-anypoint-architecture` |
| Any pattern whose writes are not idempotent | `skills/integration/idempotent-integration-patterns` before the build starts |
| Cataloguing what the org already integrates with | `agents/integration-catalog-builder/AGENT.md` |
| Documenting the contract the chosen pattern exposes | `skills/admin/api-contract-documentation` |
