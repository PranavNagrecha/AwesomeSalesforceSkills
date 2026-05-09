# LLM Anti-Patterns — Scheduled ERP Sync Pattern

Common mistakes AI assistants make when generating or advising on Scheduled ERP Sync. Avoid these when producing recommendations or code.

---

## Anti-Pattern 1: Putting the callout directly in the Schedulable

**What the LLM generates:**

```apex
public class ErpSyncScheduler implements Schedulable {
    public void execute(SchedulableContext sc) {
        Http http = new Http();
        HttpRequest req = new HttpRequest();
        req.setEndpoint('https://erp.example.com/api/invoices');  // also wrong: hardcoded URL
        req.setMethod('GET');
        HttpResponse res = http.send(req);   // <— throws CalloutException
        // ...
    }
}
```

**Why it happens:** LLMs see "scheduled job that calls an API" and generate the most direct expression of the idea. The platform restriction that Schedulable contexts cannot do callouts is a non-obvious Salesforce-ism not present in most general-purpose schedulers (cron, Java `@Scheduled`, etc.).

**Correct pattern:**

```apex
public class ErpSyncScheduler implements Schedulable {
    public void execute(SchedulableContext sc) {
        System.enqueueJob(new ErpInvoicePullQueueable(Datetime.now(), ...));
    }
}
public class ErpInvoicePullQueueable implements Queueable, Database.AllowsCallouts {
    public void execute(QueueableContext qc) {
        // callouts allowed here
    }
}
```

**Detection hint:** Search for `implements Schedulable` and look for `Http` / `http.send` / `HttpRequest` in the same class body. If both appear together it is wrong.

---

## Anti-Pattern 2: `insert` instead of `Database.upsert(records, ExternalId)`

**What the LLM generates:**

```apex
List<Account> accs = parseErpResponse(res.getBody());
insert accs;   // <— duplicates on every retry
```

**Why it happens:** LLMs default to the simplest DML verb. `insert` is shorter and more familiar; `upsert` requires the External ID parameter and the External ID field to be configured. Without explicit grounding in the idempotency requirement, models pick `insert`.

**Correct pattern:**

```apex
List<Account> accs = parseErpResponse(res.getBody());
// External_Id__c is marked External ID + Unique on the Account object
Database.upsert(accs, Account.External_Id__c, false);
```

**Detection hint:** Search for `insert` or `Database.insert` in any code that processes ERP-fetched payloads. If the records are inbound from an external system, this is almost always wrong — should be `upsert` keyed on an External ID.

---

## Anti-Pattern 3: `Thread.sleep` or `while (Limits.getCpuTime() < N) {}` to implement backoff

**What the LLM generates:**

```apex
public void retryWithBackoff() {
    Integer delayMs = Math.pow(2, attempt) * 1000;
    Thread.sleep(delayMs);   // <— Thread does not exist in Apex
    // or
    Long start = System.currentTimeMillis();
    while (System.currentTimeMillis() - start < delayMs) { }   // <— burns CPU governor
    retry();
}
```

**Why it happens:** Java / Python / Node training data is full of `Thread.sleep(2000)` retry loops. Apex has no thread API and "sleep" patterns from other languages either fail to compile (`Thread`) or silently burn the 10-second CPU governor (`while`-spin).

**Correct pattern:**

```apex
// Re-enqueue a fresh Queueable (immediate) — platform schedules it shortly after.
System.enqueueJob(new ErpInvoicePullQueueable(..., retryCount + 1));

// Or, for delayed retry (>1 minute), use System.scheduleBatch:
System.scheduleBatch(
    new ErpRetryScheduler(...),
    'ERP_Retry_' + cycleId + '_' + attempt,
    delayMin    // minutes from now
);
```

**Detection hint:** Search for `Thread.sleep`, `Thread.currentThread`, or any while-loop that conditions on `System.currentTimeMillis` / `Limits.getCpuTime` in retry contexts.

---

## Anti-Pattern 4: Storing ERP access token in a Custom Setting / Custom Object

**What the LLM generates:**

```apex
public class ErpAuthService {
    public static String getToken() {
        ERP_Auth__c cfg = ERP_Auth__c.getOrgDefaults();
        if (cfg.Expires_At__c < Datetime.now()) {
            cfg.Token__c = refreshToken();   // <— DIY refresh in Apex
            cfg.Expires_At__c = Datetime.now().addHours(1);
            update cfg;
        }
        return cfg.Token__c;
    }
}
```

