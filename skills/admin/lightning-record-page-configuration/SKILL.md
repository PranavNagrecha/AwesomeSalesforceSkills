---
name: lightning-record-page-configuration
description: "Use when building a Lightning record page in App Builder or when the page users see is not the one you assigned. Trigger keywords: configure lightning record page, lightning app builder, flexipage, record page assignment, org default vs app default, activate lightning page. NOT for page speed - use admin/lightning-page-performance-tuning. NOT for page layout to Dynamic Forms migration - use admin/dynamic-forms-migration. NOT for related list columns - use admin/related-list-configuration."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
  - Performance
  - Security
triggers:
  - "why is my Lightning record page not showing for some users but showing for others"
  - "how do I assign a Lightning record page to one profile and one record type"
  - "I set the record page as org default but the old page still appears in the app"
  - "deploy a Lightning record page from sandbox to production without losing the assignment"
  - "hide a component on the record page unless the opportunity stage is Closed Won"
  - "what is the difference between org default and app default for a Lightning page"
  - "the record page looks right on desktop but wrong in the Salesforce mobile app"
  - "build a record page with tabs so related lists are not on the first screen"
  - "flexipage deploy fails after retrieving the page at an older API version"
tags:
  - lightning-record-page
  - lightning-app-builder
  - flexipage
  - page-assignment
  - component-visibility
  - dynamic-forms
  - dynamic-actions
  - record-page-deployment
inputs:
  - "Target object API name, and whether the page is a record page, app page, or Home page"
  - "Which Lightning apps the object is reached from, and whether any use console navigation"
  - "Record types in play and which profiles should land on which page"
  - "Form factors that must be covered — Lightning Experience desktop (Large), the Salesforce mobile app (Small), or both"
  - "Existing FlexiPage inventory for the object, from Setup > Lightning App Builder or a Tooling API query"
  - "How the page will move between orgs: change set, unlocked package, or sf project deploy start"
outputs:
  - "Activated Lightning record page with a written assignment matrix covering org default, app default, and app + record type + profile"
  - "Deployable FlexiPage metadata plus the CustomObject and CustomApplication override fragments that actually carry the assignment"
  - "Component visibility filter set expressed as UiFormulaRule criteria with an explicit booleanFilter"
  - "Assignment precedence audit naming which rung wins for each user population"
  - "Checker script report listing unassigned pages, over-capacity regions, and legacy metadata shapes"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-08-15
---

# Lightning Record Page Configuration

This skill activates when an admin builds a Lightning page in the Lightning App Builder and then has to make the right users actually land on it. Building the page is the easy half. The assignment model — org default, app default, and app + record type + profile — is where the work goes wrong, because assignment is stored in different metadata from the page itself and the more specific assignment silently wins.

Every API name, enum value, and numeric cap on this page comes from the Metadata API and Tooling API references listed in `references/well-architected.md`.

---

## Before Starting

Gather this context before touching the App Builder:

- **Which page type is this?** `RecordPage`, `AppPage`, and `HomePage` are three values of the same `type` field on one metadata type, but they behave differently. Only a record page has a record in context, so only a record page can use `{!Record.field}` in a visibility filter, place Dynamic Forms field components, or host Dynamic Actions. An app page has no record and no `sobjectType`.
- **Which apps reach this object?** Assignment is app-scoped. An object surfaced in four Lightning apps can show four different pages, and the org default is the one that loses. If the org runs a console app alongside a standard app, assume they need separate assignments until proven otherwise.
- **Which form factors are in scope?** `formFactor` is part of the assignment, not part of the page. `Large` is the Lightning Experience desktop environment; `Small` is the Salesforce mobile app. A page assigned only at `Large` does nothing on a phone, and the absence of a form factor on a `CustomObject` action override means Salesforce Classic, not "all of them".
- **Is `sobjectType` already set?** On a `RecordPage` the object association is fixed once written. There is no repoint; there is only clone-and-reassign. Decide the object before the first save.
- **What is the deployment path?** The `.flexipage` file carries zero assignment information. If the plan is "retrieve the flexipages folder and deploy it", the plan ships an inert page. See `references/gotchas.md` Gotcha 1 before writing the manifest.

---

## Core Concepts

### Page Types Are One Metadata Type With Different Rules

`FlexiPage` has existed since API version 29.0. It stores as `<name>.flexipage-meta.xml` under `flexipages/`, and `type` selects the behaviour:

