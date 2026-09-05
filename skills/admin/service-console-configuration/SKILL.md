---
name: service-console-configuration
description: "Use this skill to configure a Lightning Service Console app in Salesforce — Console Navigation (split view), workspace tabs and subtabs, the utility bar with Omni-Channel, Macros and History, Quick Text, keyboard shortcuts, and navigation rules per object. Trigger keywords: Service Console, console app, workspace tabs, subtabs, utility bar macros, Omni-Channel utility, split view, Quick Text, console navigation rules, keyboard shortcuts service console, navType Console, workspaceConfig mappings, WorkspaceMapping fieldName, UtilityBar FlexiPage, tabLimitConfig, listPlacement, MacroInstruction, QuickText Channel multipicklist, isNavTabPersistenceDisabled. NOT for opening or refreshing console tabs from code — use lwc/lwc-console-workspace-api. NOT for Omni-Channel routing setup — use admin/omni-channel-routing-setup."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Performance
triggers:
  - "how do I set up the Service Console for my support team"
  - "why are my agents losing case context when they click a contact"
  - "how to configure workspace tabs and subtabs in Salesforce"
  - "how to add Omni-Channel and Macros to the utility bar"
  - "how to create keyboard shortcuts for the Lightning console"
  - "what is Console Navigation and how is it different from Standard Navigation"
  - "service console isn't working"
  - "every record opens as a new workspace tab instead of a subtab"
  - "contact opens as a primary tab instead of a subtab of the account"
  - "change an existing Lightning app from standard navigation to console"
  - "quick text snippets don't show up when the agent composes an email"
  - "macro runs but nothing happens for the agent"
  - "utility bar change in one app also changed another app"
  - "what goes in workspaceConfig mappings fieldName"
  - "console app deployed but split view is not showing"
  - "audit script says the org has no console apps"
tags:
  - service-console
  - console-navigation
  - workspace-tabs
  - utility-bar
  - macros
  - quick-text
  - omni-channel
  - keyboard-shortcuts
inputs:
  - "Whether the org has Service Cloud licenses (required for console app type)"
  - "List of objects agents work — Cases, Contacts, Accounts, Knowledge, etc."
  - "Utility items required — Omni-Channel, Macros, History, Open CTI Softphone, Quick Text"
  - "Objects that should open as workspace tabs vs subtabs, and the lookup field that names the parent for each subtab"
  - "Keyboard shortcut customizations needed"
outputs:
  - "Configured Lightning console app with Console Navigation enabled and split view active"
  - "A CustomApplication with navType Console and one workspaceConfig mapping per navigation tab"
  - "A UtilityBar FlexiPage with the agent's utility items, panel sizes as component decorators, and any background items"
  - "Macro records covering repetitive agent actions"
  - "Quick Text entries for common agent responses"
  - "Keyboard shortcut configuration for the console app"
  - "Deploy order, package.xml, and post-deploy AppDefinition / MacroUsage verification queries"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Service Console Configuration

Use this skill when an admin needs to configure a Lightning Service Console app for a support team — this includes enabling Console Navigation (split view), configuring workspace tabs and subtabs, setting up the utility bar, creating macros and Quick Text entries, defining navigation rules per object, and customizing keyboard shortcuts. This skill covers the full console setup from app creation to agent-ready configuration.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has **Service Cloud** licenses. Console navigation requires a Service Cloud or Sales Cloud console license for each agent user. Without the license, users see the app but it degrades to standard navigation.
- Know which objects agents interact with during a case, **and the lookup field that connects each one to its parent**. The mapping that makes a record a subtab is field-driven, so "Contact should be a subtab" is not a complete requirement — "Contact, under the Account in `Contact.AccountId`" is.
- Determine whether Omni-Channel is already configured. The Omni-Channel utility requires Omni-Channel to be enabled in the org (Setup > Omni-Channel Settings) and at least one Service Channel before the widget is useful in the utility bar.
- Identify the current utility bar contents if the app already exists — the utility bar is a shared `FlexiPage`, so capture it with a retrieve before making changes and check which other apps point at it.

