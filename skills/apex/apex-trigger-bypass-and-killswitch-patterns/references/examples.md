## Example 1: Bulk data loader bypass via Custom Permission

**Context:** The customer has nightly Data Loader inserts of 2M Contact rows
from a marketing platform. The Contact trigger enriches with territory,
fires outbound callouts, and recalculates rollups. None of this should run
during the load.

**Problem:** Practitioners often disable the trigger by deploying a
commented-out version, run the load, then redeploy. This is unsafe (window
of risk for other users), slow, and leaves no audit trail.

**Solution:**

```apex
// ContactTriggerHandler.cls
public with sharing class ContactTriggerHandler extends TriggerHandler {
    public override void run() {
        if (!TriggerControl.isActive('Contact', 'ContactTriggerHandler')) {
            ApplicationLogger.info(
                'ContactTriggerHandler',
                'Skipped: kill switch / bypass permission active for user '
                    + UserInfo.getUserId()
            );
            return;
        }
        super.run();
    }
}
```

The Data Loader runs as the `dataload@acme.com` user, who has the
`Bypass_Triggers` Custom Permission via the `Bulk_Loader_Bypass` Permission Set.
`TriggerControl.isActive(...)` calls
`FeatureManagement.checkPermission('TriggerControl_BypassAll')` — when true,
returns `false` and the handler exits.

**Why it works:** No code change is required to enable or disable the load.
Permission Set assignment is auditable in Setup Audit Trail. Other users
(non-loader) are not affected because the perm is scoped to the loader user.

---

## Example 2: Integration-user bypass via permission set assignment

**Context:** A MuleSoft job synchronises Account data into Salesforce every
15 minutes. The data is already enriched and validated upstream. The org's
Account trigger should not re-derive territory or fire outbound webhooks.

**Problem:** A common wrong pattern is `if (UserInfo.getUserId() == '0051x...')`
hardcoded in the trigger. This breaks across sandboxes, hides the dependency,
and cannot be governed.

**Solution:**

1. Create Custom Permission `Bypass_Triggers` (or reuse the canonical
   `TriggerControl_BypassAll`).
2. Create Permission Set `Integration_User_Bypass` and grant the Custom
   Permission.
3. Assign the perm set to the integration user only.
4. The handler's `run()` already calls `TriggerControl.isActive(...)` —
   nothing else changes.

```apex
// In TriggerControl (canonical, already in templates/apex/TriggerControl.cls):
private static Boolean hasBypassAllPermission() {
    return FeatureManagement.checkPermission('TriggerControl_BypassAll');
}
```

**Why it works:** Permission is the right abstraction for "can this user
skip enrichment?" — not identity. Adding a second integration user later is
a perm-set assignment, not a code change.

---

## Example 3: Programmatic in-transaction bypass during a cascade update

**Context:** Closing an Opportunity should set the parent Account's
`Last_Won_Date__c` and `Tier__c`. The Opportunity service does that update
itself — but the Account trigger handler runs heavy territory and rollup
logic that should NOT fire for this internal cascade (it's already correct).

**Problem:** Without scoped bypass, the Account handler runs, re-derives
territory (slow), and may fire callouts. With a sloppy bypass (e.g. setting
a static `disable = true` and never restoring), a later unrelated DML in
the same transaction silently skips Account logic — a heisenbug.

**Solution:**

```apex
public with sharing class OpportunityWonService {
    public static void onWon(Set<Id> oppIds) {
        List<Account> accountsToUpdate = buildAccountUpdates(oppIds);

        try {
            TriggerControl.bypass('Account', 'AccountTriggerHandler');
            ApplicationLogger.info(
                'OpportunityWonService',
                'Programmatic bypass: AccountTriggerHandler for cascade update'
            );
            update accountsToUpdate;
        } finally {
            TriggerControl.restore('Account', 'AccountTriggerHandler');
        }
    }
}
```

**Why it works:** `try/finally` guarantees restore even if `update` throws.
Static state is scoped to this transaction. The audit log entry tells
post-incident reviewers why the Account trigger did not run for those rows.

---

## Anti-Pattern: Hardcoded user-id check

**What practitioners do:** Add `if (UserInfo.getUserId() == '0051x000...')`
inside the trigger to skip work for the integration user.

**What goes wrong:** The hardcoded ID is wrong in every sandbox. Adding a
second integration user requires a code change and a deployment. There is
no audit. Reviewers cannot tell what business rule the check encodes.

**Correct approach:** Custom Permission gated through
`FeatureManagement.checkPermission(...)`, assigned via Permission Set.
