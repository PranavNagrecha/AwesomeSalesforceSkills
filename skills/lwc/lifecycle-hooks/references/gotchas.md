# Gotchas: LWC Lifecycle Hooks

Line citations are to the crawled Lightning Web Components Developer Guide
(`lwc_guide <page-slug> L<line>`); each page is at
`https://developer.salesforce.com/docs/platform/lwc/guide/<page-slug>.html`.

---

## Event Listeners Without Cleanup Accumulate in Experience Cloud

**What happens:** A FlexCard or LWC on an Experience Cloud site adds a `window.addEventListener('resize', ...)` in `connectedCallback`. In Experience Cloud, users navigate between pages without full page reloads (client-side routing). The component is destroyed (`disconnectedCallback` called) but the listener was never removed. The user navigates back to the page — a new instance adds another listener. After 5 page visits: 5 identical listeners firing on every resize event. Memory grows. The destroyed components' `this` references are held alive by the listeners, preventing garbage collection. On low-memory mobile devices, the browser tab crashes.

UNVERIFIED (2026-09-05): the guide states the responsibility split — "The framework takes care of managing and cleaning up listeners for you as part of the component lifecycle. However, if you add a listener to anything else (like the window object, the document object, and so on), you're responsible for removing the listener yourself" (`lwc_guide events-handling` L5102-L5103) — and that `connectedCallback` can fire repeatedly (`create-lifecycle-hooks-dom` L4111). The Experience Cloud client-side-routing detail and the mobile tab-crash outcome are field observation, not documented in the guide.

**When it bites you:** Any LWC with `window.addEventListener` or `document.addEventListener` deployed in Experience Cloud. Internal org Lightning pages also affected but less severely (full page reloads are more common).

**How to avoid it:**
- Always store the bound handler: `this._handler = this.myMethod.bind(this)`
- Always remove it: `window.removeEventListener('resize', this._handler)` in `disconnectedCallback`
- The bound reference must be the SAME object — calling `.bind(this)` twice creates two different function objects; `removeEventListener` won't find the second one

---

## `renderedCallback` Without a Guard Causes Infinite Re-render

**What happens:** A developer uses `renderedCallback` to set a reactive property (`@track` or any reactive state). Setting the property triggers a re-render. Re-render calls `renderedCallback` again. Another state update. Infinite loop. The component locks up the browser tab.

The guide is explicit about both halves: "When a component rerenders, the expressions used in the template are reevaluated and the `renderedCallback()` lifecycle hook executes" (`lwc_guide reactivity-fields` L2286) and "Updating the state of your component in `renderedCallback()` can cause an infinite loop" (`lwc_guide create-lifecycle-hooks-rendered` L4138). Fields are reactive without any decorator — "LWC tracks field value changes in a shallow fashion. Changes are detected when a new value is assigned to the field by comparing the value identity using `===`" (`reactivity-fields` L2287) — so a plain `this.height = ...` is enough to re-enter the hook.

UNVERIFIED (2026-09-05): the specific console text ("Maximum update depth exceeded") is a browser/engine string not quoted anywhere in the guide.

**The specific pattern that burns people:**
```javascript
renderedCallback() {
    this.componentHeight = this.template.querySelector('.container').offsetHeight;
    // componentHeight is reactive → triggers re-render → renderedCallback fires again → loop
}
```

**How to avoid it:**
```javascript
renderedCallback() {
    if (this._heightMeasured) return;
    this._heightMeasured = true;
    this.componentHeight = this.template.querySelector('.container').offsetHeight;
}
```

The guide names this exact remedy: "use a boolean field like `hasRendered` to track whether `renderedCallback()` has been executed" (`create-lifecycle-hooks-rendered` L4136).

---

## `window.location.href` Breaks in Three Deployment Contexts

**What happens:** A developer navigates using `window.location.href = '/lightning/r/Account/' + id + '/view'`. Works perfectly in the developer console. Works in a full desktop browser on Lightning Experience. Breaks in: (1) Salesforce mobile app — the mobile shell has its own navigation stack; direct URL manipulation bypasses it and opens a web view instead of the native record page. (2) Experience Cloud — community URLs have different base paths (`/s/` prefix); hardcoded `/lightning/r/` paths 404. (3) Lightning Out / embedded components — the host page's routing is bypassed.

