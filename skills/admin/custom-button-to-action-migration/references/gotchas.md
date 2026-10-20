# Gotchas — Custom Button to Action Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

UNVERIFIED (2026-10-20): Gotchas 1, 2, 3, 4, 5, 6 and 7 describe Lightning runtime behaviour (non-rendering JavaScript buttons, a 200-record selection cap, merge-field syntax, Console navigation, hidden list-view actions, cross-window limits, ignored `PageReference`). None is stated in the Metadata API, Object Reference, Apex or LWC guides, so each is Help-only or field-observed and is marked again inside the gotcha.

## Gotcha 1: JavaScript Buttons Need a Rebuild for Lightning

**What happens:** A Page Layout includes a JavaScript button. In Classic, users see and click it. In Lightning, users may find it absent from the action bar — no error, no "unsupported" indicator — assume the action is missing entirely, file support tickets or work around the missing functionality. UNVERIFIED (2026-10-20): the absence and the silence are Help-only; the corpus only shows that `linkType = javascript` is a valid WebLink value (api_meta 264 L47926-47932).

**Why:** UNVERIFIED (2026-10-20): that Salesforce omits unsupported buttons silently, with no affordance that the button exists in Classic, is Help-only.

**Mitigation:** Audit Page Layouts for JS buttons. For each, either build a Lightning replacement or explicitly notify users that the button is Classic-only (and provide an alternative path). Don't rely on users discovering missing functionality.

## Gotcha 2: Mass Action Selections May Be Capped

**What happens:** A user selects 500 records on a list view and clicks a list-view action. If the cap is 200, the action processes only the first 200 and the other 300 are silently ignored. The user sees no error, just incomplete results. UNVERIFIED (2026-10-20): the 200 figure and the silent truncation are Help-only.

**Why:** UNVERIFIED (2026-10-20): that list-view action selection is capped, and that the framework passes only the first 200 selected record IDs to the invoked Apex / Flow, is Help-only.

**Mitigation:** For Mass Actions that may operate on more records than the cap, design with explicit batch processing. Either: (a) Apex method launches an asynchronous batch job and returns immediately with a "started" toast; (b) Flow uses a Loop with a "process in chunks" subflow; (c) LWC notifies the user that >200 records will be processed asynchronously and queues a job. Always communicate the chunking behavior in the UX.

## Gotcha 3: Classic URL Merge Fields Have No Quick Action Equivalent

**What happens:** A Classic URL button uses `{!Account.Custom_Field__c}` and works perfectly. The migration looks for a quick action that holds the same URL and merge field, and there is none: `QuickActionType` has no URL value (api_meta 264 L102947-102971).

**Why:** Classic merge fields resolve inside the WebLink `url`, which "can include fields as tokens within the URL" (object_reference 264 L314994; api_meta 264 L47984-47986). A Lightning replacement has no URL field to resolve them in, so each value is read and encoded in code. UNVERIFIED (2026-10-20): any quick-action merge syntax, such as `{Record.Custom_Field__c}`, is Help-only.

**Mitigation:** Test every merge field after migration on a real record. Don't assume Classic merge syntax carries over. When in doubt, use an LWC Quick Action where the recordId is exposed via `@api recordId` and the LWC queries the field explicitly.

## Gotcha 4: Console Subtab Quick Action Navigation Behaves Unexpectedly

**What happens:** A Quick Action invokes `NavigationMixin.Navigate({type: 'standard__recordPage', attributes: {recordId: x}})`. In standard Lightning Experience, this opens the record. In Service Cloud Console, it opens as a new subtab — sometimes the user expected it to replace the current subtab. Or the navigation is blocked entirely because the console workspace doesn't allow the navigation type.

**Why:** Service Cloud Console has its own navigation context (`workspaceAPI`, subtab management, primary tab management). Standard NavigationMixin calls don't always honor the console's expected navigation patterns. UNVERIFIED (2026-10-20): Console navigation behaviour is Help-only.

**Mitigation:** For actions invoked in Console, import `lightning/platformWorkspaceApi` and use `openTab`, `openSubtab`, `closeTab` for explicit console-aware navigation (UNVERIFIED (2026-10-20): the module and method names are not in the corpus). Test the action in both standard Lightning Experience AND Service Console contexts before declaring migration complete.

## Gotcha 5: List View Actions Hidden on Empty List Views

**What happens:** A user creates a custom list view with a filter that returns no records. The list-view action button is missing from that list view entirely. Users assume the action is broken or removed.

**Why:** List View Actions require at least one selectable record to display. If the filter returns zero rows, the action button is hidden — there's nothing to act on. UNVERIFIED (2026-10-20): Help-only.

