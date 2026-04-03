# Examples — Test Class Standards

## Example 1: Factory + `@testSetup` + Bulk And Negative Assertions

**Context:** An `AccountService` updates a custom status field and creates related records when input passes validation.

**Problem:** Existing tests create one record per method, assert only on coverage, and miss bulk or failure behavior.

**Solution:**

```apex
@isTest
private class AccountServiceTest {

    @testSetup
    static void setupData() {
        insert TestDataFactory.accounts(5);
    }

    @isTest
    static void updatesAccountsInBulk() {
        List<Account> accounts = [SELECT Id, Name, Customer_Status__c FROM Account LIMIT 5];

        Test.startTest();
        AccountService.markCustomersActive(accounts);
        Test.stopTest();

        List<Account> refreshed = [
            SELECT Customer_Status__c
            FROM Account
            WHERE Id IN :accounts
        ];
        for (Account accountRecord : refreshed) {
            System.assertEquals('Active', accountRecord.Customer_Status__c);
        }
    }

    @isTest
    static void throwsForMissingRequiredInput() {
        try {
            Test.startTest();
            AccountService.markCustomersActive(new List<Account>());
            Test.stopTest();
            System.assert(false, 'Expected AccountServiceException');
        } catch (AccountService.AccountServiceException e) {
            System.assert(e.getMessage().contains('at least one Account'));
        }
    }
}
```

**Why it works:** The setup is reusable, the test covers bulk behavior, and the negative path proves the exception contract instead of merely executing lines.

---

## Example 2: Callout Test With `HttpCalloutMock`

**Context:** A Queueable sends `Case` updates to an external system.

**Problem:** The team wants to test success and failure behavior, but making a real HTTP request inside a test is prohibited.

**Solution:**

```apex
@isTest
private class CaseSyncQueueableTest {

    private class SuccessMock implements HttpCalloutMock {
        public HTTPResponse respond(HTTPRequest request) {
            HttpResponse response = new HttpResponse();
            response.setStatusCode(200);
            response.setBody('{"status":"ok"}');
            return response;
        }
    }

    @isTest
    static void syncsCaseSuccessfully() {
        Case caseRecord = new Case(Subject = 'Sync me', Status = 'New', Origin = 'Phone');
        insert caseRecord;

        Test.setMock(HttpCalloutMock.class, new SuccessMock());

        Test.startTest();
        System.enqueueJob(new CaseSyncQueueable(new Set<Id>{caseRecord.Id}));
        Test.stopTest();

        Case refreshed = [SELECT Sync_Status__c FROM Case WHERE Id = :caseRecord.Id];
        System.assertEquals('Sent', refreshed.Sync_Status__c);
    }
}
```

**Why it works:** The mock controls the remote response and keeps the test deterministic. `stopTest()` ensures the Queueable actually runs before assertions.

---

## Anti-Pattern: Coverage Test With No Useful Assertion

**What practitioners do:** They call the method, catch any exception, and assert only that execution reached the end.

```apex
@isTest
static void coverageOnly() {
    Test.startTest();
    AccountService.markCustomersActive(new List<Account>());
    Test.stopTest();
    System.assert(true);
}
```

**What goes wrong:** This proves nothing about the service contract, negative behavior, or actual data changes. Coverage rises while regression risk stays high.

**Correct approach:** Assert the expected record state, expected exception, or expected side effect with enough specificity that a real regression would fail the test.
