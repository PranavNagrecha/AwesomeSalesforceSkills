# Code Examples — Apex Collections Patterns

A deployable `CollectionUtils` class, a multi-key `Comparator`, a custom Map-key
class with `equals`/`hashCode`, and the test class that pins the semantics the
rest of this skill claims. Deploy §1–§4 together; §5–§7 are the metadata and the
verification run.

The canonical repo scaffolds are referenced by path rather than re-inventing them:

| Need | Canonical file | Why not rewrite it |
|---|---|---|
| Trigger entry point that calls these helpers | `templates/apex/TriggerHandler.cls` | Handler dispatch and recursion control already live there |
| Query layer that hands you the `List<SObject>` to index | `templates/apex/BaseSelector.cls` | `public abstract inherited sharing class BaseSelector` — the sharing decision is already made |
| Domain layer that consumes the grouped map | `templates/apex/BaseDomain.cls` | Keeps grouping in the utility and rules in the domain |
| Bulk test data | `templates/apex/tests/TestDataFactory.cls` | `createAccounts(count, overrides)` returns records **uninserted**; callers insert |
| 200-record bulk shape | `templates/apex/tests/BulkTestPattern.cls` | The repo's canonical bulk case |

---

## 0. Which container, by access pattern

| You need to… | Container | Grounded reason |
|---|---|---|
| Preserve order and address by position | `List<T>` | "A list is an ordered collection of elements that are distinguished by their indices" (`apexdev` L1452–1454); index 0 is first (L1466) |
| Test membership and de-duplicate | `Set<T>` | "Apex uses a hash structure for all sets" (`apexdev` L1640); a set "does not contain any duplicates" (L1592) |
| Look up one record by a key | `Map<K,V>` | "Apex uses a hash structure for all maps" (`apexdev` L1691) |
| Group many children under one parent | `Map<Id, List<SObject>>` | Map values "can be any data type—primitive types, collections, sObjects…" (`apexdev` L1646–1648) |
| Group on two dimensions | `Map<CustomKey, V>` with `equals`/`hashCode` | "Uniqueness of map keys of user-defined types is determined by the equals and hashCode methods" (`apexdev` L1700) |

Neither the number of items nor the nesting depth is the binding constraint in
practice: "There is no limit on the number of items a collection can hold.
However, there is a general limit on heap size" (`apexdev` L1431), and a list,
set or map key may nest "up to seven levels of nested collections … up to eight
levels overall" (`apexdev` L1471, L1601, L1657). The binding constraint is heap:
6 MB synchronous, 12 MB asynchronous (`apexdev` L19577).

---

## 1. `CollectionUtils.cls` — typed grouping, indexing, partitioning

