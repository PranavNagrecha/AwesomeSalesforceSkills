# LLM Anti-Patterns — LWC Toast and Notifications

Common mistakes AI coding assistants make when generating or advising on toast messages and notification patterns in LWC.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using ShowToastEvent in Experience Cloud, then "fixing" it with a runtime branch

**What the LLM generates:**

```javascript
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

handleSave() {
    this.dispatchEvent(new ShowToastEvent({
        title: 'Success',
        message: 'Record saved.',
        variant: 'success'
    }));
}
```

…and, once told it does not work in a site, "corrects" it to an `if (this._isExperienceCloud)`
branch or to `lightning-alert`.

**Why it happens:** `ShowToastEvent` dominates LWC training data, so it is the default reach. The
second-order mistake is subtler: the model knows the failure is contextual, so it reaches for
context detection — a plausible-looking fix that adds an untested code path and still leaves the
event module in the bundle.

**Correct pattern:**

```javascript
import Toast from 'lightning/toast';

// lightning/toast is the preferred module and is supported in LWR sites
// (lwc_guide use-toast L10448, L10452; base-components-all L4651).
Toast.show({ label: 'Success', message: 'Record saved.', variant: 'success' }, this);
```

The guide's own recommendation is unconditional — "We recommend that you use lightning/toast
instead" (`lwc_guide base-components-patterns L4773`) — so there is nothing to branch on. Escalating
to `lightning-alert` is a worse fix again: an alert blocks the user for a message that did not need
acknowledging.

UNVERIFIED (2026-09-05): the second argument to `Toast.show()` and the `variant` key are not
printed in the crawled guide; they come from the lightning/toast Component Library specification.
The guide states only that `label` is required and `message` optional (`use-toast L10451`).

**Detection hint:** `lightning/platformShowToastEvent` imported in a bundle whose `.js-meta.xml`
declares any `lightningCommunity__` target. The bundled checker reports this as a WARN.

## Anti-Pattern 2: Stating toast `mode` and `variant` values as documented fact

**What the LLM generates:**

```javascript
this.dispatchEvent(new ShowToastEvent({
    title: 'Error',
    message: error.body.message,
    variant: 'error',
    mode: 'sticky'   // "sticky so the user cannot miss it"
}));
```

…usually accompanied by a confident sentence listing `dismissable` (default), `sticky`, and
`pester`, and the variants `info` (default), `success`, `warning`, `error`.

**Why it happens:** those enums are widely repeated in blog posts and sample repos, so the model
has seen them far more often than it has seen the actual reference. The Lightning Web Components
Developer Guide names `variant` and `mode` as properties (`lwc_guide use-toast L10456`) and says
its example "uses the default value for mode, so it's not included" — but it never prints the
accepted values or which is the default. Only `variant: 'success'` and `variant: 'error'` appear
anywhere in its samples (`data-table-inline-edit L5694`, `L5746`).

**Correct pattern:** use the value, and say where it came from.

```javascript
// variant 'error' appears in the guide's own samples (data-table-inline-edit L5746).
// mode: the value list lives in the platformShowToastEvent Component Library specification,
// not in the Developer Guide — check it before relying on a literal.
this.dispatchEvent(new ShowToastEvent({
    title: 'Save failed',
    message: reduceErrors(error).join('; '),
    variant: 'error'
}));
```

The design point survives the citation problem: a message the user must act on can persist; a
routine confirmation should not. Applying one mode uniformly across every toast is what dilutes
the signal.

**Detection hint:** any prose that lists toast modes or variants without naming a source, or a
`mode:` literal with no comment explaining why this message outlives the default.

## Anti-Pattern 3: Showing a toast for every successful action without user value

**What the LLM generates:**

```javascript
handleFieldChange() {
    this.dispatchEvent(new ShowToastEvent({
        title: 'Updated',
        message: 'Field value changed successfully.',
        variant: 'success'
    }));
}
```

**Why it happens:** LLMs add success toasts after every operation for "completeness." Frequent toasts for routine actions (field changes, filter selections, tab switches) create notification fatigue.

**Correct pattern:**

Show toasts only for significant state changes (record save, delete, batch completion):

```javascript
handleSave() {
    await saveRecord(this.record);
    this.dispatchEvent(new ShowToastEvent({
        title: 'Saved',
        message: 'Account updated successfully.',
        variant: 'success'
    }));
}

handleFieldChange() {
    // No toast — inline visual feedback is sufficient
    this.hasUnsavedChanges = true;
}
```

**Detection hint:** `ShowToastEvent` with `variant: 'success'` in handlers for minor interactions like change, blur, or toggle events.

---

## Anti-Pattern 4: Not extracting useful error messages from the error object

**What the LLM generates:**

```javascript
handleError(error) {
    this.dispatchEvent(new ShowToastEvent({
        title: 'Error',
        message: JSON.stringify(error), // Raw error object — unreadable
        variant: 'error'
    }));
}
```

**Why it happens:** LLMs do not know the shape of the error object at generation time, so they stringify the whole thing. This produces unreadable JSON in the toast.

**Correct pattern:**

```javascript
// Utility function to extract meaningful messages
reduceErrors(error) {
    if (Array.isArray(error.body)) {
        return error.body.map(e => e.message);
    }
    if (error.body?.message) {
        return [error.body.message];
    }
    if (typeof error.message === 'string') {
        return [error.message];
    }
    return ['Unknown error'];
}

handleError(error) {
    this.dispatchEvent(new ShowToastEvent({
        title: 'Error',
        message: this.reduceErrors(error).join('; '),
        variant: 'error'
    }));
}
```

