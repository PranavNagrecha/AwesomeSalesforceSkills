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
