# Well-Architected Notes — LWC Offline And Mobile

## Relevant Pillars

### User Experience

Mobile components succeed or fail on touch ergonomics, constrained space, and graceful fallback when device-specific features are unavailable. The platform also removes affordances the desktop design assumed: pull-to-refresh does not reach custom components, and LWC quick actions do not appear in the Salesforce mobile app at all.

### Reliability

Intermittent connectivity, background/resume behavior, and container differences make reliability a primary design concern. The reliability boundary is drawn at the data module — a component fed by Apex has no cache to fall back on, and only one of the two GraphQL wire modules participates in Mobile Offline.

### Performance

Mobile users are more sensitive to payload size, unnecessary rerenders, and interaction lag than desktop users. Polling a refresh in place of a user-driven control creates server load the guide explicitly warns against.

## Architectural Tradeoffs

- **One component for every container vs specialized experience:** Reuse is attractive, but some mobile tasks need deliberate simplification or gating — and some base components are simply not supported on the smaller surface, which makes the "one component" option unavailable rather than merely worse.
- **Deep device integration vs broad portability:** The more the component relies on mobile APIs, the more important runtime detection and fallback become. Note that the availability check and the error handler are two obligations, not one.
- **Server dependence vs offline tolerance:** Rich server-driven behavior is easier to build, but it is fragile for mobile users with inconsistent connectivity.
- **Current module vs offline-capable module:** The GraphQL wire module that supports Mobile Offline is the one the guide marks deprecated. Choosing correctness over recency here means documenting the choice, because the next reader's instinct will be to reverse it.
- **Form-factor breadth now vs later:** Supported form factors can only be widened after the component is in use on a Lightning page, never narrowed — so an over-broad declaration is a one-way door.

## Anti-Patterns

1. **Assuming device APIs exist everywhere** — unsupported environments need intentional fallback behavior.
2. **Treating `isAvailable()` as error handling** — permission denial and service errors come back from the call, not the check.
3. **Designing no reconnect or resume path** — mobile sessions are routinely interrupted, and the platform's refresh gesture will not rescue you.
4. **Reusing dense desktop interaction models unchanged** — touch ergonomics, small screens, and an unsupported datatable all point the same way.
5. **Letting module recency outrank the offline requirement** — the newer GraphQL module is the one that does not work offline.

## Official Sources Used

- Lightning Web Components Developer Guide, `lightning/mobileCapabilities` Module — https://developer.salesforce.com/docs/platform/lwc/guide/reference-lightning-mobilecapabilities.html (mobile capability APIs are available only when a component runs in a supported mobile app on a mobile device; SKILL.md Core Concepts, gotchas 7)
- Lightning Web Components Developer Guide, `isAvailable()` and `scan(options)` for BarcodeScanner — https://developer.salesforce.com/docs/platform/lwc/guide/reference-lightning-barcodescanner-isavailable.html and .../reference-lightning-barcodescanner-scan.html (the guard is not required and not sufficient; `scan()` resolves an array; the OS scanner interface stays up until `dismiss()`; user cancel arrives as a rejection — gotchas 5, 6, 7, 12)
- Lightning Web Components Developer Guide, GraphQL API Wire Adapter comparison — https://developer.salesforce.com/docs/platform/lwc/guide/reference-graphql-intro.html and .../reference-refreshgraphql.html (`lightning/uiGraphQLApi` supports Mobile Offline and `lightning/graphql` does not, while the v1 module is marked deprecated; gotcha 1, code-examples.md §1, decision guidance)
- Lightning Web Components Developer Guide, Handle Errors in Lightning Data Service — https://developer.salesforce.com/docs/platform/lwc/guide/data-error.html (an error is returned when the record isn't in the cache and the server is offline; network errors return `error.body` as an object while UI API reads return an array; gotcha 4 and the `reduceErrors` helper)
- Lightning Web Components Developer Guide, Work with Salesforce Data guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html (Apex shares no data cache or data store with LDS, so Apex and wire data can be inconsistent online and offline; gotcha 10, anti-pattern 5)
- Lightning Web Components Developer Guide, Form Factors and the `lightning__RecordAction` target reference — https://developer.salesforce.com/docs/platform/lwc/guide/use-config-form-factors.html and .../targets-lightning-record-action.html (`supportedFormFactor` accepts only Large and Small; supported form factors can only be increased once the component is in use; `Small` is unsupported for `lightning__RecordAction` because LWC quick actions don't appear in the Salesforce mobile app — gotchas 8, 9)
- Lightning Web Components Developer Guide, Lightning App Builder configuration tips — https://developer.salesforce.com/docs/platform/lwc/guide/use-config-for-app-builder-tips.html (pull to refresh doesn't work for custom Lightning web components in the Salesforce mobile app; gotcha 3 and the explicit refresh control in code-examples.md §2)
- Lightning Web Components Developer Guide, Display Record Data in a Table — https://developer.salesforce.com/docs/platform/lwc/guide/data-table-vs-tree-grid.html (`lightning-datatable` and `lightning-tree-grid` aren't supported on mobile devices; gotcha 2, checker rule MX5)
- Lightning Web Components Developer Guide, Write Jest Tests for Wire Service and Jest Test Patterns — https://developer.salesforce.com/docs/platform/lwc/guide/unit-testing-using-wire-utility.html and .../unit-testing-using-jest-patterns.html (`@salesforce/sfdx-lwc-jest` adapters, the `__tests__/data/<adapter>.json` convention, and `moduleNameMapper` for custom mocks; code-examples.md §3)
- Lightning Web Components Developer Guide, Run a Live Component Preview and Debug Mobile Components — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-test-components.html and .../debug-mobile.html (Live Preview previews only Lightning apps in a mobile environment; `--device-type` accepts desktop/ios/android; Device Mode is not a substitute for a real device — gotcha 11, code-examples.md §6)

<!-- UNVERIFIED (2026-09-05): the Mobile and Offline Developer Guide is named by the LWC guide as
     "an essential companion" for mobile work (mobile-extensions L547, mobile L4515,
     use-mobile-capabilities L10725) but is not in the crawled corpus. Anything this package says
     about Briefcase priming rules, metaschema directives, or offline sync internals is marked at
     the point of the claim and belongs to lwc/lwc-mobile-offline-and-briefcase. -->
