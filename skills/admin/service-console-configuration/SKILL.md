---
name: service-console-configuration
description: "Use this skill to configure a Lightning Service Console app in Salesforce — setting Console Navigation (split view), defining workspace tabs and subtabs, configuring the utility bar with Omni-Channel, Macros, and History, creating Quick Text entries, setting up keyboard shortcuts, and defining navigation rules per object. Trigger keywords: Service Console, console app, workspace tabs, subtabs, utility bar macros, Omni-Channel utility, split view, Quick Text, console navigation rules, keyboard shortcuts service console. NOT for generic Lightning app creation (use app-and-tab-configuration), NOT for Omni-Channel routing configuration (use omni-channel-routing), NOT for CTI adapter installation (use open-cti-setup), NOT for Einstein Bot or Messaging setup."
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
  - "Objects that should open as workspace tabs vs subtabs (navigation rules)"
  - "Keyboard shortcut customizations needed"
outputs:
  - "Configured Lightning console app with Console Navigation enabled and split view active"
  - "Navigation rules defining how each object opens (workspace tab or subtab)"
  - "Utility bar configured with correct components for agent workflow"
  - "Macro records covering repetitive agent actions"
  - "Quick Text entries for common agent responses"
  - "Keyboard shortcut configuration for the console app"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Service Console Configuration

Use this skill when an admin needs to configure a Lightning Service Console app for a support team — this includes enabling Console Navigation (split view), configuring workspace tabs and subtabs, setting up the utility bar, creating macros and Quick Text entries, defining navigation rules per object, and customizing keyboard shortcuts. This skill covers the full console setup from app creation to agent-ready configuration.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has **Service Cloud** licenses. Console navigation requires a Service Cloud or Sales Cloud console license for each agent user. Without the license, users see the app but it degrades to standard navigation.
- Know which objects agents interact with during a case. The most common workspace object is Case; related objects like Contact, Account, and Knowledge Articles are typically subtabs opened from within a case workspace.
- Determine whether Omni-Channel is already configured. The Omni-Channel utility requires Omni-Channel to be enabled in the org (Setup > Omni-Channel Settings) and at least one Service Channel before the widget is useful in the utility bar.
- Identify the current utility bar contents if the app already exists — editing a utility bar replaces the full item list, so capture the existing items before making changes.

---

## Core Concepts

### Console Navigation vs Standard Navigation

Lightning apps use one of two navigation types set at app creation time in App Manager:

- **Standard Navigation** — horizontal nav bar at the top; each object opens a full-page view replacing the current view; this is the default for most apps.
- **Console Navigation** — enables the Service Console workspace layout: a persistent split view with a sidebar (list panel) on the left and one or more workspace tabs in the main area. Agents can work multiple records simultaneously without losing context.

The navigation type is a fixed property of the app — you cannot switch an existing app from Standard to Console or vice versa without recreating it. The Metadata API field is `navType` set to `Console` on the `CustomApplication` component.

Console Navigation is the core differentiator of the Service Console. Everything else (utility bar, macros, keyboard shortcuts) works in any Lightning app, but split view and workspace tabs only function in console navigation apps.

### Workspace Tabs and Subtabs

In a console app, records open as **workspace tabs** — full horizontal tabs across the top of the main content area. Each workspace tab has its own **subtab bar** where related records opened from within that workspace appear as narrower tabs.

**Navigation rules** (configured in the console app settings) define how each object opens:

- **Workspace tab** — the record opens as a new primary tab. Agents can switch between multiple open cases without leaving any of them.
- **Subtab of current workspace** — the record opens under whichever workspace tab is currently active. Used for Contacts, Accounts, or Knowledge Articles opened from a Case record.
- **Subtab of the workspace with matching object** — opens a related record as a subtab of an existing workspace tab that shows the same object type.

Default navigation rule is workspace tab for every object. To configure: in App Manager, edit the app, navigate to the Console Navigation tab, and use the navigation rules section to set each object's behavior.

### Utility Bar

The utility bar is a persistent footer toolbar visible at the bottom of the screen throughout the console session. In a Service Console context, the following utility items are most common:

