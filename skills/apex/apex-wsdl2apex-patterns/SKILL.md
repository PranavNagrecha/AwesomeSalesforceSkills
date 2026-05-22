---
name: apex-wsdl2apex-patterns
description: "Use when consuming a third-party SOAP web service from Apex by generating proxy classes from a WSDL — covers the Setup > Apex Classes > Generate from WSDL tool, WSDL pre-processing for the parser's limits, the generated stub's `_x` HTTP control properties, Named Credential wiring, SOAP fault handling, and WebServiceMock testing. Triggers: 'generate Apex from WSDL', 'wsdl2apex', 'WSDL parse error xsd:choice', 'outbound SOAP callout from Apex', 'WebServiceCalloutException not caught'. NOT for Salesforce-as-SOAP-server (enterprise/partner WSDL — use integration/soap-api-patterns), REST callouts (use apex/callouts-and-http-integrations), or generic HTTP retry (use apex/apex-callout-retry-and-resilience)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "I need to call an external SOAP service from Apex and have a WSDL file"
  - "Generate from WSDL fails with unsupported xsd:choice or xsd:any element"
  - "my outbound SOAP call ignores the Named Credential endpoint and uses the WSDL location"
  - "WebServiceCalloutException is not caught by my callout handler"
  - "WSDL is larger than 1 MB and the Generate from WSDL tool rejects it"
  - "mock outbound SOAP in unit tests — HttpCalloutMock does not intercept it"
  - "regenerating the WSDL stub overwrites my hand-edits"
tags:
  - apex
  - soap
  - wsdl
  - wsdl2apex
  - callouts
  - integration
  - outbound
  - named-credentials
  - webservicemock
inputs:
  - "the third-party WSDL file (XML) and the SOAP operations to be consumed"
  - "the Named Credential or endpoint that will serve the external service URL and auth"
  - "the calling Apex layer (synchronous controller, queueable, batch, future) and its bulk profile"
outputs:
  - "a saveable generated Apex stub class (under 1 MB compiled) plus any required WSDL pre-processing edits"
  - "a wrapper service class that sets endpoint_x via Named Credential, timeout_x, and headers"
  - "a WebServiceMock test class with a doInvoke implementation that exercises the success and SOAP-fault paths"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-22
---

# Apex WSDL-to-Apex Patterns

Activate when Apex needs to call **out** to a third-party SOAP web service and the integration starts from a WSDL the vendor provides. The skill covers the Setup > Apex Classes > Generate from WSDL tool, the WSDL features the parser does not support (the source of nearly every first-attempt failure), the shape of the generated stub class — including its `_x`-suffixed HTTP control properties — Named Credential wiring, the two distinct exception types the runtime raises, and the `WebServiceMock` testing contract that replaces `HttpCalloutMock` for SOAP. This is the **outbound direction**; for Salesforce as a SOAP server (enterprise / partner WSDL), use `integration/soap-api-patterns`.

---

## Before Starting

Gather this context before working on anything in this domain:

- **The WSDL file itself.** Open it and check three things: (1) total size — the platform parser rejects WSDLs over **1 MB**; (2) presence of `xsd:choice`, `xsd:any`, mixed content, recursive types, or external `<xsd:import>` references — all parser stoppers; (3) SOAP binding version — only **SOAP 1.1** is supported.
- **The auth model the vendor exposes.** Basic, OAuth client-credentials, mTLS, or a custom SOAP header (e.g. `<SessionHeader>`). This decides whether the auth is handled by a Named Credential (preferred) or by setting `inputHttpHeaders_x` on the stub.
- **The Apex layer that will call the service.** Synchronous transactions can hold a single open callout but block the user; queueable / batch is the canonical async wrapper. Apex callout governor limits apply: **120 second** total callout time and **120 second** per-call `timeout_x` max.
- **The runtime fault contract.** SOAP faults are NOT `CalloutException` — they raise `System.WebServiceCalloutException`. Plan the catch ladder before writing the stub.
- **Whether the stub will be regenerated later.** Hand-edits to the generated class are lost on regen. If the WSDL needs structural edits (e.g. `xsd:choice` → `xsd:sequence`), persist the edits to the WSDL on disk, not to the generated Apex.

---

## Core Concepts

### The Generate from WSDL tool and what it rejects

Setup > Custom Code > Apex Classes > **Generate from WSDL** parses the WSDL and produces one Apex class per `wsdl:portType`. Each `wsdl:operation` becomes a method on the port class; each `xsd:complexType` becomes a static inner class. The tool is strict — it operates in batch (no partial generation) and rejects the entire WSDL on any unsupported construct. Known stoppers:

- WSDL file over 1 MB (hard cap)
- SOAP 1.2 bindings (`http://schemas.xmlsoap.org/wsdl/soap12/`)
- `<xsd:choice>` and `<xsd:any>` model groups
- Recursive type references (a type that contains itself)
- External `<xsd:import>` and `<wsdl:import>` (the imported schema must be inlined)
- `<xsd:complexType mixed="true">` (text-and-element mixed content)
- More than one binding per port — only the first is honored
- Generated Apex that exceeds the 1 MB Apex class size limit (large WSDLs hit this even when the WSDL itself is under 1 MB)

The remediation pattern is always: **edit the WSDL on disk** (not the generated stub) to remove or simplify the unsupported construct, then re-run Generate from WSDL.

### Generated stub anatomy — the `_x` properties

Every generated port class exposes a fixed set of HTTP control properties, all suffixed with `_x` to avoid colliding with WSDL element names. The fields and their defaults:

| Property | Type | Default | Purpose |
|---|---|---|---|
| `endpoint_x` | `String` | service `<soap:address location>` from the WSDL | Runtime endpoint. **Always override** with `'callout:<NC>'`. |
| `timeout_x` | `Integer` | 10000 (ms) | Per-call timeout, max 120000. |
| `inputHttpHeaders_x` | `Map<String,String>` | empty | Outbound HTTP headers (e.g. `SOAPAction`, custom auth). |
| `outputHttpHeaders_x` | `Map<String,String>` | null until call returns | Populated by the runtime with response headers. |
| `clientCertName_x` | `String` | null | Name of a Certificate in Setup > Certificate and Key Management for mTLS. |
| `clientCert_x` / `clientCertPasswd_x` | `String` | null | Inline base64 cert + password — rarely used; prefer `clientCertName_x`. |
| `SessionHeader` and named SOAP headers | inner class | null | Any `<wsdl:header>` declared in the WSDL becomes a typed property the caller populates before invocation. |

Stub instantiation has no constructor argument; the caller mutates properties on the new instance, then invokes the operation method. **Reserved-word collisions** (`type`, `class`, `return`) in WSDL element names get auto-suffixed with `_x` on the generated class — clients must use the suffixed name.

### Named Credentials are the only correct endpoint source

The WSDL's `<soap:address location>` baked into `endpoint_x` is the vendor's documentation default — typically `https://api.example.com/v1/Service.svc` — which is **not the URL you should call in production**. Salesforce blocks any callout to a host not in Setup > Security > Remote Site Settings or fronted by a Named Credential. The correct pattern is to set `endpoint_x = 'callout:My_External_Service'` where `My_External_Service` is a Named Credential that resolves URL + auth at runtime. The Named Credential is also the right place to attach OAuth or Basic auth — those headers should NOT be set via `inputHttpHeaders_x` (the platform strips conflicting auth headers when the endpoint resolves to an NC). For mTLS, attach the client certificate at the External Credential / Named Credential level rather than via `clientCertName_x`.

### Two exception types, not one

The runtime distinguishes:

- **`System.CalloutException`** — transport-level failures (timeout, DNS, TLS handshake, HTTP non-2xx without a SOAP body, governor-limit excess).
- **`System.WebServiceCalloutException`** — the server returned HTTP 500 with a SOAP `<faultcode>` / `<faultstring>` body. The exception has `getCommonRuntimeException()` (deprecated) and the SOAP fault content is accessible via the exception message.

Catching `Exception` is too broad (you lose the fault metadata). Catching `CalloutException` alone misses every SOAP fault. The canonical handler is two `catch` blocks, fault first.

---

## Common Patterns

### Pattern 1 — Generate, wrap with Named Credential, dispatch from Queueable

**When to use:** Standard outbound SOAP call from a record-update path, asynchronous to avoid blocking the user.

**How it works:**

1. Pre-process the WSDL on disk: remove `xsd:choice`, inline imported schemas, replace SOAP 1.2 binding with 1.1 if both are declared.
2. Setup > Apex Classes > Generate from WSDL, upload the cleaned WSDL, accept the proposed class name. The tool generates `MyServicePort.cls` plus inner element classes.
3. Create a Named Credential `My_External_Service` with the production URL and auth (OAuth client credentials or Password Authentication for Basic).
4. Write a wrapper service class (`ExternalServiceCallout.cls`) that instantiates the stub, sets `endpoint_x = 'callout:My_External_Service'`, sets `timeout_x = 60000`, and dispatches the call. Wrap in `try` / `catch (System.WebServiceCalloutException fault) ... catch (System.CalloutException net) ...`.
5. Invoke the wrapper from a Queueable launched from the trigger handler, never from the trigger transaction itself. This decouples the callout from the DML and keeps the synchronous transaction under the 10-callout / 120-second budget.

**Why not the alternative:** Direct invocation from a `@future(callout=true)` method works but loses the typed payload (the future receives only primitive arguments), forcing serialization. Queueable preserves typed inputs and supports chaining for retry.

