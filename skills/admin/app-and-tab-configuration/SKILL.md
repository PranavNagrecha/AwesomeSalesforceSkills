---
name: app-and-tab-configuration
description: "Create and configure Lightning apps in Salesforce Setup, add navigation items and tabs to apps, configure utility bar components, and control app visibility by profile or permission set. Also covers the deployable metadata behind all of that: CustomApplication, CustomTab, and the FlexiPage of type UtilityBar. Trigger keywords: Lightning app, App Manager, custom tab, navigation bar, utility bar, app visibility, CustomApplication, tabs element, standard- tab prefix, defaultLandingTab, formFactors, navType, uiType, workspaceConfig, applicationVisibilities, tabSettings, AppDefinition, TabDefinition, AppTabMember, app deployed but not visible. NOT for console navigation, workspace tabs and subtabs - use admin/service-console-configuration. NOT for the record page or app page inside the app - use admin/lightning-app-builder-advanced."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
triggers:
  - "deployed a Lightning app and users still cannot see it in the App Launcher"
  - "lightning app not visible to users after deploy"
  - "add a custom object tab to an app navigation bar"
  - "utility bar changed in one app and showed up in another app"
  - "console app opens records as primary tabs instead of subtabs"
  - "Lightning app is missing from the Salesforce mobile app launcher"
  - "deploy a custom application and its tabs from sandbox to production"
  - "set the default landing page for a Lightning app"
  - "tab is in the app navigation but hidden for a profile"
  - "create a web tab or Lightning component tab and put it in an app"
tags:
  - lightning-app
  - custom-tabs
  - app-manager
  - navigation
  - utility-bar
inputs:
  - "List of objects or pages to expose in the app navigation"
  - "Profiles or permission sets that should have access to the app"
  - "Whether the app needs a utility bar and which utility items (e.g., Open CTI, History, Notes)"
  - "App type: standard Lightning app or console app"
outputs:
  - "Configured Lightning app visible in the App Launcher with correct navigation items"
  - "Deployable CustomApplication, CustomTab, and UtilityBar FlexiPage metadata plus the package.xml and deploy order for them"
  - "Custom tabs created and assigned to the app"
  - "Utility bar configured if required"
  - "App visibility restricted to correct profiles or permission sets, shipped alongside the app"
  - "Post-deploy AppDefinition / AppTabMember verification run in a target user's session"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# App and Tab Configuration

Use this skill when an admin needs to create a Lightning app, expose custom objects via custom tabs, configure a utility bar, or control which users see which apps. This skill covers the full App Manager workflow from initial creation through profile visibility assignment.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the org uses Lightning Experience — Lightning apps only appear in Lightning Experience, not Salesforce Classic. Classic users see Classic apps.
- Know whether users need a standard navigation app or a console app (console apps have split-view and a work queue; standard apps have a horizontal nav bar).
- Identify which custom objects require tabs — a custom object does NOT appear in navigation unless a custom tab exists for it.
- Confirm which profiles or permission sets will use the app, and plan to ship that grant in the same package. `CustomApplication` has no visibility field of its own — `applicationVisibilities` lives in `PermissionSet` or `Profile` — and granting the app does not grant object or field access.
- For a console app, know the parent lookup field for every tab that should open as a subtab. That mapping is part of the app file, and there is no default.

---

## Questions to Ask Before Configuring

Ask these before opening App Manager. Each one maps to a documented platform behaviour that silently produces a wrong-looking-right app when it is skipped.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Who is granted this app, and through a profile or a permission set?" | `CustomApplication` carries no visibility field at all — a green deploy grants nobody (Gotcha 6) | The `applicationVisibilities` grant that ships in the same package as the app |
| "Standard navigation or console?" | `navType` is documented "Not updateable" — the answer is permanent for the life of the app (Gotcha 5) | The app type, plus a `workspaceConfig` mapping per tab if the answer is console |
| "For each console tab: does it anchor a workspace, or nest under one, and by which lookup field?" | `fieldName` is the only thing that makes a record open as a subtab; tab order does not (Gotcha 8) | The mapping table: tab → parent lookup, or explicitly none |
| "Desktop only, or desktop and the mobile app?" | `formFactors` decides; `Large` alone makes the app invisible on phones (Gotcha 9) | Both `formFactors` elements written explicitly, and per-tab mobile availability checked |
| "Which tab is the landing page, and which tabs are merely reachable?" | `defaultLandingTab` is a separate field, and `tabSettings` distinguishes `Visible` from `Available` | A first screen chosen on purpose and a short tab list rather than a long one |
| "Does this app need its own utility bar, or is it reusing one?" | Utility bars are shared: editing one changes every app that names it (Gotcha 7) | One `FlexiPage` of type `UtilityBar` per app, deployed before the app |
| "Which of these tabs already exist, and what is their exact API name?" | Standard tabs need the `standard-` prefix; a wrong name deploys clean and drops the item (Gotcha 10) | Tab names harvested from a retrieve or from `TabDefinition`, not typed from memory |