**Why it happens:** LLMs replicate generic OAuth client patterns from non-Salesforce contexts (Node, Python). Salesforce has a built-in mechanism (Named Credentials + External Credentials with Auth Provider) that handles this entirely — but recognizing it requires Salesforce-specific knowledge of the External Credential model that became the canonical answer in Winter '23.

**Correct pattern:**

- Configure External Credential with OAuth 2.0 Auth Provider for the ERP.
- Configure Named Credential pointing at the External Credential.
- In Apex, simply: `req.setEndpoint('callout:ERP_NetSuite/invoices')`.
- The platform handles token storage and refresh transparently. Never store tokens in Custom Settings or Custom Objects.

**Detection hint:** Any custom object or custom setting field named `Token`, `Access_Token`, `Bearer_Token`, `Expires_At` is almost always wrong in a Salesforce integration. The token is not your data.

---

## Anti-Pattern 5: Watermark advanced to `Datetime.now()` after cycle completes

**What the LLM generates:**

```apex
public void execute(QueueableContext qc) {
    Datetime priorWatermark = readWatermark();
    List<Record> records = pullFromErp(priorWatermark);
    upsert records;
    advanceWatermark(Datetime.now());   // <— wrong: skips records modified during cycle
}
```

**Why it happens:** LLMs produce code linearly: do the work, then update the cursor. The race condition where ERP records are modified *during* the pull window is subtle and rarely surfaces in non-Salesforce examples — most non-SF schedulers don't have transactional contexts that wrap multi-second callout windows the same way.

**Correct pattern:**

```apex
public void execute(QueueableContext qc) {
    Datetime cycleStart = this.cycleStart;   // captured by Schedulable, passed in
    Datetime priorWatermark = this.priorWatermark;
    List<Record> records = pullFromErp(priorWatermark);
    upsert records;
    // Advance only on end-to-end success of the entire chain — and to cycleStart, not now()
    if (isLastInChain) advanceWatermark(cycleStart);
}
```

**Detection hint:** Search for `advanceWatermark(Datetime.now())` or `lastSync = Datetime.now()` in any post-cycle code. The argument should be a `cycleStart` captured before the work began, not the current time after.

---

## Anti-Pattern 6: No DLQ — failures logged to `System.debug` and forgotten

**What the LLM generates:**

```apex
try {
    HttpResponse res = http.send(req);
    if (res.getStatusCode() != 200) {
        System.debug(LoggingLevel.ERROR, 'ERP failed: ' + res.getBody());
        return;
    }
} catch (Exception e) {
    System.debug(LoggingLevel.ERROR, 'ERP exception: ' + e);
}
```

**Why it happens:** LLMs treat logging as the canonical error response — true in many non-SF contexts. In Salesforce, debug logs are not queryable, not retained beyond 24 hours, and not visible to ops without enabling user-level trace flags. They are not a substitute for an audit-trail object.

**Correct pattern:**

```apex
try {
    HttpResponse res = http.send(req);
    if (res.getStatusCode() != 200) {
        ErpDlqWriter.writePermanent(res, 'invoices', cycleStart);
        return;
    }
} catch (CalloutException e) {
    ErpDlqWriter.writeRetryExhausted(null, e.getMessage(), 'invoices', cycleStart);
}
```

**Detection hint:** Any `catch` block whose body is solely `System.debug(...)` in integration code is wrong. Failures should land in `Integration_DLQ__c` (or equivalent) for replay tooling.

---

## Anti-Pattern 7: Recommending the polling pattern when CDC / Platform Events would be correct

**What the LLM generates:** "Set up a 15-minute scheduled Apex job that calls the ERP, parses the response, and upserts records." — without checking the ERP's event-publication capabilities or the volume profile.

**Why it happens:** Polling is the most common integration shape in training data and the easiest to demonstrate. Streaming patterns (Pub/Sub API, Platform Events, CDC consumed via Pub/Sub) require more nuanced architectural reasoning and are often skipped.

**Correct pattern:** Before recommending polling, walk through Concept 4's volume / cadence table. If volume routinely exceeds 10K per cycle, sub-minute latency is required, or the ERP supports event publication, the right answer is *not* this pattern. Route to:
- `integration/platform-events-publish-subscribe` — if ERP can publish events
- `integration/change-data-capture-consumer-pattern` — if change is sourced from another Salesforce instance or ERP-side CDC
- `data/data-loader-bulk-api` — if volume is the dominant constraint

**Detection hint:** A recommendation for "scheduled poll" without explicitly addressing volume, cadence, and the ERP's event-publication capability is incomplete. The skill activation should always include the Concept 4 check.
