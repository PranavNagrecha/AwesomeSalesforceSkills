# Gotchas — LWC Web Components Interop

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

Third-party web components in LWC are a **Beta** feature: "This feature is a Beta
Service. Customer may opt to try such Beta Service in its sole discretion." Weigh
that before putting one on the critical path of a production release.

---

## Gotcha 1: Lightning Locker blocks the whole feature — LWS is a prerequisite, not a preference

**What happens:** The component loads, `customElements.define()` runs, the tag
renders as an inert unknown element, and nothing works. The cause is org-level:
"To use third-party web components, enable Lightning Web Security first.
Lightning Locker doesn't support the use of custom elements, a key building block
of third-party web components."

**When it occurs:** Any org still on Locker — commonly older orgs where LWS was
deferred because an unrelated managed package needed retesting.

**How to avoid:** Check the org's Lightning Web Security setting *before*
scoping the work, not after the prototype fails. Enabling LWS is an org-wide
change that affects every component in the org, so it is a project with its own
regression test plan, not a checkbox you tick to unblock one component. If LWS
cannot be enabled, this approach is unavailable — write a native LWC instead.

---

## Gotcha 2: `loadScript` cannot load an ES module, which is how most libraries now ship

**What happens:** A modern component library publishes ES modules. `loadScript`
rejects them: "loadScript doesn't currently support ECMAScript Modules
(ESM)... Import third-party web components using pre-bundled JavaScript files
with custom elements in a legacy format such as IIFE or UMD." The failure appears
as a syntax error or an undefined global, not as a helpful message about module
format.

**When it occurs:** Essentially every current library — Shoelace, Material Web,
and most of the ecosystem ship ESM first, and many ship ESM only.

**How to avoid:** Establish the module format during evaluation, before anything
is promised. If the library publishes a UMD or IIFE build, use it. If it does
not, you own a bundling step (Rollup or esbuild producing IIFE) and therefore a
maintenance commitment: every upstream version bump needs a rebuild and a
re-upload. Price that in, and remember the bundle lands in a static resource
capped at 5 MB.

---

## Gotcha 3: Attribute changes after the first render are ignored

**What happens:** The component renders correctly with its initial data. A
reactive property updates, LWC writes the new attribute value, and the custom
element does not change. Per the docs: "LWC sets the data as attributes by
default, and sets properties only if they exist," and after rendering "attribute
changes are ignored."

**When it occurs:** Every wire-driven component — the first paint uses one value
and every subsequent update silently does nothing. It reads as a stale-data bug
and gets misdiagnosed as a caching problem.

**How to avoid:** Make the third-party element expose the data as a *property*
with a setter, so LWC updates the property rather than an inert attribute. Where
you cannot change the element, the docs give the other route: implement
`observedAttributes()` and `attributeChangedCallback()` so the element reacts to
the attribute write itself. Test the update path explicitly, not just the initial
render — this failure is invisible in a static demo.

---

## Gotcha 4: Template event bindings are lowercase-only

**What happens:** The library dispatches `CustomEvent('valueChange')` and the
template binds `onvalueChange={handleChange}`. The handler never fires. Per the
docs: "Event bindings support only lowercase events. To use events with
non-lowercase names, add an event listener using the `addEventListener()` API."

**When it occurs:** Any library using camelCase or kebab-case event names, which
is most of them — `sl-change`, `valueChanged`, `itemSelected`.

**How to avoid:** For a non-lowercase event name, attach the listener in
JavaScript with `addEventListener` rather than binding it in the template, and
re-dispatch a lowercase, Salesforce-flavoured event from the wrapper so the rest
of the codebase can use ordinary template bindings. That re-dispatch is the main
reason the wrapper component earns its keep.

---

## Gotcha 5: `customElements.define()` is global, so a second load throws

**What happens:** Two LWCs each call `loadScript` for the same library. The
registry is per page, and the custom element name "must contain a hyphen and be
unique on a page." The second registration throws, and because it happens inside
a promise chain it frequently surfaces as a silently empty component rather than
a visible error.

**When it occurs:** As soon as a second consumer appears — typically when the
wrapper succeeds and a colleague reuses the same library directly.

**How to avoid:** One wrapper component owns the load, and every other component
composes that wrapper. If the library must be loaded from more than one place,
guard the registration with `customElements.get('tag-name')` before defining. The
same uniqueness rule means the tag name has to be namespaced against everything
else on the page, including managed packages you do not control.

---

## Gotcha 6: `lwc:external` is a static directive with real edges

**What happens:** The tag must carry `lwc:external` for LWC to render it as a
native web component — `<third-party-component lwc:external></third-party-component>`.
Teams then hit its boundaries: "`lwc:external` doesn't support dynamic component
creation," so `lwc:is` / dynamic instantiation is out; "Slotting for synthetic
shadow isn't supported in third-party web components," so any design relying on
slots breaks on a surface still using synthetic shadow; and "LWS doesn't support
the `extends` option for customized built-in elements," so `class MyInput extends
HTMLInputElement` libraries do not work at all.

**When it occurs:** In the second sprint, once the simple case works and the
design starts asking for composition or a dynamically chosen component.

**How to avoid:** Test the composition shape — slots, dynamic selection,
customized built-ins — in the spike, not after the wrapper is written. If the
library depends on customized built-in elements, stop: there is no workaround,
and the earlier that is known the cheaper it is. Also note `lwc:spread`, the
bulk-property route, allows "Only one instance of `lwc:spread` on an element."

---

## Gotcha 7: Experience Builder does not support this with LWS enabled

**What happens:** The wrapper works in the Lightning app and produces nothing in
the Experience Cloud site. Per the docs: "Experience Builder sites don't
currently support third-party web components when Lightning Web Security (LWS)
is enabled." LWS is the prerequisite for the feature, so this is a hard
exclusion, not a configuration to work around.

**When it occurs:** Late, because internal surfaces are usually built and
demonstrated first and the portal is phase two.

**How to avoid:** Enumerate the target surfaces in the spike and test each one —
Lightning app, Experience Cloud site, mobile, and any embedded context. If an
Experience Cloud site is in scope, plan a native LWC for that surface from the
start rather than discovering the exclusion after the shared component is built.

---

## Gotcha 8: The element cannot reach the global document

**What happens:** Library code calling `document.getElementById('some-id')`
returns nothing. LWC restricts access to the global HTML document, and the
element is inside a shadow root. Libraries that render tooltips, dropdowns or
modals by appending to `document.body` — a very common pattern for overlay
positioning — fail or render in the wrong place.

**When it occurs:** Components with floating UI: date pickers, select menus,
tooltips, dialogs. The core control works and the overlay does not.

**How to avoid:** Test the overlay behaviour specifically, and check whether the
library offers a "boundary" or "container" option that keeps its portal inside
the component instead of `document.body`. Where it does not, that library is not
a candidate. This is also a useful early filter: a library whose docs talk about
appending to `document.body` will be difficult here regardless of how good it is.
