# Examples — Apex Test Setup Patterns

Two worked scenarios and one anti-pattern showing how to use `@TestSetup`
correctly for shared data, deep hierarchies, and bulk fixtures. The
examples emphasize the runtime behavior that breaks practitioners most
often: SObject Ids persist across test methods, but every field/state
change inside a test method rolls back to the post-setup snapshot before
the next method runs.

---

## Example 1: Three test methods sharing an Account/Opportunity baseline — Id persistence + per-method state rollback

**Context:** `OpportunityRollupServiceTest` has three test methods that
each need the same 5 Accounts and 25 Opportunities to exercise different
branches of the rollup logic (won, lost, in-progress). Creating the
data inside each method runs ~30 DML statements per test (5 accounts +
25 opps, with intermediate parent-lookup queries), and the test class
runs in 18s instead of 4s.

**Problem:** Practitioners often "fix" this by promoting the data
creation into `@TestSetup` but then assume each test method gets a
*literally fresh* copy of the records — including new Ids. They write
asserts that hard-code the index (`accs[0].Id`), and the asserts fail
in the *second* test method because the records exist with the *same*
Ids but the field state from the first test's DML has been rolled back.

**Solution:** Use `@TestSetup` once. Re-query inside each test method
to pick up the post-rollback state. Never cache Ids in static variables
across methods.

```apex
@IsTest
private class OpportunityRollupServiceTest {

    @TestSetup
    static void seedAccountsAndOpps() {
        List<Account> accs = new List<Account>();
        for (Integer i = 0; i < 5; i++) {
            accs.add(new Account(Name = 'Rollup Test ' + i));
        }
        insert accs;

        List<Opportunity> opps = new List<Opportunity>();
        for (Account a : accs) {
            for (Integer j = 0; j < 5; j++) {
                opps.add(new Opportunity(
                    Name       = a.Name + ' Opp ' + j,
                    AccountId  = a.Id,
                    StageName  = 'Prospecting',
                    CloseDate  = Date.today().addDays(30),
                    Amount     = 1000 * (j + 1)
                ));
            }
        }
        insert opps;
    }

    @IsTest
    static void rollupSumsClosedWonOnly() {
        // Re-query — the post-setup snapshot is what we see here.
        List<Opportunity> opps = [SELECT Id FROM Opportunity LIMIT 10];
        for (Opportunity o : opps) {
            o.StageName = 'Closed Won';
        }
        update opps;

        Test.startTest();
        OpportunityRollupService.recalculateAll();
        Test.stopTest();

        Account a = [SELECT Total_Won__c FROM Account
                     WHERE Id IN (SELECT AccountId FROM Opportunity)
                     LIMIT 1];
        System.assertNotEquals(null, a.Total_Won__c);
    }

    @IsTest
    static void rollupIgnoresClosedLost() {
        // The 10 opps that method 1 set to Closed Won are back to
        // Prospecting here — DML from rollupSumsClosedWonOnly rolled
        // back. But the Ids are identical to what method 1 saw.
        List<Opportunity> opps = [SELECT Id, StageName FROM Opportunity];
        System.assertEquals(25, opps.size());
        for (Opportunity o : opps) {
            System.assertEquals('Prospecting', o.StageName);
        }
        // ...exercise the closed-lost branch.
    }

    @IsTest
    static void rollupHandlesEmptyAmount() {
        // Same starting snapshot, different mutation path.
        List<Opportunity> opps = [SELECT Id FROM Opportunity LIMIT 5];
        for (Opportunity o : opps) o.Amount = null;
        update opps;
        // ...assert rollup tolerates nulls.
    }
}
```

**Why it works:** Salesforce wraps each `@IsTest` method in a savepoint
established immediately after `@TestSetup` completes. The savepoint is
released and the database rewound to the post-setup snapshot before
the next test method runs. Record Ids stay stable across that rewind
because the underlying rows are not physically deleted — only the
in-flight changes since the savepoint are reversed. The test class
above runs in roughly 4s instead of 18s because the 30 baseline DML
statements happen once, not three times. Each test re-queries to see
the rewound state instead of trusting cached references.

---

## Example 2: Account with 200 Contacts and a multi-junction hierarchy in @TestSetup

**Context:** `CampaignMembershipBulkTest` needs a realistic bulk
scenario: one Account, 200 Contacts on that Account, one Campaign, and
a CampaignMember junction row for every Contact. The trigger under test
fires on CampaignMember insert and back-stamps a count on the parent
Campaign. Three test methods need this hierarchy: insert-path, update-
path, and delete-path.

**Problem:** Creating 200 Contacts inline in each test consumes 200/200
of the DML row budget shared with the trigger code (Salesforce allows
10,000 DML rows per transaction, but practitioners often hit the 150
DML *statements* limit instead by looping inserts). The class flakes
intermittently when CI runs it on a busy sandbox because the trigger
code itself uses an extra 5–10 DML statements and the per-test setup
leaves no margin.

**Solution:** Push the hierarchy into `@TestSetup` and bulk-insert each
level in a single DML statement. Wrap the code-under-test in
`Test.startTest()` / `Test.stopTest()` so it gets a fresh 100-SOQL /
150-DML budget independent of the setup work.

