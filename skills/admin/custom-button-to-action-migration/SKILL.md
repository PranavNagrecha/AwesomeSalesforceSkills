---
name: custom-button-to-action-migration
description: "Migrating Classic Custom Buttons (Detail Page Buttons, List Buttons, Mass Action Buttons) and JavaScript Buttons to Lightning Quick Actions, Screen Flow Actions, LWC Quick Actions, and headless Quick Actions. Covers JavaScript-button-to-action translation patterns (sforce.apex.execute → Apex action, navigation alerts → toast events, MassAction.update → record-collection processing), URL button translation, and the irreversible loss of Classic JavaScript button capability in Lightning. NOT for new Quick Action design (use admin/quick-actions-and-flow-actions) or Lightning record page composition (use admin/lightning-app-builder-advanced)."
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
  - "List View Buttons replaced by Mass Quick Actions or Custom List Buttons (URL only)"
  - "Mass Action replacement: list-view button + invocable Apex/Flow processing record collections"
  - "Audit log mapping each Classic button to its Lightning replacement (or 'retained for Classic only' status)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-30
---

# Custom Button to Action Migration

This skill activates when a practitioner needs to migrate Classic Custom Buttons (especially JavaScript buttons, which are not supported in Lightning Experience) to Lightning Quick Actions, Screen Flow Actions, LWC Quick Actions, or other Lightning-native action surfaces.

---

## Before Starting

Gather this context before working on anything in this domain:

