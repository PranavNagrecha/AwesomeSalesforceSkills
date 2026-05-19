# Well-Architected Notes — LWC ShowToast Patterns

## Relevant Pillars

Toast notifications look like a UX detail, but the architectural
weight comes from how the platform's event-based primitive
enforces consistency, accessibility, and runtime portability that
hand-rolled banners and `window.alert()` calls do not. Three
pillars carry weight; the dominant one is Accessibility because
the platform's `aria-live` wiring, focus behavior, and dismiss
controls are the difference between "screen-reader users hear the
confirmation" and "screen-reader users hear nothing."

- **Accessibility (a sub-concern of Reliability + User Experience)** —
  The Lightning Experience platform manages a single
  `aria-live` region per page into which all `ShowToastEvent`
  dispatches land. Screen readers announce the toast's title and
  message through that region with the correct politeness level
  (polite for `info` / `success`, assertive for `warning` /
  `error`). The close (X) button is keyboard-reachable and
  appropriately labeled. Hand-rolled banners reimplement these
  WCAG 4.1.2 (Name, Role, Value), 2.4.3 (Focus Order), and
  3.3.1 (Error Identification) requirements per-component, and
  almost always get at least one wrong on the first cut.
  `messageData`-substituted links carry the platform's `<a>`
  rendering with focus-visible styling and SLDS link colors —
  hand-rolled string concatenation does not.
- **User Experience (Operational Excellence)** — Standardizing on
  `ShowToastEvent` across an org means one toast position, one
  dismiss behavior, one set of variant icons, and one stack
  behavior when multiple toasts fire in close succession. Two
  hand-rolled banners from two LWCs on the same page collide
  with no z-index coordination, dismiss on different timers, and
  render with inconsistent SLDS styling depending on which team
  wrote which. The platform's toast container provides a single
  audit surface — one place to fix a regression, one set of
  visuals to QA.
- **Reliability** — Errors must be visible long enough to read.
  Using `mode: 'sticky'` for the `'error'` variant means a
  validation message stays on screen until the user explicitly
  dismisses it, rather than evaporating at 5 seconds when the
  user is mid-read. The default `'dismissible'` mode is correct
  for confirmations ("Saved"); for any error message, sticky is
  the default that reduces support tickets. The runtime portability
  story matters too: dispatching from `connectedCallback` before
  the component is in the DOM means the toast silently vanishes
  — feedback the user never sees IS unreliable, even though the
  code "succeeded."

## Architectural Tradeoffs

The defining tradeoff is **which feedback primitive to use**,
since Salesforce ships several overlapping mechanisms with
different blocking semantics, return-value semantics, and
runtime support:

| Dimension | `ShowToastEvent` (`lightning/platformShowToastEvent`) | `lightning-modal` | `lightning-prompt` (within `lightning-modal`) | Inline `<lightning-input-field>` error | `lightning/empApi` push toast |
|---|---|---|---|---|---|
| Blocking | No (transient overlay) | Yes (modal blocks page) | Yes (modal with text input) | No (inline next to field) | No (asynchronous push) |
| User must acknowledge | No (auto-dismiss in `dismissible`/`pester`) | Yes (button or X) | Yes (typed answer) | No | Depends |
| Return value to caller | None | `Promise<value>` from `Modal.open()` | `Promise<string>` (typed input) | N/A (validation in form) | N/A (server-pushed) |
| Runtime support | LEX + Aura Experience Cloud (NOT LWR/standalone) | LEX + Experience Cloud | LEX + Experience Cloud | All LWC surfaces | LEX + supporting clients |
| Best for | Transient success/info/warning feedback after an action | "Are you sure?" confirmations that block until answered | Asking for a single string value | Field-level validation errors during data entry | Background events from server (record updates, alerts) |
| Worst for | Errors the user must read carefully (use `sticky` mode, or escalate to modal) | Brief success confirmations | Anything more complex than a single typed string | Cross-record or async errors | Synchronous user feedback right after a button click |

