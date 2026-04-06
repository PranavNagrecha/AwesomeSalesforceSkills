# Examples — Secure Coding Review Checklist

## Example 1: Fixing CRUD/FLS Gaps in an @AuraEnabled Controller

**Context:** An ISV is preparing a managed package for AppExchange submission. The package includes an LWC that displays Account and Contact data through an `@AuraEnabled` Apex controller. The controller uses inline SOQL with no CRUD/FLS enforcement.

**Problem:** The Checkmarx source scanner flags every SOQL query in the controller as a CRUD/FLS violation. The security review team rejects the submission with the comment: "All data access must respect the running user's object and field permissions."

**Solution:**

```apex
// BEFORE — fails security review
public with sharing class AccountController {
    @AuraEnabled(cacheable=true)
    public static List<Account> getAccounts(String industry) {
        return [SELECT Id, Name, AnnualRevenue, Phone
                FROM Account
                WHERE Industry = :industry];
    }
}

// AFTER — passes security review
public with sharing class AccountController {
    @AuraEnabled(cacheable=true)
    public static List<Account> getAccounts(String industry) {
        return [SELECT Id, Name, AnnualRevenue, Phone
                FROM Account
                WHERE Industry = :industry
                WITH USER_MODE];
    }
}
```

**Why it works:** Adding `WITH USER_MODE` to the SOQL query forces the platform to evaluate the running user's profile permissions for both object-level CRUD and field-level read access. If the user cannot see `AnnualRevenue`, the query throws a `System.FlsException` rather than silently returning the value. This is a single-line change that addresses the most common security review failure category. The Salesforce Code Analyzer and Checkmarx both recognize `WITH USER_MODE` as valid CRUD/FLS enforcement.

---

## Example 2: Preventing SOQL Injection in Dynamic Search

**Context:** A custom search component allows users to type a keyword and search across multiple objects. The Apex controller builds a dynamic SOQL query by concatenating the search term into the WHERE clause.

**Problem:** The Salesforce Code Analyzer PMD rule `ApexSOQLInjection` flags the query. An attacker could input `' OR Name != '` to bypass the WHERE clause filter and retrieve all records regardless of the intended filter.

**Solution:**

```apex
// BEFORE — vulnerable to SOQL injection
public with sharing class SearchController {
    @AuraEnabled
    public static List<Account> search(String keyword) {
        String query = 'SELECT Id, Name FROM Account '
                     + 'WHERE Name LIKE \'%' + keyword + '%\'';
        return Database.query(query);
    }
}

// AFTER — injection-safe with escapeSingleQuotes + stripInaccessible
public with sharing class SearchController {
    @AuraEnabled
    public static List<Account> search(String keyword) {
        String safeKeyword = '%' + String.escapeSingleQuotes(keyword) + '%';
        String query = 'SELECT Id, Name FROM Account '
                     + 'WHERE Name LIKE :safeKeyword';
        // Use bind variable in dynamic query where possible (Spring '21+)
        List<Account> results = Database.queryWithBinds(
            'SELECT Id, Name FROM Account WHERE Name LIKE :keyword',
            new Map<String, Object>{ 'keyword' => safeKeyword },
            AccessLevel.USER_MODE
        );
        return results;
    }
}
```

**Why it works:** `Database.queryWithBinds()` with `AccessLevel.USER_MODE` combines injection prevention (bind variables) with CRUD/FLS enforcement in a single call. The bind variable prevents the user input from being interpreted as SOQL syntax. When `queryWithBinds` is not available (pre-Spring '21), `String.escapeSingleQuotes()` escapes single quotes in the input, neutralizing the most common injection vector. The `AccessLevel.USER_MODE` parameter replaces the need for separate `stripInaccessible()` calls.

---

## Anti-Pattern: Checking CRUD/FLS With Schema Describes But Missing Fields

**What practitioners do:** They add `Schema.SObjectType.Account.getDescribe().isAccessible()` at the top of the method, checking object-level access, but skip field-level checks for individual fields in the SELECT clause. They assume object-level access implies field-level access.

**What goes wrong:** The security review rejects the submission because field-level security is not enforced. A user with read access to the Account object but without access to the `AnnualRevenue` field would still receive that field's value in the query results. The Checkmarx scanner specifically checks for per-field `isAccessible()` calls when the describe pattern is used.

**Correct approach:** Use `WITH USER_MODE` to enforce both object-level and field-level security in a single mechanism, or call `Security.stripInaccessible(AccessType.READABLE, records)` on query results to physically remove inaccessible fields. Both approaches satisfy the security review without requiring manual per-field describe checks.
