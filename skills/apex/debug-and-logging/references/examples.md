# Examples — Debug And Logging

## Example 1: Structured Log Record For A Failed Integration

**Context:** A Queueable integration occasionally fails after a remote API returns 500.

**Problem:** `System.debug` shows the error locally, but support has no durable trail in production.

**Solution:**

```apex
public class IntegrationLogger {
    public static void logError(String operationName, Id recordId, String jobId, String message) {
        insert new Integration_Log__c(
            Operation__c = operationName,
            Related_Record_Id__c = recordId,
            Async_Job_Id__c = jobId,
            Severity__c = 'ERROR',
            Message__c = message
        );
    }
}

public class InvoiceSyncQueueable implements Queueable, Database.AllowsCallouts {
    public void execute(QueueableContext context) {
        try {
            // callout work
        } catch (Exception e) {
            IntegrationLogger.logError('InvoiceSync', null, context.getJobId(), e.getMessage());
            throw e;
        }
    }
}
```

**Why it works:** The job can still fail loudly while support gets a durable correlation record tied to the async job.

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
