---
name: apex-dynamic-soql-binding-safety
description: "Safe construction of dynamic SOQL — Database.query bind variables (:varName, API 60+ semantics), Database.queryWithBinds(query, Map<String,Object>, AccessLevel) (API 55+), field-name allowlisting, ORDER BY direction whitelist, LIMIT/OFFSET typing, and the interaction with WITH USER_MODE / WITH SECURITY_ENFORCED. NOT for static SOQL — see apex-soql-fundamentals. NOT for FLS enforcement on results — see soql-security or apex-stripinaccessible-and-fls-enforcement."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
triggers:
  - "how to safely concatenate user input into dynamic soql"
  - "database.query bind variable colon prefix not in scope error"
  - "database.querywithbinds map string object accesslevel example"
  - "soql injection apex string.escapesinglequotes is it enough"
  - "dynamic field list reporting tool whitelist field names apex"
  - "with user_mode dynamic soql fls runtime enforcement"
tags:
  - apex
  - soql
  - injection
  - dynamic
  - binding
  - security
inputs:
  - User-supplied filter values, field names, sort columns, or limits
  - The dynamic SOQL string being built
  - Required AccessLevel (USER_MODE vs SYSTEM_MODE) and FLS posture
  - Schema of the queried sObject (for field-name allowlisting)
outputs:
  - Database.queryWithBinds call site with explicit bind map
  - Field-name and ORDER BY direction allowlists
  - SOQL-injection negative tests asserting safe behavior on attack payloads
  - Documented USER_MODE / SYSTEM_MODE choice with justification
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Apex Dynamic SOQL Binding Safety

Activate when ANY part of a SOQL query string is built at runtime from variables — filter values, field names, sort columns, limits, or the WHERE clause itself. Dynamic SOQL is necessary for reporting tools, configurable list views, and search; it is also the single most common SOQL-injection vector in Apex. This skill establishes the safe construction pattern for every value, identifier, and clause that flows into `Database.query` or `Database.queryWithBinds`.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Where does each fragment of the query string come from?** Trace every concatenation back to its source — Visualforce parameter, LWC `@AuraEnabled` argument, REST request, custom metadata, or hard-coded literal. Hard-coded literals are safe; everything else needs binding or allowlisting.
- **Is the dynamic part a value or an identifier?** Bind variables protect VALUES. They do NOT protect field names, sObject names, ORDER BY columns, ASC/DESC direction, or LIMIT keywords — those require allowlisting.
- **What AccessLevel is correct?** `AccessLevel.USER_MODE` enforces FLS and object permissions at runtime; `AccessLevel.SYSTEM_MODE` bypasses them. Default to USER_MODE; document any SYSTEM_MODE call.
- **Common wrong assumption:** "I called `String.escapeSingleQuotes` so I'm safe." Escaping single quotes prevents quote-breakout on string literals, but does nothing for field-name injection, ORDER BY injection, or LIMIT injection.

---

## Core Concepts

### Why string concatenation is SOQL injection

Consider:

```apex
String name = ApexPages.currentPage().getParameters().get('name');
String soql = 'SELECT Id, Name FROM Account WHERE Name = \'' + name + '\'';
List<Account> accs = Database.query(soql);
```

If a user supplies `name = ' OR Id != null --`, the resulting query becomes `SELECT Id, Name FROM Account WHERE Name = '' OR Id != null --'`. Every Account in the org is returned, FLS-aware or not. The `--` swallows the trailing quote so the parser is happy. Variants exist for sub-selects, UNION-style trickery via semi-joins, and ORDER BY exfiltration.

`String.escapeSingleQuotes(input)` defangs the quote-breakout vector but provides ZERO protection if the attacker controls a field name, ORDER BY column, or LIMIT integer represented as a string. It is necessary but not sufficient.

### Bind variables in `Database.query`

When the query string contains a colon-prefixed token like `:accountName`, `Database.query(soql)` resolves it against the local scope of the call site. The platform parameterizes the value — the user input never participates in SOQL parsing. Caveats:

- The variable MUST be in lexical scope at the `Database.query(...)` call. A variable defined in the calling class but not in the executing method will throw `System.QueryException: Variable does not exist`.
- `IN :collection` requires `collection` to be a `List` or `Set`.
- Works for primitives, sObjects, IDs, and collections of those.

### `Database.queryWithBinds` (API 55+) — the modern explicit-bind variant

```apex
Map<String, Object> binds = new Map<String, Object>{
    'searchName' => '%' + sanitizedTerm + '%',
    'minAmount'  => userMinAmount
};
List<Opportunity> opps = Database.queryWithBinds(
    'SELECT Id, Name, Amount FROM Opportunity ' +
    'WHERE Name LIKE :searchName AND Amount >= :minAmount',
    binds,
    AccessLevel.USER_MODE
);
```

