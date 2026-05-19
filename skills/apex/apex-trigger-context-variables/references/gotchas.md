# Gotchas — Apex Trigger Context Variables

Second-order behaviors that surface once practitioners have memorized
the event matrix in `SKILL.md`. These are the platform rules that
cause "the code looks right and the unit test passes, but production
throws" — typically because the unit test ran one record through one
event and missed the cross-event or cross-batch reality.

## Gotcha 1: `Trigger.new` is null in delete events; reaching for it throws NPE

**What happens:** A handler routes through `before delete` or
`after delete` and references `Trigger.new` — for instance, to do
a "snapshot the deleted record" pattern by reading the current
field values. Salesforce returns `Trigger.new` as `null` in any
delete context (the records are being deleted; there's no "new"
version of them), so the next line — `for (Account a : Trigger.new)`
or `Trigger.new[0].Name` — throws `System.NullPointerException:
Attempt to de-reference a null object`.

**When it occurs:** Cross-event helper methods that take
`Trigger.new` as a parameter from any caller, including delete
contexts. Also occurs in handlers that copy-paste an `after insert`
pattern into `after delete` without re-checking the matrix.

**How to avoid:** In delete handlers, use `Trigger.old` and
`Trigger.oldMap` exclusively. The canonical "soft-delete audit"
shape:

```apex
protected override void beforeDelete() {
    for (Account a : (List<Account>) Trigger.old) {
        if (a.Is_Protected__c) a.addError('Cannot delete');
    }
}
```

When sharing helper methods across insert/update/delete contexts,
pass the appropriate collection at the call site (`Trigger.isDelete
? Trigger.old : Trigger.new`) rather than letting the helper guess
from the context booleans.

---

## Gotcha 2: `Trigger.old` is null in insert events; defaulting from "previous value" is impossible

**What happens:** A practitioner writes a generic
"stamp `Previous_Status__c` from old value" routine that runs in
both `before insert` and `before update`. In `before insert`,
`Trigger.old` and `Trigger.oldMap` are both null because there's
no previous version of the record — the record doesn't exist yet.
The `Trigger.oldMap.get(rec.Id)` call throws
`System.NullPointerException`, and the whole insert rolls back.

**When it occurs:** Generic field-change tracking patterns that
want to run on both create and update. Particularly common when
developers copy a "diff and stamp" handler from one object to
another and don't re-read the event matrix for the new object's
trigger configuration.

**How to avoid:** Branch on `Trigger.isInsert` vs `Trigger.isUpdate`
inside the handler, or split into dedicated `beforeInsert()` and
`beforeUpdate()` overrides in a `TriggerHandler` subclass (the
canonical fix — see `templates/apex/TriggerHandler.cls`). In
`before insert`, default `Previous_Status__c` to null or to the
current `Status__c` value:

```apex
protected override void beforeInsert() {
    for (Account a : (List<Account>) Trigger.new) {
        a.Previous_Status__c = null;   // there is no previous value
    }
}
protected override void beforeUpdate() {
    for (Account a : (List<Account>) Trigger.new) {
        Account oldA = (Account) Trigger.oldMap.get(a.Id);
        a.Previous_Status__c = oldA.Status__c;
    }
}
```

---

## Gotcha 3: `Trigger.newMap` is unavailable in `before insert` because the records have no Ids yet

**What happens:** A `before insert` handler tries to use
`Trigger.newMap.get(someId)` to look up a record from the inserting
batch. The call throws `System.NullPointerException` — the platform
doesn't populate `Trigger.newMap` in `before insert` because the
inserting records don't have Ids yet (the Id is assigned by the
database during the upcoming INSERT, after this trigger returns).

**When it occurs:** Cross-record validations within the same batch
("if any inserting Account has Industry = 'X', flag the others") that
borrow a `Map`-keyed lookup pattern from a working `before update`
handler. Also occurs when developers think of `Trigger.newMap` as
"the records, but indexable" and try to use it as a convenience
collection — it isn't; in `before insert` it doesn't exist.

**How to avoid:** In `before insert`, iterate `Trigger.new` directly.
If you need a keyed lookup, key by something other than Id — a
combination of `Name + Owner` or an external Id field works:

```apex
protected override void beforeInsert() {
    Map<String, Account> byExtId = new Map<String, Account>();
    for (Account a : (List<Account>) Trigger.new) {
        if (a.External_Id__c != null) byExtId.put(a.External_Id__c, a);
    }
    // ...use byExtId for cross-record checks within the batch
}
```

Note: `Trigger.newMap` IS populated in `after insert` — by then
the platform has assigned the Ids. So patterns that build a
`Map<Id, ChildRecord>` keyed by parent Id are correct from
`after insert` onward, just not in the `before` phase.

---

## Gotcha 4: `Trigger.size` reflects the whole batch, not records matching your filter

**What happens:** A handler tries to detect "single-record edit
from the UI vs bulk update from Data Loader" by checking
`if (Trigger.size == 1)`. This is broken in three orthogonal ways:
(1) `Trigger.size` is the count of records the trigger fired for
in this invocation — a single sObject DML can still fire the
trigger with up to 200 records; (2) a Data Loader job with a
batch size of 1 also passes `Trigger.size == 1`; (3) if your code
intends "only process the one record that has Industry = 'Tech'",
`Trigger.size` doesn't help — it's the batch size, not the
filtered-match count.

**When it occurs:** Practitioners trying to short-circuit "expensive
logic" for the single-record case. The branch *appears* to work in
unit tests (which usually insert one record) and on the UI
(which fires a one-record DML), so the bug ships and only surfaces
when a batch hits.

**How to avoid:** Don't branch on `Trigger.size` at all. Bulkify
every code path unconditionally — the same code must handle 1 and
200 records identically. If you need "did exactly one record in the
batch match my filter," count the matches yourself:

```apex
List<Account> matching = new List<Account>();
for (Account a : (List<Account>) Trigger.new) {
    if (a.Industry == 'Tech') matching.add(a);
}
if (matching.size() == 1) {
    // ...special-case logic
}
```

`Trigger.size` is fine for *informational* logging (`'Trigger fired
for ' + Trigger.size + ' records'`) but never for control flow.

---

## Gotcha 5: Assigning to `Trigger.new[i].SomeField` in any `after`-context throws `System.FinalException: Record is read-only`

**What happens:** A practitioner extends a `before update` handler
to also run logic in `after update` (e.g., to access the now-committed
record Id from a newly inserted lookup) and copies the field-stamp
loop forward. The first assignment — `Trigger.new[i].Audit_Stamp__c
= Datetime.now()` or `a.Audit_Stamp__c = Datetime.now()` where `a`
came from `Trigger.new` — throws:

```
System.FinalException: Record is read-only
```

The exception fires at the moment of assignment. The platform
explicitly seals `Trigger.new` in `after` contexts because the
record state visible to the trigger is the post-commit snapshot;
allowing an in-memory mutation would silently desync the in-memory
record from the database version. The same exception fires when
assigning to `Trigger.old` in any context — `Trigger.old` and
`Trigger.oldMap` records are read-only in *all* events, including
`before update` and `before delete`.

**When it occurs:** Any field-stamping logic accidentally placed in
an `after` trigger. Also common when developers refactor a single
event into a multi-event handler without re-reading the mutability
rules. Often masked in unit tests when the assignment line is
reached only conditionally — the test passes when the condition
is false, then production hits the condition and crashes.

**How to avoid:** Stamp fields in `before` events whenever possible
— the engine persists the mutation as part of the DML the trigger
fired for, with zero extra DML cost. If the stamp genuinely
requires `after`-context information (e.g., the new Id), build a
shallow-copy `List<SObject>` and `update` it explicitly, paired
with a recursion guard:

```apex
protected override void afterInsert() {
    List<Account> toUpdate = new List<Account>();
    for (Account a : (List<Account>) Trigger.new) {
        toUpdate.add(new Account(Id = a.Id, Audit_Stamp__c = Datetime.now()));
    }
    if (!toUpdate.isEmpty()) {
        TriggerHandler.skipOnce('AccountTriggerHandler');
        update toUpdate;
    }
}
```

See `templates/apex/TriggerHandler.cls` for the canonical
`skipOnce()` hook and depth counter.
