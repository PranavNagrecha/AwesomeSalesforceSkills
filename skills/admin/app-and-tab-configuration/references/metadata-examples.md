# Metadata Examples — App and Tab Configuration

Deployable shapes for the three metadata types an app is actually made of: `CustomApplication` (the app),
`CustomTab` (each navigation item that is not a standard tab), and a `FlexiPage` of type `UtilityBar` (the
utility bar). Shapes are taken from the Metadata API Developer Guide (v62 PDF — `CustomApplication`
api_meta.txt L39621–40737, `CustomTab` L47248–47467, `FlexiPage` L66865–68023) and extended to one
worked Field Service example.

Two things this file deliberately does **not** own:

- **The custom-object tab itself.** `admin/object-creation-and-design` `references/metadata-examples.md`
  carries the `<customObject>true</customObject>` shape and the `motif` catalogue. The app below just
  references that tab by name.
- **Permission-set design.** `admin/permission-set-architecture` `references/metadata-examples.md` carries
  the full `PermissionSet` shape. The fragment in section 6 exists only to show the two elements that make
  an app and its tabs reachable.

## Where the files live

| Type | package.xml `<name>` | `<members>` syntax | Wildcard `*` | DX source file | API |
|---|---|---|---|---|---|
| `CustomApplication` | `CustomApplication` | app name; `standard__<Name>` for a standard app; `<ns>__<Name>` for a packaged one | **Supported** (L40734–40736) | `applications/Field_Service.app-meta.xml` | custom 10.0+, standard 30.0+ (L39635–39636) |
| `CustomTab` | `CustomTab` | tab name (for an object tab, the object API name) | **Supported** (L47465–47467) | `tabs/Parts_Lookup.tab-meta.xml` | 10.0+ (L47263) |
| `FlexiPage` (utility bar) | `FlexiPage` | Lightning page name | **Supported** (L68020–68022) | `flexipages/Field_Service_Utilities.flexipage-meta.xml` | `UtilityBar` type 38.0+ (L67084–67086) |

MDAPI folder names are `applications/` (suffix `.app`), `tabs/` (suffix `.tab`), and `flexipages/`
(suffix `.flexipage`) — L39628, L47258, L66897. The DX suffixes above add `-meta.xml`.

Both `CustomApplication` and `CustomTab` carry the same warning: "Retrieving a component of this metadata
type in a project makes the component appear in any Profile and PermissionSet components that are
retrieved in the same package" (L39630, L47260). That is the *retrieve* side of the same coupling that
section 6 handles on the *deploy* side.

---

## 1. Lightning app, standard navigation, five tabs, branded

`force-app/main/default/applications/Field_Service.app-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomApplication xmlns="http://soap.sforce.com/2006/04/metadata">
    <brand>
        <headerColor>#0B5CAB</headerColor>
        <shouldOverrideOrgTheme>true</shouldOverrideOrgTheme>
    </brand>
    <defaultLandingTab>Field_Ops_Home</defaultLandingTab>
    <description>Day-to-day app for field technicians: visits, the depot map, and parts lookup.</description>
    <formFactors>Large</formFactors>
    <formFactors>Small</formFactors>
    <isNavAutoTempTabsDisabled>false</isNavAutoTempTabsDisabled>
    <isNavPersonalizationDisabled>false</isNavPersonalizationDisabled>
    <label>Field Service</label>
    <navType>Standard</navType>
    <setupExperience>service</setupExperience>
    <tabs>Field_Ops_Home</tabs>
    <tabs>Field_Visit__c</tabs>
    <tabs>standard-Account</tabs>
    <tabs>Parts_Lookup</tabs>
    <tabs>Depot_Map</tabs>
    <uiType>Lightning</uiType>
    <utilityBar>Field_Service_Utilities</utilityBar>
</CustomApplication>
```

How to read it:

- **`tabs` is the navigation list**, one element per item, in display order — "The list of tabs included in
  this application" (L39767–39775). The element was named `tab` before API 42.0. There is no `navItems`
  element on `CustomApplication`.
- **Standard tabs take the `standard-` prefix** in API 13.0 and later: `standard-Account`, not `Account`
  (L39769–39775). The guide's own sample uses `standard-Feed`, `standard-File`, `standard-Account`,
  `standard-Case`, `standard-report`, `standard-Dashboard` (L40501–40510). Custom tabs are bare names.