| `type` value | Has a record in context | `sobjectType` | Typical use |
|---|---|---|---|
| `RecordPage` | Yes | Set, and unchangeable afterwards | The detail page for one object |
| `AppPage` | No | Not used | A custom tab-level landing page in a Lightning app |
| `HomePage` (API 37.0+) | No | Not used | The app or org Home tab |
| `RecordPreview` (API 45.0+) | Yes | Set, and unchangeable afterwards | The hover / preview card |
| `UtilityBar` (API 38.0+) | No | Not used | The docked utility bar for an app |

Experience Cloud pages use a parallel `Comm*` family (`CommRecordPage`, `CommObjectPage`, `CommLoginPage`, and others). Two enum values, `EmailContentPage` and `EmailTemplatePage`, are builder-generated and cannot be retrieved or deployed through the API at all.

Required fields on every FlexiPage are `masterLabel`, `type`, and — from API version 39.0 — `template`. Salesforce's own published sample record pages use `<template><name>flexipage:recordHomeTemplateDesktop</name></template>` and inherit from the platform's default record page via `<parentFlexiPage>flexipage__default_rec_L</parentFlexiPage>`.

### Regions, Facets, and the 100-Component Cap

A page is a list of `flexiPageRegions`. Each region has a `name`, a `type`, and `itemInstances`. Region `type` is one of `Region`, `Facet`, or `Background` (utility bars only). A **Region** is a slot the template defines — `header`, `main`, `sidebar`. A **Facet** is a container's payload: any component that holds other components (a tab, a column, a field section) points at a facet by name rather than nesting XML inside itself.

A region can contain up to 100 components.

Each `itemInstance` holds either a `componentInstance` (a Lightning component) or a `fieldInstance` (a Dynamic Forms field). `componentInstance` requires `componentName` and, from API version 53.0, an `identifier` of at most 120 characters. The reference caps the whole `ComponentInstanceProperty` at 10,000 characters — the limit is stated against the property, not against its `value` child alone, so a long literal plus its surrounding element markup shares one budget. That is what bounds a Rich Text component's body.

### Assignment: Three Rungs and a Fallback

Assignment is not stored on the page. It is stored as action overrides on the object and on each app, and the more specific override wins. The Metadata API reference states it directly for the app-versus-org case: *"When a user invokes the custom app, a matching ProfileActionOverride assignment takes precedence over existing overrides for the record page specified in ActionOverride."*

| Rung | Setup label | Metadata home | Element |
|---|---|---|---|
| 1 (wins) | App, Record Type, and Profile | `CustomApplication` | `<profileActionOverrides>` (`AppProfileActionOverride`) |
| 2 | App Default | `CustomApplication` | `<actionOverrides>` (`AppActionOverride`) |
| 3 | Org Default | `CustomObject` | `<actionOverrides>` (`ActionOverride`) |
| 4 | none | — | Salesforce's system default record page |

`AppProfileActionOverride` carries `actionName` (`View` for a record page, `Tab` for a Home page), `pageOrSobjectType` (`record-home` or `standard-home`), `recordType`, `profile`, and `formFactor`, plus the read-only `content` and `type`. `recordType` is not the optional field it looks like: the reference states it *"is required when actionName is set to View"*, which is every record-page assignment, and conversely that it must be null when `pageOrSobjectType` is `standard-home` (the Home-page case, `actionName` `Tab`). There is no documented "this app, this profile, any record type" row — Rung 1 names a record type, or it is not a Rung 1 row. An org that wants one page for a profile across every record type states that at Rung 2 or with component visibility, not by omitting `recordType`.

Note what is *not* in that field list: there is no permission-set dimension. The only identity qualifier in the assignment metadata is `profile`. Orgs midway through a profile-to-permission-set programme still need those profiles alive purely to hold page assignments.

Org default lives on the object, in an `ActionOverride` whose `actionName` is `view`, `type` is `flexipage`, `content` is the FlexiPage name, and `formFactor` is `Large`. The `type` enum also accepts `default`, `lightningcomponent`, `scontrol`, `standard`, and `visualforce`; only `flexipage` points at a Lightning page, and the reference limits it to the View action in Lightning Experience.

### Activation Is Assignment — There Is No Separate Active Flag

The App Builder's Activation dialog is a writer for the three rungs above. Saving a page creates the `FlexiPage`; activating it writes an override. A saved-but-unassigned page is valid, deployable, and completely invisible: nothing points at it, so the object keeps rendering whatever the next rung down supplies. There is no error, no warning, and no state on the page record itself to inspect — which is why "I saved it and nothing changed" is the most common symptom in this domain.

