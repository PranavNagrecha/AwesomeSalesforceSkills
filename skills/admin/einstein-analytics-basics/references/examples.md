# Examples: Einstein Analytics Basics

---

## Example: Standard Reports Are Still Enough

**Scenario:** Sales leadership wants a weekly pipeline dashboard by owner, stage, and close month. The data is entirely in Opportunities and needs to reflect today's numbers.

**Decision:** Use Salesforce Reports and Dashboards.

**Why:**
- real-time data matters
- no complex transformation is required
- business users may want to tweak filters themselves
- no extra CRM Analytics licenses are needed

**What would be wasteful:** creating a CRM Analytics dataset just to show pipeline by rep.

---

## Example: CRM Analytics Is the Better Fit

**Scenario:** A support organization needs a service dashboard that blends Cases, Entitlements, milestone timing, reopen behavior, and trend calculations over a large history window.

**Decision:** Use CRM Analytics.

**Why:**
- multiple transformed metrics are needed
- historical analysis is heavier than standard reports handle well
- executives want mobile-friendly dashboards with richer visual design

**Non-negotiables:**
- define refresh cadence
- confirm license coverage
- design dataset security explicitly

---

## Example: Tableau, Not CRM Analytics

**Scenario:** Operations wants a dashboard combining Salesforce pipeline, ERP backlog, product usage telemetry, and finance forecasts.

**Decision:** Evaluate Tableau or the enterprise BI platform.

**Why:** This is a cross-system analytics problem, not just a Salesforce dashboard problem.

**Admin takeaway:** Do not use CRM Analytics as a political compromise when the real need is enterprise BI.

---

## Example 2: Enable CRM Analytics And Grant View Access, As A Setup Procedure And As Deployable Metadata

**Scenario:** The service dashboard from the second example above is approved for 40 support managers. The admin must enable CRM Analytics, give the managers view access, and keep the access in source control so it survives a disable and re-enable.

**Step 1: check licences before promising access.** Permission set licences in the org:

```soql
SELECT MasterLabel, DeveloperName, Status, TotalLicenses, UsedLicenses, ExpirationDate
FROM PermissionSetLicense
WHERE MasterLabel LIKE '%Analytics%'
```

User licences held by the audience (the CRM Analytics permission set licence pairs only with Lightning Platform, Full CRM, Salesforce Platform, and Salesforce Platform One user licences):

```soql
SELECT Name, MasterLabel, Status, TotalLicenses, UsedLicenses
FROM UserLicense
```

**Step 2: the Setup procedure** (Setup Guide, Basic and Advanced CRM Analytics Platform Setup):

1. Setup > Quick Find: **Analytics** > **Getting Started** > **Enable CRM Analytics**.
2. Setup > **Users** > **Permission Sets** > **New**. Label: `View CRM Analytics`. License: the CRM Analytics permission set licence, so assignment auto-assigns it. **Save**.
3. **System Permissions** > **Edit**. Select **Use CRM Analytics** (and **Upload External Data to CRM Analytics** only if managers upload CSV files). **Save**.
4. **Manage Assignments** > **Add Assignments**, select the 40 managers, **Assign**. Fix any user the result page reports as failed.
5. In Analytics Studio, share the app with the managers as **Viewer**: "if a user has the 'Use CRM Analytics' permission, the user must also have Viewer access on an app to view its datasets, lenses, and dashboards."

**Step 3: the same settings as deployable metadata.** `force-app/main/default/settings/Analytics.settings-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AnalyticsSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableInsights>true</enableInsights>
    <canAccessAnalyticsViaAPI>true</canAccessAnalyticsViaAPI>
</AnalyticsSettings>
```

`enableInsights` "Indicates whether CRM Analytics is enabled"; both fields appear in the Metadata API sample for `AnalyticsSettings`, stored in `Analytics.settings`.

`force-app/main/default/permissionsets/View_CRM_Analytics.permissionset-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>View CRM Analytics apps shared with the user. Use CRM Analytics only.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <label>View CRM Analytics</label>
    <userPermissions>
        <enabled>true</enabled>
        <name>InsightsAppUser</name>
    </userPermissions>
</PermissionSet>
```

UNVERIFIED (2026-10-03): the API name `InsightsAppUser` for "Use CRM Analytics" is not in any fetched source; the Setup Guide gives only the Setup labels. This file omits `<license>`, which matches choosing "--None--" in Step 2; the Setup Guide says users then need the permission set licence assigned manually before the permission set. Before deploying, build the permission set once in Setup (Step 2), retrieve it with `sf project retrieve start --metadata PermissionSet:View_CRM_Analytics`, and copy the retrieved `userPermissions` name and any `license` value into this file.

**Manifest members** (`manifest/package.xml`):

| Component | Type | `package.xml` member form |
|---|---|---|
| CRM Analytics enablement | `AnalyticsSettings` (settings type) | `<members>Analytics</members><name>Settings</name>` |
| View access | `PermissionSet` | `<members>View_CRM_Analytics</members><name>PermissionSet</name>` |

The `Analytics` member under `Settings` is the Metadata API's own example manifest for `AnalyticsSettings`.

**Why it works:** the licence check runs before anyone is promised a dashboard, the Setup steps match the documented order, and the deployable files mean a disable and re-enable (which strips permissions from every CRM Analytics permission set) is a redeploy rather than a rebuild.

