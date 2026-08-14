# Examples — Apex System Runas

## Example 1: Prove a permission gap instead of assuming one

**Context:** `AccountService` creates Accounts on behalf of a self-service persona. Security review asks for a test that
demonstrates the restricted profile genuinely cannot create Accounts, and that the Permission Set is what unlocks it.

**Problem:** The usual attempt wraps a bare `insert` in `runAs` and asserts a row count. On a class saved at API 66.0 or
earlier that assertion is meaningless — the DML runs in system mode and succeeds regardless of the impersonated user's
object permissions. The test goes green and the permission model is never actually exercised.

**Solution:** State the access mode explicitly on the DML instead of inheriting it. `AccessLevel.USER_MODE` enforces the
running user's object and field permissions at every API version, so the assertion holds whether the class is pinned to
58.0 or 67.0.

```apex
@IsTest
private with sharing class AccountCreationPermissionTest {

    @IsTest
    static void restrictedUserCannotCreateAccountsWithoutPermSet() {
        // templates/apex/tests/TestUserFactory.cls
        User restricted = TestUserFactory.createUser('Minimum Access - Salesforce', new List<String>());

        System.runAs(restricted) {
            try {
                Database.insert(new Account(Name = 'Blocked'), AccessLevel.USER_MODE);
                Assert.fail('Expected a SecurityException — the profile has no Create on Account.');
            } catch (SecurityException ex) {
                Assert.isTrue(ex.getMessage().contains('Account'), 'Exception should name the blocked object.');
            }
        }
    }

    @IsTest
    static void permissionSetGrantsAccountCreate() {
        User granted = TestUserFactory.createUser(
            'Minimum Access - Salesforce',
            new List<String>{ 'Account_Create_Access' }
        );

        System.runAs(granted) {
            Database.SaveResult sr = Database.insert(new Account(Name = 'Allowed'), AccessLevel.USER_MODE);
            Assert.isTrue(sr.isSuccess(), 'Permission Set should grant Create on Account.');
        }
    }
}
```

**Why it works:** The pair of tests brackets the permission. One proves the deny, one proves the grant, and the delta
between them is exactly the Permission Set under review — so revoking that Permission Set in a later release fails the
suite instead of silently widening access. `SecurityException` is the documented failure mode for a user-mode DML the
running user is not entitled to perform.

---

## Example 2: Confine setup-object DML to a mixed-DML boundary in `@TestSetup`

**Context:** A test class needs a Queue, a Permission Set Assignment, and 200 Cases. All three in one `@TestSetup`
raises `MIXED_DML_OPERATION`.

**Problem:** Teams usually discover this after the fact and scatter `runAs(new User(Id = UserInfo.getUserId()))` around
whichever line happened to throw. That works until somebody adds a helper that inserts a `QueueSObject` or a
`PermissionSetAssignment` a few frames down, and the error moves.

**Solution:** Make the boundary structural. One `runAs` block owns every setup object; record data is created strictly
after it, outside the block.

```apex
@IsTest
private with sharing class CaseRoutingTest {

    @TestSetup
    static void makeData() {
        // Everything the platform classifies as a setup object goes inside this block.
        // The impersonation is a no-op — the block exists only to partition the DML.
        System.runAs(new User(Id = UserInfo.getUserId())) {
            User agent = TestUserFactory.createUser(
                'Standard User',
                new List<String>{ 'Case_Agent_Access' }
            );

            Group q = new Group(Name = 'Tier 1 Support', Type = 'Queue');
            insert q;
            insert new QueueSObject(QueueId = q.Id, SObjectType = 'Case');
            insert new GroupMember(GroupId = q.Id, UserOrGroupId = agent.Id);
        }

        // Non-setup DML — legal only because it is outside the block above.
        List<Case> cases = new List<Case>();
        for (Integer i = 0; i < 200; i++) {
            cases.add(new Case(Subject = 'Bulk ' + i, Status = 'New', Origin = 'Web'));
        }
        insert cases;
    }

    @IsTest
    static void agentCannotSeeCasesOwnedByTheSetupUser() {
        // TestUserFactory usernames carry a known domain — query on that, not on
        // Profile.Name, which will also match users other tests happened to create.
        User agent = [
            SELECT Id FROM User
            WHERE Username LIKE 'test.user.%@skills.repo.test' AND IsActive = true
            LIMIT 1
        ];

        System.runAs(agent) {
            // Assert with a query issued HERE, not through a service class — a called class
            // contributes its own sharing mode, not the test class's.
            // The 200 Cases are owned by the @TestSetup (admin) user and are not routed to
            // the queue, so with Case OWD = Private the agent sees none of them. If your org
            // runs Case at Public Read, this expectation is 200 instead — the number is a
            // statement about the OWD, not about runAs.
            Assert.areEqual(0, [SELECT COUNT() FROM Case]);
        }
    }
}
```

**Why it works:** `Group`, `GroupMember`, `QueueSObject`, `User`, and `PermissionSetAssignment` are all on the
documented setup-object list, and that list is explicitly "not an exhaustive list" — so grouping them by *category*
rather than by *the line that threw* survives a future object being reclassified. Note the `Group` sub-rule: insert and
update are allowed alongside other sObjects, other DML operations are not.

---

## Anti-Pattern: Treating a `runAs` block as an FLS test

**What practitioners do:** Wrap a query in `runAs(lowPrivUser)`, read a restricted field, and conclude from the absence
of an exception that field-level security is behaving.

```apex
System.runAs(lowPrivUser) {
    Account a = [SELECT Id, Hidden__c FROM Account LIMIT 1];
    Assert.isNotNull(a.Hidden__c);   // proves nothing on a class saved at API 66.0 or earlier
}
```

**What goes wrong:** The result is version-dependent and therefore not an assertion at all. At API 66.0 and earlier the
query runs in system mode and never consults FLS; at 67.0 and later it throws. Same source, opposite outcome, decided by
a number in a `.cls-meta.xml` file that no reviewer looked at.

**Correct approach:** Name the access mode in the query so the test asserts the same thing at every API version, and use
`Security.stripInaccessible` when the requirement is "drop the fields the user cannot see" rather than "fail the whole
operation".

```apex
System.runAs(lowPrivUser) {
    try {
        Account a = [SELECT Id, Hidden__c FROM Account WITH USER_MODE LIMIT 1];
        Assert.fail('Hidden__c should not be readable by this profile.');
    } catch (QueryException ex) {
        Assert.isTrue(ex.getMessage().contains('Hidden__c'));
    }

    // Where partial success is the requirement, strip rather than throw:
    SObjectAccessDecision decision = Security.stripInaccessible(
        AccessType.READABLE,
        [SELECT Id, Hidden__c FROM Account WITH SYSTEM_MODE LIMIT 1]
    );
    Assert.isFalse(decision.getRemovedFields().get('Account').isEmpty());
}
```
