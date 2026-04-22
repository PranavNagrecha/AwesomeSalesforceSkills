# LLM Anti-Patterns — Apex Trigger Context Variables

Common mistakes AI coding assistants make with Trigger.new / old / newMap / oldMap.

## Anti-Pattern 1: Accessing Trigger.oldMap in before insert

**What the LLM generates:**

```
trigger MyT on Account (before insert) {
    for (Account a : Trigger.new) {
        Account old = Trigger.oldMap.get(a.Id);  // NPE
    }
}
```

**Why it happens:** Model uses `Trigger.oldMap` blindly.

**Correct pattern:**

```
In before insert and after insert, Trigger.old and Trigger.oldMap
are null. Guard:
if (Trigger.isUpdate) {
    Account old = Trigger.oldMap.get(a.Id);
}
Or split the trigger into separate event handlers.
```

**Detection hint:** Apex trigger with `Trigger.oldMap.get(` inside an insert-only event.

---

## Anti-Pattern 2: Indexing Trigger.newMap in before insert

**What the LLM generates:** `Trigger.newMap.get(id)` in a before-insert handler.

**Why it happens:** Model conflates insert and update semantics.

**Correct pattern:**

```
Before insert: records have no Ids yet. Trigger.newMap is null.
Iterate Trigger.new directly for field stamping:
for (Account a : Trigger.new) {
    a.SomeField__c = 'X';
}
Trigger.newMap becomes useful from after-insert onward.
```

**Detection hint:** Apex referencing `Trigger.newMap` in a before-insert branch.

---

## Anti-Pattern 3: Modifying Trigger.new in after events

**What the LLM generates:**

```
trigger T on Account (after update) {
    for (Account a : Trigger.new) a.SomeField__c = 'X';  // throws
}
```

**Why it happens:** Model doesn't distinguish before/after mutability.

**Correct pattern:**

```
In after events, Trigger.new is read-only. To update records, build a
new list and DML:
List<Account> toUpdate = new List<Account>();
for (Account a : Trigger.new) toUpdate.add(new Account(Id=a.Id, SomeField__c='X'));
update toUpdate;

Even better: do the update in before-update and avoid the extra DML.
```

**Detection hint:** Apex assigning to record fields inside an after-event trigger body.

---

## Anti-Pattern 4: No recursion guard on record update

**What the LLM generates:** Trigger that updates its own records unconditionally, causing infinite re-entry.

**Why it happens:** Model doesn't track trigger re-fire semantics.

**Correct pattern:**

```
Guard with a static flag:
public class TriggerControl {
    public static Set<Id> processed = new Set<Id>();
}

for (Account a : Trigger.new) {
    if (TriggerControl.processed.contains(a.Id)) continue;
    TriggerControl.processed.add(a.Id);
    // work
}

Or use the repo's TriggerControl template at templates/apex/TriggerControl.cls.
```

**Detection hint:** Trigger performing DML on Trigger.new records with no visible static guard.

---

## Anti-Pattern 5: Using Trigger.size when .new is more informative

**What the LLM generates:** `if (Trigger.size > 1) { /* bulk path */ }` scattered across the trigger.

**Why it happens:** Model tries to micro-optimize.

**Correct pattern:**

```
Bulkify unconditionally. Trigger.size early-exits mask bugs when a
bulk insert hits. The same code must handle 1 and 200 records.
Use Trigger.new.size() only when a specific optimization is justified
and tested.
```

**Detection hint:** Trigger code branching on `Trigger.size` for single vs bulk paths.