- **History** — list of recently visited records within the current session; console apps only, not available in standard-navigation apps.
- **Omni-Channel** — displays the agent's Omni-Channel status and incoming work requests; requires Omni-Channel to be enabled and the user to be a Service Cloud user with a routing configuration.
- **Macros** — provides a macros panel so agents can run macros without leaving the active workspace; macros automate multi-step repetitive actions (update fields, send emails, post to chatter) with a single click.
- **Open CTI Softphone** — requires a CTI adapter package to be installed; the utility item renders the adapter's phone panel.
- **Quick Text** — surfaces Quick Text snippets for insertion into emails, chats, or feed posts. Quick Text entries are text templates stored as `QuickText` records, organized by channels (Email, Chat, Phone, etc.) and accessible via the utility or inline in editors.

Utility items are configured per app. Each item can have default panel width, height, and whether it auto-opens when the app loads.

### Macros

Macros are records of type `Macro` that store a sequence of automated actions for agents. Each macro contains one or more instructions (called macro actions) that can:
- Update field values on the case or related records
- Send an email using an email template
- Post to Chatter
- Log a call
- Run a quick action

Macros are created in Setup > Macros or directly from the Macros utility panel. They can be run manually by agents or triggered by Bulk Macro runs. Macros target the currently active workspace record — agents must have the Macros permission enabled on their profile.

### Keyboard Shortcuts

Console apps support configurable keyboard shortcuts that let agents navigate tabs, open records, and trigger macros without a mouse. Keyboard shortcuts are configured at the console app level in App Manager > edit app > Keyboard Shortcuts. Salesforce provides a set of default shortcuts (e.g., navigate to next/previous tab, open a new workspace) that can be enabled, disabled, or reassigned. Custom shortcut bindings can reference specific macros to allow one-key macro execution.

---

## Common Patterns

### Pattern: Full Service Console App Setup for a Case-Centric Team

**When to use:** A support team works primarily on Cases, with Contacts and Accounts as reference records opened from within Cases. Agents handle multiple cases concurrently.

**How it works:**
1. Setup > App Manager > New Lightning App — choose Console Navigation; add branding.
2. Navigation Items — add Cases, Contacts, Accounts, Knowledge in that order. Cases becomes the default landing tab.
3. Utility Bar — add History, Omni-Channel, Macros, and Open CTI Softphone (if CTI is configured).
4. User Profiles — assign Service Cloud agent profiles.
5. Save the app. Open the app's console navigation settings and configure navigation rules:
   - Case → Workspace Tab
   - Contact → Subtab of current workspace
   - Account → Subtab of current workspace
   - Knowledge Article → Subtab of current workspace
6. Create Macro records for top-3 agent repetitive tasks (e.g., "Escalate to Tier 2" = set Status=Escalated + send email).
7. Create Quick Text entries for standard agent responses grouped by channel.

**Why not the alternative:** Using a standard navigation app forces agents to navigate away from the current case every time they open a contact or account, losing context and increasing handle time.

### Pattern: Navigation Rules for Complex Object Hierarchies

**When to use:** Agents work with Cases linked to Assets or Work Orders, and those child records need to open in context rather than as independent primary tabs.

**How it works:**
1. In the console app's navigation settings, set the parent object (e.g., Case) to Workspace Tab.
2. Set child objects (Asset, Work Order, Contact) to Subtab of current workspace.
3. If agents also need to open Assets independently (not from a Case), add a second navigation rule: when no workspace is open, open Asset as a Workspace Tab.

Navigation rules are evaluated in order — the first matching rule wins. Order them most-specific first.

