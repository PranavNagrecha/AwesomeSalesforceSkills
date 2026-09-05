# Examples — Custom Metadata Types And Settings

## Example 1: Multi-Org Feature Flag Using Custom Metadata Type

**Context:** A development team is rolling out a redesigned checkout flow incrementally. They need a feature flag that is off in sandbox, on in UAT, and can be turned on in production without a code deployment. The flag must also be consistent — every user in a given org sees the same behavior.

**Problem:** The first attempt stores the flag in a Custom Setting. When the team deploys to UAT, the definition and its fields deploy but the record value is blank — `getInstance()` hands back an object whose `Is_Enabled__c` is null, so the flag reads as off without anything failing. The flag is effectively off in every new org until someone manually sets it in Setup. Production deployments require an extra manual step after every release, causing incidents when the step is forgotten.

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

In Flow, use a Get Records element: Object = `Feature_Flag__mdt`, filter `DeveloperName = New_Checkout_Flow`. It returns the same deployed value regardless of which user triggers the flow. UNVERIFIED (2026-09-05): the zero-SOQL guarantee is grounded for Apex transactions in the App Limits Cheat Sheet; the extracted guides make no equivalent statement about Flow Get Records.

**Why it works:** The flag value travels with the release. There is no manual post-deploy step and no org-specific drift, and custom metadata records can be queried without limit inside a single Apex transaction. The `DeveloperName` key is stable across all orgs.

---

## Example 2: Per-Profile Alert Threshold Using Hierarchical Custom Setting

**Context:** A sales operations team needs Case alert thresholds to be different for Sales Reps (low threshold, many alerts), Sales Managers (medium), and System Admins (no alerts). Individual top performers also want personal thresholds that override the profile default.

**Problem:** The first attempt uses a Custom Metadata Type with separate records for each profile. The logic that picks the right record requires querying the running user's profile ID and matching it against CMT records. User-level overrides require another query and comparison layer. The code grows complex and the admin cannot manage overrides without a deployment.

**Solution:**

Create a `Case_Alerts__c` Hierarchical Custom Setting with a field `Alert_Threshold__c` (Number). Set org default to 20. Set profile-level records for the Sales Rep and Sales Manager profiles. Let individual users set their own record through a Setup menu if given permissions.

```apex
public with sharing class CaseAlertService {
    private static final Integer FALLBACK = 20;

    // getInstance() with no args resolves User > Profile > Org Default per field.
    // It never returns null: an unseeded org yields an object with empty fields,
    // so the guard belongs on the field.
    public static Integer getAlertThreshold() {
        Case_Alerts__c settings = Case_Alerts__c.getInstance();
        return settings.Alert_Threshold__c == null
            ? FALLBACK
            : (Integer) settings.Alert_Threshold__c;
    }

    // Use when running in batch or trigger context and the target user differs
    // from UserInfo.getUserId(). getValues(userId) would be wrong here: it returns
    // only the user-level row and nulls anything set at profile or org level.
    public static Integer getAlertThresholdFor(Id userId) {
        Case_Alerts__c settings = Case_Alerts__c.getInstance(userId);
        return settings.Alert_Threshold__c == null
            ? FALLBACK
            : (Integer) settings.Alert_Threshold__c;
    }
}
```

Setting the org default during post-deploy setup — `SetupOwnerId` has to be assigned, because the object `getOrgDefaults()` hands back for an unseeded org has neither an Id nor an owner:

```apex
Case_Alerts__c orgDefault = Case_Alerts__c.getOrgDefaults();
orgDefault.SetupOwnerId = UserInfo.getOrganizationId();
orgDefault.Alert_Threshold__c = 20;
upsert orgDefault;
```

What the three levels actually resolve to, given an org default of 20, a Sales Rep profile row of 5, and a user row of 1 for the rep Dana:

| Caller / call | Returns | Why |
|---|---|---|
| Dana → `getInstance()` | 1 | user row wins |
| A Sales Rep with no user row → `getInstance()` | 5 | profile row merges down |
| A System Admin → `getInstance()` | 20 | no profile row, so the org default |
| Any caller → `getOrgDefaults()` | 20 | the org row, ignoring who is running |
| Any caller → `getValues(danaId)` | 1 | Dana's row only — a field she has not set reads null |

**Why it works:** Hierarchical resolution is built into the platform and merges field by field, so a value set only at the org level still reaches a user who has their own row. No custom matching logic is needed. Admins manage profile and user overrides in Setup without a deployment. The definition deploys; the values are set by a post-deploy script run once per org.

---

## Anti-Pattern: Storing Per-User Preferences In Custom Metadata

**What practitioners do:** They model per-user preferences (display format, default record type, notification frequency) as Custom Metadata records, creating one record per user with the user's ID or name as part of the `DeveloperName`. They update these records in production when user preferences change.

**What goes wrong:** CMT records are metadata, not user data. Each change to a preference becomes a metadata deployment. The org accumulates hundreds or thousands of CMT records, approaching the 200-record-per-type limit or creating confusion in source control. More importantly, preferences now require a developer or admin to edit metadata and track it in git — a wildly over-engineered solution for user preferences.

**Correct approach:** Use Hierarchical Custom Settings for per-user overrides. The platform is purpose-built for this: `SetupOwnerId` can be a User ID, and the record is editable in Setup or via DML without a deployment. For more complex user preferences that need reporting or bulk management, use a Custom Object.

Concretely, the CMT-per-user design collapses into three rows of ordinary data:

```sql
-- What the per-user CMT design tries to express, done as custom setting rows.
-- Run this after seeding to prove each level landed on the owner you intended.
SELECT SetupOwnerId, SetupOwner.Name, SetupOwner.Type, Alert_Threshold__c
FROM Case_Alerts__c
ORDER BY SetupOwner.Type, SetupOwner.Name

-- SetupOwner.Type  SetupOwner.Name        Alert_Threshold__c
-- Organization     (the org)              20
-- Profile          Sales Rep               5
-- User             Dana Whitfield          1
```

Three rows an admin edits in Setup, versus one CMT record per user promoted through a deployment pipeline. `SetupOwner` is a polymorphic reference, which is why `SetupOwner.Type` is the field that tells you which level a row belongs to.
