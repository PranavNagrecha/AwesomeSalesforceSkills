# Examples — Debug And Logging

## Example 1: Structured Log Record For A Failed Integration

**Context:** A Queueable integration occasionally fails after a remote API returns 500.

**Problem:** `System.debug` shows the error locally, but support has no durable trail in production.

**Solution:** attach a finalizer. It runs whether the Queueable succeeds or dies, so the log survives
the rollback that discards everything `execute()` did. Do not write a second logger — `LogService`
(references/code-examples.md) already wraps `templates/apex/ApplicationLogger.cls`.

```apex
public class InvoiceSyncQueueable implements Queueable, Database.AllowsCallouts {

    private final List<Id> invoiceIds;

    public InvoiceSyncQueueable(List<Id> invoiceIds) {
        this.invoiceIds = invoiceIds;
    }

    public void execute(QueueableContext context) {
        System.attachFinalizer(new InvoiceSyncFinalizer(invoiceIds.size()));
        LogService.info('InvoiceSync.execute', 'Syncing ' + invoiceIds.size() + ' invoices');
        // callout work; an unhandled exception here still reaches the finalizer
    }
}

public class InvoiceSyncFinalizer implements Finalizer {

    private final Integer requested;

    public InvoiceSyncFinalizer(Integer requested) {
        this.requested = requested;
    }

    public void execute(FinalizerContext ctx) {
        String source = 'InvoiceSync.finalizer job=' + ctx.getAsyncApexJobId();
        if (ctx.getResult() == ParentJobResult.UNHANDLED_EXCEPTION) {
            LogService.error(source, ctx.getException());
        } else {
            LogService.info(source, 'Completed ' + requested + ' invoices; req=' + ctx.getRequestId());
        }
        LogService.flush();
    }
}
```

**Why it works:** The job still fails loudly, but the finalizer commits the record after the rollback. `getResult()` returns `SUCCESS` or `UNHANDLED_EXCEPTION` and `getException()` returns the failure (Apex Developer Guide L16337–16344); `getAsyncApexJobId()` is what joins the row to `AsyncApexJob`, while `getRequestId()` joins it to Event Monitoring (L16327–16329).

---

## Example 2: Targeted Sandbox Debugging

**Context:** A developer needs to inspect a specific branch in a trigger handler during a sandbox defect investigation.

**Problem:** Broad debug statements already produce noisy logs that are hard to read.

**Solution:**

```apex
System.debug(LoggingLevel.INFO, 'OpportunityQualification: entered beforeUpdate branch');
System.debug(LoggingLevel.DEBUG, 'OpportunityQualification changed stages for Id=' + opp.Id);
```

**Why it works:** The debug lines are labeled and scoped to one investigation rather than serving as a permanent logging strategy.

---

## Anti-Pattern: Permanent `System.debug` As Production Observability

**What practitioners do:** They leave many debug lines in service code and assume those logs will be enough during incidents.

**What goes wrong:** Logs are transient, noisy, and not queryable in the way support needs. Sensitive payload data can also leak.

**Correct approach:** Keep debug lines temporary and use a structured logging sink for production-critical operations.

---

## Example 3: Triaging From `ApexLog` When The Debug Log Is Already Gone

**Context:** A user reports an error from 09:40. It is now 15:00 and the Developer Console log for that
session has expired.

**Problem:** The transient log is unavailable, but `ApexLog` rows and durable log rows both survive
long enough to reconstruct the request — if you know which fields to join on.

**Solution:**

```sql
-- Step 1: find the durable rows for the window and pull their correlation ids.
SELECT Request_Id__c, Severity__c, Source__c, Exception_Type__c, Limits_Snapshot__c, CreatedDate
FROM Application_Log__c
WHERE CreatedDate >= 2026-09-05T09:30:00Z AND CreatedDate <= 2026-09-05T09:50:00Z
  AND Severity__c IN ('ERROR','FATAL')
ORDER BY CreatedDate

-- Step 2: was a debug log captured for that same request? Monitoring logs live seven days,
--         Developer Console (SystemLog) logs only 24 hours.
SELECT Id, Operation, Status, Request, Location, LogLength, DurationMilliseconds, StartTime
FROM ApexLog
WHERE RequestIdentifier = '<Request_Id__c from step 1>'

-- Step 3: if the ceiling is the problem, this is what is eating it.
SELECT LogUserId, Location, COUNT(Id) logs, SUM(LogLength) bytes
FROM ApexLog
WHERE StartTime = LAST_N_DAYS:1
GROUP BY LogUserId, Location
ORDER BY SUM(LogLength) DESC
```

To capture the *next* occurrence, set a scoped trace flag. `TraceFlag` and `DebugLevel` are **Tooling
API** objects, not Metadata API types — they are set "in the Developer Console or in Setup or by using
the `TraceFlag` and `DebugLevel` Tooling API objects" (Apex Developer Guide L39543–39546) — so they
cannot go in `package.xml`. The Tooling API request bodies:

```json
{
  "DebugLevel": {
    "DeveloperName": "Apex_Only_Fine",
    "MasterLabel": "Apex Only Fine",
    "ApexCode": "FINE",
    "ApexProfiling": "NONE",
    "Callout": "NONE",
    "Database": "NONE",
    "System": "NONE",
    "Validation": "NONE",
    "Visualforce": "NONE",
    "Workflow": "NONE"
  },
  "TraceFlag": {
    "TracedEntityId": "<ApexClass Id, ApexTrigger Id, or User Id>",
    "DebugLevelId": "<Id returned by the DebugLevel insert>",
    "LogType": "CLASS_TRACING",
    "StartDate": "2026-09-05T09:00:00.000+0000",
    "ExpirationDate": "2026-09-05T10:00:00.000+0000"
  }
}
```

**Why it works:** A class-scoped trace flag has "the debug log type `CLASS_TRACING`" and overrides
"the debug log levels of the `USER_DEBUG` and `DEVELOPER_LOG` trace flags" (Apex Developer Guide
L38297–38299), so you raise verbosity for one class without generating org-wide volume. Setting every
other category to `NONE` keeps the log under the 20 MB truncation point. And a class trace flag alone
generates nothing — "Setting class and trigger trace flags doesn't cause logs to be generated or
saved … If logging is enabled when classes or triggers execute, logs are generated at the time of
execution" (L38105–38108), so a user-level flag must also be active.

UNVERIFIED (2026-09-05): the exact Tooling API field names and the enumerated `LogType` values beyond
`CLASS_TRACING`, `USER_DEBUG` and `DEVELOPER_LOG` come from the Tooling API Developer Guide, which is
not in the grounding corpus. The three log-type names and the category list above are grounded in the
Apex Developer Guide; treat the JSON shape as a starting point and confirm against `/services/data/
vXX.0/tooling/sobjects/TraceFlag/describe` before scripting it.
