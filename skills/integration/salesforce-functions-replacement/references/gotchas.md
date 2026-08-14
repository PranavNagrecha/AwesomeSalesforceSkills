# Gotchas — Salesforce Functions Replacement

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Heroku kills the request at 30 seconds and does not tell your code

**What happens:** The natural lift-and-shift for a long-running Function is a
Heroku web dyno behind a Named Credential callout. Heroku's router terminates
any web request that takes longer than **30 seconds** — "The timeout value is not
configurable" — and logs error **H12**. Worse, per Heroku's own docs: "your
application will not know that the request it is processing has reached a
time-out, and your application will continue to work on the request." The dyno
is then poisoned for everyone else: "Subsequent requests may then be routed to
the same process which will be unable to respond (depending on the concurrency
behavior of the application's language/framework) causing further degradation."

**When it occurs:** Exactly the workloads that justified Functions in the first
place. Heroku's own list of work that belongs in a background job names
"Rendering an image or PDF", "Heavy computation (computing a fibonacci sequence,
etc.)", "Heavy database usage (slow or numerous queries, N+1 queries)",
"Accessing a remote API", "Sending an email", and "Web scraping / crawling".

**How to avoid:** Do not port a >30 s Function to a synchronous web endpoint.
Split it: the web dyno accepts the job, returns `202 Accepted` with a job id
immediately, and a worker dyno does the work and writes the result back to
Salesforce over the REST API or a Platform Event. Apex then either polls the job
id from a Queueable or subscribes to the completion event. The mistake is
architectural, not configurable — there is no Heroku setting that makes the
30-second cap go away.

---

## Gotcha 2: Apex's 120-second callout budget is a *transaction* budget, not a per-call one

**What happens:** Per the Apex Developer Guide: "The default timeout is 10
seconds... the minimum is 1 millisecond and the maximum is 120,000
milliseconds," and "The maximum cumulative timeout for callouts by a single Apex
transaction is 120 seconds. This time is additive across all callouts invoked by
the Apex transaction." Teams set `req.setTimeout(120000)` on every callout to be
safe, then fan out to three external services in one transaction and the third
callout dies regardless of its own timeout.

**When it occurs:** Any Function that was decomposed into several external calls
during migration — a common outcome when one Function becomes one microservice
per responsibility.

**How to avoid:** Budget the 120 seconds explicitly across the callouts in a
transaction and set each `setTimeout` to its real ceiling, not the maximum. If
the total genuinely exceeds 120 s, the work is not a synchronous callout — it is
an async job with a callback. `templates/apex/HttpClient.cls` defaults
`timeoutMs` to 30000 and exposes `.timeoutMs(Integer)` for this reason.

---

## Gotcha 3: Moving compute into Apex means the 10-second CPU wall, not the 60-second one

**What happens:** "Simple enough to move to Apex" gets validated against the
asynchronous limit and then deployed into a synchronous path. The Apex governor
limits are **10,000 ms** maximum CPU time for synchronous Apex and **60,000 ms**
for asynchronous, with heap at **6 MB** sync and **12 MB** async. A trigger-path
rewrite of a Function gets the 10-second number and half the heap.

**When it occurs:** Enrichment logic that used to run in a Function invoked from
a trigger. Keeping the trigger entry point keeps the synchronous limits.

**How to avoid:** Decide the execution context before you decide the language. If
the rewrite is going into Apex, put it in a Queueable so it gets 60,000 ms and
12 MB, and confirm the workload fits with realistic bulk data — not a
single-record test. CPU time is measured on Salesforce application servers only;
time spent waiting on a callout does not count toward it, which is why a
callout-heavy rewrite can pass CPU and still fail on the 120-second callout
budget from Gotcha 2.

---

## Gotcha 4: The retirement date is fixed and the SOQL/DML row budget travels with the caller

**What happens:** Salesforce Functions retired on **January 31, 2025**. The
official notice is unambiguous: "Salesforce Functions is retiring on January 31,
2025. To keep the functionality of the functions deployed to your org, migrate
them to a different product before the end-of-life date." Any org still invoking
a Function is already broken, not approaching breakage.

**When it occurs:** Discovery on legacy orgs, where a Function invocation sits in
a rarely-exercised path (an annual batch, a quarterly close) and nobody noticed
it stopped.

**How to avoid:** Do not scope the migration from the Functions project
directory — scope it from *invocation sites*. Search the org's Apex for
`Function.get(` and `functions.Function` references, and search Flow and
Platform Event subscribers, before declaring the inventory complete. A Function
that is dead code should be deleted with the same ceremony as one being
replaced, so the inventory reaches zero rather than "zero that we found".

---

## Gotcha 5: The replacement inherits the *caller's* limits, which Functions did not

**What happens:** Functions ran outside the Apex transaction, so a Function that
queried 200,000 rows or made 500 HTTP calls did not consume the calling
transaction's budget. A Heroku or container replacement called synchronously from
Apex sits *inside* the transaction: its callout counts against the **100 callouts
per transaction** limit, its round trip counts against the 120-second cumulative
callout timeout, and any records the Apex caller then writes count against DML
limits. The transaction that used to hand work away now carries it.

**When it occurs:** The migration looks correct in a unit test with one record and
fails on the first bulk operation.

**How to avoid:** Push the boundary back out. Have Salesforce publish a Platform
Event or have the external service pull from Salesforce over the REST or Bulk
API, so the heavy path is not inside an Apex transaction at all. Where a
synchronous callout is genuinely required, make it one callout per transaction
carrying a batched payload, never one callout per record.

---

## Gotcha 6: A dyno is not a compliance boundary by itself

**What happens:** PII or regulated data that was flowing through a Function gets
re-pointed at a standard Heroku dyno on the assumption that "Heroku is
Salesforce, so it is covered". Compliance posture on Heroku is a function of the
plan and space type, not of ownership. Standard dynos do not carry the isolation
and controls that regulated workloads require.

**When it occurs:** Health, financial services, education, and public sector
migrations, where the Function was handling record data subject to a BAA or an
equivalent contractual control.

**How to avoid:** Confirm the required compliance posture with Salesforce/Heroku
for the specific plan and space before any regulated data crosses the boundary,
and get it in writing — this is a contractual question, not a documentation one.
Independently of that, minimise what crosses: send record Ids and let the service
call back for field data under a scoped integration user, rather than pushing
full payloads outward.
