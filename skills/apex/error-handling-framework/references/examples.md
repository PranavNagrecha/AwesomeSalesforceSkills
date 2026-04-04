# Examples — Error Handling Framework

## Example 1: Rollback-Safe Logging in a Batch Apex Execute Method

**Context:** A nightly batch job processes 50,000 Account records and syncs them to an external ERP. Some records fail ERP validation. The org previously logged failures by inserting `Error_Log__c` records inside the `execute` method's catch block. Records were occasionally missing from the log because the batch chunk rolled back on an unrelated `LimitException` mid-chunk, taking the log insert with it.

**Problem:** DML inside a failing transaction rolls back with the transaction. `Error_Log__c` inserts in a catch block are not exempt from this behavior. When the batch chunk fails due to a CPU time limit or an uncaught exception, any log records inserted during that chunk are discarded.

**Solution:**

```apex
public class AccountERPSyncBatch implements Database.Batchable<SObject>, Database.AllowsCallouts {

    private final String correlationId;

    public AccountERPSyncBatch(String correlationId) {
        this.correlationId = correlationId;
    }

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([SELECT Id, Name, BillingCity FROM Account WHERE Sync_Status__c = 'Pending']);
    }

    public void execute(Database.BatchableContext bc, List<SObject> scope) {
        List<Account> accounts = (List<Account>) scope;
        for (Account acct : accounts) {
            try {
                ERPService.syncAccount(acct);
            } catch (IntegrationException ie) {
                // Publish Platform Event — survives rollback of this chunk's DML
                ErrorLogger.logException(
                    'ERROR',
                    'AccountERPSyncBatch.execute',
                    ie,
                    correlationId,
                    JSON.serialize(new Map<String, Object>{
                        'accountId'   => acct.Id,
                        'accountName' => acct.Name
                    })
                );
            }
        }
    }

    public void finish(Database.BatchableContext bc) { }
}
```

The `ErrorLogger.logException` method calls `EventBus.publish()` — not `insert`. The subscriber trigger on `ErrorLog__e` inserts the `Error_Log__c` record in a completely separate transaction that is unaffected by any rollback in the batch chunk.

**Why it works:** Platform Event delivery is decoupled from the publishing transaction's DML commit status. The event is enqueued at publish time and delivered to the subscriber regardless of whether the publisher's transaction succeeds or fails.

---

## Example 2: Typed Exception Hierarchy with AuraHandledException at the Controller Boundary

**Context:** An LWC component lets users submit an insurance claim. The controller calls a service class that validates the claim, calls an external insurance API, and updates records. Several different failure modes can occur: missing required field, duplicate claim, API timeout. Previously, all of these surfaced as generic "An internal server error has occurred" messages in the UI because the service layer threw raw `Exception` or `AuraHandledException` deep in the call stack.

**Problem:** When `AuraHandledException` is thrown in a service class, the full Apex stack trace is suppressed in the Lightning response. All failures look identical from the UI. The LWC has no way to distinguish a user-fixable validation error from a retryable timeout.

**Solution:**

Define the exception hierarchy (deployed once, used everywhere):

```apex
// AppException.cls
public class AppException extends Exception {
    public enum ErrorCode {
        REQUIRED_FIELD_MISSING,
        DUPLICATE_CLAIM,
        CALLOUT_TIMEOUT,
        INTEGRATION_AUTH_FAILURE,
        CONFIGURATION_MISSING,
        UNEXPECTED
    }
    public ErrorCode code { get; private set; }

    public AppException(ErrorCode code, String message) {
        this(message);
        this.code = code;
    }
}

public class ValidationException extends AppException { }
public class IntegrationException extends AppException { }
```

Service class throws typed exceptions:

```apex
// ClaimService.cls
public class ClaimService {
    public void submitClaim(Claim__c claim) {
        if (String.isBlank(claim.Policy_Number__c)) {
            throw new ValidationException(
                AppException.ErrorCode.REQUIRED_FIELD_MISSING,
                'Policy number is required to submit a claim.'
            );
        }
        // ... callout logic ...
        HttpResponse resp = callInsuranceAPI(claim);
        if (resp.getStatusCode() == 408) {
            throw new IntegrationException(
                AppException.ErrorCode.CALLOUT_TIMEOUT,
                'Insurance API timed out. Please retry in a few minutes.'
            );
        }
    }
}
```

Controller wraps at the boundary:

