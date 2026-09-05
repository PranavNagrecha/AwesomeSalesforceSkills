# Gotchas — Integration Pattern Selection

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Salesforce Cannot Participate in Distributed Transactions Across Multiple Systems

**What happens:** When architects design multi-system orchestration in Apex — calling ERP, shipping, and billing systems in sequence — Salesforce DML can be rolled back on an Apex exception, but external system calls that succeeded before the exception cannot be reversed. If the billing system call fails at step 3, ERP and shipping already created records that cannot be undone by the Apex transaction rollback. The systems are left in an inconsistent state.

**When it occurs:** Whenever an Apex trigger or scheduled job makes multiple sequential HTTP callouts to different external systems and tries to handle failure by catching exceptions.

**How to avoid:** Multi-system transactions with cross-system rollback requirements must be orchestrated by middleware (MuleSoft, Boomi). Salesforce participates as an endpoint (Remote Call-In) or as an event source (fires a Platform Event); it does not orchestrate the cross-system transaction.

---

## Gotcha 2: Synchronous Callout Timeout Is 120 Seconds — Not Indefinite

**What happens:** Apex HTTP callouts timeout after 120 seconds. If an external system takes longer than 120 seconds to respond — common for high-latency ERP systems, large file processing, or ML inference endpoints — the callout throws a System.CalloutException and the Salesforce transaction may rollback. Any Salesforce DML that was part of the same transaction is also rolled back.

**When it occurs:** When a synchronous Request/Reply pattern is chosen for integrations with external systems that do not have guaranteed sub-120-second response times.

**How to avoid:** Apply the timing test rigorously: if the external system cannot guarantee sub-60-second responses (allowing margin), the integration must use an asynchronous Fire-and-Forget pattern with a callback mechanism. Never choose synchronous for integrations with unknown or variable external response times.

---

## Gotcha 3: Platform Events Are Eventually Consistent — Not Guaranteed Delivery

**What happens:** Platform Events have a 72-hour replay window, and EventBus.RetryableException provides up to 9 automatic retries. After 9 failures, the subscriber trigger is suspended and does not process new events until manually re-enabled. Events that were published while the trigger was suspended are replayed only if the Replay ID mechanism works correctly — Replay ID can be stale after Salesforce maintenance events.

**When it occurs:** When Platform Events are selected as the Fire-and-Forget mechanism without designing a dead-letter monitoring and trigger suspension recovery pattern.

**How to avoid:** Any integration using Platform Events must include: (1) monitoring for trigger suspension, (2) a dead-letter queue pattern for failed events, and (3) a replay recovery procedure after org maintenance windows. Do not select Platform Events for integrations that require guaranteed single delivery or strong ordering guarantees.

**Grounding for the two numbers above.** The 72-hour figure is documented: subscribing from the earliest stored events sends new events and any others less than 72 hours old (Metadata API Developer Guide, `ManagedEventSubscription.defaultReplay`, api_meta.txt L86613–L86619). The "9 retries" figure is a *recommendation*, not a documented hard ceiling: the Object Reference's `EventBusSubscriber.Status` entry says a trigger reaches the `Error` state when it exceeds the maximum retries with `EventBus.RetryableException`, and recommends limiting retries to fewer than nine times to avoid reaching that state (object_reference.txt L131382–L131391). It also states that trigger assertion failures and unhandled exceptions do *not* cause the error state. Design to the recommendation; do not quote nine as a platform limit.

---

## Gotcha 4: REST Volume Is Bounded By The Org's 24-Hour API Allocation, Not By The Endpoint

**What happens:** A pattern chosen on latency alone ("REST, because it's real-time") spends
a shared, org-wide, 24-hour budget that nothing in the integration's own design mentions.
Developer Edition orgs get 15,000 total calls per 24 hours. Enterprise and Professional
(with API access) orgs get 100,000 plus the number of licences times the per-licence rate
plus any purchased API Call Add-Ons, where a full Salesforce licence is worth 1,000 calls
per 24 hours and a Lightning Platform - One App licence is worth 200. Unlimited and
Performance orgs use the same formula with 5,000 per Salesforce licence. Community and
Partner Community Login licences contribute 10 each, and Customer Community contributes 0
(Developer Limits and Allocations Quick Reference, *Total API Request Allocations*,
salesforce_app_limits_cheatsheet.txt L516–L560). Exceed it and the API returns
`REQUEST_LIMIT_EXCEEDED` with HTTP 403 (REST API Developer Guide, api_rest.txt L1145–L1146).

