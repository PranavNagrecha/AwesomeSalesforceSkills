# Gotchas — App and Tab Configuration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Utility Bar Does Not Appear in the Salesforce Mobile App

**What happens:** Admins configure a utility bar with CTI, History, or custom LWC utilities, and users report that none of it appears when they use the Salesforce mobile app. The utility bar is completely absent on mobile.

**When it occurs:** Any time a Lightning app has a utility bar and users access it via the Salesforce mobile app (iOS/Android). This affects all utility items without exception.

**How to avoid:** Design mobile workflows independently of utility bar functionality. If CTI is required on mobile, the telephony vendor's mobile integration (not the utility bar component) must be used. Document this limitation in the app's requirements and set expectations with stakeholders before rollout.

---

## Gotcha 2: Profile Tab Setting "Tab Hidden" Overrides App Navigation

**What happens:** An admin adds a tab to a Lightning app and assigns the profile, but users on that profile still cannot see the tab in the navigation bar. No error is shown; the tab is simply absent.

**When it occurs:** When the profile's Tab Settings for that particular tab are set to "Tab Hidden." This setting is independent of the app's navigation item list. The profile Tab Setting is evaluated first; if it is "Tab Hidden," the navigation item is silently suppressed.

**How to avoid:** After adding a tab to an app, verify the target profile's Tab Settings (Setup > Profiles > [Profile] > Tab Settings). Set the tab to at minimum "Default Off" to allow users to access it. "Default On" pins it in their navigation bar by default. Note: Users can reorder their own navigation items, but they cannot unhide a tab that is set to "Tab Hidden" on their profile.

---

## Gotcha 3: Lightning App Changes Require App Refresh or Re-Login to Take Effect

**What happens:** An admin adds a new navigation item or changes utility bar configuration on a Lightning app, but users who are already logged in do not see the change. They continue seeing the previous app layout until they refresh or log out.

**When it occurs:** Whenever an in-session user's app configuration is updated by an admin. The app configuration is cached client-side in Lightning Experience.

**How to avoid:** After making app configuration changes that affect active users (adding a tab, changing utility bar, modifying profile visibility), notify affected users to refresh their browser (F5 or Cmd+R) or log out and back in. For high-impact changes, consider scheduling them during low-traffic periods.

---

## Gotcha 4: Renaming an App Does Not Change Its API Name

**What happens:** An admin renames a Lightning app from "Sales App" to "Revenue Operations" in App Manager. Deployments, permission sets, and metadata that reference the app by API name (`Sales_App`) continue to work. However, new configurations that search by label may not find the app if they expect the new name.

**When it occurs:** When an app is renamed after initial creation. Salesforce does not update the API name when the label changes.

