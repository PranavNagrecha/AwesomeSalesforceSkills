# Gotchas — LWC Lightning Modal

Five behaviors of `lightning/modal` that surprise practitioners
coming from custom-overlay patterns, from `lightning/overlayLib`
(Aura), or from web-component libraries with different lifecycle
contracts. These are the issues that show up after the first
"Hello, Modal" works — when you try to do something real.

---

## Gotcha 1: `LightningModal` is a class to extend, not a tag to render

**What happens:** Practitioners new to the API try to place a
`<lightning-modal>` element in a parent template — there is no such
tag. Or they try to instantiate the modal as a child of a parent
LWC and toggle its visibility via `lwc:if`. The component never
renders. The Component Library doesn't list `lightning-modal` as a
slotted component because it isn't one — it's the base class.

**When it occurs:** First time using the API, especially when copying
fragments from older Aura-era examples that used
`<aura:component extends="force:overlay">` patterns or from
hand-rolled modal LWCs that the team is migrating.

**How to avoid:** Import `LightningModal` from `lightning/modal` and
`extend` it: `export default class MyModal extends LightningModal`.
Then invoke `MyModal.open(options)` from the parent — `open()` is a
static method on the class (inherited from `LightningModal`), not
on an instance. There is no template tag. There is no parent-side
`<c-my-modal>` element. The modal is portal-rendered into a
separate DOM root managed by Salesforce when `open()` is called.

---

## Gotcha 2: `@api` props are set once at `open()` and are NOT reactive afterward

**What happens:** Practitioners write `await
MyModal.open({ recordId: this.someRef })` then later mutate
`this.someRef` in the parent and expect the modal to re-render with
the new value. It doesn't. The modal's `@api recordId` was set
during `open()` — the same way a template-bound `@api` is set on
first render — but there is no ongoing binding between the parent
property and the modal instance because the modal is not in the
parent's template.

**When it occurs:** Wizard modals where the parent wants to push
fresh data mid-flight (e.g., "the parent's record refreshed via
RefreshApex — push the new recordId in"). Or list-edit modals where
the parent picks a different row while the modal is open and tries
to re-target it.

**How to avoid:** Treat the `open()` options object as a one-shot
initial state. If the modal needs to react to parent changes, the
right pattern is to close the current modal and open a new one with
the updated props — modal instances are designed to be ephemeral
(per the API docs, "the modal instance is destroyed upon closing").
If you need bidirectional ongoing communication, dispatch a custom
event from the modal that the parent listens for via a temporary
subscription pattern (lightning/messageService LMC works well here),
not via prop mutation. Mutating the modal's properties after open
silently no-ops.

---

## Gotcha 3: The `label` option is required, and missing it fails accessibility audits

**What happens:** Practitioners build a modal whose `lightning-modal-header`
they want to omit (e.g., a borderless image lightbox) and skip the
`label` option in `open()` too. The modal opens and looks fine. Then
Lighthouse / axe / Salesforce's Accessibility Audit flags it as
"dialog without accessible name." Screen readers announce only
"dialog" with no name. WCAG 4.1.2 (Name, Role, Value) is violated.

**When it occurs:** Header-less variants, modal-as-image-viewer
patterns, and any scenario where the visual design doesn't include a
title bar but the platform still needs an accessible name. Also
hits practitioners migrating from custom modals where the only
"name" was the visible `<h2>` text.

**How to avoid:** Always pass `label` to `Modal.open()`, even when
you're not rendering a `lightning-modal-header`. Per the
`lightning/modal` API reference, `label` "sets the modal's title and
assistive device label" — when no header is rendered, label is the
only source of an accessible name. Pair it with `description` (which
maps to `aria-description` / `aria-describedby`) when the modal's
purpose needs a sentence of context beyond the title. Audit your
modals by running them through Salesforce's Accessibility Tools
extension or the Component Library's built-in audit — missing
`label` is the single most common LightningModal a11y finding.

---

## Gotcha 4: `this.close(value)` resolves the open() Promise — don't `dispatchEvent` to return values

**What happens:** Practitioners try to return data from the modal
via `this.dispatchEvent(new CustomEvent('save', { detail: payload }))`,
expecting the parent's `Modal.open()` caller to receive the data
through an event listener. The parent never sees the event because
the modal lives in a separate portal — the parent has no element
handle to attach a listener to. The save happens visually (button
fires), but the parent's `await Modal.open(...)` Promise never
resolves with the payload; it eventually resolves with `undefined`
when the user dismisses some other way.

**When it occurs:** Form modals where the developer's reflex from
regular LWCs is "fire a custom event up the tree." Also any time the
return value is something more complex than a primitive — practitioners
fall back to events when they're not sure how to pass a typed object.

**How to avoid:** `this.close(value)` is the return-value channel.
The argument can be anything serializable as a JavaScript value:
primitives, plain objects, arrays. The parent receives it as the
Promise resolution of `Modal.open()`. For the confirm/cancel/dismiss
distinction, pass a typed sentinel ('confirm' / 'cancel') or a
structured object (`{ status: 'created', recordId: '001...' }`) and
treat the dismissal path (`undefined`) as a third explicit branch.
Custom events ARE useful inside the modal (for the modal's own
internal children to talk to the modal class) but don't cross the
portal boundary to the opener.

---

## Gotcha 5: `LightningModal` cannot be hosted in Quick Actions, Aura components, or under restricted CSP

**What happens:** A practitioner builds a beautiful LightningModal,
then tries to surface it from a `lightning-quick-action` ("Headless
Quick Action") and discovers the modal won't open — Quick Actions
have their own modal shell and the platform refuses to nest a
`LightningModal` inside one. Or they try to wrap the modal in an
Aura component (because the page still uses an Aura `c:lwcContainer`)
and `LightningModal.open()` throws because Aura can't extend an LWC
base class. Or the modal works in Lightning Experience but fails in
an Experience Cloud site with a tight CSP — `Modal.open()` succeeds
but rendering the portal triggers a CSP violation.

**When it occurs:** Quick Action surfaces (both screen and headless
flavors), Aura-host pages still in the org (record pages with
unconverted Aura components in the surrounding layout), Experience
Cloud sites with custom CSP / "Strict CSP" enabled, and Mobile
Publisher apps with locked-down WKWebView settings.

**How to avoid:** Check the surface before committing to
`LightningModal`. For Quick Actions, use the action's own
header/footer slots (the action IS the modal — don't open one inside
one). For Aura-host scenarios, expose the LWC that *opens* the modal
through the `c:lwcContainer` boundary, not the modal class itself.
For Experience Cloud, validate against the site's CSP setting in the
target sandbox before promoting — the failure mode is silent in
many builds. As an additional constraint: Aura components cannot
`extend` `LightningModal` (it's an LWC-only base class), so any
shared-platform pattern that requires Aura participation has to
treat the modal as opaque to Aura.
