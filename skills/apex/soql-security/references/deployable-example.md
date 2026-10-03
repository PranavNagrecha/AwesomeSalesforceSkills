# Deployable Example: Injection-Safe, User-Mode Account Search

A complete LWC-facing search controller, its test class, and the manifest. It uses only idioms documented in the Apex Developer Guide, Version 67.0: `Database.queryWithBinds` with `AccessLevel.USER_MODE` (Dynamic SOQL), a structural allowlist (SOQL Injection Defenses), and `System.runAs` with a Minimum Access user (Using the runAs Method). The same class is the "good" fixture for `scripts/check_soql_security.py`.

## File: `force-app/main/default/classes/AccountSearchController.cls`

```apex
public with sharing class AccountSearchController {
    private static final Map<String, String> SORTABLE = new Map<String, String>{
        'name' => 'Name',
        'created' => 'CreatedDate',
        'revenue' => 'AnnualRevenue'
    };
    private static final Integer MAX_ROWS = 200;

    @AuraEnabled(cacheable=true)
    public static List<Account> search(String searchTerm, String sortKey, Integer rowLimit) {
        String sortField = SORTABLE.get(sortKey == null ? 'name' : sortKey.toLowerCase());
        if (sortField == null) {
            throw new AuraHandledException('Unsupported sort key.');
        }
        Integer safeLimit = (rowLimit == null || rowLimit < 1 || rowLimit > MAX_ROWS) ? MAX_ROWS : rowLimit;
        Map<String, Object> binds = new Map<String, Object>{
            'pattern' => '%' + (searchTerm == null ? '' : searchTerm) + '%',
            'maxRows' => safeLimit
        };
        // sortField comes only from the SORTABLE allowlist above
        String soql = 'SELECT Id, Name, AnnualRevenue FROM Account WHERE Name LIKE :pattern '
            + 'ORDER BY ' + sortField + ' LIMIT :maxRows'; // allowlisted
        return Database.queryWithBinds(soql, binds, AccessLevel.USER_MODE);
    }
}
```

Why each line is there:

| Element | Purpose |
|---|---|
| `with sharing` | Record visibility, stated explicitly at every `apiVersion` |
| `SORTABLE` map | Structural input never reaches the query unless it is a known key |
| `binds` map | Values are data, so a quote in `searchTerm` cannot change the query |
| `AccessLevel.USER_MODE` | Object permissions and field-level security; required argument for `queryWithBinds` |
| `MAX_ROWS` clamp | The caller cannot request an unbounded result |

## File: `force-app/main/default/classes/AccountSearchController.cls-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

## File: `force-app/main/default/classes/AccountSearchControllerTest.cls`

```apex
@IsTest
private class AccountSearchControllerTest {
    @TestSetup
    static void seed() {
        insert new List<Account>{
            new Account(Name = 'Acme North'),
            new Account(Name = 'Acme South'),
            new Account(Name = 'Globex')
        };
    }

    @IsTest
    static void returnsMatchesInAllowlistedOrder() {
        Test.startTest();
        List<Account> rows = AccountSearchController.search('Acme', 'name', 10);
        Test.stopTest();
        Assert.areEqual(2, rows.size(), 'Both Acme accounts should match');
        Assert.areEqual('Acme North', rows[0].Name, 'Rows are sorted by Name');
    }

    @IsTest
    static void rejectsSortKeyOutsideAllowlist() {
        Boolean rejected = false;
        try {
            AccountSearchController.search('Acme', 'Name FROM User --', 10);
        } catch (AuraHandledException e) {
            rejected = true;
        }
        Assert.isTrue(rejected, 'A structural value outside the allowlist must be rejected');
    }

    @IsTest
    static void treatsQuotesInSearchTermAsData() {
        List<Account> rows = AccountSearchController.search('\' OR Name != \'', 'name', 10);
        Assert.areEqual(0, rows.size(), 'Quote characters must not change the query');
    }

    @IsTest
    static void blocksUserWithoutAccountAccess() {
        Profile minimum = [SELECT Id FROM Profile WHERE Name = 'Minimum Access - Salesforce' LIMIT 1];
        User lowAccess = new User(
            Alias = 'lowacc',
            Email = 'lowaccess@example.com',
            EmailEncodingKey = 'UTF-8',
            LastName = 'LowAccess',
            LanguageLocaleKey = 'en_US',
            LocaleSidKey = 'en_US',
            ProfileId = minimum.Id,
            TimeZoneSidKey = 'America/Los_Angeles',
            UserName = 'lowaccess' + DateTime.now().getTime() + '@example.com'
        );
        insert lowAccess;

        Boolean blocked = false;
        System.runAs(lowAccess) {
            try {
                AccountSearchController.search('Acme', 'name', 10);
            } catch (Exception e) {
                blocked = true;
            }
        }
        Assert.isTrue(blocked, 'User mode must block a user with no Account read access');
    }
}
```

UNVERIFIED (2026-10-03): the exact exception type a user-mode query raises when the running user has no read access to the object is not stated in the fetched guides, so the last test catches `Exception`. The Apex Developer Guide's own `withPermissionSetId` sample expects `SecurityException` for the equivalent user-mode insert. That the standard Minimum Access profile has no Account read access is also an assumption to confirm in the target org.

## File: `force-app/main/default/classes/AccountSearchControllerTest.cls-meta.xml`

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
        <members>AccountSearchController</members>
        <members>AccountSearchControllerTest</members>
        <name>ApexClass</name>
    </types>
    <version>67.0</version>
</Package>
```

## Verify

```bash
python3 skills/apex/soql-security/scripts/check_soql_security.py force-app/main/default/classes
sf project deploy start --manifest manifest/package.xml --test-level RunSpecifiedTests --tests AccountSearchControllerTest --dry-run --target-org <alias>
```

The checker should report no finding for this class: the `ORDER BY` concatenation carries an `allowlisted` comment and the query uses `AccessLevel.USER_MODE`.