```apex
/**
 * CollectionUtils — grouping, indexing and partitioning helpers for Apex
 * collections. Every method is bulk-safe: no SOQL, no DML, one pass per call.
 *
 * Deliberate design decisions, each traceable to a documented platform rule:
 *  - indexById() SKIPS records whose Id is null rather than keying them. A map
 *    key may legally hold null (apexdev L1694) and "Adding a map entry with a
 *    key that matches an existing key ... overwrites the existing entry"
 *    (apexdev L1695), so a list of unsaved records would collapse into one
 *    null-keyed entry and silently lose rows.
 *  - snapshotKeys() copies. "the returned keySet is backed by the map and
 *    reflects any changes made to the map, and vice versa" (apexrefguide
 *    L222249) — the keySet is a view, not a copy.
 *  - No method mutates an argument. Set.retainAll "Retains only the elements in
 *    this set" and returns whether the receiver changed (apexrefguide
 *    L230750-L230751, L230771): it is destructive.
 */
public inherited sharing class CollectionUtils {

    public class CollectionException extends Exception {}

    /**
     * Group records by the value of one field.
     * Records whose key value is null land under the null key, which is legal
     * (apexdev L1694). Call groupByLookup() when you want them dropped instead.
     */
    public static Map<Object, List<SObject>> groupBy(
        List<SObject> records,
        Schema.SObjectField field
    ) {
        Map<Object, List<SObject>> grouped = new Map<Object, List<SObject>>();
        if (records == null || field == null) {
            return grouped;
        }
        for (SObject record : records) {
            Object key = record.get(field);
            List<SObject> bucket = grouped.get(key);
            if (bucket == null) {
                bucket = new List<SObject>();
                grouped.put(key, bucket);
            }
            bucket.add(record);
        }
        return grouped;
    }

    /**
     * Group child records by a lookup/master-detail field, dropping children
     * whose lookup is null. This is the Map<Id, List<Child>> that a bulkified
     * trigger handler wants.
     */
    public static Map<Id, List<SObject>> groupByLookup(
        List<SObject> records,
        Schema.SObjectField lookupField
    ) {
        Map<Id, List<SObject>> grouped = new Map<Id, List<SObject>>();
        if (records == null || lookupField == null) {
            return grouped;
        }
        for (SObject record : records) {
            Id key = (Id) record.get(lookupField);
            if (key == null) {
                continue;
            }
            List<SObject> bucket = grouped.get(key);
            if (bucket == null) {
                bucket = new List<SObject>();
                grouped.put(key, bucket);
            }
            bucket.add(record);
        }
        return grouped;
    }

    /**
     * Index records by their own Id, skipping unsaved records.
     * Prefer `new Map<Id, Account>(records)` when every record is persisted —
     * that constructor "populates it with the passed-in list of sObject
     * records. The keys are populated with the sObject IDs" (apexrefguide
     * L222322-L222324). Use this method when the list may contain new records.
     */
    public static Map<Id, SObject> indexById(List<SObject> records) {
        Map<Id, SObject> indexed = new Map<Id, SObject>();
        if (records == null) {
            return indexed;
        }
        for (SObject record : records) {
            if (record.Id != null) {
                indexed.put(record.Id, record);
            }
        }
        return indexed;
    }

    /**
     * Index by an arbitrary field, refusing to lose a row silently.
     * Last-write-wins is the platform default; when the caller believes the
     * field is unique, a collision is a data defect and should surface here.
     */
    public static Map<Object, SObject> indexByUnique(
        List<SObject> records,
        Schema.SObjectField field
    ) {
        Map<Object, SObject> indexed = new Map<Object, SObject>();
        if (records == null || field == null) {
            return indexed;
        }
        for (SObject record : records) {
            Object key = record.get(field);
            if (indexed.containsKey(key)) {
                throw new CollectionException(
                    'Duplicate key on ' + field + ': ' + key
                );
            }
            indexed.put(key, record);
        }
        return indexed;
    }

    /**
     * Split one list into matched / unmatched buckets in a single pass.
     * Both buckets always exist, so callers never need a containsKey guard.
     */
    public static Map<Boolean, List<SObject>> partition(
        List<SObject> records,
        Schema.SObjectField field,
        Set<Object> matchingValues
    ) {
        Map<Boolean, List<SObject>> parts = new Map<Boolean, List<SObject>>{
            true  => new List<SObject>(),
            false => new List<SObject>()
        };
        if (records == null || field == null) {
            return parts;
        }
        Set<Object> matches = (matchingValues == null)
            ? new Set<Object>()
            : matchingValues;
        for (SObject record : records) {
            Boolean hit = matches.contains(record.get(field));
            parts.get(hit).add(record);
        }
        return parts;
    }

    /**
     * A detached copy of a map's keys, safe to iterate while the map is edited.
     * Iterating the live keySet and removing from the map inside the loop is
     * "Modifying a collection's elements while iterating through that
     * collection is not supported and causes an error" (apexdev L3182-L3183).
     */
    public static Set<Id> snapshotKeys(Map<Id, SObject> source) {
        return (source == null)
            ? new Set<Id>()
            : new Set<Id>(source.keySet());
    }

    /**
     * Intersection without mutating either argument.
     */
    public static Set<Id> intersect(Set<Id> left, Set<Id> right) {
        if (left == null || right == null) {
            return new Set<Id>();
        }
        Set<Id> result = new Set<Id>(left);
        result.retainAll(right);
        return result;
    }

    /**
     * Difference without mutating either argument.
     */
    public static Set<Id> subtract(Set<Id> left, Set<Id> right) {
        if (left == null) {
            return new Set<Id>();
        }
        Set<Id> result = new Set<Id>(left);
        if (right != null) {
            result.removeAll(right);
        }
        return result;
    }
}
```

---

## 2. `OpportunitySortComparator.cls` — multi-key sort

