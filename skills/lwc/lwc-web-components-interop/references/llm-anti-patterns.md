# LLM Anti-Patterns — LWC Web Components Interop

Common mistakes AI coding assistants make when embedding third-party web components in LWC.

## Anti-Pattern 1: Calling customElements.define() from every LWC

**What the LLM generates:** Each LWC that uses `<my-widget>` calls `customElements.define('my-widget', MyWidget)` in its connectedCallback.

**Why it happens:** The model isolates each component's setup and does not account for the global registry.

**Correct pattern:**

```
customElements.define() is global. Define ONCE per page. Centralize
load in a shared utility that checks `customElements.get(tag)` before
defining. Double-define throws "already defined" and breaks the
page.
```

**Detection hint:** Multiple LWCs with `customElements.define('same-tag', ...)` in their connectedCallback.

---

## Anti-Pattern 2: Embedding a React-wrapped web component as if it were native

**What the LLM generates:** `<my-react-chart>` pulled from npm, imported as Static Resource, expected to just render.

**Why it happens:** The model sees a custom-element-looking tag and assumes standard compatibility.

**Correct pattern:**

```
Verify the library publishes a STANDARD custom element, not a React-
or Vue-wrapped component. Framework-bundled components drag their
framework into Salesforce's page, break LWS, and bloat load. For
interop, use a standards-based library (Shoelace, Lit-based) or
wrap the source React component server-side.
```

**Detection hint:** package.json listing `react` / `react-dom` as dependencies for a "web component" library.

---

## Anti-Pattern 3: Passing complex objects via attributes instead of properties

**What the LLM generates:** `<my-widget data-config="{...}">` with a JSON string.

**Why it happens:** The model writes HTML attributes and misses that custom elements expose properties on the element instance.

**Correct pattern:**

```
Pass complex values via element PROPERTIES, not attributes. In LWC:
`<my-widget config={configObject}>` with a template binding, or
`this.refs.widget.config = obj` in renderedCallback. Attributes are
strings; properties carry any JS value and avoid JSON encoding.
```

**Detection hint:** `data-*` attributes holding serialized JSON for web-component configuration.

---

## Anti-Pattern 4: Styling via global CSS leaking past shadow DOM

**What the LLM generates:** Adds SLDS overrides in a stylesheet hoping to style the third-party component.

**Why it happens:** The model does not account for shadow DOM encapsulation.

**Correct pattern:**

```
Third-party web components with shadow DOM block external CSS. Style
via (a) CSS custom properties they expose (--sl-color-primary), (b)
parts (::part(button)) if the component supports it, or (c) wrapping
in a styled container. Global overrides fail silently.
```

**Detection hint:** LWC stylesheet with selectors targeting internal third-party elements that never apply.

---

## Anti-Pattern 5: Listening for third-party events with LWC template `on` syntax assuming hyphenated names

**What the LLM generates:** `<sl-input onsl-change={handle}>` expecting dashed event name to work.

**Why it happens:** The model uses LWC template syntax for a name it does not know is lowercased.

**Correct pattern:**

```
LWC template `on<event>` requires lowercase, no-dash event names.
For third-party events like `sl-change`, use
`this.addEventListener('sl-change', ...)` in renderedCallback. Or
bridge in the wrapper LWC by re-dispatching the event as `slchange`
before consumers see it.
```

**Detection hint:** LWC template with `on<dash-event>` attributes that never fire.