- **`defaultLandingTab` is a separate field**, not "whatever is first in `tabs`" — "The fullName of a
  standard tab or custom tab that opens when this application is selected" (L39661–39663). The guide's
  standard-app sample uses `standard-home` (L40521). Omit it and the platform picks; state it and the
  landing page is a reviewed decision.
- **`navType` and `uiType` are both marked "Not updateable"** (L39719, L39782). `navType` is `Standard` or
  `Console`; `uiType` is `Lightning` (Lightning Experience) or `Aloha` (Salesforce Classic). A deploy that
  changes either value on an existing app does not convert the app — see `references/gotchas.md` Gotcha 5.
- **`formFactors` decides where the app appears.** `Large` = Lightning Experience desktop, `Small` = the
  Salesforce mobile app, `Medium` reserved, null = Salesforce Classic desktop (L39666–39685). `Small` is
  supported for Lightning apps only in API 47.0 and later. Drop `Small` and the app is desktop-only.
- **`brand.headerColor` is a hex string** and `shouldOverrideOrgTheme` decides whether the app's colours
  beat the org theme — "When false, the global theme for the org is used, even if the user has set a color
  scheme and logo" (L39885–39889). `brand.logo` (not used above) is "the optional reference to the image
  document for the application" (L39880).

  > UNVERIFIED (2026-09-04): the Metadata API guide says `logo` is a reference to an "image document" but
  > does not name the metadata type or the required asset format. Retrieve an already-branded app from the
  > target org and copy the exact `logo` / `logoVersion` values rather than authoring them.

- **`setupExperience`** is `all`, `essentials`, or `service`; null is equivalent to `all` (L39735–39745).
  The older `AllSetup` / `ServiceSetup` / `EssentialsSetup` values are deprecated.
- **`utilityBar` names a FlexiPage by developer name** (L39788–39795) — see section 4.
- **Not in this file: who can see the app.** `CustomApplication` has no visibility field at all. See
  section 6.

---

## 2. The non-object tabs

Only one of `auraComponent`, `customObject`, `flexiPage`, `lwcComponent`, `page`, `scontrol`, `url` may
carry a value on a single `CustomTab` (L47276–47285, repeated per field). `motif` is required on every tab
(L47362–47363).

### Lightning web component tab

`force-app/main/default/tabs/Parts_Lookup.tab-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomTab xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Search the parts catalogue by SKU or symptom.</description>
    <label>Parts Lookup</label>
    <lwcComponent>partsLookup</lwcComponent>
    <motif>Custom19: Wrench</motif>
</CustomTab>
```

### Lightning app page tab

`force-app/main/default/tabs/Field_Ops_Home.tab-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomTab xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Landing page for the Field Service app.</description>
    <flexiPage>Field_Ops_Home_Page</flexiPage>
    <label>Field Ops Home</label>
    <motif>Custom35: Microphone</motif>
</CustomTab>
```

### Web tab

`force-app/main/default/tabs/Depot_Map.tab-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomTab xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Depot and stock-location map, hosted by Logistics.</description>
    <frameHeight>600</frameHeight>
    <hasSidebar>false</hasSidebar>
    <label>Depot Map</label>
    <motif>Custom78: Map</motif>
    <url>https://depots.example.com/map</url>
    <urlEncodingKey>UTF-8</urlEncodingKey>
</CustomTab>
```

How to read all three:

- **`label` is documented as "The label of the tab, for web tabs only"** (L47341). A custom object tab
  takes its name from the object; for component and page tabs the fullName "is arbitrary" (L47311–47318)
  and the label is what users read.

  > UNVERIFIED (2026-09-04): the guide restricts `label` to web tabs, but every Lightning component tab and
  > Lightning page tab retrieved from a live org carries a `label`. The field is included above because a
  > component tab with no label has nothing to render in the nav bar. Retrieve one existing component tab
  > from the target org before assuming either way.

- **`frameHeight` is "Required for s-control and page tabs"** (L47319–47320) — it belongs on the web tab,
  not on the LWC or Lightning-page tab.
- **`urlEncodingKey` defaults to UTF-8** and only applies when the tab type is URL (L47437–47441).
- **`hasSidebar`** controls whether the tab shows the sidebar panel (L47335). It is a Salesforce Classic
  concept; leaving it `false` on a Lightning-only web tab is the safe default.
- **`splashPageLink`** (not used) points at a `HomePageComponent` used as an introductory splash page
  (L47424–47426).
- The custom-object tab `Field_Visit__c` is **not** shown here — see
  `admin/object-creation-and-design` `references/metadata-examples.md`, section "The tab".

---

## 3. Every navigation item, side by side