**Detection hint:** `JSON.stringify(error)` or `error.toString()` passed as the toast message.

---

## Anti-Pattern 5: Confusing lightning-alert / lightning-confirm with ShowToastEvent

**What the LLM generates:**

```javascript
import LightningAlert from 'lightning/alert';

// Uses alert for a success notification — blocks the user unnecessarily
await LightningAlert.open({
    message: 'Record saved successfully.',
    label: 'Success',
    theme: 'success'
});
```

**Why it happens:** LLMs know both APIs exist and sometimes swap them. Alerts block the user until dismissed — they should not be used for routine success messages.

**Correct pattern:**

- **Toast** for non-blocking, transient feedback (success, info, minor errors)
- **Alert** for important messages that require explicit acknowledgment
- **Confirm** for yes/no decisions before destructive actions

```javascript
// Success: use toast (non-blocking)
this.dispatchEvent(new ShowToastEvent({
    title: 'Success', message: 'Record saved.', variant: 'success'
}));

// Destructive confirmation: use confirm (blocking)
const proceed = await LightningConfirm.open({
    message: 'Delete this record?', label: 'Confirm', theme: 'warning'
});
```

**Detection hint:** `LightningAlert.open` with `theme: 'success'` for routine success feedback.

---

## Anti-Pattern 6: Explaining a missing toast with an invented propagation rule

**What the LLM generates:**

```javascript
// Deep nested child component
this.dispatchEvent(new ShowToastEvent({
    title: 'Error', message: 'Validation failed', variant: 'error'
}));
// "Toast never appears — ShowToastEvent has bubbles: false, so it can't reach the app container"
```

**Why it happens:** the model knows one real rule — a plain `CustomEvent` defaults to
`bubbles: false` and does not cross the shadow boundary (`lwc_guide events-propagation L5119`,
`L5125`) — and applies it to `ShowToastEvent`, which is not a plain `CustomEvent` the developer
configures. The crawled Developer Guide never states `ShowToastEvent`'s own `bubbles` or
`composed` configuration, and its samples dispatch it from ordinary components, including from a
headless quick action (`lwc_guide use-quick-actions-headless L10615`). The explanation is fluent,
specific, and unsupported — and it sends the reader to restructure their component tree instead of
to the real cause, which is almost always the container (Gotcha 1).

**Correct pattern:** diagnose the container first, then propagation.

```javascript
// 1. What does the bundle's .js-meta.xml declare? A lightningCommunity__ target with the event
//    module is a silent no-op (lwc_guide use-toast L10449) — no propagation theory needed.
// 2. Is the page already showing its maximum toasts? The container queues the extra
//    (lwc_guide use-toast L10464).
// 3. Only then consider re-dispatching from a parent, and say so as a hypothesis, not a rule.
this.dispatchEvent(new CustomEvent('showerror', {
    detail: { message: 'Validation failed' },
    bubbles: true, composed: true
}));
```

UNVERIFIED (2026-09-05): whether `ShowToastEvent` bubbles and crosses shadow boundaries is not
documented in the crawled guide. Do not assert either answer; test it in the target container.

**Detection hint:** any explanation of an invisible toast that names `bubbles`, `composed`, or
"the app container" without first naming the bundle's targets.

## Anti-Pattern: Inventing `lightning/platformNotificationService` for Experience Cloud toasts

**What the LLM generates:**

```javascript
import { ShowNotification } from 'lightning/platformNotificationService';
// or
import { NotificationsLibrary } from 'lightning/platformNotificationService';
```

…usually attached to a *correct* diagnosis ("`ShowToastEvent` doesn't render in Experience Cloud, so use the platform notification service instead").

**Why it happens:** The mechanism is real and the model knows it, so it confabulates a module name to fit. Three real things get blended: (1) the Aura component `lightning:notificationsLibrary`, which is Aura-only and has no LWC equivalent; (2) the *custom notification* feature (Notification Builder / Send Custom Notification action), which is server-side automation and unrelated to in-page toasts; (3) the genuine `lightning/platform*` module family (`lightning/platformShowToastEvent`, `lightning/platformResourceLoader`), whose naming convention makes `lightning/platformNotificationService` look plausible. No such module exists and no `ShowNotification` export exists anywhere in the LWC platform module set, so the import fails at compile time.

**Correct version:**

```javascript
import Toast from 'lightning/toast';

Toast.show({ label: 'Saved', message: 'Record updated.', variant: 'success', mode: 'dismissible' }, this);
```

`Toast.show(config, component)` — the second argument is the component reference and is required. Add `lightning-toast-container` (`lightning/toastContainer`) in LWR sites to control placement. Salesforce's Toast Notifications page states `lightning/platformShowToastEvent` "isn't supported on login pages in Aura sites, LWR sites for Experience Cloud, and standalone apps" and recommends `lightning/toast` instead.

**Detection hint:** grep for `platformNotificationService`, `ShowNotification`, or `NotificationsLibrary` in any `.js` file or LWC guidance — zero of the three is a real LWC module or export. More generally: any `lightning/…` import whose module name is not in the documented Salesforce module list. Second hint: `Toast.show(` called with one argument — the missing component reference is the most common real-API mistake once the module name is right.
