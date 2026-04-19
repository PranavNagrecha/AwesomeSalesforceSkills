# LLM Anti-Patterns — Apex Collections Patterns

Common mistakes AI coding assistants make when generating or advising on Apex collection usage.

## Anti-Pattern 1: Using Map.get() without containsKey guard

**What the LLM generates:**
```apex
Map<Id, Account> accountMap = new Map<Id, Account>([SELECT Id, Name FROM Account]);
String name = accountMap.get(contact.AccountId).Name; // NPE if key missing
```

**Why it happens:** LLMs mirror Java / Python patterns where map access typically throws a meaningful exception or the map is assumed to be fully populated. In Apex, `Map.get()` silently returns null for missing keys.

**Correct pattern:**
```apex
if (accountMap.containsKey(contact.AccountId)) {
    String name = accountMap.get(contact.AccountId).Name;
}
```

**Detection hint:** Look for `map.get(key).field` or `map.get(key).method()` patterns without a preceding `containsKey` guard or null check on the result.

---

## Anti-Pattern 2: Calling retainAll without cloning when original set is needed later

**What the LLM generates:**
```apex
Set<Id> activeIds = getActiveIds();
Set<Id> processedIds = getProcessedIds();
activeIds.retainAll(processedIds); // mutates activeIds
// BUG: activeIds no longer contains original active Ids
doSomethingWithActiveIds(activeIds); // wrong set passed
```

**Why it happens:** LLMs treat `retainAll()` as a non-destructive "filter" operation, not realizing it mutates the receiver in place (matching Java's `Set.retainAll` semantics but the mutation surprise is common).

**Correct pattern:**
```apex
Set<Id> intersection = new Set<Id>(activeIds); // clone first
intersection.retainAll(processedIds);
doSomethingWithActiveIds(activeIds);    // original preserved
doSomethingWithIntersection(intersection);
```

**Detection hint:** `retainAll()` called on a Set variable that is also referenced after the call.

---

## Anti-Pattern 3: Building Map from list containing null-Id records

**What the LLM generates:**
```apex
List<Contact> contacts = buildContactsWithSomeNew(records);
Map<Id, Contact> contactMap = new Map<Id, Contact>(contacts);
// NullPointerException if any contact has null Id
```

**Why it happens:** LLMs generate the Map constructor pattern correctly for persisted records but don't check whether the list might contain unsaved SObjects with null Ids.

**Correct pattern:**
```apex
Map<Id, Contact> contactMap = new Map<Id, Contact>();
for (Contact c : contacts) {
    if (c.Id != null) {
        contactMap.put(c.Id, c);
    }
}
```

**Detection hint:** `new Map<Id, SObject>(list)` where `list` may contain records that have not been inserted yet (e.g., built from external data without prior DML).

---

## Anti-Pattern 4: Accumulating SObject records in Database.Stateful batch

**What the LLM generates:**
```apex
global class MyBatch implements Database.Batchable<SObject>, Database.Stateful {
    private List<Account> allProcessed = new List<Account>();

    global void execute(Database.BatchableContext bc, List<Account> scope) {
        // process...
        allProcessed.addAll(scope); // unbounded heap accumulation
    }

    global void finish(Database.BatchableContext bc) {
        sendSummaryEmail(allProcessed); // 12 MB heap limit hit at scale
    }
}
```

**Why it happens:** LLMs generate the "collect everything, summarize in finish()" pattern because it avoids a re-query. The heap implication at scale (thousands of records × field count) is not modeled.

**Correct pattern:**
```apex
private List<Id> processedIds = new List<Id>(); // accumulate Ids, not full records

global void execute(Database.BatchableContext bc, List<Account> scope) {
    for (Account a : scope) {
        processedIds.add(a.Id);
    }
}

global void finish(Database.BatchableContext bc) {
    // Re-query only what finish() needs
    List<Account> forSummary = [SELECT Id, Name FROM Account WHERE Id IN :processedIds];
    sendSummaryEmail(forSummary);
}
```

**Detection hint:** `addAll(scope)` or `add(record)` inside a Stateful batch's `execute()` adding full SObjects to a member list.

---

## Anti-Pattern 5: Nested loops instead of Map-based lookup

**What the LLM generates:**
```apex
for (Contact c : contacts) {
    for (Account a : accounts) {
        if (a.Id == c.AccountId) {
            c.Description = a.Industry; // O(n×m)
        }
    }
}
```

**Why it happens:** LLMs default to the nested loop "find matching record" pattern from general programming. In Apex bulk contexts this is O(n×m) and fails with CPU timeout on large data volumes.

**Correct pattern:**
```apex
Map<Id, Account> accountMap = new Map<Id, Account>(accounts);
for (Contact c : contacts) {
    if (accountMap.containsKey(c.AccountId)) {
        c.Description = accountMap.get(c.AccountId).Industry; // O(1)
    }
}
```

**Detection hint:** Two nested `for` loops where the inner loop searches for a matching record by Id. Always replace with a Map built from the inner list and O(1) lookup.
