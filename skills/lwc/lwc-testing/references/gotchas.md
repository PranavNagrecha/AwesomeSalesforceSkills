# Gotchas - LWC Testing

## Assertions Often Run Before Rerender Finishes

**What happens:** A click or emitted wire value appears to do nothing in the test even though the component works in the browser.

**When it occurs:** The test asserts immediately after an async boundary instead of waiting for the rerender cycle.

**How to avoid:** Use a small `flushPromises` helper or `await Promise.resolve()` after state changes that trigger rerender.

---

## Imperative Apex And Wired Apex Need Different Mocks

**What happens:** The test uses a wire adapter helper for an imperative import or tries to `mockResolvedValue` on a wire adapter.

**When it occurs:** The implementation path changed and the tests did not change with it.

**How to avoid:** Match the mocking strategy to the production contract: wire utilities for `@wire`, promise mocks for imperative imports.

---

## Base Component Markup Is Not The Live Platform DOM

**What happens:** A test reaches too deeply into the internal markup of a `lightning-*` base component and breaks after tooling or dependency updates.

**When it occurs:** Assertions depend on private base-component structure instead of the contract your component controls.

**How to avoid:** Assert your own component behavior, labels, events, and state, not the platform's internal stub structure.

---

## Missing DOM Cleanup Causes Cross-Test Leakage

**What happens:** Later tests fail or pass for strange reasons because earlier elements were left mounted in `document.body`.

**When it occurs:** The suite appends elements but skips `afterEach` cleanup.

**How to avoid:** Remove all mounted elements after every test and keep shared setup small.

---

## A Property Set Before `appendChild` Renders Synchronously — After It Does Not

**What happens:** Two tests that look identical behave differently. One asserts
straight after `appendChild` and passes; the other sets a property first, asserts,
and reads the old DOM. Developers conclude the test runner is flaky and start
sprinkling `await` everywhere, or worse, `setTimeout`.

**When it occurs:** `appendChild()` inserts the component and runs
`connectedCallback()` and `renderedCallback()` synchronously, so a property
assigned in `Object.assign(element, ...)` *before* the append is already in the
first render. A property assigned *after* the append schedules an asynchronous
rerender instead.

**How to avoid:** Set every known input before `appendChild` — the guide's own
attribute example uses `Object.assign(element, { backgroundColor: 'red' })` ahead
of the append (`lwc_guide unit-testing-using-jest-patterns L12606-L12613`). Reserve
`await Promise.resolve()` for changes that genuinely happen after mount: wire
emissions, clicks, resolved promises. "In cases where the property is set before
the `appendChild()` call, the component is rendered synchronously… you don't need
to wait for asynchronous updates or return a promise"
(`lwc_guide unit-testing-using-jest-create-tests L12505-L12506`).

---

## `flushPromises` Is A Local Helper, Not A Platform API

**What happens:** A generated test calls `await flushPromises()` and dies with
`flushPromises is not defined`, or a team copies a four-line helper into forty
files and each one flushes a different number of microtasks.

**When it occurs:** Any time a test is written from memory of another codebase.
**UNVERIFIED (2026-09-05): the string `flushPromises` does not appear anywhere in
the crawled Lightning Web Components Developer Guide** — every example in the
guide uses `await Promise.resolve()` (`L12485`) or
`return Promise.resolve().then(...)` (`L12556`, `L12600`).

**How to avoid:** Either use `await Promise.resolve()` directly, or define the
helper once and import it. `templates/lwc/component-skeleton/__tests__/componentSkeleton.test.js`
defines `async function flushPromises() { return Promise.resolve(); }` — treat that
as a repo convention with a known body, not as an API. One call flushes one
microtask; a click that awaits an Apex promise and then rerenders needs two.

---

## Emitting Before `appendChild` Silently Provisions Nothing

**What happens:** A wire test emits mock data, awaits, queries the DOM and finds
the empty state. No error, no warning — the assertion just fails on data the test
demonstrably supplied.

**When it occurs:** The `emit()` call is placed above `document.body.appendChild(element)`,
usually because a helper function was refactored to build and mount in one step and
the emit stayed where it was.

**How to avoid:** Emit only after the append. "The component receives updates about
data only when the component is connected to the DOM. After the component connects,
pass the mocked data to the `emit` function on the wire adapter"
(`lwc_guide unit-testing-using-wire-utility L12548`).

---

## A `bubbles: false` Event Is Invisible To A `document.body` Listener

**What happens:** `expect(handler).toHaveBeenCalled()` fails even though the
component demonstrably dispatches the event in the browser. The team adds
`bubbles: true, composed: true` to the production event just to make the test pass
— and now the event is part of every ancestor's API.

**When it occurs:** The test attaches the listener to `document.body` or to a
wrapper `div` instead of to the element under test. `Event.bubbles` and
`Event.composed` both default to `false`
(`lwc_guide events-propagation L5119-L5121`), so an event dispatched with
`this.dispatchEvent(new CustomEvent('x'))` is observable on the host element only.

