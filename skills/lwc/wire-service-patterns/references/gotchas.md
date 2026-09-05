# Gotchas — Wire Service Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.
Line citations are `lwc_guide <page-slug> L<n>` against the crawled Lightning Web Components
Developer Guide.

## An Undefined Reactive Parameter Looks Like A Silent Failure

**What happens:** The component renders, but no request is made and the developer assumes the wire service is broken. There is nothing in `error` either — the guide is explicit that "before the wire fires for the first time, both `data` and `error` are undefined. The wire isn't in an error state, it just hasn't fired yet" (`data-error L6572`).

**When it occurs:** A dynamic parameter such as `$recordId` or a parent-provided value is still `undefined`. "Properties in the `{adapterConfig}` object can't be `undefined`. If a property is undefined, the wire service doesn't provision data, and both `data` and `error` stay `undefined`" (`data-wire-service-about L6408`).

**How to avoid:** Treat wire configuration completeness as part of the component contract and guard for missing inputs explicitly. In Chrome DevTools with custom formatters on, inspect the wired property: `isDataProvisionedForConfig` tells you whether a config was ever reported (`debug-wire L12189`).

---

## `null` Fires The Wire; `undefined` Does Not

**What happens:** A developer initialises a reactive param to `null` to mean "nothing selected yet", and the Apex method runs anyway — with a null argument it was never written to survive. Initialising to `undefined` instead produces the opposite surprise: the method never runs and the component sits empty.

**When it occurs:** Any wired Apex method with a `$`-prefixed param. "If a parameter value is `null`, the method is called. If a parameter value is `undefined`, the method isn't called" (`apex-wire-method L7104`).

**How to avoid:** Pick the sentinel deliberately. Use `undefined` when the wire must not fire, `null` when it must fire and the server should handle the empty case — and then actually handle `null` in the Apex method, as in `references/code-examples.md` § 1.

---

## Nesting `$` Inside An Array Turns It Into A Literal String

**What happens:** `@wire(getStuff, { ids: ['$accountIds'] })` compiles, deploys, and passes the seven-character string `$accountIds` to the server. The wire is not reactive and the query returns nothing or errors on a bad Id.

**When it occurs:** Any config where the reactive value belongs inside a collection. "Use the `$` prefix for top-level values in the configuration object. Nesting the `$` prefix such as in an array like `['$accountIds']` makes it a literal string, which is not dynamic or reactive" (`data-wire-service-about L6443`).

