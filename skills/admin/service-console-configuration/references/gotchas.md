# Gotchas — Service Console Configuration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

Guide line references are `api_meta.txt` (Metadata API Developer Guide) and `object_reference.txt`
(Object Reference), Summer '26 / v62 —
https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf and
https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf

## Gotcha 1: Navigation Type Is Permanently Set at App Creation

**What happens:** Once a Lightning app is saved with Standard Navigation, there is no setting or button in
Setup to switch it to Console Navigation. The Metadata API guide marks the field itself: `navType` is
"**Not updateable**. Indicates the type of navigation the app uses" (api_meta.txt L39719–39723). Neither
Setup nor a metadata deploy has a documented conversion path.

**When it occurs:** Admins realize they need split view after the standard app has already been configured
with navigation items, utility bar items, custom branding, and profile assignments. Attempting to "update"
the navigation type via metadata deploy may appear to succeed but is not a documented conversion.

**How to avoid:** Decide the navigation type before creating the app. If there is any chance the team will
need console capabilities, create a console navigation app from the start. To migrate an existing team,
create a new console app and recreate all navigation items and utility bar settings. Capture the existing
configuration first with `sf project retrieve start --metadata CustomApplication:<Name>`.

---

## Gotcha 2: Omni-Channel Utility Shows a Blank or Error State Without Prior Setup

**What happens:** Admins add the Omni-Channel utility to the console app's utility bar and deploy. Agents
open the console and see a blank Omni-Channel panel or an error message. No work items appear and agents
cannot set their status.

**When it occurs:** The Omni-Channel utility is added before Omni-Channel itself is enabled in the org, or
before any Service Channels or Presence Configurations have been created. Nothing in the FlexiPage that
carries the widget expresses a dependency on them, so the deploy is clean.

**How to avoid:** Before adding the Omni-Channel utility:
1. Enable Omni-Channel in Setup > Omni-Channel Settings.
2. Create at least one Service Channel (e.g., Cases).
3. Create a Presence Configuration and assign it to the agent profile.
4. Verify the agent user is assigned a routing configuration and at least one `ServicePresenceStatus`
   ("Represents a presence status that can be assigned to a service channel", object_reference L258947).

Sequencing and the objects involved belong to `admin/omni-channel-routing-setup`.

---

## Gotcha 3: Macros Silently Do Nothing Without the Macros User Permission

**What happens:** An admin creates a Macro and adds the Macros utility to the console app. Agents open the
utility panel, select the macro, and click Run. Nothing happens — no field changes, no email sent, no error
message displayed.

**When it occurs:** The agent's profile or permission set does not have the "Macros" user permission
enabled. The Macros utility panel renders and the macro list is visible, but execution is blocked.

> UNVERIFIED (2026-09-05): the user-permission names "Macros" and "Manage Macros" do not appear anywhere in
> `api_meta.txt` or `object_reference.txt` — they are Salesforce Help / Setup-UI names, and
> help.salesforce.com cannot be fetched to confirm the exact spelling or the Permission Set API name.
> Confirm against Setup > Permission Sets > System Permissions in the target org before writing them into a
> `PermissionSet` file.

**How to avoid:** Do not diagnose this by guessing at permission names — query the evidence. `MacroUsage`
records the outcome of every run, and `FailureReason` is a picklist of `ACCESS`, `GENERIC`, `TIMEOUT`,
`UNSUPPORTED` (object_reference L178311–178322):

```sql
SELECT MacroId, ExecutionState, FailureReason, ExecutedInstructionCount, InstructionCount
FROM MacroUsage WHERE ExecutionState = 'FAILURE' ORDER BY ExecutionEndTime DESC
```

A wall of `ACCESS` is the permission problem. `UNSUPPORTED` is a `Target` the object does not offer.
Test as an agent user in a sandbox before deploying to production.

---

## Gotcha 4: `QuickText.Channel` Is a Multipicklist — Duplicating Records per Channel Is Wasted Work

**What happens:** An admin creates one Quick Text record per channel — the same greeting three times, for
Email, for Chat, and for the portal — because the Channel field is assumed to hold a single value. The
library triples in size, and edits then have to be applied three times, so the copies drift apart.

**When it occurs:** Whenever the field is treated as a picklist. It is not: "`Channel` — Type
**multipicklist** … A multi-select picklist that can be used to specify where specific quick text messages
are available, such as in Chat or in the Email publisher in Case Feed" (object_reference L238905–238913).
There is also no fixed enum of channel values published in the guides — `QuickText.Channel` is backed by
the `QuickTextChannel` **StandardValueSet** (api_meta.txt L142921), so the available values are whatever
that value set holds in the org.

**How to avoid:** Put every applicable channel on one record — in a Data Loader CSV the multipicklist
separator is `;` (`Email;Chat`). Read the org's actual channel values from the `QuickTextChannel` standard
value set rather than assuming a list. And set `IsInsertable` deliberately: it is the "Include in selected
channels" checkbox, and while it defaults to `true` for records created from the Quick Text page or via the
API, it defaults to **`false`** for records created by the Einstein Reply Recommendations reply publishing
process (object_reference L238932–238946) — so a library exported from that feature and re-loaded elsewhere
can arrive entirely invisible.

