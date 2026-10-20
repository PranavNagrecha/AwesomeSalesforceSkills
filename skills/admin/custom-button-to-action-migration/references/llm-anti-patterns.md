# LLM Anti-Patterns — Custom Button to Action Migration

Common mistakes AI coding assistants make when generating or advising on Custom Button to Action migrations.

UNVERIFIED (2026-10-20): Anti-Patterns 3, 5 and 8 restate Help-only Lightning behaviour (ignored `PageReference`, the 200-record cap, mobile subset support) and are marked inside each.

## Anti-Pattern 1: Recommending Direct JavaScript-to-LWC "Translation"

**What the LLM generates:** Line-by-line conversion of the Classic button's JavaScript into LWC JS — `alert()` becomes `console.log()`, `sforce.apex.execute` becomes some made-up wrapper, `document.getElementById` becomes a `template.querySelector` on cross-component elements.

**Why it happens:** Pattern-matching on syntax similarities.

**Correct pattern:** Re-architect the action, don't translate. Identify the user-facing intent of the button (call Apex, prompt for input, navigate, mass-update). Choose the right Lightning surface (Headless LWC, Screen Flow, a headless LWC that navigates for URL buttons, or a mass quick action for a create or update on a selection, api_meta 264 L47565-47572). Build that from scratch. Direct translation produces broken code that almost works but fails in subtle ways (missing global APIs, DOM access limited to the component's own template).

## Anti-Pattern 2: Using `alert()` and `confirm()` in LWC

**What the LLM generates:**

```js
async invoke() {
    if (confirm("Are you sure?")) {
        await someApex();
        alert("Done");
    }
}
```

**Why it happens:** These are universal browser APIs.

**Correct pattern:** Use `LightningConfirm` and `ShowToastEvent`:

```js
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import LightningConfirm from 'lightning/confirm';

async invoke() {
    const confirmed = await LightningConfirm.open({
        message: 'Are you sure?',
        variant: 'header',
        label: 'Confirm action'
    });
    if (confirmed) {
        await someApex();
        this.dispatchEvent(new ShowToastEvent({ title: 'Done', variant: 'success' }));
    }
}
```

The guide presents `LightningConfirm` as the alternative to the native `window.confirm()`, which isn't supported for cross-origin iframes in Chrome and Safari, and `LightningConfirm.open()` returns a promise instead of halting the page (LWC guide `use-dialog-confirm`; `use-dialog-alert` gives `LightningAlert` the same role). A native call can therefore break the action. UNVERIFIED (2026-10-20): that Lightning Web Security blocks them is not in the corpus or the LWC guide pages read.

## Anti-Pattern 3: Returning `PageReference` from `@AuraEnabled` Apex Called by LWC Action

**What the LLM generates:**

```apex
@AuraEnabled
public static PageReference saveAndRedirect(Id recId) {
    update [SELECT Id, Status__c FROM Account WHERE Id = :recId];
    return new PageReference('/' + recId);
}
```

**Why it happens:** Carrying over Classic patterns.

**Correct pattern:** Apex returns data only. The LWC explicitly navigates after the call resolves (UNVERIFIED (2026-10-20): that Lightning ignores a returned `PageReference` is Help-only):

```apex
@AuraEnabled
public static Id save(Id recId) {
    Account a = [SELECT Id, Status__c FROM Account WHERE Id = :recId];
    a.Status__c = 'Active';
    update a;
    return a.Id;
}
```

```js
async invoke() {
    const id = await save({ recId: this.recordId });
    this[NavigationMixin.Navigate]({
        type: 'standard__recordPage',
        attributes: { recordId: id, actionName: 'view' }
    });
}
```

## Anti-Pattern 4: Skipping the Coexistence Period

**What the LLM generates:** Migration plan that says "Build the Lightning replacement; remove the Classic button."

**Why it happens:** Treating migration as a single-step swap.