```apex
@IsTest
private class CampaignMembershipBulkTest {

    @TestSetup
    static void seedHierarchy() {
        Account a = new Account(Name = 'Bulk Test Account');
        insert a;

        List<Contact> contacts = new List<Contact>();
        for (Integer i = 0; i < 200; i++) {
            contacts.add(new Contact(
                FirstName = 'Test',
                LastName  = 'Contact ' + i,
                AccountId = a.Id,
                Email     = 'bulk' + i + '@example.invalid'
            ));
        }
        insert contacts;  // 1 DML statement, 200 rows

        Campaign c = new Campaign(
            Name     = 'Bulk Test Campaign',
            IsActive = true,
            Type     = 'Email'
        );
        insert c;

        List<CampaignMember> members = new List<CampaignMember>();
        for (Contact ct : contacts) {
            members.add(new CampaignMember(
                CampaignId = c.Id,
                ContactId  = ct.Id,
                Status     = 'Sent'
            ));
        }
        insert members;  // 1 DML statement, 200 rows
    }

    @IsTest
    static void insertedMembersUpdateCampaignCount() {
        Campaign c = [SELECT Id FROM Campaign LIMIT 1];

        Test.startTest();  // fresh 150-DML / 100-SOQL budget
        Contact extra = new Contact(LastName = 'Extra', AccountId =
            [SELECT Id FROM Account LIMIT 1].Id);
        insert extra;
        insert new CampaignMember(CampaignId = c.Id, ContactId = extra.Id);
        Test.stopTest();

        Campaign reloaded = [SELECT Member_Count__c FROM Campaign
                             WHERE Id = :c.Id];
        System.assertEquals(201, reloaded.Member_Count__c);
    }

    @IsTest
    static void deletedMembersDecrementCampaignCount() {
        List<CampaignMember> toRemove = [SELECT Id FROM CampaignMember
                                         LIMIT 50];
        Test.startTest();
        delete toRemove;
        Test.stopTest();

        Campaign reloaded = [SELECT Member_Count__c FROM Campaign LIMIT 1];
        System.assertEquals(150, reloaded.Member_Count__c);
    }
}
```

**Why it works:** Each hierarchy level inserts as a single bulk DML
statement, so `@TestSetup` consumes 4 of the 150 DML statements
available to the class — not 401. The `Test.startTest()` boundary
gives the code-under-test a clean budget: even if the trigger does
additional queries and updates, it starts at 0/100 SOQL and 0/150
DML rather than inheriting a partially-consumed budget. The 200-record
fixture matches the Apex trigger batch size, so the bulk-path branches
of the trigger get exercised the same way Data Loader will exercise
them in production.

---

## Anti-Pattern: Recreating the same data inside every test method

**What practitioners do:**

```apex
@IsTest
private class AccountServiceTest {

    @IsTest
    static void testCreateOpportunity() {
        Account a = new Account(Name = 'Acme');
        insert a;
        for (Integer i = 0; i < 10; i++) {
            insert new Contact(LastName = 'C' + i, AccountId = a.Id);
        }
        // ... actual assertion code, 3 lines
    }

    @IsTest
    static void testCloseOpportunity() {
        Account a = new Account(Name = 'Acme');
        insert a;
        for (Integer i = 0; i < 10; i++) {
            insert new Contact(LastName = 'C' + i, AccountId = a.Id);
        }
        // ... actual assertion code, 5 lines
    }

    @IsTest
    static void testDeleteOpportunity() {
        Account a = new Account(Name = 'Acme');
        insert a;
        for (Integer i = 0; i < 10; i++) {
            insert new Contact(LastName = 'C' + i, AccountId = a.Id);
        }
        // ... actual assertion code, 4 lines
    }
}
```

**What goes wrong:** Three failure modes compound.

*First*, each method consumes 11 of the 150 DML statements before the
code-under-test runs (1 Account insert + 10 looped Contact inserts).
With 10 test methods, the class spends 110 DML budget on duplicated
setup. The looped inserts also burn 10 of the 150 DML *statement*
budget per method, which is the limit that bites first on real test
classes — the 10,000-row DML limit is rarely the bottleneck.

*Second*, the test class wall-clock time scales linearly with method
count. A class with one method takes ~1.5s; ten methods take ~15s.
A `@TestSetup` version of the same class runs the data creation
once and finishes in ~3s — a 5x test-suite speedup that compounds
across 200+ test classes in a mature org.

*Third*, when a validation rule or required field is added to Account
or Contact, every duplicated `new Account(Name = 'Acme')` / `new
Contact(LastName = 'C0', ...)` line breaks individually. A centralized
`@TestSetup` (or a `TestDataFactory` invoked from `@TestSetup`) has
exactly one place to update.

**Correct approach:** Move the shared data into `@TestSetup` and have
each test method re-query for what it needs. Use a bulk-insert pattern
(build a `List<Contact>`, then a single `insert contacts;`) so the
setup costs 2 DML statements regardless of record count. If only one
test method needs unusual data, keep the bulk hierarchy in
`@TestSetup` and add the one-off record inside that method — don't
duplicate the entire baseline. See Example 1 for the canonical shape.