---

## Questions to Ask Before Configuring

Ask these before opening App Manager. Each one changes the metadata, and an LLM that skips them produces a console app that deploys cleanly and behaves wrong for agents.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "For each object agents open, which record should it appear *under*, and which field says so?" | `WorkspaceMapping.fieldName` names a lookup on the child's own object; absence of a `fieldName` means primary tab, not "inherit the current workspace" (Gotcha 6, Gotcha 7) | One `mappings` entry per tab, each with the exact lookup API name or a deliberate blank |
| "Does an app for these agents already exist, and is it Standard or Console navigation?" | `navType` is "Not updateable" — the answer decides between editing and rebuilding (Gotcha 1) | A build-vs-migrate decision made before any configuration is invested |
| "Which other apps use the utility bar we are about to edit?" | Utility bars are shared FlexiPages; an edit here changes every app that names it (Gotcha 12) | A named FlexiPage this app owns, or an explicit accepted coupling |
| "Do two teams need the same object to behave differently?" | Workspace mappings have no `profile` field, unlike record-page overrides (Gotcha 5) | Either one standardized rule with training, or a second console app, decided now |
| "Which utility items must run without the agent clicking anything?" | Background utility items need a second `flexiPageRegions` entry of type `Background`, supported for utility bars only | The split between visible footer items and invisible listeners |
| "Is a developer available for the keyboard shortcuts you want?" | Custom shortcuts require an `addEventListener()` handler in the Console Integration Toolkit first; only the 18 default actions are declarative (Gotcha 11) | Shortcuts scoped to what can actually ship this release |
| "Who owns the Quick Text library, and which channels does each snippet serve?" | `Channel` is a multipicklist backed by a standard value set, not a fixed five-value picklist (Gotcha 4) | One record per snippet with all its channels, instead of a triplicated library that drifts |

What a proper configuration adds over just creating a console app: every tab's behaviour is a stated decision with the lookup field that implements it, the utility bar belongs to one app, and the checker can prove before deploy that no mapping points at a field that does not exist.

---

## Core Concepts

### Console Navigation vs Standard Navigation

Lightning apps use one of two navigation types set at app creation time in App Manager:

- **Standard Navigation** — horizontal nav bar at the top; each object opens a full-page view replacing the current view; this is the default for most apps.
- **Console Navigation** — enables the Service Console workspace layout: a persistent list panel plus one or more workspace tabs in the main area. Agents can work multiple records simultaneously without losing context.

The navigation type is a fixed property of the app — you cannot switch an existing app from Standard to Console or vice versa without recreating it. The Metadata API field is `navType` set to `Console` on the `CustomApplication` component, and the guide marks it "Not updateable" (`api_meta.txt` L39719–39723).

Two related fields are easy to misread:

- **`isServiceCloudConsole` is null on a Lightning console app.** It only means something for Salesforce Classic: "For Lightning Experience console apps, this field is null and the `navType` field is set to `Console`" (L39702–39706). Any audit that looks for `isServiceCloudConsole = true` misses every Lightning console app in the org.
- **The list panel is not fixed to the left.** In the Classic console shape, `ListPlacement.location` accepts `full`, `top`, or `left`, with `width` required for `left` and `height` required for `top` (L40245–40254).

Console Navigation is the core differentiator of the Service Console. Everything else (utility bar, macros, keyboard shortcuts) works in any Lightning app, but split view and workspace tabs only function in console navigation apps.

### Workspace Tabs and Subtabs — the `workspaceConfig` mechanism

In a console app, records open as **workspace tabs** — full horizontal tabs across the top of the main content area. Each workspace tab has its own **subtab bar** where related records opened from within that workspace appear as narrower tabs.

What Setup calls *navigation rules* is `CustomApplication.workspaceConfig` in the API — an `AppWorkspaceConfig` holding `mappings` (L39796–39799, L40019–40032). Each mapping is a `WorkspaceMapping` with exactly two fields:

