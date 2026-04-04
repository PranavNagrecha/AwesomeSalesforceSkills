---
name: lwc-toast-and-notifications
description: "Use when implementing or reviewing user feedback patterns in Lightning Web Components — specifically toast messages, lightning-alert, lightning-confirm, lightning-prompt, and platform notifications. Trigger keywords: 'ShowToastEvent', 'toast in lwc', 'lightning-alert lwc', 'lightning-confirm promise', 'Experience Cloud notification'. NOT for modal overlays (use lwc-modal-and-overlay)."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
tags:
  - lwc
  - toast
  - notifications
  - ShowToastEvent
  - lightning-alert
  - lightning-confirm
  - platform-notifications
inputs:
  - "what user action or system event triggered the need for feedback"
  - "whether the feedback requires user acknowledgment or is purely informational"
  - "whether the component runs in Lightning Experience, Experience Cloud, or a mobile context"
outputs:
  - "implementation of the correct notification primitive for the scenario"
  - "review findings for toast misuse, sticky-mode overuse, and Experience Cloud gaps"
  - "Jest test pattern for verifying toast dispatch"
triggers:
  - "how do I show a toast message in LWC"
  - "ShowToastEvent not showing in Experience Cloud"
  - "lightning-confirm promise-based dialog LWC"
  - "display success error warning notification LWC"
  - "sticky toast vs dismissable toast when to use"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

Use this skill when a component needs to communicate feedback, status, or a decision prompt to the user and the team must choose the right platform primitive. Toast is the default for non-blocking success, warning, and error messages in Lightning Experience; `lightning-alert` and `lightning-confirm` replace browser-native dialogs with promise-based equivalents; platform notifications handle Experience Cloud contexts where toast is invisible.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the component running in Lightning Experience, Experience Cloud, a mobile app, or an embedded Visualforce page? Toast does not render in Experience Cloud or Visualforce contexts.
- Does the user need to acknowledge the message (blocking) or just be informed (non-blocking)? That choice drives the primitive selection.
- Is the action irreversible? Confirm dialogs are appropriate before destructive operations; toast is not.

---

## Core Concepts

Notification design in LWC centers on matching the interruption level of the primitive to the weight of the event. The platform provides four distinct primitives, and picking the wrong one degrades the experience even when the technical implementation is correct.

### ShowToastEvent and the Toast Contract

`ShowToastEvent` is imported from `lightning/platformShowToastEvent` and fired as a custom event on the component:

```javascript
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

// inside a handler:
this.dispatchEvent(
    new ShowToastEvent({
        title: 'Record Saved',
        message: 'The account was updated successfully.',
        variant: 'success',
        mode: 'dismissable'
    })
);
```

**Parameters:**

| Parameter | Required | Values / Notes |
|---|---|---|
| `title` | Yes | Short heading displayed in bold |
| `message` | No | Body text; supports `{0}`, `{1}` placeholders when `messageData` is provided |
| `variant` | No | `info` (default), `success`, `warning`, `error` |
| `mode` | No | `dismissable` (default), `sticky`, `pester` |
| `messageData` | No | Array of strings or link objects for placeholder substitution in `message` |

**Variants map directly to semantic intent:**

- `info` — neutral informational update
- `success` — completed action (save, approval, send)
- `warning` — non-fatal issue requiring attention
- `error` — operation failed; pair with `sticky` or `pester` so the user cannot miss it

**Modes control dismissal behavior:**

- `dismissable` — the user can click the X to close; auto-closes after a platform-controlled timeout
- `sticky` — persists until the user explicitly closes it; appropriate for errors the user must act on
- `pester` — cannot be closed; disappears on its own after a fixed timeout

**`messageData` for link substitution:**

```javascript
this.dispatchEvent(
    new ShowToastEvent({
        title: 'Related Record Created',
        message: 'A case was opened: {0}. View it {1}.',
        messageData: [
            '00001234',
            {
                url: '/lightning/r/Case/500xx000000XXXX/view',
                label: 'here'
            }
        ],
        variant: 'success'
    })
);
```

The `messageData` array must contain exactly as many entries as there are `{n}` placeholders in `message`. A mismatch causes the placeholder text to render literally.

### lightning-alert — Promise-Based Acknowledgment

`lightning-alert` is an inline LWC component that replaces the browser `window.alert()` native dialog. It returns a promise that resolves when the user dismisses it, making control flow explicit:

```javascript
import LightningAlert from 'lightning/alert';

async handleAlertClick() {
    await LightningAlert.open({
        message: 'You must complete required fields before proceeding.',
        theme: 'error',
        label: 'Action Required'
    });
    // execution resumes here after dismissal
}
```

**Parameters:**

| Parameter | Required | Notes |
|---|---|---|
| `message` | Yes | Dialog body text |
| `label` | Yes | Accessible dialog heading (used as `aria-label`) |
| `theme` | No | `default`, `shade`, `inverse`, `alt-inverse`, `success`, `info`, `warning`, `error`, `offline` |

`lightning-alert` is supported in Lightning Experience. It is not supported in Visualforce or standalone HTML pages.

### lightning-confirm — Promise-Based Boolean Decision

`lightning-confirm` prompts the user to confirm or cancel and resolves to `true` (confirmed) or `false` (cancelled):

