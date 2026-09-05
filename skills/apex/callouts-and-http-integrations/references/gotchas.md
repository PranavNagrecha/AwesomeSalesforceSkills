# Gotchas — Callouts And HTTP Integrations

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

Line references are into the **Apex Developer Guide v67.0, Summer '26** (`apexdev`), the **Apex
Reference Guide v67.0** (`apexrefguide`), the **Metadata API Developer Guide** (`api_meta`) and the
**Salesforce App Limits Cheat Sheet** (`cheatsheet`).

## Gotcha 1: DML And Callouts In The Same Transaction Need Careful Boundaries

**What happens:** the callout never leaves the org. `System.CalloutException` carries the exact text
`You have uncommitted work pending. Please commit or rollback before calling out.` (apexdev
L8769–8770).

**When it occurs:** the trigger for it is broader than "an `insert` ran". The guide lists four
sources of pending work: "DML operations, queueable jobs (that are queued with
System.enqueueJob), Database.executeBatch, or future methods" (apexdev L35379–35380), and repeats
the list as "DML statements, asynchronous Apex (such as future methods and batch Apex jobs),
scheduled Apex, or sending email" (apexdev L35861–35862). A method that only *enqueues* a job and
then calls out fails the same way a method that inserted a record does.

**How to avoid:** the ordering rule is directional, not symmetric. "You can make callouts before
performing these types of operations" (apexdev L35862–35863) — callout first, then DML, is always legal;
DML first, then callout, is not. When the save must happen first, hand the callout to a separate
transaction (`BillingSyncQueueable` in `references/code-examples.md`).

---

## Gotcha 2: An Unreleased Savepoint Blocks The Callout Even After A Rollback

**What happens:** a different `CalloutException`, with a different message: `All active Savepoints
must be released before making callouts.` (apexdev L8747–8748). Rolling back is not enough — the
savepoint handle itself is the blocker.

**When it occurs:** any `Database.setSavepoint()` still live when `Http.send()` runs. The guide's
own worked example rolls back *and* calls `Database.releaseSavepoint(sp)` before the callout
succeeds (apexdev L8725–8740). Two further traps: released savepoints do not undo pending work —
"If there's uncommitted work pending when `Database.releaseSavepoint()` is called, the uncommitted
work isn't rolled back. It's committed if the transaction succeeds" (apexdev L8774–8776) — and
releasing one savepoint "also releases nested savepoints" (apexdev L8781–8782).

**How to avoid:** in a method that both guards with a savepoint and calls out, roll back, then
release, then call out — in that order. In tests at **API version 60.0 or later** the platform does
it for you: "all savepoints are released when `Test.startTest()` and `Test.stopTest()` are called"
and a `SAVEPOINT_RESET` event is logged (apexdev L8786–8788). Below 60.0, "making a callout after
creating savepoints throws a `CalloutException` regardless of whether there was uncommitted DML"
(apexdev L8789–8791) — so a test that passes on an old-API class can fail after an API bump, or the
reverse.

---

## Gotcha 3: `setTimeout()` Caps The Connection, Not The Whole Request

**What happens:** a request with `setTimeout(5000)` blocks for far longer than five seconds, and the
transaction dies against the cumulative budget instead of returning a clean timeout.

**When it occurs:** whenever the remote server accepts the connection quickly and then streams
slowly. The reference is explicit: the value sets "a timeout for the request between 1 and 120,000
milliseconds. The timeout is the maximum time to wait for **establishing the HTTP connection**. The
same timeout is used for waiting for the request to start. When the request is executing, such as
retrieving or posting data, **the connection is kept alive until the request finishes**"
(apexrefguide L216720–216723, emphasis added).

**How to avoid:** treat `setTimeout` as a connect guard and the platform's two hard ceilings as the
real bound: 100 callouts per transaction (apexdev L35844) and "maximum cumulative timeout for
callouts by a single Apex transaction is 120 seconds … additive across all callouts invoked by the
Apex transaction" (apexdev L35856–35857). Budget backwards from 120 s: `n × timeout ≤ 120,000` is
the arithmetic that decides how many records one job may process. Anything the remote system cannot
finish inside that envelope needs a Continuation, whose per-continuation timeout is a separate
120 s and which **ignores** `HttpRequest.setTimeout` entirely (apexdev L36303, L36314–36315).

---

## Gotcha 4: A Request Body On A GET Silently Turns It Into A POST

**What happens:** the remote system logs a `POST` where the Apex reads `setMethod('GET')`, and a
read-only endpoint either 405s or, worse, creates something.

