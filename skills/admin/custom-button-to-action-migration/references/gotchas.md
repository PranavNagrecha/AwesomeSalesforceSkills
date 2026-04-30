# Gotchas — Custom Button to Action Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: JavaScript Buttons Render as Nothing in Lightning — Silently

**What happens:** A Page Layout includes a JavaScript button. In Classic, users see and click it. In Lightning, the button is absent from the action bar — no error, no "unsupported" indicator. Users assume the action is missing entirely; they may file support tickets or work around the missing functionality.

**Why:** Salesforce's design choice for unsupported buttons in Lightning is silent omission. There's no UI affordance signaling that the button exists in Classic.

**Mitigation:** Audit Page Layouts for JS buttons. For each, either build a Lightning replacement or explicitly notify users that the button is Classic-only (and provide an alternative path). Don't rely on users discovering missing functionality.

## Gotcha 2: Mass Action Default Limit Is 200 Records

**What happens:** A user selects 500 records on a list view and clicks a Mass Quick Action. The action processes only the first 200; the other 300 are silently ignored. The user sees no error, just incomplete results.

**Why:** Mass Action / List View Action selection is governor-limited. The framework passes only the first 200 selected record IDs to the invoked Apex / Flow / LWC.

**Mitigation:** For Mass Actions that may operate on >200 records, design with explicit batch processing. Either: (a) Apex method launches an asynchronous batch job and returns immediately with a "started" toast; (b) Flow uses a Loop with a "process in chunks" subflow; (c) LWC notifies the user that >200 records will be processed asynchronously and queues a job. Always communicate the chunking behavior in the UX.

## Gotcha 3: Quick Action Merge Fields Differ from Classic Button Merge Fields

**What happens:** A Classic URL button uses `{!Account.Custom_Field__c}` and works perfectly. The migrated Quick Action uses the same syntax in the URL field — but the merge field doesn't resolve. The URL contains literal `{!Account.Custom_Field__c}` instead of the value.

**Why:** Quick Actions use a different merge field syntax than Classic Custom Buttons. Quick Action URLs use `{!Account.Custom_Field__c}` for some merge contexts but not all; some require `{Record.Custom_Field__c}`. Behavior varies by Quick Action type and target context.

**Mitigation:** Test every merge field after migration on a real record. Don't assume Classic merge syntax carries over. When in doubt, use an LWC Quick Action where the recordId is exposed via `@api recordId` and the LWC queries the field explicitly.

## Gotcha 4: Console Subtab Quick Action Navigation Behaves Unexpectedly

**What happens:** A Quick Action invokes `NavigationMixin.Navigate({type: 'standard__recordPage', attributes: {recordId: x}})`. In standard Lightning Experience, this opens the record. In Service Cloud Console, it opens as a new subtab — sometimes the user expected it to replace the current subtab. Or the navigation is blocked entirely because the console workspace doesn't allow the navigation type.

**Why:** Service Cloud Console has its own navigation context (`workspaceAPI`, subtab management, primary tab management). Standard NavigationMixin calls don't always honor the console's expected navigation patterns.

**Mitigation:** For actions invoked in Console, import `lightning/platformWorkspaceApi` and use `openTab`, `openSubtab`, `closeTab` for explicit console-aware navigation. Test the action in both standard Lightning Experience AND Service Console contexts before declaring migration complete.

## Gotcha 5: List View Actions Hidden on Empty List Views

**What happens:** A user creates a custom list view with a filter that returns no records. The Mass Quick Action button is missing from that list view entirely. Users assume the action is broken or removed.

**Why:** List View Actions require at least one selectable record to display. If the filter returns zero rows, the action button is hidden — there's nothing to act on.

**Mitigation:** Document this behavior. For frequently-empty list views, consider whether the action should be a regular Quick Action (always visible) or a List View Action (visible only when records exist). Sometimes the right fix is to adjust the filter so the list isn't empty.

## Gotcha 6: `window.opener` and Cross-Window Patterns Don't Translate

**What happens:** A Classic JS button opened a popup window for input, then called `window.opener.location.reload()` to refresh the parent. Migration assumes a similar pattern can be re-built in LWC. It can't — popups are sandboxed differently and cross-window communication is restricted by Lightning Web Security.

**Why:** Lightning sandboxes the iframe / window context to prevent cross-frame data leaks. `window.opener` is null or restricted for LWC-launched windows.

**Mitigation:** Re-architect the flow. Instead of popup + parent reload, use a Screen Flow Quick Action (modal in the same window) or an LWC Quick Action with internal screens. Both complete in the same window context with no cross-window communication.

## Gotcha 7: `PageReference` Returns from Apex Are Ignored in Lightning Actions

**What happens:** A Classic JS button called `sforce.apex.execute(...)`; the Apex method returned `new PageReference('/' + recordId)`; Classic followed the redirect. The migrated LWC Quick Action calls the same Apex method (now `@AuraEnabled`) — but no redirect happens. The user is stuck on the original page.

**Why:** `PageReference` is a Visualforce framework object. LWC and Lightning navigation use `NavigationMixin` from JS. Apex methods called from LWC return data; navigation must be explicitly invoked from the LWC.

**Mitigation:** Refactor Apex to return data only (e.g., the new record ID). The LWC then explicitly navigates after the call resolves: `this[NavigationMixin.Navigate]({type: 'standard__recordPage', attributes: {recordId: newId, actionName: 'view'}})`.

## Gotcha 8: Headless LWC Quick Action Doesn't Support All Context Variables

**What happens:** A migration assumes a Headless LWC Quick Action will receive both `recordId` and `userId`, like a JS button could read both via Classic merge fields. The LWC receives `recordId` but not `userId` — and the migration logic depends on the user context.

**Why:** Headless LWC Quick Actions expose `@api recordId` (when invoked from a record page) and `@api selectedIds` (when invoked from a list). They don't expose a `userId` automatically — the running user is implicit.

**Mitigation:** Use `import userId from '@salesforce/user/Id'` to access the current user ID inside the LWC. For other user attributes, use `import userField from '@salesforce/schema/User.FirstName'` etc. The pattern is different from Classic but the data is accessible.

## Gotcha 9: Salesforce Mobile App Quick Actions Don't Always Match Lightning Desktop

**What happens:** A Quick Action works perfectly on Lightning desktop. On Salesforce Mobile App, it either doesn't appear, appears but doesn't invoke, or invokes with a degraded UI.

**Why:** Mobile app's Lightning runtime has subset support for Quick Action types. Headless LWC Quick Actions may render in a mobile drawer instead of inline; some action types (Custom Visualforce overrides, certain navigation patterns) don't work on mobile.

**Mitigation:** Test every migrated Quick Action on Salesforce Mobile App for both iOS and Android. Some actions may need mobile-specific variants (use `$Browser.FormFactor` in component visibility or build a separate mobile-friendly action).

## Gotcha 10: Coexistence Period Without Adoption Tracking Drags On

**What happens:** A migration introduces Lightning replacements while keeping Classic buttons "for the transition." Months later, both still exist, neither has been retired, and the codebase complexity is permanently increased.

**Why:** Without measurement, there's no trigger for retiring the Classic version. Inertia preserves both indefinitely.

**Mitigation:** Instrument both surfaces with a tracking field (Example 6 in the examples file). Set a quantitative retirement criterion ("when 95% of invocations come from Lightning, retire Classic"). Schedule the retirement decision at a fixed date, not "when we feel ready."
