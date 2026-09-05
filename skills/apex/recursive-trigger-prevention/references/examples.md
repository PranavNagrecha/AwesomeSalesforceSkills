# Examples — Recursive Trigger Prevention

## Example 1: Set<Id>-Based Guard For Self-DML

**Context:** An after-update trigger enriches Accounts and may update the same records again.

**Problem:** A single static Boolean blocks unrelated records and still creates confusion in bulk processing.

**Solution:**

```apex
public class AccountRecursionGuard {
    private static Set<Id> processedAccountIds = new Set<Id>();

    public static Boolean shouldProcess(Id recordId) {
        if (processedAccountIds.contains(recordId)) {
            return false;
        }
        processedAccountIds.add(recordId);
        return true;
    }
}

for (Account accountRecord : Trigger.new) {
    if (!AccountRecursionGuard.shouldProcess(accountRecord.Id)) {
        continue;
    }
    // self-DML path that would otherwise retrigger
}
```

**Why it works:** The guard is scoped to the affected record rather than suppressing the entire transaction globally.

---

## Example 2: Delta Check Before Self-Triggering Work

**Context:** A trigger should only create follow-up work when `Status__c` truly changes.

**Problem:** The handler updates the record and retriggers even when the relevant state did not change.

**Solution:**

```apex
Map<Id, Case> oldMap = (Map<Id, Case>) Trigger.oldMap;
for (Case caseRecord : (List<Case>) Trigger.new) {
    Case oldCase = oldMap.get(caseRecord.Id);
    if (oldCase.Status == caseRecord.Status) {
        continue;
    }
    if (caseRecord.Status == 'Escalated') {
        escalationIds.add(caseRecord.Id);
    }
}
```

`Status` is the standard Case picklist, not a custom field — a `Status__c` here fails to compile. Note
one limit of the delta check on its own: after a workflow field update re-fires the update triggers,
`Trigger.old` still holds the values from before the *initial* user edit, not the workflow-updated ones
(`apexdev` L15494–15498), so the comparison on that pass is original-vs-final rather than
previous-vs-final.

**Why it works:** The delta check removes unnecessary re-entry before a static guard even becomes necessary.

---

---

## Example 3: Reading The Loop Out Of A Debug Log Before Writing Any Guard

**Context:** Users report that saving an Account "hangs and then errors". Nobody knows which automation
is looping, and three candidate triggers plus two flows exist on the object.

**Problem:** Every guard proposed so far is a guess. Installing one would suppress a symptom and might
silence the wrong automation.

**Solution:** Count trigger entries in the log first. `CODE_UNIT_STARTED` and `CODE_UNIT_FINISHED`
delimit units of code, a trigger is one such unit, and the line names the trigger and its event
(`apexdev` L38178-38190).

```bash
sf apex tail log --target-org myOrg > /tmp/save.log
# reproduce the save in the UI, then Ctrl-C

# how many times did each trigger/event pair start?
grep -o 'CODE_UNIT_STARTED.*trigger event [A-Za-z]*' /tmp/save.log \
  | sed 's/.*\]//' \
  | sort | uniq -c | sort -rn
```

UNVERIFIED (2026-09-05): `sf apex tail log` and its flags are Salesforce CLI syntax, not defined in
the Apex Developer Guide; the log-line format it greps for is grounded (`apexdev` L38178-38190).

Representative output from a real ping-pong:

```text
   9 AccountTrigger on Account trigger event AfterUpdate
   9 ContactTrigger on Contact trigger event AfterUpdate
   1 AccountTrigger on Account trigger event BeforeUpdate
```

**Why it works:** the two counts moving together in lockstep identifies a mutual loop between the two
objects, not a self-DML loop inside one handler - which changes where the guard goes. A count of 1 for
`BeforeUpdate` against 9 for `AfterUpdate` further narrows it to the after-save path. Nine is also the
number to watch: the ceiling is a stack depth of 16 (`apexdev` L19559), so this save was a few records'
worth of nesting away from an uncatchable failure.

A count of exactly 2 is not a loop. That is the workflow field update re-firing the update triggers "one
more time (and only one more time)" (`apexdev` L15455-15460) - expected, bounded, and usually work you
want served.

---

## Anti-Pattern: One Global Static Boolean

**What practitioners do:** They write `if (isExecuting) return; isExecuting = true;`.

**What goes wrong:** The first processed record or phase can suppress legitimate work for every later record in the transaction.

**Correct approach:** Use record-aware guards and delta checks instead of one global switch.
