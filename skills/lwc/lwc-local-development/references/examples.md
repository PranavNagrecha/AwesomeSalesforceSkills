# Examples — LWC Local Development

All commands below are illustrative and authored from the official Lightning Web Components
developer guide and the `@salesforce/plugin-lightning-dev` reference. Replace org aliases,
component, app, and site names with your own. Run against a **sandbox or scratch org**, not
production.

## Example 1: Single-component inner loop

**Context:** you're iterating on an `accountTile` LWC that reads an Account through Lightning
Data Service and want a fast edit-save-see loop against real org data.

**Problem:** deploying and navigating to an app page for every markup or CSS tweak is slow and
clutters the org.

**Solution:**

```bash
# Plugin is auto-installed with Salesforce CLI (`sf update` if missing)

# Preview a single component in isolation against a sandbox
sf lightning dev component --target-org mySandbox --name accountTile
```

First run prompts you to enable the feature — press Enter or type `y`. Then edit the bundle:

```javascript
// accountTile.js — a JS method change like this HOT-RELOADS on save
get formattedName() {
    return this.account?.data?.fields?.Name?.value ?? 'Unknown';
}
```

```html
<!-- accountTile.html — attribute/markup changes HOT-RELOAD on save -->
<lightning-card title={formattedName}></lightning-card>
```

**Why it works:** single-component preview supports platform modules — LDS wire adapters,
`@salesforce` scoped modules, and Apex controllers — so the component renders with live data,
and template/CSS/JS-method edits push to the browser on save.

---

## Example 2: A change that needs a manual refresh

**Context:** the same `accountTile`, but now you add a new public property.

**Problem:** you save and nothing changes in the preview — it looks broken.

**Solution:** recognize this edit is in the **manual-reload** category and refresh the browser
(for single-component preview) or redeploy + restart (for app/site preview).

```javascript
// accountTile.js — a NEW @api property does NOT hot-reload
import { LightningElement, api, wire } from 'lwc';
import { getRecord } from 'lightning/uiRecordApi';

export default class AccountTile extends LightningElement {
    @api recordId;
    @api variant = 'base';        // <-- newly added @api: refresh the browser to pick it up

    // A NEW @wire config also does NOT hot-reload
    @wire(getRecord, { recordId: '$recordId', fields: ['Account.Name'] })
    account;
}
```

Edits that need the manual step: **new `@api` properties/methods, `@wire` adapter changes,
new `@salesforce` imports, and any `.js-meta.xml` update.**

**Why it works:** the preview server keeps serving the last compiled build for these change
classes; a refresh (single component) or `sf project deploy start` + server restart
(app/site) forces the rebuild.

---

## Example 3: Full-app preview on desktop and mobile

**Context:** you need to verify `accountTile` inside a real Lightning app and on the Salesforce
mobile app.

**Solution:**

```bash
# Desktop app preview
sf lightning dev app --target-org mySandbox --name Sales_Console

# iOS simulator (requires Xcode installed from the Mac App Store)
sf lightning dev app -o mySandbox -n Sales_Console --device-type ios

# Android emulator (requires Android Studio)
sf lightning dev app -o mySandbox -n Sales_Console --device-type android
```

**Why it works:** app preview reproduces app-level navigation and cross-component context that
single-component preview can't; mobile targets render in the native simulator once the
platform SDK is present. The CLI prompts to install the Salesforce mobile app if it's missing.

---

## Example 4: Experience (LWR) site preview

**Context:** previewing LWR Experience Cloud site changes before publishing.

**Solution:**

```bash
sf lightning dev site --target-org mySandbox --name Customer_Portal
```

**Why it works:** site preview renders the LWR site locally in the browser (desktop only), so
you can iterate without hitting the publish-time freeze. Aura sites are not supported — see
`lwc/lwr-site-development`.

---

## Example 5: VS Code Live Preview extension

**Context:** you prefer to stay in the IDE rather than the terminal.

**Solution:** with the Live Preview VS Code extension installed, right-click a component (or use
the Command Palette) to launch its preview. LWC preview in the extension is **generally
available**; **React component preview is Beta**.

**Why it works:** the extension wraps the single-component preview flow — same live-reload
behavior and the same manual-reload caveats for `@api`/`@wire`/`.js-meta.xml` changes.

---

## Anti-Pattern: expecting Live Preview to replace tests

**What practitioners do:** treat a clean render in Live Preview as proof the component is
correct and skip Jest.

**What goes wrong:** preview confirms it *renders* against one org's data; it doesn't assert
behavior, cover error branches, or run in CI. Regressions slip through.

**Correct approach:** use Live Preview for the visual/interactive inner loop, then run Jest
(`lwc/lwc-testing`) and deploy through the normal pipeline before calling the work done.