**Mitigation:** Document this behavior. For frequently-empty list views, consider whether the action should be a regular Quick Action (always visible) or a List View Action (visible only when records exist). Sometimes the right fix is to adjust the filter so the list isn't empty.

## Gotcha 6: `window.opener` and Cross-Window Patterns Don't Translate

**What happens:** A Classic JS button opened a popup window for input, then called `window.opener.location.reload()` to refresh the parent. Migration assumes a similar pattern can be re-built in LWC. It can't — popups are sandboxed differently and cross-window communication is restricted by Lightning Web Security.

**Why:** Lightning sandboxes the iframe / window context to prevent cross-frame data leaks. `window.opener` is null or restricted for LWC-launched windows. UNVERIFIED (2026-10-20): the `window.opener` restriction is Help-only; the LWC guide says only that components must not reach the page through `window`/`document` for DOM queries (`create-components-dom-work`).

**Mitigation:** Re-architect the flow. Instead of popup + parent reload, use a Screen Flow Quick Action (modal in the same window) or an LWC Quick Action with internal screens (a screen quick action opens in a modal window, LWC guide `use-quick-actions-screen`). Both complete in the same window context with no cross-window communication.

## Gotcha 7: `PageReference` Returns from Apex Need Explicit LWC Navigation

**What happens:** A Classic JS button called `sforce.apex.execute(...)`; the Apex method returned `new PageReference('/' + recordId)`; Classic followed the redirect. The migrated LWC Quick Action calls the same Apex method (now `@AuraEnabled`) — but no redirect happens (UNVERIFIED (2026-10-20): Help-only). The user is stuck on the original page.

**Why:** `PageReference` is a Visualforce framework object. LWC and Lightning navigation use `NavigationMixin` from JS (LWC guide `use-navigate-quick-action`). Apex methods called from LWC return data; navigation must be explicitly invoked from the LWC. UNVERIFIED (2026-10-20): that Lightning ignores a returned `PageReference` is Help-only.

**Mitigation:** Refactor Apex to return data only (e.g., the new record ID). The LWC then explicitly navigates after the call resolves: `this[NavigationMixin.Navigate]({type: 'standard__recordPage', attributes: {recordId: newId, actionName: 'view'}})`.

## Gotcha 8: Headless LWC Quick Action Doesn't Pass Every Context Variable

**What happens:** A migration assumes a Headless LWC Quick Action will receive `recordId` in `connectedCallback()` and a `userId`, like a JS button could read both via Classic merge fields. Neither arrives that way, and the migration logic depends on them.

**Why:** LWC quick actions, unlike other components on record pages, don't pass `recordId` in `connectedCallback()`; the guide says to set it in code (`use-quick-actions-headless`), and a screen action reads it through an `@api` setter (`use-quick-actions-screen`). Nothing passes a `userId`; the running user is implicit. LWC quick actions run on record pages only, so there is no selection input to read (`use-config-for-quick-actions`).

**Mitigation:** Use `import userId from '@salesforce/user/Id'` to access the current user ID inside the LWC (`get-current-user`). For other user attributes, use `import userField from '@salesforce/schema/User.FirstName'` etc. The pattern is different from Classic but the data is accessible.

## Gotcha 9: Salesforce Mobile App Quick Actions Don't Always Match Lightning Desktop

**What happens:** A Quick Action works perfectly on Lightning desktop. On Salesforce Mobile App, it either doesn't appear, appears but doesn't invoke, or invokes with a degraded UI.

**Why:** Using a Lightning web component as a quick action isn't supported in the Salesforce mobile app (LWC guide `use-config-for-quick-actions`). UNVERIFIED (2026-10-20): that other action types have subset support, or that Custom Visualforce overrides and certain navigation patterns fail, is Help-only.

**Mitigation:** Test every migrated Quick Action on Salesforce Mobile App for both iOS and Android. Some actions need a non-LWC variant for mobile, or a form-factor check in the component (`@salesforce/client/formFactor` returns Large, Medium or Small; LWC guide `create-client-form-factor`).

## Gotcha 10: Coexistence Period Without Adoption Tracking Drags On

**What happens:** A migration introduces Lightning replacements while keeping Classic buttons "for the transition." Months later, both still exist, neither has been retired, and the codebase complexity is permanently increased.

**Why:** Without measurement, there's no trigger for retiring the Classic version. Inertia preserves both indefinitely.

**Mitigation:** Instrument both surfaces with a tracking field (Example 6 in the examples file). Set a quantitative retirement criterion ("when 95% of invocations come from Lightning, retire Classic"). Schedule the retirement decision at a fixed date, not "when we feel ready."
