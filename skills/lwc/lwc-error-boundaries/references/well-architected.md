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

## Official Sources Used

- errorCallback() — what it captures in descendants, the unmount-on-error behaviour, and the exclusion of programmatically assigned handlers — https://developer.salesforce.com/docs/platform/lwc/guide/create-lifecycle-hooks-error.html
- Lifecycle Hooks — where `errorCallback` sits relative to `connectedCallback` and `renderedCallback` — https://developer.salesforce.com/docs/platform/lwc/guide/create-lifecycle-hooks.html
- Handle Errors — wire failures provisioned onto the `error` property — https://developer.salesforce.com/docs/platform/lwc/guide/data-error.html
- Work with Errors — the `FetchResponse` shape (`body`, `status`, `statusText`) — https://developer.salesforce.com/docs/platform/lwc/guide/data-error-types.html
- Pass Markup into Slots — the `<slot>` mechanism the wrapper pattern depends on — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-slots.html