```javascript
import LightningConfirm from 'lightning/confirm';

async handleDelete() {
    const confirmed = await LightningConfirm.open({
        message: 'Deleting this record is permanent and cannot be undone.',
        theme: 'warning',
        label: 'Delete Record'
    });
    if (confirmed) {
        await deleteRecord(this.recordId);
    }
}
```

`lightning-confirm` is the correct replacement for the browser `window.confirm()` call inside LWC. It shares the same parameter shape as `lightning-alert`.

### Platform Notifications for Experience Cloud

Toast dispatched from a LWC component is caught and rendered by the Lightning page host. In Experience Cloud (formerly Community Cloud) that host is absent, so toast events bubble up and disappear silently. The correct alternative is the `NotificationsLibrary` wire service from `lightning/platformNotificationService`, which works across Experience Cloud contexts:

```javascript
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
// NOT suitable in Experience Cloud — use below instead

import { ShowNotification } from 'lightning/platformNotificationService';
// available in Experience Cloud builders
```

For components that must work in both contexts, detect the current context via the `@salesforce/client/formFactor` import or use a feature detection pattern, and dispatch the appropriate notification.

---

## Common Patterns

### Toast After Apex DML

**When to use:** A component calls an Apex method to save, update, or delete a record and needs to confirm the outcome to the user without interrupting navigation.

**How it works:** In the `.then()` handler (or in an `async/await` success branch) dispatch a `success` variant toast. In the catch block dispatch an `error` variant toast with `mode: 'sticky'` so the user cannot miss the failure.

**Why not the alternative:** Using `window.alert()` inside LWC is explicitly disallowed by the Locker Service and breaks in Lightning Experience. `lightning-alert` is appropriate for mandatory-read blocking messages, but a simple save confirmation does not need to block the user.

### Confirm Before Destructive Action

**When to use:** The user initiates a delete, archive, or bulk overwrite operation that cannot be reversed.

**How it works:** Open `LightningConfirm` before the Apex call and only proceed if the promise resolves `true`. This pattern makes the gate explicit in code and eliminates the need for manual DOM manipulation or a full `LightningModal` for a single yes/no decision.

**Why not the alternative:** Skipping confirmation for destructive actions is a data integrity risk. Using a full `LightningModal` is heavier than needed for a single-question decision.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Confirm save succeeded | `ShowToastEvent` with `variant: 'success'` | Non-blocking; user stays in context |
| Notify user of non-fatal validation issue | `ShowToastEvent` with `variant: 'warning'` | Visible but not blocking |
| Notify user of a recoverable error | `ShowToastEvent` with `variant: 'error', mode: 'sticky'` | Error must persist until the user acts |
| Require acknowledgment before proceeding | `lightning-alert` | Promise resolves after dismissal; explicit control flow |
| Confirm an irreversible destructive action | `lightning-confirm` | Returns boolean; simpler than a full modal |
| Component runs in Experience Cloud | `NotificationsLibrary` / `platformNotificationService` | Toast is invisible outside Lightning page host |
| Complex multi-step confirmation with form fields | `LightningModal` (see `lwc-modal-and-overlay`) | Notification primitives are not form containers |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The correct variant (`info`, `success`, `warning`, `error`) matches the semantic meaning of the event.
- [ ] `sticky` mode is used only for errors that require user action, not for routine success confirmations.
- [ ] `messageData` placeholder count matches the `{n}` count in `message`.
- [ ] Components deployed to Experience Cloud use `platformNotificationService`, not `ShowToastEvent`.
- [ ] Destructive actions are guarded with `lightning-confirm` before the DML call.
- [ ] Jest tests assert that `ShowToastEvent` was dispatched with the correct parameters.
- [ ] `lightning-alert` and `lightning-confirm` are not used in Visualforce or standalone HTML contexts.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Toast is silent in Experience Cloud** — `ShowToastEvent` bubbles to the Lightning page host. In Experience Cloud that host is absent, so the event fires without rendering. Teams discover this in QA after deploying to a community. Use `platformNotificationService` instead.
2. **`sticky` mode on success toasts is hostile UX** — it requires the user to manually dismiss a non-critical message. Reserve `sticky` for `error` or `warning` variants where the user must acknowledge a problem.
3. **`messageData` placeholder mismatch renders raw template text** — if `message` contains `{0}` but `messageData` is an empty array or contains fewer items, the literal string `{0}` appears to end users. Always validate array length against placeholder count.
4. **`lightning-alert` and `lightning-confirm` are unsupported outside Lightning Experience** — they are not available in Visualforce, standalone pages, or some embedded app contexts. Feature-detect or document the deployment target before choosing these primitives.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Notification implementation | JavaScript handler using the correct primitive for the scenario |
| Review findings | Issues in variant choice, sticky-mode overuse, and Experience Cloud gaps |
| Jest test pattern | Test verifying toast dispatch with expected parameters |

---

## Related Skills

- `lwc/lwc-modal-and-overlay` — use when the interaction requires a dedicated task container, form input, or a complex result-returning dialog rather than a single-line notification.
- `lwc/lwc-testing` — use alongside this skill when verifying toast dispatch in Jest unit tests.
- `lwc/lifecycle-hooks` — use when notification timing issues are really rerender or async sequencing problems.