**How to avoid:** Use the API name (visible in App Manager's list view) when referencing apps in metadata, CI/CD pipelines, or permission set configurations. If a rename is required and the API name must also change, a new app must be created — Salesforce does not allow renaming the API name of an existing `CustomApplication` record through the UI.

---

## Gotcha 5: Console App Type Cannot Be Changed After Creation

**What happens:** An admin creates a standard Lightning app but later realizes users need the console layout (split-view, work queue). There is no option to convert an existing standard Lightning app to a console app or vice versa.

**When it occurs:** When app type selection is made at creation and the requirements change later.

**How to avoid:** Clarify upfront whether users need a console experience (high-volume case or lead processing, side panel work) or a standard navigation app. If uncertain, prototype with both types in a sandbox before creating the production app. Switching types requires creating a new app and re-assigning profiles.

**Why the API cannot rescue you either:** `CustomApplication.navType` is documented as "Not updateable" (api_meta.txt L39719–39724), as is `uiType`, which selects `Aloha` (Salesforce Classic) versus `Lightning` (api_meta.txt L39782–39787). Deploying a `.app-meta.xml` whose `navType` differs from the live app does not convert it — the Setup UI restriction is a restatement of the metadata contract, not a separate limitation.

---

## Gotcha 6: A Perfect App File Deploys Green and Nobody Can Open the App

**What happens:** `sf project deploy start` reports Succeeded for the `CustomApplication`, the app shows in Setup → App Manager, and every non-admin user's App Launcher looks exactly as it did before. No error, no warning, nothing in the deploy log.

**When it occurs:** Every time the deployment package contains the app but not the `Profile` or `PermissionSet` that grants it. `CustomApplication` has no visibility field — the entire field list (api_meta.txt L39641–39800) contains `label`, `tabs`, `navType`, `brand`, `utilityBar` and so on, and nothing that names a user, profile, or permission set. Access lives in `PermissionSetApplicationVisibility` (`application` + `visible`, api_meta.txt L94903–94910) or `ProfileApplicationVisibility` (`application` + `visible` + a required `default` flag, of which "Only one app per profile can be set to true", api_meta.txt L97897–97907).

**How to avoid:** Treat the app and its access grant as one deployable unit. Put the `PermissionSet` in the same `package.xml` and deploy it after the app, since the permission set cannot reference an application that does not exist yet. Verify by querying `AppDefinition` **as a target user, not as the admin** — that object "Metadata is returned only for apps that the current user can access" (object_reference.txt L34140–34143), so zero rows is a positive answer, not an empty one.

---

## Gotcha 7: Editing One App's Utility Bar Silently Edits Every Other App's

**What happens:** An admin adds a Macros utility to the Service Console. A week later the Sales team reports a Macros icon they never asked for, sitting in their own app's utility bar. Nobody deployed anything to the Sales app.

**When it occurs:** Whenever two or more `CustomApplication` records name the same `<utilityBar>` FlexiPage. The utility bar is not stored inside the app — the app holds only "the developer name of the utility bar associated with this app", and the guide states the consequence directly: "We recommend assigning a utility bar to only one Lightning App, because utility bars are shared. Sharing means that if you change the utility bar in one app, it automatically changes in all apps associated with it" (api_meta.txt L39788–39795). The utility bar itself is a separate `FlexiPage` whose `type` is `UtilityBar` (api_meta.txt L67084–67086).

**How to avoid:** One utility bar FlexiPage per app, named after the app, even when two apps start with identical utilities — the cost of the duplicate is one file, the cost of sharing is a cross-team incident. Before editing any utility bar, query which apps point at it: `SELECT DeveloperName, UtilityBar FROM AppDefinition WHERE UtilityBar != null`. And because the app's `<utilityBar>` is a reference rather than a definition, the FlexiPage must exist in the org or be earlier in the same deployment — deploying the app alone against a missing utility bar fails on the reference.

---

## Gotcha 8: In a Console App, Tab Order Does Not Decide What Opens as a Subtab

**What happens:** A dispatcher opens a Field Visit expecting it to appear as a subtab under the Account they were already working. It opens as its own workspace tab instead, and the Account tab they had open is now a second, unrelated tab. The navigation order in the app is exactly as designed.

**When it occurs:** When a console app's `workspaceConfig` mapping for that tab omits `fieldName`. `WorkspaceMapping.fieldName` is "The name of the field that specifies the primary tab in which to display tab as a subtab. **If not specified, tab opens as a primary tab**" (api_meta.txt L40044–40047). The parent/child relationship is driven entirely by that lookup field, not by the order of `<tabs>` elements and not by the object's master-detail relationships. A mapping is also "Required for each tab specified in the CustomApplication" (api_meta.txt L40028–40032), so a tab that was added to a console app without a matching `<mappings>` entry has no defined open behaviour at all.

**How to avoid:** For every tab in a console app, write a `<mappings>` entry, and decide deliberately whether it carries a `fieldName`. Omitting `fieldName` is the correct choice for a genuine workspace anchor (Account, Case) and the wrong one for anything that should nest. After deploy, confirm without re-retrieving the app: `AppTabMember.WorkspaceDriverField` "Refers to the workspace mapping in the CustomApplication Metadata API object" (object_reference.txt L36749–36760).

---

## Gotcha 9: The App Is Invisible on Phones Because `formFactors` Was Never Written

**What happens:** Desktop users see the new app immediately. Mobile users open the Salesforce mobile app, tap the App Launcher, and the app is not there. Their profile grants it, their tabs are Visible, and nothing is misconfigured in Setup.

**When it occurs:** When the `.app-meta.xml` declares `<formFactors>Large</formFactors>` and nothing else. `Large` means "For a desktop using Lightning Experience"; `Small` means "For a mobile device using the Salesforce mobile app"; `Medium` is "Reserved for future use"; and a null value means Salesforce Classic desktop (api_meta.txt L39666–39685). `Small` became valid for Lightning apps only in API version 47.0. The inverse bites Classic orgs: "For Salesforce Classic apps in packages created with API 38.0 or later, you must set `formFactors` to `Large` for Salesforce Classic apps to appear in the Lightning Experience desktop."

**How to avoid:** Decide the form factors when the app is designed, not when a user reports the gap, and write both elements explicitly rather than relying on a default. Verify per-app with `AppDefinition.IsSmallFormFactorSupported` / `IsLargeFormFactorSupported`, which "Indicates whether the Small [/ Large] form factor is set in the CustomApplication metadata" (object_reference.txt L34197–34204, L34260–34272), and per-tab with `TabDefinition.IsAvailableInMobile` (object_reference.txt L277724–277730) — a mobile-visible app whose key tab is not mobile-available lands the user on an empty nav bar.

---

## Gotcha 10: `standard-` Is Part of the Tab Name, and Dropping It Removes the Tab Without an Error

**What happens:** An admin hand-writes `<tabs>Account</tabs>` into an app file, deploys, and the Accounts item is gone from the navigation bar. The deploy succeeded.

**When it occurs:** From API version 13.0 onward, built-in tabs "are prefixed with `standard-`. For example, to reference the Account tab you would use `standard-Account`" (api_meta.txt L39767–39775). Only API version 12.0 used the bare name. The same prefix rule applies to `defaultLandingTab`, whose value is "The fullName of a standard tab or custom tab" (api_meta.txt L39661–39663) — the guide's own standard-app sample sets it to `standard-home` (api_meta.txt L40521). The prefix is not consistently cased across standard tabs either: the guide's Lightning sample mixes `standard-Account` and `standard-Case` with `standard-report` (api_meta.txt L40501–40510).

**How to avoid:** Never author a standard tab name from memory. Retrieve an existing app that already carries the tab and copy the exact string, or read it from the org: `SELECT Name, Label, IsCustom FROM TabDefinition WHERE IsCustom = false`. `TabDefinition.Name` is "The developer name of the tab" (object_reference.txt L277764–277770), which is the value `<tabs>` expects.

---

## Gotcha 11: A Profile Action Override Cannot Be Removed With `destructiveChanges.xml`

**What happens:** An admin assigned a custom record page to one profile inside an app, then wants that profile back on the org default page. They add the override to `destructiveChanges.xml`, deploy, and nothing changes — or the deploy fails without explaining what to do instead.

**When it occurs:** Any attempt to delete a `profileActionOverrides` entry from a `CustomApplication` by destructive change. The guide is explicit: "You can't delete custom app ProfileActionOverrides by deploying with destructiveChange.xml" (api_meta.txt L40398–40407). The same page adds a second trap for `AppActionOverride`: "A Flexipage AppActionOverride set to App Default can't be deleted via Metadata API. Instead, remove the override using the page assignment wizard in the Lightning App Builder UI" (api_meta.txt L39871–39877).

**How to avoid:** Follow the documented removal sequence instead — retrieve the app, find the `<profileActionOverrides>` section, remove the `<content>` row, change that section's `<type>` from `flexipage` to `default`, rezip, and deploy. The guide adds an operational warning that costs a deploy cycle when ignored: "we recommend that you do a fresh retrieve every time you want to delete a new override. Don't use a previously retrieved file." Multiple overrides can go in one deploy, but each round must start from a current retrieve.