**When it occurs:** any request that sets both. "When you set a request body in the callout, set the
method to POST. If you set a request body and the request method is GET, **a POST request is
performed**" (apexdev L35377–35378). This is a silent coercion — no exception, no warning.

**How to avoid:** never call `setBody`/`setBodyAsBlob` on a GET. Query parameters go on the endpoint,
where a Named Credential URL accepts them: "You can append a query string to a named credential URL.
Use a question mark (?) as the separator" (apexdev L34335–34336). The checker in `scripts/` flags
`setBody` in a method whose `setMethod` is `GET`.

---

## Gotcha 5: The 6 MB / 12 MB Payload Cap Is Also A Heap Cap

**What happens:** a large response either fails the callout or blows the heap a few lines later,
while the record count looks perfectly modest.

**When it occurs:** "Maximum size of callout request or response (HTTP request or Web services
call): **6 MB for synchronous Apex or 12 MB for asynchronous Apex**" (cheatsheet L389–391; the same
limit is restated per-method at apexrefguide L216506 for `setBody`, L216863 for `getBody`, L216887
for `getBodyAsBlob`). The footnote is the part that bites: "The HTTP request and response sizes
count towards the total heap size" (cheatsheet L415). Total heap is itself 6 MB sync / 12 MB async
(apexdev L19577). So a 5 MB synchronous response leaves roughly 1 MB for everything else in the
transaction, and `JSON.deserialize` allocates a second copy of what it parses.

**How to avoid:** page the remote API rather than pulling one large document, and run anything above
a megabyte in asynchronous context for the doubled ceiling. `HttpRequest.setCompressed(true)`
compresses what you send, and on the way back "if a response comes back in compressed format,
`getBody` recognizes the format, uncompresses it, and returns the uncompressed value" (apexrefguide
L216278–216279) — which means compression does **not** buy you headroom against these limits, since
the uncompressed value is what lands on the heap.

---

## Gotcha 6: Individual Header Values Cap At 100 KB

**What happens:** a callout carrying a large bearer token, a signed assertion, or a serialized
context header fails on the header rather than on the body, so the error points at the wrong place.

**When it occurs:** `HttpRequest.setHeader(key, value)` carries a documented "Limit 100 KB"
(apexrefguide L216680). This is separate from the 6 MB/12 MB body cap in Gotcha 5.

**How to avoid:** keep per-request identity out of Apex-built headers. A Named Credential's
`HttpHeader` parameter type "allows the user to specify custom headers to be added to the callout at
run time" with `parameterValue` as "a formula of a header value that is evaluated at run time"
(api_meta L90326–90331), and `generateAuthorizationHeader` (default `true`, api_meta L90040–90046)
means Salesforce writes `Authorization` for you. If your Apex is constructing an auth header by
hand, the Named Credential is misconfigured.

---

## Gotcha 7: Queueable Callouts Require `Database.AllowsCallouts`

**What happens:** the class compiles, the job enqueues, `AsyncApexJob` shows it ran, and the callout
inside it fails.

**When it occurs:** the interface is the switch, not the code: "Apex allows HTTP and web service
callouts from queueable jobs, **if they implement the `Database.AllowsCallouts` marker interface**.
In queueable jobs that implement this interface, callouts are also allowed in chained queueable
jobs" (apexdev L16164–16166). The same marker gates Batch Apex (apexdev L17508–17510). Future
methods use a different switch entirely — `@Future(callout=true)`, where "the default is
`(callout=false)`, which prevents a method from making callouts" (apexdev L5134–5135).

**How to avoid:** treat callout-capable async as a two-part declaration: `implements Queueable,
Database.AllowsCallouts` for a job, `@Future(callout=true)` for a future method. The checker flags a
`Queueable` that references `Http` without the marker, and a `@future` without `callout=true`.

---

## Gotcha 8: Named Credential Design Affects User Context

**What happens:** the integration works for the admin who built it and fails for a subset of users,
usually with a 401 that looks like an outage.

**When it occurs:** the principal type on the External Credential decides this. `NamedPrincipal`
"specifies that the parameter uses the same set of user credentials for all users who access the
external system"; `PerUserPrincipal` "provides access control at the individual user level"
(api_meta L63806–63808). With `PerUserPrincipal`, any user who has not authenticated individually
has no credential to send. There is also a version trap: the `principal` field that used to point
the External Credential at a permission set was "First available in API version 56.0, this field is
removed in API version 58.0 and later" (api_meta L63830–63831), so a credential deployed from an
older source tree can land with nobody granted access to it.

