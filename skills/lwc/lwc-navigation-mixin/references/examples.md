# Examples — LWC NavigationMixin

Two worked scenarios and one anti-pattern. Each example uses
`NavigationMixin` correctly applied via the `extends` mixin pattern
and chooses a PageReference type that matches the surface (internal
Lightning vs Experience Cloud).

---

## Example 1: "Open in new tab" link generated from a record list

**Context:** An LWC on an Opportunity record page renders a list of
related Cases (custom rendering, not the standard related list).
Each row needs an "Open in new tab" affordance that lets the user
ctrl/cmd-click or right-click → "Open link in new tab" — standard
browser behavior. The link must point to the standard Salesforce
Case record page, not a custom URL.

**Problem:** Practitioners use `NavigationMixin.Navigate` directly
in a click handler, which routes inside the current tab and breaks
ctrl-click. Or they hand-build the URL: `'/lightning/r/Case/' + caseId + '/view'`,
which works in Lightning Experience but breaks in Experience Cloud
(wrong base path), mobile (wrong scheme), and survives Salesforce
infrastructure changes only until the next URL routing update.
The correct pattern uses `NavigationMixin.GenerateUrl` to produce a
context-appropriate URL and wraps it in a standard `<a>` anchor.

**Solution:**

```javascript
// caseListRow.js
import { LightningElement, api } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';

export default class CaseListRow extends NavigationMixin(LightningElement) {
    @api caseRecord;
    caseUrl;

    async connectedCallback() {
        this.caseUrl = await this[NavigationMixin.GenerateUrl]({
            type: 'standard__recordPage',
            attributes: {
                recordId: this.caseRecord.Id,
                objectApiName: 'Case',
                actionName: 'view'
            }
        });
    }
}
```

```html
<!-- caseListRow.html -->
<template>
    <a href={caseUrl} class="case-link">
        {caseRecord.CaseNumber} — {caseRecord.Subject}
    </a>
</template>
```

**Why it works:** The `<a href>` is a real anchor, so the browser
honors all native interactions: click (in-tab), ctrl/cmd-click
(new tab), right-click → copy link, middle-click (new tab in some
browsers), keyboard focus + Enter. `GenerateUrl` returns the
correct URL for the current Salesforce context — Lightning
Experience, Experience Cloud, or mobile-wrapped — without the
component knowing which surface it's running on. The `async
connectedCallback` ensures the URL is ready before the first
render; if the user clicks before `connectedCallback` resolves
(rare), the anchor's `href` is empty and the click is a no-op
rather than a broken navigation.

---

## Example 2: Programmatic navigation with `state` for post-navigation context

**Context:** A custom "Quick Triage" LWC presents the user with three
buttons: "Escalate this Case to the Compliance queue," "Defer to next
quarter," "Mark resolved." All three navigate to the Case record page
but each should land on a *different default tab* (Escalation,
Activities, Resolution Details respectively). The receiving Case
record page has a custom LWC that reads which tab to open on load.

**Problem:** The naive approach passes the tab info via URL hash or
a session variable, both of which break in unexpected ways
(session vars don't survive a browser refresh; URL hash conflicts
with Salesforce's own routing). The correct pattern is the
PageReference `state` object — custom keys must be prefixed `c__`
or the platform strips them.

**Solution:**

```javascript
// quickTriage.js
import { LightningElement, api } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';

const TAB_TO_NAVIGATE = {
    escalate: 'escalation',
    defer:    'activities',
    resolve:  'resolution-details'
};

export default class QuickTriage extends NavigationMixin(LightningElement) {
    @api caseId;

    handleAction(event) {
        const action = event.target.dataset.action;  // 'escalate' | 'defer' | 'resolve'
        const tab = TAB_TO_NAVIGATE[action];
        if (!tab) return;

        this[NavigationMixin.Navigate]({
            type: 'standard__recordPage',
            attributes: {
                recordId: this.caseId,
                objectApiName: 'Case',
                actionName: 'view'
            },
            state: {
                c__triageTab: tab,
                c__triageReason: action
            }
        });
    }
}
```

```javascript
// caseRecordPageHost.js (the receiver on the target page)
import { LightningElement, wire } from 'lwc';
import { CurrentPageReference } from 'lightning/navigation';

export default class CaseRecordPageHost extends LightningElement {
    activeTab;

    @wire(CurrentPageReference)
    setPageContext(pageRef) {
        const tabFromState = pageRef?.state?.c__triageTab;
        if (tabFromState) {
            this.activeTab = tabFromState;
        }
    }
}
```

**Why it works:** The `c__` prefix tells the platform "this is a
custom state key, please preserve it." Without the prefix
(e.g., `state: { triageTab: 'escalation' }`), Salesforce strips
the key from the URL — the receiving component sees `pageRef.state.triageTab === undefined`.
The `CurrentPageReference` wire is the canonical way to read the
state on the receiver side; it re-fires on every navigation,
so the receiver doesn't need its own URL-parsing logic.

---

## Anti-Pattern: `window.location.href = ...` for navigation

**What practitioners do:**

```javascript
handleOpen() {
    window.location.href = '/lightning/r/Case/' + this.caseId + '/view';
}
```

Or, in Experience Cloud:

```javascript
window.location.href = '/s/case/' + this.caseId;
```

**What goes wrong:** Several things, each painful:

1. **Bypasses Salesforce's tab and routing infrastructure.** The
   browser performs a full page reload — every LWC on the page
   re-mounts, every wire re-fires, the user loses unsaved form
   state, and the "Recently Viewed" entry is logged twice (once
   for the source page, once for the destination).
2. **Breaks across surfaces.** The Lightning Experience URL pattern
   doesn't work in Experience Cloud, and vice versa. The component
   has to detect which surface it's on (no clean way) and switch
   URL formats — exactly the problem `NavigationMixin` solves.
3. **Breaks on mobile.** The Salesforce mobile app intercepts
   navigation through its own routing layer. A `window.location`
   reload from inside the app may force the wrapper to fall back
   to the desktop view, kicking the user out of the app shell.
4. **CSP enforcement.** Newer org permissions (Locker, Lightning
   Web Security) increasingly restrict direct `window` mutations.
   `window.location.href = ...` may throw or be silently no-op'd
   under tighter security profiles, depending on Salesforce
   release version.

**Correct approach:** Use `NavigationMixin.Navigate` for in-tab
navigation and `GenerateUrl` + `<a>` for ctrl-click-able links.
The only legitimate use of `window.open` (NOT `window.location`)
inside an LWC is to open an external URL when you can't or
shouldn't use `standard__webPage` — and even then, prefer
`NavigationMixin.Navigate({ type: 'standard__webPage', attributes: { url } })`
so Salesforce can wrap the external link with its own click-tracking
and security policies.

If you truly need a hard browser refresh — say, after a
deploy-triggered cache flush — that's a workflow issue, not
an LWC concern: surface a "please refresh" toast and let the
user do it, rather than triggering it from inside an LWC.
