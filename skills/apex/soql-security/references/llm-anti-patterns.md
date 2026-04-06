# LLM Anti-Patterns — SOQL Security

Common mistakes AI coding assistants make when generating or advising on SOQL injection prevention and CRUD/FLS enforcement.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Concatenating user input directly into dynamic SOQL

**What the LLM generates:**

```apex
String searchTerm = userInput;
String query = 'SELECT Id, Name FROM Account WHERE Name LIKE \'%' + searchTerm + '%\'';
List<Account> results = Database.query(query);
// SOQL injection: user sends "' OR Name != '"
```

**Why it happens:** LLMs generate dynamic SOQL with string concatenation because it reads naturally. This is the textbook SOQL injection vulnerability — a malicious input can alter the query structure.

**Correct pattern:**

```apex
// Option 1: Use bind variables (preferred — immune to injection)
String searchTerm = '%' + userInput + '%';
List<Account> results = [SELECT Id, Name FROM Account WHERE Name LIKE :searchTerm];

// Option 2: If dynamic SOQL is required, escape single quotes
String safeTerm = '%' + String.escapeSingleQuotes(userInput) + '%';
String query = 'SELECT Id, Name FROM Account WHERE Name LIKE \'' + safeTerm + '\'';
List<Account> results = Database.query(query);
```

**Detection hint:** `Database\.query\(.*\+.*` where the concatenated variable comes from user input without `String.escapeSingleQuotes`.

---

## Anti-Pattern 2: Using WITH SECURITY_ENFORCED but not handling the exception it throws

**What the LLM generates:**

```apex
@AuraEnabled
public static List<Account> getAccounts() {
    return [SELECT Id, Name, SSN__c FROM Account WITH SECURITY_ENFORCED];
    // Throws System.QueryException if user lacks FLS on SSN__c
}
```

**Why it happens:** LLMs add `WITH SECURITY_ENFORCED` for FLS compliance but do not handle the `QueryException` it throws when a field is inaccessible. The unhandled exception crashes the LWC component with a cryptic error instead of gracefully degrading.

**Correct pattern:**

```apex
@AuraEnabled
public static List<Account> getAccounts() {
    try {
        return [SELECT Id, Name, SSN__c FROM Account WITH SECURITY_ENFORCED];
    } catch (System.QueryException e) {
        // WITH SECURITY_ENFORCED throws when FLS fails
        // Option: fall back to accessible fields only
        return [SELECT Id, Name FROM Account WITH SECURITY_ENFORCED];
        // Or: throw a user-friendly error
        // throw new AuraHandledException('You do not have access to all required fields.');
    }
}
```

**Detection hint:** `WITH SECURITY_ENFORCED` in a query without a surrounding try/catch for `QueryException`.

---

## Anti-Pattern 3: Using WITH USER_MODE but calling Database.query() with string SOQL

**What the LLM generates:**

```apex
String query = 'SELECT Id, Name FROM Account WHERE Industry = :industry';
List<Account> results = Database.query(query); // Runs in system mode
// WITH USER_MODE cannot be appended to Database.query string
```

**Why it happens:** LLMs know about `WITH USER_MODE` but forget it is a compile-time clause for inline SOQL, not for dynamic `Database.query()`. For dynamic SOQL with user-mode enforcement, you must use `Database.query(query, AccessLevel.USER_MODE)`.

**Correct pattern:**

```apex
// For inline SOQL — WITH USER_MODE works
List<Account> results = [SELECT Id, Name FROM Account WHERE Industry = :industry WITH USER_MODE];

// For dynamic SOQL — use AccessLevel parameter
String query = 'SELECT Id, Name FROM Account WHERE Industry = :industry';
List<Account> results = Database.query(query, AccessLevel.USER_MODE);
```

**Detection hint:** `Database\.query\(` without `AccessLevel.USER_MODE` as the second parameter, combined with missing `WITH USER_MODE` in the query string.

---

## Anti-Pattern 4: Relying on stripInaccessible for SOQL injection protection

**What the LLM generates:**

```apex
// "Secure" query
String query = 'SELECT Id, ' + userFieldList + ' FROM Account';
List<Account> results = Database.query(query);
SObjectAccessDecision decision = Security.stripInaccessible(AccessType.READABLE, results);
// FLS is stripped, but the query is still injectable via userFieldList
```

**Why it happens:** LLMs confuse FLS enforcement with injection prevention. `stripInaccessible` removes fields the user cannot access from the result set, but it does nothing to prevent SOQL injection in the query string itself. An attacker can inject `Id FROM Account WHERE Name != '' //` to alter the query.

**Correct pattern:**

```apex
// Validate field names against describe results BEFORE building the query
Set<String> allowedFields = Schema.SObjectType.Account.fields.getMap().keySet();
List<String> safeFields = new List<String>();
for (String field : userRequestedFields) {
    if (allowedFields.contains(field.toLowerCase())) {
        safeFields.add(field);
    }
}
String query = 'SELECT ' + String.join(safeFields, ', ') + ' FROM Account';
List<Account> results = Database.query(query);

// THEN also strip inaccessible fields for FLS
SObjectAccessDecision decision = Security.stripInaccessible(AccessType.READABLE, results);
return decision.getRecords();
```

**Detection hint:** Dynamic SOQL with user-provided field or object names that are not validated against `Schema.SObjectType` before query execution.

---

## Anti-Pattern 5: Omitting CRUD/FLS checks entirely in classes without sharing keyword

**What the LLM generates:**

```apex
public class DataExporter {
    // No sharing keyword — defaults to without sharing in many contexts
    @AuraEnabled
    public static List<Account> exportData() {
        return [SELECT Id, Name, AnnualRevenue, SSN__c FROM Account];
        // No sharing enforcement, no FLS, no CRUD check
    }
}
```

**Why it happens:** LLMs generate the query without any security clause and omit the sharing keyword. For `@AuraEnabled` methods, this means any user can access any record and any field — a critical security vulnerability that would fail a Salesforce security review.

**Correct pattern:**

```apex
public with sharing class DataExporter {
    @AuraEnabled
    public static List<Account> exportData() {
        return [SELECT Id, Name, AnnualRevenue FROM Account WITH USER_MODE];
    }
}
```

**Detection hint:** `@AuraEnabled` methods in classes without `with sharing`, and SOQL without `WITH USER_MODE` or `WITH SECURITY_ENFORCED`.

---

## Anti-Pattern 6: Building dynamic ORDER BY or LIMIT from user input without validation

**What the LLM generates:**

```apex
String sortField = request.params.get('sort');
String query = 'SELECT Id, Name FROM Account ORDER BY ' + sortField + ' LIMIT 100';
List<Account> results = Database.query(query);
// Injection: sort = "Name; DELETE [SELECT Id FROM Account]"
```

**Why it happens:** LLMs parameterize WHERE clauses but forget that ORDER BY, LIMIT, and other clauses are equally injectable. An attacker can inject arbitrary SOQL through the sort field parameter.

**Correct pattern:**

```apex
// Whitelist allowed sort fields
Map<String, String> allowedSorts = new Map<String, String>{
    'name' => 'Name',
    'created' => 'CreatedDate',
    'revenue' => 'AnnualRevenue'
};
String sortField = allowedSorts.get(request.params.get('sort')?.toLowerCase());
if (sortField == null) {
    sortField = 'Name'; // Safe default
}
String query = 'SELECT Id, Name FROM Account ORDER BY ' + sortField + ' LIMIT 100';
List<Account> results = Database.query(query);
```

**Detection hint:** User-provided values concatenated into `ORDER BY`, `GROUP BY`, or `LIMIT` clauses without whitelist validation.
