---
name: lwc-show-toast-patterns
description: "ShowToastEvent in LWC: variants (success/warning/error/info), modes (dismissible/pester/sticky), message formatting, NOT supported in LWR Experience Cloud sites, alternatives (lightning-alert, inline banners). NOT for custom notification types (use admin/custom-notification-types). NOT for SLDS popovers."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Reliability
tags:
  - lwc
  - showtoastevent
  - toast
  - lightning-platform-show-toast-event
triggers:
  - "showtoastevent lwc variant mode sticky"
  - "lwc toast not showing experience cloud lwr"
  - "dismissible pester sticky toast mode"
  - "format toast message with link url clickable"
  - "lightning alert vs showtoastevent choose"
  - "toast event on desktop but not on mobile"
inputs:
  - Feedback intent (confirmation, warning, error, info)
  - Context (Lightning Experience, LWR, Mobile)
  - Dismiss behavior needed
outputs:
  - Dispatch code with correct variant + mode
  - Fallback plan for LWR sites
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-22
---

# LWC ShowToast Patterns

Activate when surfacing user feedback in LWC. `ShowToastEvent` (from `lightning/platformShowToastEvent`) is the idiomatic toast API in Lightning Experience and Experience Cloud Aura sites — but **NOT supported in LWR (Lightning Web Runtime) sites**. Pick the right tool per context.

## Before Starting

- **Determine runtime.** Lightning Experience / mobile Salesforce app / Aura Experience Cloud → ShowToastEvent works. LWR → NOT supported, use alternatives.
- **Pick the variant.** `success` / `warning` / `error` / `info` — each has distinct styling.
- **Pick the mode.** `dismissible` (default, 3s auto), `pester` (stays until dismissed, errors only), `sticky` (stays until dismissed).

## Core Concepts

### Basic dispatch

```
import { LightningElement } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

export default class MyCmp extends LightningElement {
    notify() {
        this.dispatchEvent(new ShowToastEvent({
            title: 'Saved',
            message: 'Record updated successfully',
            variant: 'success',
            mode: 'dismissible'
        }));
    }
}
```

### Variants

| Variant | When to use |
|---|---|
| `success` | Confirmation of successful action |
| `warning` | Non-blocking caution |
| `error` | Failure requiring attention |
| `info` | Neutral status |

### Modes

| Mode | Behavior |
|---|---|
| `dismissible` (default) | Auto-dismisses after ~3 seconds; user can close |
| `pester` | Stays until user dismisses (only valid for `error` variant) |
| `sticky` | Stays until user dismisses |

### Message placeholders and links

```
this.dispatchEvent(new ShowToastEvent({
    title: 'Record Saved',
    message: 'See {0}',
    messageData: [
        { url: '/lightning/r/Account/0012x.../view', label: 'Acme' }
    ],
    variant: 'success'
}));
```

`{0}` is replaced by the object at index 0 — either plain text or `{url, label}` for a link.

### LWR Experience Cloud caveat

ShowToastEvent is silently ignored on LWR sites. Alternatives:

- `lightning-alert` / `lightning-confirm` modals
- Inline banner component using `lightning-icon` + SLDS notification classes
- Custom toast implementation with `lightning-layout` + CSS animation

## Common Patterns

### Pattern: Error toast with sticky mode

```
this.dispatchEvent(new ShowToastEvent({
    title: 'Save failed',
    message: error.body.message,
    variant: 'error',
    mode: 'sticky'
}));
```

### Pattern: Link-in-message toast

```
this.dispatchEvent(new ShowToastEvent({
    title: 'Record Created',
    message: 'View {0}',
    messageData: [
        { url: `/lightning/r/Account/${recordId}/view`, label: accountName }
    ],
    variant: 'success'
}));
```

### Pattern: LWR-compatible fallback

```
// lwrToast.js — a custom banner component
@api message;
@api variant;
isShown = false;
show() { this.isShown = true; setTimeout(() => this.isShown = false, 3000); }
```

## Decision Guidance

| Context | Feedback mechanism |
|---|---|
| Lightning Experience | `ShowToastEvent` |
| Mobile Salesforce app | `ShowToastEvent` |
| Aura Experience Cloud site | `ShowToastEvent` |
| LWR Experience Cloud site | Custom banner, `lightning-alert`, or inline component |
| Blocking confirmation needed | `lightning-confirm` (not a toast) |
| Rich content / interactive | `LightningModal` (not a toast) |

## Recommended Workflow

1. Confirm target runtime (Lightning vs LWR) before writing.
2. Dispatch `ShowToastEvent` with explicit `variant` and `mode`.
3. For errors, use `sticky` or `pester` so users can read.
4. For cross-runtime components, check `@salesforce/client/formFactor` and fall back to a banner in LWR.
5. Test toasts in the actual runtime, not just LEX (LWR renders differently).
6. For accessibility, keep toast messages ≤75 characters so screen readers announce cleanly.
7. Document that LWR does not render toasts — downstream teams must be warned.

## Review Checklist

- [ ] Target runtime verified (LWR alternatives used where needed)
- [ ] Variant matches semantic intent
- [ ] Error variants use `sticky` or `pester` (not `dismissible`)
- [ ] Message kept short for accessibility
- [ ] Link-in-message uses `messageData` placeholders
- [ ] Fallback implemented for LWR sites

## Salesforce-Specific Gotchas

1. **LWR Experience Cloud silently swallows `ShowToastEvent`** — no console warning, just no toast. Use `lightning-alert` or a custom banner.
2. **`pester` mode is only valid for `variant='error'`.** With other variants it falls back to `dismissible`.
3. **Toasts dispatched before the component is fully rendered may be lost.** Use `renderedCallback` or defer to after async work completes.
4. **Custom toast styling is not supported.** `slds-notify_toast` classes apply to the built-in component, not reproducible outside the framework.

## Output Artifacts

| Artifact | Description |
|---|---|
| Toast dispatch helper | Utility wrapping `ShowToastEvent` with defaults |
| LWR fallback component | Banner for Experience Cloud LWR |
| Accessibility snippet | Short message + role='alert' pattern |

## Related Skills

- `lwc/lwc-lightning-modal` — when blocking user attention is required
- `lwc/lwc-accessibility-patterns` — semantic feedback patterns
- `admin/custom-notification-types` — for async/server-side notifications
