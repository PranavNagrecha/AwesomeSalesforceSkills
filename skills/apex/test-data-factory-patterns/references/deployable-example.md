# Deployable Example: Bulk Factory With a Mixed-DML-Safe User Builder

A complete `@IsTest` factory, a test class that uses it, and the manifest. Every behavior the tests assert is stated in the Apex Developer Guide, Version 67.0: list-based inserts (Common Test Utility Classes for Test Data Creation), setup records that reset between methods (Using Test Setup Methods), and setup-object DML inside `System.runAs` (Mixed DML Operations in Test Methods).

## File: `force-app/main/default/classes/TestDataFactory.cls`

```apex
@IsTest
public class TestDataFactory {
    private static Integer uniqueCounter = 0;

    public static String uniqueSuffix() {
        uniqueCounter++;
        return String.valueOf(DateTime.now().getTime()) + '-' + uniqueCounter;
    }

    public static List<Account> createAccounts(Integer count, Boolean doInsert) {
        List<Account> rows = new List<Account>();
        for (Integer i = 0; i < count; i++) {
            rows.add(new Account(Name = 'Factory Account ' + i, BillingCountry = 'US'));
        }
        if (doInsert) {
            insert rows;
        }
        return rows;
    }

    public static List<Contact> createContacts(List<Account> parents, Integer perAccount, Boolean doInsert) {
        List<Contact> rows = new List<Contact>();
        for (Account parent : parents) {
            for (Integer i = 0; i < perAccount; i++) {
                rows.add(new Contact(AccountId = parent.Id, LastName = 'Factory ' + i));
            }
        }
        if (doInsert) {
            insert rows;
        }
        return rows;
    }

    public static User newUser(String profileName) {
        Profile p = [SELECT Id FROM Profile WHERE Name = :profileName LIMIT 1];
        String suffix = uniqueSuffix();
        return new User(
            Alias = 'fact' + String.valueOf(Math.mod(uniqueCounter, 10000)).leftPad(4, '0'),
            Email = 'factory.' + suffix + '@example.com',
            EmailEncodingKey = 'UTF-8',
            LastName = 'Factory',
            LanguageLocaleKey = 'en_US',
            LocaleSidKey = 'en_US',
            ProfileId = p.Id,
            TimeZoneSidKey = 'America/Los_Angeles',
            UserName = 'factory.' + suffix + '@example.com'
        );
    }

    // UserRole, User-with-role, and PermissionSetAssignment are setup objects.
    // Running their DML inside System.runAs keeps it from colliding with
    // Account or Contact DML earlier in the same test transaction.
    public static User createUserWithAccess(String profileName, String roleName, List<String> permissionSetNames) {
        User u = newUser(profileName);
        System.runAs(new User(Id = UserInfo.getUserId())) {
            if (roleName != null) {
                UserRole role = new UserRole(Name = roleName);
                insert role;
                u.UserRoleId = role.Id;
            }
            insert u;
            if (permissionSetNames != null && !permissionSetNames.isEmpty()) {
                List<PermissionSetAssignment> assignments = new List<PermissionSetAssignment>();
                for (PermissionSet ps : [SELECT Id FROM PermissionSet WHERE Name IN :permissionSetNames]) {
                    assignments.add(new PermissionSetAssignment(AssigneeId = u.Id, PermissionSetId = ps.Id));
                }
                insert assignments;
            }
        }
        return u;
    }
}
```

## File: `force-app/main/default/classes/TestDataFactory.cls-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

## File: `force-app/main/default/classes/TestDataFactoryUsageTest.cls`

```apex
@IsTest
private class TestDataFactoryUsageTest {
    @TestSetup
    static void setup() {
        TestDataFactory.createAccounts(200, true);
    }

    @IsTest
    static void bulkAccountsAreVisibleInEveryMethod() {
        Assert.areEqual(200, [SELECT COUNT() FROM Account WHERE Name LIKE 'Factory Account %'],
            'Setup records are available to each test method');
    }

    @IsTest
    static void deletionsRollBackBetweenMethods() {
        delete [SELECT Id FROM Account WHERE Name = 'Factory Account 0'];
        Assert.areEqual(199, [SELECT COUNT() FROM Account WHERE Name LIKE 'Factory Account %'],
            'The delete is local to this method; the other method still sees 200');
    }

    @IsTest
    static void createsUserWithRoleAfterNonSetupDml() {
        insert new Account(Name = 'Mixed DML Guard');
        User u = TestDataFactory.createUserWithAccess('Standard User', 'Factory Test Role', null);
        User reloaded = [SELECT Id, UserRoleId FROM User WHERE Id = :u.Id];
        Assert.isNotNull(reloaded.UserRoleId, 'Role assigned without a mixed DML error');
    }

    @IsTest
    static void contactsAreBuiltInOneStatement() {
        List<Account> parents = [SELECT Id FROM Account WHERE Name LIKE 'Factory Account %' LIMIT 50];
        Integer before = Limits.getDmlStatements();
        TestDataFactory.createContacts(parents, 2, true);
        Assert.areEqual(before + 1, Limits.getDmlStatements(), 'Bulk factory uses a single insert');
    }
}
```

UNVERIFIED (2026-10-03): the profile name `Standard User` comes from the Apex Developer Guide's own samples; confirm it exists in the target org, or pass the org's equivalent. Required fields and validation rules on Account and Contact in the target org can require more defaults than the factory sets.

## File: `force-app/main/default/classes/TestDataFactoryUsageTest.cls-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

## Manifest: `manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>TestDataFactory</members>
        <members>TestDataFactoryUsageTest</members>
        <name>ApexClass</name>
    </types>
    <version>67.0</version>
</Package>
```

## Verify

```bash
python3 skills/apex/test-data-factory-patterns/scripts/check_test_data_factory_patterns.py --apex-dir force-app/main/default/classes
sf apex run test --class-names TestDataFactoryUsageTest --result-format human --target-org <alias>
```

Run the test from the UI as well as through a validation deploy: mixed DML validation is skipped during deployment, so only the UI run proves the `runAs` wrapping is needed and present.
