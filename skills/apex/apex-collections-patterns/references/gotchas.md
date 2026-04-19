# Gotchas — Apex Collections Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Map.get() returns null — not an exception

**What happens:** `myMap.get(key)` returns `null` when the key does not exist — it does not throw an exception. Accessing a field or calling a method on the returned null value causes a `NullPointerException` at the call site, not at the `get()` call, making the root cause harder to trace.

**When it occurs:** Any time `Map.get()` is called without a prior `containsKey()` guard and the caller directly uses the result (e.g., `myMap.get(id).Name`).

**How to avoid:** Always guard with `if (myMap.containsKey(key))` before using the value, or null-check the result. For Map<Id, SObject>, a safe pattern is: `SObject record = myMap.get(id); if (record != null) { ... }`.

---

## Gotcha 2: Set.retainAll() mutates the receiver

**What happens:** `setA.retainAll(setB)` modifies `setA` in place, removing any element not present in `setB`. If you need the original `setA` after the intersection, it is gone.

**When it occurs:** When building set intersections in trigger handlers or service layers where the original set is reused after the `retainAll()` call (e.g., used in a query, then intersected, but then the original is needed for another branch).

**How to avoid:** If you need both the original set and the intersection, clone first: `Set<Id> intersection = new Set<Id>(setA); intersection.retainAll(setB);`.

---

## Gotcha 3: putAll(List<SObject>) keys by Id — null Id throws NullPointerException

**What happens:** `Map<Id, SObject> m = new Map<Id, SObject>(recordList)` and `m.putAll(recordList)` both key records by their `Id` field. If any record in the list has a null `Id` (e.g., a newly constructed SObject not yet inserted), the call throws `NullPointerException`.

**When it occurs:** When building a Map from a list that contains unsaved (in-memory) SObjects with no Id assigned yet.

**How to avoid:** Ensure all records have an `Id` before calling `putAll`. If the list contains a mix of saved and unsaved records, filter first: `recordList.removeIf(r -> r.Id == null)` (or use a loop to build the map only for records with non-null Id).

---

## Gotcha 4: Set<SObject> uses deep equality, not identity

**What happens:** `Set<SObject>` and `Map<SObject, ?>` use deep equality (comparing all field values) rather than object identity. Two different `SObject` instances with the same field values are treated as the same element.

**When it occurs:** When building a Set to de-duplicate SObject references by identity (e.g., tracking which wrapper objects have been processed), and two independently constructed SObjects happen to have the same field values.

**How to avoid:** For SObject identity de-duplication, use `Set<Id>` (keying by the record's Id) rather than `Set<SObject>`. If identity is truly needed, wrap the SObject in a custom class with an identity-based `equals()` / `hashCode()`.

---

## Gotcha 5: Unbounded accumulation in Database.Stateful batch classes

**What happens:** In a `Database.Stateful` batch class, instance variables persist across execute() calls. Appending records to a member `List<SObject>` in every execute() call accumulates all processed records in heap until the job finishes, eventually hitting the 12 MB async heap limit with a fatal `LimitException`.

**When it occurs:** Batch classes that collect all processed records for a final summary, post-process, or report in the `finish()` method — especially with large data volumes.

**How to avoid:** For aggregation in Stateful batches, accumulate summary data (counts, Ids of failures, small primitives) rather than full SObject records. If you must reference records in `finish()`, re-query from the database there instead of storing them across execute() calls.