**Correct pattern:** Coexistence (Pattern 5 in SKILL.md) is mandatory if Classic users exist. Removing the Classic button immediately breaks production for Classic users. Even in a Lightning-only org, retain the Classic button for at least one release cycle to handle edge cases (admins still using Classic Setup, browser sessions that haven't migrated). Track adoption via instrumentation (Example 6); retire when adoption metric is met.

## Anti-Pattern 5: Ignoring Mass Action Limits

**What the LLM generates:** A list-view action that processes whatever record collection is passed in, without any check on size.

**Why it happens:** The model doesn't know that list-view selections can be capped (UNVERIFIED (2026-10-20): the 200-record default is Help-only).

**Correct pattern:** Assume a selection cap and verify it in a sandbox. For Apex/Flow that may receive larger collections, explicitly handle the limit: chunk processing, or kick off async batch jobs and notify the user. Always communicate to the user when a chunked or async path is being taken — silently processing only the first 200 is the worst UX.

## Anti-Pattern 6: Recommending Headless LWC for Actions That Need Input

**What the LLM generates:** Headless LWC Quick Action for an action that requires user input ("ask for a reason before closing the case").

**Why it happens:** Headless feels like the "modern" replacement for one-click Classic JS buttons.

**Correct pattern:** Headless LWC Quick Actions have NO UI. They're for one-click "do it now" operations. Actions that need input require either: (a) a Screen LWC Quick Action with a form, (b) a Screen Flow Action with collection screens, or (c) the Lightning Confirm modal pattern. Choose based on input complexity — simple input → Confirm or Screen Flow; rich input → Screen LWC.

## Anti-Pattern 7: Using `document.getElementById` for Cross-Component DOM Access

**What the LLM generates:** LWC code that does `document.getElementById('related-list').innerHTML = ...` to update content outside the LWC's own template.

**Why it happens:** Carrying over global-DOM patterns from Classic JavaScript.

**Correct pattern:** LWC sandboxes DOM access to its own template. `this.template.querySelector(...)` works only on the component's own DOM. To affect other components, use Lightning Message Service (LMS) to broadcast events, or use `RefreshEvent` to ask the platform to refresh related components, or restructure as a parent-child hierarchy with `@api` properties.

## Anti-Pattern 8: Not Testing on Salesforce Mobile App

**What the LLM generates:** Migration plan with desktop-browser testing only.

**Why it happens:** Mobile is a forgotten surface.

**Correct pattern:** An LWC quick action is not supported in the Salesforce mobile app (LWC guide `use-config-for-quick-actions`), so a migration that moves a mobile-used button to LWC loses it there. Test every migrated action on real iOS and Android Salesforce Mobile App devices for any action expected to work on mobile. UNVERIFIED (2026-10-20): subset support for other types, drawer rendering and Visualforce overrides not rendering are Help-only.

## Anti-Pattern 9: Recommending S-Control Conversion Patterns

**What the LLM generates:** A migration plan for S-Control buttons that proposes "convert the S-Control's HTML to Visualforce, then to LWC."

**Why it happens:** Treating S-Controls as if they have a migration path.

**Correct pattern:** S-controls are deprecated (since Spring '09, api_meta 264 L45109-45110; the `Scontrol` type is marked Deprecated, L109760-109761). There is no conversion path to preserve. Rebuild the underlying functionality from scratch as a Quick Action / LWC / Flow. Don't try to preserve any S-Control content — it predates current security models and security-coding patterns and should be discarded.

## Anti-Pattern 10: Hardcoded Record IDs in Migrated Actions

**What the LLM generates:** An LWC quick action or Flow that contains a hardcoded record ID like `'001000000000abc'` because the original Classic JS button hardcoded it.

**Why it happens:** Verbatim translation of the Classic source.

**Correct pattern:** Hardcoded record IDs were always an anti-pattern in Classic JS buttons (they break across environments, demo orgs, and refresh cycles). Migration is the moment to remove them. Use Custom Settings, Custom Metadata Types, or proper record-context resolution (e.g., always operate on the *current* record's parent, not a hardcoded one). Reject any migration suggestion that preserves hardcoded IDs from the source.