UNVERIFIED (2026-09-05): the LWC Developer Guide does not state that `window.location` breaks in these containers — it uses `window.location.pathname` itself in an LWR sample (`lwc_guide create-community-info` L3905-L3908). The guide does list navigation as a `connectedCallback` use case via `lightning/navigation` (`create-lifecycle-hooks-dom` L4108). Navigation behaviour across containers is owned by `lwc/navigation-and-routing`; treat the three-context claim as field guidance until confirmed there.

**How to avoid it:**
- `NavigationMixin.Navigate()` handles all three deployment contexts transparently
- For record pages: `type: 'standard__recordPage'`
- For list views: `type: 'standard__objectPage'`
- For custom pages: `type: 'standard__navItemPage'`
- For external URLs: `type: 'standard__webPage'`

---

## Cross-Component DOM Access Returns `null`, It Does Not Throw

**What happens:** A developer uses `this.template.querySelector('c-child-component').shadowRoot.querySelector('.submit-button')` to click a button in a child component. What actually happens under Lightning Locker / Lightning Web Security is quieter than a permission error: "Accessing `shadowRoot` on a component retrieved from the template always returns `null`" (`lwc_guide get-started-oss` L131). The next line dereferences `null` and the component dies with a `TypeError` that names `querySelector`, not shadow DOM — which is why the cause is usually mis-diagnosed. The same page notes `this.template.host` always returns `null` too (L130). Separately, the guide says outright: "Don't use these DOM APIs to reach into a component's shadow tree in orgs that use Lightning Locker" (`create-dom` L3130).

**When it bites you:** Any time you try to "reach into" another component's DOM from a parent or sibling — even for something simple like setting focus. It also bites in the opposite direction: `element.shadowRoot` *does* work in Jest, because it is a test-only API (`unit-testing-using-jest-create-tests` L12379), so a green test suite proves nothing about this failure.

**How to avoid it:**
- Parent → Child communication: `@api` property on the child
- Child → Parent communication: `CustomEvent` dispatch from child
- Programmatic actions on child (focus, click): expose an `@api` method on the child: `@api focus() { this.template.querySelector('input').focus(); }`
- Sibling → Sibling: Lightning Message Service (LMS) or shared parent state

---

## Inline `<script>` Tags Are Silently Blocked by CSP

**What happens:** A developer adds `<script src="https://cdn.example.com/library.min.js"></script>` to an LWC template, following standard HTML practice. The component renders but the library doesn't work. No visible error. The developer spends an hour debugging the library before checking CSP. Uploading the library as a static resource is not a preference — it is "a Lightning Web Components content security policy requirement" (`lwc_guide js-third-party-library` L2655).

UNVERIFIED (2026-09-05): the exact browser console text ("Refused to load the script … Content Security Policy directive") is a browser string, not quoted in the guide.

**How to avoid it:**
1. Upload the library to Salesforce Static Resources
2. Import `loadScript` from `lightning/platformResourceLoader`
3. Load it on the first render — the guide invokes `loadStyle` and `loadScript` "in `renderedCallback()` on the first render. Using `renderedCallback()` ensures that the page loads and renders the container before the graph is created" (`js-third-party-library` L2680), and aggregates the two promises with `Promise.all()` plus a `catch()` (L2681)

This is one of the most commonly missed LWC setup steps for developers coming from traditional web development. See `lwc/static-resources-in-lwc` for the full loading contract.

---

## `disconnectedCallback` Flows Parent → Child, Not Child → Parent

**What happens:** A parent tears down shared state in its `disconnectedCallback` — closing a cache, releasing a context, nulling a shared handle — and a child's `disconnectedCallback` then tries to use it. Developers assume unmount mirrors mount and runs bottom-up, the way `renderedCallback` does. It does not. The guide puts both insertion and removal in the same direction: "The `connectedCallback()` lifecycle hook fires when a component is inserted into the DOM. The `disconnectedCallback()` lifecycle hook fires when a component is removed or hidden from the DOM. **Both hooks flow from parent to child**" (`lwc_guide create-lifecycle-hooks-dom` L4101). Only `renderedCallback` reverses: it "flows from child to parent" (`create-lifecycle-hooks-rendered` L4127).

