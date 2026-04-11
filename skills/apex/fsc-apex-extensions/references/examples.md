# Examples — FSC Apex Extensions

## Example 1: Custom Trigger on FinancialAccount with FSC Trigger Guard

**Context:** A wealth management firm needs to send a custom platform event whenever a Financial Account's `FinServ__Balance__c` changes by more than 10%. An FSC built-in trigger already fires on `FinServ__FinancialAccount__c` after-update to recalculate household rollups. Without coordination, both triggers fire and the rollup increments twice.

**Problem:** Without disabling the FSC account trigger during the custom handler, both the FSC trigger and the custom trigger fire on the same after-update event. The household balance rollup increments twice per transaction, producing corrupted household totals. The error is silent — no exception is thrown.

**Solution:**

```apex
public class FinancialAccountTriggerHandler {

    public static void handleAfterUpdate(
        List<FinServ__FinancialAccount__c> newList,
        Map<Id, FinServ__FinancialAccount__c> oldMap
    ) {
        // Disable the FSC account trigger to prevent double-processing
        FinServ__TriggerSettings__c ts = FinServ__TriggerSettings__c.getInstance();
        Boolean wasEnabled = ts.FinServ__AccountTrigger__c;
        try {
            if (wasEnabled) {
                ts.FinServ__AccountTrigger__c = false;
                upsert ts;
            }

            List<BalanceChangeEvent__e> events = new List<BalanceChangeEvent__e>();
            for (FinServ__FinancialAccount__c fa : newList) {
                FinServ__FinancialAccount__c old = oldMap.get(fa.Id);
                if (old.FinServ__Balance__c != null && old.FinServ__Balance__c != 0) {
                    Decimal changePct =
                        Math.abs(fa.FinServ__Balance__c - old.FinServ__Balance__c)
                        / Math.abs(old.FinServ__Balance__c) * 100;
                    if (changePct > 10) {
                        events.add(new BalanceChangeEvent__e(
                            AccountId__c = fa.Id,
                            ChangePercent__c = changePct
                        ));
                    }
                }
            }
            if (!events.isEmpty()) {
                EventBus.publish(events);
            }

        } finally {
            // Always re-enable the FSC trigger, even if an exception occurred
            if (wasEnabled) {
                ts.FinServ__AccountTrigger__c = true;
                upsert ts;
            }
        }
    }
}
```

**Why it works:** The `FinServ__TriggerSettings__c` custom setting acts as a per-transaction gate for FSC built-in triggers. Disabling the account trigger flag before custom DML prevents FSC from firing its rollup handler for the same records. The `try/finally` pattern guarantees the flag is restored even when an exception is thrown, preventing permanent disablement that would silently break rollup behavior for all subsequent transactions.

---

## Example 2: Post-Bulk-Load Rollup Recalculation Invocation

**Context:** A bank is migrating 2 million Financial Account records from a legacy system using Bulk API 2.0. After the load, relationship managers report that household net worth totals are still showing pre-migration values or zeros.

**Problem:** Bulk API inserts bypass the transactional Apex trigger path at the volume and batch size used. The FSC rollup engine never receives the trigger events needed to update household totals. Totals remain stale indefinitely until manual intervention.

**Solution:**

```apex
// Called immediately after the Bulk API job completes — either via
// post-load Apex job or invoked manually from Developer Console.

public class PostLoadRollupJob implements Queueable {

    public void execute(QueueableContext ctx) {
        // Batch size 200 is Salesforce-recommended for FSC rollup recalculation
        // to avoid CPU limit violations on complex household graphs.
        Id batchId = Database.executeBatch(
            new FinServ.RollupRecalculationBatchable(),
            200
        );
        System.debug('Rollup recalculation batch started: ' + batchId);
    }
}

// Enqueue after the Bulk API job is confirmed complete:
// System.enqueueJob(new PostLoadRollupJob());
```

**Why it works:** `FinServ.RollupRecalculationBatchable` iterates all accounts with pending rollup state and recomputes household totals from scratch using the current data. It is not incremental — it rebuilds the rollup graph for affected records regardless of the DML path that created them. The explicit batch size of 200 is required because FSC household graphs can involve dozens of related FinancialAccount records per batch item; higher batch sizes approach CPU time limits on complex data models.

---

## Example 3: Compliant Data Sharing — Adding a Participant via Apex

**Context:** An insurance org uses FSC Compliant Data Sharing on Financial Account records. A custom integration creates Financial Account records on behalf of relationship managers and needs to grant the assigned advisor read access after record creation. A developer attempts to insert a `FinancialAccountShare` record with a manual Apex sharing statement.

**Problem:** The manual `FinancialAccountShare` insert succeeds initially. However, the next time the CDS recalculation job runs (scheduled nightly, or triggered by a participant model change), the manually inserted share is deleted. The advisor loses access silently. No error is logged.

**Solution:**

```apex
// After creating the FinancialAccount record, register the advisor
// as a CDS participant rather than inserting a share directly.

public static void grantAdvisorAccess(Id financialAccountId, Id advisorUserId) {
    // Look up the sharing role for advisors (must match the CDS role definition)
    // Role names are org-specific; query FinServ__ShareRole__c for available roles.
    FinServ__ShareRole__c advisorRole = [
        SELECT Id
        FROM FinServ__ShareRole__c
        WHERE Name = 'Advisor'
        LIMIT 1
    ];

    FinServ__ShareParticipant__c participant = new FinServ__ShareParticipant__c(
        FinServ__FinancialAccount__c = financialAccountId,
        FinServ__User__c            = advisorUserId,
        FinServ__ShareRole__c       = advisorRole.Id
    );

    insert participant;
    // CDS will generate the share records with RowCause = CompliantDataSharing
    // on its next recalculation pass (or immediately via an async job).
}
```

**Why it works:** Inserting a `FinServ__ShareParticipant__c` record registers the user in the CDS participant model. The CDS engine itself generates the corresponding share record with `RowCause = CompliantDataSharing` — a system-owned row cause that cannot be set manually. Because the share record is CDS-owned, the recalculation job treats it as canonical and does not delete it. Any subsequent model changes (role updates, revocations) are handled by updating or deleting the participant record, not the share record directly.

---

## Anti-Pattern: Inserting Share Records Directly on CDS-Governed Objects

**What practitioners do:** Insert `AccountShare` or `FinancialAccountShare` records directly from Apex using standard `insert` DML, exactly as they would in a non-CDS org.

**What goes wrong:** The share records are accepted by the platform and visible immediately. However, when the CDS recalculation job next runs — whether triggered by a model change or the scheduled batch — the system evaluates all share records on governed objects against the current participant model. Any share with a `RowCause` not recognized by CDS (e.g., `Manual` or a custom row cause) is deleted. The affected users lose access with no exception or log entry recorded on the share record itself.

**Correct approach:** Always use `FinServ__ShareParticipant__c` inserts to grant access under CDS. To revoke access, delete the participant record — not the share record. If the org requires immediate share propagation rather than waiting for the scheduled batch, call the CDS recalculation API method after inserting the participant.
