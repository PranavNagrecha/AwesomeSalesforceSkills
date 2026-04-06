# Examples — Feature Flags And Kill Switches

## Example 1: Emergency Kill Switch for an External Integration Callout

**Context:** An org has a trigger-invoked callout to an external ERP system that runs on every Opportunity close. The ERP vendor announces emergency maintenance with 30 minutes notice. The team needs to disable the callout instantly without a code deployment.

**Problem:** Without a kill switch, the only options are (a) deploy a code change setting a boolean to `false`, which takes 10-20 minutes with tests, or (b) deactivate the trigger entirely, which disables all trigger logic — not just the callout.

**Solution:**

```apex
// FeatureFlag__mdt with records: ERP_Sync (IsEnabled__c = true)

public class FeatureFlags {
    public static Boolean isEnabled(String featureName) {
        FeatureFlag__mdt flag = FeatureFlag__mdt.getInstance(featureName);
        return flag != null && flag.IsEnabled__c;
    }
}

// In the trigger handler:
public class OpportunityTriggerHandler {
    public void afterUpdate(List<Opportunity> newList, Map<Id, Opportunity> oldMap) {
        if (!FeatureFlags.isEnabled('ERP_Sync')) {
            return; // Kill switch is off — skip integration entirely
        }

        List<Opportunity> closedOpps = new List<Opportunity>();
        for (Opportunity opp : newList) {
            if (opp.StageName == 'Closed Won' && oldMap.get(opp.Id).StageName != 'Closed Won') {
                closedOpps.add(opp);
            }
        }
        if (!closedOpps.isEmpty()) {
            ERPSyncService.enqueueSync(closedOpps);
        }
    }
}
```

**Why it works:** The admin navigates to Setup > Custom Metadata Types > FeatureFlag > ERP_Sync and unchecks `IsEnabled__c`. The CMDT record update takes effect within seconds (after a brief metadata deployment). No code deploy, no test execution, no trigger deactivation. The rest of the trigger logic continues running normally. When the vendor maintenance ends, the admin re-checks the box.

---

## Example 2: Gradual Rollout of a New Lightning Experience via Custom Permission

**Context:** The team built a new Apex-driven checkout flow for a community portal. They want to roll it out to 50 internal testers first, then expand to all community users over two weeks.

**Problem:** A hard-coded boolean or org-wide CMDT flag only supports all-or-nothing. The team needs per-user control.

**Solution:**

```apex
// Custom Permission: BetaNewCheckout
// Permission Set: Beta - New Checkout (contains the Custom Permission)
// Assigned to 50 pilot users

public class CheckoutController {
    @AuraEnabled
    public static CheckoutResult processCheckout(Id cartId) {
        if (FeatureManagement.checkPermission('BetaNewCheckout')) {
            return NewCheckoutService.process(cartId);
        } else {
            return LegacyCheckoutService.process(cartId);
        }
    }
}
```

**Why it works:** The permission set acts as the feature gate. Adding users to the beta is a permission set assignment — an admin action requiring no code. When the beta succeeds, the team either assigns the permission set to all users via a public group or removes the `if` check entirely. The Custom Permission is also available in LWC via `@wire` with `hasPermission`, enabling UI-level gating without Apex.

---

## Example 3: Per-Profile Debug Logging Flag via Hierarchical Custom Setting

**Context:** A production org experiences intermittent data quality issues in a batch job. The team needs to enable verbose debug logging for the batch process, but only for the System Administrator profile, without flooding logs for all users.

**Problem:** Changing `LoggingLevel` in debug logs is transient and expires. A CMDT flag is org-wide. The team needs profile-level control.

**Solution:**

```apex
// Hierarchical Custom Setting: DebugFlags__c
// Field: VerboseBatchLogging__c (Checkbox)
// Org default: false
// System Administrator profile override: true

public class AccountCleanupBatch implements Database.Batchable<SObject> {
    private Boolean verboseLogging;

    public AccountCleanupBatch() {
        this.verboseLogging = DebugFlags__c.getInstance().VerboseBatchLogging__c;
    }

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator('SELECT Id, Name FROM Account WHERE IsActive__c = false');
    }

    public void execute(Database.BatchableContext bc, List<Account> scope) {
        if (verboseLogging) {
            System.debug(LoggingLevel.INFO, 'Processing batch of ' + scope.size() + ' accounts');
        }
        // ... batch logic
    }

    public void finish(Database.BatchableContext bc) {
        if (verboseLogging) {
            System.debug(LoggingLevel.INFO, 'Batch complete');
        }
    }
}
```

**Why it works:** `DebugFlags__c.getInstance()` returns the most specific value for the running user — if there is a user-level override it wins, then profile-level, then org default. Since the batch runs as a specific user, only batches kicked off by System Administrators will produce verbose logs. The admin can flip the profile-level value via DML instantly, no deployment required.

---

## Anti-Pattern: Hard-Coding Feature Toggles as Apex Constants

**What practitioners do:** They create a class with `public static final Boolean ENABLE_ERP_SYNC = true;` and change it to `false` when they need to disable the feature.

**What goes wrong:** Changing a constant requires a code deployment, which in production means running all tests (minimum 75% coverage gate). During an outage, this can take 20+ minutes. In managed packages, the subscriber cannot change the constant at all.

**Correct approach:** Use a Custom Metadata Type flag with a centralized utility class. The flag value is metadata, not code, so it changes without a deployment. In managed packages, CMDT records can be subscriber-editable, giving customers control over the flag.
