# Examples — LWC ShowToast Patterns

Two worked scenarios and one anti-pattern showing how to dispatch
`ShowToastEvent` from `lightning/platformShowToastEvent` with the
right `variant`, `mode`, and `messageData` shape. The scenarios cover
the two most common shapes: a success toast that embeds a clickable
record link via `messageData` token substitution, and a sticky error
toast that surfaces a parsed UI API error to a user who needs to
read and act on it. The anti-pattern shows what breaks when
practitioners reach for `window.alert()` or a hand-rolled banner
instead of the platform event.

---

## Example 1: Success toast with a clickable record link via `messageData`

**Context:** A bulk-edit LWC ("Reassign Contacts") lets the user
reassign N Contacts to a different Account in one action. On
success, the user wants confirmation of the count *and* a one-click
way to navigate to the new owning Account so they can verify the
result. Pluralization matters — "1 contact was updated" reads
correctly; "1 contacts were updated" looks broken.

**Problem:** Practitioners build the message with template string
concatenation: `` message: `${count} contacts were updated. See ${accountName}` ``.
That produces a literal string with no clickable link — the user
has to navigate to the Account manually. Switching to a custom
event that the parent listens for adds three components of plumbing
(modal → parent → record page navigation) for what should be a
single toast.

**Solution:** Use the `messageData` token-substitution syntax with
the `{ url, label }` link shape at the right index. The platform
renders the matching token as an anchor with the URL and the
provided label as the visible text.

```javascript
// reassignContactsAction.js
import { LightningElement, api } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import reassign from '@salesforce/apex/ContactReassignController.reassign';

export default class ReassignContactsAction extends LightningElement {
    @api selectedIds = [];
    @api targetAccountId;
    @api targetAccountName;

    async handleReassign() {
        try {
            const count = await reassign({
                contactIds: this.selectedIds,
                accountId: this.targetAccountId
            });

            const noun = count === 1 ? 'contact was' : 'contacts were';
            this.dispatchEvent(new ShowToastEvent({
                title: 'Reassignment Complete',
                message: '{0} ' + noun + ' reassigned to {1}.',
                messageData: [
                    String(count),
                    {
                        url: `/lightning/r/Account/${this.targetAccountId}/view`,
                        label: this.targetAccountName
                    }
                ],
                variant: 'success',
                mode: 'dismissible'
            }));
        } catch (e) {
            // see Example 2 for the error branch
        }
    }
}
```

**Why it works:** `messageData` is an array of substitution values
matched against the `{0}..{N}` tokens in `message`. Each entry can be
either a plain string (substituted as text) or an object of shape
`{ url, label }` (substituted as a rendered anchor with `url` as the
href and `label` as the visible link text). Index `{0}` gets the
count as text; index `{1}` gets the URL/label object as a clickable
link to the target Account. The platform handles the anchor element
markup, SLDS link styling, and screen-reader-friendly role
assignment — practitioners do not need to inject HTML into `message`,
which would be sanitized to plain text anyway.

The `variant: 'success'` choice triggers the green checkmark icon
and success accent color from SLDS. The `mode: 'dismissible'`
auto-dismisses after 5 seconds and gives the user the close (X)
button if they want to dismiss earlier — appropriate for a
confirmation that doesn't need extended dwell time. The
pluralization branch (`count === 1`) is handled in JS rather than
in `messageData` because `ShowToastEvent` has no plural-form
helper; the alternative is two separate dispatch paths, which adds
duplication for no benefit.

---

## Example 2: Sticky error toast with parsed UI API error extraction

**Context:** The same Reassign action above can fail in several
shapes: a validation rule fires server-side and the UI API returns
a structured error body, a CRUD/FLS check fails with a different
body shape, a network timeout fires before the response, or the
Apex method throws an `AuraHandledException`. Each surfaces as a
different exception shape on the JS side. The user needs to see
the actual error message (so they can fix the data and retry) and
needs enough time to read a multi-line error — not 5 seconds.

**Problem:** Practitioners write `message: error.message` and ship
it. UI API errors arrive with the user-facing text under
`error.body.message` (for `lightning/uiRecordApi` calls) or
`error.body[0].message` (for some Apex error shapes), not on
`error.message` directly. Result: every toast says "Save failed"
with no actionable text. Or practitioners use the default
`mode: 'dismissible'` for the error toast and the user gets a
5-second window to read a 4-line validation error before it
auto-dismisses, no recourse to re-read.

**Solution:** Extract the message via a defensive fallback chain
and set `mode: 'sticky'` so the toast stays until the user
explicitly dismisses it.

```javascript
// reassignContactsAction.js — error branch
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

handleError(error) {
    // UI API errors expose .body.message; Apex AuraHandledException
    // surfaces .body.message too; some shapes use .body[0].message
    // (array of FieldApiName errors). Fall back to .message, then
    // a generic string so we never display 'undefined'.
    const userMessage =
        error?.body?.message
        ?? (Array.isArray(error?.body) ? error.body[0]?.message : null)
        ?? error?.message
        ?? 'An unexpected error occurred. Check the browser console.';

    this.dispatchEvent(new ShowToastEvent({
        title: 'Reassignment Failed',
        message: userMessage,
        variant: 'error',
        mode: 'sticky'
    }));

    // Also log the full error for debugging — toast shows only
    // the user-facing string; engineers need the full shape.
    // eslint-disable-next-line no-console
    console.error('Reassignment failed', JSON.stringify(error));
}
```