The handoff rule that works in practice: **use `ShowToastEvent`
for any transient feedback after a user-initiated action where the
user doesn't need to acknowledge anything to proceed. Escalate to
`lightning-modal` (with `lightning-confirm`/`lightning-prompt`
inside) when the workflow needs an explicit Yes/No answer before
continuing. Use inline form errors for validation that fires
during data entry — toast is the wrong primitive for "this field
must be a number." Use `lightning/empApi` push-then-toast when
the trigger is server-side and a user happens to be on the page;
the toast is the surface, but the primitive is the platform
event subscription.**

A second tradeoff: **`ShowToastEvent` vs `lightning/toast.show()`**.
The event-based API is the legacy LEX/Aura primitive; the static
`Toast.show()` from `lightning/toast` is the modern alternative
that also works in LWR Experience Cloud and standalone LWC apps
where the event-based API is silently ignored. For components that
ship to both LEX and LWR, prefer `lightning/toast.show()` —
shorter migration path, broader runtime coverage. For components
that only run in LEX (the majority of internal-org work), either
choice works; teams already standardized on `ShowToastEvent`
should not migrate without reason. The two APIs surface
near-identical capabilities (`label`/`title`, `message`, `variant`,
`mode`), so the switch is mechanical.

A third tradeoff: **`messageData` link substitution vs `dispatchEvent`
+ `NavigationMixin.Navigate`**. The link-in-toast pattern lets the
user click a generated URL inline ("Record saved. View {0}"). The
alternative is to fire a toast saying "Record saved" and immediately
call `NavigationMixin.Navigate` to push the user to the new record.
The first is non-blocking — the user reads the toast, chooses
whether to click. The second is auto-navigation — the user has no
choice. For workflows where the new record is a side-effect (created
in passing while the user's main task continues), prefer the link
pattern. For workflows where the new record is the *destination*
(create-and-view), prefer the navigate pattern. Combining both
(navigate + toast) is acceptable but the toast becomes redundant
if the user lands on the destination page immediately.

## Anti-Patterns

1. **Using `window.alert()` for transient feedback.** Blocks the
   browser tab, renders as a native OS dialog with no LEX styling,
   may be suppressed entirely in strict-CSP surfaces. See
   `examples.md` anti-pattern.
2. **Hand-rolled in-component banner instead of `ShowToastEvent`.**
   Loses the platform's `aria-live` wiring, conflicts with other
   banners on the same page, lacks the platform's standardized
   dismiss control, misses release-notes improvements (high-contrast
   theme, mobile-toast positioning) that ship for free to
   `ShowToastEvent` dispatches.
3. **Defaulting `'error'` variants to `mode: 'dismissible'`.**
   5-second auto-dismiss is too short for any non-trivial
   validation message. Default error toasts to `mode: 'sticky'`;
   only fall back to `dismissible` when the message is a single
   short sentence the user doesn't need to act on.
4. **Dispatching `ShowToastEvent` from `connectedCallback` before
   the component is attached to the DOM.** Event has nowhere to
   bubble to; silently lost. Defer to `renderedCallback` (with a
   one-shot guard) or to after any awaited async work resolves.
5. **Passing `{ href, text }` instead of `{ url, label }` to
   `messageData` link entries.** Renders the literal `[object
   Object]` string in place of the intended link. Only `url` and
   `label` are recognized — case-sensitive, exact keys.

## Official Sources Used

- ShowToastEvent (lightning/platformShowToastEvent) API reference:
  https://developer.salesforce.com/docs/component-library/bundle/lightning-platform-show-toast-event/documentation
- Display a Toast Notification (LWC developer guide):
  https://developer.salesforce.com/docs/platform/lwc/guide/use-toast.html
- lightning/toast module (the modern alternative that works in LWR):
  https://developer.salesforce.com/docs/component-library/bundle/lightning-toast/documentation
- lightning-alert / lightning-confirm / lightning-prompt:
  https://developer.salesforce.com/docs/component-library/bundle/lightning-alert/documentation
- LWC Best Practices (component library):
  https://developer.salesforce.com/docs/platform/lwc/guide/best-practices.html
