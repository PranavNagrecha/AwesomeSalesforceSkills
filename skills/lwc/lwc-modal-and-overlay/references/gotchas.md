# Gotchas - LWC Modal And Overlay

Line citations are to the Lightning Web Components Developer Guide, given as
`page-slug`, L<line>, where the slug is the page id in
`https://developer.salesforce.com/docs/platform/lwc/guide/<slug>.html`.

## `LightningModal` Has A Different Mental Model Than Template Toggles

**What happens:** Developers expect to open the modal by conditionally rendering it in the parent template.

**When it occurs:** Teams approach the modal as normal component markup instead of an overlay API.

**How to avoid:** Treat the modal as an interaction surface opened through `LightningModal.open()` and closed through `close(result)`.

---

## There Is No `<lightning-modal>` Tag, And The Import Is A Default Import

**What happens:** A template containing `<lightning-modal>` silently renders nothing, and
`import { LightningModal } from 'lightning/modal'` yields `undefined`, so `extends undefined` throws
at module evaluation with an error that names neither the tag nor the import.

**When it occurs:** Any time the modal is modelled on ordinary base components. The guide is blunt
about this being the exception: "Unlike most base components, when you use this component you don't
add a `<lightning-modal>` tag to your component template or extend `LightningElement`. There is no
`lightning-modal` component" (`use-dialog-modal`, L10375). Only `lightning/modal` and
`lightning/datatable` support class extension at all (`base-components-patterns`, L4774–L4776).

**How to avoid:** `import LightningModal from 'lightning/modal';` — no braces — and
`export default class X extends LightningModal`. Import `api` from `lwc`, but never
`LightningElement` alongside it (`use-dialog-modal`, L10377, L10379).

---

## `lightning-modal-body` Is Required; Header And Footer Are Not

**What happens:** A modal whose template omits `lightning-modal-body` and instead puts content in a
bare `<div>` loses the padding, scrolling, and frame the modal container expects, and the content
can sit outside the scroll region on small viewports.

**When it occurs:** When someone builds the header and footer first and treats the body as ordinary
markup. The guide states the split plainly: "Use the **required** `lightning-modal-body` component to
provide the main content displayed in the modal. Use the **optional** `lightning-modal-header`
component ... and the **optional** `lightning-modal-footer`" (`use-dialog-modal`, L10376).

**How to avoid:** Every modal template starts with `lightning-modal-body`. Add header and footer only
when there is a title or actions to put in them. `lightning-modal-body` does not let you restyle the
white frame, the close button, or the grey backdrop (`base-components-min-version` table, L4579) —
if a design demands that, the design is wrong, not the component.

---

## `@api` Properties On A Modal Are Set By `open()`, Not By Markup

**What happens:** A reviewer greps the repo, finds `@api queues` on the modal, finds no
`<c-queue-picker-modal queues={...}>` anywhere, and deletes the property as dead code. The modal then
opens empty in production.

**When it occurs:** Always, because a modal is never placed in a parent template. The guide describes
the mechanism from the other direction: the launcher "opens the `myModal` component using the
component's `open` method and **provides data to be used in the modal's `options` property**"
(`use-dialog-modal`, L10387).

**How to avoid:** Name every `@api` property of the modal in the launcher's `open({...})` call and in
a Jest assertion (`toHaveBeenCalledWith(expect.objectContaining({...}))`) so a rename breaks a test
rather than a user. The skill checker flags an `@api` property on a `LightningModal` subclass that no
launcher's `open()` mentions.

---

## `open()` Returns A Promise; `close()` With No Argument Resolves It To `undefined`

**What happens:** The launcher awaits `open()`, gets `undefined` back, and cannot distinguish "user
cancelled", "user saved", and "user dismissed with the X" — so it either refreshes on every close or
never refreshes.

**When it occurs:** When `close()` is called bare. The guide ties the two ends together in one
sentence: "When the user clicks the Option 1 or Option 2 button, `this.close(id)` returns the option
that they chose and the modal closes", and the launcher's "result value is returned from `MyModal`"
(`use-dialog-modal`, L10379, L10388).

**How to avoid:** Close with a tagged shape on every path — `this.close({ status: 'cancelled' })`,
`this.close({ status: 'confirmed', ... })` — and branch on the tag. Never leave a code path that can
close the modal without calling `close()` at all.

---

## `NavigationMixin` Cannot Wrap A `LightningModal` Subclass

**What happens:** `export default class MyModal extends NavigationMixin(LightningModal)` compiles,
and then navigation from inside the modal does nothing or errors at runtime.

**When it occurs:** Whenever a modal needs to send the user to a record. The guide restricts the
mixin explicitly: "Use `NavigationMixin` only with a Lightning web component that extends
`LightningElement`. **You can't use the `NavigationMixin` function directly in a custom component that
extends `LightningModal`**" (`use-navigate-modal`, L10258–L10259).

**How to avoid:** Use the documented relay — the child inside the modal builds the `PageReference`
and dispatches it, the modal passes it out through `close()` or an event on `open()`, and the parent
(a plain `LightningElement`) calls `NavigationMixin.Navigate` (`use-navigate-modal`, L10260). See
`lwc/navigation-and-routing` for the routing-side treatment.

---

## Modal Stacking Is A Documented Platform Behaviour, Not Necessarily Your Bug

