# Well-Architected Notes — LWC Web Components Interop

## Relevant Pillars

- **Reliability** — This feature is Beta, requires an org-wide Lightning Web
  Security change, is excluded on Experience Builder sites while LWS is enabled,
  and does not support customized built-in elements or synthetic-shadow slotting.
  None of those are bugs to route around; they are the shape of the platform
  surface. Reliability here means discovering the constraints in a spike that
  exercises every target surface, rather than after a shared component is on
  three pages.

- **Performance** — Every third-party library is a static resource on a shared
  budget: 5 MB per resource, 250 MB per org. It also arrives as a synchronous
  `loadScript` before first paint, so the component has two visual states — before
  the library resolves and after. Designing the pre-load state deliberately (a
  base-component fallback, not a blank div) is the difference between a component
  that degrades and one that looks broken.

- **Operational Excellence** — The interop rules are non-obvious and each one
  fails silently: `lwc:external` on the tag, guarded registration, properties
  rather than attributes for anything reactive, `addEventListener` for
  non-lowercase events. Encoding them once in a wrapper is what keeps the
  knowledge from having to live in every developer's head.

## Architectural Tradeoffs

**Third-party element vs building the control natively.** The library is free
until it is not: it costs a bundling step (since `loadScript` cannot load ESM and
most libraries now ship ESM only), an org-wide LWS migration, a static resource
to version, a Beta dependency, and one excluded surface. A native LWC costs build
time and gives you SLDS alignment, accessibility you control, and no version
treadmill. Reach for the library when it provides something genuinely hard — a
rich text editor, a diagram canvas, a data grid with virtual scrolling — and
build natively when it provides something merely tedious.

**Wrapper component vs direct consumption.** Direct consumption is fewer files
today and spreads the interop rules across every consumer. A wrapper concentrates
them: one place owns the load, the guarded registration, the property contract,
and the event renaming, and swapping libraries later becomes a change to one
component instead of an archaeology exercise. Take the wrapper on the second
consumer, at the latest.

**Where the update path lives.** Reactive data must reach the element as a
property, because attribute writes after the first render are ignored. If the
element already exposes properties, this is free. If it does not, you are
subclassing or patching a third-party element — which means you now own a fork,
and every upstream release is a merge. That cost belongs in the evaluation, not
in the sprint that discovers it.

**Enabling LWS for one component.** LWS is a prerequisite and an org-wide switch
that changes the security context of every existing component. Treating it as a
dependency of one feature understates it; it is its own project with its own
regression plan. If LWS is already on, this whole trade-off disappears — which is
why the first question in the spike is which security architecture the org runs.

## Anti-Patterns

1. **Prototyping in a Locker org.** Lightning Locker does not support custom
   elements at all, so the feature cannot work. The symptom is an inert tag, not
   an error message naming the cause.
2. **Wrapping a framework component and calling it a web component.** Ships a
   second UI framework into the page and forfeits every interop mechanism the
   platform provides.
3. **Binding reactive data as an attribute.** The first render is correct and
   every subsequent update is silently dropped — the most expensive failure in
   this domain because it passes review.
4. **Loading the library from more than one component.** `customElements.define()`
   is global per page; the second registration throws inside a promise chain and
   surfaces as an empty component.

## Official Sources Used

- LWC Developer Guide — Third-Party Web Components (Beta) — https://developer.salesforce.com/docs/platform/lwc/guide/create-use-third-party-intro.html — confirms the Beta status ("This feature is a Beta Service...") and that "To use third-party web components, enable Lightning Web Security first. Lightning Locker doesn't support the use of custom elements, a key building block of third-party web components." (verified 2026-08-14)
- LWC Developer Guide — Use Third-Party Web Components in LWC (Beta) — https://developer.salesforce.com/docs/platform/lwc/guide/create-use-third-party-components.html — confirms the `lwc:external` directive and its markup, that "loadScript doesn't currently support ECMAScript Modules (ESM)" and libraries must be "pre-bundled JavaScript files with custom elements in a legacy format such as IIFE or UMD", that "lwc:external doesn't support dynamic component creation", that "Experience Builder sites don't currently support third-party web components when Lightning Web Security (LWS) is enabled", that LWS does not support the `extends` option for customized built-in elements, and that components cannot use `document.getElementById()` because LWC restricts access to the global document (verified 2026-08-14)
- LWC Developer Guide — Work with Custom Elements (Beta) — https://developer.salesforce.com/docs/platform/lwc/guide/create-use-custom-elements.html — confirms registration via `customElements.define(name, constructor)`, that "The `name` must contain a hyphen and be unique on a page", the lifecycle callbacks, and that "Lightning Locker doesn't support third-party web components" (verified 2026-08-14)
- LWC Developer Guide — Pass Data to a Custom Element (Beta) — https://developer.salesforce.com/docs/platform/lwc/guide/create-use-third-party-pass-data.html — confirms that "LWC sets the data as attributes by default, and sets properties only if they exist", that after rendering "attribute changes are ignored" and `observedAttributes()`/`attributeChangedCallback()` are the remedy, and that "Event bindings support only lowercase events. To use events with non-lowercase names, add an event listener using the `addEventListener()` API." (verified 2026-08-14)
- LWC Developer Guide — HTML Template Directives — https://developer.salesforce.com/docs/platform/lwc/guide/reference-directives.html — confirms `lwc:spread` "Spreads properties to a child component" and that "Only one instance of `lwc:spread` on an element is allowed" (verified 2026-08-14)
- LWC Developer Guide — Use Third-Party JavaScript Libraries — https://developer.salesforce.com/docs/platform/lwc/guide/js-third-party-library.html — confirms the `loadScript` import from `lightning/platformResourceLoader`, that static-resource hosting is "a Lightning Web Components content security policy requirement", and that under LWS "most third-party libraries work as expected without changes. However, some libraries require changes to work with LWS." (verified 2026-08-14)
- LWC Developer Guide — Static Resources — https://developer.salesforce.com/docs/platform/lwc/guide/create-resources.html — confirms "The maximum file size is 5 MB" and "An org can have up to 250 MB of static resources" (verified 2026-08-14)

**Not verified, deliberately omitted:** the API version in which `lwc:external`
became available. The Beta documentation does not state one, and no other
developer.salesforce.com page read for this skill gave a number — check the
release notes for the org's target API version rather than taking a figure from
here.
