# Examples — Order of Execution Deep Dive

## Example 1: Workflow Field Update Causing Double Trigger Fire

**Context:** An Account before trigger unconditionally inserts a child `Audit_Log__c` record on every update. A workflow rule on Account fires a field update when `Type` changes to "Customer".

**Problem:** When a rep changes the Account Type to "Customer", two `Audit_Log__c` records are created instead of one. No one changed the trigger logic.

**Root cause:** The workflow field update at step 12 causes before and after triggers to re-run once. The before trigger runs a second time and creates a second audit log.

**Solution:**

```apex
trigger AccountTrigger on Account (before update) {
    AccountTriggerHandler.handleBeforeUpdate(Trigger.new, Trigger.oldMap);
}

public class AccountTriggerHandler {
    private static Set<Id> auditLogCreated = new Set<Id>();

    public static void handleBeforeUpdate(List<Account> newList, Map<Id, Account> oldMap) {
        List<Audit_Log__c> logs = new List<Audit_Log__c>();
        for (Account a : newList) {
            if (auditLogCreated.contains(a.Id)) continue; // skip re-fire
            auditLogCreated.add(a.Id);
            logs.add(new Audit_Log__c(
                Account__c = a.Id,
                Event__c   = 'Updated',
                Timestamp__c = System.now()
            ));
        }
        if (!logs.isEmpty()) insert logs;
    }
}
```

**Why it works:** The static `Set<Id>` persists across the trigger re-fire caused by the workflow field update. On the second pass the Id is already in the set, so the audit log is not created again.

---

## Example 2: Before-Save Flow and Before Trigger Writing the Same Field

**Context:** A before-save record-triggered Flow sets `Description` to a formatted summary. A before Apex trigger also writes to `Description` to append a timestamp. After save, only the timestamp appears — the Flow's summary is gone.

**Problem:** Both run at step 3. The Apex trigger runs after the Flow (execution order within step 3 is not guaranteed, but in practice the trigger overwrote the Flow's value by doing an unconditional assignment).

**Solution:**

```apex
// In the before trigger: only write Description if it is blank
// (let the Flow set it; only fill in as a fallback)
trigger AccountTrigger on Account (before insert, before update) {
    for (Account a : Trigger.new) {
        if (String.isBlank(a.Description)) {
            a.Description = '[Updated: ' + System.now().format() + ']';
        }
    }
}
```

**Why it works:** The trigger now acts as a fallback rather than an unconditional writer. The Flow's value, written earlier in step 3, is preserved because the trigger only writes when the field is empty.

---

## Example 3: After-Save Flow Running Unexpectedly After Workflow Side Effects

**Context:** A developer builds an after-save Flow to send a notification email when a Case is closed. A workflow rule also sends an email when a Case is closed. Operations reports two emails being sent.

**Problem:** This is actually correct behavior, not a bug. The workflow email fires at step 11; the after-save Flow fires at step 15. Both fire independently. The developer assumed the Flow would suppress the workflow email.

**Solution:** Deactivate the workflow rule email alert and manage all email logic from the after-save Flow (step 15), or vice versa. Do not assume one automation will prevent another from firing.

**Why it works:** Understanding the order removes the incorrect assumption. Both step 11 (workflow) and step 15 (after-save Flow) are independent execution points. Consolidating to one tool removes the duplicate.

---

## Example 4: Roll-Up Summary Triggering Parent Trigger Unexpectedly

**Context:** An Opportunity after trigger updates a field on the parent Account. The Account also has an after trigger that sends an email. The email is sent on every Opportunity update, even when nothing Account-related changed.

**Problem:** The Opportunity is in a master-detail relationship with Account via a roll-up summary. At step 17 of the Opportunity save, the roll-up summary causes the Account record to be updated, firing the Account after trigger — which sends the email.

**Solution:**

```apex
// In the Account after trigger, check which fields actually changed
// before sending the email
trigger AccountTrigger on Account (after update) {
    for (Account a : Trigger.new) {
        Account old = Trigger.oldMap.get(a.Id);
        // Only send email if a human-meaningful field changed
        if (a.AnnualRevenue != old.AnnualRevenue || a.Type != old.Type) {
            EmailService.sendAccountChangeNotification(a.Id);
        }
    }
}
```

**Why it works:** The trigger now compares field values to detect meaningful changes. Roll-up summary updates typically change only the summary field, so the condition is false and no email is sent.

---

## Anti-Pattern: Treating After-Save Flow as Equivalent to After Trigger in Timing

**What practitioners do:** Assume an after-save Flow (step 15) and an after Apex trigger (step 8) run at roughly the same time and can be used interchangeably for writing related records.

**What goes wrong:** An after-save Flow creates a related record at step 15. An after trigger that queries for that related record runs at step 8 — before the Flow has created it. The query returns zero rows, and the trigger logic silently skips processing.

**Correct approach:** If trigger logic depends on a Flow-created record, move the creation into the after trigger (step 8) and remove the Flow creation step, or restructure so the trigger does not depend on a Flow side effect.