**What happens:** A screen quick action's modal stays open and inactive underneath a second modal
that a `NavigationMixin.Navigate` call opened on top of it. Teams "fix" this by closing the first
modal manually and then break the browser Back button.

**When it occurs:** Any navigation from inside a modal. "By default, `replace` is false and the
previous modal isn't closed automatically. In this case, the newer modal overlays and stacks on the
previous modal ... To automatically close the previous modal when navigating, set `replace` to true"
(`use-navigate-quick-action`, L10324–L10326).

**How to avoid:** Decide the stacking behaviour deliberately with the `replace` argument of
`[NavigationMixin.Navigate](pageReference, replace)`. Know the two documented exceptions: even with
`replace` true, the previous modal is preserved when the new modal comes from a lookup field's
record-create modal, or from `LightningModal.open()` called out of the quick-action modal
(`use-navigate-quick-action`, L10331–L10333).

---

## Focus Return Is Easy To Forget

**What happens:** The modal closes, but keyboard users land at the top of the page or lose context.

**When it occurs:** The launching control is not remembered and focus restoration is left implicit.

**How to avoid:** Store the launcher when appropriate and define where focus should return after
cancel or success. When you do hand-build focusable regions, only `tabindex` values `0` and `-1` are
supported, and `tabindex` must not be combined with `delegatesFocus` because it throws off the focus
order (`create-components-focus`, L4044, L4065). Focus depth belongs to `lwc/lwc-focus-management`.

---

## Blocking Close During Save Must Be Temporary

**What happens:** Users are trapped in an overlay with no escape path after an error or long-running action.

**When it occurs:** `disableClose` or an equivalent pattern is left active longer than the bounded save window.

**How to avoid:** Pair any temporary close lock with visible progress, timeout awareness, and immediate restoration once the action settles — set it in a `try` and clear it in a `finally`, never on the success branch alone.

UNVERIFIED (2026-09-05): `disableClose` appears nowhere in the LWC Developer Guide text. It is a
`lightning/modal` Component Library specification property. The behaviour described here is the
pattern this skill recommends; confirm the property name and its exact effect on the Escape key and
the header X against the Component Library before writing it into code.

---

## A Screen Quick Action's Modal Is Not A `LightningModal`, And Its X Skips Your Cancel Logic

**What happens:** A screen quick action ships with a custom footer whose Cancel button rolls back a
draft. A user clicks the header X instead, the panel closes, and the rollback never runs.

**When it occurs:** Only for LWC screen quick actions, which are a separate modal surface: a screen
quick action "displays a component in a modal window" and is closed programmatically by dispatching
`CloseActionScreenEvent` from `lightning/actions` (`use-quick-actions-screen`, L10569, L10572). The
guide states the trap directly: "If you build a screen quick action with custom footer buttons,
pressing X only closes the modal, there are no hooks to execute additional logic on close. If a
screen quick action has logic that executes on Cancel, the logic is bypassed when the panel closes"
(`use-quick-actions-screen`, L10574).

**How to avoid:** Never put must-run cleanup behind a quick action's Cancel button. Make the action
idempotent, or do the work only on Save. Note the second quick-action trap in the same page: unlike
other components on a record page, LWC quick actions do not pass `recordId` in `connectedCallback()`
— declare an `@api` setter that stores it in a private field and read `this._recordId`
(`use-quick-actions-screen`, L10571). Use `lightning-quick-action-panel` for the header/body/footer
frame there, not `lightning-modal-*` (`use-quick-actions-screen`, L10575).

---

## The Two Toast Modules Are Not Interchangeable, And The Container Silently Queues

**What happens:** A toast fired with `ShowToastEvent` never appears in an LWR Experience Cloud site.
Separately, the fourth toast on a page does not appear until an earlier one is dismissed, so a batch
operation looks like it only reported three results.

**When it occurs:** `lightning/platformShowToastEvent` "isn't supported on login pages in Aura sites,
LWR sites for Experience Cloud, and standalone apps"; `lightning/toast` is the preferred module and
supports inline links in both title and message (`use-toast`, L10448–L10449, L10452). The queueing is
the `lightning/toastContainer` default of **3** maximum toasts, position **top-center**, container
position **fixed**, one instance per page — and "when the page displays the maximum number of toasts,
any attempt to display an additional toast results in the toast being displayed only when a toast is
closed or dismissed" (`use-toast`, L10458–L10464).

**How to avoid:** Default to `lightning/toast` and reserve `ShowToastEvent` for code that must run on
older bundles. Never report per-record results as N toasts — summarise into one, or use an alert if
the user must acknowledge. Also note the styling asymmetry: `lightning/platformShowToastEvent` does
not support the `--slds-c-toast-*` custom properties, while `lightning/toast` and
`lightning/toastContainer` do (`create-components-css-custom-properties`, L1721).

---

## Overlays Multiply Quickly

**What happens:** A modal opens another dialog or quick action, and the user can no longer reason about the stack.

**When it occurs:** Teams keep escalating interruption instead of simplifying the workflow.

**How to avoid:** Avoid nested overlays and move larger workflows to a dedicated page or flow experience. One place the platform forbids them outright: an Experience Builder custom property editor must not "create flyouts, popouts, or window overlays (also known as modals)", because they interrupt the Builder user's editing experience (`use-experience-cloud-general-guidelines`, L8331).