Use `queryWithBinds` whenever a query is constructed across methods or service layers — bind values travel as a map, not a hidden lexical-scope contract. Always pair with `AccessLevel.USER_MODE` unless SYSTEM_MODE is documented.

### Allowlisting field names, sObject names, and clauses

Bind variables cannot bind identifiers. For fields:

```apex
Map<String, Schema.SObjectField> fieldMap =
    Schema.SObjectType.Account.fields.getMap();
String requested = userInput.toLowerCase();
if (!fieldMap.containsKey(requested)) {
    throw new IllegalArgumentException('Unknown field: ' + userInput);
}
String fieldName = fieldMap.get(requested).getDescribe().getName();
```

Use the canonical name returned by `getDescribe().getName()` (not the raw user input) when concatenating into the query. Apply analogous patterns for sObject names (`Schema.getGlobalDescribe()`).

For ORDER BY direction, hard-code an allowlist:

```apex
String dir = ('DESC'.equalsIgnoreCase(userDir)) ? 'DESC' : 'ASC';
```

For LIMIT and OFFSET, parse to `Integer` first; never let a String reach the query. Apex `Integer.valueOf` throws on non-numeric input — that is the desired failure mode.

### Dynamic SOQL with `WITH USER_MODE` / `WITH SECURITY_ENFORCED`

Both clauses are valid INSIDE a dynamic query string. `WITH USER_MODE` (API 58+) is preferred and is enforced at parse time on the field list. `WITH SECURITY_ENFORCED` is the older equivalent. They protect what the query CAN ASK FOR; they do not protect HOW the query is built. A dynamic query with `WITH USER_MODE` is still injectable if you concatenate user input into the WHERE clause — `WITH USER_MODE` just stops the attacker from selecting fields they cannot see.

Prefer `Database.queryWithBinds(..., AccessLevel.USER_MODE)` over an in-string `WITH USER_MODE`; the AccessLevel argument does the same job and stays out of the parsed string.

---

## Common Patterns

### Pattern: `queryWithBinds` for user-supplied values

**When to use:** Any time the WHERE clause contains a value derived from user input.

**How it works:**

```apex
public List<Contact> searchContacts(String term, Integer maxRows) {
    Map<String, Object> binds = new Map<String, Object>{
        'term' => '%' + String.escapeSingleQuotes(term) + '%',
        'cap'  => Math.min(maxRows, 200)
    };
    return Database.queryWithBinds(
        'SELECT Id, Name FROM Contact WHERE Name LIKE :term LIMIT :cap',
        binds,
        AccessLevel.USER_MODE
    );
}
```

`String.escapeSingleQuotes` here is defense-in-depth; the bind itself prevents injection.

**Why not the alternative:** Inline concatenation of `term` into the query string is injectable. `Database.query(soql)` would also work, but `queryWithBinds` makes the bind contract explicit and survives refactoring.

### Pattern: Field-name allowlist for dynamic field lists

**When to use:** Reporting tool, list view, or export where the user picks which columns appear.

**How it works:**

```apex
public List<SObject> runReport(String objectApi, List<String> requestedFields) {
    Schema.SObjectType sot = Schema.getGlobalDescribe().get(objectApi);
    if (sot == null) throw new IllegalArgumentException('Unknown object');
    Map<String, Schema.SObjectField> fmap = sot.getDescribe().fields.getMap();

    List<String> safeFields = new List<String>();
    for (String f : requestedFields) {
        Schema.SObjectField sf = fmap.get(f.toLowerCase());
        if (sf == null) throw new IllegalArgumentException('Unknown field: ' + f);
        safeFields.add(sf.getDescribe().getName());
    }

    String soql = 'SELECT ' + String.join(safeFields, ', ') +
                  ' FROM ' + sot.getDescribe().getName() +
                  ' WITH USER_MODE LIMIT 200';
    return Database.queryWithBinds(soql, new Map<String, Object>(), AccessLevel.USER_MODE);
}
```

**Why not the alternative:** Concatenating `requestedFields` directly lets an attacker inject `Id), (SELECT Username FROM User` or similar. The lookup-then-canonical-name pattern guarantees only real, current fields reach the parser.

### Pattern: ORDER BY direction whitelist

**When to use:** Sortable list views or table headers backed by Apex.

**How it works:**

```apex
String safeField = canonicalFieldName(sortField);   // allowlist as above
String dir = 'DESC'.equalsIgnoreCase(sortDir) ? 'DESC' : 'ASC';
String soql = 'SELECT Id, Name FROM Account ORDER BY ' + safeField + ' ' + dir +
              ' LIMIT :pageSize';
Map<String, Object> binds = new Map<String, Object>{ 'pageSize' => pageSize };
return Database.queryWithBinds(soql, binds, AccessLevel.USER_MODE);
```

