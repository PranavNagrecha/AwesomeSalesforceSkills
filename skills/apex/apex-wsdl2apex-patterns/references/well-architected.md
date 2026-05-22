# Well-Architected Notes — Apex WSDL-to-Apex Patterns

## Relevant Pillars

### Reliability

Outbound SOAP integrations fail in three categorically different ways and the wrapper layer must distinguish them:

- **Transport failure** (timeout, DNS, TLS) — surfaces as `System.CalloutException`. Usually transient; retry-able with exponential backoff.
- **SOAP fault** (HTTP 500 + `<faultcode>` / `<faultstring>`) — surfaces as `System.WebServiceCalloutException`. Indicates a business-rule rejection or input-validation failure; retry without changing the payload is futile.
- **Successful HTTP envelope with a business-error payload** — no exception at all; the response element carries an `ErrorCode` or `Status="Failed"`. The wrapper must inspect the response, not just trust the absence of an exception.

Wrappers that collapse these three into a single error path lose the information needed to decide retry vs. dead-letter vs. user-visible message. The two-catch ladder plus response inspection is the minimum reliable pattern.

### Security

The Named Credential / External Credential is the only correct place for SOAP integration auth. Mixing strategies (NC for endpoint, `inputHttpHeaders_x` for Authorization) leads to silent header strip-out — auth can succeed using the wrong credentials, which is the worst possible failure mode in a multi-tenant vendor system because it can manifest as cross-tenant data access. mTLS attaches at the External Credential / Certificate layer, not via `clientCertName_x` directly — this keeps cert rotation independent of code deploys.

Hand-edited stubs are a security smell: a regen rolls them back, and there's no audit trail of what was changed or by whom. Treat the generated stub as build artifact; persist customization to the wrapper or the WSDL.

### Adaptability

The wsdl2apex toolchain is **brittle on schema change**. A vendor adding a single new `xsd:choice` somewhere in the WSDL fails the entire regen. A new required field on a type ripples into every consumer of that type. Two architectural moves limit the blast radius:

- **Pin the WSDL version** in source control alongside the cleaned WSDL. A change to the vendor's WSDL is a code change, not a runtime surprise.
- **Wrap the stub in a service class** with method signatures driven by the calling layer's needs, not the WSDL's element shape. Renames and field additions in the stub do not require ripple-changes through the codebase.

The architectural decision to use SOAP is itself an adaptability tradeoff. New integrations should default to REST unless the vendor truly requires SOAP (i.e. there is no REST surface). Existing SOAP integrations are reasonable to maintain; migrating them to REST purely for technology preference adds risk without proportional benefit.

---

## Architectural Tradeoffs

### wsdl2apex vs. hand-authored SOAP envelope with `Http.send()`

The wsdl2apex tool produces typed stubs that are pleasant to call (`stub.GetQuote(subtotal, state)` vs. building XML by hand). The cost: parser limitations (1 MB cap, no SOAP 1.2, no `xsd:choice` / `xsd:any`), regen brittleness, and the 1 MB compiled-class ceiling. For WSDLs that defy pre-processing — large, deeply polymorphic, SOAP 1.2 only — the practical fallback is hand-authoring the SOAP envelope as XML via `Http.send()`, using the WSDL as documentation only. This trades type safety for parser independence.

### Named Credential vs. inline auth

Named Credentials add an upfront configuration burden (External Credential, Auth Provider, Permission Set) and they cannot be deployed as `.namedCredential-meta.xml` without coordinating with the External Credential. The benefit is that auth lives outside code, is rotatable without redeploy, and is auditable in Setup. Inline auth (Authorization header in `inputHttpHeaders_x`) is faster to ship but quietly bypasses Salesforce's auth-management surface and creates a credential-in-code risk. Default to Named Credentials; the exceptions (one-off integrations, throwaway prototypes, services that demand custom auth headers the NC cannot synthesize) should be documented and have an explicit retirement plan.

### Synchronous vs. async wrapping

A synchronous SOAP callout from a controller is fastest for the user (single round trip) but binds the user's session to the vendor's latency. The wrapping decision tree:

- **Latency < 2 s, low-volume, user-initiated**: synchronous is acceptable; surface a spinner.
- **Latency 2–15 s OR DML before / after the call**: Queueable. Decouples the callout from the trigger transaction, preserves typed payload, and supports retry chaining.
- **Volume > 10k records / hour**: Batch Apex. Keeps the callout budget healthy across the population.

`@future(callout=true)` is feasible but loses the typed payload — the future receives only primitives, forcing serialization. Queueable is the modern default.

---

## Anti-Patterns

1. **Hand-edit the generated stub instead of the WSDL** — Edits are destroyed on regen. Fix the WSDL on disk and commit it alongside the project; the cleaned WSDL is the source of truth.
2. **Use `HttpCalloutMock` to mock SOAP callouts** — Tests compile and fail at runtime. SOAP uses `WebServiceMock` with the `response.put('response_x', element)` contract.
3. **Bake the production URL into `endpoint_x`** — Promotes sandbox URLs into production deploys. Always set `endpoint_x = 'callout:<NC>'`.
4. **Single-catch `CalloutException` block for outbound SOAP** — Silently swallows SOAP-fault metadata. Use the two-catch ladder, `WebServiceCalloutException` first.
5. **Mix Named Credential endpoint with inline Authorization header** — Auth is silently stripped; integration may run with the wrong credentials. Auth belongs to the NC.

---

## Official Sources Used

- Apex Developer Guide — Calling Web Services Using WSDL2Apex — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_wsdl2apex.htm
- Apex Developer Guide — Considerations When Using WSDL to Apex — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_wsdl2apex_considerations.htm
- Apex Developer Guide — Testing Web Service Callouts — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_wsdl2apex_testing.htm
- Apex Reference Guide — WebServiceMock Interface — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_webservicemock.htm
- Apex Reference Guide — CalloutException Class — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_CalloutException.htm
- Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Named Credentials Help — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
