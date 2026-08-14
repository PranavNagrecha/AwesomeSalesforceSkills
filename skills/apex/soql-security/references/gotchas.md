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

## 2. FLS Enforcement Throws on ANY Inaccessible Field — It Does Not Filter

If any field in the SELECT list is inaccessible to the running user, the query throws a `System.QueryException` and the entire query fails. This means:
- A user who can't see `AnnualRevenue` gets no records at all, not records without that field
- For UI components where partial results are OK, use `stripInaccessible()` instead — that is the whole difference between the two, and switching enforcement idiom does not change it
- `WITH USER_MODE` (GA in Spring '23 / API 57.0) behaves the same way

**Which idiom applies is decided by the `apiVersion` in the class's `.cls-meta.xml`, not the org's release** — a Summer '26 org runs a class pinned to 58.0 quite happily. `WITH SECURITY_ENFORCED` was removed in 67.0 and does not compile there (`WITH SECURITY_ENFORCED is no longer supported, use WITH USER_MODE instead`); below that it still compiles but is the weaker construct. `WITH USER_MODE` is the read idiom at every version from 57.0. For the per-version breakdown read the canonical table — [`agents/_shared/AGENT_CONTRACT.md`](../../../../agents/_shared/AGENT_CONTRACT.md) § *Apex security idiom by API version* — rather than a copy of it here.

---

## 3. `WITH USER_MODE` vs `with sharing` — They Are Not The Same

| | `with sharing` | `WITH USER_MODE` |
|--|--------------|-----------------|
| Enforces row-level sharing rules | ✅ | ✅ |
| Enforces object-level CRUD | ❌ | ✅ |
| Enforces field-level security | ❌ | ✅ |
| Available since | Always | GA Spring '23 (API 57.0) |

A class declared `with sharing` does NOT enforce FLS — the keyword never did, at any version. **At `apiVersion` ≤ 66.0** that means you can read `SSN__c` from a `with sharing` class unless you also use `WITH USER_MODE` or `stripInaccessible`. **At 67.0+** the unqualified query is blocked anyway, but by the default access mode rather than by the keyword: the sharing keyword still contributes nothing to FLS.

---

## 4. `@AuraEnabled` Methods Run in System Context By Default — Below API 67.0

This gotcha is version-gated, and the gate is the class's own `apiVersion`, not the org's release.

**At `apiVersion` ≤ 66.0** — even when a user calls an `@AuraEnabled` method, Apex runs in system context unless:
- The class is declared `with sharing` (enforces row sharing)
- The query enforces FLS with `WITH USER_MODE` (57.0+), or `Security.stripInaccessible` on the result

Without these, your LWC can expose fields the user doesn't have read access to.

**At `apiVersion` 67.0+ the default inverted.** Apex database operations run in user mode by default, and a class with no sharing keyword defaults to `with sharing`. The exposure risk above is closed by default; the new risk is its mirror image — integration, batch, and system-utility code that legitimately needs elevated access now silently returns fewer rows, or throws, unless it opts in with `WITH SYSTEM_MODE` / `AccessLevel.SYSTEM_MODE`. Adding "user mode for security" to a 67.0 class is a no-op.

**Do not treat `WITH SECURITY_ENFORCED` as satisfying this at any version** — see Gotcha 2. `scripts/check_soql_security.py` reports it as a finding whose severity it derives from the sibling `.cls-meta.xml`: CRITICAL at 67.0+ (a build failure), LOW below it (legacy to migrate).

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

## 6. Inline SOQL in `without sharing` Classes — What It Bypasses Depends on the `apiVersion`

Inline SOQL (not dynamic) is safe from injection but not automatically safe from an access-control perspective. **At `apiVersion` ≤ 66.0** the query below bypasses both sharing and FLS. **At 67.0+** `without sharing` is a record-visibility keyword only: database operations enforce the running user's FLS and object permissions by default, so code that genuinely needs them off states it per statement (`WITH SYSTEM_MODE`, `AccessLevel.SYSTEM_MODE`) — which is the improvement, because the bypass is now written down.

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

In Visualforce `StandardController` extensions, the platform enforces FLS automatically for bound fields (`{!account.Name}`). But at `apiVersion` ≤ 66.0 Apex queries in the extension class still bypass FLS unless you add `WITH USER_MODE` (at 67.0+ they enforce it by default). Don't assume Visualforce field binding protects your Apex layer either way.

---

## 9. Dynamic SOQL in Test Classes Can Mask Injection Vulnerabilities

If you use `Test.isRunningTest()` to skip validation in test context, you won't catch injection vulnerabilities in test coverage. Never bypass allowlist or bind variable logic in tests.

---

## 10. `Security.stripInaccessible` Was Introduced in Summer '18

If you're on an older API version or deploying to a legacy scratch org definition, `stripInaccessible` may not be available. Check the org's API version. For environments before Summer '18, use `Schema.DescribeFieldResult.isAccessible()` per-field checks.
