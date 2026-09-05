# Gotchas - LWC Accessibility

Line citations are `<page-slug> L<line>` against the Lightning Web Components Developer Guide
(https://developer.salesforce.com/docs/platform/lwc/guide/<page-slug>.html). Claims marked
"web standard" come from WAI-ARIA / WCAG, not from the Salesforce guide.

## Clickable Containers Drift Out Of Compliance Fast

**What happens:** A custom card or tile is made clickable with `onclick`, and then keyboard activation, focus styling, and announcements all need to be re-created manually.

**When it occurs:** Teams optimize for layout freedom before choosing a semantic interactive element.

**How to avoid:** Keep containers presentational and move interaction onto a button, link, or supported Lightning base component.

*Grounded:* `create-components-focus` L4043 — `<a>`, `<button>`, `<input>`, `<textarea>` receive
focus automatically; `<div>` and `<span>` do not and need `tabindex="0"` to be reachable at all.

---

## Icon-Only Actions Need Text Equivalents

**What happens:** A pencil or trash icon is obvious visually but vague to assistive technology.

**When it occurs:** `lightning-icon` or icon buttons are used without `alternative-text` or another accessible label.

**How to avoid:** Give every meaningful icon action a clear text equivalent. Treat icons as decorative only when the adjacent text already names the action.

*Grounded:* `base-components-accessibility` L4964 — `lightning-avatar` and `lightning-icon`
provide `alternative-text` for WCAG 1.1.1 non-text content; `lightning-icon` renders that
description with the `slds-assistive-text` SLDS class rather than showing it.

---

## Focus Loss Often Appears Only After Async Updates

**What happens:** Focus lands correctly on first render but disappears after save, conditional rerender, or modal close.

**When it occurs:** The component changes its template structure or closes an overlay without restoring focus.

**How to avoid:** Define focus targets for open, error, success, and close states and test them with keyboard-only navigation.

*Grounded:* `create-components-dom-work` L3062 — "Elements not rendered to the DOM aren't returned
in the `querySelector` result", so a focus call issued in the same tick as the state flip finds
nothing. Wait a microtask (or `renderedCallback`, `create-lifecycle-hooks-rendered` L4127) before
focusing newly rendered content.

---

## Manual ARIA Can Conflict With Built-In Semantics

**What happens:** Developers add extra roles or labels to elements that already expose semantics, creating duplicate or confusing announcements.

**When it occurs:** ARIA is used defensively instead of intentionally.

**How to avoid:** Prefer native semantics first, then add ARIA only when the component truly needs extra context or a supported composite-widget pattern.

*Grounded:* `base-components-accessibility` L4954–L4955 — base components already manage ARIA roles
and properties and update them on interaction (for example `lightning-accordion` toggles
`aria-hidden`, `lightning-input` appends `aria-describedby` when a validation error is displayed).
Adding your own on top is duplication, not reinforcement.

---

## Template `id` Values Are Rewritten, So Nothing May Select On Them

**What happens:** `this.template.querySelector('#myInput')` returns `null` in the org even though the
same selector works in a plain HTML page, and an `#myInput` CSS rule never applies.

**When it occurs:** Any time an `id` written in a template is used as a selector in JavaScript or CSS.
The framework transforms template `id` values into globally unique values when the template renders,
so the literal string you wrote no longer exists in the DOM.

**How to avoid:** Use `class`, `data-*`, or — preferably — `lwc:ref` plus `this.refs`. Reserve `id`
purely for the `for` / `aria-*` associations the framework rewires for you. In Jest, assert the
*relationship* (`label.getAttribute('for') === input.getAttribute('id')`), never a literal id.

*Grounded:* `create-components-accessibility-attributes` L4009–L4010;
`create-components-dom-work` L3063 and L3078–L3080; `create-components-css` L1853.

---

## Id-Based ARIA Association Stops At The Shadow Boundary

**What happens:** A label rendered by one component and an input rendered by another never link.
The screen reader announces an unlabelled edit field, and `aria-describedby` pointing at a sibling
component's help text is silently inert. No console error is raised.

**When it occurs:** Whenever `for`, `aria-labelledby`, `aria-describedby`, `aria-controls`,
`aria-owns`, or `aria-errormessage` names an id that lives in a **different** template. The guide is
explicit: ids and ARIA attributes in the same template are linked automatically, but attributes in
different templates must be linked manually, and in native shadow DOM they cannot be linked at all.

**How to avoid:** Keep the label, the control, the help text, and the error text in one template —
that is the whole reason the wrapper component in `code-examples.md` owns all four. If a genuine
cross-component reference is unavoidable, the guide's documented escape hatch is light DOM, which
does not scope ids and therefore lets `<label for="my-input">` reach an `<input id="my-input">` in a
separate component. Light DOM has a real security cost: it exposes the component to DOM scraping and
is not protected by Locker/LWS at the top level, so nest it inside a shadow DOM ancestor.

*Grounded:* `create-components-accessibility-attributes` L4034–L4036; `create-light-dom` L3188,
L3242–L3249, L3190, L3204.

---

## Id-Referencing ARIA Attributes Are Not Ordinary Reflected Properties

**What happens:** A component exposes `@api ariaDescribedBy` and assigns it like a normal field. The
value never appears in the rendered HTML, so assistive technology sees nothing, while the JavaScript
property reads back correctly and every unit test on the property passes.

**When it occurs:** Taking control of an attribute by exposing it as a public property stops it from
appearing in the HTML output by default. That applies to all attributes, but it bites hardest on the
id-referencing set — `for`, `aria-activedescendant`, `aria-controls`, `aria-describedby`,
`aria-details`, `aria-errormessage`, `aria-flowto`, `aria-labelledby`, `aria-owns` — which the guide
says must be set and read with `setAttribute()` and `getAttribute()`.

**How to avoid:** For that list, write a getter/setter pair that calls `setAttribute()` /
`getAttribute()` (and `removeAttribute()` to clear). For plain-value ARIA such as `aria-label` or
`aria-pressed`, the camel-case accessor mapping applies (`aria-label` → `ariaLabel`). Set host
defaults in `connectedCallback()`; the constructor may not add attributes to the host element.

*Grounded:* `js-props-html-attributes` L2515–L2517, L2531–L2542;
`create-components-accessibility-attributes` L4001–L4003, L4019, L4021;
`create-lifecycle-hooks-created` L4084.

---

## `tabindex` Accepts Only `0` And `-1`, And Fights `delegatesFocus`

**What happens:** A developer writes `tabindex="2"` to force a control earlier in the tab order, or
sprinkles `tabindex` across a component that has already set `delegatesFocus`. Focus order becomes
unpredictable — often the container is focused first and the real control second, giving keyboard
users a dead stop.

**When it occurs:** Only `0` and `-1` are supported values. `0` puts the element in the standard
sequential navigation order; `-1` removes it from that order while leaving it programmatically
focusable. Separately, the guide states outright that `tabindex` must not be combined with
`delegatesFocus` because it throws off the focus order.

**How to avoid:** Fix tab order by fixing DOM order. Use `tabindex="-1"` only for a node you intend
to focus programmatically (a heading or error region you move focus to). Pick one mechanism per
component: either `delegatesFocus` or explicit `tabindex`, never both.

*Grounded:* `create-components-focus` L4044, L4065.

---

## Focus Skips The Custom Element Unless You Opt In

**What happens:** A parent calls `this.refs.myField.focus()` and nothing happens, or tabbing reaches
the child component and appears to consume a tab stop that does nothing.

**When it occurs:** For custom components, focus skips the component container and moves to the
elements inside it. A custom element therefore has no default focus behaviour of its own: calling
`focus()` on the host is a no-op unless you supply one.

**How to avoid:** Two supported routes. Set `delegatesFocus` to `true` so host `focus()` reaches the
first focusable area inside, clicking a non-focusable node inside focuses that area, and `:focus`
applies to the host as well as the focused element. Or expose an explicit `@api` method that focuses
a `lwc:ref` target. The third route — putting `tabindex="0"` on the child element in the *parent's*
template — makes the whole component a tab stop, which is the right answer for a composite widget
and the wrong answer for a field wrapper.

*Grounded:* `create-components-focus` L4045, L4052, L4057, L4061–L4065.

---

## Base Components Always Render In Shadow DOM, Even Inside A Light DOM Component

**What happens:** A team switches a component to light DOM specifically to get cross-component id
association working, and the association still fails for the `lightning-input` inside it.

**When it occurs:** `renderMode` only changes *your* component's rendering. Base components are
always rendered in shadow DOM, so their internal `<input>` stays behind a boundary your `id` cannot
reach. Their internal markup and CSS classes are also explicitly not part of the contract and can
change in any release.

**How to avoid:** Do not try to reach inside a base component to fix its labelling. Use the
component's own documented attributes (`label`, `alternative-text`, `field-level-help`, its ARIA
attributes) — base components already associate the label you provide with the input field.

