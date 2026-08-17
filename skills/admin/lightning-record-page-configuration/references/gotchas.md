# Gotchas — Lightning Record Page Configuration

Non-obvious platform behaviours that cause real production problems when building and assigning Lightning pages.

## Gotcha 1: The `.flexipage` File Contains No Assignment, So Deploying It Alone Ships an Inert Page

**What happens:** A record page is built and activated in a sandbox, retrieved into source control, and deployed to production. The deploy succeeds — green, no warnings, `FlexiPage` listed as changed. Users open a record and see the old page. Nothing in the deploy output hints at the problem, because nothing failed.

**Why:** The `FlexiPage` metadata type has no field that names a profile, an app, a record type, or a form factor. Its full field list is `description`, `events`, `flexiPageRegions`, `masterLabel`, `pageTemplate`, `parentFlexiPage`, `platformActionlist`, `quickActionList`, `sobjectType`, `template`, and `type` — eleven fields, none of them an audience. (`pageTemplate` is deprecated: the reference restricts it to API versions 33.0 through 38.0 and directs later versions to `template`.) Assignment lives in two other types entirely:

- Org default → an `ActionOverride` inside the object's `CustomObject` metadata, with `actionName` `View`, `type` `Flexipage`, `content` set to the page name, `formFactor` `Large`. (The reference lists the enum values lower-cased; retrieved `.object-meta.xml` files carry them capitalised, as in Salesforce's own `Property__c` sample.)
- App default and app + record type + profile → `AppActionOverride` and `AppProfileActionOverride` entries inside each `CustomApplication`.

Deploying `FlexiPage` transfers the page's contents and nothing about who sees it.

**How to avoid:** Put all three metadata types in the same manifest, and treat a manifest that names only `FlexiPage` as incomplete by definition.

```xml
<types><members>Opportunity_Record_Page</members><name>FlexiPage</name></types>
<types><members>Opportunity</members><name>CustomObject</name></types>
<types><members>Sales_Console</members><name>CustomApplication</name></types>
```

Change sets have the same trap under a friendlier name: adding the Lightning page component does not add the object or the app. After any promotion, open a record in the target org as a user from each profile in the assignment matrix — do not accept the deploy result as proof.

**Source:** Metadata API Developer Guide — FlexiPage, ActionOverride, CustomApplication.

---

## Gotcha 2: An App-Scoped Assignment Silently Outranks the Org Default

**What happens:** An admin sets a new record page as Org Default. Some users get it immediately. Others — often the largest, loudest team — keep seeing the previous page. Re-activating, clearing cache, and re-saving all change nothing, because the org default was never the assignment those users were resolving against.

**Why:** Assignment resolution is a specificity ladder, and app scope sits above org scope. The Metadata API reference for `CustomApplication` states it without hedging: *"When a user invokes the custom app, a matching ProfileActionOverride assignment takes precedence over existing overrides for the record page specified in ActionOverride."* An `AppProfileActionOverride` written months ago, for one profile, inside one app, keeps winning forever. It is stored inside the app's metadata, not the object's, so an admin looking at the object's Lightning Record Pages list has no reason to suspect it exists.

**When it occurs:** Most reliably in orgs with more than one Lightning app touching the same object — a console app plus a standard app is the classic pair — and in orgs where someone once used the Activation dialog's third tab to fix one team's page and never documented it.

**How to avoid:** Before changing an org default, enumerate every override that already exists. Retrieve the `CustomApplication` metadata for every app that exposes the object and read `profileActionOverrides`. A matching entry looks like this and is what you are hunting for:

```xml
<profileActionOverrides>
    <actionName>View</actionName>
    <content>Opportunity_Record_Page_Legacy</content>
    <formFactor>Large</formFactor>
    <pageOrSobjectType>Opportunity</pageOrSobjectType>  <!-- see the caveat below -->
    <profile>Sales_User</profile>
    <recordType>Opportunity.Enterprise</recordType>
    <type>Flexipage</type>
</profileActionOverrides>
```

**Watch `pageOrSobjectType` — and do not confuse the two subtypes that spell it the same way.** Two different blocks live inside a `CustomApplication`, and `pageOrSobjectType` means something different in each:

| Block | Subtype | What the reference says `pageOrSobjectType` holds |
|---|---|---|
| `<actionOverrides>` | `AppActionOverride` | *"The name of the sObject type being overridden. Valid values are standard and custom. This value must be standard-home when actionName is tab."* |
| `<profileActionOverrides>` | `AppProfileActionOverride` | *"Required. The name of the page being overridden. The only valid values are record-home and standard-home."* |

