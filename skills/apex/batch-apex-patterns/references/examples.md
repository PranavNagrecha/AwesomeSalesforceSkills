# Examples — Batch Apex Patterns

## Example 1: QueryLocator Batch With Summary In `finish()`

**Context:** A nightly process must close stale Leads at scale and notify operations about the job outcome.

**Problem:** Running the cleanup in one transaction cannot scale or report meaningfully.

**Solution:**

```apex
global class StaleLeadBatch implements Database.Batchable<SObject>, Database.Stateful {
    global Integer closedCount = 0;

    global Database.QueryLocator start(Database.BatchableContext context) {
        return Database.getQueryLocator([
            SELECT Id, Status
            FROM Lead
            WHERE Status = 'Open'
            AND LastActivityDate < :Date.today().addDays(-90)
        ]);
    }

    global void execute(Database.BatchableContext context, List<Lead> scope) {
        for (Lead leadRecord : scope) {
            leadRecord.Status = 'Closed - Inactive';
        }
        Database.SaveResult[] results = Database.update(scope, false);
        for (Database.SaveResult result : results) {
            if (result.isSuccess()) {
                closedCount++;
            }
        }
    }

    global void finish(Database.BatchableContext context) {
        AsyncApexJob job = [
            SELECT Status, JobItemsProcessed, NumberOfErrors
            FROM AsyncApexJob
            WHERE Id = :context.getJobId()
        ];
        System.debug('Closed ' + closedCount + ' leads. Status=' + job.Status);
    }
}
```

**Why it works:** The batch handles large volume in scopes and uses `finish()` plus `AsyncApexJob` for summary visibility.

---

## Example 2: Callout Batch With Smaller Scope

**Context:** A batch must send records to an external API, which cannot tolerate large payloads.

**Problem:** Default scope assumptions create timeouts and oversized requests.

**Solution:**

```apex
global class ContactSyncBatch implements Database.Batchable<SObject>, Database.AllowsCallouts {
    global Database.QueryLocator start(Database.BatchableContext context) {
        return Database.getQueryLocator([
            SELECT Id, Email
            FROM Contact
            WHERE Sync_Pending__c = true
        ]);
    }

    global void execute(Database.BatchableContext context, List<Contact> scope) {
        HttpRequest request = new HttpRequest();
        request.setEndpoint('callout:Marketing_API/contacts');
        request.setMethod('POST');
        request.setTimeout(15000);
        request.setBody(JSON.serialize(scope));
        new Http().send(request);
    }

    global void finish(Database.BatchableContext context) { }
}

Id jobId = Database.executeBatch(new ContactSyncBatch(), 20);
```

**Why it works:** The batch is explicitly callout-enabled and uses a smaller scope size that matches the remote system’s tolerance.

---

## Anti-Pattern: Batch For Small Transactional Work

**What practitioners do:** They reach for Batch Apex for a few dozen records simply because the work is asynchronous.

**What goes wrong:** The solution gains framework overhead, more moving parts, and more monitoring burden than a Queueable would need.

**Correct approach:** Use Batch only when chunked large-volume processing or Batch lifecycle semantics are genuinely required.