What a proper configuration adds over just clicking through App Manager: the app, its tabs, its utility bar, and the permission set that grants all three deploy as one reviewed unit, and "the user cannot see it" becomes a query against `AppDefinition` run as that user instead of a guess between four independent switches.

---

## Core Concepts

### Lightning Apps vs Classic Apps

App Manager (Setup > App Manager) shows all apps in the org. Lightning Experience apps appear in the App Launcher (`waffle` icon). Classic apps appear in the Classic app menu. An app marked as "Lightning Experience App" cannot be used in Classic, and vice versa. Console apps are a subtype of Lightning app that provide a multi-tab work environment; they require the Service Cloud or Sales Cloud console license for most users.

The Metadata API type for apps is `CustomApplication`, stored in `applications/` with the suffix `.app`. Navigation items are listed one per `<tabs>` element inside that file — the element is named `tabs`, not `navItems`, and it was renamed from `tab` in API version 42.0. Tabs themselves are separate `CustomTab` components in `tabs/` that reference the object, Lightning page, Visualforce page, Lightning component, or URL the tab surfaces.

An app is really four artefacts, and only the first is the `.app` file:

| Artefact | Metadata type | What it decides |
|---|---|---|
| The app | `CustomApplication` | Label, branding, `navType`, `uiType`, `formFactors`, the `<tabs>` list, `defaultLandingTab`, console `workspaceConfig` |
| Each non-standard navigation item | `CustomTab` | What the item points at — exactly one of `customObject`, `flexiPage`, `lwcComponent`, `auraComponent`, `page`, `scontrol`, `url` |
| The utility bar | `FlexiPage` with `type` `UtilityBar` | Which utilities appear, and their width, height, and label via component decorators |
| Who can see any of it | `PermissionSet` / `Profile` | `applicationVisibilities` for the app, `tabSettings` / `tabVisibilities` for each tab |

Deployable shapes for all four are in `references/metadata-examples.md`.

### Custom Tabs

A custom tab is required to surface any of the following in a Lightning app navigation bar:
- A custom object's list view and record pages
- A Visualforce page
- A Lightning component (Aura or LWC)
- An external web URL

Custom tabs are created in Setup > Tabs. In `CustomTab` metadata the type is decided by which single element carries a value — exactly one of `customObject`, `page`, `auraComponent`, `lwcComponent`, `flexiPage`, `scontrol`, `url` may be set on one tab:

| Setup tab type | `CustomTab` element | Notes |
|---|---|---|
| Custom Object Tab | `customObject` = true | File name must equal the object API name; owned by `admin/object-creation-and-design` |
| Visualforce Tab | `page` | `frameHeight` is required for page tabs |
| Lightning Component Tab | `auraComponent` or `lwcComponent` | The component must expose the tab target |
| Lightning Page Tab | `flexiPage` | Points at a Lightning app page; the FlexiPage must ship in the same deploy |
| Web Tab | `url` | Takes `urlEncodingKey`, and `frameHeight` for the framed variant |

Every tab also requires `motif`, the style string that carries the icon and colour (`Custom1:Heart` through `Custom100:TVWidescreen`).

Tab visibility is not in the tab file. It is set per profile (Tab Settings: Default On, Default Off, Tab Hidden) or per permission set — and the two use different words for the same three states, `DefaultOn` / `DefaultOff` / `Hidden` in `Profile` versus `Visible` / `Available` / `None` in `PermissionSet`. A tab set to "Tab Hidden" (`Hidden` / `None`) prevents the user from seeing the tab in any app, even if the app includes that tab in its navigation.

