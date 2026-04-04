# Examples — Custom Metadata Types And Settings

## Example 1: Multi-Org Feature Flag Using Custom Metadata Type

**Context:** A development team is rolling out a redesigned checkout flow incrementally. They need a feature flag that is off in sandbox, on in UAT, and can be turned on in production without a code deployment. The flag must also be consistent — every user in a given org sees the same behavior.

**Problem:** The first attempt stores the flag in a Custom Setting. When the team deploys to UAT, the Custom Setting field definition deploys but the record value is blank. The flag is effectively off in every new org until someone manually sets it in Setup. Production deployments require an extra manual step after every release, causing incidents when the step is forgotten.

**Solution:**

Create a `Feature_Flag__mdt` Custom Metadata Type with fields `DeveloperName` (standard), `Is_Enabled__c` (Checkbox), and `Description__c` (Text). Create a record `New_Checkout_Flow` with `Is_Enabled__c = false` for sandbox and `Is_Enabled__c = true` for UAT. Commit both the type definition and records to source control. They deploy automatically.

```apex
public with sharing class CheckoutRouter {
    // Zero SOQL cost — platform serves this from metadata cache
    private static Feature_Flag__mdt getFlag(String developerName) {
        return [
            SELECT Is_Enabled__c
            FROM Feature_Flag__mdt
            WHERE DeveloperName = :developerName
            LIMIT 1
        ];
    }

    public static Boolean isNewCheckoutEnabled() {
        try {
            return getFlag('New_Checkout_Flow').Is_Enabled__c;
        } catch (QueryException e) {
            return false; // safe default if record missing
        }
    }
}
```

In Flow, use a Get Records element: Object = `Feature_Flag__mdt`, filter `DeveloperName = New_Checkout_Flow`. This costs zero SOQL queries and returns the same deployed value regardless of which user triggers the flow.

**Why it works:** The flag value travels with the release. There is no manual post-deploy step, no org-specific drift, and no SOQL governor consumption. The `DeveloperName` key is stable across all orgs.

---

## Example 2: Per-Profile Alert Threshold Using Hierarchical Custom Setting

**Context:** A sales operations team needs Case alert thresholds to be different for Sales Reps (low threshold, many alerts), Sales Managers (medium), and System Admins (no alerts). Individual top performers also want personal thresholds that override the profile default.

**Problem:** The first attempt uses a Custom Metadata Type with separate records for each profile. The logic that picks the right record requires querying the running user's profile ID and matching it against CMT records. User-level overrides require another query and comparison layer. The code grows complex and the admin cannot manage overrides without a deployment.

**Solution:**

Create a `Case_Alerts__c` Hierarchical Custom Setting with a field `Alert_Threshold__c` (Number). Set org default to 20. Set profile-level records for the Sales Rep and Sales Manager profiles. Let individual users set their own record through a Setup menu if given permissions.

```apex
public with sharing class CaseAlertService {
    // getInstance() with no args resolves: User > Profile > Org Default automatically
    public static Integer getAlertThreshold() {
        Case_Alerts__c settings = Case_Alerts__c.getInstance();
        if (settings == null || settings.Alert_Threshold__c == null) {
            return 20; // safe fallback
        }
        return (Integer) settings.Alert_Threshold__c;
    }

    // Use when running in batch or trigger context and the target user differs
    // from UserInfo.getUserId()
    public static Integer getAlertThresholdFor(Id userId) {
        Case_Alerts__c settings = Case_Alerts__c.getInstance(userId);
        if (settings == null || settings.Alert_Threshold__c == null) {
            return 20;
        }
        return (Integer) settings.Alert_Threshold__c;
    }
}
```

Setting the org default during post-deploy setup:

```apex
Case_Alerts__c orgDefault = Case_Alerts__c.getOrgDefaults();
orgDefault.Alert_Threshold__c = 20;
upsert orgDefault;
```

**Why it works:** Hierarchical resolution is built into the platform. No custom matching logic is needed. Admins can manage profile and user overrides directly in Setup without a deployment. The field definition deploys; the values are set via a post-deploy script run once per org.

---

## Anti-Pattern: Storing Per-User Preferences In Custom Metadata

**What practitioners do:** They model per-user preferences (display format, default record type, notification frequency) as Custom Metadata records, creating one record per user with the user's ID or name as part of the `DeveloperName`. They update these records in production when user preferences change.

**What goes wrong:** CMT records are metadata, not user data. Each change to a preference becomes a metadata deployment. The org accumulates hundreds or thousands of CMT records, approaching the 200-record-per-type limit or creating confusion in source control. More importantly, preferences now require a developer or admin to edit metadata and track it in git — a wildly over-engineered solution for user preferences.

**Correct approach:** Use Hierarchical Custom Settings for per-user overrides. The platform is purpose-built for this: `SetupOwnerId` can be a User ID, and the record is editable in Setup or via DML without a deployment. For more complex user preferences that need reporting or bulk management, use a Custom Object.