**Why not the alternative:** A user-supplied direction string can carry `, (SELECT ...)` or `NULLS FIRST OFFSET 9999`. Two-value choice removes the entire class.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| User-supplied filter value | `Database.queryWithBinds` + bind map | Parameterizes value; explicit AccessLevel |
| Single-method dynamic query, value only | `Database.query` with `:localVar` | Simplest; bind in lexical scope |
| User-supplied field or object name | Schema describe lookup + canonical name | Bind variables cannot bind identifiers |
| User-supplied sort direction | Two-value `ASC`/`DESC` ternary | Allowlist of two; nothing else can sneak in |
| User-supplied LIMIT/OFFSET | Parse to `Integer` then bind | Type system rejects non-numeric input |
| Need FLS at runtime on dynamic query | `AccessLevel.USER_MODE` on `queryWithBinds` | Single-knob enforcement, cleaner than `WITH USER_MODE` in string |
| Background job that legitimately needs SYSTEM_MODE | `AccessLevel.SYSTEM_MODE` + comment block explaining why | Documented exception, reviewable |

---

## Recommended Workflow

1. **Inventory every variable** that flows into the query string. Mark each as VALUE or IDENTIFIER.
2. **Bind every VALUE** via `Database.queryWithBinds` (preferred) or `Database.query` with `:varName`. Never concatenate a value.
3. **Allowlist every IDENTIFIER** — field names via `Schema.SObjectType.X.fields.getMap()` (lowercase the input, use the canonical name from `getDescribe().getName()`); sObject names via `Schema.getGlobalDescribe()`; ORDER BY direction via two-value ternary; LIMIT/OFFSET via `Integer` parsing.
4. **Choose AccessLevel deliberately** — default `USER_MODE`; document `SYSTEM_MODE` with a justification comment.
5. **Write a SOQL-injection negative test** — feed `' OR Id != null --` and `; DELETE FROM Account` style payloads; assert the call returns expected rows or throws `QueryException`, never extra rows.
6. **Run the skill checker** — `python3 skills/apex/apex-dynamic-soql-binding-safety/scripts/check_apex_dynamic_soql_binding_safety.py --manifest-dir path/to/classes`.
7. **Code review pass** — verify no `Database.query('... ' + ` patterns escaped the audit, especially ones hidden behind helper methods.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] No string concatenation of user input inside any `Database.query(...)` call
- [ ] Every value-shaped fragment uses a bind variable (`:name` or bind map)
- [ ] Every identifier-shaped fragment is allowlisted via `Schema` describe
- [ ] ORDER BY direction is the result of a two-value ternary
- [ ] LIMIT and OFFSET are typed `Integer`, not `String`
- [ ] `AccessLevel.USER_MODE` used unless SYSTEM_MODE is explicitly justified in a comment
- [ ] Negative test exists for at least one classic SOQL-injection payload
- [ ] `String.escapeSingleQuotes` is treated as defense-in-depth, never the sole control

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`Database.query` bind scope is lexical, not class-wide.** `:term` resolves against the executing method's local variables, not a class field with the same name in some cases — and definitely not a variable in the caller. Refactoring a query into a helper method routinely produces `Variable does not exist` at runtime. Use `Database.queryWithBinds` to pass binds explicitly.
2. **`Database.queryWithBinds` requires `Map<String, Object>`.** A `Map<String, String>` will compile but throw at runtime when the platform tries to bind a non-string value (Integer for LIMIT, List for IN). Always declare the map as `Map<String, Object>`.
3. **`AccessLevel.SYSTEM_MODE` silently bypasses FLS and CRUD.** It is the right choice for some background jobs but is a security regression in user-facing controllers. Default to `USER_MODE`; require a code comment for any `SYSTEM_MODE` call site.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `queryWithBinds` call site | The canonical safe call: query string + bind map + AccessLevel |
| Field-name allowlist helper | Method that maps user input → canonical field name via Schema |
| ORDER BY direction whitelist | Two-value ternary collapsed to `ASC`/`DESC` |
| Injection negative test | Test method asserting attack payloads return expected rows or throw |

---

## Related Skills

- `apex/apex-soql-fundamentals` — static SOQL, when dynamic SOQL is unnecessary
- `apex/apex-stripinaccessible-and-fls-enforcement` — post-query FLS scrubbing for results
- `apex/apex-soql-injection-prevention` — broader injection threat model
- `security/soql-security` — security-pillar guidance for SOQL access control
