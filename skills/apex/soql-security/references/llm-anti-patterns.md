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

**At `apiVersion` 67.0+ the clause is gone** and the code above does not compile at all (`WITH SECURITY_ENFORCED is no longer supported, use WITH USER_MODE instead`). Read the fix as `WITH USER_MODE`, which throws the same `QueryException` and needs the same handling.

**Detection hint:** `WITH SECURITY_ENFORCED` in a query without a surrounding try/catch for `QueryException`.

---

## Anti-Pattern 3: Claiming WITH USER_MODE cannot be used in a Database.query string

**What the LLM generates:**

```apex
String query = 'SELECT Id, Name FROM Account WHERE Industry = :industry';
List<Account> results = Database.query(query); // access mode left implicit
// "WITH USER_MODE is compile-time only, so dynamic SOQL cannot enforce FLS"
```

**Why it happens:** The model remembers that `WITH USER_MODE` appears in inline SOQL examples and invents a restriction. An earlier version of this skill made the same claim. The Version 67.0 Apex Developer Guide shows `Database.query('SELECT Id FROM Account__dlm WITH USER_MODE LIMIT 1')` in its integration-test example, so the clause is valid inside a dynamic string.

**Correct pattern:**

```apex
// Inline SOQL
List<Account> a = [SELECT Id, Name FROM Account WHERE Industry = :industry WITH USER_MODE];

// Dynamic SOQL: either form enforces user mode; the AccessLevel argument keeps
// the query string free of security clauses and is required by queryWithBinds
List<Account> b = Database.query(
    'SELECT Id, Name FROM Account WHERE Industry = :industry', AccessLevel.USER_MODE);
Map<String, Object> binds = new Map<String, Object>{ 'industry' => industry };
List<Account> c = Database.queryWithBinds(
    'SELECT Id, Name FROM Account WHERE Industry = :industry', binds, AccessLevel.USER_MODE);
```

**Detection hint:** A `Database.query(` call in a class saved at 66.0 or earlier with neither `AccessLevel.USER_MODE` nor `WITH USER_MODE` in the string, or advice that says the clause is inline-only.

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

## Anti-Pattern 5: Omitting CRUD/FLS checks entirely in classes without sharing keyword (`apiVersion` ≤ 66.0)

**What the LLM generates:**

```apex
public class DataExporter {
    // No sharing keyword. At apiVersion <= 66.0 an @AuraEnabled method called
    // from LWC runs with sharing, but object and field permissions are NOT
    // enforced because system mode is the default there. At 67.0+ the class
    // runs with sharing and database operations run in user mode.
    @AuraEnabled
    public static List<Account> exportData() {
        return [SELECT Id, Name, AnnualRevenue, SSN__c FROM Account];
        // No FLS or CRUD check at <= 66.0 (sharing applies only because the
        // caller is LWC; any other entry point inherits or drops it)
    }
}
```

**Why it happens:** LLMs generate the query without any security clause and omit the sharing keyword. On a class pinned to `apiVersion` ≤ 66.0, still the common case for existing code, that `@AuraEnabled` method lets any user read any field on the records they can see (the Apex Developer Guide says an `@AuraEnabled` method called from LWC runs `with sharing` even without a keyword, but system mode still skips object and field permissions), a critical vulnerability that would fail a Salesforce security review. On a 67.0+ class both defaults invert and the gap closes on its own, so the correct pattern below is a no-op there rather than a fix; write it anyway, because the same source file is one `apiVersion` edit away from the old behavior and the explicit form reads the same at every version.

**Correct pattern:**

```apex
public with sharing class DataExporter {
    @AuraEnabled
    public static List<Account> exportData() {
        return [SELECT Id, Name, AnnualRevenue FROM Account WITH USER_MODE];
    }
}
```

**Detection hint:** `@AuraEnabled` methods in a class pinned below `apiVersion` 67.0 that declares no sharing keyword, whose SOQL has no `WITH USER_MODE` and no `Security.stripInaccessible` on the result. `WITH SECURITY_ENFORCED` does not clear this hint at any version; see Gotcha 3 in `references/gotchas.md`.

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

---

## Anti-Pattern 7: Saying the 67.0 user-mode default does not reach trigger bodies

**What the LLM generates:** "Triggers always run in system mode, so the query in this 67.0 trigger sees every Contact." The handler then assumes it will find all related records.

**Why it happens:** For years triggers were described as system-mode code. The Version 67.0 Apex Developer Guide now says the trigger itself runs without sharing, but "database operations within trigger bodies ... run in user mode unless system mode is explicitly specified", which "effectively enforces a with sharing context in the trigger body".

**Correct pattern:**

```apex
// trigger saved at apiVersion 67.0
trigger AccountContactSync on Account (after update) {
    // Deliberate elevation, written down: the sync must see every related Contact
    List<Contact> related = [
        SELECT Id, AccountId FROM Contact
        WHERE AccountId IN :Trigger.newMap.keySet()
        WITH SYSTEM_MODE
    ];
    AccountContactSyncHandler.apply(related);
}
```

**Detection hint:** A `.trigger` saved at 67.0+ whose SOQL or DML has no explicit access mode, together with logic that assumes all records are visible.

---

## Anti-Pattern 8: Escaping a value that is already a bind variable

**What the LLM generates:**

```apex
String likePattern = '%' + String.escapeSingleQuotes(searchTerm) + '%';
List<Account> rows = [SELECT Id FROM Account WHERE Name LIKE :likePattern];
```

**Why it happens:** The model stacks every defense it knows. A bind variable is already treated as data, so escaping it adds a literal backslash before each apostrophe and a search for `O'Brien` stops matching.

**Correct pattern:**

```apex
String likePattern = '%' + searchTerm + '%';
List<Account> rows = [SELECT Id FROM Account WHERE Name LIKE :likePattern WITH USER_MODE];
```

**Detection hint:** `escapeSingleQuotes` applied to a variable that is then used only after a `:` bind marker.