There is a second, separate ceiling that has nothing to do with the daily one: concurrent
inbound requests lasting 20 seconds or longer are capped at 25 in production orgs and
sandboxes, and 5 in Developer Edition and Trial orgs. Exceeding it also returns
`REQUEST_LIMIT_EXCEEDED`, and no new concurrent requests are processed until the count
drops below the limit. There is no limit on concurrent requests shorter than 20 seconds
(cheat sheet L481–L496).

**When it occurs:** Any external → Salesforce design that sizes itself on records rather
than requests. A 300,000-row nightly file at 200 records per sObject Collections request is
1,500 calls; the same file record-by-record is 300,000 calls, which no Enterprise org's
allocation absorbs alongside its normal traffic.

**How to avoid:** Convert the volume into *requests* before choosing, and take the
`integration-pattern-selection.md` Q5 branch on that number. When REST is genuinely right,
batch it: an sObject Collections request carries up to 200 records and the entire request
counts as a single call toward the API limits (api_rest.txt L22642–L22652). Read the org's
remaining headroom from `GET /services/data/vXX.X/limits/`, which returns
`DailyApiRequests` (api_rest.txt L7799, L7879), and record the measured number in the
decision record's `volume` block.

---

## Gotcha 5: Callouts Must Be Asynchronous From A Trigger — And Any Pending DML Blocks Them Anyway

**What happens:** Two separate platform rules make "call the API from the trigger" fail, and
they fail differently. First, the Apex Developer Guide states that callouts must be made
asynchronously from a trigger, so that the trigger process is not blocked while waiting for
the external service's response; the asynchronous callout runs in a background process and
the response arrives when the external service returns it (apexdev.txt L14900–L14903).
Second, even outside a trigger, a callout attempted while DML is uncommitted throws
`System.CalloutException` carrying `You have uncommitted work pending. Please commit or
rollback before calling out.`, and an unreleased savepoint throws `All active Savepoints
must be released before making callouts.` (apexdev.txt L8742–L8771).

**When it occurs:** Every "just add an HTTP callout to the trigger handler" design, and
every synchronous callout placed after an insert or update in the same Apex transaction.

**How to avoid:** Treat this as a pattern-selection constraint, not an implementation
detail. When `integration-pattern-selection.md` Q1 says "No, fire-and-forget", the answer is
a Queueable with `AllowsCallouts` — that is the branch, and it is chosen at decision time so
that the record's `latency` field says `near_realtime` rather than `realtime`. If the
business genuinely needs the answer inside the user's transaction, the trigger is the wrong
entry point: move to an `@AuraEnabled` Apex call from the UI (Q1, "Yes, under 10s") where no
DML is pending.

---

## Gotcha 6: A Bulk Job Is Asynchronous, And Its Evidence Expires In Seven Days

**What happens:** Bulk API 2.0 accepts the upload and returns immediately; the work happens
later, in batches Salesforce creates on its own — one batch for every 10,000 records
(api_asynch.txt L1242). A batch that cannot be processed within 5 minutes fails and is
retried automatically up to 20 times; after 20 retries the entire ingest job moves to
`Failed` and the remaining job data is not processed (api_asynch.txt L1244–L1247). Nothing
in the caller's response body says any of this happened. The ingest job's results —
successful, failed and unprocessed records — can be retrieved for **7 days** after job
completion, unless the job is deleted explicitly (salesforce_app_limits_cheatsheet.txt
L812–L816). An ingest job can also stay open for a maximum of 24 hours (cheat sheet
L770–L772).

**When it occurs:** Any nightly load whose monitoring is "the job returned 200". The
discrepancy surfaces on day nine, when someone asks which rows did not land and the results
endpoints have nothing left to return.

**How to avoid:** Make the decision record commit to pulling all three result sets —
`successfulResults`, `failedResults` and `unprocessedrecords` (api_asynch.txt L2092–L2097,
L2138–L2143, L2185–L2189) — and to archiving them outside Salesforce inside the 7-day
window. `unprocessedrecords` is the one that matters: results are not recorded at all for
batches that exceed the daily batch allocation (api_asynch.txt L2178), so a short
`successfulResults` file with an empty `failedResults` file is not a clean run.

---

## Gotcha 7: Event Retention Is 72 Hours, And Catching Up Spends The Same Allocation It Is Recovering From

**What happens:** A subscriber that reconnects and asks for the earliest stored events gets
new events plus any others less than 72 hours old. The Metadata API guide's own advice on
that option is to use it sparingly: subscribing with `EARLIEST` when a large number of event
messages are stored can slow performance and exhaust the event delivery allocation
(Metadata API Developer Guide, `ManagedEventSubscription.defaultReplay` and
`errorRecoveryReplay`, api_meta.txt L86613–L86619 and L86627–L86634). A replay that is meant
to recover a gap therefore competes for the same budget the gap came out of, and anything
older than the window is simply gone.