| `<tabs>` value | Backed by | File | Fails silently if |
|---|---|---|---|
| `Field_Ops_Home` | `CustomTab` → `flexiPage` | `tabs/Field_Ops_Home.tab-meta.xml` | the FlexiPage `Field_Ops_Home_Page` is not in the same deploy |
| `Field_Visit__c` | `CustomTab` → `customObject` | `tabs/Field_Visit__c.tab-meta.xml` | the object exists but nobody created the tab |
| `standard-Account` | standard tab | none | the `standard-` prefix is dropped |
| `Parts_Lookup` | `CustomTab` → `lwcComponent` | `tabs/Parts_Lookup.tab-meta.xml` | the LWC does not expose `lightning__Tab` as a target |
| `Depot_Map` | `CustomTab` → `url` | `tabs/Depot_Map.tab-meta.xml` | the URL host blocks framing |

---

## 4. The utility bar is a FlexiPage, not part of the app file

`force-app/main/default/flexipages/Field_Service_Utilities.flexipage-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlexiPage xmlns="http://soap.sforce.com/2006/04/metadata">
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>label</name>
                    <type>decorator</type>
                    <value>History</value>
                </componentInstanceProperties>
                <componentInstanceProperties>
                    <name>width</name>
                    <type>decorator</type>
                    <value>340</value>
                </componentInstanceProperties>
                <componentName>forceSearch:historyUtilityItem</componentName>
            </componentInstance>
        </itemInstances>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>label</name>
                    <type>decorator</type>
                    <value>Notes</value>
                </componentInstanceProperties>
                <componentInstanceProperties>
                    <name>height</name>
                    <type>decorator</type>
                    <value>480</value>
                </componentInstanceProperties>
                <componentName>one:notesUtility</componentName>
            </componentInstance>
        </itemInstances>
        <name>utilityItems</name>
        <type>Region</type>
    </flexiPageRegions>
    <masterLabel>Field Service Utilities</masterLabel>
    <template>
        <name>flexipage:utilityBarTemplateDesktop</name>
    </template>
    <type>UtilityBar</type>
</FlexiPage>
```

How to read it:

- **`type` is `UtilityBar`** — "A Lightning page used as the utility bar in Lightning Experience apps",
  available in API 38.0 and later (L67084–67086). The app then names this page in its own `<utilityBar>`
  element (L39788).
- **`<type>decorator</type>` on a `componentInstanceProperties` entry is the utility-bar-specific escape
  hatch.** The guide is explicit: the decorator "can apply more capabilities to the component when it
  renders on a specific page… for example, you can configure a component decorator around a component on
  the Lightning Experience utility bar to set the component's height or width when opened. **The UtilityBar
  is the only page type that supports component decorators**" (L67353–67366). That is where panel width,
  panel height, and the utility's own label live — not on the app.
- **A `flexiPageRegions` entry of `type` `Background` holds utility items that are not visible in the UI**,
  and the guide notes it is "Supported for utility bars only" (L67288–67292). Use it for a utility that
  must run without a button, such as a telephony listener.
- `masterLabel` and `template` are both required on any FlexiPage (L67210, L67230).

  > UNVERIFIED (2026-09-04): the template name `flexipage:utilityBarTemplateDesktop`, the region name
  > `utilityItems`, and the component names `forceSearch:historyUtilityItem` and `one:notesUtility` are not
  > published in the Metadata API Developer Guide, which documents the FlexiPage *structure* but not the
  > catalogue of templates or standard utility components. Retrieve the utility bar of an existing app
  > (`sf project retrieve start --metadata FlexiPage:<Name>`) and copy the exact strings before deploying
  > a hand-authored one.

---

## 5. Console variant: the same tabs, opened differently

`force-app/main/default/applications/Field_Service_Console.app-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomApplication xmlns="http://soap.sforce.com/2006/04/metadata">
    <brand>
        <headerColor>#0B5CAB</headerColor>
        <shouldOverrideOrgTheme>true</shouldOverrideOrgTheme>
    </brand>
    <defaultLandingTab>standard-home</defaultLandingTab>
    <description>Dispatcher console: visits opened as workspace tabs, the account as a subtab.</description>
    <formFactors>Large</formFactors>
    <isNavTabPersistenceDisabled>false</isNavTabPersistenceDisabled>
    <label>Field Service Console</label>
    <navType>Console</navType>
    <tabs>standard-Account</tabs>
    <tabs>Field_Visit__c</tabs>
    <tabs>standard-Case</tabs>
    <uiType>Lightning</uiType>
    <utilityBar>Field_Service_Utilities</utilityBar>
    <workspaceConfig>
        <mappings>
            <tab>standard-Account</tab>
        </mappings>
        <mappings>
            <fieldName>Account__c</fieldName>
            <tab>Field_Visit__c</tab>
        </mappings>
        <mappings>
            <fieldName>AccountId</fieldName>
            <tab>standard-Case</tab>
        </mappings>
    </workspaceConfig>
</CustomApplication>
```

