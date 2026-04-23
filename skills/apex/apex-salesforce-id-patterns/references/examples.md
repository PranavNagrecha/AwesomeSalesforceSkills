# Examples — Apex Salesforce Id Patterns

## Example 1: Routing An Id To The Right Handler

**Context:** A webhook hits an Apex REST endpoint with a `recordId` that could be an Account, Contact, or Case — the external system doesn't tag which.

**Problem:** A naive implementation hardcodes prefix strings (`startsWith('001')`) which breaks when a new object enters scope and requires re-deploys.

**Solution:**

```apex
@RestResource(urlMapping='/webhook/*')
global with sharing class WebhookController {
    @HttpPost
    global static void handle(String recordId) {
        Id rid;
        try { rid = Id.valueOf(recordId); }
        catch (System.StringException e) {
            RestContext.response.statusCode = 400;
            RestContext.response.responseBody = Blob.valueOf('Invalid Id format');
            return;
        }
        Schema.SObjectType t = rid.getSobjectType();
        if (t == Account.SObjectType)        AccountHandler.handle(rid);
        else if (t == Contact.SObjectType)   ContactHandler.handle(rid);
        else if (t == Case.SObjectType)      CaseHandler.handle(rid);
        else {
            RestContext.response.statusCode = 422;
            RestContext.response.responseBody = Blob.valueOf('Unsupported object: ' + t);
        }
    }
}
```

**Why it works:** `Id.valueOf` enforces format and type legitimacy up front, and `getSobjectType()` returns a `Schema.SObjectType` that can be compared directly to the token. No string prefix compare, no hardcoded `a0*` custom prefixes, no false routes.

---

## Example 2: Bulkified Heterogeneous Id Lookup

**Context:** A UI sends a batch of `Id`s that may be mixed sObject types. The Apex method must fetch each record for display.

**Problem:** The naive pattern issues one SOQL per Id, blowing the 100-query limit with only 101 records.

**Solution:**

```apex
public static List<SObject> fetchMany(List<Id> ids) {
    Map<Schema.SObjectType, List<Id>> byType = new Map<Schema.SObjectType, List<Id>>();
    for (Id i : ids) {
        Schema.SObjectType t = i.getSobjectType();
        if (!byType.containsKey(t)) byType.put(t, new List<Id>());
        byType.get(t).add(i);
    }

    List<SObject> out = new List<SObject>();
    for (Schema.SObjectType t : byType.keySet()) {
        String objName = t.getDescribe().getName();
        String q = 'SELECT Id, Name FROM ' + objName +
                   ' WHERE Id IN :ids WITH USER_MODE';
        List<Id> ids2 = byType.get(t);
        out.addAll(Database.query(q.replace(':ids', ':ids2')));
        // Use named binds in real code; this is illustrative.
    }
    return out;
}
```

**Why it works:** Grouping by `SObjectType` converts an O(N) SOQL pattern into O(distinct-types) — typically 2-4 queries regardless of input size.

---

## Example 3: Normalizing 15-Char Ids From A CSV

**Context:** An admin is loading a CSV of Lead Ids exported from a report (15-char) and matching them to existing records queried via SOQL (18-char). String compare fails silently.

**Problem:** A Set<String> of 15-char values will not contain 18-char values even when they point to the same record.

**Solution:**

```apex
public static Set<Id> normalizeIds(List<String> rawIds) {
    Set<Id> out = new Set<Id>();
    for (String r : rawIds) {
        if (String.isBlank(r)) continue;
        try { out.add((Id) r); }
        catch (System.StringException e) {
            // log or collect — do not silently drop in production
        }
    }
    return out;
}
```

**Why it works:** Casting to `Id` normalizes to 18 chars and the `Set<Id>` comparator is case-insensitive-safe. The `try/catch` keeps bad rows from blowing up the whole batch.

---

## Anti-Pattern: Hardcoding A Custom Object Prefix

**What practitioners do:**

```apex
if (someString.startsWith('a03')) {
    // treat as MyCustomObject__c
}
```

**What goes wrong:** Custom object prefixes are assigned at creation time and are **org-specific**. The sandbox where you developed may have `a03` for `MyCustomObject__c`, but production may have assigned it to a different object. The hardcoded compare silently misroutes in prod.

**Correct approach:** Use `Schema.getGlobalDescribe().get('MyCustomObject__c').getDescribe().getKeyPrefix()` or, better, type the value as `Id` and compare `getSobjectType() == MyCustomObject__c.SObjectType`.

---

## Anti-Pattern: Comparing 15-Char And 18-Char Strings

**What practitioners do:**

```apex
Set<String> known = new Set<String>{ '001A000000abcde' }; // 15-char
Account a = [SELECT Id FROM Account LIMIT 1]; // Id is 18-char
if (!known.contains(a.Id)) {
    // always enters here — the Set holds the 15-char version
}
```

**What goes wrong:** `Set<String>.contains` is case-sensitive and length-sensitive — `001A000000abcde` does not equal `001A000000abcdeAAA`. Records appear "not found" when they actually exist.

**Correct approach:** Either (a) cast the input side to `Id` to normalize to 18-char, or (b) use `Set<Id>` which handles case-insensitive compare automatically.