---

## Gotcha 5: Workspace Mappings Are App-Scoped, Not Profile-Scoped

**What happens:** Two agent teams share a console app. Team A wants Contacts to open as subtabs; Team B
needs Contacts to open as workspace tabs (they frequently work Contact records independently). An admin
cannot satisfy both teams with a single app.

**When it occurs:** Different agent workflows require different tab behaviour for the same object, but the
app is shared across teams. The asymmetry is visible in the metadata: `AppWorkspaceConfig` and
`WorkspaceMapping` have no `profile` field at all (api_meta.txt L40019–40047), whereas
`AppProfileActionOverride` — which governs record-page overrides in the same app file — explicitly does
carry one (L39973–39976).

**How to avoid:** Create separate console apps for the two teams. This is a platform design constraint —
there is no per-profile workspace mapping. If the teams are similar enough, standardize the mapping and
train agents on the resulting behavior rather than maintaining two apps that drift.

---

## Gotcha 6: A Tab With No Mapping Silently Opens as a Primary Tab

**What happens:** An admin adds Contact to a console app's navigation items, deploys, and every Contact an
agent clicks from a Case opens as its own full workspace tab. Within an hour the tab bar is unreadable and
agents cannot tell which case they were working. Nothing errored.

**When it occurs:** `workspaceConfig` is absent, or present but missing a `mappings` entry for that tab.
The default is not "inherit from the parent" — `WorkspaceMapping.fieldName` reads "The name of the field
that specifies the primary tab in which to display `tab` as a subtab. **If not specified, `tab` opens as a
primary tab**" (api_meta.txt L40044–40046), and `AppWorkspaceConfig.mappings` is "Required for each tab
specified in the `CustomApplication`" (L40025–40032). Omission is therefore both a silent default *and* a
violation of a stated requirement.

**How to avoid:** Write one `mappings` entry per `<tabs>` entry, always — including the ones that should be
primary tabs, where the entry is just `<tab>` with no `fieldName`. Making the primary-tab case explicit is
what tells the next reader it was a decision. `scripts/check_service_console_configuration.py` fails an app
whose tab list and mapping list disagree.

---

## Gotcha 7: `fieldName` Names a Lookup on the Child's Object, and Nothing Validates the Direction

**What happens:** An admin writes `<fieldName>ContactId</fieldName><tab>standard-Account</tab>`, intending
"open the Account under the Contact." It deploys cleanly. In the console, Accounts keep opening as primary
tabs and the subtab never appears.

**When it occurs:** Whenever the mapping is read as "the parent's field" rather than "a field on the mapped
tab's own object." The guide's own sample is the correct direction: `standard-Account` mapped on `ParentId`
(a field on Account, pointing at the parent Account) and `standard-Contact` mapped on `AccountId` (a field
on Contact, pointing at the Account) — api_meta.txt L40712–40724. The lookup lives on the record that
becomes the *subtab*.

Two further consequences the Setup wording hides: the parent workspace is chosen by **data**, not by
whichever tab is focused — so a Contact whose `AccountId` is null has no parent to nest under and falls
back to a primary tab; and the parent object's tab must itself be in the app.

**How to avoid:** For every mapping with a `fieldName`, state the sentence out loud: "`<fieldName>` is a
lookup **on** `<tab>`'s object **to** the parent object, and the parent's tab is also in this app." The
checker verifies exactly that against the `CustomObject` files in the manifest and flags a `fieldName` that
does not resolve to a field on the mapped object.

---

## Gotcha 8: `isServiceCloudConsole` Is Null on Every Lightning Console App

**What happens:** An audit script, a change-set filter, or an org-comparison report enumerates "our console
apps" by looking for `isServiceCloudConsole = true`, and returns zero rows in an org that runs entirely on
Lightning console apps. The team concludes there are no console apps to review.

**When it occurs:** Any time Classic-era knowledge is applied to a Lightning org. The field is explicit:
"Indicates if the application is a Salesforce Classic console app. **For Lightning Experience console apps,
this field is null and the `navType` field is set to `Console`**" (api_meta.txt L39702–39706).

The same split runs through the sibling elements: `AppPreferences` is "the preferences for a Salesforce
Classic console app", `enableTabLimits` governs "a **Salesforce Classic** console session"
(L39962–39964), and `CustomShortcut` is "custom keyboard shortcuts assigned to a Salesforce console app
**in Salesforce Classic**" (L40052). Reading any of them as the Lightning shape produces confident, wrong
guidance.

**How to avoid:** Detect console apps by `navType == 'Console'` in metadata and by
`AppDefinition.NavType = 'Console'` in SOQL (object_reference L34301–34309). Treat `isServiceCloudConsole`
purely as a Classic marker.

---

## Gotcha 9: `AppWorkspaceConfig` and `AppComponentList` Were Renamed in API 42.0