**Why it works:** The fallback chain handles the three common UI
API / Apex error shapes in priority order: structured `.body.message`
first (UI API record write errors, Apex `AuraHandledException`),
then array-of-errors `.body[0].message` (some Apex bulk-error
shapes), then plain `.message` (network errors, unhandled
JavaScript exceptions). The final string fallback prevents the
literal `undefined` from rendering — a common bug when a new
error shape ships and the fallback chain misses it.

`variant: 'error'` gives the toast the red-accent error styling
and the error icon. `mode: 'sticky'` keeps the toast on screen
until the user clicks the close (X) button — no auto-dismiss.
This is the correct choice for errors because (a) the user
likely needs to read the message to know what to fix, and (b) a
5-second window is not enough for any non-trivial validation
message. The `pester` mode is an alternative that also stays
visible until dismissed, but `pester` is only valid for the
`'error'` variant and behaves identically to `sticky` for that
case — `sticky` is the more general choice that works across
variants without surprise. The companion `console.error` is not
about the toast — it ensures the full error object is captured
for engineers debugging via the browser DevTools, since the toast
intentionally shows only the user-facing string.

---

## Anti-Pattern: Using `window.alert()` or a hand-rolled in-component banner for transient feedback

**What practitioners do:**

```javascript
// reassignContactsAction.js — DON'T DO THIS
async handleReassign() {
    try {
        const count = await reassign({ /* ... */ });
        // Anti-pattern A: native browser alert
        // eslint-disable-next-line no-alert
        window.alert(`${count} contacts were updated.`);
    } catch (e) {
        // Anti-pattern B: in-component banner toggle
        this.bannerVariant = 'error';
        this.bannerMessage = e.message;
        this.showBanner = true;
        setTimeout(() => { this.showBanner = false; }, 3000);
    }
}
```

```html
<!-- with a hand-rolled banner in the template -->
<template lwc:if={showBanner}>
    <div class={bannerClass} role="status">
        <p>{bannerMessage}</p>
    </div>
</template>
```

**What goes wrong:**

1. **`window.alert()` is blocking and unstyled.** It freezes the
   entire browser tab until the user clicks OK, including any
   other JavaScript on the page (other LWCs, the navigation bar,
   keyboard shortcuts). It renders as a native OS dialog with no
   Lightning Experience styling — visually jarring and instantly
   recognizable as "an LWC the team didn't finish." Mobile
   Salesforce app and Mobile Publisher apps may render the alert
   in inconsistent positions or block it entirely depending on
   the WKWebView wrapper.
2. **Hand-rolled banners lose the platform's a11y wiring.** A
   proper LEX toast announces itself to assistive technology via
   the platform's `aria-live` region (one per page, managed by
   the host). A bespoke `<div role="status">` adds a *second*
   live region that competes with the platform's — screen
   readers may announce both, neither, or only one depending on
   timing. Toast events ship with the platform's tested focus and
   announcement behavior; the banner does not.
3. **No central dismiss control.** Toasts dispatched via
   `ShowToastEvent` are queued and dismissed by the Lightning
   page host — the user has one consistent close (X) button in a
   consistent position. A bespoke banner is rendered inside the
   parent component's shadow tree, dismissed by a `setTimeout`
   the developer wrote, and discoverable only if the user
   happens to look at the right region. Two bespoke banners from
   two LWCs on the same page collide visually with no z-index
   coordination.
4. **`window.alert()` is blocked or unsupported in several
   platform surfaces.** Aura inside an iframe in Visualforce,
   strict-CSP Experience Cloud sites, and Quick Action overlays
   suppress the call entirely or fail silently. The "success
   toast" simply never shows; the developer sees the function
   complete and assumes everything worked.
5. **Loses release-notes improvements for free.** When Salesforce
   updates the platform's toast styling, a11y wiring, or mobile
   rendering (e.g., Winter '24's high-contrast theme work),
   `ShowToastEvent`-based dispatches inherit the improvement
   with zero work from app teams. Bespoke banners do not.

**Correct approach:** Dispatch `ShowToastEvent` from
`lightning/platformShowToastEvent` for all transient feedback.
Reserve `lightning-alert` / `lightning-confirm` / `lightning-prompt`
for blocking modal dialogs that require an explicit user
acknowledgment before the workflow continues. For LWR Experience
Cloud sites (where `ShowToastEvent` is silently ignored), use the
`lightning/toast` `show()` static method instead — it covers the
LWR case the event-based API doesn't reach. Never reach for
`window.alert()` or a hand-rolled banner in a new LWC; the only
acceptable use of either is in a Visualforce-hosted LWC where the
host page genuinely cannot render the platform toast, and even
then the correct fix is usually to migrate the host off
Visualforce, not to bake in a custom banner.
