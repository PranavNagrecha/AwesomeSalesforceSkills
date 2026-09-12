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

## Example 5: User-Mode Code — The Whole Class Runs As A Permissioned User

**Context:** `Tier2EscalationService` queries `WITH USER_MODE` and writes with `Database.update(..., AccessLevel.USER_MODE)`. `Case.Tier2_Notified_At__c` and the `Tier2_Webhook_Admin` permission set that grants it are in the same deployment as the class.

**Problem:** The obvious test — `@TestSetup` seeds Cases, each method queries and calls the service — compiles, and then fails every method at `sf project deploy start --dry-run --test-level RunSpecifiedTests` with `No such column 'Tier2_Notified_At__c' on entity 'Case'`. The tests are running as the deploying admin, whose profile was not in the deployment and therefore has no FLS on a field this deployment just created. See `references/gotchas.md` Gotcha 13.

**Solution:** Mint the running user in `@TestSetup`, assign the shipped permission set, and put every body inside `System.runAs(testUser)`. Note the three distinct `runAs` jobs in this class — they are easy to conflate and only the last one is about permissions.

```apex
@IsTest
private class Tier2EscalationServiceTest {

    private static final String PERM_SET  = 'Tier2_Webhook_Admin';  // ships in this deployment
    private static final String PROFILE   = 'Standard User';

    @TestSetup
    static void seed() {
        // (1) User is a setup object. Inserting it alongside Case DML in one
        //     transaction is a mixed-DML error, so the setup-object work is
        //     fenced inside runAs of the *current* user. This grants nothing.
        User agent;
        System.runAs(new User(Id = UserInfo.getUserId())) {
            agent = TestUserFactory.createUser(PROFILE, new List<String>{ PERM_SET });
            // TestUserFactory.createUser inserts the User and the matching
            // PermissionSetAssignment rows; see templates/apex/tests/TestUserFactory.cls.
            Assert.isNotNull(agent.Id, 'the runAs user must exist before any Case is seeded');
        }

        // (2) Business data is seeded as the permissioned user, so a create-FLS
        //     gap in the permission set fails here — loudly, in setup — rather
        //     than surfacing later as an unexplained empty query result.
        System.runAs(agent) {
            insert TestDataFactory.createCases(200, null, null);
        }
    }

    /** Re-queried per method: @TestSetup state reaches a test method only through the database. */
    private static User agent() {
        return [SELECT Id FROM User WHERE Alias LIKE 'tu%' ORDER BY CreatedDate DESC LIMIT 1];
    }

    @IsTest
    static void escalationStampsTheCase() {
        User testUser = agent();

        // (3) The real one. Inside this block the user's object- and field-level
        //     permissions are enforced regardless of the test class's sharing
        //     mode (apexdev L41331-L41333) — which is the only reason the
        //     WITH USER_MODE query below can see Tier2_Notified_At__c at all.
        System.runAs(testUser) {
            List<Case> due = [SELECT Id, Tier2_Notified_At__c FROM Case WITH USER_MODE LIMIT 2];
            Set<Id> dueIds = new Map<Id, Case>(due).keySet();

            Test.startTest();
            Tier2EscalationService.escalate(due);
            Test.stopTest();

            List<Case> stamped = [
                SELECT Id FROM Case
                WHERE Id IN :dueIds AND Tier2_Notified_At__c != NULL
                WITH USER_MODE
            ];
            Assert.areEqual(2, stamped.size(), 'escalation must stamp Tier2_Notified_At__c for the permissioned user');
        }
    }

    @IsTest
    static void anAgentWithoutThePermissionSetCannotStamp() {
        User unpermissioned = TestUserFactory.createUser(PROFILE, new List<String>());

        System.runAs(unpermissioned) {
            Test.startTest();
            try {
                Tier2EscalationService.escalate([SELECT Id FROM Case LIMIT 1]);
                Assert.fail('a user without ' + PERM_SET + ' must not be able to stamp the Case');
            } catch (Exception e) {
                // Apex has no multi-catch. The two shapes this can take are a
                // QueryException from the WITH USER_MODE read and a DmlException
                // ('fields being inaccessible') from the user-mode write, so assert
                // on the message rather than narrowing the catch to one of them.
                Assert.isTrue(
                    e.getMessage().contains('Tier2_Notified_At__c') || e.getMessage().contains('inaccessible'),
                    'the failure must name the field the permission set grants, got: ' + e.getMessage()
                );
            }
            Test.stopTest();
        }
    }
}
```

**Why this matters beyond style:** the second method is what turns the permission set from an untested deployment artefact into a tested one. Without it the suite proves the happy path works for *someone*, but not that the permission set is the thing granting it — so silently dropping a `fieldPermissions` entry from the permission set stays green until production.

**Budget note:** every `runAs` call spends a DML statement (Gotcha 11). Four blocks is fine; a `runAs` per record is how a sharing test hits the 150-statement limit and then gets blamed on the trigger.

**Checker:** `python3 skills/apex/test-class-standards/scripts/check_test_class_standards.py --manifest-dir <classes dir>` fires `user-mode-test-without-runas` (ERROR) on the "obvious test" above and is silent on this one. It deliberately does not count `System.runAs(new User(Id = UserInfo.getUserId()))` — block (1) — as a permissioned `runAs`.

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