`List.sort()` on sObjects follows a fixed sequence — sObject type label, then
`Name`, then standard fields alphabetically excluding Id and Name, then custom
fields alphabetically (`apexdev` L10245–L10258). That sequence is almost never
the business order, so a multi-key sort needs an explicit comparator. The
reference guide is blunt about the one obligation: "Your implementation must
explicitly handle null inputs in the compare() method to avoid a null pointer
exception" (`apexrefguide` L202283).

```apex
/**
 * Sort Opportunities by StageName ascending, then Amount descending, then Name
 * ascending. Nulls sort last in every key so a partially populated pipeline
 * does not scatter through the middle of the report.
 *
 * Passed to List.sort(): "a class implementing the Comparator interface can be
 * passed as a parameter to the List.sort method" (apexrefguide L221837-L221839).
 */
public inherited sharing class OpportunitySortComparator implements Comparator<Opportunity> {

    public Integer compare(Opportunity a, Opportunity b) {
        // Required by the interface contract: handle null elements explicitly.
        if (a == null && b == null) { return 0; }
        if (a == null) { return 1; }   // nulls last
        if (b == null) { return -1; }

        Integer byStage = compareStrings(a.StageName, b.StageName);
        if (byStage != 0) { return byStage; }

        Integer byAmount = compareDecimals(b.Amount, a.Amount);  // descending
        if (byAmount != 0) { return byAmount; }

        return compareStrings(a.Name, b.Name);
    }

    private Integer compareStrings(String left, String right) {
        if (left == right) { return 0; }
        if (left == null) { return 1; }
        if (right == null) { return -1; }
        // Not Collator: "locale-sensitive sorting can produce different results
        // depending on the user running the code, avoid using it in triggers or
        // in code that expects a particular sort order" (apexdev L7026-L7027).
        if (left > right) { return 1; }
        if (left < right) { return -1; }
        return 0;
    }

    private Integer compareDecimals(Decimal left, Decimal right) {
        if (left == null && right == null) { return 0; }
        if (left == null) { return 1; }
        if (right == null) { return -1; }
        return left.compareTo(right);
    }
}
```

Caller:

```apex
List<Opportunity> pipeline = [
    SELECT Id, Name, StageName, Amount
    FROM Opportunity
    WHERE IsClosed = false
    WITH USER_MODE
    LIMIT 5000
];
pipeline.sort(new OpportunitySortComparator());
```

---

## 3. `StageOwnerKey.cls` — a custom class as a Map key

Two-dimensional roll-ups are usually written as `Map<Id, Map<String, Decimal>>`,
which needs a containsKey guard at every level. A custom key class flattens it —
but only if the class supplies both methods: "provide equals and hashCode
methods in your class. Apex uses these two methods to determine equality and
uniqueness of keys for your objects" (`apexdev` L7044–L7045). Without them,
"User-defined types are compared by reference, which means that two objects are
equal only if they reference the same location in memory" (`apexdev`
L2135–L2138), so every constructed key is a distinct entry.

```apex
/**
 * Composite key: (OwnerId, StageName). Immutable on purpose — the guide warns
 * "If the object in your map keys or set elements changes after being added to
 * the collection, it won't be found anymore because of changed field values"
 * (apexdev L7040-L7041).
 */
public inherited sharing class StageOwnerKey {

    public final Id ownerId;
    public final String stageName;

    public StageOwnerKey(Id ownerId, String stageName) {
        this.ownerId = ownerId;
        this.stageName = stageName;
    }

    public Boolean equals(Object obj) {
        if (!(obj instanceof StageOwnerKey)) {
            return false;
        }
        StageOwnerKey other = (StageOwnerKey) obj;
        return this.ownerId == other.ownerId
            && this.stageName == other.stageName;
    }

    public Integer hashCode() {
        Integer ownerHash = (ownerId == null) ? 0 : ownerId.hashCode();
        Integer stageHash = (stageName == null) ? 0 : stageName.hashCode();
        return (31 * ownerHash) ^ stageHash;
    }

    public override String toString() {
        return 'StageOwnerKey[' + ownerId + '|' + stageName + ']';
    }
}
```

Rolling up in one pass, with no nested map and no guard:

```apex
Map<StageOwnerKey, Decimal> totals = new Map<StageOwnerKey, Decimal>();
for (Opportunity o : scope) {
    StageOwnerKey key = new StageOwnerKey(o.OwnerId, o.StageName);
    Decimal running = totals.get(key);
    totals.put(key, (running == null ? 0 : running) + (o.Amount == null ? 0 : o.Amount));
}
```

Note that `equals` uses `==` on `ownerId`. That is deliberate: "ID comparison
using `==` is case-sensitive and doesn't distinguish between 15-character and
18-character formats" (`apexdev` L2135–L2136), so a key built from a 15-character
Id still matches one built from the 18-character form. The same is **not** true
of `stageName`, or of any `Set<String>` holding Ids — see §4's
`testIdStringsAreNotIdKeys`.

---

## 4. `CollectionUtilsTest.cls` — pins the semantics, not just the coverage

```apex
@IsTest
private class CollectionUtilsTest {

    private static final Integer BULK = 200;

    @IsTest
    static void testGroupByLookupBucketsChildrenAndDropsNullKeys() {
        Account parentA = new Account(Name = 'Parent A');
        Account parentB = new Account(Name = 'Parent B');
        insert new List<Account>{ parentA, parentB };

        List<Contact> children = new List<Contact>();
        children.addAll(TestDataFactory.createContacts(3, parentA.Id, null));
        children.addAll(TestDataFactory.createContacts(2, parentB.Id, null));
        children.addAll(TestDataFactory.createContacts(1, null, null));  // orphan

        Map<Id, List<SObject>> grouped =
            CollectionUtils.groupByLookup(children, Contact.AccountId);

        Assert.areEqual(2, grouped.size(), 'orphan must not create a null bucket');
        Assert.areEqual(3, grouped.get(parentA.Id).size(), 'parent A bucket');
        Assert.areEqual(2, grouped.get(parentB.Id).size(), 'parent B bucket');
    }

    @IsTest
    static void testIndexByIdSkipsUnsavedRecords() {
        List<Account> saved = TestDataFactory.createAccounts(2, null);
        insert saved;
        List<Account> mixed = new List<Account>(saved);
        mixed.addAll(TestDataFactory.createAccounts(3, null));  // never inserted

        Map<Id, SObject> indexed = CollectionUtils.indexById(mixed);

        Assert.areEqual(2, indexed.size(),
            'three unsaved records share the null key and would collapse to one entry');
    }

    @IsTest
    static void testIndexByUniqueSurfacesCollisions() {
        List<Account> dupes = TestDataFactory.createAccounts(
            2, new Map<String, Object>{ 'AccountNumber' => 'ACME-1' }
        );
        Boolean threw = false;
        try {
            CollectionUtils.indexByUnique(dupes, Account.AccountNumber);
        } catch (CollectionUtils.CollectionException e) {
            threw = true;
        }
        Assert.isTrue(threw, 'a duplicate key must surface, not silently overwrite');
    }

    @IsTest
    static void testSnapshotKeysDetachesFromTheMap() {
        List<Account> accounts = TestDataFactory.createAccounts(3, null);
        insert accounts;
        Map<Id, SObject> live = CollectionUtils.indexById(accounts);

        Set<Id> snapshot = CollectionUtils.snapshotKeys(live);
        Set<Id> backedView = live.keySet();
        live.remove(accounts[0].Id);

        Assert.areEqual(3, snapshot.size(), 'the copy is unaffected by the removal');
        Assert.areEqual(2, backedView.size(),
            'keySet() is backed by the map: apexrefguide L222249');
    }

    @IsTest
    static void testSetOperationsDoNotMutateArguments() {
        Set<Id> left = new Set<Id>{ fakeId(1), fakeId(2), fakeId(3) };
        Set<Id> right = new Set<Id>{ fakeId(2), fakeId(3), fakeId(4) };

        Set<Id> both = CollectionUtils.intersect(left, right);
        Set<Id> only = CollectionUtils.subtract(left, right);

        Assert.areEqual(2, both.size(), 'intersection');
        Assert.areEqual(1, only.size(), 'difference');
        Assert.areEqual(3, left.size(), 'retainAll/removeAll must not reach the caller');
        Assert.areEqual(3, right.size(), 'argument set is untouched');
    }

    @IsTest
    static void testComparatorSortsOnThreeKeysWithNullsLast() {
        List<Opportunity> opps = new List<Opportunity>{
            new Opportunity(Name = 'B', StageName = 'Prospecting', Amount = 100),
            new Opportunity(Name = 'A', StageName = 'Prospecting', Amount = 100),
            new Opportunity(Name = 'C', StageName = 'Prospecting', Amount = 500),
            new Opportunity(Name = 'D', StageName = 'Prospecting', Amount = null),
            new Opportunity(Name = 'E', StageName = 'Negotiation',  Amount = 1)
        };

        opps.sort(new OpportunitySortComparator());

        Assert.areEqual('E', opps[0].Name, 'Negotiation sorts before Prospecting');
        Assert.areEqual('C', opps[1].Name, 'highest Amount first inside the stage');
        Assert.areEqual('A', opps[2].Name, 'Amount tie broken by Name ascending');
        Assert.areEqual('B', opps[3].Name, 'Amount tie broken by Name ascending');
        Assert.areEqual('D', opps[4].Name, 'null Amount sorts last');
    }

    @IsTest
    static void testCustomKeyCollapsesEqualKeys() {
        Id owner = UserInfo.getUserId();
        StageOwnerKey k1 = new StageOwnerKey(owner, 'Prospecting');
        StageOwnerKey k2 = new StageOwnerKey(owner, 'Prospecting');
        StageOwnerKey k3 = new StageOwnerKey(owner, 'Negotiation');

        Map<StageOwnerKey, Decimal> totals = new Map<StageOwnerKey, Decimal>();
        totals.put(k1, 100);
        totals.put(k2, 250);
        totals.put(k3, 50);

        Assert.areEqual(2, totals.size(), 'equals/hashCode collapse k1 and k2');
        Assert.areEqual(250, totals.get(k1).intValue(), 'later put overwrote the earlier entry');
        Assert.isTrue(new Set<StageOwnerKey>{ k1, k2, k3 }.size() == 2,
            'set uniqueness uses the same two methods');
    }

    @IsTest
    static void testIdStringsAreNotIdKeys() {
        Id full = UserInfo.getUserId();
        String eighteen = String.valueOf(full);
        String fifteen = eighteen.substring(0, 15);

        Set<Id> asIds = new Set<Id>{ Id.valueOf(eighteen), Id.valueOf(fifteen) };
        Set<String> asStrings = new Set<String>{ eighteen, fifteen };

        Assert.areEqual(1, asIds.size(),
            'Id normalizes 15-char to 18-char: apexdev L1255');
        Assert.areEqual(2, asStrings.size(),
            'Set<String> keeps both forms: string set elements are case-sensitive '
            + 'and are not Id-normalized, apexrefguide L230262-L230263');
    }

    @IsTest
    static void testBulkGroupingIsHeapNeutralAt200() {
        Account parent = new Account(Name = 'Bulk Parent');
        insert parent;
        List<Contact> children = TestDataFactory.createContacts(BULK, parent.Id, null);
        insert children;

        Test.startTest();
        Integer heapBefore = Limits.getHeapSize();
        Map<Id, List<SObject>> grouped =
            CollectionUtils.groupByLookup(children, Contact.AccountId);
        Integer heapAfter = Limits.getHeapSize();
        Integer queriesUsed = Limits.getQueries();
        Test.stopTest();

        Assert.areEqual(1, grouped.size(), 'one parent bucket');
        Assert.areEqual(BULK, grouped.get(parent.Id).size(), 'all 200 children grouped');
        Assert.areEqual(0, queriesUsed, 'grouping issues no SOQL of its own');
        Assert.isTrue(
            (heapAfter - heapBefore) < (Limits.getLimitHeapSize() / 10),
            'grouping 200 records must cost under 10% of the heap ceiling; used '
            + (heapAfter - heapBefore) + ' of ' + Limits.getLimitHeapSize()
        );
    }

    private static Id fakeId(Integer seed) {
        // 3-character key prefix + 12 padded characters = a 15-character Id
        // string; "If you set ID to a 15-character value, Apex converts the
        // value to its 18-character representation" (apexdev L1255).
        return Id.valueOf('001' + String.valueOf(seed).leftPad(12, '0'));
    }
}
```

