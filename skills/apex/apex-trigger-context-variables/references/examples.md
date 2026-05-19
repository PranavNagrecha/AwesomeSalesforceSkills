# Examples — Apex Trigger Context Variables

Two worked scenarios and one anti-pattern that show how the
context variables (`Trigger.new`, `Trigger.old`, `Trigger.newMap`,
`Trigger.oldMap`, the event booleans) compose in real handlers.
Each example assumes a one-trigger-per-object pattern that delegates
to a `TriggerHandler` subclass (see `templates/apex/TriggerHandler.cls`
and `templates/apex/TriggerControl.cls`).

---

## Example 1: Bulk-safe field diff in before-update with cascading child write

**Context:** When an Account's `Industry` changes, every related
Opportunity needs a `Source_Industry_Snapshot__c` updated so the
pipeline report can group historical revenue by the Industry at the
moment of close. A Data Loader job updates 200 Accounts at a time
during quarterly cleanups. Each Account has 10–50 Opportunities.

**Problem:** A practitioner writes a per-record diff with a SOQL
fetch inside the loop and an `update opp` per Account. At 200
Accounts × 1 SOQL each, the trigger hits the 100-SOQL governor
limit at Account #101; the whole bulk update rolls back. Worse,
the simpler form `if (a.Industry != Trigger.oldMap.get(a.Id).Industry)`
without bulk-aware structure looks correct in a single-record
sandbox test but explodes in production.

**Solution:** Collect changed-Account Ids in a single pass over
`Trigger.new` + `Trigger.oldMap`, do ONE SOQL for related
Opportunities, mutate them in memory, and issue ONE `update`.
The diff itself uses the platform-canonical
"`Trigger.new[i]` field vs `Trigger.oldMap.get(record.Id)` field"
pattern — Apex has no built-in `ISCHANGED()`; this comparison IS
the equivalent.

```apex
public class AccountTriggerHandler extends TriggerHandler {

    protected override void beforeUpdate() {
        // Step 1: identify which Accounts actually changed Industry.
        // Trigger.oldMap is populated in before-update, so a
        // map-keyed lookup is safe (it's null in before-insert).
        Set<Id> changedAccountIds = new Set<Id>();
        for (Account a : (List<Account>) Trigger.new) {
            Account oldA = (Account) Trigger.oldMap.get(a.Id);
            if (a.Industry != oldA.Industry) {
                changedAccountIds.add(a.Id);
            }
        }
        if (changedAccountIds.isEmpty()) return;

        // Step 2: one SOQL for all related Opportunities across the batch.
        Map<Id, List<Opportunity>> oppsByAccount = new Map<Id, List<Opportunity>>();
        for (Opportunity o : [
            SELECT Id, AccountId, Source_Industry_Snapshot__c
            FROM Opportunity
            WHERE AccountId IN :changedAccountIds
            WITH SYSTEM_MODE
        ]) {
            if (!oppsByAccount.containsKey(o.AccountId)) {
                oppsByAccount.put(o.AccountId, new List<Opportunity>());
            }
            oppsByAccount.get(o.AccountId).add(o);
        }

        // Step 3: build the update list. Mutate copies, not Trigger.old.
        List<Opportunity> toUpdate = new List<Opportunity>();
        for (Account a : (List<Account>) Trigger.new) {
            if (!oppsByAccount.containsKey(a.Id)) continue;
            for (Opportunity o : oppsByAccount.get(a.Id)) {
                o.Source_Industry_Snapshot__c = a.Industry;
                toUpdate.add(o);
            }
        }

        // Step 4: one DML for all 200 × N child rows.
        if (!toUpdate.isEmpty()) update toUpdate;
    }
}
```

**Why it works:** The diff is read-only — it consults
`Trigger.oldMap` (populated in before-update) and the iteration
variable from `Trigger.new`. The cascading child write happens on
a separate, freshly built `List<Opportunity>`. Because the diff,
the SOQL, and the DML are each O(1) per transaction (not per record),
the handler scales identically at 1 record and 200 records. The
canonical "before-update mutates fields directly on `Trigger.new`"
path doesn't apply here — the Industry change isn't being
overridden; it's being *snapshot* onto related rows.

---

## Example 2: Single-handler dispatch routed by isInsert / isUpdate / isBefore / isAfter

**Context:** A single `ContactTrigger` listens on all six events
(`before insert`, `before update`, `after insert`, `after update`,
`before delete`, `after delete`). The handler needs to keep each
event's logic isolated so the team can change the after-insert
related-record creation without risking the before-update field
stamping.

**Problem:** Practitioners express the routing inline in the trigger
body with a cascade of `if (Trigger.isBefore && Trigger.isInsert)`
branches. Once the trigger has 200 lines of mixed-event code, every
change requires re-reading every branch to confirm it doesn't fire
in the wrong context — and a typo (`Trigger.isInsert` instead of
`Trigger.isUpdate`) silently runs the wrong logic at the wrong time
because the booleans are mutually exclusive but never null.

