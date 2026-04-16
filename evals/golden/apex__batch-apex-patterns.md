# Eval: apex/batch-apex-patterns

- **Skill under test:** `skills/apex/batch-apex-patterns/SKILL.md`
- **Priority:** P0
- **Cases:** 3
- **Last verified:** 2026-04-16
- **Related templates:** `templates/apex/tests/BulkTestPattern.cls`, `templates/apex/ApplicationLogger.cls`
- **Related decision trees:** `standards/decision-trees/async-selection.md`

## Pass criteria

The AI must produce a Batchable implementation with an explicit `scope`,
a selective `start()` query, state management only where needed, idempotent
`finish()`, and a test that actually exercises `finish()` by inserting at
least the `scope` size inside `Test.startTest()/stopTest()`.

## Case 1 — "Make this Batch faster"

**Priority:** P0

**User prompt:**

> "Our nightly `LeadDedupeBatch` takes 6 hours and sometimes fails with
> `TOTAL_ROWS_EXCEEDED`. What should I change?"

**Context provided:**

- Start query: `SELECT Id, Email FROM Lead`.
- Scope = 2000 (hard-coded).
- `execute()` loops each Lead, does `[SELECT Id FROM Lead WHERE Email = :lead.Email]`, merges matches.

**Expected output MUST include:**

- Root cause identification: non-selective `start()` query AND SOQL-in-loop
  in `execute()` — both are fatal.
- Fix 1: selective start query — filter by `IsConverted = false AND Email != null`
  and put an index on `Email` (if not already).
- Fix 2: one SOQL in `execute()` collecting all emails, then a `Map<String, List<Lead>>`
  for in-memory dedupe.
- Fix 3: reduce scope to 200 — the in-memory map plus potential merge DML
  makes 2000 dangerous.
- Fix 4: `Database.Stateful` to accumulate a per-run metrics record.
- Fix 5: add bulk tests that insert 200 Leads with duplicate emails.

**Expected output MUST NOT include:**

