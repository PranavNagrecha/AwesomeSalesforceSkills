# SOQL Security — Gotchas

## 1. `String.escapeSingleQuotes()` Does NOT Protect Structural SOQL

`String.escapeSingleQuotes()` only prevents injection through quoted string values. It does nothing when user input appears in:
- Field names: `SELECT ` + userField + ` FROM Account`
- Object names: `SELECT Id FROM ` + userObject
- ORDER BY: `ORDER BY ` + sortField
- Operators: `WHERE Status ` + operator + ` 'Active'`
- LIMIT/OFFSET: `LIMIT ` + userLimit

For all structural elements, use an **allowlist**. `escapeSingleQuotes` is a supplementary defense for string values only.

---

## 2. `WITH SECURITY_ENFORCED` Throws on ANY Inaccessible Field — Even Inactive Ones

If any field in the SELECT list is inaccessible to the running user, `WITH SECURITY_ENFORCED` throws a `System.QueryException` — the entire query fails. This means:
- A user who can't see `AnnualRevenue` gets no records at all, not records without that field
- For UI components where partial results are OK, use `stripInaccessible()` instead
- `WITH USER_MODE` (Winter '23+) has the same behavior

---

## 3. `WITH USER_MODE` vs `with sharing` — They Are Not The Same

| | `with sharing` | `WITH USER_MODE` |
|--|--------------|-----------------|
| Enforces row-level sharing rules | ✅ | ✅ |
| Enforces object-level CRUD | ❌ | ✅ |
| Enforces field-level security | ❌ | ✅ |
| Available since | Always | Winter '23 (API 56) |

A class declared `with sharing` does NOT enforce FLS. You can read `SSN__c` from a `with sharing` class if you don't also use `WITH USER_MODE` or `stripInaccessible`.

---

## 4. `@AuraEnabled` Methods Run in System Context By Default

Even when a user calls an `@AuraEnabled` method, Apex runs in system context unless:
- The class is declared `with sharing` (enforces row sharing)
- The query uses `WITH USER_MODE` or `WITH SECURITY_ENFORCED` (enforces FLS)

Without these, your LWC can expose fields the user doesn't have read access to.

---

## 5. Bind Variables Don't Work for All SOQL Clauses

Bind variables (`:varName`) are only valid for **values** in WHERE clauses, not for:
- Field names in SELECT
- Object names in FROM
- ORDER BY fields
- LIMIT values (though `:intVar` works for LIMIT since API 20)

```apex
// ✅ LIMIT with bind variable works
Integer maxRecords = 100;
List<Account> accts = [SELECT Id FROM Account LIMIT :maxRecords];

// ❌ Field name bind variable does NOT work — compile error
String fieldName = 'Name';
List<Account> accts = [SELECT :fieldName FROM Account]; // Invalid
```

---

## 6. Inline SOQL in `without sharing` Classes Bypasses Everything

If you write inline SOQL (not dynamic) inside a `without sharing` class, you still bypass FLS and sharing. The query syntax is safe from injection, but it's not secure from an access control perspective.

```apex
public without sharing class BatchProcessor {
    // ❌ Even though no injection risk, this exposes ALL account records
    // regardless of the user's sharing access
    List<Account> allAccounts = [SELECT Id, SSN__c FROM Account];
}
```

---

## 7. `stripInaccessible` Returns a New Collection — The Original Is Unchanged

```apex
SObjectAccessDecision decision = Security.stripInaccessible(AccessType.READABLE, records);
// ❌ records still has all the original fields
// ✅ Use decision.getRecords() for the safe version
List<Account> safeRecords = (List<Account>) decision.getRecords();
```

---

## 8. SOQL in Visualforce Controllers Has Different Rules

In Visualforce `StandardController` extensions, the platform enforces FLS automatically for bound fields (`{!account.Name}`). But Apex queries in the extension class still bypass FLS unless you add `WITH USER_MODE`. Don't assume Visualforce field binding protects your Apex layer.

---

## 9. Dynamic SOQL in Test Classes Can Mask Injection Vulnerabilities

If you use `Test.isRunningTest()` to skip validation in test context, you won't catch injection vulnerabilities in test coverage. Never bypass allowlist or bind variable logic in tests.

---

## 10. `Security.stripInaccessible` Was Introduced in Summer '18

If you're on an older API version or deploying to a legacy scratch org definition, `stripInaccessible` may not be available. Check the org's API version. For environments before Summer '18, use `Schema.DescribeFieldResult.isAccessible()` per-field checks.