The app-level `<actionOverrides>` half is settled: the object API name is the documented value, and Salesforce's published `Dreamhouse.app-meta.xml` uses `<pageOrSobjectType>Property__c</pageOrSobjectType>` in exactly that block. That file contains **no** `profileActionOverrides` at all, so it is not evidence about the profile-scoped subtype in either direction.

The genuine conflict is confined to the `ProfileActionOverride` reference page contradicting itself: the field description restricts the value to `record-home` / `standard-home`, while the sample `<profileActionOverrides>` XML printed on that same page carries `<pageOrSobjectType>TestObj__c</pageOrSobjectType>` — an object API name. Nothing published resolves it. For a `profileActionOverrides` entry, take the value from a file retrieved out of the target org rather than from either half of the reference, and never let an agent generate this element from memory.

Delete stale entries rather than layering another assignment on top. Every rung you leave behind is a future incident.

**Source:** Metadata API Developer Guide — CustomApplication (`profileActionOverrides`), ProfileActionOverride.

---

## Gotcha 3: `formFactor` Is Part of the Assignment, and `Large` Does Not Mean "Everywhere"

**What happens:** A page is built, assigned, verified on a laptop, and shipped. Field users on the Salesforce mobile app see a completely different page — usually the previous one, sometimes the platform default. Nothing about the desktop configuration looks wrong, because nothing about it is wrong.

**Why:** `formFactor` is a field on the override, not on the page. The `ActionOverride` reference defines the values precisely: `Large` is the Lightning Experience desktop environment, `Small` is the Salesforce mobile app, and an absent or null `formFactor` means Salesforce Classic. Three different values, three independent assignments, one page. Assigning at `Large` says nothing at all about the phone.

**When it occurs:** Any org with a mobile user population, and specifically any migration where the desktop page was rebuilt but the mobile assignment was inherited from whatever existed before.

**How to avoid:** Treat form factor as a column in the assignment matrix, not a footnote. For each row, state whether it covers `Large`, `Small`, or both, and write the second override explicitly when both are needed — covering both is literally two overrides that differ in one element. Salesforce's own `Dreamhouse` sample app ships exactly that pair per object:

```xml
<!-- force-app/main/default/applications/Dreamhouse.app-meta.xml -->
<actionOverrides>
    <actionName>View</actionName>
    <comment>Action override created by Lightning App Builder during activation.</comment>
    <content>Property_Record_Page</content>
    <formFactor>Small</formFactor>
    <skipRecordTypeSelect>false</skipRecordTypeSelect>
    <type>Flexipage</type>
    <pageOrSobjectType>Property__c</pageOrSobjectType>
</actionOverrides>
<actionOverrides>
    <actionName>View</actionName>
    <comment>Action override created by Lightning App Builder during activation.</comment>
    <content>Property_Record_Page</content>
    <formFactor>Large</formFactor>
    <skipRecordTypeSelect>false</skipRecordTypeSelect>
    <type>Flexipage</type>
    <pageOrSobjectType>Property__c</pageOrSobjectType>
</actionOverrides>
```

When auditing an org, grep retrieved metadata for `<formFactor>` and count the distinct values per page — a page carrying only `Large` overrides has no mobile story, whatever the admin believes. The literal string `Action override created by Lightning App Builder during activation.` in a `<comment>` marks an override the Activation dialog wrote, which is the fastest way to separate builder-generated assignments from hand-authored ones during a cleanup.

**Source:** Metadata API Developer Guide — ActionOverride (`formFactor`), CustomApplication (`formFactors`); `trailheadapps/dreamhouse-lwc` `Dreamhouse.app-meta.xml` (verified 2026-08-15).

---

## Gotcha 4: `sobjectType` Cannot Be Changed After It Is Set

**What happens:** A record page is built against the wrong object — usually a near-namesake custom object in an org that has `Claim__c` and `Claim_Line__c`, or a page started from the wrong Setup entry point. The admin opens the page to repoint it and finds no control that does so. Editing the retrieved XML and redeploying fails rather than silently repointing it.

**Why:** The Metadata API reference marks `sobjectType` on `FlexiPage` as unchangeable once set (API 37.0 and later). The object association is identity, not configuration.

**When it occurs:** Most often on custom objects with similar names, and in orgs where record pages are cloned from an existing page as a starting point — the clone inherits the source page's object.

**How to avoid:** Confirm the object before the first save, and name the page after the object so the mismatch is visible in every list. Recovery is clone-and-rebuild: create a new page against the correct object, recreate the regions, then move every assignment across and delete the original. Budget for the assignments, not just the layout — the new page starts with zero overrides pointing at it, which puts you straight back into Gotcha 1.

**Source:** Metadata API Developer Guide — FlexiPage (`sobjectType`).

---