| Field | Required | Guide text (L40038–40047) |
|---|---|---|
| `tab` | Yes | "Name of the tab." |
| `fieldName` | No | "The name of the field that specifies the primary tab in which to display `tab` as a subtab. **If not specified, `tab` opens as a primary tab.**" |

So the behaviour is not an enum of three UI choices. It is the presence or absence of a lookup field name:

| Mapping | What the agent sees |
|---|---|
| `<tab>standard-Case</tab>` | A Case opens as its own workspace (primary) tab |
| `<fieldName>AccountId</fieldName><tab>standard-Contact</tab>` | A Contact opens as a subtab of the Account named in `Contact.AccountId` |
| `<fieldName>ParentId</fieldName><tab>standard-Account</tab>` | A child Account opens as a subtab of its parent Account |

The last two are the guide's own console sample (L40701–40724). Three consequences:

- The parent is chosen by **data**, not by whichever tab happens to be focused. A Contact with a null `AccountId` has no parent and falls back to a primary tab.
- `fieldName` is a lookup **on the mapped tab's object**, pointing at the parent. `AccountId` is a field on Contact, not on Account. Reversing it deploys cleanly and does nothing.
- `mappings` is "Required for each tab specified in the `CustomApplication`" (L40025–40032), so a missing entry is both a silent default and a documented omission.

There is no element named `navRules`, `consoleComponents`, or `navigationRules` anywhere in the Metadata API. Full XML in `references/metadata-examples.md` § 1–2.

### Utility Bar

The utility bar is a persistent footer toolbar, and it is a separate metadata component: a `FlexiPage` whose `type` is `UtilityBar` — "A Lightning page used as the utility bar in Lightning Experience apps", API 38.0+ (L67084–67086). The app points at it by developer name through `CustomApplication.utilityBar` (L39788–39794).

| Utility item | Purpose |
|---|---|
| History | List of recently visited records within the current session. UNVERIFIED (2026-09-05): the widely-repeated "console apps only" restriction is Salesforce Help content — neither `api_meta.txt` nor `object_reference.txt` names a History utility item at all, and help.salesforce.com cannot be fetched to confirm it. Test in a standard-navigation app before relying on either answer. |
| Omni-Channel | Displays the agent's Omni-Channel status and incoming work requests; requires Omni-Channel to be enabled and the user to have a presence configuration and routing configuration. |
| Macros | A macros panel so agents can run macros without leaving the active workspace. |
| Open CTI Softphone | Requires a CTI adapter package to be installed; the utility item renders the adapter's phone panel. |
| Quick Text | Surfaces Quick Text snippets for insertion into emails, chats, or feed posts. Snippets are `QuickText` records scoped by a `Channel` **multipicklist** (object_reference L238905–238913). |

Three structural facts that decide where configuration lives:

- **Panel width, height, and the visible label are component decorators on the FlexiPage, not app settings.** A `componentInstanceProperties` entry with `<type>decorator</type>` carries them, and "The `UtilityBar` is the only page type that supports component decorators" (L67352–67363).
- **A utility that must run with no button goes in a `flexiPageRegions` entry of type `Background`** — "a region for background utility items, which aren't visible in the UI. Supported for utility bars only" (L67286–67290). The other region types are `Facet` and `Region`.
- **Utility bars are shared.** "We recommend assigning a utility bar to only one Lightning App, because utility bars are shared. Sharing means that if you change the utility bar in one app, it automatically changes in all apps associated with it" (L39788–39794).

> UNVERIFIED (2026-09-05): the "auto-open when the app loads" / *Start automatically* setting has no counterpart in the FlexiPage field tables in `api_meta.txt`. It is presumably a further decorator property; confirm its property `name` against a retrieved utility bar rather than authoring one from memory.

### Macros

A macro is not one record. "A macro definition consists of a `Macro` object and several associated `MacroInstruction` objects" (object_reference L177953–177958), and neither has a Metadata API type — they move between orgs as **data**, not in a package.