### Pattern 2 — WSDL with custom SOAP header (auth token in envelope)

**When to use:** Vendor authentication uses a SOAP header element (e.g. `<SessionHeader><Token>...</Token></SessionHeader>`) rather than an HTTP header.

**How it works:** The generated stub exposes the WSDL header as a typed property on the port class (e.g. `MyServicePort.SessionHeader_element`). Populate it before each operation call:

```apex
MyServicePort.Soap stub = new MyServicePort.Soap();
stub.endpoint_x = 'callout:My_External_Service';
stub.SessionHeader = new MyServicePort.SessionHeader_element();
stub.SessionHeader.Token = sessionTokenFromCustomMetadata();
MyServicePort.GetAccountResponse_element resp = stub.GetAccount(accountId);
```

**Why not the alternative:** Trying to fake the SOAP header by stuffing it into `inputHttpHeaders_x` puts it in the HTTP envelope, not the SOAP envelope — the server rejects it.

### Pattern 3 — Mocking outbound SOAP for tests

**When to use:** Any test class that exercises code which calls a generated stub method. SOAP callouts cannot run in test context without a mock.

**How it works:** Implement `WebServiceMock` (NOT `HttpCalloutMock` — that interface only intercepts `Http.send()`):

```apex
@isTest
private class MyServiceMock implements WebServiceMock {
    public void doInvoke(
        Object stub, Object request, Map<String, Object> response,
        String endpoint, String soapAction, String requestName,
        String responseNS, String responseName, String responseType
    ) {
        MyServicePort.GetAccountResponse_element r = new MyServicePort.GetAccountResponse_element();
        r.Result = 'mocked';
        response.put('response_x', r);
    }
}

@isTest static void coversCallout() {
    Test.setMock(WebServiceMock.class, new MyServiceMock());
    // ... code under test calls the stub ...
}
```

The response is returned by populating `response.put('response_x', element)` — the literal key `'response_x'` is the runtime contract.

**Why not the alternative:** Using `Test.setMock(HttpCalloutMock.class, ...)` compiles but never intercepts the SOAP callout — tests will throw "no callout mock" at runtime.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Vendor offers both REST and SOAP | Prefer REST (`apex/callouts-and-http-integrations`) | Smaller stubs, no WSDL maintenance, JSON ergonomics. |
| Vendor offers SOAP only, WSDL is under 1 MB and clean | Generate from WSDL; wrap with Named Credential | Standard path; stub is regenerable. |
| Vendor WSDL has `xsd:choice` / `xsd:any` / external imports | Pre-process WSDL on disk; commit the cleaned WSDL to source control | Hand-edits to generated Apex are lost on regen. |
| Generated Apex class exceeds 1 MB | Split the WSDL by port / operation set | Apex class file size cap. |
| Auth via OAuth / Basic | Named Credential + External Credential, do NOT set Authorization in `inputHttpHeaders_x` | NC strips conflicting headers. |
| Auth via SOAP header token | Populate the generated SOAP header property on the stub | Belongs in SOAP envelope, not HTTP header. |
| Auth via mTLS | Named Credential pointing to a Certificate, NOT `clientCertName_x` directly | Centralized cert lifecycle. |
| Need bulk DML + outbound SOAP per record | Queueable per chunk, NOT a `@future(callout=true)` | 50 future calls / transaction limit; queueable chains for retry. |
| Test class needs to cover the callout | `Test.setMock(WebServiceMock.class, ...)` | HttpCalloutMock does not intercept SOAP. |
| Vendor WSDL uses SOAP 1.2 | Ask for a SOAP 1.1 binding; otherwise hand-author the HTTP request | wsdl2apex does not support SOAP 1.2. |

---

## Recommended Workflow

1. **Inspect the WSDL** for the parser stoppers (size, SOAP version, `xsd:choice`, `xsd:any`, external imports, mixed content). Fix them on the WSDL file itself before uploading.
2. **Generate the stub** via Setup > Apex Classes > Generate from WSDL. Save the cleaned WSDL alongside the project as source-of-truth for future regens.
3. **Create the Named Credential** for the production endpoint and auth. Do not bake the URL into `endpoint_x` defaults.
4. **Write the wrapper service class** that sets `endpoint_x = 'callout:<NC>'`, sets `timeout_x` (default 10s is too low for most SOAP services), and dispatches through a typed method per operation.
5. **Implement the two-catch ladder**: `WebServiceCalloutException` first (SOAP faults), then `CalloutException` (network). Log both via `ApplicationLogger`.
6. **Decide the async surface**: synchronous controller (rare — only for sub-2-second services), Queueable (default), or Batch (high-volume).
7. **Write the WebServiceMock**. Cover happy path, SOAP fault, and timeout. Verify with `Test.startTest()` / `Test.stopTest()`.
8. **Document the regen procedure** in the wrapper class header: which WSDL file, where it lives, and which WSDL edits were applied.