**What happens:** A deploy fails with an unknown-element error, or a retrieve from an older tooling
configuration produces XML that no longer matches the current guide. Hand-written XML copied from an old
blog post uses `<workspaceMappings>` or `<customApplicationComponent>` and is rejected.

**When it occurs:** Any project pinned below API 42.0, or any example predating it. "In API version 42.0,
this type was renamed from `WorkspaceMappings` to `AppWorkspaceConfig`" (api_meta.txt L40022), and
"In API version 42.0, this type was renamed from `CustomApplicationComponents` to `AppComponentList`", with
its `components` field renamed from `customApplicationComponent` (L39900–39907). The keyboard-shortcut
collections moved the same way — `customShortcut` → `customShortcuts` and `defaultShortcut` →
`defaultShortcuts` (L40216–40232) — and `tab` → `tabs` on `CustomApplication` itself (L39767–39774).

**How to avoid:** Pin `sourceApiVersion` at 42.0 or later, and never hand-copy console XML from an
undated source. Retrieve the shape from the target org and edit that.

---

## Gotcha 10: A Flexipage App-Default Override Cannot Be Deleted by Deploying a Destructive Change

**What happens:** A console app has a `profileActionOverrides` entry assigning a custom record page as the
App Default. The team removes it from the source file and deploys, or adds it to `destructiveChanges.xml`.
The deploy succeeds. The override is still there.

**When it occurs:** Whenever the override type is `Flexipage` and its scope is App Default: "A `Flexipage`
`AppActionOverride` set to App Default can't be deleted via Metadata API. Instead, remove the override using
the page assignment wizard in the Lightning App Builder UI" (api_meta.txt L39859–39861). The guide adds:
"You can't delete custom app `ProfileActionOverrides` by deploying with `destructiveChange.xml`"
(L40397–40399).

**How to avoid:** Use the documented workaround instead of a delete — retrieve the app, find the
`<profileActionOverrides>` section, remove the `<content>` row, change that entry's `<type>` from
`flexipage` to `default`, rezip and deploy (L40397–40409). The guide recommends a fresh retrieve for every
override you reset rather than reusing a previously retrieved file. Multiple overrides can be reset in one
deploy.

---

## Gotcha 11: A Custom Keyboard Shortcut Needs Developer Code First, and Cannot Point at a Macro

**What happens:** An admin promises agents a one-keystroke escalation, writes a `customShortcuts` entry with
`<action>Escalate</action>` and an `eventName`, and deploys. The key combination does nothing.

**When it occurs:** Whenever a custom shortcut is treated as declarative. "Before you can create custom
shortcuts, a developer must define the shortcut's action with the `addEventListener()` method in the
Salesforce Console Integration Toolkit. You can't create keyboard shortcuts for actions performed outside of
the console" (api_meta.txt L40052–40054). `CustomShortcut` has exactly five fields — `action`, `active`,
`keyCommand`, `description`, `eventName` — and none of them references a `Macro` record, so a shortcut
cannot be bound directly to a macro through this metadata.

`keyCommand` has its own grammar: up to four modifier keys followed by exactly one non-modifier key, joined
by `+`, with the non-modifier last; the valid modifiers are `SHIFT`, `CTRL`, `ALT`, `META`
(L40062–40074).

**How to avoid:** Scope the developer work before promising the shortcut. If no developer is available, use
the `defaultShortcuts` set instead — an 18-value enum (`FOCUS_CONSOLE`, `CLOSE_TAB`, `MOVE_RIGHT`, `SAVE`,
and so on, L40170–40195) that can be enabled, disabled, or rebound with no code.

---

## Gotcha 12: Utility Bars Are Shared Between Apps, and Panel Size Lives on the FlexiPage

**What happens:** An admin widens the Macros panel for the Tier-1 console and, without touching it, the
Tier-2 console's footer changes too. Or: an admin looks for panel width in the app file, cannot find it, and
concludes it is not configurable in metadata.

**When it occurs:** Both symptoms come from the same structural fact — the utility bar is not part of the
app. `CustomApplication.utilityBar` holds only "the developer name of the utility bar associated with this
app", and the guide warns: "We recommend assigning a utility bar to only one Lightning App, because utility
bars are shared. Sharing means that if you change the utility bar in one app, it automatically changes in
all apps associated with it" (api_meta.txt L39788–39794).

Panel width, height, and the visible label live on that FlexiPage as **component decorators** — a
`componentInstanceProperties` entry whose `<type>` is `decorator`. "The `UtilityBar` is the only page type
that supports component decorators" (L67352–67363). A utility that must run with no button at all goes in a
`flexiPageRegions` entry of `type` `Background`, "a region for background utility items, which aren't
visible in the UI. Supported for utility bars only" (L67286–67290).

**How to avoid:** One utility bar FlexiPage per app, named after the app. Before editing one, check who
else uses it:

```sql
SELECT DeveloperName, Label, UtilityBar FROM AppDefinition WHERE UtilityBar != null
```

Two apps sharing a `UtilityBar` Id means every footer change is a two-app change.
