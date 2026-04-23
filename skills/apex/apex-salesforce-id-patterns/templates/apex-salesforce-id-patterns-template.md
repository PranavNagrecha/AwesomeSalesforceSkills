# Apex Salesforce Id Patterns — Work Template

Use this template when validating or typing Salesforce Ids at a trust boundary.

## Scope

**Skill:** `apex-salesforce-id-patterns`

**Request summary:** (what Id is being handled, from where, to do what)

## Id Source

- [ ] URL parameter / query string
- [ ] REST or SOAP API request body
- [ ] Aura-enabled / LWC-invoked method
- [ ] CSV / Data Loader input
- [ ] Trigger context (`Trigger.new`, `Trigger.oldMap`)
- [ ] Internal helper call (trusted)
- [ ] Platform Event payload

## Context Gathered

- **Expected sObject(s):** (single? many? polymorphic?)
- **Length variance expected:** (15-char? 18-char? mixed?)
- **Null expected?** (polymorphic lookups, optional fields)
- **Error surface:** (REST statusCode? AuraHandledException? silent skip?)

## Approach

- [ ] Type parameter as `Id` directly (trusted internal)
- [ ] Cast `(Id) str` with `try/catch (System.StringException)` (untrusted)
- [ ] Use `getSobjectType()` to confirm expected type
- [ ] Bulk: group by `Schema.SObjectType` to avoid per-Id SOQL

## Code Sketch

```apex
public static void handle(String rawId, Schema.SObjectType expectedType) {
    if (String.isBlank(rawId)) {
        throw new IllegalArgumentException('Id required');
    }
    Id idValue;
    try {
        idValue = (Id) rawId;
    } catch (System.StringException e) {
        throw new IllegalArgumentException('Malformed Id: ' + rawId);
    }
    if (idValue.getSobjectType() != expectedType) {
        throw new IllegalArgumentException(
            'Expected ' + expectedType + ' but got ' + idValue.getSobjectType());
    }
    // proceed using WITH USER_MODE SOQL on :idValue
}
```

## Checklist

- [ ] No `.startsWith('001')` style prefix routing.
- [ ] No `Schema.getGlobalDescribe()` inside loops.
- [ ] `try/catch` wraps every cast from untrusted string.
- [ ] `Set<Id>` used for bulk membership, not `Set<String>`.
- [ ] Tests cover: empty string, garbage string, wrong-type Id, 15-char and 18-char forms, null.

## Notes

Any edge cases (polymorphic WhoId/WhatId, external-id confusion, managed-package prefix collisions).
