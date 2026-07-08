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

## Example 3: Same Test Written With The `System.Assert` Class

**Context:** A new test verifies that `AccountService.markCustomersActive` sets the status and never nulls the name.

**Problem:** The team's older tests use `System.assertEquals`, but new tests should default to the `Assert` class for clearer failure output.

**Solution:**

```apex
@isTest
static void marksActiveWithAssertClass() {
    Account seed = TestDataFactory.createAccount('Test Corp');
    insert seed;

    Test.startTest();
    AccountService.markCustomersActive(new List<Account>{ seed });
    Test.stopTest();

    Account refreshed = [SELECT Name, Customer_Status__c FROM Account WHERE Id = :seed.Id];
    Assert.areEqual('Active', refreshed.Customer_Status__c, 'Status should be Active after processing');
    Assert.isNotNull(refreshed.Name, 'Name must not be cleared by the service');
}
```

**Why it works:** `Assert.areEqual` and `Assert.isNotNull` read as intent and emit clearer messages on failure. The message argument is a `String`, which the `Assert` methods require. The legacy `System.assertEquals` call in older tests still works and does not need rewriting.

---

## Example 4: Isolating A Service From Its Selector With The Stub API

**Context:** `OpportunityService.closeStale()` asks `OpportunitySelector.selectStale()` for records, then flips their stage. You want to test the service's decision logic without seeding matching data or exercising the selector's SOQL.

**Problem:** A callout mock does not apply — the collaborator is a plain Apex class, not an HTTP endpoint.

**Solution:**

```apex
@isTest
private class OpportunityServiceTest {

    private class SelectorStub implements StubProvider {
        private List<Opportunity> canned;
        SelectorStub(List<Opportunity> canned) { this.canned = canned; }

        public Object handleMethodCall(
            Object stubbed, String methodName, Type returnType,
            List<Type> paramTypes, List<String> paramNames, List<Object> args
        ) {
            if (methodName == 'selectStale') {
                return canned;
            }
            return null;
        }
    }

    @isTest
    static void closesStaleFromStubbedSelector() {
        List<Opportunity> stale = new List<Opportunity>{
            new Opportunity(Id = TestDataFactory.fakeId(Opportunity.SObjectType), StageName = 'Prospecting')
        };
        OpportunitySelector mockSelector = (OpportunitySelector) Test.createStub(
            OpportunitySelector.class, new SelectorStub(stale)
        );

        Test.startTest();
        List<Opportunity> result = new OpportunityService(mockSelector).closeStale();
        Test.stopTest();

        Assert.areEqual('Closed Lost', result[0].StageName, 'Stale opportunities should be closed');
    }
}
```

**Why it works:** `Test.createStub()` returns a runtime double for `OpportunitySelector`, so the test drives the service's logic against a controlled response with no database dependency. The stub only works because `selectStale` is a non-static, non-private instance method — the Stub API cannot intercept static, `@future`, private, or property members.

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
