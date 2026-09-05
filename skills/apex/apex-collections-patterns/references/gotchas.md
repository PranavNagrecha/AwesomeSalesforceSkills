# Gotchas — Apex Collections Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.
Line citations are to the Summer '26 Apex Developer Guide (`apexdev`) and Apex Reference Guide
(`apexrefguide`) — see `well-architected.md` § Official Sources Used for the PDF locations.

## Gotcha 1: Map.get() returns null — not an exception

**What happens:** `myMap.get(key)` returns `null` when the key does not exist — it does not throw an exception. The reference guide states it plainly: "Returns the value to which the specified key is mapped, or null if the map contains no value for this key" (`apexrefguide` L222556–L222557). Accessing a field or calling a method on the returned null value causes a `NullPointerException` at the call site, not at the `get()` call, making the root cause harder to trace.

**When it occurs:** Any time `Map.get()` is called without a prior `containsKey()` guard and the caller directly uses the result (e.g., `myMap.get(id).Name`).

**How to avoid:** Always guard with `if (myMap.containsKey(key))` before using the value, or null-check the result. For Map<Id, SObject>, a safe pattern is: `SObject record = myMap.get(id); if (record != null) { ... }`. The one-liner is the safe navigation operator, which "short-circuits expressions that attempt to operate on a null value and returns null instead of throwing a NullPointerException" (`apexdev` L2353–L2355): `myMap.get(id)?.Name`.

---

## Gotcha 2: Set.retainAll() mutates the receiver

**What happens:** `setA.retainAll(setB)` modifies `setA` in place, removing any element not present in `setB`. The signature returns a `Boolean` — "true if the original set changed as a result of the call" (`apexrefguide` L230771) — not a new set. If you need the original `setA` after the intersection, it is gone.

**When it occurs:** When building set intersections in trigger handlers or service layers where the original set is reused after the `retainAll()` call (e.g., used in a query, then intersected, but then the original is needed for another branch).

**How to avoid:** If you need both the original set and the intersection, clone first: `Set<Id> intersection = new Set<Id>(setA); intersection.retainAll(setB);`. `CollectionUtils.intersect()` / `subtract()` in `code-examples.md` §1 do this for you and never touch an argument.

---

## Gotcha 3: Building a map from records whose Id is null

**What happens:** `Map<Id, SObject> m = new Map<Id, SObject>(recordList)` and `m.putAll(recordList)` both key records by their `Id` field (`apexrefguide` L222322–L222324). Two documented rules govern what happens when that Id is null: "A map key can hold the null value" (`apexdev` L1694) and "Adding a map entry with a key that matches an existing key in the map overwrites the existing entry with that key with the new entry" (`apexdev` L1695–L1696). Together they mean every unsaved record in the list competes for one null-keyed slot, and only the last one survives — a silent data loss, not an error.

*UNVERIFIED (2026-09-05): the Apex Developer Guide and Reference Guide document the null-key and overwrite rules above, but neither documents what the `Map<ID,sObject>(recordList)` constructor specifically does when a record's Id is null — whether it throws or keys on null. Earlier versions of this skill asserted a `NullPointerException`; that claim is not in either guide. Treat both outcomes as unacceptable and prevent the input.*

**When it occurs:** When building a Map from a list that contains unsaved (in-memory) SObjects with no Id assigned yet — typically records built from an integration payload, or a mix of queried and constructed records.

**How to avoid:** Do not hand a mixed list to the constructor. Build the map explicitly and skip records without an Id, as `CollectionUtils.indexById()` does in `code-examples.md` §1. Apex has no `removeIf` method and no lambda syntax, so the filter is an ordinary loop.

---

## Gotcha 4: Set<SObject> and sObject map keys use field-value equality, not identity

