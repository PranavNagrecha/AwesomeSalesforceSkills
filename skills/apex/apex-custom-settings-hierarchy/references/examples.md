# Examples — Apex Custom Settings Hierarchy

## Example 1: Feature Flag Resolution With Per-User Override

**Context:** A payment module has a beta "auto-retry failed charges" feature. Finance wants the org default to be OFF but enables it for their QA user and for the Integration Profile.

**Problem:** Practitioners write `getOrgDefaults()` — missing the user-level override — or check `s == null` and return before reading fields, which incorrectly treats "hierarchy settled, no field value set" as "setting not configured."

**Solution:**

```apex
public with sharing class PaymentRetryFlag {
    public static Boolean isEnabled() {
        PaymentFlags__c s = PaymentFlags__c.getInstance();
        return s != null && s.AutoRetryEnabled__c == true;
    }
}
```

And an admin sets:

- Org Default: `AutoRetryEnabled__c = false`
- Integration Profile override: `AutoRetryEnabled__c = true`
- QA user override: `AutoRetryEnabled__c = true`

**Why it works:** `getInstance()` resolves User → Profile → Org in that order. The `== true` (not `!= null`) coerces null to false safely, so missing configuration defaults to the safe off path.

---

## Example 2: Bulk-Seeding Per-User Overrides Without Hitting DML Limits

**Context:** A migration script enables a feature for 800 pilot users listed in a CSV.

**Problem:** A loop that does `insert new PerUserFlag__c(SetupOwnerId=u, Enabled__c=true);` hits 150 DML in one transaction.

**Solution:**

```apex
public with sharing class PilotEnablement {
    public static void enablePilot(Set<Id> pilotUserIds) {
        List<PerUserFlag__c> rows = new List<PerUserFlag__c>();
        for (Id u : pilotUserIds) {
            rows.add(new PerUserFlag__c(SetupOwnerId = u, Enabled__c = true));
        }
        upsert rows SetupOwnerId;
    }
}
```

**Why it works:** A single list upsert. `SetupOwnerId` is unique per tier, so `upsert` updates existing rows and inserts new ones in one DML statement. Handles up to 10,000 records per call.

---

## Example 3: Test That Exercises The Hierarchy

**Context:** A unit test needs to prove the resolution order is respected.

**Problem:** Practitioners set only the org default, see the value, and assume the feature works for all users.

**Solution:**

```apex
@IsTest
static void hierarchy_userBeatsProfileBeatsOrg() {
    insert new PaymentFlags__c(SetupOwnerId = UserInfo.getOrganizationId(),
                               AutoRetryEnabled__c = false);

    Profile admin = [SELECT Id FROM Profile WHERE Name = 'System Administrator' LIMIT 1];
    insert new PaymentFlags__c(SetupOwnerId = admin.Id, AutoRetryEnabled__c = true);

    System.assertEquals(true, PaymentRetryFlag.isEnabled(),
        'Profile override should beat org default');

    insert new PaymentFlags__c(SetupOwnerId = UserInfo.getUserId(),
                               AutoRetryEnabled__c = false);

    System.assertEquals(false, PaymentRetryFlag.isEnabled(),
        'User override should beat profile override');
}
```

**Why it works:** Each tier is asserted independently. The test exercises the real hierarchy instead of mocking the accessor.

---

## Anti-Pattern: Using Custom Settings For Deployable Configuration

**What practitioners do:** Store integration endpoint URLs, named-credential fallbacks, or retry caps in a List Custom Setting and "seed" production via a post-install script.

**What goes wrong:** Custom Setting *data* does not travel with metadata deploys. Each sandbox refresh wipes the values. Each production deploy requires a manual data-loader step that the release engineer forgets. Configuration drift between orgs is guaranteed.

**Correct approach:** Migrate to Custom Metadata Types. CMDTs deploy with the source and are packageable. Keep Custom Settings only for values admins legitimately change in production Setup UI.

---

## Anti-Pattern: Null-Checking The Record Instead Of The Field

**What practitioners do:**

```apex
if (PaymentFlags__c.getInstance() != null) { /* read fields */ }
```

**What goes wrong:** `getInstance()` **never** returns `null` for Hierarchy Custom Settings. The check always passes, including when no tier is configured. Fields are still `null`, so downstream field access causes `NullPointerException` on `.intValue()`.

**Correct approach:** Always null-check the specific field you're reading, or use safe navigation: `s?.MaxRetries__c != null`.
