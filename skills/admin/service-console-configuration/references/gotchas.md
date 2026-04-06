# Gotchas — Service Console Configuration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Navigation Type Is Permanently Set at App Creation

**What happens:** Once a Lightning app is saved with Standard Navigation, there is no setting or button in Setup to switch it to Console Navigation. The `navType` field in the `CustomApplication` metadata component cannot be updated on an existing app via Setup UI — only via metadata deployment, and even then Salesforce does not guarantee a clean upgrade path.

**When it occurs:** Admins realize they need split view after the standard app has already been configured with navigation items, utility bar items, custom branding, and profile assignments. Attempting to "update" the navigation type via metadata deploy may succeed in some orgs but is unsupported and can produce inconsistent results.

**How to avoid:** Decide the navigation type before creating the app. If there is any chance the team will need console capabilities, create a console navigation app from the start. To migrate an existing team, create a new console app and manually recreate all navigation items and utility bar settings. Capture the existing configuration first with a metadata retrieve.

---

## Gotcha 2: Omni-Channel Utility Shows a Blank or Error State Without Prior Setup

**What happens:** Admins add the Omni-Channel utility to the console app's utility bar and deploy. Agents open the console and see a blank Omni-Channel panel or an error message. No work items appear and agents cannot set their status.

**When it occurs:** The Omni-Channel utility is added before Omni-Channel itself is enabled in the org, or before any Service Channels or Presence Configurations have been created.

**How to avoid:** Before adding the Omni-Channel utility:
1. Enable Omni-Channel in Setup > Omni-Channel Settings.
2. Create at least one Service Channel (e.g., Cases).
3. Create a Presence Configuration and assign it to the agent profile.
4. Verify the agent user is assigned a routing configuration.
Only then add the utility to the console app.

---

## Gotcha 3: Macros Silently Do Nothing Without the Macros User Permission

**What happens:** An admin creates a Macro and adds the Macros utility to the console app. Agents open the utility panel, select the macro, and click Run. Nothing happens — no field changes, no email sent, no error message displayed.

**When it occurs:** The agent's profile or permission set does not have the "Macros" user permission enabled. The Macros utility panel renders and the macro list is visible, but execution is blocked silently.

**How to avoid:** Enable the "Macros" permission on the agent's profile or in a permission set assigned to agents. The "Manage Macros" permission is a separate permission required to create and edit macros (typically admin-only). Test macros in a sandbox logged in as an agent user before deploying to production.

---

## Gotcha 4: Quick Text Entries Not Visible in the Right Channels

**What happens:** Quick Text entries are created and visible in the Macros/Quick Text utility, but agents cannot find them when composing an email or chat reply inline. The entries appear in the utility panel but do not surface in the inline type-ahead shortcut (`:` prefix trigger) inside the email or chat window.

**When it occurs:** Quick Text entries are created with incorrect channel assignments. Each QuickText record has a `Channel` picklist (Email, Chat, Phone, Portal, Internal) — entries only surface in the matching channel context. An entry created for "Internal" will not appear when the agent is composing a customer-facing email.

**How to avoid:** When creating Quick Text entries, explicitly set the Channel to match the contexts where agents will use them. For entries usable in multiple channels, create separate QuickText records per channel or verify whether the multi-channel field option is available in your org's release.

---

## Gotcha 5: Navigation Rules Apply to All Profiles in the App — No Per-Profile Override

**What happens:** Two agent teams share a console app. Team A wants Contacts to open as subtabs; Team B needs Contacts to open as workspace tabs (they frequently work Contact records independently). An admin cannot satisfy both teams with a single navigation rule.

**When it occurs:** Different agent workflows require different navigation patterns for the same object, but the app is shared across teams.

**How to avoid:** Create separate console apps for the two teams. Navigation rules are app-scoped, not profile-scoped or user-scoped. This is a platform design constraint — there is no workaround within a single app. If the teams are similar enough, it is often better to standardize the navigation rule and train agents on the resulting behavior rather than manage two separate apps.