Each `MacroInstruction` has an `Operation` and a `Target`. The `Operation` picklist is exactly `Select`, `Set`, `Insert`, `Submit`, `Close`, plus `IF`, `ELSEIF`, `ELSE`, `ENDIF` for conditional macros in API 46.0 and later (L178095–178126). There is no "Update Field", "Send Email", "Post to Chatter", or "Save Record" operation — those are Setup-UI labels for combinations of the five. The guide's own worked example of sending an email is:

```text
0. SELECT Tab.Case
1.   SELECT QuickAction.Case.Email
2.     SET    Field.EmailMessage.Subject
3.     SET    Field.EmailMessage.ToAddress
4.     INSERT Field.EmailMessage.HtmlBody.cursor
5.     SUBMIT
```

`Target` follows a published grammar and hierarchy (L177980–178020): `Tab.<EntityApiName>` at the root, then `QuickAction.<EntityApiName>.<QuickActionName>`, then `Field.<QATargetEntityApiName>.<FieldApiName>`, with `.cursor` and `.end` suffixes for `INSERT` into text fields. "A target isn't available if its parent isn't" — which is why step 0 selects the tab. `SortOrder` is 0-based and "If there's an incorrect sequence of macro instructions, the macro doesn't execute" (L177958–177961).

`StartingContext` names the object the macro acts on, and it is constrained: "In Lightning Experience, macros are supported on standard and custom objects that allow quick actions and have a customizable page layout" (L177943–177950). Macros can be run manually or as bulk macros — `MacroUsage.IsFromBulk` marks the latter, where "usage is recorded per record" (L178346–178352). Agents must have the Macros user permission — see Gotcha 3, which carries an UNVERIFIED marker on the permission's exact name.

### Keyboard Shortcuts

`KeyboardShortcuts` (L40211–40232) holds two collections: `defaultShortcuts` and `customShortcuts`.

- **`defaultShortcuts.action` is a closed 18-value enum** — `FOCUS_CONSOLE`, `FOCUS_NAVIGATOR_TAB`, `FOCUS_DETAIL_VIEW`, `FOCUS_PRIMARY_TAB_PANEL`, `FOCUS_SUBTAB_PANEL`, `FOCUS_LIST_VIEW`, `FOCUS_FIRST_LIST_VIEW`, `FOCUS_SEARCH_INPUT`, `MOVE_LEFT`, `MOVE_RIGHT`, `UP_ARROW`, `DOWN_ARROW`, `OPEN_TAB_SCROLLER_MENU`, `OPEN_TAB`, `CLOSE_TAB`, `ENTER`, `EDIT`, `SAVE` (L40170–40195). These can be enabled, disabled, or rebound with no code.
- **`customShortcuts` are not declarative.** "Before you can create custom shortcuts, a developer must define the shortcut's action with the `addEventListener()` method in the Salesforce Console Integration Toolkit. You can't create keyboard shortcuts for actions performed outside of the console" (L40052–40054). `CustomShortcut` has five fields — `action`, `active`, `keyCommand`, `description`, `eventName` — and none of them references a `Macro`, so a shortcut cannot be bound directly to a macro at the metadata level.
- **`keyCommand` grammar**: up to four modifier keys followed by exactly one non-modifier key, joined by `+`, non-modifier last. Valid modifiers are `SHIFT`, `CTRL`, `ALT`, `META` (L40062–40074).

### Tab limits and session persistence

Two levers the Setup wizard buries:

- **`isNavTabPersistenceDisabled`** — "Indicates whether workspace tabs are cleared for each new console session (true) or not (false). Applies only to Lightning apps with console navigation", API 54.0+ (L39697–39701). Set it `true` for shared workstations; leave it `false` where agents resume yesterday's queue.
- **`tabLimitConfig`** caps open tabs, with closed value sets: `maxNumberOfPrimaryTabs` accepts `5`, `10`, `20`, `30`; `maxNumberOfSubTabs` accepts `5`, `10`, `15` (L40382–40395). It is required whenever `enableTabLimits` is true — and `enableTabLimits` is documented against "a Salesforce Classic console session" (L39962–39964), so read `references/metadata-examples.md` § 3 before assuming it applies to a Lightning console app.