### App Navigation Items

When creating or editing a Lightning app in App Manager, the navigation items list defines what appears in the app's top navigation bar. Items can be:
- Standard objects (Accounts, Contacts, etc.)
- Custom tabs (object tabs, Visualforce tabs, component tabs)
- Lightning page tabs
- Utility items are separate from navigation items and live in the utility bar

The order of items in the list determines the order in the navigation bar. It does **not** decide the landing page: `defaultLandingTab` is a separate field on `CustomApplication` — "The fullName of a standard tab or custom tab that opens when this application is selected" — and standard tabs need the `standard-` prefix there as well (`standard-home`). Leave it out and the platform picks.

**Keep the list short on purpose.** `isNavPersonalizationDisabled` and `isNavAutoTempTabsDisabled` (both API 43.0+) control whether users may reorder the bar and whether temporary tabs are created automatically; `isNavTabPersistenceDisabled` (API 54.0+) applies only to console apps and clears workspace tabs each session. Set them deliberately rather than accepting whatever the wizard wrote.

UNVERIFIED (2026-09-04): an earlier revision of this skill stated a hard limit of 50 navigation items per app, above which end-user personalization is disabled. That number does not appear in the Metadata API Developer Guide's `CustomApplication` section or in the Salesforce Developer Limits and Allocations Quick Reference, which explicitly excludes "User interface elements in the Salesforce application" from its scope and refers per-edition allocations to *Salesforce Features and Edition Allocations*. Treat 50 as folklore until confirmed against that page; the design advice to stay well under it stands regardless.

### Utility Bar

The utility bar is a persistent toolbar at the bottom of the screen, available only in Lightning Experience on desktop — it does NOT appear in the Salesforce mobile app. Each utility item is a standard or custom Lightning component. Common built-in utilities include:
| Utility | Notes |
|---|---|
| History | Recently visited records. UNVERIFIED (2026-09-04): an earlier revision recorded this as console-apps-only; the Metadata API guide documents the utility bar's structure but publishes no catalogue of standard utility components, so confirm against the Setup picker in the target org |
| Recent Items | Quick access to recently accessed records (available in all app types) |
| Open CTI Softphone | Requires CTI adapter |
| Notes | Quick note capture |
| Macros | For Service Console users |
| Omni-Channel | For agents using Service Cloud routing; requires Service Cloud console app |

Per-item width, height, and label are not app settings — they are stored on the utility bar's own FlexiPage as **component decorators**, a `componentInstanceProperties` entry with `<type>decorator</type>`. The Metadata API guide states that the `UtilityBar` page type is the only one that supports them. A utility that must run without a visible button goes in a `flexiPageRegions` entry of type `Background`, which the guide notes is supported for utility bars only. Custom LWC components can be added as utilities if they implement the correct interface.

---

## Common Patterns

### Pattern: Create a Custom Object App for a Business Team

**When to use:** A team works primarily with one or two custom objects and needs a focused app with only their relevant tabs.

**How it works:**
1. Setup > Tabs > New (Custom Object Tab) — select the custom object, choose a tab style (icon), set default visibility.
2. Setup > App Manager > New Lightning App — enter app name, branding color, logo.
3. Navigation Items step — add the custom object tab plus any related standard objects.
4. Utility Bar step — add History and Notes utilities.
5. User Profiles step — add profiles that should see this app. Remove it from the All profiles default if not needed globally.
6. Save. Users with the selected profiles see the app in the App Launcher.

**Why not the alternative:** Giving users the full default Salesforce app creates noise — they see dozens of objects irrelevant to their work, reducing adoption and increasing support requests.

### Pattern: Restrict App Visibility Without Removing Profile Access

**When to use:** An app should only appear for a subset of users who share a profile but have different roles.

**How it works:**
1. Create a permission set assigned only to the target users.
2. In App Manager > edit the app > User Profiles step — use the permission set visibility option (available in newer releases) or create a profile copy if permission set visibility is not available.
3. Alternatively, use a custom profile for each user group.

