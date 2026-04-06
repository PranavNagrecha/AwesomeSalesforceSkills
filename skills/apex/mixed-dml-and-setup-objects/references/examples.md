# Examples — Mixed DML and Setup Objects

## Example 1: Test Class Creating User and Account

**Context:** A test class needs to verify that a custom trigger on Account creates a Task, and the test must run as a specific User with a specific Profile.

**Problem:** Inserting the User and Account in the same test method without isolation throws `MIXED_DML_OPERATION`.

**Solution:**

```apex
@IsTest
static void testAccountTriggerCreatesTask() {
    // Step 1: Create non-setup records (no restriction yet)
    Account acc = new Account(Name = 'Acme Corp');
    insert acc;

    // Step 2: Create setup records inside System.runAs()
    User salesUser;
    System.runAs(new User(Id = UserInfo.getUserId())) {
        Profile p = [SELECT Id FROM Profile WHERE Name = 'Standard User' LIMIT 1];
        salesUser = new User(
            FirstName = 'Sales', LastName = 'Rep',
            Email = 'salesrep@example.com',
            Username = 'salesrep' + DateTime.now().getTime() + '@example.com',
            Alias = 'srep', ProfileId = p.Id,
            TimeZoneSidKey = 'America/New_York',
            LocaleSidKey = 'en_US',
            EmailEncodingKey = 'UTF-8',
            LanguageLocaleKey = 'en_US'
        );
        insert salesUser;
    }

    // Step 3: Run business logic as the new user
    System.runAs(salesUser) {
        Account updateAcc = [SELECT Id FROM Account WHERE Id = :acc.Id];
        updateAcc.Description = 'Updated by sales rep';
        update updateAcc;

        List<Task> tasks = [SELECT Id FROM Task WHERE WhatId = :acc.Id];
        System.assertEquals(1, tasks.size(), 'Trigger should create a Task on Account update');
    }
}
```

**Why it works:** `System.runAs()` creates a new DML context in test execution. The User insert happens in a separate transaction context from the Account insert, satisfying the platform restriction.

---

## Example 2: Production Auto-Provisioning with @future

**Context:** When a partner Account is created, the system must automatically create a portal User linked to the Account's primary Contact.

**Problem:** The trigger fires on Account insert (non-setup DML), and creating the User (setup DML) in the same transaction context violates the mixed DML restriction.

**Solution:**

```apex
// Trigger
trigger AccountTrigger on Account (after insert) {
    List<Id> partnerAccountIds = new List<Id>();
    for (Account a : Trigger.new) {
        if (a.Type == 'Partner') {
            partnerAccountIds.add(a.Id);
        }
    }
    if (!partnerAccountIds.isEmpty()) {
        PortalUserService.provisionPortalUsersAsync(partnerAccountIds);
    }
}

// Service class
public class PortalUserService {

    @future
    public static void provisionPortalUsersAsync(List<Id> accountIds) {
        List<Contact> contacts = [
            SELECT Id, FirstName, LastName, Email, AccountId
            FROM Contact
            WHERE AccountId IN :accountIds AND Email != null
            ORDER BY CreatedDate ASC
        ];

        Profile communityProfile = [
            SELECT Id FROM Profile
            WHERE Name = 'Customer Community User' LIMIT 1
        ];

        List<User> usersToInsert = new List<User>();
        for (Contact c : contacts) {
            usersToInsert.add(new User(
                ContactId = c.Id,
                FirstName = c.FirstName,
                LastName = c.LastName,
                Email = c.Email,
                Username = c.Email + '.' + c.AccountId,
                Alias = c.LastName.left(8),
                ProfileId = communityProfile.Id,
                TimeZoneSidKey = 'America/New_York',
                LocaleSidKey = 'en_US',
                EmailEncodingKey = 'UTF-8',
                LanguageLocaleKey = 'en_US'
            ));
        }
        if (!usersToInsert.isEmpty()) {
            insert usersToInsert;
        }
    }
}
```

**Why it works:** The `@future` method runs in a completely separate transaction. The Account insert completes first, then the User insert runs asynchronously without sharing a transaction boundary.

---

## Example 3: Assigning Permission Sets in Test Setup

**Context:** A test class needs records owned by a user who has a specific permission set, and the test must verify permission-gated behavior.

**Problem:** Creating the User and inserting the PermissionSetAssignment alongside business records causes a mixed DML error.

**Solution:**

```apex
@testSetup
static void setup() {
    // Non-setup records first
    Account acc = new Account(Name = 'PermTest Corp');
    insert acc;
    Contact con = new Contact(AccountId = acc.Id, LastName = 'Tester');
    insert con;

    // Setup records inside System.runAs()
    System.runAs(new User(Id = UserInfo.getUserId())) {
        Profile p = [SELECT Id FROM Profile WHERE Name = 'Standard User' LIMIT 1];
        User u = new User(
            FirstName = 'Perm', LastName = 'Tester',
            Email = 'permtest@example.com',
            Username = 'permtest' + DateTime.now().getTime() + '@example.com',
            Alias = 'ptst', ProfileId = p.Id,
            TimeZoneSidKey = 'America/New_York',
            LocaleSidKey = 'en_US',
            EmailEncodingKey = 'UTF-8',
            LanguageLocaleKey = 'en_US'
        );
        insert u;

        PermissionSet ps = [SELECT Id FROM PermissionSet WHERE Name = 'Custom_Access' LIMIT 1];
        insert new PermissionSetAssignment(AssigneeId = u.Id, PermissionSetId = ps.Id);
    }
}

@IsTest
static void testPermissionGatedLogic() {
    User u = [SELECT Id FROM User WHERE Email = 'permtest@example.com' LIMIT 1];
    Account acc = [SELECT Id FROM Account WHERE Name = 'PermTest Corp' LIMIT 1];

    System.runAs(u) {
        acc.Description = 'Should succeed with custom permission';
        update acc;
        System.assertNotEquals(null, acc.Id);
    }
}
```

**Why it works:** Both the User insert and the PermissionSetAssignment insert are setup DML. They can coexist in the same `System.runAs()` block. The key is keeping them separated from the non-setup Account and Contact inserts.

---

## Anti-Pattern: Inserting User and Account in the Same Scope

**What practitioners do:** Insert a User and an Account in sequential lines without any transaction isolation.

```apex
@IsTest
static void testBadPattern() {
    Account acc = new Account(Name = 'Test');
    insert acc;

    User u = new User(/* fields */);
    insert u; // MIXED_DML_OPERATION thrown here
}
```

**What goes wrong:** The test fails at runtime with `System.DmlException: MIXED_DML_OPERATION`. The User insert occurs in the same transaction context as the Account insert.

**Correct approach:** Wrap the User insert in `System.runAs(new User(Id = UserInfo.getUserId()))` to create a separate DML context.