---

## Common Patterns

### Pattern: Full Service Console App Setup for a Case-Centric Team

**When to use:** A support team works primarily on Cases, with Contacts and Accounts as reference records opened from within Cases. Agents handle multiple cases concurrently.

**How it works:**
1. Setup > App Manager > New Lightning App — choose Console Navigation; add branding.
2. Navigation Items — add Cases, Contacts, Accounts, Knowledge in that order, and set `defaultLandingTab` explicitly rather than relying on tab order.
3. Utility Bar — build one `UtilityBar` FlexiPage owned by this app with History, Omni-Channel, Macros, and Open CTI Softphone (if CTI is configured).
4. User Profiles — assign Service Cloud agent profiles via `PermissionSet.applicationVisibilities`; `CustomApplication` has no visibility field of its own.
5. Write one `workspaceConfig` mapping per tab — Case and Account with no `fieldName` (primary tabs), Contact keyed on `AccountId`, Knowledge with no `fieldName`.
6. Create Macro records for the top three agent repetitive tasks, expressed as `Select` / `Set` / `Insert` / `Submit` instruction rows with 0-based `SortOrder`.
7. Create Quick Text entries, one record per snippet with every applicable channel in the `Channel` multipicklist.

**Why not the alternative:** Using a standard navigation app forces agents to navigate away from the current case every time they open a contact or account, losing context and increasing handle time.

### Pattern: Workspace Mappings for Complex Object Hierarchies

**When to use:** Agents work with Cases linked to Assets or Work Orders, and those child records need to open in context rather than as independent primary tabs.

**How it works:**
1. Map the parent object with no `fieldName` — it opens as a workspace tab.
2. Map each child on the lookup field that lives **on the child** and points at the parent: `<fieldName>Case__c</fieldName><tab>Work_Order__c</tab>`.
3. If agents also open Assets independently, the object cannot be both — a tab is either mapped with a `fieldName` or without one. Give the second workflow its own console app rather than looking for a conditional rule that does not exist.
4. Confirm the parent's tab is in the app. A mapping that points at an object with no tab has nothing to nest under.

**Why not the alternative:** Leaving tabs unmapped means every record click opens a new primary tab, quickly filling the tab bar and making it difficult to track the active case — and because `mappings` is documented as required per tab, the omission is a defect rather than a default.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New app for case-handling agents | Create a new app with `navType` `Console` | Standard navigation loses agent context between records |
| Existing standard app used by service team | Create a new console app; do not convert | `navType` is documented "Not updateable" (L39719) |
| Related record should open in context | Map its tab with the lookup `fieldName` that points at the parent | Absence of `fieldName` means primary tab, not inheritance (L40044–40046) |
| Two teams want different tab behaviour for one object | Two console apps | `WorkspaceMapping` has no `profile` field; record-page overrides do (L39973–39976) |
| Agents need phone panel in the console | Add Open CTI Softphone utility; ensure CTI adapter is installed | Softphone utility renders the CTI adapter UI inside the console |
| A utility must run with no visible button | A second `flexiPageRegions` entry of type `Background` | "Supported for utility bars only" (L67286–67290) |
| Agents need one-click repetitive action | Create a Macro + MacroInstruction rows; add the Macros utility | Macros automate multi-step actions inside the active workspace |
| Agents need standard reply snippets | One Quick Text record per snippet, all channels on it | `Channel` is a multipicklist (object_reference L238905–238913) |
| Shared workstations must not inherit open tabs | `isNavTabPersistenceDisabled` = `true` | Console-only field, API 54.0+ (L39697–39701) |
| One-keystroke custom action requested | Confirm developer capacity first, else use `defaultShortcuts` | Custom shortcuts need an `addEventListener()` handler (L40052–40054) |

---

## Recommended Workflow

