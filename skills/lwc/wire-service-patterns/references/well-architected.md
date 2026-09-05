# Well-Architected Notes — Wire Service Patterns

## Relevant Pillars

### Performance

The wire service is a performance tool when used well because it aligns with LDS caching and reactive data provisioning. LDS loads a record once no matter how many components on the page use it, bulkifies and dedupes server calls, and serves from a client-side cache whose lifetime is deliberately undocumented and subject to change — which is precisely why a component must never encode an assumed cache duration and must refresh explicitly when it knows a value is stale.

### Reliability

Reactive parameters, refresh behavior, and immutable handling all determine whether the component shows trustworthy data. The reliability failure mode here is silent: an undefined config property produces no data *and* no error, so a broken wire and a slow wire look identical from the outside. Mixing Apex and LDS reads over the same records is a second silent failure — the two do not share a cache and can disagree.

### User Experience

Users experience stale data as a broken app. A deliberate wire strategy keeps the UI current without unnecessary loading or duplicate calls. The three-state discipline — loading, empty, error — is the UX half of the same design: because both `data` and `error` are `undefined` before the first emission, a component that treats "no data" as "failed" shows an error panel to every user for the first few hundred milliseconds.

## Architectural Tradeoffs

- **Wire convenience vs imperative control:** Wire is excellent for reads, while imperative patterns are clearer for writes and explicit user actions. The `cacheable=true` annotation makes this a hard boundary rather than a preference: a method that mutates cannot be cacheable, and a method that is not cacheable cannot be wired.
- **UI API simplicity vs custom Apex flexibility:** UI API is safer and cheaper for standard record access, while Apex is justified only for logic UI API cannot express — unsupported objects such as Task and Event, criteria-based loading, and transactional multi-record work. The cost of choosing Apex is that its data is unmanaged and every refresh becomes the component's responsibility.
- **Single-purpose wires vs GraphQL read models:** GraphQL can simplify complex reads and returns only the fields queried, where `getRecord` also returns child relationships and layout types. It introduces a different response shape (`errors`, not `error`) and should stay focused on read scenarios.
- **`fields` vs `layoutTypes`:** Naming fields is faster and predictable; a layout hands field selection to the administrator and obliges the component to render whatever the layout carries for the context user. Choose a layout only when that delegation is the actual requirement.
- **Refresh precision vs refresh breadth:** `refreshApex()` re-runs one wire; `notifyRecordUpdateAvailable()` re-emits to every wire on those records across every instantiated component. The broader call is correct more often and costs more — and neither is a substitute for the other, since `refreshApex` against a non-Apex adapter is deprecated.

## Anti-Patterns

1. **Using custom Apex for ordinary record reads** — needless maintenance and weaker default platform protections.
2. **Mutating wired data directly** — blurs immutable input and local state, and throws at runtime rather than at compile time.
3. **Assuming wires auto-refresh after every server-side change** — stale UI remains until an explicit refresh strategy exists; a trigger or auto-launched flow never re-evaluates a wire.
4. **Polling a refresh function on a timer** — creates unnecessary server load; a user-driven refresh action is the documented alternative when the mutation's completion cannot be detected.
5. **Treating "no data" as "error"** — before the first emission the wire is in neither state.

## Official Sources Used

- Understand the Wire Service — https://developer.salesforce.com/docs/platform/lwc/guide/data-wire-service-about.html (the immutable stream and read-only rule; `adapterConfig` properties cannot be `undefined`; `$` is top-level only and nesting it produces a literal string; the constructor → placeholder → `connectedCallback`/`render`/`renderedCallback` → data order; async triggers and flows do not re-evaluate a wire; refresh once and never poll; the two-hour delay on name cascade that also affects `<objects>` in `meta.xml`)
- Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html (LDS supports all custom objects and the standard objects UI API supports, but not custom metadata types; Apex data is unmanaged; `refreshApex` on a non-Apex wire adapter is deprecated; Apex and LDS do not share a cache; the four documented reasons to drop to Apex, including Task and Event)
- Lightning Data Service — https://developer.salesforce.com/docs/platform/lwc/guide/data-ui-api.html (one record load shared across every component on the page; bulkify/dedupe; the client cache lifetime is subject to change; UI API responses respect CRUD, FLS and sharing)
- Wire Apex Methods to Components — https://developer.salesforce.com/docs/platform/lwc/guide/apex-wire-method.html (`@AuraEnabled(cacheable=true)` is required to wire a method; a `null` parameter calls the method while `undefined` does not; params must be an object, not a bare value, and maps are unsupported; decimals over 15 digits of precision serialise as JSON strings)
- Client-Side Caching of Apex Method Results — https://developer.salesforce.com/docs/platform/lwc/guide/apex-result-caching.html (a cacheable method must only get data; `refreshApex()` must receive an object previously emitted by an Apex `@wire`; its Promise resolves fresh but its resolved value is meaningless; use `notifyRecordUpdateAvailable()` after imperative Apex)
- Handle Errors in Lightning Data Service — https://developer.salesforce.com/docs/platform/lwc/guide/data-error.html (`FetchResponse` shape with `body`/`ok`/`status`/`statusText`; UI API reads return `error.body` as an array of objects while UI API writes, Apex, and network errors return it as an object; before the first emission the wire is not in an error state)
- getRecord — https://developer.salesforce.com/docs/platform/lwc/guide/reference-wire-adapters-record.html (`fields` or `layoutTypes` is required and they are alternatives; polymorphic fields are unsupported in `fields`; `optionalFields` degrade instead of erroring; read `recordTypeId`, never `recordTypeInfo`)
- getRecords — https://developer.salesforce.com/docs/platform/lwc/guide/reference-wire-adapters-records.html (batch reads across objects; the composed UI API SOQL query has a 100k-character limit; an HTTP 200 can carry failed subrequests whose `hasErrors` flag is not part of `data`)
- notifyRecordUpdateAvailable(recordIds) — https://developer.salesforce.com/docs/platform/lwc/guide/reference-notify-record-update.html (supersedes `getRecordNotifyChange`; considers the record data wired by all instantiated components; returns a Promise resolved after LDS has pushed updates)
- getPicklistValues — https://developer.salesforce.com/docs/platform/lwc/guide/reference-wire-adapters-picklist-values.html (both `recordTypeId` and `fieldApiName` are required; feed `defaultRecordTypeId` from `getObjectInfo` through a reactive variable; `012000000000000AAA` is the master record type; `value` is the untranslated API name and `label` is translated)
- Write Jest Tests for Wire Service — https://developer.salesforce.com/docs/platform/lwc/guide/unit-testing-using-wire-utility.html (three mock adapters; `emit()` on the imported adapter after the component is appended to the DOM; snapshot the mock JSON from the UI API resource; registering the adapter is the pre-Spring '21 shape and is no longer recommended)
- Secure Apex Classes — https://developer.salesforce.com/docs/platform/lwc/guide/apex-security.html (API 67.0+ runs Apex in user mode by default; `WITH USER_MODE` for SOQL; `with sharing` is the implicit default for an `@AuraEnabled` class but should be declared explicitly)
- lightning/graphql Wire Adapter (v2) — https://developer.salesforce.com/docs/platform/lwc/guide/reference-lightning-graphql-module.html (v2 supersedes `lightning/uiGraphQLApi` v1; the adapter returns `errors` for GraphQL specification compatibility; `refresh()` must not be polled)