**How to avoid:** decide the identity model before writing Apex, default to `NamedPrincipal` unless
the remote system genuinely needs end-user delegation, and verify principal access is granted by
permission set in the target org rather than assuming the metadata carried it. Setup access is
itself restricted: "As of Spring '20 and later, only users with the View Setup and Configuration
permission can access this type" (api_meta L89909).

---

## Gotcha 9: A Test That Performs A Callout Fails Unless A Mock Is Registered — And The Statement Order Matters

**What happens:** the test fails on the callout, not on an assertion, and the message points at the
callout rather than at the missing mock.

**When it occurs:** "By default, test methods don't support HTTP callouts, so tests that perform
callouts fail" (apexdev L35384–35385). The subtler failure is a test that *does* register a mock but
inserts test data first: DML before a mock callout produces exactly the pending-work exception from
Gotcha 1. The escape has a required order — "enclose the portion of your code that performs the
callout within `Test.startTest` and `Test.stopTest` statements. **The `Test.startTest` statement
must appear before the `Test.setMock` statement.** Also, the calls to DML operations must not be
part of the `Test.startTest`/`Test.stopTest` block" (apexdev L35678–35681). The same applies to
asynchronous calls in a test (apexdev L35737–35745).

**How to avoid:** the fixed shape is: insert data → `Test.startTest()` → `Test.setMock(...)` →
exercise → `Test.stopTest()` → assert. Note the reverse direction is free: "DML operations that occur
after mock callouts are allowed and don't require any changes in test methods" (apexdev L35681). For
`HttpCalloutMock` implementation detail — routing, sequences, static resources — see
apex/apex-http-callout-mocking.

---

## Gotcha 10: Tests Must Simulate Both Success And Failure

**What happens:** the happy-path mock returns `200`, coverage is green, and production fails on a
`401`, a `429`, or a `200` carrying an HTML maintenance page.

**When it occurs:** whenever one mock instance answers every call. A single `HttpCalloutMock` whose
`respond` "returns an HTTP response for the given request" (apexrefguide L216190–216192) will happily
return the same 200 to a retry test, so a retry ladder is never actually exercised. Static-resource
mocks (`StaticResourceCalloutMock`, `MultiStaticResourceCalloutMock`, apexdev L35497–35595) have the
same property per resource.

**How to avoid:** assert on the *classification*, not on the parsed body — success, retryable,
non-retryable, malformed — and use a sequence-capable mock so a 500-then-200 pair proves the retry
actually happened. `templates/apex/tests/MockHttpResponseGenerator.cls` has `pushSequence(status,
body)` for exactly this.

---

## Gotcha 11: Callouts Still Execute In Read-Only Mode, But The Follow-Up DML Does Not

**What happens:** during a Salesforce read-only maintenance window the external system is called,
does its work, and Salesforce cannot record that it happened. The next run calls it again.

**When it occurs:** "During read-only mode, Apex callouts to external services execute and aren't
blocked by the system … But write operations in Salesforce, such as record updates, are blocked
during read-only mode. This inconsistency in behavior in read-only mode can break your program flow
and causes issues" (apexdev L35869–35874).

**How to avoid:** the guide's own recommendation is to skip the callout: check
`System.getApplicationReadWriteMode()` and proceed only when the value is not
`ApplicationReadWriteMode.READ_ONLY` (apexdev L35875–35880). This matters most for non-idempotent
POSTs — which is the second reason the `Idempotency-Key` header in `references/code-examples.md`
earns its place.

---

## Gotcha 12: Two Small Environment Limits That Only Bite In Specific Orgs

**What happens:** an integration that passes in a scratch org or Developer Edition behaves
differently in a full sandbox, or a request hangs on a header nobody wrote deliberately.

**When it occurs:**
- **Developer Edition concurrency.** "In Developer Edition orgs, you can only make up to 20
  concurrent callouts to endpoints outside of your Salesforce org's domain. This limit doesn't apply
  to non-Developer Edition orgs" (apexdev L35852–35853). A parallel-batch design that passes DE is
  not proof it scales, and one that fails DE may be fine in production.
- **`Expect: 100-Continue`.** "When the header `Expect: 100-Continue` is added to a callout request
  and a `HTTP/1.1 100 Continue` response isn't returned by the external server, a timeout occurs"
  (apexdev L35866–35867). Some HTTP libraries and proxies add this header for large bodies; against
  a server that does not implement it, every large POST times out.

**How to avoid:** run load-shaped tests in a sandbox that matches the production edition, and never
set `Expect` explicitly unless the remote system has confirmed it honours the handshake.