How to read it:

- **`fieldName` is what makes a record a subtab.** "The name of the field that specifies the primary tab in
  which to display tab as a subtab. **If not specified, tab opens as a primary tab**" (L40044–40047). Above,
  Account opens as its own workspace tab; a Field Visit opens as a subtab of the Account named by
  `Field_Visit__c.Account__c`; a Case opens as a subtab of `Case.AccountId`.
- **A mapping is required for each tab**: `AppWorkspaceConfig.mappings` is "Required for each tab specified
  in the CustomApplication" (L40028–40032, L40038–40041). A console tab with no mapping is the most common
  reason records open in the wrong place.
- **`isNavTabPersistenceDisabled`** applies only to console apps: true clears workspace tabs on each new
  console session (L39697–39701).
- `isServiceCloudConsole` stays absent. It "Indicates if the application is a Salesforce Classic console
  app. For Lightning Experience console apps, this field is null and the `navType` field is set to
  `Console`" (L39711–39715). Setting it on a Lightning app is the Classic shape, not this one.
- The `consoleConfig` / `preferences` blocks in the guide's console sample (L40527–40725) are the
  **Salesforce Classic** console shape (`AppPreferences` "Represents the preferences for a Salesforce
  Classic console app", L40007). Do not copy them into a Lightning console app.
- Deeper console layout work — split view, workspace behaviour, keyboard shortcuts — belongs to
  `admin/service-console-configuration`.

---

## 6. Nothing above makes the app visible

`CustomApplication` and `CustomTab` carry no visibility field. Access lives in `Profile` or `PermissionSet`.

`force-app/main/default/permissionsets/Field_Technician.permissionset-meta.xml` (excerpt — the surrounding
`PermissionSet` element is shown so the fragment parses on its own; the full shape is in
`admin/permission-set-architecture`)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Field Technician</label>
    <applicationVisibilities>
        <application>Field_Service</application>
        <visible>true</visible>
    </applicationVisibilities>
    <tabSettings>
        <tab>Field_Visit__c</tab>
        <visibility>Visible</visibility>
    </tabSettings>
    <tabSettings>
        <tab>Parts_Lookup</tab>
        <visibility>Visible</visibility>
    </tabSettings>
    <tabSettings>
        <tab>Depot_Map</tab>
        <visibility>Available</visibility>
    </tabSettings>
</PermissionSet>
```

- `PermissionSetApplicationVisibility` has exactly two required fields, `application` and `visible`
  (L94903–94910). The profile equivalent, `ProfileApplicationVisibility`, adds a required `default` flag —
  "Only one app per profile can be set to true" (L97897–97907).
- `tabSettings.visibility` takes `Visible`, `Available`, or `None` (L95149–95161). `Visible` puts the tab in
  the app; `Available` puts it only on the All Tabs page, where the user has to add it themselves; `None`
  hides it everywhere. The profile equivalent uses different words for the same three states —
  `DefaultOn`, `DefaultOff`, `Hidden` (L98250–98266).
- The `tab` value is the tab's own name — `Field_Visit__c` for the object tab, `Parts_Lookup` for the LWC
  tab. The guide's permission-set sample shows `<tab>Job_Request__c</tab>` (L95241–95244).

---

## 7. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Field_Service</members>
        <members>Field_Service_Console</members>
        <name>CustomApplication</name>
    </types>
    <types>
        <members>Field_Ops_Home</members>
        <members>Depot_Map</members>
        <members>Parts_Lookup</members>
        <members>Field_Visit__c</members>
        <name>CustomTab</name>
    </types>
    <types>
        <members>Field_Service_Utilities</members>
        <members>Field_Ops_Home_Page</members>
        <name>FlexiPage</name>
    </types>
    <types>
        <members>Field_Technician</members>
        <name>PermissionSet</name>
    </types>
    <version>62.0</version>
</Package>
```

All four types support the `*` wildcard (L40734–40736, L47465–47467, L68020–68022, and PermissionSet).
Wildcarding `CustomApplication` pulls standard apps too — in API 29.0 and earlier it returned only custom
apps (L40415–40417). To name a standard app explicitly, prefix it: `standard__Chatter` (L40428–40434). For a
packaged app, prefix the namespace: `myInstalledPackageNS__PackageApp` (L40437–40444).

---

## 8. Retrieve and deploy

```bash
# Pull the existing app before editing it — this is also how you harvest real
# utility-bar template and component names (section 4).
sf project retrieve start --metadata CustomApplication:Field_Service --target-org my-sandbox
sf project retrieve start --metadata FlexiPage:Field_Service_Utilities --target-org my-sandbox

python3 skills/admin/app-and-tab-configuration/scripts/check_app_and_tab_configuration.py \
  --manifest-dir force-app/main/default

sf project deploy start --manifest manifest/package.xml --target-org my-sandbox --dry-run
sf project deploy start --manifest manifest/package.xml --target-org my-sandbox
```

Order inside one package matters, and a single `sf project deploy start` resolves it:

1. `CustomTab`, and the `FlexiPage` any `flexiPage` tab points at.
2. The `FlexiPage` of type `UtilityBar` — the app's `<utilityBar>` is a reference, not a definition.
3. `CustomApplication`.
4. `PermissionSet` / `Profile` — `applicationVisibilities` and `tabSettings` cannot reference an app or tab
   that does not exist yet.

Splitting these across separate deployments fails at whichever step runs first without its dependency.

One deletion does not work this way at all: "You can't delete custom app ProfileActionOverrides by
deploying with destructiveChange.xml" — retrieve the app, remove the `<content>` row inside
`<profileActionOverrides>`, change that section's `<type>` to `default`, and redeploy, using a fresh
retrieve each time (L40398–40407).

---

## 9. Verify after deploy

Setup check, in order:

1. **Setup → Apps → App Manager** — both apps are listed, App Type reads *Lightning*, and Visible in
   Lightning is checked. Confirm the Developer Name matches what was deployed.
2. **Setup → Apps → App Manager → App Launcher (App Menu)** — the app is not sorted into *Hidden*. This is
   an org-wide toggle independent of any profile or permission set.
3. **Setup → User Interface → Tabs** — each custom tab exists under the right heading (Custom Object Tabs /
   Web Tabs / Lightning Component Tabs).
4. **Log in as a target user, not as the admin.** Open the App Launcher, open the app, and count the
   navigation items against `<tabs>`.

Then confirm from the platform side. `AppDefinition`, `TabDefinition`, and `AppTabMember` are all API 43.0+
and all return only what the *running user* can access (object_reference.txt L34140–34143, L277676–277678,
L36689–36691) — which makes them the fastest honest answer to "can this user see the app?" when run
through a target user's session.

```sql
SELECT DurableId, DeveloperName, Label, NavType, UiType, UtilityBar,
       IsSmallFormFactorSupported, IsLargeFormFactorSupported, IsNavPersonalizationDisabled
FROM AppDefinition
WHERE DeveloperName IN ('Field_Service', 'Field_Service_Console')
```

```sql
SELECT AppDefinition.DeveloperName, TabDefinition.Name, TabDefinition.Label,
       TabDefinition.IsCustom, TabDefinition.IsAvailableInLightning,
       TabDefinition.IsAvailableInMobile, SortOrder, WorkspaceDriverField
FROM AppTabMember
WHERE AppDefinition.DeveloperName = 'Field_Service'
ORDER BY SortOrder
```

- `AppTabMember.SortOrder` is "The number used to sort this tab in the application" and
  `WorkspaceDriverField` "Refers to the workspace mapping in the CustomApplication Metadata API object"
  (object_reference.txt L36728–36757) — so the console mapping from section 5 is verifiable without
  re-retrieving the app.
- `TabDefinition.IsAvailableInMobile` is the honest check for "will the technician see this on a phone",
  and `IsAvailableInLightning` for the Classic-versus-Lightning split (object_reference.txt L277717–277730).
- Zero rows from either query run as a target user means the visibility work in section 6 did not land —
  both objects return "only the tabs that the current user has access to" / "Metadata is returned only for
  apps that the current user can access".

The org-wide App Launcher toggle is queryable separately, and `IsVisible` is the only updateable field on
it (object_reference.txt L34561–34562, L34699–34704):

```sql
SELECT ApplicationId, Label, Type, IsVisible, IsAccessible, SortOrder FROM AppMenuItem ORDER BY SortOrder
```
