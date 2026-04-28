# Apex Dynamic SOQL Binding Safety — Work Template

Use this template when constructing or refactoring any dynamic SOQL in Apex.

## Scope

**Skill:** `apex-dynamic-soql-binding-safety`

**Request summary:** (fill in what the user asked for — e.g. "build a search service", "audit existing dynamic SOQL", "refactor naive concat into safe form")

## Context Gathered

- Source of each dynamic fragment (UI parameter, REST input, custom metadata, hard-coded):
- Identifier vs value classification of each fragment:
- Required AccessLevel (USER_MODE / SYSTEM_MODE) and justification:
- sObjects and fields referenced (for allowlist construction):
- Failure modes to watch for: empty result vs exception vs over-fetch

## Approach

Pick the matching pattern from `SKILL.md`:

- [ ] **Pattern A — `queryWithBinds` for value-binding**
- [ ] **Pattern B — Field-name allowlist via Schema describe**
- [ ] **Pattern C — ORDER BY direction whitelist + Integer-typed LIMIT**

(Most real implementations need all three together.)

---

## Pattern A — `queryWithBinds` for value-binding

```apex
Map<String, Object> binds = new Map<String, Object>{
    'param1' => value1,
    'param2' => value2
};
List<SObject> rows = Database.queryWithBinds(
    'SELECT Id, Name FROM Account WHERE Name = :param1 AND Industry = :param2 LIMIT :cap',
    binds,
    AccessLevel.USER_MODE
);
```

Verification:
- [ ] Bind map declared as `Map<String, Object>` (not `Map<String, String>`)
- [ ] Every `:token` in the query has a key in the bind map
- [ ] Every map key is referenced in the query
- [ ] `AccessLevel.USER_MODE` unless SYSTEM_MODE is justified in a comment

---

## Pattern B — Field-name allowlist via Schema describe

```apex
private static String safeFieldName(SObjectType sot, String requested) {
    if (requested == null) {
        throw new IllegalArgumentException('Field name required');
    }
    Schema.SObjectField sf = sot.getDescribe().fields.getMap().get(requested.toLowerCase());
    if (sf == null) {
        throw new IllegalArgumentException('Unknown field: ' + requested);
    }
    return sf.getDescribe().getName();
}
```

Verification:
- [ ] Input is lowercased before lookup
- [ ] Returned value is the canonical name from `getDescribe().getName()`, NOT the user input
- [ ] Unknown field throws explicitly (no silent fallback to a default)
- [ ] sObject name (if also dynamic) is allowlisted via `Schema.getGlobalDescribe()`

---

## Pattern C — ORDER BY direction whitelist + Integer-typed LIMIT

```apex
String safeDir = 'DESC'.equalsIgnoreCase(userDir) ? 'DESC' : 'ASC';
Integer cap = (userLimit == null) ? 50 : Math.min(Math.max(userLimit, 1), 200);
String soql = 'SELECT Id FROM Account ORDER BY ' + safeField + ' ' + safeDir +
              ' LIMIT :cap';
Map<String, Object> binds = new Map<String, Object>{ 'cap' => cap };
List<Account> rows = Database.queryWithBinds(soql, binds, AccessLevel.USER_MODE);
```

Verification:
- [ ] Direction collapsed to two literal values via ternary
- [ ] LIMIT and OFFSET are `Integer`, never `String`
- [ ] LIMIT clamped to a sane upper bound (e.g. 200)

---

## Negative-test scaffold

```apex
@IsTest
static void rejectsInjectionPayload() {
    String payload = '\' OR Id != null --';
    Test.startTest();
    Integer rowCount;
    try {
        List<SObject> rows = MyService.search(payload);
        rowCount = rows.size();
    } catch (QueryException qe) {
        rowCount = -1; // throwing is also acceptable
    }
    Test.stopTest();
    System.assert(rowCount == 0 || rowCount == -1,
        'Injection payload must not return extra rows');
}
```

Verification:
- [ ] Test exists for at least one classic payload
- [ ] Assertion accepts either "no rows" or "QueryException"
- [ ] Assertion does NOT accept "all rows in org"

---

## Checklist

- [ ] No `Database.query(...)` call contains `+` concatenation of user-supplied values
- [ ] Every value-shaped fragment uses a bind variable
- [ ] Every identifier-shaped fragment is allowlisted via Schema describe
- [ ] ORDER BY direction is two-value ternary
- [ ] LIMIT/OFFSET are `Integer`
- [ ] `AccessLevel.USER_MODE` (or documented SYSTEM_MODE)
- [ ] Negative-test method exists
- [ ] `python3 scripts/check_apex_dynamic_soql_binding_safety.py --manifest-dir <classes>` passes

## Notes

(Record any deviations from the standard pattern and why — e.g. SYSTEM_MODE rationale, custom allowlist source, performance constraints.)