**Solution:** Keep the trigger body to a single line. Let the
canonical `TriggerHandler` base class dispatch each event to a
dedicated virtual method via `Trigger.isBefore` / `Trigger.isAfter`
× `Trigger.isInsert` / `Trigger.isUpdate` / etc. The subclass only
overrides the events it actually cares about — every other event
is a free no-op.

```apex
// Trigger body — one line, one entry point.
trigger ContactTrigger on Contact (
    before insert, before update, before delete,
    after insert, after update, after delete
) {
    new ContactTriggerHandler().run();
}
```

```apex
public class ContactTriggerHandler extends TriggerHandler {

    // before insert: Trigger.new is read-write; Trigger.newMap and
    // Trigger.old are null (no Ids exist yet).
    protected override void beforeInsert() {
        for (Contact c : (List<Contact>) Trigger.new) {
            if (String.isBlank(c.LeadSource)) c.LeadSource = 'Web';
        }
    }

    // before update: both maps populated; canonical diff pattern.
    protected override void beforeUpdate() {
        for (Contact c : (List<Contact>) Trigger.new) {
            Contact oldC = (Contact) Trigger.oldMap.get(c.Id);
            if (c.Email != oldC.Email) c.Email_Last_Changed__c = Datetime.now();
        }
    }

    // after insert: Trigger.new is read-only; Trigger.newMap is now
    // populated (Ids exist). Create child records via separate DML.
    protected override void afterInsert() {
        List<Task> defaults = new List<Task>();
        for (Contact c : (List<Contact>) Trigger.new) {
            defaults.add(new Task(WhoId = c.Id, Subject = 'Welcome', Status = 'Open'));
        }
        if (!defaults.isEmpty()) insert defaults;
    }

    // before delete: Trigger.new is null. Only Trigger.old / Trigger.oldMap.
    protected override void beforeDelete() {
        for (Contact c : (List<Contact>) Trigger.old) {
            if (c.Is_Protected__c) c.addError('Cannot delete protected Contact');
        }
    }
}
```

**Why it works:** The `TriggerHandler.run()` method inspects the
context booleans exactly once per transaction in its `dispatch()`
method and routes to the right virtual. Each subclass method
references only the context variables guaranteed populated in its
event — there's no defensive `Trigger.oldMap != null` check needed
in `beforeUpdate()` because the method literally cannot run outside
that context. The recursion guard, the `TriggerControl` bypass
hook, and the depth-limit enforcement come for free from the base
class.

---

## Anti-Pattern: Assigning to Trigger.new in an after-trigger

**What practitioners do:**

```apex
trigger AccountTrigger on Account (after update) {
    for (Account a : Trigger.new) {
        // Looks like a normal field stamp...
        a.Audit_Last_Modified__c = Datetime.now();
    }
}
```

**What goes wrong:** Salesforce throws at runtime:

```
System.FinalException: Record is read-only
```

The exception fires on the first assignment to `a.Audit_Last_Modified__c`.
`Trigger.new` is read-write ONLY in `before` events; in any `after`
event the records are sealed by the platform (the values are already
committed to the database in this transaction's view, so an in-memory
mutation would silently diverge from what was persisted). The
`Trigger.old` and `Trigger.oldMap` collections are read-only in
*every* event — even `before delete`. Assigning to a field on a
record from `Trigger.old` throws the same `System.FinalException`
regardless of context.

The same bug appears in a more disguised form when developers pass
`Trigger.new` into a helper method that mutates it:

```apex
trigger AccountTrigger on Account (after insert) {
    AccountStamper.stamp(Trigger.new);   // throws inside the helper
}
```

The exception fires from inside `AccountStamper.stamp`, which makes
the stack trace point at the helper class rather than the trigger
file. Reviewers who don't notice the `after insert` context spend
time hunting for the bug in the helper.

**Correct approach:** Two options, in order of preference.

1. **Move the mutation to a before-trigger.** Field stamping
   belongs in `before insert` / `before update` because the engine
   persists the mutated `Trigger.new` values automatically — no
   extra DML, no governor cost, no `FinalException` risk:

   ```apex
   protected override void beforeUpdate() {
       for (Account a : (List<Account>) Trigger.new) {
           a.Audit_Last_Modified__c = Datetime.now();
       }
   }
   ```

2. **If the stamp truly must happen after insert** (e.g., it
   depends on the Id, which doesn't exist until after-insert),
   build a fresh `List<Account>` of shallow copies and `update`
   them explicitly:

   ```apex
   protected override void afterInsert() {
       List<Account> toUpdate = new List<Account>();
       for (Account a : (List<Account>) Trigger.new) {
           toUpdate.add(new Account(Id = a.Id, Audit_Last_Modified__c = Datetime.now()));
       }
       if (!toUpdate.isEmpty()) update toUpdate;
   }
   ```

   This costs one extra DML and re-fires the trigger — add the
   recursion guard via `TriggerControl.skipOnce('AccountTriggerHandler')`
   before the `update`, or use the canonical depth counter in
   `templates/apex/TriggerHandler.cls`. The first option is almost
   always preferable; the second exists for the rare case where
   the field genuinely depends on post-insert state.
