# LLM Anti-Patterns — App and Tab Configuration

Common mistakes AI coding assistants make when generating or advising on Lightning app and tab configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming custom object tabs exist automatically

**What the LLM generates:** "Add the Invoice__c object to your Lightning app's navigation items in App Manager."

**Why it happens:** LLMs conflate objects with tabs. Training data rarely emphasizes that a custom object must have a custom tab created before it can appear in any app's navigation. The LLM skips the tab creation step entirely.

**Correct pattern:**

```
1. Go to Setup → Tabs → Custom Object Tabs → New.
2. Select Invoice__c, choose a tab style, and save.
3. Go to Setup → App Manager → Edit your Lightning app.
4. In the Navigation Items step, move Invoice__c from Available to Selected.
```

**Detection hint:** If instructions mention adding an object to app navigation without a prior "create a custom tab" step, the tab prerequisite is missing. Search for `Setup → Tabs` or `Custom Object Tabs` in the output.

---

## Anti-Pattern 2: Confusing app visibility assignment between profiles and permission sets

**What the LLM generates:** "Assign the app to users via a permission set so they can see it in the App Launcher."

**Why it happens:** LLMs know permission sets grant access broadly, but Lightning app visibility in the App Manager wizard is controlled by selecting specific profiles. The LLM conflates permission-set-based access with the App Manager profile assignment step.

**Correct pattern:**

```
In App Manager → Edit App → App Settings → Assign to Profiles:
- Move target profiles from Available to Selected.
- Users with those profiles see the app in the App Launcher.

Note: App visibility can also be controlled through "Visible" checkboxes
on a profile's App Settings or via permission sets that include app
assignments, but the App Manager wizard itself assigns by profile.
```

**Detection hint:** Check whether the output conflates App Manager profile assignment with permission set assignment. Look for `permission set` in the same paragraph as `App Manager → Assign`.

---

## Anti-Pattern 3: Recommending Classic app creation instead of Lightning app

**What the LLM generates:** "Go to Setup → Create → Apps → New and create a new app with a logo and tabs."

**Why it happens:** Older training data references the Classic App setup flow. In Lightning Experience, apps are created via Setup → App Manager → New Lightning App, which uses a different wizard with navigation items, utility bar configuration, and profile assignment steps.

**Correct pattern:**

```
Setup → App Manager → New Lightning App
Wizard steps:
1. App Details (name, developer name, description)
2. App Options (standard vs console navigation)
3. Utility Items (optional utility bar components)
4. Navigation Items (tabs and pages)
5. User Profiles (which profiles see this app)
```

**Detection hint:** If the output references `Setup → Create → Apps` or describes adding "tabs to an app" via a Classic-style interface without mentioning "App Manager," it is describing the Classic flow.

---

## Anti-Pattern 4: Omitting utility bar component configuration details

**What the LLM generates:** "Add a utility bar to your app and include Open CTI, History, and Notes."

**Why it happens:** The LLM treats utility bar items as a simple checklist. In practice, each utility item has configuration properties (panel height, panel width, auto-open behavior, and component-specific settings like CTI adapter URL). Omitting these leads to utility items that appear but do not function.

**Correct pattern:**

```
In App Manager → Edit App → Utility Items:
1. Click "Add Utility Item."
2. Select the component (e.g., Open CTI Softphone).
3. Configure component properties:
   - Panel Height: 340px (default)
   - Panel Width: 340px (default)
   - Start automatically: checked/unchecked based on requirement
   - For Open CTI: the CTI adapter and Softphone Layout must be
     configured separately under Setup → Softphone Layouts.
4. Repeat for each utility item.
```

**Detection hint:** If utility bar advice lists component names without mentioning panel sizing, auto-start, or component-specific properties, the guidance is incomplete. Search for `Panel Height` or `component properties`.

---

## Anti-Pattern 5: Ignoring console app vs standard app distinction

**What the LLM generates:** "Create a Lightning app and add Cases, Accounts, and Contacts to the navigation bar for your service team."

**Why it happens:** LLMs default to standard navigation apps. For service teams that need split-view, workspace tabs, and subtabs, a console app is required. The LLM does not ask which app type is appropriate before advising.

**Correct pattern:**

```
For service or support teams, choose Console Navigation during app creation:
  App Manager → New Lightning App → App Options → Console Navigation

Console apps provide:
- Workspace tabs (multiple records open simultaneously)
- Subtabs (related records open under the primary tab)
- Split view (list + record detail side by side)

Standard Navigation apps provide:
- Traditional horizontal nav bar
- One record page at a time
- Better for users who work sequentially
```

**Detection hint:** If the output recommends a Lightning app for a service/support use case without discussing `Console Navigation` vs `Standard Navigation`, the app type decision is missing.

---

## Anti-Pattern 6: Forgetting that Lightning apps only work in Lightning Experience

**What the LLM generates:** "Create a Lightning app so all your users can access it from the App Launcher or the Classic app menu."

**Why it happens:** LLMs do not always distinguish between Lightning Experience and Salesforce Classic. Lightning apps only appear in the App Launcher in Lightning Experience. Classic users see Classic apps. If the org has users still on Classic, a separate Classic app may be needed.

**Correct pattern:**

```
Lightning apps are visible ONLY in Lightning Experience.
Classic users see Classic apps via the app menu (top right).

If the org has both Lightning and Classic users:
- Create a Lightning app for Lightning Experience users.
- Create a Classic app (Setup → Apps → New) for Classic users.
- Or migrate all users to Lightning Experience first.
```

**Detection hint:** If the output mentions "App Launcher" and "Classic" in the same sentence as if they are interchangeable, the Lightning-only constraint is being ignored.
