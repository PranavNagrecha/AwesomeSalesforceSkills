# Gotchas — LWC Toast And Notifications

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Toast Events Are Silent in Experience Cloud

**What happens:** A component dispatches `ShowToastEvent` and no toast appears on screen. No JavaScript error is thrown. The event fires and disappears without any visible feedback to the user.

**When it occurs:** When the LWC component is deployed inside an Experience Cloud (formerly Community Cloud) site. The toast event propagates up the DOM looking for the Lightning page host that renders toast notifications. That host is not present in Experience Cloud, so the event is consumed silently.

**How to avoid:** For components that must run in Experience Cloud, use the `NotificationsLibrary` or `ShowNotification` from `lightning/platformNotificationService`. If the same component must work in both Lightning Experience and Experience Cloud, detect the deployment context at runtime using `@salesforce/client/formFactor` or check the URL origin, and dispatch the appropriate notification primitive. Document the deployment target constraint in the component's header comment.

---

## Gotcha 2: sticky Mode on Success Toasts Creates Hostile UX

**What happens:** Users must manually close every success confirmation by clicking the X button, even for routine save operations that require no further action. On high-frequency workflows, this becomes friction that accumulates across every save.

**When it occurs:** When `mode: 'sticky'` is applied indiscriminately to all toast variants rather than selectively to `error` or `warning` messages. This often happens when a developer uses `sticky` for an error early in development and then copies the pattern to all subsequent toasts without reconsidering it.

**How to avoid:** Use `mode: 'sticky'` only for `error` and `warning` toasts where the user must see and acknowledge the message before proceeding. Use the default `dismissable` mode (or `pester` for brief purely-informational messages) for `success` and `info` toasts. Establish a team convention: `sticky` requires justification in a code comment.

---

## Gotcha 3: messageData Placeholder Mismatch Renders Raw Template Text

**What happens:** The toast body displays literal strings like `{0}` or `{1}` to the end user instead of the substituted value.

**When it occurs:** When the `messageData` array has fewer entries than the number of `{n}` placeholders in the `message` string, or when `messageData` is omitted entirely while `message` still contains placeholder tokens. A common cause is refactoring `message` to add a new placeholder without updating `messageData`.

**How to avoid:** Treat placeholder count as a compile-time constraint: count the `{n}` tokens in `message` and ensure `messageData.length` equals that count. The checker script at `scripts/check_lwc_toasts.py` in this skill package flags this pattern statically. Consider a utility wrapper that validates the array length before dispatch in development builds.

---

## Gotcha 4: lightning-alert and lightning-confirm Are Unsupported Outside Lightning Experience

**What happens:** `LightningAlert.open()` or `LightningConfirm.open()` throw a runtime error, produce no UI, or return unexpected values when called inside Visualforce pages, standalone LWC apps, or embedded iframes that are not part of the Lightning framework.

**When it occurs:** When a component originally built for Lightning Experience is later reused in a Visualforce page wrapper, a utility bar, or a Lightning Out context that does not fully support the `lightning/alert` and `lightning/confirm` modules.

**How to avoid:** Before using `lightning-alert` or `lightning-confirm`, confirm that the component is only deployed to supported Lightning contexts. Document the constraint in the component metadata. If cross-context support is required, fall back to a lightweight `LightningModal`-based confirm pattern (see `lwc/lwc-modal-and-overlay`) that works in more contexts.