There is a second failure mode on the Apex side: a subscriber that exceeds its retry budget
lands in `EventBusSubscriber.Status = Error` and stops receiving published events; the
Object Reference recommends limiting retries to fewer than nine to avoid reaching that state
(object_reference.txt L131382–L131391).

**When it occurs:** After any subscriber outage longer than a weekend, and after any
deployment that suspends a platform-event trigger.

**How to avoid:** Do not choose an event pattern for data whose loss is unacceptable beyond
72 hours without a separate reconciliation channel — that is what the
`integration-pattern-selection.md` Q14 replication branch is for. Record `ordering:
at_least_once` honestly rather than aspirationally, and query `EventBusSubscriber` on a
schedule so a `Suspended` or `Error` status is discovered inside the retention window rather
than after it.

---

## Gotcha 8: An External Id That Is Not Unique Turns An Upsert Into HTTP 300

**What happens:** Upsert on an External Id field assumes exactly one match. When the value
exists in more than one record, the REST API returns **300**, and the response body contains
the list of matching records rather than a saved record (REST API Developer Guide, *Status
Codes and Error Responses*, api_rest.txt L1134–L1135). A 300 is not in the 2xx family and is
not in the 4xx family, so integration code that branches on "status < 400 means success"
treats a silent non-write as a success.

**When it occurs:** The first time a legacy source system re-issues a key, or the first time
an External Id field is created without the Unique attribute — which the platform allows.

**How to avoid:** Make `who_knows_ids: external_key` in the decision record a claim that has
been checked, not assumed: confirm the field is marked Unique before the pattern is
approved, and require the client to treat 300 as a hard failure with the returned record
list logged. This is the concrete reason `integration-pattern-selection.md` Q7's third
branch ("No, reference by name") is marked strongly discouraged.

---

## Gotcha 9: A Platform Event Published Immediately Fires Even When The Transaction Rolls Back

**What happens:** `CustomObject.publishBehavior` has two values. `PublishAfterCommit`
publishes the event message only after a transaction commits successfully, and not at all if
the transaction fails. `PublishImmediately` publishes when the publish call executes,
regardless of whether the transaction succeeds. **If the field is not specified, the default
is `PublishImmediately`** (Metadata API Developer Guide, `CustomObject`, api_meta.txt
L42206–L42230). The behaviour applies to event messages published through the Lightning
Platform — Apex, Process Builder and Flow Builder — and not to those published through the
Salesforce APIs (api_meta.txt L42206–L42212).

**When it occurs:** Any event definition deployed without the field, which is the shape most
generated metadata takes. Downstream systems then act on records that were rolled back — an
order picked for a deal that never closed.

**How to avoid:** Set `publishBehavior` explicitly on every event definition, and record the
choice in the decision record beside the pattern. The related per-transaction ceiling is
worth carrying too: a transaction allows a maximum of 150 `EventBus.publish` calls for
platform events configured to publish immediately (salesforce_app_limits_cheatsheet.txt
L102–L103), and the Apex trigger batch size for platform events and Change Data Capture
events is 2,000 (cheat sheet L417–L418).

---

## Gotcha 10: A Remote Site Setting Is A Hard-Coded Endpoint The Org Still Honours

**What happens:** `RemoteSiteSetting` is the pre-Named-Credential mechanism: before any
Visualforce page, Apex callout, or JavaScript using `XmlHttpRequest` in an s-control or
custom button can call an external site, that site must be registered in Remote Site
Settings or the call fails (Metadata API Developer Guide, api_meta.txt L103804–L103808). It
still works, so nothing complains. The hostname lives in metadata and the credential lives
wherever the developer put it — commonly a Custom Setting or an Apex constant, which the
tree's Named Credentials section forbids outright.

**When it occurs:** In any org older than the Named Credential feature, and in any new
integration copied from an older one.

**How to avoid:** Retrieve `RemoteSiteSetting` as part of the integration inventory (see
`references/decision-record-examples.md` § *The Integration Inventory*) and treat every row
as an open question about where its secret is stored. New records must name a Named
Credential in the `auth` block; the checker script fails a record that does not. One related
constraint to design around: connected app creation is restricted as of Spring '26 —
existing connected apps still work during and after Spring '26, Salesforce recommends
external client apps instead, and creating new connected apps requires contacting Salesforce
Support (api_meta.txt L35022–L35026).