1. **Inventory the target and fill in the template.** Complete `templates/service-console-configuration-template.md` — every navigation tab, and for each one the parent object and the lookup field that names it. Retrieve any existing app and its utility bar first: `sf project retrieve start --metadata CustomApplication:<Name>,FlexiPage:<UtilityBar>`. Confirm from `AppDefinition.NavType` whether you are editing or rebuilding.
2. **Decide build-vs-rebuild before configuring anything.** If the existing app's `navType` is `Standard`, stop and plan a new app (Gotcha 1). Check `SELECT DeveloperName, UtilityBar FROM AppDefinition WHERE UtilityBar != null` for utility bars shared with other apps (Gotcha 12).
3. **Write the utility bar FlexiPage first**, following `references/metadata-examples.md` § 4 — visible items with decorator width/height/label, a `Background` region for listeners. Copy the real template and component names out of the retrieve from step 1; do not type them from memory.
4. **Write the `CustomApplication`** per `references/metadata-examples.md` § 1 — `navType` `Console`, `defaultLandingTab`, `isNavTabPersistenceDisabled`, `utilityBar`, and one `workspaceConfig` mapping per `<tabs>` entry. Cross-check every `fieldName` against the child object's fields, not the parent's (Gotcha 7).
5. **Author Quick Text and Macros as data**, per `references/metadata-examples.md` § 5 — CSVs for `QuickText`, then `Macro`, then `MacroInstruction` with 0-based `SortOrder`, `Operation` from the five-value enum, and `Target` following the documented grammar.
6. **Run the checker before deploying**: `python3 scripts/check_service_console_configuration.py --manifest-dir force-app/main/default`. It fails on a console app with no mappings, a mapping whose `fieldName` is not a field on that tab's object, a `utilityBar` pointing at a FlexiPage that is missing or not of type `UtilityBar`, out-of-enum `tabLimitConfig` or `listPlacement` values, and `profileActionOverrides` referencing a FlexiPage not in the manifest.
7. **Deploy in order and verify in the org.** Follow `references/metadata-examples.md` § 7, then run the § 8 queries — `AppDefinition.NavType` = `Console`, the utility bar unshared, `MacroInstruction` ordered from `SortOrder` 0, and `MacroUsage` free of `ACCESS` failures. Finish by logging in as an agent and confirming a Contact opened from a Case lands as a subtab of the right Account.

---

## Review Checklist

Before marking service console configuration complete:

- [ ] `navType` is `Console` and `isServiceCloudConsole` is absent from the Lightning app file
- [ ] Every `<tabs>` entry has a matching `workspaceConfig` mapping — including the primary-tab ones
- [ ] Every mapping `fieldName` is a lookup on that tab's own object, pointing at an object whose tab is also in the app
- [ ] `defaultLandingTab` is set deliberately, not inherited from tab order
- [ ] The `utilityBar` FlexiPage exists, is `type` `UtilityBar`, and no other app names it
- [ ] Panel width/height/label are decorator properties on the FlexiPage, not invented app fields
- [ ] `isNavTabPersistenceDisabled` reflects a decision about shared workstations
- [ ] App visibility assigned via `PermissionSet.applicationVisibilities` (the app file has no visibility field)
- [ ] Macro instructions use only `Select` / `Set` / `Insert` / `Submit` / `Close` (+ `IF`/`ELSEIF`/`ELSE`/`ENDIF`) with 0-based `SortOrder`
- [ ] Quick Text records carry every applicable channel on one record, with `IsInsertable` set explicitly
- [ ] `scripts/check_service_console_configuration.py` passes against the manifest directory
- [ ] Tested end-to-end as an agent user — split view active, subtabs open under the right parent, macros execute

---

## Salesforce-Specific Gotchas

Full detail, with guide line references, in `references/gotchas.md`.