### Component Visibility Filters

Every `componentInstance` and every `fieldInstance` accepts a `visibilityRule` (`UiFormulaRule`, API 41.0+) made of `criteria` plus an optional `booleanFilter` string such as `1 AND 2`. Each criterion is a `leftValue` / `operator` / `rightValue` triple.

| Field | Value | Notes |
|---|---|---|
| `leftValue` | `{!Record.StageName}` | Record pages only — an app or Home page has no record in context |
| `leftValue` | `{!$User.Department}` | Valid on app, Home, and record pages |
| `leftValue` | `{!$Permission.CustomPermission.Show_Risk_Panel}` | App, Home, and record pages only; `$Permission.StandardPermission.<name>` is the standard-permission form |
| `leftValue` | `{!$Client.FormFactor}` | Returns `Small` / `Medium` / `Large`; app pages from API 41.0, record pages from API 47.0 |
| `operator` | `EQUAL`, `NE`, `CONTAINS`, `GT`, `GE`, `LT`, `LE` | This is the whole set. `!=`, `>=`, `LIKE`, and `IN` are not operators here |
| `rightValue` | `Closed Won` | Literal; no quoting |
| `booleanFilter` | `(1 OR 2) AND 3` | Combines criteria by 1-based index |

One hard constraint: an expression in a component visibility rule can span no more than five fields. Cross-object hops burn that budget fast, and the usual fix is a formula field on the record that collapses the traversal to a single hop.

### Dynamic Forms and Dynamic Actions

**Dynamic Forms** replaces the monolithic record-detail component with per-field placement. In metadata that means `fieldInstance` items (API 49.0+) instead of one detail component. A field instance carries `fieldItem` — the API name with a context prefix, `Record.Amount` — an `identifier`, an optional `visibilityRule`, and `fieldInstanceProperties`. Two property names are valid: `uiBehavior` (API 49.0+) and `conditionalFormatRuleset` (API 62.0+). The Metadata API reference documents the `uiBehavior` values as `None`, `Readonly`, and `Required`; files retrieved from an org carry them lower-cased (`none`, `readonly`, `required`), which is the form to match when hand-editing a retrieved page. Fields group into `flexipage:fieldSection` components whose `columns` property names a facet; each column is a `flexipage:column` whose `body` names another facet holding the field instances.

Dynamic Forms object availability has expanded release by release and differs between standard and custom objects — check the App Builder for the target object rather than assuming, and use `admin/dynamic-forms-migration` for the conversion project itself.

**Dynamic Actions** moves the action bar out of the page layout and into the page. It is stored on the page as a `PlatformActionList` (API 34.0+) whose `actionListContext` is `Flexipage`, holding `platformActionListItems` with `actionName`, `actionType`, `sortOrder`, and `subtype`. Valid `actionType` values are `ActionLink`, `CustomButton`, `InvocableAction`, `ProductivityAction`, `QuickAction`, and `StandardButton`. Each item takes its own visibility rule, which is the point: one page can show Escalate to support agents and hide it from sales without a second page existing.

### Tabs and Accordion

The Tabs component is a container plus one facet per tab. Salesforce's published sample record pages use exactly this shape:

```xml
<!-- force-app/main/default/flexipages/Property_Record_Page.flexipage-meta.xml -->
<flexiPageRegions>
    <itemInstances>
        <componentInstance>
            <componentInstanceProperties>
                <name>active</name><value>true</value>
            </componentInstanceProperties>
            <componentInstanceProperties>
                <name>body</name><value>detailTabContent</value>
            </componentInstanceProperties>
            <componentInstanceProperties>
                <name>title</name><value>Standard.Tab.detail</value>
            </componentInstanceProperties>
            <componentName>flexipage:tab</componentName>
            <identifier>detailTab</identifier>
        </componentInstance>
    </itemInstances>
    <mode>Replace</mode>
    <name>maintabs</name>
    <type>Facet</type>
</flexiPageRegions>
<flexiPageRegions>
    <itemInstances>
        <componentInstance>
            <componentInstanceProperties>
                <name>tabs</name><value>maintabs</value>
            </componentInstanceProperties>
            <componentName>flexipage:tabset</componentName>
            <identifier>flexipage_tabset</identifier>
        </componentInstance>
    </itemInstances>
    <mode>Replace</mode>
    <name>main</name>
    <type>Region</type>
</flexiPageRegions>
```

