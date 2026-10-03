# SOQL Security — Gotchas

Non-obvious behaviors that cause real security-review failures and production incidents. Each gotcha names its source. "Apex Guide" means the Apex Developer Guide, Version 67.0 (Summer '26). "Apex Reference" means the Apex Reference Guide, Version 67.0. "SOQL Reference" means the SOQL and SOSL Reference, Version 67.0.

The controlling fact for most of these is the `apiVersion` in the class's or trigger's own `-meta.xml`, not the org's release. A Summer '26 org runs a class saved at 58.0 with 58.0 behavior. For the per-version table read [`agents/_shared/AGENT_CONTRACT.md`](../../../../agents/_shared/AGENT_CONTRACT.md) § *Apex security idiom by API version*.

## Gotcha 1: `String.escapeSingleQuotes()` Does Not Protect Structural SOQL

**What happens:** A reviewer accepts `escapeSingleQuotes` as the injection fix, and the query is still injectable through a field name, sort column, operator, object name, or `LIMIT` value.

**When it occurs:** User input is concatenated anywhere outside a quoted string literal, for example `'SELECT ' + userField + ' FROM Account'`, `'ORDER BY ' + sortField`, `'WHERE Status ' + operator + ' \'Active\''`, or `'LIMIT ' + userLimit`. The Apex Guide says the method "adds the escape character (\) to all single quotation marks in a string" and "ensures that all single quotation marks are treated as enclosing strings, instead of database commands". That is the whole of what it does.

**How to avoid:** Use static SOQL and bind variables first (Apex Guide, SOQL Injection Defenses). Allowlist every structural element against a fixed set or a `Schema` describe. Treat `escapeSingleQuotes` as a fallback for a quoted literal that cannot be bound, never as the primary control. Do not escape a value that is already passed as a bind variable: a bind is treated as data, so escaping adds a literal backslash to the value you are searching for.

**Source:** Apex Guide, SOQL Injection and SOQL Injection Defenses; Apex Reference, String Class `escapeSingleQuotes`.

---

## Gotcha 2: FLS Enforcement on Read Throws; It Does Not Filter

**What happens:** A user who cannot read one selected field gets no rows at all, and the LWC shows an error instead of a list.

**When it occurs:** The query uses `WITH USER_MODE` (or `AccessLevel.USER_MODE`) and selects a field the running user cannot read. User mode "finds all FLS errors in your SOQL query" and "supports the getInaccessibleFields() method on QueryException to examine the full set of access errors". It also processes the `WHERE` clause and polymorphic fields such as `Owner`.

**How to avoid:** Decide per method whether the contract is fail-fast or degrade. For fail-fast, keep `WITH USER_MODE` and catch `QueryException`, reporting `getInaccessibleFields()`. For degrade, query and pass the result through `Security.stripInaccessible(AccessType.READABLE, rows)`. Switching enforcement idiom is the only way to change this behavior.

**Source:** Apex Guide, Set an Access Mode for Database Operations (Set an Access Mode for SOQL and SOSL Queries).

---

## Gotcha 3: `WITH SECURITY_ENFORCED` Is Not Supported at API 67.0 and Later

**What happens:** Code copied from an older example fails to save or deploy once its `apiVersion` is raised to 67.0.

**When it occurs:** Any Apex SOQL `SELECT` with `WITH SECURITY_ENFORCED` in a class or trigger saved at 67.0+. The Apex Guide versioned-behavior table for 67.0 says: "you cannot use the WITH SECURITY_ENFORCED clause in SOQL SELECT queries in Apex code. Instead, to run a SOQL or SOSL query in user mode, use the WITH USER_MODE clause." Below 67.0 the clause still compiles, and the SOQL Reference recommends `WITH USER_MODE` "because it has fewer limitations". UNVERIFIED (2026-10-03): the exact compiler message `WITH SECURITY_ENFORCED is no longer supported, use WITH USER_MODE instead` quoted by this skill's checker is not printed in any fetched guide.

**How to avoid:** Replace the clause with `WITH USER_MODE` before raising `apiVersion`. `scripts/check_soql_security.py` reports the clause as CRITICAL when the sibling `-meta.xml` says 67.0+ and as LOW below it.

**Source:** Apex Guide, Apex Versioned Behavior Changes (Version 67.0) and Apex Security and Sharing Model (Versioned Behavior Changes); SOQL Reference, WITH.

---

## Gotcha 4: `with sharing` Never Enforced FLS or Object Permissions

**What happens:** A `with sharing` class at `apiVersion` 66.0 or earlier returns `SSN__c` to a user whose profile hides that field.

**When it occurs:** Teams treat the sharing keyword as the whole security model. The Apex Guide is explicit: "Using the with sharing keyword doesn't enforce the user's permissions and field-level security." At 67.0+ the unqualified query is blocked anyway, but by the default access mode, not by the keyword.

**How to avoid:** Pair the sharing keyword with a field-level idiom: `WITH USER_MODE`, `AccessLevel.USER_MODE`, or `Security.stripInaccessible`. State user mode even at 67.0+, so the intent survives a later copy into an older class.

| | `with sharing` | `WITH USER_MODE` |
|--|--|--|
| Enforces record sharing | Yes | Yes |
| Enforces object permissions | No | Yes |
| Enforces field-level security | No | Yes |

**Source:** Apex Guide, Enforce Sharing Rules (Note) and Set an Access Mode for Database Operations (Note on user mode always applying sharing).

---

## Gotcha 5: At 66.0 and Earlier, a Keyword-less `@AuraEnabled` Class Is `with sharing` but Still Ignores FLS

**What happens:** A reviewer assumes a keyword-less `@AuraEnabled` controller at 66.0 runs without sharing and is surprised that record visibility is already restricted, while field-level security is still not enforced.

**When it occurs:** For classes saved at 66.0 or earlier with no sharing declaration, the Apex Guide lists the rules: if any class in the inheritance chain is saved at 67.0+ the class runs `with sharing`; "if the class is an Aura controller or an @AuraEnabled method called from a Lightning web component, the class runs in with sharing mode"; a non-entry-point class takes the caller's mode; otherwise it runs `without sharing`. Object and field permissions are not enforced at 66.0 and earlier because system mode is the default there. This corrects an earlier version of this skill, which said such a method runs without sharing.

**How to avoid:** Declare a sharing keyword on every class with SOQL or DML, as the Apex Guide recommends, and add a field-level idiom. At 67.0+ classes with no keyword run `with sharing` and database operations run in user mode, so the inverse risk appears: batch, integration, and utility code that needs elevation must opt in with `WITH SYSTEM_MODE` or `AccessLevel.SYSTEM_MODE`.

**Source:** Apex Guide, Apex Security and Sharing Model (Versioned Behavior Changes) and Use the with sharing, without sharing, and inherited sharing Keywords (Omitted Sharing).

---

## Gotcha 6: Trigger Bodies Run Without Sharing, but Their Queries Run in User Mode at 67.0+

**What happens:** A trigger saved at 67.0 suddenly sees fewer related records, or throws on a field the running user cannot read, after a version bump.

**When it occurs:** "Apex triggers can't have an explicit sharing declaration. Triggers always run implicitly in a without sharing context." However, "database operations within trigger bodies, including SOQL queries, SOSL queries, DML statements, and Database methods, run in user mode unless system mode is explicitly specified. User mode overrides the trigger's without sharing context and effectively enforces a with sharing context in the trigger body." This corrects an earlier version of this skill, which said the 67.0 default does not reach the trigger body.

**How to avoid:** Set an explicit access mode on every database operation in triggers and handlers, as the Apex Guide recommends. Use `WITH SYSTEM_MODE` only where the trigger genuinely needs all records, and delegate logic to a handler class that declares its own sharing keyword.

**Source:** Apex Guide, Use the with sharing, without sharing, and inherited sharing Keywords (Implementation in Apex Triggers, AccountUpdateTrigger example).

---

## Gotcha 7: Bind Variables Work for Values, Not for Structure or Object Fields in Dynamic SOQL

**What happens:** A developer tries to bind a field name, or binds `:record.Field__c` inside a `Database.query` string, and gets a compile error or `Variable does not exist` at run time.

**When it occurs:** Binds replace values only. In dynamic SOQL "you can't use bind variable fields in the query string with Database.query", so `:myVariable.field1__c` fails. With `Database.queryWithBinds`, map keys are compared case-insensitively, and duplicate keys that differ only in case throw `QueryException`.

**How to avoid:** Resolve object fields into a local variable first, or use `Database.queryWithBinds(query, bindMap, AccessLevel.USER_MODE)` with unique keys. Allowlist structural parts separately.

```apex
// LIMIT accepts a bind; a field name does not
Integer maxRecords = 100;
List<Account> accts = [SELECT Id FROM Account LIMIT :maxRecords];
```

**Source:** Apex Guide, Dynamic SOQL and Dynamic SOQL Considerations.

---

## Gotcha 8: `stripInaccessible` Returns a New List, Never Filters Records, and Throws on Object Access

**What happens:** Code keeps using the original list and leaks the fields, or expects an empty list for a user who cannot read the object and gets an exception instead.

**When it occurs:** `Security.stripInaccessible` "creates a return list of sObjects that is identical to the source records, except that the fields that are inaccessible to the current user are removed". It does not change record visibility. The `enforceRootObjectCRUD` parameter defaults to true, so a failed object-level check throws. The method does not support `AggregateResult`, and the `Id` field is never stripped.

**How to avoid:** Always continue with `decision.getRecords()`. Use `getRemovedFields()` for logging. Combine with a sharing keyword for record visibility, and catch the exception where object access may be missing.

```apex
SObjectAccessDecision decision = Security.stripInaccessible(AccessType.READABLE, records);
List<Account> safeRecords = (List<Account>) decision.getRecords();
```

**Source:** Apex Guide, Enforce Security with the stripInaccessible Method; Apex Reference, Security Class `stripInaccessible(accessCheckType, sourceRecords, enforceRootObjectCRUD)`.

---

## Gotcha 9: User Mode Does Not Enforce Experience Cloud Personal Information Settings

**What happens:** A site member sees another user's email or phone through an Apex query, even though the query runs in user mode.

**When it occurs:** Orgs with Experience Cloud sites hide personal user fields through site settings. The Apex Guide states these settings "aren't enforced in Apex, even with security features such as the WITH USER_MODE clause or the stripInaccessible method".

**How to avoid:** Filter User fields explicitly in Apex for site-facing code, following the guide's "Comply with a User's Personal Information Visibility Settings" sample. Test with a site member, not an internal user.

**Source:** Apex Guide, Enforce Object and Field Permissions (Considerations).

---

## Gotcha 10: The SOQL Reference and the Apex Guide Disagree About the Default Mode

**What happens:** A reviewer quotes the SOQL Reference line "Apex code runs in system mode by default" to argue that a 67.0 class without `WITH USER_MODE` is insecure, or the reverse.

**When it occurs:** The Version 67.0 SOQL Reference still describes system mode as the Apex default in its `WITH` section, while the Version 67.0 Apex Guide says user mode is the default at 67.0+ and system mode at 66.0 and earlier.

**How to avoid:** Treat the Apex Guide versioned-behavior table as authoritative for the default, keyed by the class's `apiVersion`. Write the access mode explicitly so the code reads the same under either reading.

**Source:** SOQL Reference, SOQL SELECT Syntax and WITH; Apex Guide, Apex Versioned Behavior Changes (Version 67.0).

---

## Gotcha 11: Tests That Skip Validation Hide Injection

**What happens:** Coverage is green, and the injectable branch was never exercised.

**When it occurs:** Code uses `Test.isRunningTest()` to bypass allowlist or bind logic in test context.

**How to avoid:** Never branch security logic on test context. Write a negative test that passes a hostile sort field and asserts the method rejects it.

**Source:** Practice guidance; no fetched guide states it. UNVERIFIED (2026-10-03) as a platform claim.

---

## Gotcha 12: `Security.stripInaccessible` Availability on Old API Versions

**What happens:** A class pinned to a very old `apiVersion` cannot call the method.

**When it occurs:** Legacy code or old scratch definitions. UNVERIFIED (2026-10-03): this skill previously dated the method to Summer '18; the Version 67.0 references do not state the introduction version.

**How to avoid:** Raise the class `apiVersion` before adopting the method. Where that is not possible, check `Schema.DescribeFieldResult.isAccessible()` per field.

**Source:** Apex Reference, Security Class (no version note found).
