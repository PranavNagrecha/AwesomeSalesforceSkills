# Well-Architected Notes — LWC Error Boundaries

**Reliability:** the value of a boundary is the size of the blast radius it defines, and
that is a placement decision rather than a coding one. Because the framework unmounts the
component that threw, a boundary at the page root converts every localised failure into a
blank page — the outcome boundaries exist to prevent. One boundary per independently useful
unit is the design; the test is whether the user can still do something on the page after
that subtree disappears.

**Reliability, second order:** a boundary narrows what a failure costs, it does not reduce
how often failures happen, and it covers less than most implementations assume. It sees
errors thrown in descendants' lifecycle hooks and in handlers declared in a template. It
does not see programmatically attached handlers, rejected promises, or wire adapter
failures — the last of which are provisioned onto the wired property's `error` member
instead. A component that leaves all three to the boundary is not protected; it is
silent.

**Observability:** catching without recording is the failure mode that survives review,
because the page looks better afterwards. A silent boundary removes the user's only reason
to report the problem while removing none of the problem. Instrumentation belongs on the
wrapper rather than on each widget, so it arrives with the pattern instead of depending on
whoever writes the next tile — and the reporting call itself needs a `catch`, since a
logger that throws inside `errorCallback` is a failure inside the failure handler.

**User Experience:** the fallback is rendered by a component whose subtree has already
failed, which is the worst possible moment to depend on anything. Static markup and a base
class or two; no wires, no imperative calls, no nested custom components, no formatting of
the data that may be the reason the boundary fired. Every dependency in the fallback is a
new way for the error state itself to error.

**Reliability, the shape problem:** a boundary that catches four different failure
mechanisms and reads them one way is a boundary that reports three of them wrong. The body
of an error response depends on which API produced it — array for a UI API read, object for
a UI API write, object for Apex, object for a network failure — and what `errorCallback`
itself receives is a native JavaScript Error with no `body` at all. Normalising once, in a
module both the boundary and its children import, is what makes a single fallback and a
single telemetry record honest across all of them.


## Official Sources Used

Line numbers are against the crawled Lightning Web Components Developer Guide
(`lwc_guide <page-slug> L<n>`); the URL is the page each citation comes from.

- `errorCallback()` — the hook captures errors "in all the descendent components in its
  tree" from "lifecycle hooks or during an event handler declared in an HTML template"
  (L4158); placement is explicitly the author's call, including wrapping the whole app
  (L4160); the throwing subtree "is unmounted and removed from the DOM" (L4162, L4165);
  `error` is a native Error and `stack` is a string (L4164); programmatically assigned
  handlers are not caught (L4167) —
  https://developer.salesforce.com/docs/platform/lwc/guide/create-lifecycle-hooks-error.html
- Handle Errors in Lightning Data Service — wire failures are provisioned onto the wired
  property's `error` member and the else-if branch is the recommended shape (L6542–L6544);
  the `FetchResponse` shape `body` / `ok` / `status` / `statusText` (L6545–L6551); the
  array-vs-object branch the normaliser copies (L6555–L6557); **the four body shapes** —
  UI API read = array, UI API write = object with object- and field-level errors, Apex =
  object, network = object (L6568–L6571); `data` and `error` both undefined before the
  first fire (L6572); try/catch handles synchronous code only, so async work needs the
  catch inside the callback (L6513, L6524–L6525) —
  https://developer.salesforce.com/docs/platform/lwc/guide/data-error.html
- Work with Errors — an unhandled error propagates to the parent and then to the enclosing
  app, producing the "A Component Error has occurred!" / "Something went wrong" modal;
  unhandled *async* errors go to the browser console instead (L7732–L7733) —
  https://developer.salesforce.com/docs/platform/lwc/guide/data-error-types.html
- Handle Errors from Apex — an unhandled Apex exception surfaces the Apex class name in
  `body.stackTrace` (L7518); `AuraHandledException` returns the custom message and omits
  `body.stackTrace` (L7521) —
  https://developer.salesforce.com/docs/platform/lwc/guide/apex-error-handling.html
- Pass Markup into Slots — the `<slot>` mechanism the wrapper depends on; slotted content
  is not in the boundary's shadow tree, so `this.template.querySelector` cannot see it
  (L2160–L2161); a conditional slot is valid under `lwc:if` and warns under `if:true`
  (L2169–L2172) —
  https://developer.salesforce.com/docs/platform/lwc/guide/create-components-slots.html
- Render DOM Elements Conditionally / HTML Template Directives — `lwc:if` removes and
  inserts DOM elements on a truthy/falsy change (L1506); `lwc:if` takes simple dot notation
  only, so `!condition` must be a getter (L19510); `lwc:elseif` / `lwc:else` must be
  immediately preceded by a sibling conditional (L19506, L19512); `key` must be a string or
  a number (L19541) —
  https://developer.salesforce.com/docs/platform/lwc/guide/create-conditional.html and
  https://developer.salesforce.com/docs/platform/lwc/guide/reference-directives.html
- Toast Notifications / Base Components Usage Patterns — `lightning/toast` is the preferred
  module; `lightning/platformShowToastEvent` is unsupported on LWR Experience Cloud sites,
  standalone apps, and Aura site login pages (L10448–L10452, L4773) —
  https://developer.salesforce.com/docs/platform/lwc/guide/use-toast.html
- Write Jest Tests / Jest Test Patterns — `__tests__` layout and `.forceignore`
  (L12328–L12331); jsdom reset between tests (L12363); `appendChild` runs
  `connectedCallback` and `renderedCallback` (L12378); `element.shadowRoot` is the test
  equivalent of `this.template` (L12379); rerender on property change is asynchronous
  (L12590); base-component mocks render but fire no events (L12622, L12627) —
  https://developer.salesforce.com/docs/platform/lwc/guide/unit-testing-using-jest-create-tests.html
- XML Configuration File Elements — every component must specify an `apiVersion` from
  Spring '25 (L18700); `isExposed` false keeps a module out of the builders (L18711) and
  `isExposed` true needs at least one `<target>` (L18712); `lightningCommunity__Default` is
  the Experience Builder target (L18722) —
  https://developer.salesforce.com/docs/platform/lwc/guide/reference-configuration-tags.html