Standard tab titles are system-defined names, not the labels shown on screen: `Standard.Tab.detail`, `Standard.Tab.relatedLists`, `Standard.Tab.activity`. A custom tab's `title` is the literal label. Exactly one tab should carry `active` = `true`.

The Accordion component is the other progressive-disclosure container: collapsible sections in one scrolling column, which suits a narrow form factor better than a tab strip does. <!-- [UNVERIFIED: the Accordion component's exact componentName string is not confirmed against an official sample here. Retrieve the real page and read its flexipage XML before hand-authoring an accordion; do not guess the element name.] -->

---

## Common Patterns

### Pattern: One Page for Many Record Types

**When to use:** Three record types on Opportunity have historically driven three page layouts. Maintaining three record pages triples the cost of every future change.

**How it works:** Build one record page. Place the record-type-specific fields and components, and give each a `visibilityRule` on `{!Record.RecordType.DeveloperName}` with `EQUAL`. Assign the single page at Rung 3 (Org Default) so every app inherits it, and leave Rungs 1 and 2 empty until a genuine exception appears.

**Why not the alternative:** Three pages means three assignments, three activation dialogs, and three places to forget when a field is added. It also multiplies the deployment surface, since each page needs its own `profileActionOverrides` entry per app.

### Pattern: Console App Gets Its Own Page

**When to use:** Support agents work in a console app and need the case page dense and tab-heavy. Everyone else opens cases from a standard-navigation app and wants the readable version.

**How it works:** Keep the readable page at Rung 3 (Org Default). Assign the dense page at Rung 2 (App Default) on the console app only. Precedence does the routing, with no profile enumeration and no visibility rules at all.

**Why not the alternative:** Doing this with profile-scoped Rung 1 assignments means listing every support profile, then re-listing them every time a profile is added. App scope tracks the workspace, which is what actually differs.

### Pattern: Moving a Page and Its Assignment Between Orgs

**When to use:** Any promotion out of a sandbox.

**How it works:** The deployment is three metadata types, not one.

```xml
<!-- manifest/package.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Opportunity_Record_Page</members>
        <name>FlexiPage</name>
    </types>
    <types>
        <members>Opportunity</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Sales_Console</members>
        <name>CustomApplication</name>
    </types>
    <version>64.0</version>
</Package>
```

The `CustomObject` member carries the org default; the `CustomApplication` member carries the app default and every app + record type + profile assignment. Any profile named in a `profileActionOverrides` entry must already exist in the target org.

**Why not the alternative:** Deploying `FlexiPage` alone succeeds, reports success, and changes nothing any user can see.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| One page should serve everyone | Org Default only (Rung 3) | Fewest moving parts; every app inherits it |
| Console and standard apps need different densities | App Default (Rung 2) on the console app | App scope matches the real difference; no profile lists to maintain |
| One team needs an extra panel, everything else identical | One page + component visibility on `$Permission.CustomPermission` | A custom permission survives profile churn; a profile-scoped page assignment does not |
| Genuinely different information architecture per record type and profile | App + Record Type + Profile (Rung 1) | The only rung that expresses all three qualifiers |
| Field-level differences per record type | One page + `fieldInstance` visibility rules | Dynamic Forms differentiates fields without a second page |
| The page must render on phones | A second assignment at `formFactor` `Small` | `Large` is desktop Lightning Experience only |
| Users report the wrong page after an org-default change | Audit `profileActionOverrides` on every app first | Rungs 1 and 2 both outrank the org default |
| The page is slow, not wrong | `admin/lightning-page-performance-tuning` | Component count, EPT, and progressive disclosure are that skill's scope |

---

## Recommended Workflow

1. **Establish the page inventory and the current winner.** Query the Tooling API for the object's pages — `SELECT Id, DeveloperName, MasterLabel, Type FROM FlexiPage WHERE EntityDefinitionId = 'Opportunity'` — then read `actionOverrides` on the object and `actionOverrides` plus `profileActionOverrides` on every app that exposes it. Until you know which rung wins today, any change is a guess.
2. **Choose the page type and fix `sobjectType`.** A record page's object association cannot be changed after it is set, so confirm the object before the first save.
3. **Build the regions.** Place components into `header` / `main` / `sidebar`, push secondary content behind `flexipage:tab` facets, and stay under 100 components per region. Give every component and field instance a stable `identifier`.
4. **Write visibility rules against the operator enum.** Use `EQUAL`, `NE`, `CONTAINS`, `GT`, `GE`, `LT`, `LE`, and a `booleanFilter` for anything beyond a single condition. Keep each expression within five fields; collapse deeper traversals into a formula field first.
5. **Assign deliberately, lowest rung first.** Set the org default, then add app defaults only where a workspace genuinely differs, then app + record type + profile only for real exceptions. Record the matrix in `templates/lightning-record-page-configuration-template.md`; the metadata never presents it in one place.
6. **Run the checker, then verify as a real user.** `python3 skills/admin/lightning-record-page-configuration/scripts/check_lightning_record_page_configuration.py --manifest-dir <metadata-dir>` flags unassigned pages, over-capacity regions, missing identifiers, invalid operators, and pre-API-49 metadata shapes. Then log in as one user per profile in the matrix and confirm the page on every form factor in scope.
7. **Deploy the page and its assignment together.** Include `FlexiPage`, `CustomObject`, and `CustomApplication` in the same manifest, and confirm the target org already has every profile named in a `profileActionOverrides` entry.

---

## Review Checklist

- [ ] Every activated page has at least one override pointing at it — no orphan FlexiPages saved and forgotten
- [ ] The assignment matrix is written down: org default, app default per app, and every app + record type + profile row
- [ ] Every Rung 1 (`profileActionOverrides`) row names a `recordType` — the reference requires it whenever `actionName` is `View`
- [ ] `formFactor` coverage is explicit; if the Salesforce mobile app is in scope, a `Small` assignment exists
- [ ] No region exceeds 100 components
- [ ] Every `componentInstance` and `fieldInstance` has an `identifier` of 120 characters or fewer
- [ ] Visibility rule operators are drawn only from `EQUAL`, `NE`, `CONTAINS`, `GT`, `GE`, `LT`, `LE`
- [ ] No visibility expression spans more than five fields
- [ ] `{!Record.*}` expressions appear only on `RecordPage` pages
- [ ] Dynamic Actions items each carry their own visibility rule, and the page layout's action bar is no longer the source of truth
- [ ] The deployment manifest lists `FlexiPage`, `CustomObject`, and `CustomApplication`
- [ ] Every profile referenced by a `profileActionOverrides` entry exists in the target org
- [ ] The page was verified by logging in as one user per row of the matrix, not by previewing inside App Builder

---

## Salesforce-Specific Gotchas

Deep versions with reproduction and recovery steps are in `references/gotchas.md`. Summarised:

1. **A deployed page with no deployed override is invisible.** Assignment lives on `CustomObject` and `CustomApplication`, never inside the `.flexipage` file.
2. **App-scoped assignments outrank the org default.** Changing the org default fixes nothing for users who enter through an app that carries its own override.
3. **`formFactor` is part of the assignment.** `Large` covers Lightning Experience desktop; the Salesforce mobile app needs `Small`; an absent form factor on a `CustomObject` override means Classic.
4. **`sobjectType` is unchangeable once set.** Repointing a record page at another object is a clone, not an edit.
5. **API 49.0 and 53.0 changed the file shape.** `componentInstances` gave way to `itemInstances`, comma-separated array values gave way to `valueList`, and `identifier` became required.
6. **Tooling API audits fail in two predictable ways.** `SobjectType` is deprecated in favour of `EntityDefinitionId`, and `FullName` / `Metadata` can only be selected when the query returns a single record.
7. **There is no permission-set rung.** Page assignment keys on `profile` only, which keeps profiles alive through a permission-set migration.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Activated record page | A `FlexiPage` of type `RecordPage` with regions, facets, and visibility rules configured |
| Assignment matrix | A written table of org default, app default, and app + record type + profile rows, with form factors |
| Deployment manifest | `package.xml` naming `FlexiPage`, `CustomObject`, and `CustomApplication` together |
| Visibility rule register | Each rule as `leftValue` / `operator` / `rightValue` plus `booleanFilter`, with the business reason |
| Checker output | Unassigned pages, over-capacity regions, missing identifiers, invalid operators, legacy shapes |

---

## Related Skills

- lightning-app-builder-advanced — custom page templates, LWC `targetConfig` constraints, and deeper component-visibility technique once the page and its assignment exist
- lightning-page-performance-tuning — when the page is correct but slow: EPT measurement, component-count reduction, progressive disclosure
- dynamic-forms-migration — the conversion project from page-layout-driven detail sections to `fieldInstance` placement
- related-list-configuration — related list columns, sort fields, and the Related Lists / Related List - Single / Quick Links choice inside a region
- record-types-and-page-layouts — record types still drive picklist values, compact layouts, and quick action layouts even after a page is fully Dynamic Forms