**What happens:** `Set<SObject>` and `Map<SObject, ?>` use field-value equality rather than object identity: "Uniqueness of keys of all other non-primitive types, such as sObject keys, is determined by comparing the objects' field values" (`apexdev` L1700–L1703). The `==` operator behaves the same way — "For sObjects and sObject arrays, `==` performs a deep check of all sObject field values before returning its result" (`apexdev` L2142–L2143). Two independently constructed `SObject` instances with the same field values are therefore one element, and the guide adds a second hazard: "Use caution when you use an sObject as a map key because when the sObject is changed, it no longer maps to the same value" (`apexdev` L1702–L1703).

**When it occurs:** When building a Set to de-duplicate SObject references by identity (e.g., tracking which records have been processed), and two independently constructed SObjects happen to have the same field values — or when a record already in the collection is later mutated.

**How to avoid:** For SObject identity de-duplication, use `Set<Id>` (keying by the record's Id) rather than `Set<SObject>`. If identity is truly needed, wrap the SObject in a custom class with an identity-based `equals()` / `hashCode()` — see `code-examples.md` §3, and `apex/apex-wrapper-class-patterns` for the wrapper design itself.

---

## Gotcha 5: Unbounded accumulation in Database.Stateful batch classes

**What happens:** In a `Database.Stateful` batch class, instance variables persist across execute() calls. Per-transaction governor counters do reset — "For Batch Apex, these limits are reset for each execution of a batch of records in the execute method" (`apexdev` L19530–L19531) — but the retained collection does not shrink with them. Appending records to a member `List<SObject>` in every execute() call accumulates all processed records in heap until the job finishes, eventually hitting the 12 MB asynchronous heap limit (`apexdev` L19577) with a `System.LimitException` that "the runtime throws if a governor limit such as heap" is exceeded (`apexdev` L39724). That exception is uncatchable (`apexdev` L17856), so no `finally` block salvages the run.

**When it occurs:** Batch classes that collect all processed records for a final summary, post-process, or report in the `finish()` method — especially with large data volumes.

**How to avoid:** For aggregation in Stateful batches, accumulate summary data (counts, Ids of failures, small primitives) rather than full SObject records. If you must reference records in `finish()`, re-query from the database there instead of storing them across execute() calls.

---

## Gotcha 6: keySet() is a live view of the map, not a snapshot

**What happens:** "With the keySet() method, the returned keySet is backed by the map and reflects any changes made to the map, and vice versa" (`apexrefguide` L222249–L222250, restated at L222682). So a `Set<Id> keys = myMap.keySet();` handed to another method is not a defensive copy — a `myMap.remove(id)` anywhere afterwards silently shrinks it. Worse, `for (Id k : myMap.keySet()) { myMap.remove(k); }` is precisely the documented "Modifying a collection's elements while iterating through that collection is not supported and causes an error" case (`apexdev` L3182–L3183).

**When it occurs:** Cleanup loops that prune a map in place; helper methods that receive `map.keySet()` and cache it; any code that iterates keys while another branch edits the map.

**How to avoid:** Snapshot before you iterate or hand it out: `Set<Id> keys = new Set<Id>(myMap.keySet());`. To remove entries while walking, "keep the keys you wish to remove in a temporary list, then remove them after you finish iterating the collection" (`apexdev` L3202–L3203). `CollectionUtils.snapshotKeys()` in `code-examples.md` §1 is the one-line version.

---

## Gotcha 7: Set<String> holding record Ids keeps 15- and 18-character forms as two elements

**What happens:** An `Id`-typed value normalizes: "If you set ID to a 15-character value, Apex converts the value to its 18-character representation" (`apexdev` L1255), and `==` on Ids "doesn't distinguish between 15-character and 18-character formats" (`apexdev` L2135–L2136). A `String` does neither. Set and map String elements are additionally case-sensitive: "If the set contains String elements, the elements are case-sensitive. Two set elements that differ only by case are considered distinct" (`apexrefguide` L230262–L230263), and the same is documented for map keys (`apexdev` L1697–L1699). So `Set<String>` fed the 15- and 18-character forms of the same record holds two elements, and `containsKey` against the wrong form misses.

**When it occurs:** Integration payloads, CSV imports and legacy reports commonly carry 15-character Ids while SOQL returns 18. Any code that stores keys as `String` — often to allow a composite or an external key alongside — inherits the split.

**How to avoid:** Type record keys as `Id`, not `String`. When a String key is genuinely required (a composite key, or a mix of Ids and external keys), normalize explicitly: `String.valueOf(Id.valueOf(raw))`. `List.sort()` already handles this case for you — "When you use sort() methods on List<Id>s that contain both 15-character and 18-character IDs, IDs for the same record sort together in API version 35.0 and later" (`apexrefguide` L221840–L221841) — but only for `List<Id>`, not `List<String>`.

---

## Gotcha 8: A custom class used as a key without equals/hashCode makes every instance unique

**What happens:** "Uniqueness of map keys of user-defined types is determined by the equals and hashCode methods, which you provide in your classes" (`apexdev` L1700–L1701). Without both, the default applies: "User-defined types are compared by reference, which means that two objects are equal only if they reference the same location in memory" (`apexdev` L2135–L2138). A roll-up map keyed on a freshly constructed key object therefore grows one entry per iteration and every `containsKey` returns false — the loop compiles, runs, and produces a map the size of the input.

**When it occurs:** Composite-key roll-ups (`Map<PeriodKey, Decimal>`), memoization caches, and de-duplication sets built on a wrapper class.

**How to avoid:** Provide both `public Boolean equals(Object obj)` and `public Integer hashCode()` — the guide gives the exact signatures at `apexdev` L7051–L7066 and a worked `PairNumbers` sample at L7078–L7095. Then make the key fields `final`: "If the object in your map keys or set elements changes after being added to the collection, it won't be found anymore because of changed field values" (`apexdev` L7040–L7041). `scripts/check_apex_collections_patterns.py` raises an ERROR when a class in the scanned tree is used as a key and is missing either method.

---

## Gotcha 9: List.sort() on sObjects uses a field sequence that is rarely the business order

**What happens:** A bare `List<Opportunity>.sort()` does not sort by "the important field". The documented sequence is: the label of the sObject type, then the `Name` field if applicable, then standard fields starting with the first alphabetically excluding Id and Name, then custom fields alphabetically (`apexdev` L10245–L10258). Primitives sort ascending with nulls first (`apexrefguide` L221858–L221872). Code that calls `sort()` and then reads `list[0]` as "the biggest one" is reading whatever `AccountNumber` happened to say.

**When it occurs:** Any "pick the newest / largest / highest-priority record" written as `records.sort(); return records[0];`.

**How to avoid:** Pass a `Comparator` to `List.sort()`, or wrap the record in a class implementing `Comparable` (`apexdev` L1537–L1539, L10335–L10339). The `Comparator` contract carries one non-negotiable obligation: "Your implementation must explicitly handle null inputs in the compare() method to avoid a null pointer exception" (`apexrefguide` L202283–L202284). `code-examples.md` §2 is a three-key implementation with the null branches written out. Avoid `Collator` inside triggers — "locale-sensitive sorting can produce different results depending on the user running the code, avoid using it in triggers or in code that expects a particular sort order" (`apexdev` L7026–L7027).

---

## Gotcha 10: Removing from a list while iterating it, and the cost of removing at all

**What happens:** "Modifying a collection's elements while iterating through that collection is not supported and causes an error. Do not directly add or remove elements while iterating through the collection that includes them" (`apexdev` L3182–L3183). The classic index-based workaround — `for (Integer i = 0; i < items.size(); i++) { items.remove(i); }` — dodges the error and silently skips every other element instead, because the list shifts under the index. Reading past the end raises "ListException: Any problem with a list, such as attempting to access an index that is out of bounds", with the message `List index out of bounds: 1` (`apexdev` L39875–L39889). The guide also warns about the operation itself: "The List.remove method performs linearly. Using it to remove elements has time and resource implications" (`apexdev` L3200).

**When it occurs:** Filtering a list in place inside a trigger handler, especially after a validation pass marks some records for exclusion.

**How to avoid:** "To remove elements while iterating a list, create a new list, then copy the elements you wish to keep" (`apexdev` L3197–L3198) — which is what `CollectionUtils.partition()` returns in one pass. For adding, "keep the new elements in a temporary list, set, or map and add them to the original after you finish iterating" (`apexdev` L3192–L3193).

---

## Gotcha 11: Decimal keys that are numerically equal can hash differently

**What happens:** "Two Decimal objects that are numerically equivalent but differ in scale (such as 1.1 and 1.10) generally don't have the same hashcode. Use caution when such Decimal objects are used in Sets or as Map keys" (`apexdev` L1245–L1247). A `Map<Decimal, X>` keyed on an amount or a rate can therefore hold two entries for what a human reads as one value, and `containsKey(1.10)` can miss an entry stored under `1.1`.

**When it occurs:** Pricing and rate lookups keyed on a currency or percent field, where one side comes from a SOQL result (scale set by the field definition) and the other from an Apex literal or a parsed string.

**How to avoid:** Do not key on `Decimal`. Normalize to a fixed scale and key on the resulting `String`, or key on the record Id and carry the Decimal as the value. If a numeric key is unavoidable, call `setScale()` on both the stored key and every lookup argument.

---

## Gotcha 12: queryWithBinds map keys are case-insensitive, unlike every other map

**What happens:** Map keys of type String are case-sensitive everywhere in Apex (`apexdev` L1697–L1699) — except in the bind map handed to `Database.queryWithBinds`. "Although map keys of type String are case-sensitive, the queryWithBinds method doesn't support Map keys that differ only in case. In a queryWithBinds method, comparison of Map keys is case-insensitive. If duplicate Map keys exist, the method throws a runtime QueryException" — the example message is `System.QueryException: The bindMap consists of duplicate case-insensitive keys: [Acctname, acctName]` (`apexdev` L11478–L11488).

**When it occurs:** Dynamic SOQL built from a bind map assembled in more than one place, where two contributors use different casing for the same logical parameter. The map itself accepts both keys without complaint; the query call is where it fails, at runtime.

**How to avoid:** Normalize bind keys to one casing when the map is built, not when it is used. Map keys must also "start with an ASCII letter, can't start with a number, must not use reserved keywords, and must adhere to variable naming requirements" (`apexdev` L11493–L11495), so a key derived from a field label needs sanitizing first.

---

## Gotcha 13: Set and Map iteration order is deterministic — but it is not insertion order

**What happens:** Two facts are easy to conflate. The guide guarantees repeatability: "The iteration order of set elements is deterministic, so you can rely on the order being the same in each subsequent execution of the same code" (`apexdev` L1642–L1643), and the same for maps (`apexdev` L1692–L1693), with `values()` carrying the guarantee too (`apexrefguide` L222913–L222915). What it does *not* guarantee is that the order matches the order you added things, and it explicitly forbids positional access: "A set is an unordered collection—you can't access a set element at a specific index. You can only iterate over set elements" (`apexdev` L1641). The map advice is blunter still: "we recommend to always access map elements by key" (`apexdev` L1693).

**When it occurs:** `new Set<String>(orderedList)` used to de-duplicate, then iterated on the assumption that the original order survived — typically when building a display string, a CSV column order, or an ordered batch of callouts.

**How to avoid:** If order matters, keep a `List` for order and a `Set` for membership, and iterate the List. A test that asserts a specific set-iteration order will pass locally and is asserting an implementation detail; assert the *contents* of the set and the order of the List instead. `CollectionUtilsTest` in `code-examples.md` §4 follows this split — it asserts sizes and membership for sets, and index-by-index order only after an explicit `sort(new Comparator())`.
