# LWC Toast And Notifications — Work Template

Use this template when implementing or reviewing notification patterns in a LWC component.

## Scope

**Skill:** `lwc-toast-and-notifications`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answer the Before Starting questions from SKILL.md before proceeding.

- **Container:** [ ] Lightning record/app page  [ ] Aura Experience Cloud site  [ ] LWR site  [ ] Flow screen  [ ] Screen/headless quick action  [ ] Other
- **Bundle facts (read from `.js-meta.xml` before choosing a module):** `apiVersion` = ______ ; `<target>` entries = ______________
- **Interaction type:** [ ] Non-blocking feedback (toast)  [ ] Mandatory acknowledgment (`lightning/alert`)  [ ] Binary decision gate (`lightning/confirm`)  [ ] Value needed (`lightning/prompt`)  [ ] Inline message  [ ] Custom notification from Apex (recipient not on the page)
- **Action reversibility:** [ ] Reversible  [ ] Irreversible — requires confirmation guard

## Pattern Choice

| Option | Choose? | Why |
|---|---|---|
| `lightning/toast` — the preferred module, API 59.0+, works in LWR sites | | |
| `ShowToastEvent` — API 45.0+, silent in LWR sites and Aura-site login pages | | |
| `lightning/alert` (acknowledgment) | | |
| `lightning/confirm` (destructive guard) | | |
| `lightning/prompt` (value needed) | | |
| Inline message on the page | | |
| `Messaging.CustomNotification` from Apex (recipient is elsewhere) | | |
| `LightningModal` — see `lwc-modal-and-overlay` | | |

## Implementation Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Module choice matches the declared targets — no `lightning/platformShowToastEvent` in a bundle exposed to `lightningCommunity__*`
- [ ] `apiVersion` >= 59.0 if the bundle imports `lightning/toast`
- [ ] Every `variant` / `mode` literal checked against the Component Library specification (the Developer Guide does not print the value lists)
- [ ] Destructive actions await `LightningConfirm.open()` and return early on `false`
- [ ] No `window.alert` / `window.confirm` / `window.prompt` in the bundle
- [ ] One notification per user operation, not one per record (the container caps the page at three)
- [ ] Jest asserts the dispatched event's `detail`, and a human has seen it render in each container
- [ ] Apex sends set a target, chunk recipients at 500, and truncate title/body at 250/750
- [ ] `python3 scripts/check_lwc_toast_and_notifications.py --manifest-dir <src>` reports no ERROR

## Notification Implementation

Start from `references/code-examples.md` § 1–§ 3 rather than retyping this. The sketch below marks
what is grounded in the Lightning Web Components Developer Guide and what is not.

```javascript
// [componentName].js
import { LightningElement } from 'lwc';
import Toast from 'lightning/toast';                  // preferred; API 59.0+
import LightningConfirm from 'lightning/confirm';     // API 54.0+
// import { ShowToastEvent } from 'lightning/platformShowToastEvent';  // only below API 59.0

export default class [ComponentName] extends LightningElement {

    // SUCCESS — `label` is the required title for lightning/toast; `message` is optional
    // (lwc_guide use-toast L10451).
    // UNVERIFIED (2026-09-05): Toast.show()'s second argument and the `variant` key are not
    // printed in the Developer Guide; they come from the Component Library specification.
    showSuccess(message) {
        Toast.show({ label: '[Action] successful', message, variant: 'success' }, this);
    }

    // FAILURE — read the server's sentence out of the error
    // (lwc_guide data-table-inline-edit L5703). Normalise once via lwc/lwc-error-boundaries.
    showFailure(error) {
        Toast.show({
            label: '[Action] failed',
            message: error?.body?.message ?? 'An unexpected error occurred.',
            variant: 'error'
        }, this);
    }

    // DESTRUCTIVE GATE — .open() returns a promise and does not block
    // (lwc_guide base-components-patterns L4769); resolves true on OK, false on Cancel
    // (use-dialog-confirm L10418). UNVERIFIED (2026-09-05): the accepted `variant` values for
    // confirm are not documented in the guide — note it names `variant` here and `theme` for
    // alert (L10404) and prompt (L10432).
    async handleDestructiveAction() {
        const confirmed = await LightningConfirm.open({
            label: 'Confirm [Action]',
            message: 'This action cannot be undone. Continue?'
        });
        if (!confirmed) {
            return;
        }
        // proceed with DML — everything that used to follow a blocking confirm() lives here
    }
}
```

## Jest Test Snippet

The grounded assertion shape reads the dispatched event's detail
(`lwc_guide unit-testing-using-jest-patterns L12630`–`L12635`). Full setup, including the
`moduleNameMapper` entries and the confirm mock, is in `references/code-examples.md` § 4.

```javascript
import { ShowToastEventName } from 'lightning/platformShowToastEvent';

const toastHandler = jest.fn();
element.addEventListener(ShowToastEventName, toastHandler);

// after triggering the action...
expect(toastHandler).toHaveBeenCalledTimes(1);
const { title, message, variant } = toastHandler.mock.calls[0][0].detail;
expect(variant).toBe('success');
```

A component built on `lightning/toast` is asserted differently — mock the module and read
`Toast.show.mock.calls[0][0]`. Either way the test proves dispatch, not display.

## Apex Custom Notification (only when the recipient is not on the page)

| Check | Value | Source |
|---|---|---|
| Title length | <= 250 characters | Apex Reference Guide L166708 |
| Body length | <= 750 characters | Apex Reference Guide L166711 |
| Recipients per `send()` | <= 500 values (UserId, AccountId, OpportunityId, GroupId, QueueId) | L166769–L166775 |
| Target | `setTargetId` or `setTargetPageRef` — `send()` throws if both are omitted | L166573 |
| Permission | Send Custom Notifications, or `send()` fails | L166593 |
| `package.xml` | Name each `CustomNotificationType` explicitly — no wildcard | Metadata API Guide L41893 |

## Notes

Record any deviations from the standard pattern and why (an org pinned below API 59, a deliberate
dummy target id, a second toast container, a `variant` or `mode` literal you verified against the
Component Library). Note every `UNVERIFIED` claim you relied on so the reviewer can check it.
