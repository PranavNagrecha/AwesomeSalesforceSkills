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
