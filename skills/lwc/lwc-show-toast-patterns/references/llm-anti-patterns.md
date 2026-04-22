# LLM Anti-Patterns — LWC Show Toast Patterns

Common mistakes AI coding assistants make with `ShowToastEvent`.

## Anti-Pattern 1: ShowToastEvent in LWR Experience Cloud

**What the LLM generates:** `ShowToastEvent` dispatch in a component targeting an LWR site.

**Why it happens:** Model doesn't distinguish LWR from Aura sites.

**Correct pattern:**

```
LWR silently ignores ShowToastEvent. Use one of:

- <lightning-alert> — blocking modal dialog
- <lightning-confirm> — blocking yes/no dialog
- Custom banner with SLDS notification classes:

<template if:true={isShown}>
    <div class="slds-notify slds-notify_toast slds-theme_success" role="alert">
        <h2>{message}</h2>
    </div>
</template>

Check runtime via import { formFactor } from '@salesforce/client/formFactor'
when a component ships to both LEX and LWR.
```

**Detection hint:** `ShowToastEvent` dispatched from a component used in an LWR `<community>` experience.

---

## Anti-Pattern 2: `pester` mode with non-error variant

**What the LLM generates:**

```
new ShowToastEvent({ variant: 'success', mode: 'pester' })
```

**Why it happens:** Model uses mode + variant independently.

**Correct pattern:**

```
pester mode is documented to work only with variant: 'error'.
For persistent success/info/warning toasts, use mode: 'sticky'.

Using pester with other variants silently degrades to dismissible
(auto-hides after ~3 seconds), which is likely not the intent.
```

**Detection hint:** `mode: 'pester'` paired with `variant` other than `'error'`.

---

## Anti-Pattern 3: Errors as dismissible toasts

**What the LLM generates:**

```
new ShowToastEvent({
    title: 'Save Failed',
    message: err.body.message,
    variant: 'error'
    // no mode → defaults to dismissible, gone in 3 seconds
})
```

**Why it happens:** Model uses defaults.

**Correct pattern:**

```
Errors need user acknowledgment. Always pair error variant with
sticky or pester:

new ShowToastEvent({
    variant: 'error',
    mode: 'sticky',
    title: 'Save Failed',
    message: err.body.message
});

Users miss 3-second error toasts — they click away, data doesn't
save, next support ticket is unavoidable.
```

**Detection hint:** `variant: 'error'` without an explicit `mode` or with `mode: 'dismissible'`.

---

## Anti-Pattern 4: Concatenating URLs into the message string

**What the LLM generates:**

```
message: 'View <a href="/lightning/r/Account/' + id + '/view">here</a>'
```

**Why it happens:** Model applies web-app patterns.

**Correct pattern:**

```
The message param is plain text — HTML is escaped. Use messageData
for interpolation + links:

{
    message: 'View {0}',
    messageData: [
        { url: '/lightning/r/Account/' + id + '/view', label: 'Account' }
    ]
}

LWC renders the {url, label} object as a proper anchor with
accessibility + security handled.
```

**Detection hint:** `message` field containing HTML tags or raw URLs.

---

## Anti-Pattern 5: Dispatching a toast in `connectedCallback` for feedback on an async load

**What the LLM generates:**

```
connectedCallback() {
    getData().then(d => {
        this.dispatchEvent(new ShowToastEvent({ message: 'Loaded' }));
    });
}
```

**Why it happens:** Model combines lifecycle + feedback.

**Correct pattern:**

```
Dispatching during component init often fires before the toast
container is ready, and the toast is lost. Also, toasts for
routine loads are noise — users haven't asked for feedback.

Restrict toasts to user-initiated actions:
- After clicking Save → success toast
- After clicking Delete → success toast
- On handler's catch block → error toast

Passive loads should show a spinner/skeleton, not a toast.
```

**Detection hint:** `ShowToastEvent` dispatched inside `connectedCallback`, `renderedCallback`, or a `@wire` error channel with no user action.