Two notes on the assertions, because both are easy to get wrong:

- `Limits.getHeapSize()` is documented as approximate (`apexrefguide`
  L220711–L220722), so the bulk test asserts a *fraction of the ceiling*, not a
  byte count. Asserting an exact number produces a test that fails on an
  unrelated release.
- The heap and query readings are taken inside `Test.startTest()` /
  `Test.stopTest()`. Moving them outside changes what is being measured, because
  the setup DML is then inside the window.

*UNVERIFIED (2026-09-05): `fakeId()` builds a syntactically valid Id from a key
prefix without touching the database. The Apex Developer Guide documents that
`ID` accepts "Any valid 18-character Lightning Platform record identifier" and
that "All invalid ID values are rejected with a runtime exception" (`apexdev`
L1253–L1256), but it does not document which synthetic strings the runtime
accepts. If your org rejects the constructed value, insert real records instead.*

---

## 5. Class metadata

Every `.cls` above needs a sibling `<ClassName>.cls-meta.xml`. The API version
matches the repo's canonical classes (`templates/apex/BaseSelector.cls-meta.xml`).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

---

## 6. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>CollectionUtils</members>
        <members>OpportunitySortComparator</members>
        <members>StageOwnerKey</members>
        <members>CollectionUtilsTest</members>
        <members>TestDataFactory</members>
        <name>ApexClass</name>
    </types>
    <version>67.0</version>
