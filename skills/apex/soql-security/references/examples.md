# SOQL Security — Examples

## Example 1: Fixing an Injectable Search Method

### Before (Vulnerable)

```apex
public class AccountSearchController {
    @AuraEnabled
    public static List<Account> searchAccounts(String searchTerm, String sortField) {
        // ❌ INJECTION: both searchTerm and sortField are user-controlled
        String query = 'SELECT Id, Name, AnnualRevenue FROM Account '
            + 'WHERE Name LIKE \'%' + searchTerm + '%\' '
            + 'ORDER BY ' + sortField;
        return Database.query(query);
    }
}
```

An attacker can pass `sortField = 'Name FROM User LIMIT 1 --'` and extract User records.

### After (Secure)

```apex
public class AccountSearchController {

    private static final Set<String> ALLOWED_SORT_FIELDS =
        new Set<String>{'Name', 'CreatedDate', 'AnnualRevenue', 'LastModifiedDate'};

    @AuraEnabled(cacheable=true)
    public static List<Account> searchAccounts(String searchTerm, String sortField) {
        // ✅ Validate sort field against allowlist
        if (!ALLOWED_SORT_FIELDS.contains(sortField)) {
            throw new AuraHandledException('Invalid sort field.');
        }

        // ✅ Bind variable for user value; WITH USER_MODE for FLS
        String likePattern = '%' + String.escapeSingleQuotes(searchTerm) + '%';
        String query = 'SELECT Id, Name, AnnualRevenue FROM Account '
            + 'WHERE Name LIKE :likePattern '
            + 'ORDER BY ' + sortField + ' ASC '
            + 'WITH USER_MODE';
        return Database.query(query);
    }
}
```

Note: `String.escapeSingleQuotes()` is added as a defense-in-depth for the LIKE pattern, but the bind variable (`:likePattern`) is the primary protection.

---

## Example 2: FLS Enforcement on AuraEnabled Method

```apex
public with sharing class ContactController {

    @AuraEnabled(cacheable=true)
    public static List<Contact> getContactsForAccount(Id accountId) {
        // WITH USER_MODE: enforces sharing, CRUD, and FLS
        // If user can't read SSN__c, the field is excluded from results (QueryException thrown)
        return [
            SELECT Id, FirstName, LastName, Email, Phone
            FROM Contact
            WHERE AccountId = :accountId
            WITH USER_MODE
            ORDER BY LastName ASC
        ];
    }
}
```

---

## Example 3: stripInaccessible for Safe DML in a Service Class

```apex
public with sharing class CaseService {

    public static void updateCases(List<Case> casesToUpdate) {
        // stripInaccessible removes fields the user can't update
        // Prevents "field not updateable" errors AND FLS bypass
        SObjectAccessDecision decision = Security.stripInaccessible(
            AccessType.UPDATABLE,
            casesToUpdate
        );

        // Check which fields were actually stripped (optional — useful for logging)
        Map<String, Set<String>> removedFields = decision.getRemovedFields();
        if (!removedFields.isEmpty()) {
            System.debug('FLS stripped fields: ' + JSON.serialize(removedFields));
        }

        update decision.getRecords();
    }

    public static List<Case> getOpenCases() {
        // stripInaccessible for SOQL results — silently removes fields user can't read
        SObjectAccessDecision decision = Security.stripInaccessible(
            AccessType.READABLE,
            [SELECT Id, Subject, Description, Internal_Notes__c FROM Case WHERE Status = 'Open']
        );
        return (List<Case>) decision.getRecords();
    }
}
```

---

## Example 4: Schema Describe for Safe Dynamic Field Access

When you need to work with field names dynamically (e.g. building a generic export), use Schema.getGlobalDescribe() instead of trusting user input.

```apex
public class DynamicExportService {

    // ✅ Get field names from Schema describe — never from user input
    public static List<String> getAccessibleFields(String objectApiName) {
        Map<String, Schema.SObjectField> fieldMap =
            Schema.getGlobalDescribe()
                  .get(objectApiName)
                  ?.getDescribe()
                  .fields.getMap();

        if (fieldMap == null) {
            throw new IllegalArgumentException('Unknown object: ' + objectApiName);
        }

        List<String> accessibleFields = new List<String>();
        for (String fieldName : fieldMap.keySet()) {
            Schema.DescribeFieldResult dfr = fieldMap.get(fieldName).getDescribe();
            if (dfr.isAccessible()) {
                accessibleFields.add(fieldName);
            }
        }
        return accessibleFields;
    }
}
```

---

## Example 5: Test Class — Verifying FLS Enforcement

```apex
@IsTest
private class ContactControllerTest {

    @IsTest
    static void testFLSEnforcedForRestrictedUser() {
        // Create a user without read on a sensitive field
        Profile minAccessProfile = [SELECT Id FROM Profile WHERE Name = 'Minimum Access - Salesforce' LIMIT 1];
        User restrictedUser = new User(
            FirstName = 'Test',
            LastName = 'FLSUser',
            Email = 'flstest@example.com',
            Username = 'flstest@example.com.test',
            Alias = 'flst',
            ProfileId = minAccessProfile.Id,
            TimeZoneSidKey = 'America/New_York',
            LocaleSidKey = 'en_US',
            EmailEncodingKey = 'UTF-8',
            LanguageLocaleKey = 'en_US'
        );
        insert restrictedUser;

        System.runAs(restrictedUser) {
            // Either expect exception or verify no sensitive fields returned
            try {
                List<Contact> results = ContactController.getContactsForAccount(null);
                // Verify sensitive field not in results
                for (Contact c : results) {
                    System.assertEquals(null, c.get('Sensitive_Field__c'),
                        'Restricted user should not see sensitive fields');
                }
            } catch (QueryException e) {
                // Expected if WITH SECURITY_ENFORCED used — field inaccessible
                System.assert(e.getMessage().contains('inaccessible'),
                    'Expected FLS exception');
            }
        }
    }
}
```