- Inventory all custom buttons across all objects. Tooling API: `SELECT Id, Name, EntityDefinition.QualifiedApiName, BehaviorType, ContentSource FROM WebLink`. `BehaviorType` includes `Detail`, `List`, `Mass`; `ContentSource` includes `URL`, `OnClickJavaScript`, `VisualforcePage`, `S Control`.
- For each JavaScript button, capture the full OnClick JavaScript. The migration is heavily dependent on what the JS does — read each button before designing replacements.
- Confirm whether each button is currently invoked: usage data via `WebLink` is limited; consider deploying lightweight tracking (custom field on the user profile or feature consumption events) BEFORE deprecating to confirm low-usage buttons can be retired without replacement.
- Confirm Lightning UI is the primary user surface. JavaScript buttons continue to work in Salesforce Classic; if the org has both Classic and Lightning users, retain the Classic button and ADD a Lightning replacement (don't remove the Classic button if Classic users still need it).
- For URL buttons, confirm whether the linked URL is a relative Salesforce path (often broken in Lightning) or an absolute external URL (usually works as-is).

---

## Core Concepts

### 1. Classic Button Type → Lightning Replacement

| Classic Button Type | Content | Lightning Replacement | Migration Difficulty |
|---|---|---|---|
| Detail Page Button — URL (relative path) | `/apex/MyVfPage?id={!Account.Id}` | Quick Action with Visualforce override OR navigation Quick Action | Low |
| Detail Page Button — URL (absolute external) | `https://external.com/lookup?id={!Account.Id}` | Quick Action with URL action type, or LWC Quick Action with `window.open` | Low |
| Detail Page Button — JavaScript (simple Apex call) | `sforce.apex.execute('MyController','myMethod', {id: '{!Id}'})` | LWC Quick Action calling imperative Apex | Medium |
| Detail Page Button — JavaScript (complex DOM manipulation) | `var elem = document.getElementById(...); elem.style...` | Re-architect as Screen Flow with Display fields OR LWC Quick Action | High |
| Detail Page Button — Visualforce Page override | Custom VF page | Quick Action with Lightning component override OR retained as VF | Medium |
| List Button — URL (relative) | URL navigates to a list-context page | List View Action OR Mass Quick Action | Medium |
| List Button — JavaScript (operates on selected records) | Reads `getRecordIds()` and processes | Mass Quick Action invoking Apex/Flow with selected record IDs | High |
| Mass Action Button | Operates on multiple records from a list view | Mass Quick Action OR List View Action invoking Flow/Apex | High |
| S-Control buttons | Legacy S-Control | NOT supported anywhere in modern Lightning; rebuild from scratch | High |

### 2. JavaScript Buttons Have NO Direct Lightning Equivalent

Salesforce explicitly does not support JavaScript Buttons in Lightning Experience. The button definition still exists in metadata (and continues to work in Classic), but in Lightning UI it does not render or fires only an "unsupported" message.

| Classic JS Pattern | Lightning Replacement |
|---|---|
| `alert('Saved')` | `ShowToastEvent` from `lightning/platformShowToastEvent` |
| `confirm('Delete?')` then conditional logic | `LightningConfirm` from `lightning/confirm` |
| `window.location.href = '/...'` | `NavigationMixin.Navigate({type: 'standard__webPage', attributes: {url: '...'}})` |
| `sforce.apex.execute('Class', 'method', params)` | Imperative Apex import + `await method({...})` |
| `sforce.connection.update(records)` | `import { updateRecord } from 'lightning/uiRecordApi'` OR `@AuraEnabled` Apex with explicit DML |
| `getRecordIds()` (list buttons) | `@api recordIds` exposed by Mass Quick Action / List Action |
| `document.getElementById(...)` DOM manipulation | LWC `this.template.querySelector(...)` (within own component only) |

### 3. Three Lightning Action Surfaces

| Action Type | When to use | Files / Components |
|---|---|---|
| Quick Action — Create / Update / Log a Call | Standard CRUD or activity logging | Setup configuration only; no code |
| Screen Flow Action | Multi-step user input, branching logic, no code | Flow Builder; deploy as Flow |
| LWC Quick Action (screen) | Custom UI for input + Apex processing | LWC bundle with `lightningRecordPage` Quick Action target |
| LWC Quick Action (headless) | One-click action with no UI (just Apex + toast) | LWC with `actionType` set to `Action` and headless invocation |
| Aura Quick Action | Legacy; only when LWC is insufficient (rare) | Aura component bundle |

LWC Quick Actions are the modern preferred replacement for most non-trivial JavaScript buttons. Headless LWC Quick Actions specifically replace the "click button → confirmation alert → save" pattern.

### 4. List View / Mass Action Replacement

| Classic Pattern | Lightning Replacement |
|---|---|
| List Button with JS that loops over `getRecordIds()` | Mass Quick Action that exposes `@api recordIds` to an LWC, which iterates and calls Apex |
| Mass Action Button (e.g., "Mass Update Status") | List View Action invoking a Screen Flow that takes the record collection as input |
| Custom Mass Action with complex UI | LWC List Action with internal logic |
| List Button that just navigates to a URL | List View URL Action (Lightning supports URL list actions) |

### 5. URL Button Translation Pitfalls

URL buttons in Lightning handle absolute external URLs cleanly. Relative paths break:

| Classic URL Pattern | Lightning Behavior |
|---|---|
| `/apex/MyVfPage?id={!Account.Id}` | Lightning rewrites to `/lightning/cmp/...` — sometimes works, often doesn't |
| `/{!Account.Id}` (record navigation) | Use `NavigationMixin` instead |
| `/{!Account.Id}/d` (record detail in Classic) | Lightning has no "detail mode" URL convention |
| Absolute external URL | Works as-is in both surfaces |
| URL with `target="_self"` vs `_blank` | Window-target hints not always honored in Lightning |

For relative paths, replace with a Quick Action that uses the Lightning navigation framework, not a URL.

---

## Common Patterns

### Pattern 1: JavaScript Button That Calls Apex → Headless LWC Quick Action

**When to use:** A Classic JS button that calls an Apex method, shows a confirmation/result, and refreshes the page. This is the most common JS button pattern.

**How it works:**
1. Identify the Apex class and method the JS button calls.
2. Convert the Apex method to `@AuraEnabled` (typically NOT cacheable since it performs side effects).
3. Build an LWC Quick Action with `actionType=Action` (headless mode) and target `lightning__RecordAction`.
4. The LWC's `invoke()` method calls the Apex imperatively, fires a toast for success/error, and dispatches `RefreshRecordEvent` from `@salesforce/apex` to refresh the page.
5. Configure the Quick Action in Setup → Object Manager → Buttons, Links, and Actions.
6. Add the Quick Action to the page layout (Lightning Actions section).

**Why not the alternative:** Screen Flow is also a valid replacement but adds a UI step (typically a confirmation screen) that users may not want for a simple "do it now" action.

### Pattern 2: JavaScript Button with User Input → Screen Flow

**When to use:** A Classic JS button that prompts for input (a `prompt()` or a custom HTML form) and processes the result.

**How it works:**
1. Build a Screen Flow with the input fields the button collected.
2. Add an Action (Apex Invocable, Update Records, etc.) for the processing logic.
3. Configure as a Screen Flow Quick Action on the object.
4. Optional: add a confirmation screen for user feedback.

**Why not the alternative:** Building a custom LWC for a simple input form is overkill when Screen Flow handles it declaratively.

### Pattern 3: JavaScript List Button → Mass Quick Action with LWC

**When to use:** A Classic JS list button that processes selected records via `getRecordIds()`.

**How it works:**
1. Build an LWC component targeted at `lightning__RecordAction` with `actionType=ScreenAction`.
2. Expose `@api recordIds` (set automatically when invoked from a list).
3. The LWC's `invoke()` method (or the connectedCallback if always invoked once mounted) iterates `this.recordIds` and calls Apex with the collection.
4. Handle partial successes — some records may fail processing.
5. Configure as a List View Action in Setup.

**Why not the alternative:** Direct Apex Invocable Action from a Flow can also work, but loses the per-record progress UI an LWC can provide.

### Pattern 4: URL Button to External System → Lightning URL Action

**When to use:** A Classic button that opens an external system URL with merge field substitution (e.g., a LinkedIn lookup, a CTI dial-out, a partner portal SSO).

**How it works:**
1. In Setup → Object Manager → Buttons, Links, and Actions, create a new Action with type "Custom Visualforce" or "URL".
2. Set the URL with merge fields: `https://external.com/lookup?id={!Account.Id}&name={!Account.Name}`.
3. Configure target window behavior (open in new tab vs replace current).
4. Add to the page layout.

**Why not the alternative:** For a simple URL navigation, an LWC Quick Action is overkill — URL Actions handle this natively.

### Pattern 5: Coexistence — Retain Classic Button, Add Lightning Action

**When to use:** The org has both Classic and Lightning users. Removing the Classic button breaks Classic users; not adding the Lightning equivalent breaks Lightning users.

**How it works:**
1. Keep the Classic Custom Button as-is (works in Classic).
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
| Classic JS list button, processes selected records | Pattern 3: Mass Quick Action with LWC | Handles record-collection processing with progress UI |
| Classic URL button, external system | Pattern 4: Lightning URL Action | Native URL action; no code |
| Classic URL button, relative Salesforce path | Quick Action with NavigationMixin | Relative paths often broken; explicit navigation is safer |
| Visualforce page override button | Quick Action with VF override OR retain as VF | Some VF overrides have no Lightning equivalent |
| S-Control buttons | Rebuild from scratch | S-Controls are fully retired |
| Classic and Lightning both in use | Pattern 5: Coexistence | Don't break Classic users prematurely |
| JS button does complex DOM manipulation | LWC Quick Action with internal DOM logic | DOM access scoped to the LWC's own template |
| Mass action operates on >50 records | Invocable Apex via Mass Action with batch consideration | Large collections may need async processing |
| Button only used in Salesforce Mobile | Check mobile-Quick-Action support per pattern | Some patterns (LWC headless) work on mobile, others don't |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Inventory custom buttons.** Run the Tooling API query for `WebLink`. Group by `BehaviorType` and `ContentSource`. Read each JS button's OnClick body and capture what it does (Apex call, navigation, alert, DOM manipulation).
2. **Categorize each button by pattern.** Apply the Decision Guidance table. Most JS buttons fall into Pattern 1 (Apex call) or Pattern 2 (input prompt). URL buttons usually map cleanly to Pattern 4.
3. **Audit usage.** Confirm which buttons are actively used. Buttons that haven't been invoked in 6+ months should be retired without replacement (validated with the user-team).
4. **Build the Lightning replacements.** Implement per-pattern. Test each against the same scenarios the original button served.
5. **Configure on page layouts and list views.** Each Lightning Action must be added to relevant page layouts (Lightning Actions section) or list view button bars.
6. **Test in sandbox with users from each affected profile.** Specifically: do users find the new action where they expect it? Does the action's UX match the original's intent?
7. **Phased production rollout.** Coexistence first (keep Classic, add Lightning). Monitor usage. Once Lightning replacement adoption is confirmed, retire Classic buttons (or schedule retirement after a soak period).
8. **Document the mapping.** Maintain an audit log: Classic button name → Lightning replacement type → status (Active, Retained for Classic only, Retired).

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every Classic Custom Button has a documented decision: replaced (with what), retained for Classic only, or retired
- [ ] JavaScript buttons that called Apex have been replaced with Headless or Screen LWC Quick Actions (or Screen Flow)
- [ ] URL buttons with absolute external URLs are mapped to Lightning URL Actions
- [ ] URL buttons with relative Salesforce paths are mapped to NavigationMixin-based Quick Actions
- [ ] List buttons that processed selected records have been replaced with Mass Quick Actions
- [ ] All Lightning replacements are added to relevant page layouts and list views
- [ ] User-acceptance testing: representative users from each affected profile confirm the action is discoverable and works as expected
- [ ] Mobile testing: any action that should work in Salesforce Mobile App has been verified on a real mobile device
- [ ] Coexistence period: original Classic button remains in place during the transition for Classic users
- [ ] Audit log of original button → Lightning replacement is committed to source control
- [ ] Apex methods called from Lightning replacements are `@AuraEnabled` with appropriate `with sharing` and FLS enforcement

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **JavaScript buttons silently render as nothing in Lightning Experience.** A user navigating Lightning sees the button's place in the page layout — but the button doesn't render. There's no error message, no "this button isn't supported" indicator. Users assume the action is missing entirely. Audit page layouts for JS buttons and either replace them or flag to users that they're Classic-only.

2. **Mass Action limit on records is 200 by default.** A list view Mass Action that operates on selected records is governor-limited. Selecting 500 records and invoking a Mass Action processes only the first 200. Users notice silently (the unselected 300 just don't get the action applied). For Mass Actions on larger collections, design a Flow with batch processing or an async Apex job.

3. **`{!Account.Id}` URL merge fields don't work the same way in all Lightning Action types.** Lightning URL Actions support some merge fields, but the `{!Object.Field}` syntax differs from the Classic Custom Button merge field syntax in subtle ways. Quick Actions of type "URL" use a slightly different merge syntax than Classic. Test each merge field after migration.

4. **Quick Actions invoked from a Console subtab don't navigate the same way as standard Lightning.** In Service Cloud Console, a Quick Action that uses `NavigationMixin.Navigate({type: 'standard__recordPage'})` opens the navigation in the console workspace — sometimes as a new tab, sometimes replacing the current tab, depending on the action's launch context. If the original button assumed a specific navigation behavior, test in Console mode explicitly.

5. **List View Actions don't appear if the list view filter doesn't match any records.** A Mass Quick Action requires at least one selectable record. Empty list views hide the action entirely. Users assume the action is missing for that list view, when actually no records match the filter.

6. **`window.opener` and cross-window communication patterns from Classic JS don't translate.** Some Classic JS buttons opened a popup window, then communicated back to the parent via `window.opener.location.reload()`. LWC and Lightning Quick Actions have no equivalent — windows are sandboxed differently. Re-architect these flows as Quick Actions that complete in the same context (no popups).

7. **`PageReference` redirects from Classic Apex callbacks don't work in Lightning Quick Actions.** A Classic JS button that called `sforce.apex.execute` and the Apex method returned a `PageReference` — Classic followed the redirect. In Lightning, the redirect is ignored. Re-architect: Apex returns data; LWC explicitly navigates via NavigationMixin after the call resolves.

8. **Hard-coded record IDs in JS buttons don't translate to merge fields cleanly.** Some JS buttons hardcoded record IDs (anti-pattern) for "demo" records or admin actions. The migration is the moment to remove the hardcoded IDs (use Custom Settings, Custom Metadata, or proper record-context resolution). Quick Actions and Flows have no equivalent for "always operate on record X regardless of context."

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Lightning Quick Actions | Object-specific actions replacing Detail Page Buttons |
| LWC Quick Actions (Headless / Screen) | Replacements for JS buttons that need Apex execution and/or custom UI |
| Screen Flow Actions | Replacements for JS buttons that need user input or branching |
| List View Actions / Mass Quick Actions | Replacements for List Buttons that operate on selected records |
| URL Actions | Replacements for URL buttons with absolute external URLs |
| Updated page layouts | Lightning Actions section configured to expose new Quick Actions |
| Migration audit log | Old button → new action mapping with status (Active, Retained, Retired) |
| Coexistence retention list | Classic buttons kept for Classic users with a planned retirement date |

---

## Related Skills

- `admin/quick-actions-and-flow-actions` — Use for new Quick Action / Flow Action design (post-migration)
- `lwc/lwc-quick-actions` — Use for designing LWC Quick Actions in detail (Headless vs Screen)
- `flow/screen-flow-patterns` — Use for designing Screen Flow Actions
- `lwc/visualforce-to-lwc-migration` — Use when buttons reference Visualforce pages being migrated
- `apex/apex-rest-and-aura-enabled` — Use when Apex methods called from new Quick Actions need to be designed correctly
- `admin/lightning-app-builder-advanced` — Use for placing Quick Actions on Lightning Record Pages
