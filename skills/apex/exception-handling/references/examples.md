# Examples — Exception Handling

## Example 1: Bulk Update With Partial Success and Structured Error Capture

**Context:** A service updates many `Case` records after an external scoring run. Some records can fail validation, but the whole batch must not abort.

**Problem:** A single `update casesToUpdate;` throws one `DmlException`, loses per-record visibility, and rolls back every valid record in the list.

**Solution:**

```apex
public with sharing class CaseScoringService {

    public class CaseScoringException extends Exception {}

    public static void applyScores(List<Case> casesToUpdate) {
        List<Case_Error__c> errorLogs = new List<Case_Error__c>();
        Database.SaveResult[] results = Database.update(casesToUpdate, false);

        for (Integer i = 0; i < results.size(); i++) {
            if (results[i].isSuccess()) {
                continue;
            }

            for (Database.Error err : results[i].getErrors()) {
                errorLogs.add(new Case_Error__c(
                    Source__c = 'CaseScoringService.applyScores',
                    Record_Id__c = casesToUpdate[i].Id,
                    Status_Code__c = String.valueOf(err.getStatusCode()),
                    Message__c = err.getMessage()
                ));
            }
        }

        if (!errorLogs.isEmpty()) {
            insert errorLogs;
        }
    }
}
```

**Why it works:** `Database.update(..., false)` preserves successful rows and exposes failures per record through `SaveResult[]`, which is the right pattern when the business process accepts partial success.

---

## Example 2: Service Exception Mapped to `AuraHandledException`

**Context:** An LWC calls Apex to submit an `Opportunity`. The user needs a clean message when a known business precondition is missing.

**Problem:** The controller surfaces raw platform messages or catches `Exception` and returns `null`, so the UI gets inconsistent behavior.

**Solution:**

```apex
public with sharing class OpportunitySubmissionController {

    @AuraEnabled
    public static void submitOpportunity(Id opportunityId) {
        try {
            OpportunitySubmissionService.submit(opportunityId);
        } catch (OpportunitySubmissionService.SubmissionException e) {
            throw new AuraHandledException(e.getMessage());
        }
    }
}

public with sharing class OpportunitySubmissionService {

    public class SubmissionException extends Exception {}

    public static void submit(Id opportunityId) {
        Opportunity opp = [
            SELECT Id, StageName, Contract_Signed__c
            FROM Opportunity
            WHERE Id = :opportunityId
            WITH USER_MODE
        ];

        if (!opp.Contract_Signed__c) {
            throw new SubmissionException('Contract must be signed before submission.');
        }

        opp.StageName = 'Submitted';
        update opp;
    }
}
```

**Why it works:** The service throws a business-specific exception. The controller converts it once at the UI boundary into a user-safe error type instead of leaking internal details.

---

## Example 3: Rollback Then Notify — The Savepoint / Callout Order

**Context:** A nightly reconciliation writes `Adjustment__c` rows. If any row is rejected the whole
adjustment must be discarded and the operations team notified over HTTP.

**Problem:** Rolling back to the savepoint feels like it cleans the transaction, so the callout goes in
the catch block straight after `Database.rollback(sp)`. It fails with `System.CalloutException`, the
notification is never sent, and the caller receives a callout error instead of the DML error.

**Solution:** roll back, *release*, then call out.

```apex
public with sharing class AdjustmentReconciler {

    public class ReconcileException extends Exception {}

    public void run(List<Adjustment__c> adjustments, String runId) {
        Savepoint sp = Database.setSavepoint();   // costs one DML STATEMENT, not a row
        try {
            insert adjustments;
            Database.releaseSavepoint(sp);        // success path: release before returning
        } catch (DmlException e) {
            Database.rollback(sp);
            Database.releaseSavepoint(sp);        // WITHOUT this line the next line throws

            HttpRequest req = new HttpRequest();
            req.setEndpoint('callout:Reconcile_Ops/v1/alerts');
            req.setMethod('POST');
            req.setBody(JSON.serialize(new Map<String, Object>{
                'runId'        => runId,
                'failedRows'   => e.getNumDml(),
                'firstBadRow'  => e.getDmlIndex(0),
                'statusCode'   => String.valueOf(e.getDmlType(0))
            }));
            new Http().send(req);

            ApplicationLogger.error('AdjustmentReconciler.run', e);
            ApplicationLogger.flush();
            throw new ReconcileException('Adjustment run ' + runId + ' was rolled back.', e);
        }
    }
}
```

**Why it works:** the guide's own worked example puts `Database.rollback(sp)` and
`Database.releaseSavepoint(sp)` before `makeACallout()` and notes that the callout then succeeds
(Apex Developer Guide, `apexdev` L8730–8741). The payload carries `getDmlIndex(0)` rather than `0`,
because the loop counter and the original row position are different numbers
(`apexrefguide` L215140).

**Verify it after a real run:** the two facts worth checking in the org are that nothing committed and
that exactly one log row exists per failed run — not one per failed row.

```sql
-- Nothing from the failed run survived the rollback.
SELECT COUNT(Id) FROM Adjustment__c WHERE Run_Id__c = 'RUN-2026-09-05'

-- Exactly one ERROR row per failed run, with the DmlException type preserved.
SELECT Source__c, Exception_Type__c, Request_Id__c, Message__c, CreatedDate
FROM Application_Log__c
WHERE Source__c = 'AdjustmentReconciler.run' AND CreatedDate = TODAY
ORDER BY CreatedDate DESC
```

---

## Anti-Pattern: Catch Everything, Log Nothing Useful, Return Null

**What practitioners do:** They wrap the whole method in `try/catch (Exception e)`, call `System.debug(e)`, and return `null`.

```apex
public static Account loadAccount(Id accountId) {
    try {
        return [SELECT Id, Name FROM Account WHERE Id = :accountId];
    } catch (Exception e) {
        System.debug(e);
        return null;
    }
}
```

**What goes wrong:** The caller cannot distinguish "not found" from "query failed" from "sharing denied." Production monitoring gets nothing actionable, and defects stay hidden.

**Correct approach:** Catch only expected exception types when you can add value. Otherwise let the exception bubble, or translate it at the boundary with structured logging.
