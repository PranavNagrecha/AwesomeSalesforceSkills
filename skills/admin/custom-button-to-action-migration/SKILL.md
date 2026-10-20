---
name: custom-button-to-action-migration
description: "Migrating Classic Custom Buttons (Detail Page Buttons, List Buttons, Mass Action Buttons) and JavaScript Buttons to Lightning Quick Actions, Screen Flow Actions, LWC Quick Actions, and headless Quick Actions. Covers JavaScript-button-to-action translation patterns (sforce.apex.execute → Apex action, navigation alerts → toast events, MassAction.update → record-collection processing), URL button translation, and the WebLink inventory (displayType, linkType) that sizes the migration. NOT for new Quick Action design (use admin/global-actions-and-quick-actions) or Lightning record page composition (use admin/lightning-app-builder-advanced)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
  - Security
triggers:
  - "How do I migrate Classic JavaScript buttons to Lightning?"
  - "JavaScript buttons are not supported in Lightning — what are my options?"
  - "Convert Detail Page Button to Lightning Quick Action"
  - "Mass Action Button replacement in Lightning"
  - "URL button (open external system) translation to Lightning"
  - "List View custom buttons in Lightning"
tags:
  - custom-buttons
  - javascript-buttons
  - quick-actions
  - lwc-quick-actions
  - screen-flow-actions
  - mass-action
  - migration
inputs:
  - "Inventory of Classic Custom Buttons by type (Detail Page, List, Mass Action) and content type (URL, OnClick JavaScript, Visualforce Page)"
  - "Per-button JavaScript content (for JS buttons) including AJAX calls, navigation, alerts, and Apex execution"
  - "Button placement (which page layouts, which list views)"
  - "User profiles allowed to invoke each button"
  - "Whether the button must work in Salesforce Mobile App (some patterns are mobile-only)"
outputs:
  - "Lightning Quick Actions (object-specific) replacing Detail Page Buttons"
  - "Screen Flow Actions replacing JavaScript buttons that need user input or branching"
  - "LWC Quick Actions (headless or screen) replacing JS buttons that perform Apex calls"
  - "List-view actions backed by Apex/Flow replacing List and Mass buttons (the list-view surface is UNVERIFIED 2026-10-20, Help-only)"
  - "Audit log mapping each Classic button to its Lightning replacement (or 'retained for Classic only' status)"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Custom Button to Action Migration

This skill activates when a practitioner needs to migrate Classic Custom Buttons (especially JavaScript buttons; UNVERIFIED (2026-10-20): that Lightning Experience does not support them is Help-only, see Core Concept 2) to Lightning Quick Actions, Screen Flow Actions, LWC Quick Actions, or other Lightning-native action surfaces.

---

## Before Starting

Gather this context before working on anything in this domain:

- Inventory all custom buttons across all objects by querying the `WebLink` sObject, which supports `query()` (object_reference 264 L314753-314755): `SELECT Id, Name, DisplayType, LinkType, OpenType, PageOrSobjectType, RequireRowSelection FROM WebLink`. `DisplayType` is `link`, `button` or `massActionButton` (api_meta 264 L47857-47860); `LinkType` is `url`, `sControl`, `javascript` or `page` (api_meta 264 L47926-47932); `PageOrSobjectType` is the page (standard objects) or object (custom objects) the button shows on (object_reference 264 L314937-314938). `RequireRowSelection` says whether the custom link requires a row selection (object_reference 264 L314948-314954), which marks the list buttons that act on selected records.
- For each JavaScript button (`LinkType = javascript`), capture the full body, which is stored in the `Url` field (api_meta 264 L47984-47986). The migration is heavily dependent on what the JS does — read each button before designing replacements.
- Confirm whether each button is currently invoked: usage data via `WebLink` is limited; consider deploying lightweight tracking (custom field on the user profile or feature consumption events) BEFORE deprecating to confirm low-usage buttons can be retired without replacement.
- Confirm Lightning UI is the primary user surface. If the org has both Classic and Lightning users, retain the Classic button and ADD a Lightning replacement (don't remove the Classic button if Classic users still need it). UNVERIFIED (2026-10-20): that JavaScript buttons keep working in Classic and do not run in Lightning Experience is a Help-only statement; no Metadata API, Object Reference or LWC guide line says where a `javascript` WebLink renders.
- For URL buttons, confirm whether the linked URL is a relative Salesforce path or an absolute external URL. UNVERIFIED (2026-10-20): that relative paths break and absolute URLs work as-is in Lightning is Help-only.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which `LinkType` and `DisplayType` does each button have, and where is each placed? | Only `javascript` buttons need a rebuild; `url` and `page` buttons map to navigation or Visualforce quick actions (Gotcha 1) | A button inventory grouped by type, so each row lands in one pattern |
| What does each JavaScript body do: Apex call, prompt, navigation, DOM edit? | The replacement surface depends on intent, not syntax (Patterns 1-3) | One-line intent per button, so nobody translates line by line |
| Are there still Classic users? | Removing a Classic button breaks them at once (Pattern 5) | A coexistence list and a retirement date |
| Must the action run in the Salesforce mobile app? | LWC quick actions are not supported there (Core Concept 3) | A non-LWC quick action type for mobile, or an agreed gap |
| Does any button act on a selection, and how large is it? | List-view surfaces and caps are unverified (Core Concepts 1, 4; Gotcha 2) | A tested selection size and a chunking decision |
| Does the button navigate, and from which app (Console or standard)? | Navigation differs by context (Gotchas 4 and 7) | Test cases per app, with navigation in LWC rather than Apex |
| Which Apex does each action call, and under what API version and sharing? | `WITH SECURITY_ENFORCED` cannot be used at API 67.0 and later (apexdev 264 L11926) | A class list with `apiVersion`, `with sharing` and `WITH USER_MODE` |

A proper migration replaces each button by intent, keeps Classic users working during the move, and checks every Lightning behaviour on a record; "just doing it" translates the JavaScript line by line and discovers the gaps in production.

---

## Core Concepts

### 1. Classic Button Type → Lightning Replacement

| Classic Button Type | Content | Lightning Replacement | Migration Difficulty |
|---|---|---|---|
| Detail Page Button — URL (relative path) | `/apex/MyVfPage?id={!Account.Id}` | Quick Action of type `VisualforcePage` OR headless LWC Quick Action that navigates | Low |
| Detail Page Button — URL (absolute external) | `https://external.com/lookup?id={!Account.Id}` | Headless LWC Quick Action that navigates with `standard__webPage` (Pattern 4); `QuickActionType` has no URL value | Low |
| Detail Page Button — JavaScript (simple Apex call) | `sforce.apex.execute('MyController','myMethod', {id: '{!Id}'})` | LWC Quick Action calling imperative Apex | Medium |
| Detail Page Button — JavaScript (complex DOM manipulation) | `var elem = document.getElementById(...); elem.style...` | Re-architect as Screen Flow with Display fields OR LWC Quick Action | High |
| Detail Page Button — Visualforce Page | Custom VF page (`LinkType = page`) | Quick Action of type `VisualforcePage`, `LightningWebComponent` or `LightningComponent`, OR retained as VF | Medium |
| List Button — URL (relative) | URL navigates to a list-context page | List-view action (surface UNVERIFIED, below the table) | Medium |
| List Button — JavaScript (operates on selected records) | Reads `getRecordIds()` and processes | List-view action invoking Apex/Flow with selected record IDs (surface UNVERIFIED, below the table) | High |
| Mass Action Button | `DisplayType = massActionButton`; operates on multiple records | List-view action invoking Flow/Apex (surface UNVERIFIED, below the table) | High |
| S-Control buttons | `LinkType = sControl` | Deprecated since Spring '09 (api_meta 264 L45109-45110; the `Scontrol` type is marked Deprecated, L109760-109761); the type still exists, so rebuild from scratch on a supported surface | High |

Mass quick actions are documented: `SearchLayouts.massQuickActions` is "the list of actions that you can use to perform mass quick action on records", each an existing create or update action, on custom objects and on standard objects that support quick actions and have a search layout in Lightning Experience (api_meta 264 L47565-47572). The buttons shown on an object's list views are `SearchLayouts.listViewButtons` (L47523-47526). A mass quick action is therefore a Create or Update action, not Apex or a Flow, and an LWC quick action cannot be the surface because it runs on record pages only (LWC guide `use-config-for-quick-actions`). UNVERIFIED (2026-10-20): the name "List View Action", which Lightning surface hands a selection to Apex or a Flow, and the claims that relative `/apex/...` paths are rewritten, or break, in Lightning are Help-only.

### 2. JavaScript Buttons Need a Rebuild: Translation Map

The button definition still exists in metadata: `linkType = javascript` is a valid WebLink value and the script sits in `url` (api_meta 264 L47926-47932, L47984-47986). UNVERIFIED (2026-10-20): that Lightning Experience does not support JavaScript buttons, and whether they render, vanish or show an "unsupported" message, is Help-only. Treat each as a rebuild.

| Classic JS Pattern | Lightning Replacement |
|---|---|
| `alert('Saved')` | `ShowToastEvent` from `lightning/platformShowToastEvent` (LWC guide `use-quick-actions-headless`) |
| `confirm('Delete?')` then conditional logic | `LightningConfirm` from `lightning/confirm`; `window.confirm()` is not supported for cross-origin iframes in Chrome and Safari (LWC guide `use-dialog-confirm`) |
| `window.location.href = '/...'` | `NavigationMixin.Navigate({type: 'standard__webPage', attributes: {url: '...'}})` |
| `sforce.apex.execute('Class', 'method', params)` | Imperative Apex import + `await method({...})` |
| `sforce.connection.update(records)` | `import { updateRecord } from 'lightning/uiRecordApi'` OR `@AuraEnabled` Apex with explicit DML |
| `getRecordIds()` (list buttons) | Selected-record IDs passed to Apex/Flow by the list-view surface (surface UNVERIFIED, see Core Concept 1) |
| `document.getElementById(...)` DOM manipulation | LWC `this.template.querySelector(...)` (within own component only) |

### 3. Three Lightning Action Surfaces

| Action Type | When to use | Files / Components |
|---|---|---|
| Quick Action — Create / Update / Log a Call | Standard CRUD or activity logging | Setup configuration only; no code |
| Screen Flow Action | Multi-step user input, branching logic, no code | Flow Builder; Quick Action `type = Flow`, which api_meta 264 L102962 labels Beta as of API 41.0 |
| LWC Quick Action (screen) | Custom UI for input + Apex processing | LWC bundle with `lightning__RecordAction` target and `actionType` `ScreenAction` (the default) |
| LWC Quick Action (headless) | One-click action with no UI (just Apex + toast) | LWC with `actionType` set to `Action` and a public `invoke()` method |
| Aura Quick Action | Legacy; only when LWC is insufficient (rare) | Aura component bundle; Quick Action `type = LightningComponent` (API 38.0+, api_meta 264 L102963-102964) |

LWC Quick Actions are the modern preferred replacement for most non-trivial JavaScript buttons. Headless LWC Quick Actions specifically replace the "click button → confirmation alert → save" pattern. Limits to design around: an LWC quick action works on record pages only (it cannot be a global action), `actionType` cannot be changed after it is defined, and it is not supported in the Salesforce mobile app (LWC guide `use-config-for-quick-actions`).

### 4. List View / Mass Action Replacement

| Classic Pattern | Lightning Replacement |
|---|---|
| List Button with JS that loops over `getRecordIds()` | List-view action that passes the selected IDs to Apex (surface UNVERIFIED) |
| Mass Action Button (e.g., "Mass Update Status") | A mass quick action: an Update quick action listed in `SearchLayouts.massQuickActions` (api_meta 264 L47565-47572); logic beyond a create or update needs the Apex/Flow surface (UNVERIFIED) |
| Custom Mass Action with complex UI | Visualforce page or Flow behind the list-view action (an LWC quick action is record-page only) |
| List Button that just navigates to a URL | List-view action that navigates (surface UNVERIFIED) |

UNVERIFIED (2026-10-20): the rows that hand a selection to Apex or a Flow, any `recordIds`/`selectedIds` input, and URL list actions are Help-only. The corpus documents mass quick actions only as create or update actions (api_meta 264 L47565-47572) and list-view buttons as `SearchLayouts.listViewButtons` (L47523-47526). The LWC guide page `use-quick-actions-mass` that an earlier source list cited does not exist (404).

### 5. URL Button Translation Pitfalls

How a URL button behaves after the move to Lightning:

| Classic URL Pattern | Lightning Behavior |
|---|---|
| `/apex/MyVfPage?id={!Account.Id}` | Lightning rewrites to `/lightning/cmp/...` — sometimes works, often doesn't |
| `/{!Account.Id}` (record navigation) | Use `NavigationMixin` instead |
| `/{!Account.Id}/d` (record detail in Classic) | Lightning has no "detail mode" URL convention |
| Absolute external URL | Works as-is in both surfaces |
| URL with `target="_self"` vs `_blank` | Window-target hints not always honored in Lightning |

For relative paths, replace with a Quick Action that uses the Lightning navigation framework, not a URL.

UNVERIFIED (2026-10-20): every Lightning-behaviour cell in the table above (rewrite to `/lightning/cmp/...`, no detail-mode URL, window-target hints, absolute URLs working as-is) is Help-only.

---

## Common Patterns

### Pattern 1: JavaScript Button That Calls Apex → Headless LWC Quick Action

**When to use:** A Classic JS button that calls an Apex method, shows a confirmation/result, and refreshes the page. This is the most common JS button pattern.

**How it works:**
1. Identify the Apex class and method the JS button calls.
2. Convert the Apex method to `@AuraEnabled` (typically NOT cacheable since it performs side effects).
3. Build an LWC Quick Action with `actionType=Action` (headless mode) and target `lightning__RecordAction`.
4. The LWC's `invoke()` method calls the Apex imperatively, fires a toast for success/error, and dispatches `RefreshEvent` from `lightning/refresh` to refresh the page (LWC guide `data-refreshview-api`).
5. Configure the Quick Action in Setup → Object Manager → Buttons, Links, and Actions.
6. Add the Quick Action to the page layout's Salesforce Mobile and Lightning Experience Actions section (LWC guide `use-config-for-quick-actions`).

**Why not the alternative:** Screen Flow is also a valid replacement but adds a UI step (typically a confirmation screen) that users may not want for a simple "do it now" action.

### Pattern 2: JavaScript Button with User Input → Screen Flow

**When to use:** A Classic JS button that prompts for input (a `prompt()` or a custom HTML form) and processes the result.

**How it works:**
1. Build a Screen Flow with the input fields the button collected.
2. Add an Action (Apex Invocable, Update Records, etc.) for the processing logic.
3. Configure as a Screen Flow Quick Action on the object.
4. Optional: add a confirmation screen for user feedback.

**Why not the alternative:** Building a custom LWC for a simple input form is overkill when Screen Flow handles it declaratively.

### Pattern 3: JavaScript List Button → List-View Action Backed by Apex

**When to use:** A Classic JS list button that processes selected records via `getRecordIds()`.

**How it works:**
1. Move the processing into one `@AuraEnabled` or invocable Apex method that takes the collection of IDs and returns per-record results (Example 4).
2. Handle partial successes — some records may fail processing (`Database.update(records, false)`).
3. Attach it to the list-view surface your org exposes for selected-record actions. UNVERIFIED (2026-10-20): which surface this is (a Screen Flow, a Visualforce page, a "mass quick action") is Help-only; do not build it as an LWC quick action, which runs on record pages only (LWC guide `use-config-for-quick-actions`).

**Why not the alternative:** A per-record LWC progress UI is not available from a record-page-only quick action.

### Pattern 4: URL Button to External System → Headless Navigation Action

**When to use:** A Classic button that opens an external system URL with merge field substitution (e.g., a LinkedIn lookup, a CTI dial-out, a partner portal SSO).

**How it works:**
1. Build a headless LWC Quick Action (Pattern 1 setup) whose `invoke()` navigates with `NavigationMixin.Navigate({type: 'standard__webPage', attributes: {url}})` (LWC guide `reference-page-reference-type`). `QuickActionType` has no URL value (api_meta 264 L102947-102971), so there is no declarative "URL" quick action to create.
2. Build the URL in JavaScript from `recordId` and the fields you read (`encodeURIComponent` for each value): `https://external.com/lookup?id=${recordId}&name=${encodeURIComponent(name)}`.
3. Add the Quick Action to the page layout.

**Why not the alternative:** A Visualforce-page quick action that redirects works, but adds a page to maintain for what is one navigation call.

### Pattern 5: Coexistence — Retain Classic Button, Add Lightning Action

**When to use:** The org has both Classic and Lightning users. Removing the Classic button breaks Classic users; not adding the Lightning equivalent breaks Lightning users.

**How it works:**
1. Keep the Classic Custom Button as-is (UNVERIFIED (2026-10-20): Help-only that it keeps working in Classic).
2. Build the Lightning Quick Action / LWC Quick Action / Screen Flow Action equivalent.
3. Both surface independently per UI mode.
4. Eventually, when all users are on Lightning, retire the Classic button.

**Why not the alternative:** Removing the Classic button before all users have moved to Lightning breaks production for Classic users immediately. Coexistence is the safe path during the transition window.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Classic JS button, calls Apex, shows alert | Pattern 1: Headless LWC Quick Action | Closest UX parity for one-click actions |
| Classic JS button, prompts for input | Pattern 2: Screen Flow | Declarative input collection; no LWC needed |
| Classic JS list button, processes selected records | Pattern 3: list-view action backed by Apex (surface UNVERIFIED) | One Apex entry point handles the collection with partial-success results |
| Classic URL button, external system | Pattern 4: headless LWC Quick Action that navigates | `QuickActionType` has no URL value, so navigation is a few lines of LWC |
| Classic URL button, relative Salesforce path | Quick Action with NavigationMixin | Explicit navigation does not depend on how Lightning treats relative paths (UNVERIFIED (2026-10-20): Help-only) |
| Visualforce page override button | Quick Action with VF override OR retain as VF | Some VF overrides have no Lightning equivalent |
| S-Control buttons | Rebuild from scratch | S-controls are deprecated (api_meta 264 L45109-45110) |
| Classic and Lightning both in use | Pattern 5: Coexistence | Don't break Classic users prematurely |
| JS button does complex DOM manipulation | LWC Quick Action with internal DOM logic | DOM access scoped to the LWC's own template |
| Mass action operates on a large selection | Invocable Apex behind the list-view action, with batch consideration | Large collections may need async processing (UNVERIFIED (2026-10-20): the selection cap is Help-only) |
| Button only used in Salesforce Mobile | LWC quick actions are not an option; use a non-LWC quick action type | LWC quick actions are not supported in the Salesforce mobile app (LWC guide `use-config-for-quick-actions`) |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Inventory custom buttons.** Run the `WebLink` query from Before Starting. Group by `DisplayType` and `LinkType`. Read each JS button's body (the `Url` field) and capture what it does (Apex call, navigation, alert, DOM manipulation).
2. **Categorize each button by pattern.** Apply the Decision Guidance table. Most JS buttons fall into Pattern 1 (Apex call) or Pattern 2 (input prompt). URL buttons usually map cleanly to Pattern 4.
3. **Audit usage.** Confirm which buttons are actively used. Buttons that haven't been invoked in 6+ months should be retired without replacement (validated with the user-team).
4. **Build the Lightning replacements.** Implement per-pattern. Test each against the same scenarios the original button served.
5. **Configure on page layouts and list views.** Each Lightning Action must be added to relevant page layouts (Salesforce Mobile and Lightning Experience Actions section) or list view button bars.
6. **Test in sandbox with users from each affected profile.** Specifically: do users find the new action where they expect it? Does the action's UX match the original's intent?
7. **Phased production rollout with audit log.** Coexistence first (keep Classic, add Lightning); monitor adoption via the `Last_Action_Source__c` field. Maintain a `Custom_Button_Migration_Log__c` mapping (Classic name → Lightning replacement → status). Retire Classic buttons when adoption hits the agreed threshold (typically ≥95% Lightning over 30 days).

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every Classic Custom Button has a documented decision: replaced (with what), retained for Classic only, or retired
- [ ] JavaScript buttons that called Apex have been replaced with Headless or Screen LWC Quick Actions (or Screen Flow)
- [ ] URL buttons with absolute external URLs are mapped to headless LWC Quick Actions that navigate with `standard__webPage`
- [ ] URL buttons with relative Salesforce paths are mapped to NavigationMixin-based Quick Actions
- [ ] List buttons that processed selected records have been replaced with a list-view action backed by Apex/Flow (surface UNVERIFIED, Core Concept 1)
- [ ] All Lightning replacements are added to relevant page layouts (Salesforce Mobile and Lightning Experience Actions section) and list views
- [ ] User-acceptance testing: representative users from each affected profile confirm the action is discoverable and works as expected
- [ ] Mobile: no LWC quick action is expected to run in the Salesforce mobile app; any other action type that must has been verified on a real mobile device
- [ ] Coexistence period: original Classic button remains in place during the transition for Classic users
- [ ] Audit log of original button → Lightning replacement is committed to source control
- [ ] Apex methods called from Lightning replacements are `@AuraEnabled` with appropriate `with sharing` and FLS enforcement

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **JavaScript buttons need a rebuild for Lightning Experience.** A user navigating Lightning may see no button where Classic showed one, with no error message and no "this button isn't supported" indicator, and assume the action is missing entirely. Audit page layouts for JS buttons and either replace them or flag to users that they're Classic-only. UNVERIFIED (2026-10-20): silent non-rendering in Lightning is Help-only.

2. **Mass Action selections may be capped.** A list view Mass Action that operates on selected records may be limited to a default of 200: selecting 500 records and invoking a Mass Action would process only the first 200, and the other 300 silently don't get the action applied. For Mass Actions on larger collections, design a Flow with batch processing or an async Apex job. UNVERIFIED (2026-10-20): the 200-record cap and "first 200 only" behaviour are Help-only.

3. **`{!Account.Id}` URL merge fields don't carry over from Classic buttons.** `QuickActionType` has no URL value (api_meta 264 L102947-102971), so there is no quick action to hold a Classic merge-field URL; build the URL in LWC from `recordId` and the fields you read. Test each value after migration. UNVERIFIED (2026-10-20): Help-only that Quick Action URL merge syntax differs from Classic.

4. **Quick Actions invoked from a Console subtab don't navigate the same way as standard Lightning.** In Service Cloud Console, a Quick Action that uses `NavigationMixin.Navigate({type: 'standard__recordPage'})` opens the navigation in the console workspace — sometimes as a new tab, sometimes replacing the current tab, depending on the action's launch context. If the original button assumed a specific navigation behavior, test in Console mode explicitly. UNVERIFIED (2026-10-20): Console tab behaviour is Help-only.

5. **List View Actions don't appear if the list view filter doesn't match any records.** A list-view action requires at least one selectable record. Empty list views hide the action entirely. Users assume the action is missing for that list view, when actually no records match the filter. UNVERIFIED (2026-10-20): Help-only.

6. **`window.opener` and cross-window communication patterns from Classic JS don't translate.** Some Classic JS buttons opened a popup window, then communicated back to the parent via `window.opener.location.reload()`. LWC and Lightning Quick Actions have no equivalent — windows are sandboxed differently. Re-architect these flows as Quick Actions that complete in the same context (no popups). UNVERIFIED (2026-10-20): that Lightning has no `window.opener` equivalent is Help-only.

7. **`PageReference` redirects from Classic Apex callbacks don't work in Lightning Quick Actions.** A Classic JS button that called `sforce.apex.execute` and the Apex method returned a `PageReference` — Classic followed the redirect. In Lightning, the redirect is ignored. Re-architect: Apex returns data; LWC explicitly navigates via NavigationMixin after the call resolves. UNVERIFIED (2026-10-20): that Lightning ignores a `PageReference` result is Help-only.

8. **Hard-coded record IDs in JS buttons don't translate to merge fields cleanly.** Some JS buttons hardcoded record IDs (anti-pattern) for "demo" records or admin actions. The migration is the moment to remove the hardcoded IDs (use Custom Settings, Custom Metadata, or proper record-context resolution). Quick Actions and Flows have no equivalent for "always operate on record X regardless of context." UNVERIFIED (2026-10-20): Help-only.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Lightning Quick Actions | Object-specific actions replacing Detail Page Buttons |
| LWC Quick Actions (Headless / Screen) | Replacements for JS buttons that need Apex execution and/or custom UI |
| Screen Flow Actions | Replacements for JS buttons that need user input or branching |
| List-view actions | Replacements for List Buttons that operate on selected records (surface UNVERIFIED) |
| Headless navigation Quick Actions | Replacements for URL buttons with absolute external URLs |
| Updated page layouts | Salesforce Mobile and Lightning Experience Actions section configured to expose new Quick Actions |
| Migration audit log | Old button → new action mapping with status (Active, Retained, Retired) |
| Coexistence retention list | Classic buttons kept for Classic users with a planned retirement date |

---

## Related Skills

- `admin/global-actions-and-quick-actions` — Use for new Quick Action / Global Action design (post-migration)
- `lwc/lwc-quick-actions` — Use for designing LWC Quick Actions in detail (Headless vs Screen)
- `flow/screen-flows` — Use for designing Screen Flow Actions
- `lwc/visualforce-to-lwc-migration` — Use when buttons reference Visualforce pages being migrated
- `apex/apex-security-patterns` — Use when Apex methods called from new Quick Actions need their sharing keyword and CRUD/FLS enforcement designed correctly
- `admin/lightning-app-builder-advanced` — Use for placing Quick Actions on Lightning Record Pages