## Gotcha 5: API 49.0 and 53.0 Changed the File Shape, and Cross-Version Round Trips Corrupt Pages

**What happens:** A page retrieved from an older project or copied from an old blog post fails to deploy, or deploys and loses its Dynamic Forms fields. The error is about an unexpected element or a missing required field, and the XML looks superficially correct.

**Why:** Two breaking shape changes sit inside the same metadata type:

| API version | What changed | Effect on hand-written XML |
|---|---|---|
| 49.0 | `componentInstances` was **removed** from `FlexiPageRegion`; `itemInstances` replaced it | Pre-49.0 XML no longer parses into the current shape |
| 49.0 | Arrays moved from comma-separated `value` to `valueList` / `valueListItems` | A multi-value component property silently collapses to one literal string |
| 49.0 | `fieldInstance` introduced — Dynamic Forms has no representation before this | Retrieving at ≤48.0 drops the field placements entirely |
| 53.0 | `identifier` became **required** on `ComponentInstance` and `FieldInstance`, max 120 characters | Deploys of older files fail validation on every component |

**When it occurs:** Whenever the `sourceApiVersion` in `sfdx-project.json` lags the org, when a page is copied out of documentation written before Winter '21, or when a package built at an older version is retrofitted.

**How to avoid:** Never hand-edit a `.flexipage` sourced from an unknown API version. Retrieve the page fresh from the org at the project's current API version, diff against what you have, and edit the fresh copy. If a legacy file must be salvaged, add an `identifier` to every `componentInstance` and `fieldInstance`, convert `componentInstances` to `itemInstances`, and convert every comma-separated property value to a `valueList`.

**Source:** Metadata API Developer Guide — FlexiPage (FlexiPageRegion, ItemInstance, ComponentInstance, FieldInstance).

---

## Gotcha 6: The Tooling API Audit Query Fails in Two Predictable Ways

**What happens:** An admin writes a query to inventory every record page in the org and gets either zero rows or an error about querying too many records, then concludes the object is not queryable.

**Why:** Two separate constraints on the Tooling API `FlexiPage` object:

1. `SobjectType` is deprecated as of version 39.0; the reference directs callers to `EntityDefinitionId` instead, described as *"The name of the standard object or ID of the custom object that the Lightning page is associated with."* Note the asymmetry — a standard object filters by name, a custom object by ID. `WHERE EntityDefinitionId = 'Opportunity'` works; `WHERE EntityDefinitionId = 'Claim__c'` may not, and the object's `EntityDefinition` ID is the reliable filter for custom objects.
2. `FullName` and `Metadata` may only be queried when the result contains a single record. A broad inventory query that selects `Metadata` fails on the second row.

**When it occurs:** During any org assessment, drift detection, or pre-migration inventory.

**How to avoid:** Split the audit into two passes. Pass one enumerates cheaply:

```soql
SELECT Id, DeveloperName, MasterLabel, Type, EntityDefinitionId, NamespacePrefix
FROM FlexiPage
WHERE Type = 'RecordPage'
```

Pass two fetches `Metadata` one page at a time, filtered by the `Id` from pass one. For the assignment side of the audit, do not use the Tooling API at all — retrieve `CustomObject` and `CustomApplication` metadata, because that is where the overrides live.

**Source:** Tooling API — FlexiPage (`EntityDefinitionId`, `SobjectType`, `FullName`, `Metadata`).

---

## Gotcha 7: Page Assignment Has No Permission-Set Dimension, So It Anchors Profiles in Place

**What happens:** An org running a profile-to-permission-set migration reduces every profile to a minimal shell, expecting to retire the differentiated profiles. Users then start landing on the wrong record pages, and the migration stalls on a dependency nobody scoped.

**Why:** The identity qualifier in `AppProfileActionOverride` is `profile`, and it is the only one. There is no `permissionSet` field, no permission-set-group field, and no custom-permission field anywhere in the assignment metadata. Collapsing ten profiles into one collapses ten page assignments into one at the same time.

**When it occurs:** In the middle of a permission-set migration, typically after the access side has been proven safe and the team assumes profiles are now cosmetic.

**How to avoid:** Inventory profile-scoped page assignments before the migration, not during it, and convert as many of them as possible into a *single* page whose components carry `{!$Permission.CustomPermission.<name>}` visibility rules. Custom permissions are assignable from permission sets, so that conversion moves the differentiation onto the surface the migration is heading towards. Assignments that genuinely need different information architecture per population keep their profiles; document those profiles as load-bearing so nobody deletes them later.

**Source:** Metadata API Developer Guide — CustomApplication (AppProfileActionOverride field list), FlexiPage (`UiFormulaCriterion` supported expressions).
