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
for (Case caseRecord : Trigger.new) {
    Case oldCase = Trigger.oldMap.get(caseRecord.Id);
    if (oldCase.Status__c == caseRecord.Status__c) {
        continue;
    }
    if (caseRecord.Status__c == 'Escalated') {
        escalationIds.add(caseRecord.Id);
    }
}
```

**Why it works:** The delta check removes unnecessary re-entry before a static guard even becomes necessary.

---

## Anti-Pattern: One Global Static Boolean

**What practitioners do:** They write `if (isExecuting) return; isExecuting = true;`.

**What goes wrong:** The first processed record or phase can suppress legitimate work for every later record in the transaction.

**Correct approach:** Use record-aware guards and delta checks instead of one global switch.