**When it bites you:** Any parent that owns a resource its children also use — a message context, a shared observer, a websocket, a cache handle — and releases it on unmount.

**How to avoid it:**
- A component tears down only what it set up. Shared resources are released by whoever created them, and children must not depend on a parent-owned handle still being live in their own `disconnectedCallback`.
- Null-check any parent-supplied handle before using it during teardown.
- If ordering genuinely matters, have the child dispatch on removal rather than reaching for parent state.

---

## `connectedCallback` Is Not a One-Time Initializer

**What happens:** A component subscribes to a message channel, opens a timer, or fires an Apex call in `connectedCallback` on the assumption that it runs once per component. It does not: "`connectedCallback()` can fire more than one time. For example, if you remove an element and then insert it into another position, such as when you reorder a list, the hook fires several times. If you want code to run one time, write code to prevent it from running twice" (`lwc_guide create-lifecycle-hooks-dom` L4111). Toggling a conditional directive has the same effect — "Using the conditional directive also triggers the `disconnectedCallback` and `connectedCallback` lifecycle callbacks" (`create-use-custom-elements` L4362). Each pass adds another subscription; the handler then runs N times per message and the component appears to double-post.

**When it bites you:** Reorderable lists, `lwc:if` toggles, console tabs being reopened, and any Experience Cloud page that swaps regions without a reload.

**How to avoid it:**
- Guard every subscription with an existence check. The guide's own sample does exactly this: `if (!this.subscription) { this.subscription = subscribe(...) }` and, on teardown, `unsubscribe(this.subscription); this.subscription = null;` (`use-message-channel-subscribe` L10018-L10031).
- Pair the guard with the teardown. A guard alone leaks; a teardown alone re-subscribes.
- If the state is derived from a public property, the guide prefers a setter over `connectedCallback` entirely: "If a component derives its internal state from the properties, it's better to write the logic in a setter than in `connectedCallback()`" (L4110).

---

## An `async` Lifecycle Hook Is Not Awaited by the Framework

**What happens:** Someone writes `async connectedCallback()` so they can `await` an Apex call, and the code reads correctly. The framework does not wait: "`connectedCallback()` and `disconnectedCallback()` are synchronous. The framework doesn't await a promise that's returned from a lifecycle hook. If you mark a hook as `async`, code after an `await` runs after the framework moves on, which causes unpredictable order of execution relative to rendering, parent and child callbacks, and event handlers" (`lwc_guide create-lifecycle-hooks-dom` L4117). The failure is intermittent and order-dependent: the tail of `connectedCallback` can land after the first `renderedCallback`, after a child has already mounted, or — for `disconnectedCallback` — after the element is gone, so the teardown touches a detached component.

**When it bites you:** Most visibly on `async disconnectedCallback()`, where cleanup that was supposed to run before removal instead runs against a detached instance and silently does nothing.

**How to avoid it:**
- Keep the hook synchronous and call a separate async method from it: "To run async work from a lifecycle hook, call a separate async method from the synchronous hook" (L4118).
- Any state the async method sets must be safe to arrive late — the component may already have re-rendered or been removed.
- `scripts/check_lwc_lifecycle.py` rule **L7** flags an `async` hook.

---

## `errorCallback` Misses Programmatically Attached Handlers

**What happens:** A boundary component implements `errorCallback` and the team assumes the subtree is covered. It is not covered uniformly. The guide draws the line at how the handler was attached: "If you provide an event handler on an element such as for a button's `onclick` event, `errorCallback()` is called when the component encounters an error. However, if you assign the handler to your element via JavaScript such as by using `addEventHandler`, `errorCallback()` isn't called when the component encounters an error" (`lwc_guide create-lifecycle-hooks-error` L4167). So a handler declared as `onclick={handleSave}` in the template is inside the boundary; the same function wired up with `addEventListener` in `renderedCallback` is outside it, and its throw escapes as an unhandled error.

The scope is also narrower than "this subtree": the hook "captures errors in all the **descendent** components in its tree" (L4158). And a caught error is not recoverable in place — "When an error is thrown, `healthy-view` is unmounted and removed from the DOM" (L4162), so the boundary's template must have something else to render.