```apex
// ClaimController.cls
@AuraEnabled
public static void submitClaim(Id claimId) {
    String correlationId = UserInfo.getUserId() + ':' + Datetime.now().getTime();
    try {
        Claim__c claim = [SELECT Id, Policy_Number__c FROM Claim__c WHERE Id = :claimId];
        ClaimService.submitClaim(claim);
    } catch (ValidationException ve) {
        // User-fixable: surface the message directly, no log needed (expected path)
        throw new AuraHandledException(ve.getMessage());
    } catch (IntegrationException ie) {
        if (ie.code == AppException.ErrorCode.CALLOUT_TIMEOUT) {
            ErrorLogger.logException('WARN', 'ClaimController.submitClaim', ie, correlationId,
                JSON.serialize(new Map<String, String>{ 'claimId' => claimId }));
            throw new AuraHandledException('The insurance service is temporarily unavailable. Please retry in a few minutes. Reference: ' + correlationId);
        }
        ErrorLogger.logException('ERROR', 'ClaimController.submitClaim', ie, correlationId, null);
        throw new AuraHandledException('An error occurred submitting your claim. Reference: ' + correlationId);
    } catch (Exception e) {
        ErrorLogger.logException('FATAL', 'ClaimController.submitClaim', e, correlationId, null);
        throw new AuraHandledException('An unexpected error occurred. Reference: ' + correlationId);
    }
}
```

**Why it works:** `AuraHandledException` is only constructed at the controller layer. Service classes remain unaware of UI transport. The LWC receives a meaningful, user-safe message. The stack trace is preserved in logs because `ErrorLogger` captures it before the `AuraHandledException` replaces it. The correlation ID in the user-facing message lets support engineers find the log entry.

---

## Example 3: BatchApexErrorEvent Subscriber for Automatic Batch Failure Capture

**Context:** The org runs dozens of batch jobs. Previously, unhandled exceptions in batch classes surfaced only in the Apex Jobs setup page and were quickly overwritten. No permanent record existed, and on-call engineers had to correlate job IDs manually with debug logs. The team wanted automatic, durable capture of all batch failures without adding try/catch to every batch class.

**Problem:** Without a `BatchApexErrorEvent` subscriber, unhandled batch exceptions are visible only in the Apex Jobs UI (transient) and in debug logs (which require active logging and expire). There is no queryable record of batch failures across job history.

**Solution:**

```apex
// BatchApexErrorEventTrigger.trigger
trigger BatchApexErrorEventTrigger on BatchApexErrorEvent (after insert) {
    List<ErrorLog__e> logsToPublish = new List<ErrorLog__e>();

    for (BatchApexErrorEvent evt : Trigger.new) {
        String payloadJson = JSON.serialize(new Map<String, Object>{
            'AsyncApexJobId'              => evt.AsyncApexJobId,
            'ExceptionType'               => evt.ExceptionType,
            'Phase'                       => evt.Phase,
            'DoesExceedJobScopeMaxLength' => evt.DoesExceedJobScopeMaxLength,
            'JobScope'                    => evt.DoesExceedJobScopeMaxLength
                                            ? '[truncated — query AsyncApexJob by AsyncApexJobId]'
                                            : evt.JobScope
        });

        logsToPublish.add(new ErrorLog__e(
            Level__c          = 'ERROR',
            Context__c        = 'BatchApexErrorEvent:' + evt.Phase,
            Message__c        = evt.Message,
            Stack_Trace__c    = evt.StackTrace,
            Payload__c        = payloadJson,
            Correlation_Id__c = evt.AsyncApexJobId
        ));
    }

    List<Database.SaveResult> results = EventBus.publish(logsToPublish);
    for (Integer i = 0; i < results.size(); i++) {
        if (!results[i].isSuccess()) {
            System.debug(LoggingLevel.ERROR,
                'BatchApexErrorEventTrigger: failed to publish ErrorLog__e for job '
                + Trigger.new[i].AsyncApexJobId + ' — ' + results[i].getErrors());
        }
    }
}
```

**Why it works:** Salesforce automatically publishes `BatchApexErrorEvent` for every unhandled batch exception from API v44+ — no per-class try/catch required. The subscriber re-publishes to `ErrorLog__e`, routing the failure through the same log infrastructure used by all other Apex contexts. `Correlation_Id__c` is set to `AsyncApexJobId` so engineers can query `Error_Log__c WHERE Correlation_Id__c = :jobId` to retrieve all failures for a specific batch run.

---

## Anti-Pattern: Inserting Error_Log__c Directly in a Catch Block Inside a Transaction

**What practitioners do:** To keep code simple, developers insert an `Error_Log__c` record directly inside a catch block:

```apex
// WRONG — log is lost if transaction rolls back
try {
    update accountsToSync;
} catch (DmlException e) {
    insert new Error_Log__c(Message__c = e.getMessage(), Stack_Trace__c = e.getStackTraceString());
    // This insert rolls back with the failed update
}
```

**What goes wrong:** If the enclosing transaction fails (which it often does at the point of exception), the `insert Error_Log__c` DML is part of that same transaction's savepoint and rolls back with it. The log record is never committed. This is especially common in Batch `execute` methods where the entire chunk rolls back on an uncaught exception.

**Correct approach:** Replace the direct DML with `EventBus.publish()` to the `ErrorLog__e` Platform Event. The PE publish is not part of the transaction's DML state and survives rollback. The subscriber trigger inserts `Error_Log__c` in an independent transaction.