</Package>
```

---

## 7. Deploy order and verification

Deploy order matters only for the test class, which references all three
production classes plus `TestDataFactory`. A single manifest deploy resolves
them together; if you deploy piecemeal, the order is
`StageOwnerKey` → `OpportunitySortComparator` → `CollectionUtils` →
`TestDataFactory` → `CollectionUtilsTest`.

```bash
# 1. Static check before the org ever sees it
python3 skills/apex/apex-collections-patterns/scripts/check_apex_collections_patterns.py \
    --manifest-dir force-app/main/default/classes --strict

# 2. Deploy the manifest
sf project deploy start --manifest manifest/package.xml --target-org myScratch

# 3. Run the semantics tests
sf apex run test \
    --tests CollectionUtilsTest \
    --result-format human \
    --code-coverage \
    --wait 10 \
    --target-org myScratch

# 4. Confirm the classes are actually active in the org
sf data query \
    --query "SELECT Name, ApiVersion, Status FROM ApexClass WHERE Name IN ('CollectionUtils','OpportunitySortComparator','StageOwnerKey')" \
    --use-tooling-api \
    --target-org myScratch
```

Step 4 is the verification step: a deploy can report success while a class is
left inactive, and `Status` on `ApexClass` is where that shows.

---

## How to read the artifact

- **`CollectionUtils` returns new collections; it never edits an argument.**
  That is the whole point. `retainAll` and `removeAll` are documented as
  operating on the receiver (`apexrefguide` L230750, L230690), so a helper that
  takes a `Set<Id>` and calls them directly hands the caller a silently mutated
  set.
- **`indexById` skipping null Ids is a design choice with a cost.** It loses the
  unsaved records rather than throwing. If losing them is wrong for your caller,
  raise `CollectionException` instead — but do not key them, because they all
  share the null key and only the last one survives (`apexdev` L1694–L1696).
- **`groupBy` returns `Map<Object, List<SObject>>`, not a typed map.** Apex
  generics do not extend to user-written methods, so callers cast: assigning the
  result to a `List<Contact>` works because "if type T is a subtype of U, then
  `List<T>` would be a subtype of `List<U>`" (`apexdev` L1741–L1744), and
  collection casting is checked at runtime (`apexdev` L6488–L6510).
- **`StageOwnerKey` fields are `final`.** A mutable key is the documented failure
  mode: change a field after insertion and the entry "won't be found anymore"
  (`apexdev` L7040–L7041).
- **The comparator sorts `StageName` lexically, not by pipeline order.** Real
  stage ordering needs a `Map<String, Integer>` rank built from
  `OpportunityStage.SortOrder`; the lexical compare here is the mechanical
  demonstration, not the business rule.
- **`testIdStringsAreNotIdKeys` is the test worth copying.** It is the one
  assertion in this file that catches a live production class of bug: an
  integration payload carrying 15-character Ids, matched against a `Set<String>`
  built from 18-character Ids.