**How to avoid:** Build the whole array as one reactive property and pass `'$parameterObject'` at the top level — the shape the `getRecords` guidance uses for dynamic record Ids (`reference-wire-adapters-records L15217`). This skill's checker flags `['$` and `["$` inside a `@wire` config.

---

## `refreshApex()` On A Non-Apex Wire Adapter Is Deprecated

**What happens:** A component calls `refreshApex(this.wiredRecord)` after an imperative write and the `getRecord` wire does not update — or updates today and stops updating later.

**When it occurs:** Whenever `refreshApex` is aimed at an LDS wire that is not backed by an Apex method. "The use of `refreshApex` to refresh data from non-Apex wire adapters is deprecated. To refresh record data returned by a non-Apex wire adapter, use `notifyRecordUpdateAvailable(recordIds)` instead" (`data-guidelines L5355`).

**How to avoid:** Route by adapter. `refreshApex()` for Apex wires (`apex-result-caching L7263`), `notifyRecordUpdateAvailable()` for UI API wires (`reference-notify-record-update L15370`), `refreshGraphQL()` for GraphQL (`data-wire-service-about L6478`). A component doing both kinds of read after one write needs two calls, not one.

---

## `refreshApex()` Rejects Anything But The Provisioned Object

**What happens:** `refreshApex(this.accounts.data)` runs without throwing and refreshes nothing, so the UI stays stale and the bug looks like a caching problem.

**When it occurs:** With the property form, when someone reaches for `.data`; with the function form, when the provisioned object was destructured on arrival and never retained. "The parameter you refresh with `refreshApex()` must be an object that was previously emitted by an Apex `@wire`" (`apex-result-caching L7264`).

**How to avoid:** In the function form, assign the whole `result` to a field *before* destructuring it — the shape in `references/code-examples.md` § 2. Note also that the resolved value of the returned Promise is meaningless: "the `@wire` has fresh data when the Promise resolves, but the actual value to which the Promise resolves is meaningless" (`apex-result-caching L7266`).

---

## Wired Data Is Behind A Read-Only Membrane, And Only Some Environments Say So

**What happens:** `this.rows.data.push(newRow)` or `row.isUrgent = true` on a wired row throws `Uncaught Error: Invalid mutation: Cannot set "msg" on "[object Object]". "[object Object]" is read-only.` (`create-components-data-flow L2021`) — but the message surfaces in the browser console, not in a Jest assertion, so it can reach production untested.

**When it occurs:** Any in-place edit, sort, or annotation of `@wire` (or `@api`) output. "Production mode also uses JavaScript proxies for … data that is provisioned through decorators `@api`, `@wire`, and `@track`. The `@api` and `@wire` decorated properties are considered read-only" (`debug-production-mode L12073`).

**How to avoid:** Shallow-copy at the boundary — `data.map((row) => ({ ...row, extra }))`. Remember shallow means shallow: "the values of the nested objects are not copied" (`create-components-data-flow L2026`), so a nested `fields` object is still frozen after a top-level spread.

---

## Async Server-Side Changes Never Re-Evaluate The Wire

**What happens:** A record-triggered flow or an Apex trigger updates the record a moment after the user's save; the component shows the pre-trigger values until the page is reloaded.

**When it occurs:** "If you asynchronously change a record using an Apex trigger or an auto-launched flow, the wire adapter won't be re-evaluated" (`data-wire-service-about L6477`).

**How to avoid:** Refresh once *after* the mutating operation completes, from the client that initiated it. Do not reach for polling: "Don't use refresh functions in a polling pattern with `setTimeout()` or `setInterval()`, as polling creates unnecessary server load" (`data-wire-service-about L6478`); the GraphQL pages add the fallback — "provide an explicit user-driven refresh action, such as a refresh button" (`reference-refreshgraphql L13657`).

---

## `getRecords` Can Return HTTP 200 With Failed Subrequests

**What happens:** The `error` branch never fires, `data` arrives, and one of the requested records silently has no fields — the component renders blanks for it.

**When it occurs:** Batch reads where one subrequest fails. "If the response status returns a 200 success code but a subrequest returns a `statusCode` of 400 or another non-200 error code, the network response returns `hasErrors:true`, but this property isn't returned as part of `data`" (`reference-wire-adapters-records L15266`).

**How to avoid:** Inspect `data.results[].result` per subrequest — a success carries record data, a failure carries `errorCode` and `message` (`reference-wire-adapters-records L15267-L15269`). Also watch the size ceiling: UI API composes a SOQL query for the batch and "this SOQL query has a limit of 100k characters" (`reference-wire-adapters-records L15219`).

---

## The `error.body` Shape Changes With The Adapter

**What happens:** `error.body.message` is `undefined` for a `getRecord` failure, so the component renders "Unknown error" for every UI API read problem while working correctly for Apex ones.

**When it occurs:** Four documented shapes, only two of which are objects: "UI API read operations, such as the `getRecord` wire adapter, return `error.body` as an array of objects. UI API write operations … return `error.body` as an object … Apex read and write operations return `error.body` as an object. Network errors, such as an offline error, return `error.body` as an object" (`data-error L6568-L6571`).

**How to avoid:** Branch on `Array.isArray(error.body)` before reading `.message`, as the guide's own sample does (`data-error L6555`). In a real org use the shared `errorUtils` normaliser from `lwc/lwc-error-boundaries` rather than repeating the branch per component.

---

## Lightning Data Service Does Not Cover Everything You Can Query

**What happens:** A `getRecord` wire on a Task, an Event, or a custom metadata type errors or is impossible to configure, and the developer concludes the wire service is broken.

**When it occurs:** "Lightning Data Service supports all custom objects and all the standard objects that User Interface API supports. **Custom metadata types are not supported**" (`data-ui-api L5379`), and Apex is the documented escape hatch "to work with objects that aren't supported by User Interface API, like Task and Event" (`data-guidelines L5357`). `Knowledge__kav` has its own carve-out: it "cannot be imported in a custom component" from `@salesforce/schema`; pass the field as a string instead (`data-wire-service-about L6441`).

**How to avoid:** Check the object before designing the wire. If it is unsupported, the choice is a cacheable Apex wire, not a workaround on the UI API adapter — and Apex and LDS do not share a cache, so mixing them on the same data can return inconsistent values (`data-guidelines L5364`).

---

## Updating A Wire Config Property In `renderedCallback()` Loops Forever

**What happens:** The component re-renders continuously and the browser tab pins a core.

**When it occurs:** A reactive config value is assigned inside `renderedCallback()`. New data is provisioned, the template changes, `renderedCallback()` fires again, the value is assigned again. "Don't update a wire adapter configuration object property in `renderedCallback()` as it can result in an infinite loop" (`data-wire-service-about L6408`).

**How to avoid:** Set reactive config from `connectedCallback()`, an `@api` setter, or an event handler — never from a render hook. This skill's checker flags assignment to a `$`-referenced property inside `renderedCallback`.

---

## Wire Timing Does Not Follow Lifecycle Intuition

**What happens:** Developers expect data to be available at a specific lifecycle hook and then write brittle code around that assumption.

**When it occurs:** Components tie provisioning expectations to `connectedCallback()` or `renderedCallback()`. The documented order is constructor → empty `{data: undefined, error: undefined}` placeholder → `connectedCallback()`/`render()`/`renderedCallback()` → data arrives → render again if the template consumes it (`data-wire-service-about L6468-L6470`). A wired *function* is looser still: "the function is invoked whenever a value is available, which can be before or after the component is connected or rendered" (`data-wire-service-about L6464`).

**How to avoid:** Treat wire emissions as asynchronous state updates managed by the framework. "Don't depend on receiving data from a wire adapter at any specific point in your component lifecycle" (`data-wire-service-about L6476`).

---

## Refresh Strategy Is Easy To Forget After Writes

**What happens:** The component successfully updates data, but the UI remains stale because the wired read is never refreshed.

**When it occurs:** Writes are performed imperatively or asynchronously by other automation. Apex data in particular is unmanaged: "Unlike Lightning Data Service data, Apex data is not managed; you must refresh the data" (`data-guidelines L5354`).

**How to avoid:** Decide up front which caches a write invalidates and refresh each with its own function. Only call `notifyRecordUpdateAvailable()` "if you expect any relevant data to be updated in the LDS cache" (`data-guidelines L5354`) — it is a signal, not a page reload.