Grounding for this: `PermissionSetApplicationVisibility` takes exactly two required fields, `application` and `visible` (Metadata API Developer Guide, `PermissionSet`). The profile equivalent adds a required `default` flag, of which only one app per profile may be true — which is precisely why profile-only app visibility drives profile proliferation. See `admin/permission-set-architecture` for the surrounding permission-set design.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Exposing a new custom object to end users | Create a Custom Object Tab first, then add it to the app | Objects without tabs cannot appear in navigation |
| Team needs split-view record work queue | Use console app type | Console layout is designed for high-volume record processing |
| Want a utility that works on mobile | Use standard in-app features, not utility bar | Utility bar is desktop only; mobile has its own navigation pattern |
| Restricting app to a subset of users on the same profile | Create a permission set and use permission-set-based app visibility | Avoids profile proliferation |
| External URL needs to appear as a tab | Create a Web Tab in Setup > Tabs | Web tabs can open the URL in the tab frame or a new window |

---

## Recommended Workflow

1. **Answer the seven questions above and fill in `templates/app-and-tab-configuration-template.md`.** One row per navigation item, one row per utility, and the visibility matrix. Every later step edits this artefact rather than inventing decisions mid-build.
2. **Harvest real names before writing any XML.** Retrieve a comparable app and its utility bar — `sf project retrieve start --metadata CustomApplication:<ExistingApp>` and `--metadata FlexiPage:<ItsUtilityBar>` — then list the tabs the org already has: `SELECT Name, Label, IsCustom, IsAvailableInLightning FROM TabDefinition`. Standard tab names, utility component names, and the utility-bar template name are all things to copy, never to type from memory.
3. **Author the tabs first, then the utility bar, then the app.** Take the shapes from `references/metadata-examples.md` sections 2, 4, and 1. A `CustomTab` may set exactly one of `customObject` / `flexiPage` / `lwcComponent` / `auraComponent` / `page` / `scontrol` / `url`. For a console app, write a `workspaceConfig` `<mappings>` entry for every tab and decide per tab whether it carries a `fieldName`.
4. **Author the access grant in the same package.** `applicationVisibilities` for the app plus a `tabSettings` entry per custom tab (`Visible` for the app's core tabs, `Available` for the ones users may opt into). This is the step that makes the app reachable; skipping it produces a clean deploy nobody can use.
5. **Run the checker on the source tree**: `python3 skills/admin/app-and-tab-configuration/scripts/check_app_and_tab_configuration.py --manifest-dir force-app/main/default`. It flags a tab referenced by an app but absent from the tree, a console app with no `workspaceConfig`, a duplicated tab inside one app, a missing `utilityBar` FlexiPage, a `navType` / `uiType` contradiction, and an app with no `defaultLandingTab`.
6. **Deploy once, in dependency order, with `--dry-run` first.** Tabs and their FlexiPages, then the utility bar, then the app, then the permission set — a single `sf project deploy start --manifest manifest/package.xml` resolves this; splitting it across deploys does not.
7. **Verify as a target user, not as the admin.** Run the `AppDefinition` and `AppTabMember` queries in `references/metadata-examples.md` section 9 through that user's session, then open the App Launcher and count the items against `<tabs>`. Record the outcome and any deviations back into the template.

---

## Review Checklist

Before marking app configuration complete:

- [ ] Custom tabs created for all custom objects that need navigation
- [ ] Tab visibility set appropriately on target profiles (Default On or Default Off, not Tab Hidden)
- [ ] App navigation items include all required tabs in correct order
- [ ] Utility bar items added if the team needs persistent utilities (CTI, History, Notes)
- [ ] App visibility assigned to correct profiles (and/or permission sets)
- [ ] Tested by logging in as a target profile user and confirming the app appears in App Launcher
- [ ] `defaultLandingTab` set deliberately, with the `standard-` prefix if it names a built-in tab
- [ ] `formFactors` names every surface the app must appear on, mobile included
- [ ] Console apps: a `workspaceConfig` `<mappings>` entry for every tab, `fieldName` present only where a subtab is intended
- [ ] The `utilityBar` FlexiPage is used by this app alone (`SELECT DeveloperName, UtilityBar FROM AppDefinition WHERE UtilityBar != null`)
- [ ] `python3 skills/admin/app-and-tab-configuration/scripts/check_app_and_tab_configuration.py --manifest-dir force-app/main/default` reports no ERROR or WARN
- [ ] App name and icon are appropriate for the business team using it

---

## Salesforce-Specific Gotchas

1. **Utility bar is invisible in the mobile app** — Users who switch to the Salesforce mobile app will not see the utility bar. If CTI or other utilities are essential for mobile users, a separate mobile app configuration or Lightning out integration is needed.
2. **Tab Hidden on profile overrides app navigation** — If a user's profile has a tab set to "Tab Hidden," that tab will not appear in any app for that user, regardless of app configuration. Admins sometimes add a tab to an app and wonder why users still can't see it — the profile tab setting is a hard override.
3. **App Launcher visibility has two independent controls** — First, profile assignment on the app controls which profiles can access it. Second, there is a separate org-wide App Menu toggle per app (Setup → App Manager → App Menu) that can hide any app from the App Launcher for all users regardless of profile assignment. If a newly created app is assigned to profiles but users still cannot see it, check the App Menu toggle — it may be set to "Hidden in App Launcher." That toggle is the `AppMenuItem` object, whose `IsVisible` field ("If true, the app is visible to users of the organization") is the only updateable field on it — so the state is queryable rather than guessable.

The rest of this domain's failure modes are in `references/gotchas.md`: an app that deploys green and grants nobody, utility bars shared silently between apps, console subtab mapping, `formFactors`, the `standard-` prefix, and the override that will not delete.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Lightning App | A configured app in App Manager with navigation items, optional utility bar, and profile visibility |
| `applications/<Name>.app-meta.xml` | The deployable `CustomApplication`: `tabs`, `navType`, `uiType`, `formFactors`, `brand`, `defaultLandingTab`, `utilityBar`, and console `workspaceConfig` |
| `tabs/<Name>.tab-meta.xml` | One `CustomTab` per non-standard navigation item |
| `flexipages/<Name>.flexipage-meta.xml` | The utility bar, as a FlexiPage of `type` `UtilityBar` |
| Custom Tab(s) | Tab metadata components linking objects, VF pages, or LWC components to navigation |
| App Visibility Matrix | A table mapping app name to authorized profiles and permission sets, realised as `applicationVisibilities` + `tabSettings` in the same package |
| Verification result | `AppDefinition` / `AppTabMember` query output captured from a target user's session, not the admin's |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing deployable `CustomApplication`, `CustomTab`, and `UtilityBar` FlexiPage XML, the console `workspaceConfig`, the package.xml and deploy order, and the post-deploy `AppDefinition` / `AppTabMember` queries |
| `references/gotchas.md` | The app deployed cleanly and behaves wrong — invisible to users, utilities leaking between apps, records opening as the wrong kind of console tab, or an override that will not delete |
| `references/examples.md` | Designing an app for a persona before any XML exists — a focused field-service app and a Classic-to-Lightning migration, end to end |
| `references/well-architected.md` | Justifying the tradeoff between purpose-built apps and app sprawl, or locating the official source behind a claim in this skill |
| `references/llm-anti-patterns.md` | Reviewing output an AI assistant produced here, especially "just add the object to the app's navigation items" |
| `templates/app-and-tab-configuration-template.md` | Running workflow step 1 — the navigation, utility, and visibility inventory |
| `scripts/check_app_and_tab_configuration.py` | Workflow step 5, before every deploy of an app or tab |

---

## Related Skills

- `admin/permission-set-architecture` — owns `applicationVisibilities` and `tabSettings` as part of permission-set design; read it before granting the app
- `admin/object-creation-and-design` — owns the custom-object `CustomTab` shape and the `motif` catalogue that this skill references by name
- `admin/lightning-app-builder-advanced` — owns the Lightning pages a `flexiPage` tab or an app's home page points at
- `admin/service-console-configuration` — owns console layout, split view, and workspace behaviour beyond the `workspaceConfig` mappings in the app file
- `admin/dynamic-forms-and-actions` — owns record-page composition, which the app's `profileActionOverrides` can redirect per profile
- `admin/in-app-guidance-and-walkthroughs` — owns onboarding prompts scoped to a specific app
- `admin/user-management` — ensures users have correct profiles before app visibility is assigned
- `admin/org-setup-and-configuration` — covers global theme and session settings that affect app branding and behavior
