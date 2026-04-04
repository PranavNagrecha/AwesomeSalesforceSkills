---
name: app-and-tab-configuration
description: "Use this skill to create and configure Lightning apps in Salesforce Setup, add navigation items and tabs to apps, configure utility bar components, and control app visibility by profile or permission set. Trigger keywords: Lightning app, App Manager, custom tab, navigation bar, utility bar, app visibility. NOT for Experience Cloud site apps (use experience-cloud skills), NOT for configuring page layouts or record pages (use Lightning App Builder), NOT for permission set architecture (use permission-set-architecture)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
triggers:
  - "how do I create a new Lightning app in Salesforce"
  - "how to add a custom object tab to the navigation bar"
  - "why can't my users see the app I created"
  - "how to add a utility bar to a Lightning app"
  - "how to restrict which profiles can see a Lightning app"
  - "how to configure navigation items in App Manager"
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
  - "Custom tabs created and assigned to the app"
  - "Utility bar configured if required"
  - "App visibility restricted to correct profiles or permission sets"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-03
---

# App and Tab Configuration

Use this skill when an admin needs to create a Lightning app, expose custom objects via custom tabs, configure a utility bar, or control which users see which apps. This skill covers the full App Manager workflow from initial creation through profile visibility assignment.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the org uses Lightning Experience — Lightning apps only appear in Lightning Experience, not Salesforce Classic. Classic users see Classic apps.
- Know whether users need a standard navigation app or a console app (console apps have split-view and a work queue; standard apps have a horizontal nav bar).
- Identify which custom objects require tabs — a custom object does NOT appear in navigation unless a custom tab exists for it.
- Confirm which profiles will use the app. App visibility is controlled per-profile via the App Manager; adding visibility to a profile does not automatically grant object or field access.

---

## Core Concepts

### Lightning Apps vs Classic Apps

App Manager (Setup > App Manager) shows all apps in the org. Lightning Experience apps appear in the App Launcher (`waffle` icon). Classic apps appear in the Classic app menu. An app marked as "Lightning Experience App" cannot be used in Classic, and vice versa. Console apps are a subtype of Lightning app that provide a multi-tab work environment; they require the Service Cloud or Sales Cloud console license for most users.

The Metadata API type for apps is `CustomApplication`. App navigation items are stored in the `CustomApplication` metadata component, with each item listed under `navItems`. Tabs are separate `CustomTab` metadata components that reference the object, Visualforce page, or Lightning component the tab surfaces.

### Custom Tabs

A custom tab is required to surface any of the following in a Lightning app navigation bar:
- A custom object's list view and record pages
- A Visualforce page
- A Lightning component (Aura or LWC)
- An external web URL

Custom tabs are created in Setup > Tabs. There are four tab types:
1. **Custom Object Tab** — links to a standard list view for a custom (or standard) object
2. **Visualforce Tab** — wraps a Visualforce page in the tab chrome
3. **Lightning Component Tab** — surfaces an Aura or LWC component as a full-page tab
4. **Web Tab** — opens a URL inside the tab frame

Tab visibility is set at the profile level (Tab Settings: Default On, Default Off, Tab Hidden). A tab set to "Tab Hidden" on a profile prevents the user from seeing the tab in any app, even if the app includes that tab in its navigation.

### App Navigation Items

When creating or editing a Lightning app in App Manager, the navigation items list defines what appears in the app's top navigation bar. Items can be:
- Standard objects (Accounts, Contacts, etc.)
- Custom tabs (object tabs, Visualforce tabs, component tabs)
- Lightning page tabs
- Utility items are separate from navigation items and live in the utility bar

The order of items in the list determines the order in the navigation bar. The first item becomes the default landing page when the user opens the app.

**Hard limit: 50 navigation items per app.** When an app reaches 50 items, end-user personalization of the navigation bar is disabled entirely — users can no longer reorder or add items even if admin personalization is allowed. Design apps well under this ceiling.

### Utility Bar

The utility bar is a persistent toolbar at the bottom of the screen, available only in Lightning Experience on desktop — it does NOT appear in the Salesforce mobile app. Each utility item is a standard or custom Lightning component. Common built-in utilities include:
- **History** — recently visited records; **console apps only** — this utility does not appear in the Setup picker for standard-navigation apps
- **Recent Items** — quick access to recently accessed records (available in all app types)
- **Open CTI Softphone** — requires CTI adapter
- **Notes** — quick note capture
- **Macros** — for Service Console users
- **Omni-Channel** — for agents using Service Cloud routing; requires Service Cloud console app

Utility items can have default width, height, and open-on-load behavior configured per item. Custom LWC components can be added as utilities if they implement the correct interface.

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

Note: As of Spring '24, app visibility by permission set is supported for Lightning apps — you do not need separate profiles solely for app visibility anymore.

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

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Before marking app configuration complete:

- [ ] Custom tabs created for all custom objects that need navigation
- [ ] Tab visibility set appropriately on target profiles (Default On or Default Off, not Tab Hidden)
- [ ] App navigation items include all required tabs in correct order
- [ ] Utility bar items added if the team needs persistent utilities (CTI, History, Notes)
- [ ] App visibility assigned to correct profiles (and/or permission sets)
- [ ] Tested by logging in as a target profile user and confirming the app appears in App Launcher
- [ ] App name and icon are appropriate for the business team using it

---

## Salesforce-Specific Gotchas

1. **Utility bar is invisible in the mobile app** — Users who switch to the Salesforce mobile app will not see the utility bar. If CTI or other utilities are essential for mobile users, a separate mobile app configuration or Lightning out integration is needed.
2. **Tab Hidden on profile overrides app navigation** — If a user's profile has a tab set to "Tab Hidden," that tab will not appear in any app for that user, regardless of app configuration. Admins sometimes add a tab to an app and wonder why users still can't see it — the profile tab setting is a hard override.
3. **App Launcher visibility has two independent controls** — First, profile assignment on the app controls which profiles can access it. Second, there is a separate org-wide App Menu toggle per app (Setup → App Manager → App Menu) that can hide any app from the App Launcher for all users regardless of profile assignment. If a newly created app is assigned to profiles but users still cannot see it, check the App Menu toggle — it may be set to "Hidden in App Launcher."

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Lightning App | A configured app in App Manager with navigation items, optional utility bar, and profile visibility |
| Custom Tab(s) | Tab metadata components linking objects, VF pages, or LWC components to navigation |
| App Visibility Matrix | A table mapping app name to authorized profiles and permission sets |

---

## Related Skills

- permission-set-architecture — use alongside this skill when restricting app visibility by permission set rather than profile
- user-management — ensures users have correct profiles before app visibility is assigned
- org-setup-and-configuration — covers global security and session settings that affect app behavior