**Why not the alternative:** Leaving all objects on the default Workspace Tab rule means every record click opens a new primary tab, quickly filling the tab bar and making it difficult to track the active case.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New app for case-handling agents | Create a new app with Console Navigation | Standard navigation loses agent context between records |
| Existing standard app used by service team | Create a new console app; do not convert | Navigation type cannot be changed post-creation |
| Agents need phone panel in the console | Add Open CTI Softphone utility; ensure CTI adapter is installed | Softphone utility renders the CTI adapter UI inside the console |
| Agents need one-click repetitive action | Create a Macro; add Macros utility to the app | Macros automate multi-step actions that would otherwise require navigating multiple pages |
| Agents need standard reply snippets | Create Quick Text entries by channel | Quick Text is searchable inline and does not require navigating away from the record |
| Team has high incoming case volume with routing | Add Omni-Channel utility and configure routing | Omni-Channel widget shows agent status and incoming work items |
| Need to enforce keyboard-only navigation | Configure keyboard shortcuts in console app settings | Reduces mouse dependency; improves handle time for keyboard-proficient agents |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Gather context** — confirm Service Cloud license availability, identify target objects and agent workflows, note whether Omni-Channel is already enabled and whether a CTI adapter is installed.
2. **Create the console app** — in App Manager, create a new Lightning app with Console Navigation; add navigation items in priority order (primary object first); assign to agent profiles.
3. **Configure navigation rules** — in the app's console settings, set each object to Workspace Tab or Subtab as appropriate for agent workflow; order rules most-specific first.
4. **Configure the utility bar** — add History, Omni-Channel, Macros, and any other required utilities; set panel dimensions and auto-open behavior.
5. **Create Macros and Quick Text** — document the top repetitive agent tasks and build macros for each; create Quick Text entries for standard responses by channel (Email, Chat, Phone).
6. **Configure keyboard shortcuts** — enable default shortcuts; add custom bindings for frequently used macros if requested.
7. **Validate** — log in as a target agent user, confirm split view is active, open a case, open a contact from the case and verify it appears as a subtab, run a macro, confirm keyboard shortcuts work.

---

## Review Checklist

Before marking service console configuration complete:

- [ ] App created with Console Navigation (not Standard Navigation)
- [ ] Navigation items include primary object (Case) first and all related objects
- [ ] App profile visibility assigned to correct agent profiles
- [ ] Navigation rules configured — primary objects as workspace tabs, related objects as subtabs
- [ ] Utility bar includes History, Omni-Channel (if routing is active), and Macros
- [ ] Macros created for top repetitive agent actions and verified to run without errors
- [ ] Quick Text entries created and grouped by correct channels
- [ ] Keyboard shortcuts reviewed and customized as needed
- [ ] Tested end-to-end as an agent user — split view active, subtabs open correctly, macros execute

---

## Salesforce-Specific Gotchas

1. **Navigation type is immutable after app creation** — You cannot change a Standard Navigation app to Console Navigation after it has been created. Admins who want to migrate a team from a standard app must create a new console app and re-add all navigation items, utility bar items, and profile assignments. Document this before starting — do not attempt in-place conversion.
2. **History utility is console-only** — The History utility item does not appear in the utility bar Setup picker when editing a Standard Navigation app. Admins sometimes add it to a standard app by editing the XML directly; it will silently fail to render for users. Always configure History utility items in Console Navigation apps only.
3. **Omni-Channel utility requires org-level Omni-Channel to be enabled first** — Adding the Omni-Channel utility to the console app does nothing if Omni-Channel has not been enabled in Setup > Omni-Channel Settings. Agents will see an empty or error state in the widget. Enable Omni-Channel and configure at least one Service Channel before configuring the utility.
4. **Macros require explicit user permission** — The "Macros" permission must be enabled on the agent's profile or permission set, and "Manage Macros" is a separate permission for admins who create and edit macros. Agents without the Macros permission cannot run macros even if the Macros utility is visible.
5. **Navigation rules are app-scoped, not profile-scoped** — There is no way to give different navigation rule behavior to different profiles within the same console app. If two teams need different navigation rules for the same objects, they need separate console apps.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Lightning Console App | App Manager record with Console Navigation, navigation items, utility bar, and profile assignments |
| Navigation Rules Configuration | Per-object settings defining workspace tab vs subtab behavior |
| Macro Records | Salesforce Macro records automating top repetitive agent actions |
| Quick Text Entries | QuickText records grouped by channel for standard agent responses |
| Keyboard Shortcut Config | Console-app-level keyboard shortcut bindings |

---

## Related Skills

- app-and-tab-configuration — use for general Lightning app and custom tab creation; this skill extends it specifically for console apps
- omni-channel-routing — covers Service Channel creation, routing configurations, and queue routing used by the Omni-Channel utility
- products-and-pricebooks — unrelated; do not conflate with console setup
