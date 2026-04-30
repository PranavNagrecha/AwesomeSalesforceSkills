# LLM Anti-Patterns — Custom Button to Action Migration

Common mistakes AI coding assistants make when generating or advising on Custom Button to Action migrations.

## Anti-Pattern 1: Recommending Direct JavaScript-to-LWC "Translation"

**What the LLM generates:** Line-by-line conversion of the Classic button's JavaScript into LWC JS — `alert()` becomes `console.log()`, `sforce.apex.execute` becomes some made-up wrapper, `document.getElementById` becomes a `template.querySelector` on cross-component elements.

**Why it happens:** Pattern-matching on syntax similarities.

**Correct pattern:** Re-architect the action, don't translate. Identify the user-facing intent of the button (call Apex, prompt for input, navigate, mass-update). Choose the right Lightning surface (Headless LWC, Screen Flow, URL Action, Mass Quick Action). Build that from scratch. Direct translation produces broken code that almost works but fails in subtle ways (Locker/LWS restrictions, missing global APIs, sandboxed DOM).

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

`alert()` and `confirm()` may work in LWS-disabled orgs but are blocked in LWS-enabled orgs (the modern default) and break the action.

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

**Correct pattern:** Apex returns data only. The LWC explicitly navigates after the call resolves:

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

**What the LLM generates:** A Mass Quick Action that processes whatever record collection is passed in, without any check on size.

**Why it happens:** The model doesn't know about the 200-record default selection limit.

**Correct pattern:** Mass Action selections are capped at 200 records by default. For Apex/Flow that may receive larger collections, explicitly handle the limit: chunk processing, or kick off async batch jobs and notify the user. Always communicate to the user when a chunked or async path is being taken — silently processing only the first 200 is the worst UX.

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

**Correct pattern:** Salesforce Mobile App has subset support for Quick Action types. Some Headless LWC Quick Actions render differently on mobile (drawer vs inline); some Visualforce overrides don't render at all. Test every migrated action on real iOS and Android Salesforce Mobile App devices for any action expected to work on mobile.

## Anti-Pattern 9: Recommending S-Control Conversion Patterns

**What the LLM generates:** A migration plan for S-Control buttons that proposes "convert the S-Control's HTML to Visualforce, then to LWC."

**Why it happens:** Treating S-Controls as if they have a migration path.

**Correct pattern:** S-Controls are fully retired in modern Salesforce. There is no conversion path. Rebuild the underlying functionality from scratch as a Quick Action / LWC / Flow. Don't try to preserve any S-Control content — it predates current security models and security-coding patterns and should be discarded.

## Anti-Pattern 10: Hardcoded Record IDs in Migrated Actions

**What the LLM generates:** A Quick Action's URL or LWC code that contains a hardcoded record ID like `'001000000000abc'` because the original Classic JS button hardcoded it.

**Why it happens:** Verbatim translation of the Classic source.

**Correct pattern:** Hardcoded record IDs were always an anti-pattern in Classic JS buttons (they break across environments, demo orgs, and refresh cycles). Migration is the moment to remove them. Use Custom Settings, Custom Metadata Types, or proper record-context resolution (e.g., always operate on the *current* record's parent, not a hardcoded one). Reject any migration suggestion that preserves hardcoded IDs from the source.
