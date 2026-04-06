# LLM Anti-Patterns — Service Console Configuration

Common mistakes AI coding assistants make when generating or advising on Service Console Configuration. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending "Edit the Existing App to Enable Console Navigation"

**What the LLM generates:** "Go to Setup > App Manager, click Edit on your existing Lightning app, and change the Navigation Style to Console to enable split view."

**Why it happens:** LLMs infer that navigation type is a mutable setting like most other app properties. They also conflate App Manager's Edit screen (which does allow changing many properties) with the fixed `navType` field.

**Correct pattern:**

```
Console Navigation is set at app creation time and cannot be changed afterward.
To enable console navigation for an existing team:
1. Create a new Lightning app and select "Console Navigation" during the setup wizard.
2. Recreate the navigation items and utility bar from the old app.
3. Assign the same profiles.
4. Migrate agents to the new app.
```

**Detection hint:** Look for phrases like "edit the existing app and set navigation to console" or "change the navigation type." These are not valid Setup actions.

---

## Anti-Pattern 2: Adding the History Utility to a Standard Navigation App

**What the LLM generates:** "Add the History utility to your app's utility bar so agents can quickly see their recently visited records."

**Why it happens:** The History utility exists and is a common utility bar recommendation. LLMs do not differentiate between utility items that are console-only vs available in all app types.

**Correct pattern:**

```
The History utility is only available in Console Navigation apps.
- For standard-navigation apps, use the "Recent Items" utility instead (available in all app types).
- For console apps, use History — it tracks the session's visited records within the console workspace.
```

**Detection hint:** Look for History utility recommendations in contexts where the app type has not been confirmed as Console Navigation, or where the app was described as a standard app.

---

## Anti-Pattern 3: Conflating Quick Text and Macros

**What the LLM generates:** "Create a macro to insert a standard reply into the case email. Add the macro to the Macros utility so agents can select it when composing emails."

**Why it happens:** Both Macros and Quick Text serve agent productivity in the console, and both surface in the utility bar. LLMs confuse their roles — Macros automate multi-step record actions; Quick Text provides reusable text snippets.

**Correct pattern:**

```
Use Quick Text for reusable text snippets inserted into email, chat, or feed:
  - Create Quick Text entries (Setup > Quick Text or via the utility)
  - Set the Channel correctly (Email, Chat, Phone, etc.)
  - Agents trigger Quick Text inline with a shortcut character or via the utility panel

Use Macros for multi-step automated record actions:
  - Update fields, send emails using templates, post to Chatter, save
  - Macros are NOT text insertion tools; they are action automators
```

**Detection hint:** Look for instructions to "create a macro to insert text" or "use a macro as a template." Text insertion belongs to Quick Text, not Macros.

---

## Anti-Pattern 4: Assuming Omni-Channel Utility Works Without Prior Omni-Channel Setup

**What the LLM generates:** "Add the Omni-Channel utility to your Service Console utility bar. Agents will then see their queue and incoming cases in the widget."

**Why it happens:** LLMs describe the end-state of a working Omni-Channel setup without listing the prerequisite steps. Omni-Channel setup is a multi-step process that precedes the utility bar item.

**Correct pattern:**

```
Prerequisites before adding Omni-Channel utility:
1. Enable Omni-Channel: Setup > Omni-Channel Settings > Enable Omni-Channel
2. Create a Service Channel for Cases (and other routable objects)
3. Create a Routing Configuration
4. Create a Queue and assign the routing configuration
5. Create a Presence Configuration and assign to agent profiles
6. Verify agent user has a presence configuration

Only after these steps does the Omni-Channel utility widget function for agents.
```

**Detection hint:** Look for Omni-Channel utility recommendations without mention of enabling Omni-Channel, creating Service Channels, or configuring Presence Configurations.

---

## Anti-Pattern 5: Configuring Navigation Rules to Open All Objects as Workspace Tabs

**What the LLM generates:** "Set all your navigation rules to Workspace Tab so agents can always get back to any record they opened."

**Why it happens:** The default navigation rule for every object is Workspace Tab. LLMs default to recommending the default, and the reasoning ("get back to any record") sounds plausible without understanding how tab bar overload affects usability.

**Correct pattern:**

```
Workspace Tab is correct for the PRIMARY object agents work (e.g., Case).
Related objects (Contact, Account, Knowledge) should open as Subtabs of the current workspace:
  - Contact → Subtab of current workspace
  - Account → Subtab of current workspace
  - Knowledge Article → Subtab of current workspace

Opening everything as a workspace tab fills the tab bar rapidly,
makes it hard to identify the active case, and defeats the purpose of split view.
Only promote an object to Workspace Tab if agents independently initiate work on it
(e.g., a dispatcher who works Cases AND Work Orders as primary records).
```

**Detection hint:** Look for navigation rule configurations where Contact, Account, or Knowledge are set to Workspace Tab without a stated reason. These are almost always subtab candidates.

---

## Anti-Pattern 6: Creating Macros for Actions That Should Be Automated

**What the LLM generates:** "Create a macro called 'Close Case' that sets Status to Closed and Owner to the archive queue. Agents should run it at the end of every call."

**Why it happens:** Macros are visible and concrete to configure. LLMs reach for them as a general action-automation tool without considering whether the action should be agent-triggered or platform-triggered.

**Correct pattern:**

```
Macros are for agent-decided, contextual actions — not universal process enforcement.
If every agent runs the same macro at the end of every case, the action belongs in a Flow:
  - Use a Screen Flow on a Case quick action for guided closure
  - Use a Record-Triggered Flow to auto-update Owner when Status changes to Closed

Reserve Macros for:
  - Escalation workflows that agents choose based on judgment
  - Specific email responses that vary by situation
  - Non-obvious multi-step actions that would otherwise be error-prone
```

**Detection hint:** Look for macros described as "required for every case" or "run at the end of every call." These signal process automation that should be a Flow, not a Macro.