---

## Review Checklist

- [ ] `endpoint_x` is set to `'callout:<NC>'`, never a literal URL
- [ ] `timeout_x` is set explicitly (default 10s is rarely correct)
- [ ] Authentication is handled by the Named Credential, not `inputHttpHeaders_x`
- [ ] SOAP-header auth (if any) is populated on the typed stub property
- [ ] The catch ladder is `WebServiceCalloutException` first, then `CalloutException`
- [ ] Test class uses `Test.setMock(WebServiceMock.class, ...)`, not `HttpCalloutMock`
- [ ] WSDL pre-processing edits are persisted to the WSDL file, not the generated Apex
- [ ] Async wrapper (Queueable/Batch) used when the calling transaction does DML
- [ ] Generated stub is not hand-edited (or, if it is, the rationale is documented and regen risks are flagged)
- [ ] WSDL size < 1 MB; generated Apex < 1 MB compiled

---

## Salesforce-Specific Gotchas

1. **`xsd:choice` rejects the whole WSDL** — The parser does not support union types. The remediation is to convert the choice to `xsd:sequence` with each option marked `minOccurs="0"`, accepting that the schema becomes laxer than the vendor intends. Document the deviation; vendors sometimes change behavior in response to the looser payload.
2. **`endpoint_x` default points at the vendor's documentation URL** — Code generated from a sandbox-style WSDL silently calls the vendor's production URL unless `endpoint_x` is overridden. Always reset before the first call.
3. **`HttpCalloutMock` compiles but does not intercept the SOAP callout** — A test that uses the wrong mock interface fails at runtime with "Callout from a test method must be wrapped in a callout mock"; the compiler does not warn. Use `WebServiceMock` and the `response.put('response_x', element)` contract.
4. **`SoapException` does not exist** — The exception class is `System.WebServiceCalloutException`. Catching the wrong class lets the fault propagate as an unhandled error.
5. **Regenerating the stub destroys hand-edits** — Any field rename, type widening, or comment added to the generated class is lost on re-generation. Persist all customization to the WSDL or to the wrapper class.
6. **Generated Apex hits the 1 MB class size limit** — A WSDL under 1 MB can still produce Apex over 1 MB because each complex type expands to a full inner class with serializers. The Save button fails with "compiled class exceeds maximum size". Split the WSDL by port or strip unused operations.
7. **Reserved-word collisions get `_x`-suffixed** — A WSDL element named `type` becomes `type_x` in the generated class. Documentation that references the original name confuses readers.
8. **`outputHttpHeaders_x` is null until the call returns** — Reading it before the operation invocation throws NPE. Read only after a successful (or fault-completed) call.
9. **`timeout_x` default of 10 seconds is too short** — Many SOAP services routinely respond in 15–30 seconds. The default silently causes `CalloutException: Read timed out`. Set `timeout_x = 60000` or higher and budget against the 120-second governor cap.
10. **`<wsdl:import>` of another WSDL is silently dropped** — Multi-file WSDL bundles must be merged into a single self-contained WSDL before upload. The tool does not fetch imported files.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Cleaned WSDL file | Pre-processed WSDL with parser-incompatible constructs removed; checked into source control alongside the project. |
| Generated stub class | Apex class produced by Generate from WSDL — committed but treated as generated code (no hand-edits). |
| Wrapper service class | Typed wrapper that sets endpoint/timeout/headers, owns the catch ladder, and exposes per-operation methods to the rest of the codebase. |
| Named Credential metadata | `.namedCredential-meta.xml` that resolves URL + auth; the only correct callout target. |
| WebServiceMock test class | Covers happy path, SOAP fault, and timeout. |
| Regen runbook | Header comment in the wrapper or a `WSDL_README.md` documenting which WSDL file, what edits were applied, and the regen command. |

---

## Related Skills

- `integration/soap-api-patterns` — for the **inbound** direction (enterprise / partner WSDL of Salesforce as the server)
- `apex/callouts-and-http-integrations` — for REST / generic HTTP callouts (preferred over SOAP for new integrations)
- `apex/apex-http-callout-mocking` — for the parallel `HttpCalloutMock` testing pattern (REST side)
- `apex/apex-callout-retry-and-resilience` — for the retry and circuit-breaker patterns to wrap around the WSDL stub
- `integration/named-credentials-setup` — for the Named Credential configuration that the wrapper depends on
- `integration/oauth-flows-and-connected-apps` — when the external service uses OAuth and the auth flows through the NC
- `integration/mutual-tls-callouts` — for mTLS attached via External Credential / Certificate
