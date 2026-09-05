# Examples — App and Tab Configuration

## Example 1: Onboarding a Field Service Team with a Focused App

**Context:** A company has deployed a custom object `Field_Visit__c` for their field technicians. The ops admin needs to give technicians a focused Lightning app with only Field Visits, Accounts, and Contacts — plus an Open CTI softphone utility bar.

**Problem:** Without a dedicated app, technicians land in the default Salesforce app and see dozens of irrelevant objects (Opportunities, Forecasts, Campaigns), causing confusion and low adoption.

**Solution:**

Step 1 — Create a custom tab for `Field_Visit__c`:
- Setup > Tabs > Custom Object Tabs > New
- Object: Field Visit
- Tab Style: pick an icon (e.g., hard hat or truck icon)
- Default Visibility: Default On (so the profile sees it automatically)
- Save

Step 2 — Create the Lightning app:
- Setup > App Manager > New Lightning App
- App Name: Field Service, Developer Name: Field_Service
- Navigation Items: Field Visits (the new tab), Accounts, Contacts
- Utility Bar: Add Open CTI Softphone, History
- User Profiles: Assign the Field Technician profile; check "Visible in App Launcher"
- Save

Step 3 — Validate, from the technician's session rather than the admin's:

```sql
-- Run in Developer Console / sf data query while logged in AS a Field Technician.
-- Both objects return only what the running user can access, so zero rows here is
-- the answer "this user cannot see it", not "the query found nothing".
SELECT DurableId, DeveloperName, Label, NavType,
       IsLargeFormFactorSupported, IsSmallFormFactorSupported
FROM AppDefinition
WHERE DeveloperName = 'Field_Service'

SELECT TabDefinition.Name, TabDefinition.Label,
       TabDefinition.IsAvailableInLightning, TabDefinition.IsAvailableInMobile, SortOrder
FROM AppTabMember
WHERE AppDefinition.DeveloperName = 'Field_Service'
ORDER BY SortOrder
```

Expected: one `AppDefinition` row, and three `AppTabMember` rows whose `SortOrder`
matches the navigation order the admin chose. A missing row is a missing
`tabSettings` entry, not a missing tab. Then confirm by eye:

- Log in as a Field Technician profile user
- Confirm "Field Service" appears in the App Launcher
- Confirm Field Visits, Accounts, Contacts appear in the nav bar
- Confirm the CTI softphone is visible in the utility bar

**Why it works:** Custom tabs are the bridge between custom objects and the navigation bar. Without the tab, `Field_Visit__c` cannot appear in any app's nav items list. Profile assignment to the app combined with "Visible in App Launcher" controls who sees the app in the waffle menu.

---

## Example 2: Migrating from a Classic App to a Lightning App

**Context:** An org still has a Classic app named "Sales Operations" assigned to the Sales Ops profile. As part of a Lightning Experience rollout, the admin needs to create an equivalent Lightning app.

**Problem:** Classic apps do not show in the App Launcher waffle menu when using Lightning Experience. Users on Lightning see a confusing fallback or the wrong app.

**Solution:**

1. In App Manager, identify all navigation items in the existing Classic app (note the tab list).
2. Create a New Lightning App:
   - Match the name ("Sales Operations") or give it a clear Lightning-era name.
   - Add the same navigation items. If Classic tabs were Visualforce tabs, confirm those Visualforce tabs also exist for Lightning Experience.
   - Configure a utility bar appropriate for the team (e.g., History, Notes).
3. Assign the Sales Ops profile with "Visible in App Launcher" checked.
4. Optionally, edit the original Classic app and uncheck "Visible in App Launcher" or remove the Sales Ops profile from it to avoid confusion.
5. Test by logging in as a Sales Ops profile user in Lightning Experience.

**Why it works:** Lightning Experience and Classic apps are separate metadata types. There is no automatic migration. Creating a parallel Lightning app ensures continuity while the org transitions.

---

## Anti-Pattern: Adding a Tab to the App Without Checking Profile Tab Settings

**What practitioners do:** Admin adds a custom tab to a Lightning app's navigation items, assigns the profile to the app, but the tab still doesn't appear for users.

**What goes wrong:** The user's profile has the tab set to "Tab Hidden" under Tab Settings. This is a profile-level hard block — it prevents the tab from appearing even if the app explicitly includes it. The App Manager configuration and the profile Tab Settings work independently; both must allow the tab.

**Correct approach:**
1. In Setup > Profiles > [Target Profile] > Tab Settings: verify the custom tab is set to "Default On" or "Default Off" (not "Tab Hidden").
2. "Default Off" means the tab is accessible but not pinned; users can still find it via the More menu.
3. "Default On" means the tab is pinned in the navigation bar by default.
4. Set the tab to at least "Default Off" for any tab you want users to be able to see.

The Setup labels and the metadata words for the same three states do not match, which
is why this is easy to get wrong in a deployment. In `Profile` metadata:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- excerpt: force-app/main/default/profiles/Field_Technician.profile-meta.xml
     Setup "Default On" = DefaultOn, "Default Off" = DefaultOff, "Tab Hidden" = Hidden.
     A PermissionSet spells the same three states Visible / Available / None. -->
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
    <custom>true</custom>
    <tabVisibilities>
        <tab>Field_Visit__c</tab>
        <visibility>DefaultOn</visibility>
    </tabVisibilities>
    <tabVisibilities>
        <tab>Depot_Map</tab>
        <visibility>DefaultOff</visibility>
    </tabVisibilities>
</Profile>
```

A tab left out of `tabVisibilities` entirely is not the same as `Hidden` — it is
"whatever the org already had", which is why a partial profile deploy can appear to do
nothing. Grant the tab in a permission set instead wherever you can; see
`admin/permission-set-architecture`.