1. **`navType` is "Not updateable"** — there is no supported Standard-to-Console conversion; plan a rebuild (Gotcha 1).
2. **A tab with no mapping opens as a primary tab, silently** — and `mappings` is documented as required per tab (Gotcha 6).
3. **`fieldName` lives on the child object, and nothing validates the direction** — a reversed mapping deploys clean and does nothing (Gotcha 7).
4. **`isServiceCloudConsole` is null on Lightning console apps** — audits keyed on it report zero console apps (Gotcha 8).
5. **`QuickText.Channel` is a multipicklist** — one record can serve several channels; duplicating per channel just creates drift (Gotcha 4).
6. **Utility bars are shared between apps** — editing one app's footer can change another's (Gotcha 12).
7. **A Flexipage App-Default override cannot be deleted by a destructive change** — reset its `<type>` to `default` instead (Gotcha 10).
8. **Custom keyboard shortcuts require developer code first** and cannot point at a macro (Gotcha 11).
9. **`AppWorkspaceConfig` and `AppComponentList` were renamed in API 42.0** — old element names still circulate in blog posts (Gotcha 9).
10. **Omni-Channel and Macros both fail quietly** when their prerequisites are missing (Gotchas 2, 3).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `applications/<Name>.app-meta.xml` | `CustomApplication` with `navType` `Console`, `workspaceConfig` mappings, `utilityBar`, and `isNavTabPersistenceDisabled` |
| `flexipages/<Name>.flexipage-meta.xml` | The utility bar, a `FlexiPage` of `type` `UtilityBar`, with decorator sizing and any `Background` region |
| `permissionsets/<Name>.permissionset-meta.xml` | `applicationVisibilities` and `tabSettings` — the app file carries no visibility |
| `QuickText.csv` | Quick Text records with the `Channel` multipicklist and `IsInsertable` |
| `Macro.csv` + `MacroInstruction.csv` | Macro definitions and their 0-based, grammar-conformant instruction rows |
| `package.xml` + deploy order | What ships as metadata, what ships as data, and in what sequence |
| Verification queries | `AppDefinition`, `MacroInstruction`, `MacroUsage` checks that prove the deploy landed |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing deployable console `CustomApplication` XML, the `workspaceConfig` mappings, the `UtilityBar` FlexiPage, the Quick Text / Macro CSVs, package.xml, deploy order, and the post-deploy verification queries |
| `references/gotchas.md` | The console app deployed cleanly and behaves wrong — records opening as the wrong kind of tab, a macro that does nothing, a utility bar that changed two apps, or an override that will not delete |
| `references/examples.md` | Designing the console for a persona before any XML exists — a Tier-1 build and an escalation macro, end to end |
| `references/well-architected.md` | Justifying single-app vs multi-app, macro-vs-Flow, and utility auto-load tradeoffs, or locating the official source behind a claim in this skill |
| `references/llm-anti-patterns.md` | Reviewing console guidance an AI assistant produced, especially "change the navigation type" and "set the navigation rule to subtab of current workspace" |
| `templates/service-console-configuration-template.md` | Running workflow step 1 — the tab, mapping, utility, and macro inventory |
| `scripts/check_service_console_configuration.py` | Workflow step 6, before every deploy of a console app or its utility bar |

---

## Related Skills

- `admin/app-and-tab-configuration` — the app skeleton, `CustomTab` shapes, branding, form factors, and app/tab visibility that this skill builds the console layer on top of
- `admin/omni-channel-routing-setup` — Service Channels, routing configurations, presence configurations, and queues behind the Omni-Channel utility
- `admin/case-management-setup` — the Case object, record types, and support process the console is built to work
- `admin/global-actions-and-quick-actions` — the quick actions that `MacroInstruction.Target` addresses as `QuickAction.<Entity>.<Name>`
- `admin/knowledge-base-administration` — Knowledge articles and the sidebar targets macros can drive (`SidebarCmp.Knowledge`)
- `admin/permission-set-architecture` — `applicationVisibilities` and `tabSettings`, without which the console app is invisible
- `data/data-loader-and-tools` — loading the `QuickText`, `Macro`, and `MacroInstruction` CSVs
- `lwc/lwc-console-workspace-api` — opening, refreshing, and closing console tabs from component code, which this skill does not cover