**How to avoid:** Attach the listener to the element returned by `createElement`:
`element.addEventListener('contactsaved', handler)`. Change the production event's
propagation because the *component contract* needs it, never because a test is
looking in the wrong place. Assert the payload too —
`handler.mock.calls[0][0].detail` — since a "was called" assertion passes on an
event carrying `undefined`.

---

## Light DOM Components Have No `template`, So Shadow-Style Queries Break

**What happens:** A component is migrated to light DOM and its whole test file
starts throwing `Cannot read properties of null`. The component itself works.

**When it occurs:** "With shadow DOM, `LightningElement.prototype.template` returns
the component-associated shadow root. The template element isn't available to
components that use light DOM, so with light DOM,
`LightningElement.prototype.template` returns `null`"
(`lwc_guide create-light-dom L3269`). The component's own
`this.template.querySelector` calls break first; the test's queries follow.

**How to avoid:** In the component, replace `this.template.querySelector` with
`this.querySelector` (`L3270`); in the test, query the host element directly rather
than through a shadow root — light DOM content "can be retrieved… which is helpful
for third-party integrations and testing" (`L3266`). Also expect different event
behaviour: "With light DOM, events aren't retargeted… `event.target` returns the
button that triggered the event, instead of the containing component" (`L3274`), so
a `target`-based assertion that held under shadow DOM will now see a different
element. **UNVERIFIED (2026-09-05): the guide states `this.template` is null for
light DOM but does not state what `element.shadowRoot` returns inside a Jest test
for such a component — check it in your own suite before relying on either shape.**

---

## Asserting Into Base-Component Internals Breaks On A Dependency Bump

**What happens:** A green suite goes red after `npm update`, with no product change.
The failing assertion reaches inside `lightning-datatable` or `lightning-input` for
a class name, an internal `<button>`, or a rendered attribute.

**When it occurs:** The stubs in the sfdx-lwc-jest `lightning-stubs` directory
"match the API of the actual components but don't have all the functionality"
(`lwc_guide unit-testing-using-jest-patterns L12622`). They are a moving target, and
they are not the platform's markup. Two further traps: "No events are fired from
these mocks but you can call `dispatchEvent()` against them" (`L12627`), and
"Lightning base components have some properties that aren't reflected as attributes
in the DOM" (`L12626`) — so `getAttribute('icon-position')` returns null on a
property that is definitely set.

**How to avoid:** Assert on the stub's public API surface — the property you set,
the event you dispatch at it, the `data-id` you own. If you need a base component to
behave rather than merely exist, map it to a custom stub with `moduleNameMapper`
(`L12637`, `L12646-L12647`) and own that behaviour explicitly. And never assert on
LWC's generated scoping attributes: from API version 59.0 they are obfuscated
`lwc-<hashstring>` strings (`lwc_guide create-components-css-antipatterns L1917, L1919`).

---

## A Label Import Resolves To Its Path, Not Its Text

**What happens:** An assertion expecting the org's message gets the literal string
`c.Contact_Save_Error`. Someone "fixes" it by asserting on the path — and the test
now passes forever regardless of what the component renders.

**When it occurs:** In Jest, "we use a jest-transformer to convert the
`@salesforce/label` import statement into a variable declaration. The value is set
to the label path. By default, `myImport` is assigned a string value of
`c.specialLabel`" (`lwc_guide unit-testing-using-jest-patterns L12650`). Jest tests
don't connect to an org, so there is no translated text to fetch.

**How to avoid:** Mock the label to a known string:
`jest.mock('@salesforce/label/c.Contact_Save_Error', () => ({ default: 'Could not save' }), { virtual: true })`
(`L12650-L12655`) and assert against that. The same applies to every `@salesforce/*`
scoped module the component imports — `@salesforce/schema`, `@salesforce/user/Id`,
`@salesforce/apex`. The `{ virtual: true }` third argument is not optional: these
modules are compiler-generated and have no file for Jest to resolve.

---

## `sf force lightning lwc test setup` Is Not Optional Plumbing

**What happens:** A developer hand-adds `@salesforce/sfdx-lwc-jest` to
`package.json`, writes a `__tests__` folder, and then a `sf project deploy` fails
on the test files, or `npm run test:unit` reports a missing script.

**When it occurs:** The CLI command does three separate things: it "creates the
necessary configuration files and installs the `sfdx-lwc-jest` package"
(`lwc_guide unit-testing-using-jest-installation L12250`), it adds the script
entries to the `scripts` block of `package.json` (`L12253`), and it writes the
`__tests__` glob into `.forceignore` so push/pull/transform commands skip the folder
(`lwc_guide unit-testing-using-jest-create-tests L12329-L12330`). Hand-installing
skips the last two.

**How to avoid:** Run `sf force lightning lwc test setup` from the top-level
directory of *each* DX project — "sfdx-lwc-jest works in Salesforce DX projects
only" (`L12244`). If your environment can't run the CLI, reproduce all three
outcomes deliberately; the checker in this skill flags the missing `.forceignore`
entry and the untested bundles.