- "Increase the scope to 5000" (max is 2000 for Batch Apex).
- "Run it twice a night" (doesn't address root cause).
- Using `Database.merge` inside a loop without bulk guard.

**Rubric (0–5):**

- **Correctness:** Both non-selective query AND SOQL-in-loop identified.
- **Completeness:** 5 fixes listed with reasons.
- **Bulk safety:** Replacement pattern is strictly one SOQL per `execute()`.
- **Security:** `WITH USER_MODE` applied; notes merge permissions.
- **Citation of official docs:** Links to selective query filters + governor limits.

**Reference answer (gold):**

"Two root causes:

1. `SELECT Id, Email FROM Lead` is non-selective and will eventually exceed
   `TOTAL_ROWS_EXCEEDED` as the Lead table grows. Add `WHERE IsConverted = false AND Email != null`
   and confirm `Email` is indexed (Salesforce indexes it by default; confirm in your org's custom index list).
2. `execute()` does one SOQL per Lead — 2000 queries per batch, 101-query
   wall hit quickly.

Refactor:

```apex
public with sharing class LeadDedupeBatch implements Database.Batchable<SObject>, Database.Stateful {
    private Integer totalMerged = 0;

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(
            'SELECT Id, Email FROM Lead WHERE IsConverted = false AND Email != null WITH USER_MODE'
        );
    }

    public void execute(Database.BatchableContext bc, List<Lead> scope) {
        Set<String> emails = new Set<String>();
        for (Lead l : scope) { emails.add(l.Email.toLowerCase()); }

        Map<String, List<Lead>> byEmail = new Map<String, List<Lead>>();
        for (Lead existing : [
            SELECT Id, Email, IsConverted
            FROM Lead
            WHERE Email IN :emails AND IsConverted = false
            WITH USER_MODE
        ]) {
            String key = existing.Email.toLowerCase();
            if (!byEmail.containsKey(key)) { byEmail.put(key, new List<Lead>()); }
            byEmail.get(key).add(existing);
        }

        List<Database.MergeResult> results = new List<Database.MergeResult>();
        for (List<Lead> duplicates : byEmail.values()) {
            if (duplicates.size() < 2) { continue; }
            Lead master = duplicates[0];
            List<Lead> rest = new List<Lead>();
            for (Integer i = 1; i < duplicates.size(); i++) { rest.add(duplicates[i]); }
            results.add(Database.merge(master, rest, false));
        }
        for (Database.MergeResult r : results) {
            if (r.isSuccess()) { totalMerged += r.getMergedRecordIds().size(); }
            else { ApplicationLogger.error('LeadDedupeBatch.execute', r.getErrors()[0].getMessage()); }
        }
    }

    public void finish(Database.BatchableContext bc) {
        ApplicationLogger.info('LeadDedupeBatch.finish', 'Merged ' + totalMerged + ' duplicates');
    }
}
```

Scope: drop to 200 — merges compound DML and you want headroom. Test: 200 Leads with 100 dup pairs inside `Test.startTest()/stopTest()`, assert `totalMerged = 100`."

## Case 2 — Callouts from Batch without hitting the per-batch callout cap

**Priority:** P0

**User prompt:**

> "My Batch syncs Orders to an external system via REST. It works for 50
> orders then throws `System.CalloutException: You have uncommitted work pending`."

**Expected output MUST include:**

- Add `implements Database.AllowsCallouts`.
- Only 1 callout per `execute()` scope — aggregate the scope into a single
  POST to the external API's batch endpoint.
- Small scope (e.g. 10–50) so the aggregate payload stays under size limits.
- Explicit mention that **no DML can occur before the callout** in the same
  `execute()` — the "uncommitted work" error comes from this.
- Use `HttpClient` template with Named Credential + retry.
- `MockHttpResponseGenerator` in tests — never hit a real endpoint.

**Expected output MUST NOT include:**

- A loop of single-record callouts in `execute()`.
- Suggesting `@future(callout=true)` inside `execute()` (valid but obscure;
  prefer Queueable chained FROM `finish()` if truly one-per-record needed).
- Catching + swallowing the exception.

**Rubric (0–5):**

- **Correctness:** Identifies Database.AllowsCallouts + DML ordering cause.
- **Completeness:** Payload batching, scope sizing, Named Credential, mock.
- **Bulk safety:** Single callout per batch scope.
- **Security:** Named Credential + External Credential.
- **Citation of official docs:** Links to `Database.AllowsCallouts` + callout limits.

**Reference answer (gold):**

"Three changes:

```apex
public with sharing class OrderSyncBatch implements Database.Batchable<SObject>, Database.AllowsCallouts {
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(
            'SELECT Id, Name, TotalAmount__c FROM Order WHERE Needs_Sync__c = true WITH USER_MODE'
        );
    }

    public void execute(Database.BatchableContext bc, List<Order> scope) {
        // NO DML before callout in this method.
        HttpClient.Response res = new HttpClient()
            .namedCredential('Order_Sync_API')
            .path('/v2/orders/batch')
            .method('POST')
            .header('Content-Type', 'application/json')
            .body(JSON.serialize(scope))
            .timeoutMs(60000)
            .retryOnTransient(true)
            .send();

        if (!res.isSuccess()) {
            ApplicationLogger.error('OrderSyncBatch.execute',
                'Upstream ' + res.statusCode + ' body=' + res.body.left(1000));
            return; // let Batch retry on next run
        }

        // DML is safe AFTER the callout.
        List<Order> toMark = new List<Order>();
        for (Order o : scope) { toMark.add(new Order(Id = o.Id, Needs_Sync__c = false)); }
        update toMark;
    }

    public void finish(Database.BatchableContext bc) {}
}
```

Scope size: start at 25, tune toward 100 based on payload size. Test using `MockHttpResponseGenerator.withResponse(200, '{}')` in `@TestSetup` and assert no records remain with `Needs_Sync__c = true` after stop."

## Case 3 — Idempotent `finish()` after partial batch failure

**Priority:** P0

**User prompt:**

> "One of our 12 batches failed last night with a lock exception. How do I
> make `finish()` restart-safe so we don't end up double-emailing the
> customer the 'processing complete' notification?"

**Expected output MUST include:**

- `finish()` MUST check an idempotency marker (custom object or
  `AsyncApexJob` status) before sending any notification.
- Example: check `Apex_Job_Status__c` record with the Batch's `AsyncApexJob.Id`
  — if marked `Completed`, no-op.
- Record the marker transactionally in `finish()` after the notification succeeds.
- Lock-exception fix: reduce scope, shorten transaction time in `execute()`,
  don't update the same parent twice per run.
- Retry semantics: Batch retries the FAILED scope only — not the whole job.

**Expected output MUST NOT include:**

- "Just rerun the whole batch" (might resend notifications).
- Storing idempotency state in a static variable (doesn't survive the
  transaction boundary).

**Rubric (0–5):**

- **Correctness:** Idempotency via persisted marker.
- **Completeness:** Both notification idempotency AND lock root cause covered.
- **Bulk safety:** Marker write is a single DML.
- **Security:** Marker object has Private OWD; creator-only write.
- **Citation of official docs:** Links to AsyncApexJob + batch retry semantics.

**Reference answer (gold):**

"Two things to fix.

**Idempotent `finish()`** — always persist a marker before side effects like emails:

```apex
public void finish(Database.BatchableContext bc) {
    AsyncApexJob job = [
        SELECT Id, Status, NumberOfErrors
        FROM AsyncApexJob
        WHERE Id = :bc.getJobId()
        WITH SYSTEM_MODE
    ];
    Apex_Job_Status__c marker = [
        SELECT Id, Notification_Sent__c
        FROM Apex_Job_Status__c
        WHERE Job_Id__c = :bc.getJobId()
        LIMIT 1
    ];
    if (marker != null && marker.Notification_Sent__c) { return; }

    Messaging.SingleEmailMessage msg = buildMessage(job);
    Messaging.sendEmail(new List<Messaging.Email>{msg});

    upsert new Apex_Job_Status__c(
        Job_Id__c = bc.getJobId(),
        Notification_Sent__c = true
    ) Job_Id__c;
}
```

**Lock root cause** — 12 concurrent batches almost always means you are
updating the same parent Account rows from multiple scopes. Three fixes in order of cheapest:

1. Reduce scope from 200 to 50–100 so transactions are shorter.
2. Order `start()` by parent Id so scopes never contend (`ORDER BY AccountId`).
3. Split into two batches: one that writes to the parent, one that writes to children. Run sequentially in `finish()` if you need.

Batch retry semantics: only the FAILED scope is retried — the rest of the
run is not rerun. Your notification guard above means even if `finish()` is
re-entered on retry, you won't double-send."
