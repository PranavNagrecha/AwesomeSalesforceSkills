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

---

## Anti-Pattern 6: A custom class used as a Map key with no equals/hashCode

**What the LLM generates:**
```apex
public class PeriodKey {
    public Id ownerId;
    public String stage;
    public PeriodKey(Id ownerId, String stage) {
        this.ownerId = ownerId;
        this.stage = stage;
    }
}

Map<PeriodKey, Decimal> totals = new Map<PeriodKey, Decimal>();
for (Opportunity o : scope) {
    PeriodKey k = new PeriodKey(o.OwnerId, o.StageName);
    // containsKey is always false: every `new PeriodKey(...)` is a distinct key
    totals.put(k, (totals.containsKey(k) ? totals.get(k) : 0) + o.Amount);
}
```

**Why it happens:** In Java, an assistant that forgets `equals`/`hashCode` gets the same bug — but Java IDEs generate the pair, and most Java training data has them. In Apex the omission is invisible: the code compiles, runs, and returns a map with one entry per input record. "User-defined types are compared by reference, which means that two objects are equal only if they reference the same location in memory" (`apexdev` L2135–L2138).

**Correct pattern:**
```apex
public class PeriodKey {
    public final Id ownerId;
    public final String stage;

    public PeriodKey(Id ownerId, String stage) {
        this.ownerId = ownerId;
        this.stage = stage;
    }

    public Boolean equals(Object obj) {
        if (!(obj instanceof PeriodKey)) { return false; }
        PeriodKey other = (PeriodKey) obj;
        return this.ownerId == other.ownerId && this.stage == other.stage;
    }

    public Integer hashCode() {
        Integer o = (ownerId == null) ? 0 : ownerId.hashCode();
        Integer s = (stage == null) ? 0 : stage.hashCode();
        return (31 * o) ^ s;
    }
}
```

**Detection hint:** `Map<X,` or `Set<X>` where `X` is a class defined in the same source tree. Grep the class body for `Boolean equals(Object` and `Integer hashCode()`; if either is missing, the collection is broken. `scripts/check_apex_collections_patterns.py` raises this as an ERROR.

---

## Anti-Pattern 7: Iterating keySet() while removing from the map

**What the LLM generates:**
```apex
for (Id recordId : recordsById.keySet()) {
    if (recordsById.get(recordId).Amount == null) {
        recordsById.remove(recordId);   // mutating the collection being iterated
    }
}
```

**Why it happens:** The Java idiom for this is `Iterator.remove()`, which Apex does not offer on a `keySet()`, so an assistant falls back to the direct form. It also does not model that "the returned keySet is backed by the map and reflects any changes made to the map, and vice versa" (`apexrefguide` L222249–L222250) — the loop is walking the map itself.

**Correct pattern:**
```apex
List<Id> toRemove = new List<Id>();
for (Id recordId : recordsById.keySet()) {
    if (recordsById.get(recordId).Amount == null) {
        toRemove.add(recordId);
    }
}
for (Id recordId : toRemove) {
    recordsById.remove(recordId);
}
```

**Detection hint:** any `.remove(`, `.put(`, `.add(` or `.clear()` on a collection named in the `for` header — directly, or through its `keySet()`.

---

## Anti-Pattern 8: Sorting with a bare sort() and reading element zero

**What the LLM generates:**
```apex
List<Opportunity> opps = [SELECT Id, Name, Amount, CloseDate FROM Opportunity WHERE AccountId = :accId];
opps.sort();
Opportunity biggest = opps[0];   // not the biggest: not sorted on Amount at all
```

**Why it happens:** `sort()` with no argument reads like "sort sensibly". For sObjects the platform sequence is the sObject type label, then `Name`, then standard fields alphabetically excluding Id and Name, then custom fields alphabetically (`apexdev` L10245–L10258) — so this list is ordered by `Name`, and `opps[0]` is alphabetical, not largest. Nothing throws.

**Correct pattern:** either order in SOQL (`ORDER BY Amount DESC NULLS LAST`) when the query is yours, or pass a `Comparator` — remembering that "Your implementation must explicitly handle null inputs in the compare() method to avoid a null pointer exception" (`apexrefguide` L202283). `references/code-examples.md` §2 is a three-key implementation.

**Detection hint:** `.sort()` with no argument on a `List<SObject>`, followed by an index read or a `[0]`. If a nearby comment names two fields, the intended order is definitely not the default.

---

## Anti-Pattern 9: Set<String> of record Ids from a mixed-width source

**What the LLM generates:**
```apex
Set<String> processedIds = new Set<String>();
for (Map<String, Object> row : payloadRows) {
    processedIds.add((String) row.get('recordId'));   // 15-char from the vendor
}
for (Account a : [SELECT Id FROM Account WHERE ...]) {
    if (processedIds.contains(a.Id)) {                // 18-char from SOQL: never matches
        continue;
    }
}
```

**Why it happens:** An assistant treats `String` as the safe, permissive key type for anything that arrives from JSON. It does not model that `Id` normalizes ("If you set ID to a 15-character value, Apex converts the value to its 18-character representation", `apexdev` L1255) while `String` does not, and that String set elements are case-sensitive (`apexrefguide` L230262–L230263).

**Correct pattern:**
```apex
Set<Id> processedIds = new Set<Id>();
for (Map<String, Object> row : payloadRows) {
    Object raw = row.get('recordId');
    if (raw != null) {
        processedIds.add(Id.valueOf(String.valueOf(raw)));   // normalizes 15 -> 18
    }
}
```

**Detection hint:** a `Set<String>` or `Map<String, ...>` fed from a field named `...Id`, or from `String.valueOf(record.Id)`. `scripts/check_apex_collections_patterns.py` reports this as an ADVISORY.
