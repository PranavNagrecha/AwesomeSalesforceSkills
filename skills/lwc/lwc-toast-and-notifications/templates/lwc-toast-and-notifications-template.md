# LWC Toast And Notifications — Work Template

Use this template when implementing or reviewing notification patterns in a LWC component.

## Scope

**Skill:** `lwc-toast-and-notifications`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answer the Before Starting questions from SKILL.md before proceeding.

- **Deployment context:** [ ] Lightning Experience  [ ] Experience Cloud  [ ] Mobile  [ ] Visualforce / Other
- **Interaction type:** [ ] Non-blocking feedback (toast)  [ ] Mandatory acknowledgment (alert)  [ ] Binary decision gate (confirm)  [ ] Platform notification (Experience Cloud)
- **Action reversibility:** [ ] Reversible  [ ] Irreversible — requires confirmation guard

## Pattern Choice

| Option | Choose? | Why |
|---|---|---|
| `ShowToastEvent` `success` / `dismissable` | | |
| `ShowToastEvent` `error` / `sticky` | | |
| `ShowToastEvent` `warning` | | |
| `lightning-alert` (blocking acknowledgment) | | |
| `lightning-confirm` (destructive guard) | | |
| `platformNotificationService` (Experience Cloud) | | |
| `LightningModal` — see `lwc-modal-and-overlay` | | |

## Implementation Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Variant (`info`, `success`, `warning`, `error`) matches semantic meaning
- [ ] `sticky` mode used only for errors requiring user action
- [ ] `messageData` placeholder count matches `{n}` count in `message`
- [ ] Experience Cloud context handled with `platformNotificationService`
- [ ] Destructive actions guarded with `lightning-confirm` before DML
- [ ] Jest test asserts `ShowToastEvent` dispatch with expected parameters
- [ ] `lightning-alert` / `lightning-confirm` not used in Visualforce or unsupported contexts

## Notification Implementation

```javascript
// [componentName].js
import { LightningElement } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
// import LightningAlert from 'lightning/alert';       // uncomment if needed
// import LightningConfirm from 'lightning/confirm';   // uncomment if needed

export default class [ComponentName] extends LightningElement {

    // SUCCESS TOAST (after save, submit, send)
    showSuccessToast(message) {
        this.dispatchEvent(new ShowToastEvent({
            title: '[Action] Successful',
            message,
            variant: 'success'
            // mode: 'dismissable'  (default — do not set for success)
        }));
    }

    // ERROR TOAST (after failed Apex call)
    showErrorToast(error) {
        this.dispatchEvent(new ShowToastEvent({
            title: '[Action] Failed',
            message: error?.body?.message ?? 'An unexpected error occurred.',
            variant: 'error',
            mode: 'sticky'  // required for errors — user must acknowledge
        }));
    }

    // CONFIRM BEFORE DESTRUCTIVE ACTION
    async handleDestructiveAction() {
        const confirmed = await LightningConfirm.open({
            message: 'This action cannot be undone. Continue?',
            theme: 'warning',
            label: 'Confirm [Action]'
        });
        if (!confirmed) return;
        // proceed with DML
    }
}
```

## Jest Test Snippet

```javascript
import { ShowToastEventName } from 'lightning/platformShowToastEvent';

const toastHandler = jest.fn();
element.addEventListener(ShowToastEventName, toastHandler);

// after triggering action...
expect(toastHandler).toHaveBeenCalledTimes(1);
const { variant, mode } = toastHandler.mock.calls[0][0].detail;
expect(variant).toBe('success');  // or 'error', 'warning'
```

## Notes

Record any deviations from the standard pattern and why (e.g., Experience Cloud dual-path, custom messageData substitution, async timing accommodations in tests).