UNVERIFIED (2026-09-05): the guide documents descendant scope but does not state whether `errorCallback` catches an error thrown by the boundary component's own hooks, nor whether it catches errors from `async` code and promise rejections. Do not assume either.

**When it bites you:** Components that attach listeners programmatically (drag-and-drop, keyboard shortcuts, third-party library callbacks) and rely on a boundary they are not actually inside.

**How to avoid it:**
- Declare handlers in the template. The guide already recommends this generally: "It's best to add event listeners declaratively in an HTML template" (`create-lifecycle-hooks-rendered` L4137).
- Where a programmatic listener is unavoidable, wrap its body in an explicit `try/catch` — the boundary will not help.
- Give the boundary a fallback template that does not include the failed child; see `lwc/lwc-error-boundaries` for placement strategy.

---

## `renderedCallback` Re-Entry Has Two Non-Obvious Triggers

**What happens:** A guarded `renderedCallback` still loops, because the re-entry did not come from an obvious `this.x = ...`. Two documented cases:

1. **Wire configuration.** "Don't update a wire adapter configuration object property in `renderedCallback()`" (`lwc_guide create-lifecycle-hooks-rendered` L4139), restated in the wire reference: "Don't update a wire adapter configuration object property in `renderedCallback()` as it can result in an infinite loop" (`data-wire-service-about` L6408). Writing the reactive `$`-prefixed property re-provisions the wire, which re-renders, which re-enters the hook.
2. **Public properties.** "Don't update a public property or field in `renderedCallback()`" (L4140). Public properties used in a template are reactive (`reactivity-public` L2265).

A third, subtler case: LDS emits are not tied to your component's lifecycle at all — "An LDS wire can emit data multiple times without the component changing its configuration. LDS controls these emits, and they aren't related to the LWC component lifecycle" (`data-wire-service-about` L6471). So the hook can fire from data arrival you never triggered.

**When it bites you:** Any component that measures the DOM and feeds the measurement back into a wire filter or a public property — a common "responsive datatable" shape.

**How to avoid it:**
- Never assign to a wire-config property or an `@api` property inside `renderedCallback`.
- Do not assume the hook count tracks user interactions; the guide's own advice is "Don't depend on receiving data from a wire adapter at any specific point in your component lifecycle" (L6476).
- `scripts/check_lwc_lifecycle.py` rule **L4** flags any `this.x = ...` in an unguarded `renderedCallback`.

---

## A `render()` Template Fork Changes CSS Resolution and `this.refs`

**What happens:** A component imports two HTML files and returns one of them from `render()`. Two things then behave differently from a single-template component:

- **CSS stops resolving the way you expect.** "To reference CSS from an extra template, the CSS filename must match the filename of the extra template. For example, `templateTwo.html` can reference CSS only from `templateTwo.css`. It can't reference CSS from `miscMultipleTemplates.css` or `templateOne.css`" (`lwc_guide create-render` L1579). Styles written in the bundle's main stylesheet simply do not apply to the alternate template, and there is no error.
- **`this.refs` is rebound.** "`this.refs` refers to the most recently rendered template in a multi-template component. When the template changes, the `this.refs` object will change too" (`create-components-dom-work` L3089). A cached ref taken during the first template's render points at a detached element after the switch.

Also worth knowing before you take the fork at all: `render()` "is not technically a lifecycle hook. It is a protected method on the `LightningElement` class… The `render()` method must exist on the prototype chain" (`create-lifecycle-hooks-render` L4153), it can be called "before or after `connectedCallback()`" (L4149), and it must return a template reference — "the imported default export from an HTML file" (`create-render` L1573).

**When it bites you:** Compact/expanded card variants, print vs screen layouts, and anything ported from a framework where a render function is the normal way to branch.

**How to avoid it:**
- Prefer the conditional directives. The guide's own recommendation: "Although it's possible for a component to render multiple templates, we recommend using the `lwc:if|elseif|else` directives to render nested templates conditionally instead" (`create-render` L1572). See `lwc/lwc-conditional-rendering`.
- If you do fork, give each template its own matching `.css` file and re-read `this.refs` after every switch rather than caching it.