*Grounded:* `create-light-dom` L3198; `base-components-patterns-global` L4805, L4811;
`create-components-accessibility-attributes` L3988, L4000.

---

## `lightning-datatable` Has Two Keyboard Modes, And Custom Cell Types Opt Out By Default

**What happens:** A custom data type is added to a datatable, and the interactive element inside the
cell is unreachable by keyboard. Testing with a mouse shows nothing wrong.

**When it occurs:** The datatable exposes navigation mode (arrow keys between cells; actionable
elements render with `tabindex="-1"`) and action mode (Enter or Spacebar to enter; actionable
elements render with `tabindex="0"`). Elements in a standard or custom data type do not participate
in keyboard navigation by default — focus moves to the cell but not into the cell's contents.

**How to avoid:** In the custom data type template, pass `tabindex={internalTabIndex}` to the element
that should be focusable (`tabindex="-1"` for those that should not), and set
`data-navigation="enable"` on every element to be reachable *and* on any element that has a focusable
child. Where the custom type wraps a child component, the parent passes
`internal-tab-index={internalTabIndex}` and the child re-exposes it as a public property.

*Grounded:* `data-table-a11y` L6215–L6222, L6236–L6240, L6248, L6272, L6275–L6276.

---

## Synthetic Shadow Hides The Cross-Boundary Failure Until The Org Moves To Native

**What happens:** An id-based ARIA association across two components works in the org today, then
stops working when the component runs in native shadow — with no code change and no error.

**When it occurs:** Lightning Experience and Experience Builder sites currently use the synthetic
shadow polyfill by default, and Salesforce states it is committed to migrating from synthetic to
native shadow via mixed shadow mode. The prohibition the guide states — you can't link ids and ARIA
attributes between elements in separate templates — is written specifically about *native* shadow
DOM. Components run in native shadow outside Lightning Experience and Experience Cloud, such as in
Lightning Out.

**How to avoid:** Treat cross-template id association as unsupported everywhere, not as something
that happens to work. Test any component with cross-component ARIA references in a native-shadow
context before assuming it ships correctly, and never rely on the synthetic-shadow scope-token
attributes, which are internal implementation and can change at any time.

*Grounded:* `create-dom-synthetic` L3152–L3154, L3159; `create-dom` L3109, L3111;
`create-components-accessibility-attributes` L4035.
